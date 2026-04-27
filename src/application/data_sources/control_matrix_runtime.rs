use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, TimeDelta, Utc};
use reqwest::blocking::Client;
use serde::Deserialize;
use serde_json::Value;
use std::process::Command;

use crate::application::backtest::Pb12RunSpec;
use crate::data::load_candles;
use crate::data::realtime::openalice::{
    AuxiliaryMarketEvidence, OpenAliceProvider, OptionsChainSummary, SpotInstrumentKind,
};
use crate::application::data_sources::{
    TVREMIX_MCP_API_KEY_ENV, TVREMIX_MCP_DEFAULT_URL, TVREMIX_MCP_URL_ENV,
};
use crate::types::Candle;

const CONTROL_MATRIX_REFERENCE_PROVIDER_ENV: &str = "ICT_ENGINE_CONTROL_MATRIX_REFERENCE_PROVIDER";
const CONTROL_MATRIX_OPTIONS_PROVIDER_ENV: &str = "ICT_ENGINE_CONTROL_MATRIX_OPTIONS_PROVIDER";
const CONTROL_MATRIX_IBKR_FETCH_SCRIPT_ENV: &str = "ICT_ENGINE_IBKR_FETCH_SCRIPT";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ControlMatrixReferenceProvider {
    YahooFinance,
    IbkrHistorical,
    TradingViewMcp,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ControlMatrixOptionsProvider {
    YahooFinance,
    TradingViewMcp,
}

#[derive(Debug, Clone, Default)]
pub struct ControlMatrixRuntimeOverrides {
    pub paired_candles: Option<Vec<Candle>>,
    pub auxiliary: Option<AuxiliaryMarketEvidence>,
    pub runtime_notes: Vec<String>,
}

pub fn build_control_matrix_runtime_overrides(
    data_path: &str,
    symbol: &str,
    run_spec: &Pb12RunSpec,
) -> Result<ControlMatrixRuntimeOverrides> {
    if !(run_spec.use_etf
        || run_spec.use_cfd
        || run_spec.use_vix
        || run_spec.use_greeks
        || run_spec.use_oi
        || run_spec.use_iv)
    {
        return Ok(ControlMatrixRuntimeOverrides::default());
    }

    let primary_candles = load_candles(data_path)?;
    if primary_candles.len() < 2 {
        return Ok(ControlMatrixRuntimeOverrides {
            runtime_notes: vec!["control_matrix_runtime_insufficient_primary_history".to_string()],
            ..ControlMatrixRuntimeOverrides::default()
        });
    }

    let etf_symbol = etf_symbol_for_futures(symbol);
    let interval = yahoo_interval_from_candles(&primary_candles);
    let start = primary_candles.first().map(|item| item.timestamp).unwrap();
    let end = primary_candles.last().map(|item| item.timestamp).unwrap();
    let client = yahoo_client()?;
    let reference_provider = resolve_reference_provider();
    let options_provider = resolve_options_provider();
    let mut runtime_notes = Vec::new();

    let mut etf_candles = None;
    if run_spec.use_etf || run_spec.use_greeks || run_spec.use_oi || run_spec.use_iv {
        match fetch_reference_candles(
            &client,
            reference_provider,
            etf_symbol,
            &interval,
            start,
            end,
            &mut runtime_notes,
        ) {
            Ok(candles) if !candles.is_empty() => {
                runtime_notes.push(format!("runtime_etf_reference_symbol={etf_symbol}"));
                etf_candles = Some(candles);
            }
            Ok(_) => runtime_notes.push(format!("runtime_etf_reference_empty_symbol={etf_symbol}")),
            Err(err) => runtime_notes.push(format!(
                "runtime_etf_reference_fetch_failed symbol={} reason={}",
                etf_symbol, err
            )),
        }
    }

    let mut vix_candles = None;
    if run_spec.use_vix {
        match fetch_reference_candles(
            &client,
            reference_provider,
            "^VIX",
            "1d",
            start - TimeDelta::days(7),
            end,
            &mut runtime_notes,
        ) {
            Ok(candles) if !candles.is_empty() => {
                runtime_notes.push("runtime_vix_overlay_symbol=^VIX".to_string());
                vix_candles = Some(candles);
            }
            Ok(_) => runtime_notes.push("runtime_vix_overlay_empty_symbol=^VIX".to_string()),
            Err(err) => runtime_notes.push(format!(
                "runtime_vix_overlay_fetch_failed symbol=^VIX reason={}",
                err
            )),
        }
    }

    if run_spec.use_cfd {
        let cfd_symbol = cfd_symbol_for_futures(symbol);
        match fetch_reference_candles(
            &client,
            reference_provider,
            cfd_symbol,
            &interval,
            start,
            end,
            &mut runtime_notes,
        ) {
            Ok(candles) if etf_candles.is_none() && !candles.is_empty() => {
                runtime_notes.push(format!("runtime_cfd_reference_symbol={cfd_symbol}"));
                etf_candles = Some(candles);
            }
            Ok(_) => runtime_notes.push(format!("runtime_cfd_reference_empty_symbol={cfd_symbol}")),
            Err(err) => runtime_notes.push(format!(
                "runtime_cfd_reference_fetch_failed symbol={} reason={}",
                cfd_symbol, err
            )),
        }
    }

    let paired_candles = if run_spec.use_etf {
        etf_candles.clone()
    } else {
        None
    };

    let auxiliary = if run_spec.use_vix
        || run_spec.use_greeks
        || run_spec.use_oi
        || run_spec.use_iv
        || run_spec.use_etf
    {
        let spot_candles = etf_candles.clone().or_else(|| vix_candles.clone());
        if let Some(spot_candles) = spot_candles {
            let mut options_summary = if run_spec.use_greeks || run_spec.use_oi || run_spec.use_iv {
                match fetch_options_summary(
                    &client,
                    options_provider,
                    etf_symbol,
                    &mut runtime_notes,
                ) {
                    Ok(summary) => summary,
                    Err(err) => {
                        runtime_notes.push(format!(
                            "runtime_options_summary_fetch_failed symbol={} reason={}",
                            etf_symbol, err
                        ));
                        default_options_summary(etf_symbol)
                    }
                }
            } else {
                default_options_summary(etf_symbol)
            };

            if !run_spec.use_oi {
                options_summary.put_call_oi_ratio = None;
                options_summary.call_open_interest = 0.0;
                options_summary.put_open_interest = 0.0;
                options_summary.call_volume = 0.0;
                options_summary.put_volume = 0.0;
                options_summary.put_call_volume_ratio = None;
            }
            if !run_spec.use_iv {
                options_summary.near_atm_implied_volatility = None;
            }
            if !run_spec.use_greeks {
                options_summary.near_atm_delta = None;
                options_summary.near_atm_gamma = None;
                options_summary.near_atm_vega = None;
                options_summary.call_gamma_oi = None;
                options_summary.put_gamma_oi = None;
                options_summary.gamma_skew = None;
            } else if options_summary.near_atm_gamma.is_none() {
                runtime_notes.push(format!(
                    "runtime_greeks_unavailable_from_provider symbol={}",
                    etf_symbol
                ));
            }

            let spot_kind = if run_spec.use_vix && !run_spec.use_etf {
                SpotInstrumentKind::Index
            } else {
                SpotInstrumentKind::Equity
            };
            let builder = OpenAliceProvider::new("internal://control-matrix-yfinance", None);
            let mut auxiliary = builder.build_auxiliary_evidence(
                spot_kind,
                if run_spec.use_vix && !run_spec.use_etf {
                    "^VIX"
                } else {
                    etf_symbol
                },
                etf_symbol,
                &primary_candles,
                &spot_candles,
                &options_summary,
            );
            if let Some(vix) = vix_candles.as_ref() {
                apply_vix_overlay(&mut auxiliary, vix, &mut runtime_notes);
            }
            Some(auxiliary)
        } else {
            None
        }
    } else {
        None
    };

    Ok(ControlMatrixRuntimeOverrides {
        paired_candles,
        auxiliary,
        runtime_notes,
    })
}

fn yahoo_client() -> Result<Client> {
    Client::builder()
        .timeout(std::time::Duration::from_secs(20))
        .build()
        .context("failed to build yahoo runtime client")
}

fn resolve_reference_provider() -> ControlMatrixReferenceProvider {
    match std::env::var(CONTROL_MATRIX_REFERENCE_PROVIDER_ENV)
        .unwrap_or_else(|_| "yfinance".to_string())
        .trim()
        .to_ascii_lowercase()
        .as_str()
    {
        "ibkr" => ControlMatrixReferenceProvider::IbkrHistorical,
        "tradingview_mcp" | "tradingview" | "tvremix" => {
            ControlMatrixReferenceProvider::TradingViewMcp
        }
        _ => ControlMatrixReferenceProvider::YahooFinance,
    }
}

fn resolve_options_provider() -> ControlMatrixOptionsProvider {
    match std::env::var(CONTROL_MATRIX_OPTIONS_PROVIDER_ENV)
        .unwrap_or_else(|_| {
            if std::env::var(TVREMIX_MCP_API_KEY_ENV)
                .map(|value| !value.trim().is_empty())
                .unwrap_or(false)
            {
                "tradingview_mcp".to_string()
            } else {
                "yfinance".to_string()
            }
        })
        .trim()
        .to_ascii_lowercase()
        .as_str()
    {
        "tradingview_mcp" | "tradingview" | "tvremix" => {
            ControlMatrixOptionsProvider::TradingViewMcp
        }
        _ => ControlMatrixOptionsProvider::YahooFinance,
    }
}

fn fetch_reference_candles(
    client: &Client,
    provider: ControlMatrixReferenceProvider,
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
    runtime_notes: &mut Vec<String>,
) -> Result<Vec<Candle>> {
    match provider {
        ControlMatrixReferenceProvider::YahooFinance => {
            runtime_notes.push("runtime_reference_provider=yfinance".to_string());
            fetch_yahoo_candles(client, symbol, interval, start, end)
        }
        ControlMatrixReferenceProvider::IbkrHistorical => {
            runtime_notes.push("runtime_reference_provider=ibkr".to_string());
            fetch_ibkr_historical_candles(symbol, interval, start, end)
        }
        ControlMatrixReferenceProvider::TradingViewMcp => {
            runtime_notes.push("runtime_reference_provider=tradingview_mcp".to_string());
            fetch_tradingview_ohlcv(symbol, interval, start, end)
        }
    }
}

fn fetch_options_summary(
    client: &Client,
    provider: ControlMatrixOptionsProvider,
    symbol: &str,
    runtime_notes: &mut Vec<String>,
) -> Result<OptionsChainSummary> {
    match provider {
        ControlMatrixOptionsProvider::YahooFinance => {
            runtime_notes.push("runtime_options_provider=yfinance".to_string());
            fetch_yahoo_options_summary(client, symbol)
        }
        ControlMatrixOptionsProvider::TradingViewMcp => {
            runtime_notes.push("runtime_options_provider=tradingview_mcp".to_string());
            fetch_tradingview_options_summary(symbol)
        }
    }
}

fn fetch_yahoo_candles(
    client: &Client,
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let url = format!(
        "https://query1.finance.yahoo.com/v8/finance/chart/{}",
        urlencoding::encode(symbol)
    );
    let response: YahooChartResponse = client
        .get(url)
        .query(&[
            ("interval", interval.to_string()),
            ("period1", start.timestamp().to_string()),
            ("period2", (end.timestamp() + 60).to_string()),
            ("includePrePost", "false".to_string()),
            ("events", "div,splits".to_string()),
        ])
        .send()
        .with_context(|| format!("failed yahoo chart request for '{}'", symbol))?
        .error_for_status()
        .with_context(|| format!("yahoo chart request returned error for '{}'", symbol))?
        .json()
        .with_context(|| format!("failed to decode yahoo chart response for '{}'", symbol))?;

    let result = response
        .chart
        .result
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("missing yahoo chart result for '{}'", symbol))?;
    let quote = result
        .indicators
        .quote
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("missing yahoo quote arrays for '{}'", symbol))?;

    let mut candles = Vec::new();
    for index in 0..result.timestamp.len() {
        let Some(open) = quote.open.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(high) = quote.high.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(low) = quote.low.get(index).and_then(|value| *value) else {
            continue;
        };
        let Some(close) = quote.close.get(index).and_then(|value| *value) else {
            continue;
        };
        let timestamp = DateTime::<Utc>::from_timestamp(result.timestamp[index], 0)
            .ok_or_else(|| anyhow!("invalid yahoo timestamp for '{}'", symbol))?;
        candles.push(Candle {
            timestamp,
            open,
            high,
            low,
            close,
            volume: quote
                .volume
                .get(index)
                .and_then(|value| *value)
                .unwrap_or_default(),
        });
    }
    if candles.is_empty() {
        bail!("no usable yahoo candles returned for '{}'", symbol);
    }
    Ok(candles)
}

fn fetch_yahoo_options_summary(client: &Client, symbol: &str) -> Result<OptionsChainSummary> {
    let url = format!(
        "https://query2.finance.yahoo.com/v7/finance/options/{}",
        urlencoding::encode(symbol)
    );
    let response: YahooOptionsResponse = client
        .get(url)
        .send()
        .with_context(|| format!("failed yahoo options request for '{}'", symbol))?
        .error_for_status()
        .with_context(|| format!("yahoo options request returned error for '{}'", symbol))?
        .json()
        .with_context(|| format!("failed to decode yahoo options response for '{}'", symbol))?;
    let result = response
        .option_chain
        .result
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("missing yahoo options result for '{}'", symbol))?;
    let option_set = result
        .options
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("missing yahoo options contracts for '{}'", symbol))?;
    let calls = option_set.calls;
    let puts = option_set.puts;
    let call_open_interest = calls
        .iter()
        .map(|item| item.open_interest.unwrap_or_default())
        .sum::<f64>();
    let put_open_interest = puts
        .iter()
        .map(|item| item.open_interest.unwrap_or_default())
        .sum::<f64>();
    let call_volume = calls
        .iter()
        .map(|item| item.volume.unwrap_or_default())
        .sum::<f64>();
    let put_volume = puts
        .iter()
        .map(|item| item.volume.unwrap_or_default())
        .sum::<f64>();
    let underlying = result.quote.regular_market_price;
    let near_atm_implied_volatility = underlying.and_then(|price| {
        let ivs = calls
            .iter()
            .chain(puts.iter())
            .filter(|item| ((item.strike - price).abs() / price.max(f64::EPSILON)) <= 0.10)
            .filter_map(|item| item.implied_volatility)
            .collect::<Vec<_>>();
        if ivs.is_empty() {
            None
        } else {
            Some(ivs.iter().sum::<f64>() / ivs.len() as f64)
        }
    });

    Ok(OptionsChainSummary {
        symbol: symbol.to_string(),
        source: Some("yahoo_direct_options".to_string()),
        underlying_price: underlying,
        call_open_interest,
        put_open_interest,
        put_call_oi_ratio: ratio(put_open_interest, call_open_interest),
        call_volume,
        put_volume,
        put_call_volume_ratio: ratio(put_volume, call_volume),
        near_atm_implied_volatility,
        near_atm_delta: None,
        near_atm_gamma: None,
        near_atm_vega: None,
        call_gamma_oi: None,
        put_gamma_oi: None,
        gamma_skew: None,
        nearest_expiration_dte: None,
    })
}

fn fetch_ibkr_historical_candles(
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let script = std::env::var(CONTROL_MATRIX_IBKR_FETCH_SCRIPT_ENV).unwrap_or_else(|_| {
        format!(
            "{}/scripts/auto_quant_external/fetch_external.py",
            env!("CARGO_MANIFEST_DIR")
        )
    });
    let temp = std::env::temp_dir().join(format!(
        "ict-engine-ibkr-{}-{}.csv",
        symbol.to_ascii_lowercase(),
        Utc::now().timestamp_nanos_opt().unwrap_or_default()
    ));
    let duration = ibkr_duration_from_range(start, end);
    let bar_size = ibkr_bar_size(interval);
    let status = Command::new("python3")
        .args([
            &script,
            "ibkr-historical",
            "--symbol",
            symbol,
            "--sec-type",
            ibkr_security_type(symbol),
            "--exchange",
            ibkr_exchange(symbol),
            "--currency",
            "USD",
            "--bar-size",
            &bar_size,
            "--duration",
            &duration,
            "--output",
            temp.to_str().unwrap_or("ibkr.csv"),
        ])
        .status()
        .with_context(|| format!("failed to spawn ibkr historical fetch for '{}'", symbol))?;
    if !status.success() {
        bail!("ibkr historical fetch failed for '{}'", symbol);
    }
    let result = load_csv_candles(&temp);
    let _ = std::fs::remove_file(&temp);
    result
}

fn fetch_tradingview_ohlcv(
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let tv_symbol = tradingview_symbol(symbol);
    let count = estimate_bar_count(interval, start, end);
    let payload = call_tradingview_tool(
        "get_ohlcv",
        serde_json::json!({
            "symbol": tv_symbol,
            "interval": tradingview_interval(interval),
            "count": count,
            "summary": false
        }),
    )?;
    let bars = payload
        .get("bars")
        .and_then(Value::as_array)
        .ok_or_else(|| anyhow!("tradingview get_ohlcv returned no bars"))?;
    let mut candles = Vec::new();
    for bar in bars {
        let ts = bar.get("t").and_then(Value::as_f64).unwrap_or_default() as i64;
        let timestamp = DateTime::<Utc>::from_timestamp(ts, 0)
            .ok_or_else(|| anyhow!("invalid tradingview timestamp"))?;
        if timestamp < start || timestamp > end + TimeDelta::days(3) {
            continue;
        }
        let open = bar.get("o").and_then(Value::as_f64).unwrap_or_default();
        let high = bar.get("h").and_then(Value::as_f64).unwrap_or_default();
        let low = bar.get("l").and_then(Value::as_f64).unwrap_or_default();
        let close = bar.get("c").and_then(Value::as_f64).unwrap_or_default();
        candles.push(Candle {
            timestamp,
            open,
            high,
            low,
            close,
            volume: bar.get("v").and_then(Value::as_f64).unwrap_or_default(),
        });
    }
    if candles.is_empty() {
        bail!("tradingview returned no usable bars for '{}'", symbol);
    }
    Ok(candles)
}

fn fetch_tradingview_options_summary(symbol: &str) -> Result<OptionsChainSummary> {
    let tv_symbol = tradingview_symbol(symbol);
    let expirations = call_tradingview_tool(
        "get_option_expirations",
        serde_json::json!({ "symbol": tv_symbol }),
    )?;
    let first_expiration = expirations
        .pointer("/data/expirations")
        .and_then(Value::as_array)
        .and_then(|items| items.first())
        .and_then(|item| item.get("expiration"))
        .and_then(Value::as_str)
        .ok_or_else(|| anyhow!("tradingview returned no option expirations for '{}'", symbol))?;
    let chain = call_tradingview_tool(
        "get_option_chain",
        serde_json::json!({
            "symbol": tv_symbol,
            "expiration": first_expiration,
        }),
    )?;
    let data = chain
        .get("data")
        .ok_or_else(|| anyhow!("tradingview option chain missing data payload"))?;
    let calls = data
        .get("calls")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let puts = data
        .get("puts")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let call_open_interest = 0.0;
    let put_open_interest = 0.0;
    let call_volume = 0.0;
    let put_volume = 0.0;
    let underlying_price = data.get("underlying_price").and_then(Value::as_f64);
    let near_atm = underlying_price.and_then(|price| {
        let mut selected = calls
            .iter()
            .chain(puts.iter())
            .filter_map(|item| {
                let strike = item.get("strike").and_then(Value::as_f64)?;
                let iv = item.get("iv").and_then(Value::as_f64)?;
                let delta = item.get("delta").and_then(Value::as_f64);
                let gamma = item.get("gamma").and_then(Value::as_f64);
                let vega = item.get("vega").and_then(Value::as_f64);
                let distance = (strike - price).abs() / price.max(f64::EPSILON);
                (distance <= 0.10).then_some((distance, iv, delta, gamma, vega))
            })
            .collect::<Vec<_>>();
        selected.sort_by(|a, b| a.0.total_cmp(&b.0));
        selected.into_iter().next()
    });
    let call_gamma_oi = calls
        .iter()
        .filter_map(|item| item.get("gamma").and_then(Value::as_f64))
        .sum::<f64>()
        .into();
    let put_gamma_oi = puts
        .iter()
        .filter_map(|item| item.get("gamma").and_then(Value::as_f64))
        .sum::<f64>()
        .into();
    let gamma_skew = match (call_gamma_oi, put_gamma_oi) {
        (Some(call), Some(put)) => Some(call - put),
        _ => None,
    };

    Ok(OptionsChainSummary {
        symbol: symbol.to_string(),
        source: Some("tradingview_mcp:get_option_chain".to_string()),
        underlying_price,
        call_open_interest,
        put_open_interest,
        put_call_oi_ratio: None,
        call_volume,
        put_volume,
        put_call_volume_ratio: None,
        near_atm_implied_volatility: near_atm.map(|item| item.1 / 100.0),
        near_atm_delta: near_atm.and_then(|item| item.2),
        near_atm_gamma: near_atm.and_then(|item| item.3),
        near_atm_vega: near_atm.and_then(|item| item.4),
        call_gamma_oi,
        put_gamma_oi,
        gamma_skew,
        nearest_expiration_dte: None,
    })
}

fn call_tradingview_tool(name: &str, arguments: Value) -> Result<Value> {
    let key = std::env::var(TVREMIX_MCP_API_KEY_ENV)
        .with_context(|| format!("{} must be set for tradingview_mcp", TVREMIX_MCP_API_KEY_ENV))?;
    let url = std::env::var(TVREMIX_MCP_URL_ENV).unwrap_or_else(|_| TVREMIX_MCP_DEFAULT_URL.to_string());
    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(20))
        .build()
        .context("failed to build tradingview MCP client")?;
    let response: Value = client
        .post(url)
        .bearer_auth(key)
        .json(&serde_json::json!({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments,
            }
        }))
        .send()
        .with_context(|| format!("tradingview MCP call '{}' failed", name))?
        .error_for_status()
        .with_context(|| format!("tradingview MCP call '{}' returned error", name))?
        .json()
        .with_context(|| format!("failed to decode tradingview MCP response for '{}'", name))?;
    if response
        .pointer("/result/isError")
        .and_then(Value::as_bool)
        .unwrap_or(false)
    {
        bail!(
            "tradingview MCP tool '{}' error: {}",
            name,
            response
                .pointer("/result/content/0/text")
                .and_then(Value::as_str)
                .unwrap_or("unknown error")
        );
    }
    response
        .pointer("/result/structuredContent")
        .cloned()
        .ok_or_else(|| anyhow!("tradingview MCP tool '{}' missing structuredContent", name))
}

fn load_csv_candles(path: &std::path::Path) -> Result<Vec<Candle>> {
    let mut reader = csv::Reader::from_path(path)
        .with_context(|| format!("failed to open generated candle csv '{}'", path.display()))?;
    let headers = reader.headers()?.clone();
    let ts_index = headers
        .iter()
        .position(|item| item.eq_ignore_ascii_case("date") || item.eq_ignore_ascii_case("ts"))
        .ok_or_else(|| anyhow!("csv missing date/ts column"))?;
    let open_index = headers.iter().position(|item| item == "open").ok_or_else(|| anyhow!("csv missing open"))?;
    let high_index = headers.iter().position(|item| item == "high").ok_or_else(|| anyhow!("csv missing high"))?;
    let low_index = headers.iter().position(|item| item == "low").ok_or_else(|| anyhow!("csv missing low"))?;
    let close_index = headers.iter().position(|item| item == "close").ok_or_else(|| anyhow!("csv missing close"))?;
    let volume_index = headers.iter().position(|item| item == "volume");
    let mut candles = Vec::new();
    for record in reader.records() {
        let record = record?;
        let timestamp = chrono::DateTime::parse_from_rfc3339(&record[ts_index])
            .or_else(|_| chrono::DateTime::parse_from_str(&record[ts_index], "%Y-%m-%d %H:%M:%S%#z"))
            .map(|value| value.with_timezone(&Utc))
            .or_else(|_| {
                chrono::NaiveDateTime::parse_from_str(&record[ts_index], "%Y-%m-%d %H:%M:%S")
                    .map(|value| value.and_utc())
            })
            .or_else(|_| {
                chrono::NaiveDate::parse_from_str(&record[ts_index], "%Y-%m-%d")
                    .map(|value| value.and_hms_opt(0, 0, 0).unwrap().and_utc())
            })
            .with_context(|| format!("failed to parse candle timestamp '{}'", &record[ts_index]))?;
        candles.push(Candle {
            timestamp,
            open: record[open_index].parse()?,
            high: record[high_index].parse()?,
            low: record[low_index].parse()?,
            close: record[close_index].parse()?,
            volume: volume_index
                .and_then(|index| record.get(index))
                .unwrap_or("0")
                .parse()
                .unwrap_or_default(),
        });
    }
    Ok(candles)
}

fn apply_vix_overlay(
    auxiliary: &mut AuxiliaryMarketEvidence,
    vix_candles: &[Candle],
    runtime_notes: &mut Vec<String>,
) {
    if vix_candles.len() < 2 {
        return;
    }
    let last = vix_candles.last().map(|item| item.close).unwrap_or_default();
    let prior = vix_candles
        .get(vix_candles.len().saturating_sub(6))
        .map(|item| item.close)
        .unwrap_or(last);
    if prior.abs() <= f64::EPSILON {
        return;
    }
    let change = (last - prior) / prior;
    runtime_notes.push(format!("runtime_vix_change_5bar={change:.4}"));
    if change > 0.03 {
        auxiliary.uncertainty_penalty = (auxiliary.uncertainty_penalty + 0.05).min(0.25);
        auxiliary.notes.push("vix_rising_increases_uncertainty".to_string());
    } else if change < -0.03 {
        auxiliary.long_bias = (auxiliary.long_bias + 0.02).min(0.20);
        auxiliary.notes.push("vix_falling_relaxes_risk".to_string());
    }
}

fn default_options_summary(symbol: &str) -> OptionsChainSummary {
    OptionsChainSummary {
        symbol: symbol.to_string(),
        source: Some("disabled_or_unavailable".to_string()),
        underlying_price: None,
        call_open_interest: 0.0,
        put_open_interest: 0.0,
        put_call_oi_ratio: None,
        call_volume: 0.0,
        put_volume: 0.0,
        put_call_volume_ratio: None,
        near_atm_implied_volatility: None,
        near_atm_delta: None,
        near_atm_gamma: None,
        near_atm_vega: None,
        call_gamma_oi: None,
        put_gamma_oi: None,
        gamma_skew: None,
        nearest_expiration_dte: None,
    }
}

fn ratio(numerator: f64, denominator: f64) -> Option<f64> {
    (denominator.abs() > f64::EPSILON).then_some(numerator / denominator)
}

fn cfd_symbol_for_futures(symbol: &str) -> &str {
    match symbol.trim().to_ascii_uppercase().as_str() {
        "NQ" => "NASDAQ:NDX",
        "ES" => "SP:SPX",
        "YM" => "DJ:DJI",
        "GC" => "OANDA:XAUUSD",
        "6E" => "FX:EURUSD",
        "CL" => "TVC:USOIL",
        _ => "SP:SPX",
    }
}

fn etf_symbol_for_futures(symbol: &str) -> &str {
    match symbol.trim().to_ascii_uppercase().as_str() {
        "NQ" => "QQQ",
        "ES" => "SPY",
        "YM" => "DIA",
        "GC" => "GLD",
        "6E" => "FXE",
        "CL" => "USO",
        _ => "SPY",
    }
}

fn tradingview_symbol(symbol: &str) -> &str {
    match symbol.trim().to_ascii_uppercase().as_str() {
        "QQQ" => "NASDAQ:QQQ",
        "SPY" => "AMEX:SPY",
        "DIA" => "AMEX:DIA",
        "GLD" => "AMEX:GLD",
        "FXE" => "AMEX:FXE",
        "USO" => "AMEX:USO",
        "^VIX" => "CBOE:VIX",
        "NASDAQ:NDX" => "NASDAQ:NDX",
        "SP:SPX" => "SP:SPX",
        "DJ:DJI" => "DJ:DJI",
        "OANDA:XAUUSD" => "OANDA:XAUUSD",
        "FX:EURUSD" => "FX:EURUSD",
        "TVC:USOIL" => "TVC:USOIL",
        _ => "NASDAQ:QQQ",
    }
}

fn tradingview_interval(interval: &str) -> &str {
    match interval {
        "1m" => "1",
        "2m" => "2",
        "5m" => "5",
        "15m" => "15",
        "30m" => "30",
        "60m" | "1h" => "60",
        "90m" => "90",
        "1d" => "1D",
        _ => "1D",
    }
}

fn ibkr_security_type(symbol: &str) -> &str {
    match symbol.trim().to_ascii_uppercase().as_str() {
        "QQQ" | "SPY" | "DIA" | "GLD" | "FXE" | "USO" => "STK",
        "^VIX" | "SPX" | "NDX" | "DJI" => "IND",
        "EURUSD" | "OANDA:XAUUSD" => "CASH",
        _ => "STK",
    }
}

fn ibkr_exchange(symbol: &str) -> &str {
    match symbol.trim().to_ascii_uppercase().as_str() {
        "QQQ" => "SMART",
        "SPY" => "SMART",
        "DIA" => "SMART",
        "GLD" => "SMART",
        "FXE" => "SMART",
        "USO" => "SMART",
        "^VIX" | "VIX" => "CBOE",
        "SPX" => "CBOE",
        "NDX" => "NASDAQ",
        "DJI" => "NYSE",
        "EURUSD" => "IDEALPRO",
        _ => "SMART",
    }
}

fn ibkr_duration_from_range(start: DateTime<Utc>, end: DateTime<Utc>) -> String {
    let days = (end - start).num_days().max(1);
    if days <= 30 {
        format!("{days} D")
    } else if days <= 365 {
        format!("{} M", (days / 30).max(1))
    } else {
        format!("{} Y", (days / 365).max(1))
    }
}

fn ibkr_bar_size(interval: &str) -> String {
    match interval {
        "1m" => "1 min",
        "2m" => "2 mins",
        "5m" => "5 mins",
        "15m" => "15 mins",
        "30m" => "30 mins",
        "60m" | "1h" => "1 hour",
        "90m" => "1 hour",
        "1d" => "1 day",
        _ => "1 day",
    }
    .to_string()
}

fn estimate_bar_count(interval: &str, start: DateTime<Utc>, end: DateTime<Utc>) -> usize {
    let minutes = (end - start).num_minutes().max(1) as usize;
    let divisor = match interval {
        "1m" => 1,
        "2m" => 2,
        "5m" => 5,
        "15m" => 15,
        "30m" => 30,
        "60m" | "1h" => 60,
        "90m" => 90,
        "1d" => 1440,
        _ => 1440,
    };
    (minutes / divisor).clamp(10, 5_000)
}

fn yahoo_interval_from_candles(candles: &[Candle]) -> String {
    if candles.len() < 2 {
        return "1d".to_string();
    }
    let delta = candles[1]
        .timestamp
        .signed_duration_since(candles[0].timestamp)
        .num_minutes()
        .abs();
    match delta {
        0 | 1 => "1m",
        2 => "2m",
        5 => "5m",
        15 => "15m",
        30 => "30m",
        60 => "60m",
        90 => "90m",
        1440 => "1d",
        _ if delta >= 1440 => "1d",
        _ => "60m",
    }
    .to_string()
}

#[derive(Debug, Deserialize)]
struct YahooChartResponse {
    chart: YahooChartBody,
}

#[derive(Debug, Deserialize)]
struct YahooChartBody {
    result: Vec<YahooChartResult>,
}

#[derive(Debug, Deserialize)]
struct YahooChartResult {
    timestamp: Vec<i64>,
    indicators: YahooChartIndicators,
}

#[derive(Debug, Deserialize)]
struct YahooChartIndicators {
    quote: Vec<YahooChartQuote>,
}

#[derive(Debug, Deserialize)]
struct YahooChartQuote {
    open: Vec<Option<f64>>,
    high: Vec<Option<f64>>,
    low: Vec<Option<f64>>,
    close: Vec<Option<f64>>,
    #[serde(default)]
    volume: Vec<Option<f64>>,
}

#[derive(Debug, Deserialize)]
struct YahooOptionsResponse {
    #[serde(rename = "optionChain")]
    option_chain: YahooOptionsChain,
}

#[derive(Debug, Deserialize)]
struct YahooOptionsChain {
    result: Vec<YahooOptionsResult>,
}

#[derive(Debug, Deserialize)]
struct YahooOptionsResult {
    quote: YahooUnderlyingQuote,
    options: Vec<YahooOptionSet>,
}

#[derive(Debug, Deserialize)]
struct YahooUnderlyingQuote {
    #[serde(rename = "regularMarketPrice")]
    regular_market_price: Option<f64>,
}

#[derive(Debug, Deserialize)]
struct YahooOptionSet {
    calls: Vec<YahooOptionContract>,
    puts: Vec<YahooOptionContract>,
}

#[derive(Debug, Deserialize)]
struct YahooOptionContract {
    strike: f64,
    #[serde(rename = "openInterest")]
    open_interest: Option<f64>,
    volume: Option<f64>,
    #[serde(rename = "impliedVolatility")]
    implied_volatility: Option<f64>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    fn candle(ts: i64, close: f64) -> Candle {
        Candle {
            timestamp: Utc.timestamp_opt(ts, 0).unwrap(),
            open: close - 1.0,
            high: close + 1.0,
            low: close - 2.0,
            close,
            volume: 1_000.0,
        }
    }

    #[test]
    fn yahoo_interval_infers_common_bar_sizes() {
        let candles = vec![
            candle(1_700_000_000, 100.0),
            candle(1_700_000_900, 101.0),
        ];
        assert_eq!(yahoo_interval_from_candles(&candles), "15m");
    }

    #[test]
    fn vix_overlay_only_adjusts_when_history_exists() {
        let mut auxiliary = AuxiliaryMarketEvidence {
            spot_symbol: "QQQ".to_string(),
            options_symbol: "QQQ".to_string(),
            spot_kind: SpotInstrumentKind::Equity,
            spot_last_close: None,
            futures_last_close: None,
            spot_return: None,
            futures_return: None,
            raw_basis_bps: None,
            normalized_basis_bps: None,
            rolling_price_ratio_mean: None,
            put_call_oi_ratio: None,
            put_call_volume_ratio: None,
            near_atm_implied_volatility: None,
            near_atm_delta: None,
            near_atm_gamma: None,
            near_atm_vega: None,
            call_gamma_oi: None,
            put_gamma_oi: None,
            gamma_skew: None,
            hedge_pressure_direction: None,
            hedge_pressure_score: None,
            long_bias: 0.0,
            short_bias: 0.0,
            uncertainty_penalty: 0.0,
            notes: Vec::new(),
        };
        let mut notes = Vec::new();
        apply_vix_overlay(
            &mut auxiliary,
            &[
                candle(1_700_000_000, 10.0),
                candle(1_700_086_400, 10.1),
                candle(1_700_172_800, 10.2),
                candle(1_700_259_200, 10.3),
                candle(1_700_345_600, 10.4),
                candle(1_700_432_000, 10.8),
            ],
            &mut notes,
        );
        assert!(auxiliary.uncertainty_penalty > 0.0);
        assert!(notes.iter().any(|item| item.starts_with("runtime_vix_change_5bar=")));
    }
}
