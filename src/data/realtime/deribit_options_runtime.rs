use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, Utc};
use futures::stream::{self, BoxStream};
use reqwest::blocking::Client;
use serde::Deserialize;

use crate::types::{Candle, Timeframe};

use super::{
    market_support::{
        apply_auxiliary_evidence_to_outcome, build_auxiliary_evidence, AuxiliaryMarketEvidence,
        OptionsChainSummary, Quote, SpotInstrumentKind,
    },
    provider::RealtimeDataProvider,
};

const DERIBIT_API_URL: &str = "https://www.deribit.com/api/v2";

pub struct DeribitOptionsRuntimeProvider {
    client: Client,
}

impl DeribitOptionsRuntimeProvider {
    pub fn new(_base_url: impl Into<String>) -> Self {
        Self {
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .user_agent("ict-engine/0.1")
                .build()
                .expect("failed to build reqwest blocking client"),
        }
    }

    /// Fetch options chain summary from Deribit public API.
    /// `currency` should be "BTC" or "ETH".
    pub fn fetch_options_chain_summary(&self, currency: &str) -> Result<OptionsChainSummary> {
        let currency = currency.trim().to_uppercase();
        let kind = if currency.starts_with("BTC") {
            "BTC"
        } else if currency.starts_with("ETH") {
            "ETH"
        } else {
            bail!("Deribit options only support BTC/ETH, got '{}'", currency);
        };

        // 1. Get index price
        let index_price = self.fetch_index_price(kind)?;

        // 2. Get book summary for all options of this currency
        let book_entries = self.fetch_book_summary(kind)?;

        // 3. Get DVOL data for volatility context
        let dvol = self.fetch_dvol(kind).ok();

        // Aggregate call/put OI, volume, IV from book summaries
        let mut call_open_interest: f64 = 0.0;
        let mut put_open_interest: f64 = 0.0;
        let mut call_volume: f64 = 0.0;
        let mut put_volume: f64 = 0.0;
        let mut atm_iv_values: Vec<f64> = Vec::new();
        let mut atm_delta_values: Vec<f64> = Vec::new();
        let mut atm_gamma_values: Vec<f64> = Vec::new();
        let mut atm_vega_values: Vec<f64> = Vec::new();
        let mut nearest_dte: Option<f64> = None;

        for entry in &book_entries {
            let is_call = entry.instrument_name.contains("-C");
            let is_put = entry.instrument_name.contains("-P");
            if !is_call && !is_put {
                continue;
            }

            let oi = entry.open_interest.unwrap_or(0.0);
            let vol = entry.mark_iv.unwrap_or(0.0); // use mark_iv as vol signal

            if is_call {
                call_open_interest += oi;
                call_volume += vol; // placeholder: Deribit summary doesn't have raw volume per contract easily
            } else {
                put_open_interest += oi;
                put_volume += vol;
            }

            // Parse strike from instrument name (e.g., BTC-28JUN26-100000-C)
            if let Some((strike, dte)) = parse_instrument_strike_dte(&entry.instrument_name) {
                // ATM filter: within 10% of spot
                let moneyness = (strike - index_price).abs() / index_price.max(f64::EPSILON);
                if moneyness <= 0.10 && dte <= 45.0 {
                    if let Some(iv) = entry.mark_iv {
                        atm_iv_values.push(iv / 100.0); // Deribit returns IV as percentage
                    }
                    if let Some(delta) = entry.greeks.as_ref().and_then(|g| g.delta) {
                        atm_delta_values.push(delta);
                    }
                    if let Some(gamma) = entry.greeks.as_ref().and_then(|g| g.gamma) {
                        atm_gamma_values.push(gamma);
                    }
                    if let Some(vega) = entry.greeks.as_ref().and_then(|g| g.vega) {
                        atm_vega_values.push(vega);
                    }
                }

                // Track nearest expiration
                match nearest_dte {
                    None => nearest_dte = Some(dte),
                    Some(current) if dte < current => nearest_dte = Some(dte),
                    _ => {}
                }
            }
        }

        let near_atm_iv = if atm_iv_values.is_empty() {
            dvol.map(|v| v / 100.0) // fallback to DVOL if no ATM contracts
        } else {
            Some(atm_iv_values.iter().sum::<f64>() / atm_iv_values.len() as f64)
        };

        let near_atm_delta = avg_option(&atm_delta_values);
        let near_atm_gamma = avg_option(&atm_gamma_values);
        let near_atm_vega = avg_option(&atm_vega_values);

        Ok(OptionsChainSummary {
            symbol: format!("{}-DERIBIT", kind),
            source: Some("deribit_public_api".to_string()),
            underlying_price: Some(index_price),
            call_open_interest,
            put_open_interest,
            put_call_oi_ratio: ratio(put_open_interest, call_open_interest),
            call_volume,
            put_volume,
            put_call_volume_ratio: ratio(put_volume, call_volume),
            near_atm_implied_volatility: near_atm_iv,
            near_atm_delta,
            near_atm_gamma,
            near_atm_vega,
            call_gamma_oi: None, // Deribit summary doesn't expose per-strike OI*gamma
            put_gamma_oi: None,
            gamma_skew: None,
            nearest_expiration_dte: nearest_dte,
        })
    }

    pub fn build_auxiliary_evidence(
        &self,
        spot_kind: SpotInstrumentKind,
        spot_symbol: &str,
        options_symbol: &str,
        futures_candles: &[Candle],
        spot_candles: &[Candle],
        options_summary: &OptionsChainSummary,
    ) -> AuxiliaryMarketEvidence {
        build_auxiliary_evidence(
            spot_kind,
            spot_symbol,
            options_symbol,
            futures_candles,
            spot_candles,
            options_summary,
        )
    }

    pub fn apply_auxiliary_evidence_to_outcome(
        &self,
        base_distribution: &[f64],
        directional_bias: f64,
        uncertainty_penalty: f64,
    ) -> Vec<f64> {
        apply_auxiliary_evidence_to_outcome(
            base_distribution,
            directional_bias,
            uncertainty_penalty,
        )
    }

    fn fetch_index_price(&self, currency: &str) -> Result<f64> {
        let response: DeribitResponse<IndexPriceResult> = self
            .client
            .get(format!("{}/public/get_index_price", DERIBIT_API_URL))
            .query(&[("index_name", format!("{}_usd", currency.to_lowercase()))])
            .send()
            .context("failed to request Deribit index price")?
            .error_for_status()
            .context("Deribit index price returned error")?
            .json()
            .context("failed to parse Deribit index price response")?;

        Ok(response.result.index_price)
    }

    fn fetch_book_summary(&self, currency: &str) -> Result<Vec<BookSummaryEntry>> {
        let response: DeribitResponse<Vec<BookSummaryEntry>> = self
            .client
            .get(format!(
                "{}/public/get_book_summary_by_currency",
                DERIBIT_API_URL
            ))
            .query(&[
                ("currency", currency.to_string()),
                ("kind", "option".to_string()),
            ])
            .send()
            .context("failed to request Deribit book summary")?
            .error_for_status()
            .context("Deribit book summary returned error")?
            .json()
            .context("failed to parse Deribit book summary response")?;

        Ok(response.result)
    }

    fn fetch_dvol(&self, currency: &str) -> Result<f64> {
        let now = Utc::now();
        let start = now - chrono::Duration::hours(1);
        let response: DeribitResponse<Vec<Vec<f64>>> = self
            .client
            .get(format!(
                "{}/public/get_volatility_index_data",
                DERIBIT_API_URL
            ))
            .query(&[
                ("currency", currency.to_string()),
                ("resolution", "60".to_string()),
                ("start_timestamp", start.timestamp_millis().to_string()),
                ("end_timestamp", now.timestamp_millis().to_string()),
            ])
            .send()
            .context("failed to request Deribit DVOL")?
            .error_for_status()
            .context("Deribit DVOL returned error")?
            .json()
            .context("failed to parse Deribit DVOL response")?;

        // DVOL data is [[timestamp, open, high, low, close], ...]
        let latest_dvol = response
            .result
            .last()
            .and_then(|row| row.get(4).copied())
            .ok_or_else(|| anyhow!("no DVOL data returned"))?;

        Ok(latest_dvol)
    }
}

#[async_trait::async_trait]
impl RealtimeDataProvider for DeribitOptionsRuntimeProvider {
    async fn fetch_candles(
        &self,
        _symbol: &str,
        _timeframe: Timeframe,
        _start: DateTime<Utc>,
        _end: DateTime<Utc>,
    ) -> Result<Vec<Candle>> {
        bail!("Deribit options runtime does not provide OHLCV candles directly")
    }

    async fn subscribe_candles(
        &self,
        _symbol: &str,
        _timeframe: Timeframe,
    ) -> Result<BoxStream<'static, Candle>> {
        Ok(Box::pin(stream::empty()))
    }

    async fn get_quote(&self, symbol: &str) -> Result<Quote> {
        let currency = if symbol.to_uppercase().starts_with("BTC") {
            "BTC"
        } else {
            "ETH"
        };
        let price = self.fetch_index_price(currency)?;
        Ok(Quote {
            symbol: symbol.to_string(),
            bid: price,
            ask: price,
            last: price,
            timestamp: Utc::now(),
        })
    }

    async fn health_check(&self) -> Result<bool> {
        let response = self
            .client
            .get(format!("{}/public/test", DERIBIT_API_URL))
            .send();
        Ok(
            matches!(response, Ok(resp) if resp.status().is_success() || resp.status().is_redirection()),
        )
    }
}

// -- Deribit API response types --

#[derive(Debug, Deserialize)]
struct DeribitResponse<T> {
    result: T,
}

#[derive(Debug, Deserialize)]
struct IndexPriceResult {
    index_price: f64,
}

#[derive(Debug, Deserialize)]
struct BookSummaryEntry {
    instrument_name: String,
    open_interest: Option<f64>,
    mark_iv: Option<f64>,
    greeks: Option<GreeksData>,
}

#[derive(Debug, Deserialize)]
struct GreeksData {
    delta: Option<f64>,
    gamma: Option<f64>,
    vega: Option<f64>,
    #[serde(rename = "theta")]
    _theta: Option<f64>,
    #[serde(rename = "rho")]
    _rho: Option<f64>,
}

// -- helpers --

/// Parse strike price and approximate DTE from Deribit instrument name.
/// Format: BTC-28JUN26-100000-C
fn parse_instrument_strike_dte(name: &str) -> Option<(f64, f64)> {
    let parts: Vec<&str> = name.split('-').collect();
    if parts.len() < 4 {
        return None;
    }
    let strike = parts[2].parse::<f64>().ok()?;

    // Parse date from parts[1] (e.g., "28JUN26")
    let date_str = parts[1];
    let dte = parse_deribit_dte(date_str)?;

    Some((strike, dte))
}

/// Parse Deribit date format (e.g., "28JUN26") and return DTE.
fn parse_deribit_dte(date_str: &str) -> Option<f64> {
    // Format: DDMMMYY (e.g., 28JUN26)
    if date_str.len() < 7 {
        return None;
    }
    let day: u32 = date_str[..2].parse().ok()?;
    let month_str = &date_str[2..5];
    let year_2d: i32 = date_str[5..7].parse().ok()?;
    let year = 2000 + year_2d;

    let month = match month_str {
        "JAN" => 1,
        "FEB" => 2,
        "MAR" => 3,
        "APR" => 4,
        "MAY" => 5,
        "JUN" => 6,
        "JUL" => 7,
        "AUG" => 8,
        "SEP" => 9,
        "OCT" => 10,
        "NOV" => 11,
        "DEC" => 12,
        _ => return None,
    };

    let expiry = chrono::NaiveDate::from_ymd_opt(year, month, day)?;
    let now = Utc::now().date_naive();
    let dte = (expiry - now).num_days() as f64;
    if dte < 0.0 {
        return None;
    }
    Some(dte)
}

fn avg_option(values: &[f64]) -> Option<f64> {
    if values.is_empty() {
        None
    } else {
        Some(values.iter().sum::<f64>() / values.len() as f64)
    }
}

fn ratio(numerator: f64, denominator: f64) -> Option<f64> {
    if denominator.abs() <= f64::EPSILON {
        None
    } else {
        Some(numerator / denominator)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_instrument_strike_dte() {
        let (strike, _) = parse_instrument_strike_dte("BTC-28JUN26-100000-C").unwrap();
        assert!((strike - 100000.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_parse_instrument_strike_dte_eth() {
        let (strike, _) = parse_instrument_strike_dte("ETH-28JUN26-5000-P").unwrap();
        assert!((strike - 5000.0).abs() < f64::EPSILON);
    }

    #[test]
    fn test_parse_instrument_invalid() {
        assert!(parse_instrument_strike_dte("INVALID").is_none());
        assert!(parse_instrument_strike_dte("BTC-C").is_none());
    }
}
