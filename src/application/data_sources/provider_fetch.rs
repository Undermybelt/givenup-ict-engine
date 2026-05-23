use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, NaiveDate, NaiveDateTime, Utc};
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

use super::harness::{
    MarketDataHarnessHubbleSpec, MarketDataHarnessIbkrSpec, MarketDataHarnessTask,
    ProviderExecutionRequest,
};
use super::tradingview_mcp::{fetch_tradingview_ohlcv, TradingViewMcpClient};
use crate::data::realtime::crypto_public_runtime::CryptoPublicRuntimeProvider;
use crate::data::realtime::market_support::{OptionsChainSummary, SpotInstrumentKind};
use crate::data::realtime::yfinance_runtime::YahooFinanceProvider;
use crate::types::Candle;

pub(crate) const CONTROL_MATRIX_IBKR_FETCH_SCRIPT_ENV: &str = "ICT_ENGINE_IBKR_FETCH_SCRIPT";
pub(crate) const CONTROL_MATRIX_IBKR_GATEWAY_PORT_ENV: &str = "ICT_ENGINE_IBKR_GATEWAY_PORT";
const HUBBLE_BASE_URL_ENV: &str = "ICT_ENGINE_HUBBLE_BASE_URL";
const HUBBLE_API_KEY_ENV: &str = "ICT_ENGINE_HUBBLE_API_KEY";
const HUBBLE_DEFAULT_API_KEY: &str = "123456";
const IBKR_GATEWAY_HOST: &str = "127.0.0.1";
const IBKR_GATEWAY_PORT_CANDIDATES: [u16; 4] = [7497, 7496, 4002, 4001];
const IBKR_GATEWAY_PORT_CACHE_RELATIVE_PATH: &str = ".ict-engine/ibkr_gateway_port.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct IbkrGatewayPortCache {
    host: String,
    port: u16,
    source: String,
}

pub(crate) fn fetch_reference_candles_for_task(
    task: &MarketDataHarnessTask,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
    count: usize,
) -> Result<Vec<Candle>> {
    match &task.request {
        ProviderExecutionRequest::YahooFinance { symbol } => {
            fetch_yahoo_candles(symbol, interval, start, end)
        }
        ProviderExecutionRequest::PublicExchange { provider, symbol } => {
            fetch_public_exchange_candles(provider, symbol, interval, start, end)
        }
        ProviderExecutionRequest::TradingViewMcp { symbol } => {
            fetch_tradingview_ohlcv(symbol, interval, start, end, count)
        }
        ProviderExecutionRequest::Hubble { spec } => {
            fetch_hubble_candles(spec, interval, start, end, count)
        }
        ProviderExecutionRequest::Ibkr { contract } => {
            fetch_ibkr_historical_candles(contract, interval, start, end)
        }
    }
}

pub(crate) fn fetch_options_summary_for_task(
    task: &MarketDataHarnessTask,
) -> Result<OptionsChainSummary> {
    match &task.request {
        ProviderExecutionRequest::YahooFinance { symbol } => {
            match fetch_yahoo_options_summary(symbol) {
                Ok(summary) => Ok(summary),
                Err(primary_error) => {
                    if let Some(proxy_symbol) = task.fallback_options_proxy_symbol.as_deref() {
                        YahooFinanceProvider::new("native://yfinance")
                            .fetch_options_volatility_proxy_summary(proxy_symbol, symbol)
                    } else {
                        Err(primary_error)
                    }
                }
            }
        }
        ProviderExecutionRequest::PublicExchange { .. } => {
            bail!("unsupported options provider '{}'", task.provider)
        }
        ProviderExecutionRequest::TradingViewMcp { symbol } => {
            match fetch_tradingview_options_summary(symbol) {
                Ok(summary) => Ok(summary),
                Err(primary_error) => {
                    let yahoo = YahooFinanceProvider::new("native://yfinance");
                    if let Some(proxy_symbol) = task.fallback_options_proxy_symbol.as_deref() {
                        yahoo.fetch_options_volatility_proxy_summary(proxy_symbol, symbol)
                    } else {
                        yahoo
                            .fetch_options_chain_summary(task.symbol.as_str())
                            .or(Err(primary_error))
                    }
                }
            }
        }
        ProviderExecutionRequest::Hubble { spec } => match fetch_hubble_options_summary(spec) {
            Ok(summary) => Ok(summary),
            Err(primary_error) => {
                if let Some(proxy_symbol) = task.fallback_options_proxy_symbol.as_deref() {
                    YahooFinanceProvider::new("native://yfinance")
                        .fetch_options_volatility_proxy_summary(proxy_symbol, &spec.symbol)
                } else {
                    Err(primary_error)
                }
            }
        },
        ProviderExecutionRequest::Ibkr { .. } => {
            bail!("unsupported options provider '{}'", task.provider)
        }
    }
}

fn fetch_yahoo_candles(
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let provider = YahooFinanceProvider::new("native://yfinance");
    let spot_kind = if symbol.starts_with('^') {
        SpotInstrumentKind::Index
    } else {
        SpotInstrumentKind::Equity
    };
    provider.fetch_spot_candles(spot_kind, symbol, Some(interval), start, end)
}

fn fetch_yahoo_options_summary(symbol: &str) -> Result<OptionsChainSummary> {
    let provider = YahooFinanceProvider::new("native://yfinance");
    provider.fetch_options_chain_summary(symbol)
}

fn fetch_public_exchange_candles(
    provider: &str,
    symbol: &str,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let exchange = match provider {
        "bybit_public" | "bybit_public_runtime" => "bybit",
        _ => "binance",
    };
    CryptoPublicRuntimeProvider::new_for_exchange(exchange)
        .fetch_futures_candles(symbol, interval, start, end)
}

fn hubble_client() -> Result<(String, Client)> {
    let base_url = std::env::var(HUBBLE_BASE_URL_ENV)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .ok_or_else(|| anyhow!("{HUBBLE_BASE_URL_ENV} must be set for Hubble runtime fetches"))?;
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .context("failed to build Hubble HTTP client")?;
    Ok((base_url.trim_end_matches('/').to_string(), client))
}

fn build_hubble_candle_request(
    spec: &MarketDataHarnessHubbleSpec,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
    count: usize,
) -> Result<(String, Vec<(String, String)>)> {
    let market = spec.market.trim().to_ascii_lowercase();
    match market.as_str() {
        "cn" => {
            let mapped = match interval {
                "1d" => "daily",
                "1w" => "weekly",
                "1mo" => "monthly",
                other => bail!("unsupported Hubble CN interval '{}'", other),
            };
            Ok((
                "/api/v2/cnstock/stocks".to_string(),
                vec![
                    ("symbol".to_string(), spec.symbol.clone()),
                    ("interval".to_string(), mapped.to_string()),
                    ("startDate".to_string(), start.format("%Y%m%d").to_string()),
                    ("endDate".to_string(), end.format("%Y%m%d").to_string()),
                    ("limit".to_string(), count.to_string()),
                ],
            ))
        }
        "hk" => {
            if interval != "1d" {
                bail!("unsupported Hubble HK interval '{}'", interval);
            }
            Ok((
                "/api/v2/hkstock/stocks".to_string(),
                vec![
                    ("symbol".to_string(), spec.symbol.clone()),
                    ("startDate".to_string(), start.format("%Y%m%d").to_string()),
                    ("endDate".to_string(), end.format("%Y%m%d").to_string()),
                ],
            ))
        }
        "us" => {
            if interval != "1d" {
                bail!("unsupported Hubble US interval '{}'", interval);
            }
            Ok((
                "/api/v2/usstock/stocks".to_string(),
                vec![
                    ("symbol".to_string(), spec.symbol.clone()),
                    ("startDate".to_string(), start.format("%Y%m%d").to_string()),
                    ("endDate".to_string(), end.format("%Y%m%d").to_string()),
                    ("limit".to_string(), count.to_string()),
                ],
            ))
        }
        "crypto" => {
            let exchange = spec
                .exchange
                .clone()
                .filter(|value| !value.trim().is_empty())
                .ok_or_else(|| anyhow!("Hubble crypto fetch requires exchange"))?;
            Ok((
                "/api/v2/crypto/klines".to_string(),
                vec![
                    ("exchange".to_string(), exchange),
                    ("symbol".to_string(), spec.symbol.clone()),
                    ("interval".to_string(), interval.to_string()),
                    ("startDate".to_string(), start.format("%Y%m%d").to_string()),
                    ("endDate".to_string(), end.format("%Y%m%d").to_string()),
                    ("limit".to_string(), count.to_string()),
                ],
            ))
        }
        other => bail!("unsupported Hubble market '{}'", other),
    }
}

fn fetch_hubble_candles(
    spec: &MarketDataHarnessHubbleSpec,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
    count: usize,
) -> Result<Vec<Candle>> {
    let (base_url, client) = hubble_client()?;
    let (path, params) = build_hubble_candle_request(spec, interval, start, end, count)?;
    let response = client
        .get(format!("{base_url}{path}"))
        .header("X-API-Key", current_hubble_api_key())
        .header("Content-Type", "application/json")
        .query(&params)
        .send()
        .with_context(|| format!("failed to fetch Hubble candles for '{}'", spec.symbol))?;
    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().unwrap_or_default();
        bail!(
            "hubble candle fetch failed for '{}' with HTTP {}: {}",
            spec.symbol,
            status,
            body
        );
    }
    let payload: Value = response.json().with_context(|| {
        format!(
            "failed to decode Hubble candle payload for '{}'",
            spec.symbol
        )
    })?;
    parse_hubble_candles_payload(&payload)
}

fn current_hubble_api_key() -> String {
    std::env::var(HUBBLE_API_KEY_ENV)
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| HUBBLE_DEFAULT_API_KEY.to_string())
}

fn parse_hubble_candles_payload(payload: &Value) -> Result<Vec<Candle>> {
    let rows = extract_hubble_rows(payload);
    if rows.is_empty() {
        bail!("Hubble candle payload contained no rows");
    }
    rows.into_iter()
        .map(parse_hubble_candle_row)
        .collect::<Result<Vec<_>>>()
}

fn extract_hubble_rows(payload: &Value) -> Vec<&Value> {
    if let Some(items) = payload.as_array() {
        return items.iter().collect();
    }
    for pointer in [
        "/data",
        "/list",
        "/rows",
        "/items",
        "/data/data",
        "/result/data",
        "/result/list",
    ] {
        if let Some(items) = payload.pointer(pointer).and_then(Value::as_array) {
            return items.iter().collect();
        }
    }
    Vec::new()
}

fn parse_hubble_candle_row(row: &Value) -> Result<Candle> {
    let timestamp = parse_hubble_timestamp(
        row.get("time")
            .or_else(|| row.get("timestamp"))
            .or_else(|| row.get("ts"))
            .or_else(|| row.get("date"))
            .ok_or_else(|| anyhow!("Hubble candle row missing timestamp"))?,
    )?;
    Ok(Candle {
        timestamp,
        open: parse_hubble_f64(row.get("open")).ok_or_else(|| anyhow!("missing open"))?,
        high: parse_hubble_f64(row.get("high")).ok_or_else(|| anyhow!("missing high"))?,
        low: parse_hubble_f64(row.get("low")).ok_or_else(|| anyhow!("missing low"))?,
        close: parse_hubble_f64(row.get("close")).ok_or_else(|| anyhow!("missing close"))?,
        volume: parse_hubble_f64(row.get("volume").or_else(|| row.get("vol"))).unwrap_or(0.0),
    })
}

fn fetch_hubble_options_summary(spec: &MarketDataHarnessHubbleSpec) -> Result<OptionsChainSummary> {
    let (base_url, client) = hubble_client()?;
    let response = client
        .get(format!("{base_url}/api/v2/options/chain"))
        .header("X-API-Key", current_hubble_api_key())
        .header("Content-Type", "application/json")
        .query(&[("symbol", spec.symbol.as_str()), ("require_greeks", "true")])
        .send()
        .with_context(|| format!("failed to fetch Hubble options chain for '{}'", spec.symbol))?;
    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().unwrap_or_default();
        bail!(
            "hubble options fetch failed for '{}' with HTTP {}: {}",
            spec.symbol,
            status,
            body
        );
    }
    let payload: Value = response.json().with_context(|| {
        format!(
            "failed to decode Hubble options payload for '{}'",
            spec.symbol
        )
    })?;
    parse_hubble_options_summary(&spec.symbol, &payload)
}

fn parse_hubble_options_summary(symbol: &str, payload: &Value) -> Result<OptionsChainSummary> {
    let rows = payload
        .pointer("/data/data")
        .and_then(Value::as_array)
        .or_else(|| payload.pointer("/data").and_then(Value::as_array))
        .ok_or_else(|| anyhow!("Hubble options payload contained no rows"))?;
    let underlying_price = payload
        .pointer("/data/underlying_price")
        .and_then(parse_hubble_f64_value)
        .or_else(|| {
            payload
                .get("underlying_price")
                .and_then(parse_hubble_f64_value)
        });
    let mut call_open_interest = 0.0;
    let mut put_open_interest = 0.0;
    let mut call_volume = 0.0;
    let mut put_volume = 0.0;
    let mut nearest_expiration: Option<NaiveDate> = None;
    type AtmOptionSummary = (f64, f64, Option<f64>, Option<f64>, Option<f64>);
    let mut nearest_atm: Option<AtmOptionSummary> = None;
    let mut call_gamma_oi = 0.0;
    let mut put_gamma_oi = 0.0;
    let mut saw_call_gamma = false;
    let mut saw_put_gamma = false;

    for row in rows {
        let option_type = row
            .get("type")
            .and_then(Value::as_str)
            .map(|value| value.to_ascii_lowercase())
            .unwrap_or_default();
        let open_interest =
            parse_hubble_f64(row.get("open_interest").or_else(|| row.get("openInterest")))
                .unwrap_or(0.0);
        let volume = parse_hubble_f64(row.get("volume")).unwrap_or(0.0);
        let gamma = parse_hubble_f64(row.get("gamma"));
        match option_type.as_str() {
            "call" | "c" => {
                call_open_interest += open_interest;
                call_volume += volume;
                if let Some(gamma) = gamma {
                    call_gamma_oi += gamma * open_interest;
                    saw_call_gamma = true;
                }
            }
            "put" | "p" => {
                put_open_interest += open_interest;
                put_volume += volume;
                if let Some(gamma) = gamma {
                    put_gamma_oi += gamma * open_interest;
                    saw_put_gamma = true;
                }
            }
            _ => {}
        }
        if let Some(expiration) = row
            .get("expiration")
            .and_then(Value::as_str)
            .and_then(parse_hubble_expiration)
        {
            if nearest_expiration
                .map(|current| expiration < current)
                .unwrap_or(true)
            {
                nearest_expiration = Some(expiration);
            }
        }
        if let Some(underlying_price) = underlying_price {
            let strike = parse_hubble_f64(row.get("strike"));
            let iv = parse_hubble_f64(
                row.get("implied_volatility")
                    .or_else(|| row.get("iv"))
                    .or_else(|| row.get("impliedVolatility")),
            );
            if let Some(strike) = strike {
                let distance =
                    (strike - underlying_price).abs() / underlying_price.max(f64::EPSILON);
                let candidate = (
                    distance,
                    iv.unwrap_or_default(),
                    parse_hubble_f64(row.get("delta")),
                    gamma,
                    parse_hubble_f64(row.get("vega")),
                );
                if nearest_atm
                    .map(|current| distance < current.0)
                    .unwrap_or(true)
                {
                    nearest_atm = Some(candidate);
                }
            }
        }
    }

    let nearest_expiration_dte =
        nearest_expiration.map(|date| (date - Utc::now().date_naive()).num_days().max(0) as f64);

    Ok(OptionsChainSummary {
        symbol: symbol.to_string(),
        source: Some("hubble:/api/v2/options/chain".to_string()),
        underlying_price,
        call_open_interest,
        put_open_interest,
        put_call_oi_ratio: ratio_or_none(put_open_interest, call_open_interest),
        call_volume,
        put_volume,
        put_call_volume_ratio: ratio_or_none(put_volume, call_volume),
        near_atm_implied_volatility: nearest_atm.map(|item| item.1).filter(|value| *value > 0.0),
        near_atm_delta: nearest_atm.and_then(|item| item.2),
        near_atm_gamma: nearest_atm.and_then(|item| item.3),
        near_atm_vega: nearest_atm.and_then(|item| item.4),
        call_gamma_oi: saw_call_gamma.then_some(call_gamma_oi),
        put_gamma_oi: saw_put_gamma.then_some(put_gamma_oi),
        gamma_skew: if saw_call_gamma || saw_put_gamma {
            Some(call_gamma_oi - put_gamma_oi)
        } else {
            None
        },
        nearest_expiration_dte,
    })
}

fn parse_hubble_timestamp(value: &Value) -> Result<DateTime<Utc>> {
    if let Some(number) = value
        .as_i64()
        .or_else(|| value.as_u64().map(|item| item as i64))
    {
        return parse_hubble_epoch(number);
    }
    let raw = value
        .as_str()
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| anyhow!("invalid Hubble timestamp"))?;
    if raw.chars().all(|item| item.is_ascii_digit()) {
        if raw.len() == 8 {
            let date = NaiveDate::parse_from_str(raw, "%Y%m%d")
                .with_context(|| format!("failed to parse Hubble date '{}'", raw))?;
            return Ok(date.and_hms_opt(0, 0, 0).unwrap().and_utc());
        }
        return parse_hubble_epoch(raw.parse::<i64>()?);
    }
    chrono::DateTime::parse_from_rfc3339(raw)
        .map(|value| value.with_timezone(&Utc))
        .or_else(|_| {
            NaiveDateTime::parse_from_str(raw, "%Y-%m-%d %H:%M:%S").map(|value| value.and_utc())
        })
        .or_else(|_| {
            NaiveDate::parse_from_str(raw, "%Y-%m-%d")
                .map(|value| value.and_hms_opt(0, 0, 0).unwrap().and_utc())
        })
        .with_context(|| format!("failed to parse Hubble timestamp '{}'", raw))
}

fn parse_hubble_epoch(value: i64) -> Result<DateTime<Utc>> {
    if value.abs() >= 1_000_000_000_000 {
        chrono::DateTime::<Utc>::from_timestamp_millis(value)
            .ok_or_else(|| anyhow!("invalid millisecond timestamp '{}'", value))
    } else {
        chrono::DateTime::<Utc>::from_timestamp(value, 0)
            .ok_or_else(|| anyhow!("invalid second timestamp '{}'", value))
    }
}

fn parse_hubble_f64(value: Option<&Value>) -> Option<f64> {
    value.and_then(parse_hubble_f64_value)
}

fn parse_hubble_f64_value(value: &Value) -> Option<f64> {
    match value {
        Value::Number(number) => number.as_f64(),
        Value::String(raw) => raw.trim().parse::<f64>().ok(),
        _ => None,
    }
}

fn parse_hubble_expiration(raw: &str) -> Option<NaiveDate> {
    NaiveDate::parse_from_str(raw, "%Y-%m-%d")
        .or_else(|_| NaiveDate::parse_from_str(raw, "%Y%m%d"))
        .ok()
}

fn ratio_or_none(numerator: f64, denominator: f64) -> Option<f64> {
    (denominator.abs() > f64::EPSILON).then_some(numerator / denominator)
}

fn fetch_ibkr_historical_candles(
    contract: &MarketDataHarnessIbkrSpec,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
) -> Result<Vec<Candle>> {
    let script = std::env::var(CONTROL_MATRIX_IBKR_FETCH_SCRIPT_ENV).unwrap_or_else(|_| {
        format!(
            "{}/support/scripts/auto_quant_external/fetch_external.py",
            env!("CARGO_MANIFEST_DIR")
        )
    });
    let temp = std::env::temp_dir().join(format!(
        "ict-engine-ibkr-{}-{}.csv",
        contract.symbol.to_ascii_lowercase(),
        Utc::now().timestamp_nanos_opt().unwrap_or_default()
    ));
    let args = build_ibkr_historical_args(
        &script,
        contract,
        interval,
        start,
        end,
        temp.to_str().unwrap_or("ibkr.csv"),
        selected_ibkr_gateway_port(),
    );
    let output = Command::new("python3")
        .args(args.iter().map(String::as_str))
        .output()
        .with_context(|| {
            format!(
                "failed to spawn ibkr historical fetch for '{}'",
                contract.symbol
            )
        })?;
    if !output.status.success() {
        bail!(
            "ibkr historical fetch failed for '{}'{}",
            contract.symbol,
            command_output_excerpt(&output, Some(ibkr_gateway_agent_prompt())),
        );
    }
    let result = load_csv_candles(&temp);
    let _ = std::fs::remove_file(&temp);
    result
}

fn build_ibkr_historical_args(
    script: &str,
    contract: &MarketDataHarnessIbkrSpec,
    interval: &str,
    start: DateTime<Utc>,
    end: DateTime<Utc>,
    output: &str,
    gateway_port: Option<u16>,
) -> Vec<String> {
    let duration = ibkr_duration_from_range(start, end);
    let bar_size = ibkr_bar_size(interval);
    let mut args = vec![
        script.to_string(),
        "ibkr-historical".to_string(),
        "--symbol".to_string(),
        contract.symbol.clone(),
        "--sec-type".to_string(),
        contract.sec_type.clone(),
        "--exchange".to_string(),
        contract.exchange.clone(),
        "--currency".to_string(),
        contract.currency.clone(),
        "--bar-size".to_string(),
        bar_size,
        "--duration".to_string(),
        duration,
        "--output".to_string(),
        output.to_string(),
    ];
    if let Some(primary_exchange) = contract.primary_exchange.as_ref() {
        args.push("--primary-exchange".to_string());
        args.push(primary_exchange.clone());
    }
    if let Some(port) = gateway_port {
        args.push("--port".to_string());
        args.push(port.to_string());
    }
    args
}

fn selected_ibkr_gateway_port() -> Option<u16> {
    selected_ibkr_gateway_port_with(
        || std::env::var(CONTROL_MATRIX_IBKR_GATEWAY_PORT_ENV).ok(),
        home_dir().as_deref(),
        ibkr_gateway_port_reachable,
    )
}

fn selected_ibkr_gateway_port_with(
    env_lookup: impl Fn() -> Option<String>,
    home_dir: Option<&Path>,
    reachable: impl Fn(&str, u16) -> bool,
) -> Option<u16> {
    if let Some(port) = env_lookup().and_then(|value| value.trim().parse::<u16>().ok()) {
        return Some(port);
    }
    if let Some(cache) = read_cached_ibkr_gateway_port(home_dir) {
        if cache.host == IBKR_GATEWAY_HOST && reachable(&cache.host, cache.port) {
            return Some(cache.port);
        }
    }
    let selected = first_reachable_ibkr_gateway_port_with(IBKR_GATEWAY_HOST, &reachable);
    if let Some(port) = selected {
        write_cached_ibkr_gateway_port(home_dir, IBKR_GATEWAY_HOST, port);
    }
    selected
}

fn first_reachable_ibkr_gateway_port_with(
    host: &str,
    reachable: impl Fn(&str, u16) -> bool,
) -> Option<u16> {
    IBKR_GATEWAY_PORT_CANDIDATES
        .into_iter()
        .find(|port| reachable(host, *port))
}

fn ibkr_gateway_port_reachable(host: &str, port: u16) -> bool {
    let Ok(addr) = format!("{host}:{port}").parse::<SocketAddr>() else {
        return false;
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(150)).is_ok()
}

fn command_output_excerpt(output: &std::process::Output, suffix: Option<&str>) -> String {
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
    let excerpt = if !stderr.is_empty() { stderr } else { stdout };
    let base = if excerpt.is_empty() {
        String::new()
    } else {
        format!(
            ": {}",
            excerpt.lines().take(3).collect::<Vec<_>>().join(" | ")
        )
    };
    match suffix {
        Some(suffix) if !suffix.is_empty() && base.is_empty() => format!(": {suffix}"),
        Some(suffix) if !suffix.is_empty() => format!("{base} | {suffix}"),
        _ => base,
    }
}

fn ibkr_gateway_agent_prompt() -> &'static str {
    "IBKR gateway port guidance: run support/scripts/ibkr_bridge/setup.py --require-gateway once, or set ICT_ENGINE_IBKR_GATEWAY_PORT=<7497|7496|4002|4001>; market-data-harness caches a reachable auto-probed port in ~/.ict-engine/ibkr_gateway_port.json"
}

fn read_cached_ibkr_gateway_port(home_dir: Option<&Path>) -> Option<IbkrGatewayPortCache> {
    let path = ibkr_gateway_port_cache_path(home_dir)?;
    let content = std::fs::read_to_string(path).ok()?;
    serde_json::from_str(&content).ok()
}

fn write_cached_ibkr_gateway_port(home_dir: Option<&Path>, host: &str, port: u16) {
    let Some(path) = ibkr_gateway_port_cache_path(home_dir) else {
        return;
    };
    if let Some(parent) = path.parent() {
        let _ = std::fs::create_dir_all(parent);
    }
    let payload = IbkrGatewayPortCache {
        host: host.to_string(),
        port,
        source: "auto_probe".to_string(),
    };
    if let Ok(content) = serde_json::to_string_pretty(&payload) {
        let _ = std::fs::write(path, content);
    }
}

fn ibkr_gateway_port_cache_path(home_dir: Option<&Path>) -> Option<PathBuf> {
    home_dir.map(|home| home.join(IBKR_GATEWAY_PORT_CACHE_RELATIVE_PATH))
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}

fn fetch_tradingview_options_summary(symbol: &str) -> Result<OptionsChainSummary> {
    let expirations = TradingViewMcpClient::from_env_or_local().call_tool(
        "get_option_expirations",
        serde_json::json!({ "symbol": symbol }),
    )?;
    let first_expiration = expirations
        .pointer("/data/expirations")
        .and_then(Value::as_array)
        .and_then(|items| items.first())
        .and_then(|item| item.get("expiration"))
        .and_then(Value::as_str)
        .ok_or_else(|| {
            anyhow!(
                "tradingview returned no option expirations for '{}'",
                symbol
            )
        })?;
    let chain = TradingViewMcpClient::from_env_or_local().call_tool(
        "get_option_chain",
        serde_json::json!({
            "symbol": symbol,
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

fn load_csv_candles(path: &std::path::Path) -> Result<Vec<Candle>> {
    let mut reader = csv::Reader::from_path(path)
        .with_context(|| format!("failed to open generated candle csv '{}'", path.display()))?;
    let headers = reader.headers()?.clone();
    let ts_index = headers
        .iter()
        .position(|item| item.eq_ignore_ascii_case("date") || item.eq_ignore_ascii_case("ts"))
        .ok_or_else(|| anyhow!("csv missing date/ts column"))?;
    let open_index = headers
        .iter()
        .position(|item| item == "open")
        .ok_or_else(|| anyhow!("csv missing open"))?;
    let high_index = headers
        .iter()
        .position(|item| item == "high")
        .ok_or_else(|| anyhow!("csv missing high"))?;
    let low_index = headers
        .iter()
        .position(|item| item == "low")
        .ok_or_else(|| anyhow!("csv missing low"))?;
    let close_index = headers
        .iter()
        .position(|item| item == "close")
        .ok_or_else(|| anyhow!("csv missing close"))?;
    let volume_index = headers.iter().position(|item| item == "volume");
    let mut candles = Vec::new();
    for record in reader.records() {
        let record = record?;
        let timestamp = chrono::DateTime::parse_from_rfc3339(&record[ts_index])
            .or_else(|_| {
                chrono::DateTime::parse_from_str(&record[ts_index], "%Y-%m-%d %H:%M:%S%#z")
            })
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

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;

    #[test]
    fn ibkr_historical_args_include_configured_gateway_port() {
        let contract = MarketDataHarnessIbkrSpec {
            symbol: "QQQ".to_string(),
            sec_type: "STK".to_string(),
            exchange: "SMART".to_string(),
            currency: "USD".to_string(),
            primary_exchange: None,
        };
        let start = Utc.with_ymd_and_hms(2026, 4, 1, 0, 0, 0).unwrap();
        let end = Utc.with_ymd_and_hms(2026, 5, 1, 0, 0, 0).unwrap();

        let args = build_ibkr_historical_args(
            "support/scripts/auto_quant_external/fetch_external.py",
            &contract,
            "1d",
            start,
            end,
            "out.csv",
            Some(4002),
        );

        assert!(args.windows(2).any(|items| items == ["--port", "4002"]));
    }

    #[test]
    fn ibkr_gateway_selection_reuses_reachable_cached_port() {
        let home = tempfile::tempdir().unwrap();
        let config_dir = home.path().join(".ict-engine");
        std::fs::create_dir_all(&config_dir).unwrap();
        std::fs::write(
            config_dir.join("ibkr_gateway_port.json"),
            r#"{"host":"127.0.0.1","port":4002,"source":"auto_probe"}"#,
        )
        .unwrap();

        let selected = selected_ibkr_gateway_port_with(
            || None,
            Some(home.path()),
            |host, port| host == "127.0.0.1" && port == 4002,
        );

        assert_eq!(selected, Some(4002));
    }

    #[test]
    fn ibkr_gateway_selection_caches_first_reachable_port() {
        let home = tempfile::tempdir().unwrap();

        let selected = selected_ibkr_gateway_port_with(
            || None,
            Some(home.path()),
            |host, port| host == "127.0.0.1" && port == 4002,
        );

        assert_eq!(selected, Some(4002));
        let cache = read_cached_ibkr_gateway_port(Some(home.path())).unwrap();
        assert_eq!(cache.host, "127.0.0.1");
        assert_eq!(cache.port, 4002);
        assert_eq!(cache.source, "auto_probe");
    }

    #[test]
    fn hubble_candle_request_uses_market_specific_paths() {
        let spec = MarketDataHarnessHubbleSpec {
            symbol: "SPY".to_string(),
            market: "us".to_string(),
            exchange: None,
        };
        let start = Utc.with_ymd_and_hms(2026, 4, 1, 0, 0, 0).unwrap();
        let end = Utc.with_ymd_and_hms(2026, 5, 1, 0, 0, 0).unwrap();

        let (path, params) = build_hubble_candle_request(&spec, "1d", start, end, 50).unwrap();

        assert_eq!(path, "/api/v2/usstock/stocks");
        assert!(params
            .iter()
            .any(|item| item == &("symbol".to_string(), "SPY".to_string())));
        assert!(params
            .iter()
            .any(|item| item == &("limit".to_string(), "50".to_string())));
    }

    #[test]
    fn hubble_candle_request_requires_crypto_exchange() {
        let spec = MarketDataHarnessHubbleSpec {
            symbol: "BTCUSDT".to_string(),
            market: "crypto".to_string(),
            exchange: None,
        };
        let start = Utc.with_ymd_and_hms(2026, 4, 1, 0, 0, 0).unwrap();
        let end = Utc.with_ymd_and_hms(2026, 5, 1, 0, 0, 0).unwrap();

        let result = build_hubble_candle_request(&spec, "1h", start, end, 200);

        assert!(result.is_err());
    }

    #[test]
    fn parse_hubble_options_payload_summarizes_call_put_rows() {
        let payload = serde_json::json!({
            "data": {
                "data": [
                    {
                        "symbol": "AAPL",
                        "expiration": "2026-06-19",
                        "strike": "200.0",
                        "type": "call",
                        "volume": "10",
                        "open_interest": "20",
                        "delta": "0.52",
                        "gamma": "0.10",
                        "vega": "0.20",
                        "iv": "0.31"
                    },
                    {
                        "symbol": "AAPL",
                        "expiration": "2026-06-19",
                        "strike": "200.0",
                        "type": "put",
                        "volume": "5",
                        "open_interest": "8",
                        "delta": "-0.48",
                        "gamma": "0.08",
                        "vega": "0.18",
                        "iv": "0.29"
                    }
                ],
                "underlying_price": 200.0
            }
        });

        let summary = parse_hubble_options_summary("AAPL", &payload).unwrap();

        assert_eq!(summary.symbol, "AAPL");
        assert_eq!(summary.call_open_interest, 20.0);
        assert_eq!(summary.put_open_interest, 8.0);
        assert_eq!(summary.call_volume, 10.0);
        assert_eq!(summary.put_volume, 5.0);
        assert_eq!(summary.put_call_oi_ratio, Some(0.4));
        assert_eq!(summary.put_call_volume_ratio, Some(0.5));
        assert_eq!(summary.near_atm_delta, Some(0.52));
        assert_eq!(summary.near_atm_gamma, Some(0.10));
        assert_eq!(summary.near_atm_vega, Some(0.20));
        assert_eq!(summary.near_atm_implied_volatility, Some(0.31));
        assert_eq!(summary.call_gamma_oi, Some(2.0));
        assert_eq!(summary.put_gamma_oi, Some(0.64));
    }
}
