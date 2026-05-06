use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, TimeDelta, Utc};
use reqwest::blocking::Client;
use serde_json::Value;
use std::process::Command;

use super::control_matrix_providers::{
    TVREMIX_MCP_API_KEY_ENV, TVREMIX_MCP_DEFAULT_URL, TVREMIX_MCP_URL_ENV,
};
use super::harness::{MarketDataHarnessIbkrSpec, MarketDataHarnessTask, ProviderExecutionRequest};
use crate::data::realtime::market_support::{OptionsChainSummary, SpotInstrumentKind};
use crate::data::realtime::yfinance_runtime::YahooFinanceProvider;
use crate::types::Candle;

pub(crate) const CONTROL_MATRIX_IBKR_FETCH_SCRIPT_ENV: &str = "ICT_ENGINE_IBKR_FETCH_SCRIPT";

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
        ProviderExecutionRequest::TradingViewMcp { symbol } => {
            fetch_tradingview_ohlcv(symbol, interval, start, end, count)
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
        ProviderExecutionRequest::TradingViewMcp { symbol } => {
            fetch_tradingview_options_summary(symbol)
        }
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

fn fetch_ibkr_historical_candles(
    contract: &MarketDataHarnessIbkrSpec,
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
        contract.symbol.to_ascii_lowercase(),
        Utc::now().timestamp_nanos_opt().unwrap_or_default()
    ));
    let duration = ibkr_duration_from_range(start, end);
    let bar_size = ibkr_bar_size(interval);
    let mut args = vec![
        script,
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
        temp.to_str().unwrap_or("ibkr.csv").to_string(),
    ];
    if let Some(primary_exchange) = contract.primary_exchange.as_ref() {
        args.push("--primary-exchange".to_string());
        args.push(primary_exchange.clone());
    }
    let status = Command::new("python3")
        .args(args.iter().map(String::as_str))
        .status()
        .with_context(|| {
            format!(
                "failed to spawn ibkr historical fetch for '{}'",
                contract.symbol
            )
        })?;
    if !status.success() {
        bail!("ibkr historical fetch failed for '{}'", contract.symbol);
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
    count: usize,
) -> Result<Vec<Candle>> {
    let payload = call_tradingview_tool(
        "get_ohlcv",
        serde_json::json!({
            "symbol": symbol,
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
    let expirations = call_tradingview_tool(
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
    let chain = call_tradingview_tool(
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

fn call_tradingview_tool(name: &str, arguments: Value) -> Result<Value> {
    let key = std::env::var(TVREMIX_MCP_API_KEY_ENV).with_context(|| {
        format!(
            "{} must be set for tradingview_mcp",
            TVREMIX_MCP_API_KEY_ENV
        )
    })?;
    let url =
        std::env::var(TVREMIX_MCP_URL_ENV).unwrap_or_else(|_| TVREMIX_MCP_DEFAULT_URL.to_string());
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
