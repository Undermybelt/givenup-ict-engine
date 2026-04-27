use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, TimeDelta, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use std::path::Path;

use super::control_matrix_providers::{
    build_provider_summary_for_requirements, ControlMatrixDataRequirement,
    ControlMatrixProviderSummary,
};
use crate::types::Candle;

use super::control_matrix_runtime::{
    fetch_options_summary_for_provider_symbol, fetch_reference_candles_for_provider_symbol,
};

pub const MARKET_DATA_HARNESS_PRESETS_FILE: &str = "config/market_data_harness_presets.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessPresetConfig {
    pub version: u32,
    #[serde(default)]
    pub markets: Vec<MarketDataHarnessPreset>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessPreset {
    pub market_key: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    #[serde(default)]
    pub related: BTreeMap<String, MarketDataHarnessSymbolSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessIbkrSpec {
    pub symbol: String,
    pub sec_type: String,
    pub exchange: String,
    #[serde(default)]
    pub currency: String,
    #[serde(default)]
    pub primary_exchange: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessSymbolSpec {
    #[serde(default)]
    pub display_symbol: Option<String>,
    #[serde(default)]
    pub yfinance: Option<String>,
    #[serde(default)]
    pub tradingview_mcp: Option<String>,
    #[serde(default)]
    pub ibkr: Option<MarketDataHarnessIbkrSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessRequest {
    pub market_key: String,
    #[serde(default)]
    pub primary_data_path: Option<String>,
    #[serde(default)]
    pub interval: Option<String>,
    #[serde(default)]
    pub start: Option<DateTime<Utc>>,
    #[serde(default)]
    pub end: Option<DateTime<Utc>>,
    #[serde(default)]
    pub count: Option<usize>,
    #[serde(default)]
    pub related_roles: Vec<String>,
    #[serde(default)]
    pub provider_preferences: BTreeMap<String, String>,
    #[serde(default)]
    pub symbol_overrides: BTreeMap<String, MarketDataHarnessSymbolSpec>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum MarketDataHarnessOperation {
    Ohlcv,
    Quote,
    OptionsSummary,
}

impl MarketDataHarnessOperation {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Ohlcv => "ohlcv.fetch",
            Self::Quote => "quote.fetch",
            Self::OptionsSummary => "options.summary",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessTask {
    pub role: String,
    pub provider: String,
    pub operation: MarketDataHarnessOperation,
    pub symbol: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessPlan {
    pub request: MarketDataHarnessRequest,
    pub provider_summary: ControlMatrixProviderSummary,
    pub tasks: Vec<MarketDataHarnessTask>,
    pub missing_roles: Vec<String>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessError {
    pub category: String,
    pub message: String,
    pub retryable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessEnvelope {
    pub ok: bool,
    pub provider: String,
    pub operation: String,
    pub role: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub symbol: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub data: Option<Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<MarketDataHarnessError>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessBundle {
    pub plan: MarketDataHarnessPlan,
    pub results: Vec<MarketDataHarnessEnvelope>,
}

pub fn load_market_data_harness_preset_config<P: AsRef<Path>>(
    repo_root: P,
) -> Result<MarketDataHarnessPresetConfig> {
    let path = repo_root.as_ref().join(MARKET_DATA_HARNESS_PRESETS_FILE);
    let raw = std::fs::read_to_string(&path).with_context(|| {
        format!(
            "failed to read market data harness preset config '{}'",
            path.display()
        )
    })?;
    serde_json::from_str(&raw).with_context(|| {
        format!(
            "failed to parse market data harness preset config '{}'",
            path.display()
        )
    })
}

pub fn repo_root_from_harness() -> std::path::PathBuf {
    std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

pub fn build_market_data_harness_plan(
    request: MarketDataHarnessRequest,
    config: &MarketDataHarnessPresetConfig,
) -> Result<MarketDataHarnessPlan> {
    let preset = find_matching_preset(config, &request.market_key);
    let required_requirements = request
        .related_roles
        .iter()
        .filter_map(|role| requirement_for_role(role))
        .collect::<std::collections::BTreeSet<_>>();
    let provider_summary = build_provider_summary_for_requirements(required_requirements);
    let interval = resolve_interval(&request)?;
    let (start, end) = resolve_range(&request)?;
    let count = request
        .count
        .unwrap_or_else(|| estimate_count_from_range(&interval, start, end));
    let mut tasks = Vec::new();
    let mut missing_roles = Vec::new();
    let mut warnings = Vec::new();
    for role in &request.related_roles {
        let operation = operation_for_role(role);
        let symbol_spec = request
            .symbol_overrides
            .get(role)
            .cloned()
            .or_else(|| preset.and_then(|item| item.related.get(role).cloned()));
        let Some(symbol_spec) = symbol_spec else {
            missing_roles.push(role.clone());
            warnings.push(format!("missing_symbol_spec_for_role={role}"));
            continue;
        };
        let provider = resolve_provider_for_role(role, &request, &provider_summary)?;
        let symbol = render_symbol_for_provider(&symbol_spec, &provider)?;
        match operation {
            MarketDataHarnessOperation::Ohlcv | MarketDataHarnessOperation::Quote => tasks.push(
                MarketDataHarnessTask {
                    role: role.clone(),
                    provider,
                    operation,
                    symbol,
                },
            ),
            MarketDataHarnessOperation::OptionsSummary => {
                tasks.push(MarketDataHarnessTask {
                    role: role.clone(),
                    provider,
                    operation,
                    symbol,
                });
            }
        }
        let _ = count;
    }
    Ok(MarketDataHarnessPlan {
        request,
        provider_summary,
        tasks,
        missing_roles,
        warnings,
    })
}

pub fn execute_market_data_harness_plan(plan: &MarketDataHarnessPlan) -> Result<MarketDataHarnessBundle> {
    let interval = resolve_interval(&plan.request)?;
    let (start, end) = resolve_range(&plan.request)?;
    let count = plan
        .request
        .count
        .unwrap_or_else(|| estimate_count_from_range(&interval, start, end));
    let mut results = Vec::new();
    for task in &plan.tasks {
        let result = match task.operation {
            MarketDataHarnessOperation::Ohlcv => {
                match fetch_reference_candles_for_provider_symbol(
                    &task.provider,
                    &task.symbol,
                    &interval,
                    start,
                    end,
                    count,
                ) {
                    Ok(candles) => MarketDataHarnessEnvelope {
                        ok: true,
                        provider: task.provider.clone(),
                        operation: task.operation.as_str().to_string(),
                        role: task.role.clone(),
                        symbol: Some(task.symbol.clone()),
                        data: Some(serde_json::to_value(&candles)?),
                        error: None,
                    },
                    Err(err) => harness_error_envelope(task, "fetch_failed", &err.to_string(), true),
                }
            }
            MarketDataHarnessOperation::OptionsSummary => {
                match fetch_options_summary_for_provider_symbol(&task.provider, &task.symbol) {
                    Ok(summary) => MarketDataHarnessEnvelope {
                        ok: true,
                        provider: task.provider.clone(),
                        operation: task.operation.as_str().to_string(),
                        role: task.role.clone(),
                        symbol: Some(task.symbol.clone()),
                        data: Some(serde_json::to_value(&summary)?),
                        error: None,
                    },
                    Err(err) => harness_error_envelope(task, "fetch_failed", &err.to_string(), true),
                }
            }
            MarketDataHarnessOperation::Quote => harness_error_envelope(
                task,
                "unsupported_operation",
                "quote.fetch is not implemented yet",
                false,
            ),
        };
        results.push(result);
    }
    Ok(MarketDataHarnessBundle {
        plan: plan.clone(),
        results,
    })
}

fn harness_error_envelope(
    task: &MarketDataHarnessTask,
    category: &str,
    message: &str,
    retryable: bool,
) -> MarketDataHarnessEnvelope {
    MarketDataHarnessEnvelope {
        ok: false,
        provider: task.provider.clone(),
        operation: task.operation.as_str().to_string(),
        role: task.role.clone(),
        symbol: Some(task.symbol.clone()),
        data: None,
        error: Some(MarketDataHarnessError {
            category: category.to_string(),
            message: message.to_string(),
            retryable,
        }),
    }
}

fn find_matching_preset<'a>(
    config: &'a MarketDataHarnessPresetConfig,
    market_key: &str,
) -> Option<&'a MarketDataHarnessPreset> {
    let normalized = market_key.trim().to_ascii_lowercase();
    config.markets.iter().find(|preset| {
        preset.market_key.eq_ignore_ascii_case(&normalized)
            || preset.aliases.iter().any(|alias| alias.eq_ignore_ascii_case(&normalized))
    })
}

fn resolve_provider_for_role(
    role: &str,
    request: &MarketDataHarnessRequest,
    provider_summary: &ControlMatrixProviderSummary,
) -> Result<String> {
    if let Some(preferred) = request.provider_preferences.get(role) {
        return Ok(preferred.clone());
    }
    let available = provider_summary
        .provider_statuses
        .iter()
        .filter(|provider| provider.healthy)
        .map(|provider| provider.provider.as_str())
        .collect::<Vec<_>>();
    let requirement = requirement_for_role(role);
    let provider = match requirement {
        Some(ControlMatrixDataRequirement::OptionsGreeks) => {
            choose_provider(&available, &["tradingview_mcp", "yfinance", "ibkr"])
        }
        Some(ControlMatrixDataRequirement::OptionsOpenInterest) => {
            choose_provider(&available, &["yfinance", "tradingview_mcp", "ibkr"])
        }
        Some(ControlMatrixDataRequirement::OptionsImpliedVolatility) => {
            choose_provider(&available, &["tradingview_mcp", "yfinance", "ibkr"])
        }
        Some(ControlMatrixDataRequirement::CfdReference) => {
            choose_provider(&available, &["tradingview_mcp", "ibkr", "yfinance"])
        }
        _ => choose_provider(&available, &["yfinance", "tradingview_mcp", "ibkr"]),
    };
    provider
        .map(str::to_string)
        .ok_or_else(|| anyhow!("no provider available for role '{}'", role))
}

fn choose_provider<'a>(available: &[&'a str], preferred: &[&'a str]) -> Option<&'a str> {
    preferred.iter().copied().find(|item| available.contains(item))
}

fn render_symbol_for_provider(spec: &MarketDataHarnessSymbolSpec, provider: &str) -> Result<String> {
    match provider {
        "yfinance" => spec
            .yfinance
            .clone()
            .or_else(|| spec.display_symbol.clone())
            .ok_or_else(|| anyhow!("missing yfinance symbol")),
        "tradingview_mcp" => spec
            .tradingview_mcp
            .clone()
            .or_else(|| spec.display_symbol.clone())
            .ok_or_else(|| anyhow!("missing tradingview symbol")),
        "ibkr" => spec
            .ibkr
            .as_ref()
            .map(|item| item.symbol.clone())
            .or_else(|| spec.display_symbol.clone())
            .ok_or_else(|| anyhow!("missing ibkr symbol")),
        other => bail!("unsupported provider '{}'", other),
    }
}

fn resolve_interval(request: &MarketDataHarnessRequest) -> Result<String> {
    if let Some(interval) = request.interval.as_ref().filter(|value| !value.trim().is_empty()) {
        return Ok(interval.clone());
    }
    if let Some(path) = request.primary_data_path.as_deref() {
        let candles = crate::data::load_candles(path)?;
        return Ok(infer_interval_from_candles(&candles));
    }
    Ok("1d".to_string())
}

fn resolve_range(request: &MarketDataHarnessRequest) -> Result<(DateTime<Utc>, DateTime<Utc>)> {
    if let (Some(start), Some(end)) = (request.start, request.end) {
        return Ok((start, end));
    }
    if let Some(path) = request.primary_data_path.as_deref() {
        let candles = crate::data::load_candles(path)?;
        let start = candles
            .first()
            .map(|item| item.timestamp)
            .ok_or_else(|| anyhow!("primary_data_path contains no candles"))?;
        let end = candles
            .last()
            .map(|item| item.timestamp)
            .ok_or_else(|| anyhow!("primary_data_path contains no candles"))?;
        return Ok((start, end));
    }
    let end = Utc::now();
    Ok((end - TimeDelta::days(30), end))
}

fn infer_interval_from_candles(candles: &[Candle]) -> String {
    if candles.len() < 2 {
        return "1d".to_string();
    }
    let minutes = candles[1]
        .timestamp
        .signed_duration_since(candles[0].timestamp)
        .num_minutes()
        .abs();
    match minutes {
        1 => "1m",
        2 => "2m",
        5 => "5m",
        15 => "15m",
        30 => "30m",
        60 => "1h",
        90 => "90m",
        1440 => "1d",
        _ if minutes >= 1440 => "1d",
        _ => "1h",
    }
    .to_string()
}

fn estimate_count_from_range(interval: &str, start: DateTime<Utc>, end: DateTime<Utc>) -> usize {
    let minutes = (end - start).num_minutes().max(1) as usize;
    let divisor = match interval {
        "1m" => 1,
        "2m" => 2,
        "5m" => 5,
        "15m" => 15,
        "30m" => 30,
        "1h" | "60m" => 60,
        "90m" => 90,
        "1d" => 1440,
        _ => 1440,
    };
    (minutes / divisor).clamp(10, 5_000)
}

fn operation_for_role(role: &str) -> MarketDataHarnessOperation {
    if role.starts_with("options") {
        MarketDataHarnessOperation::OptionsSummary
    } else if role.ends_with("_quote") {
        MarketDataHarnessOperation::Quote
    } else {
        MarketDataHarnessOperation::Ohlcv
    }
}

fn requirement_for_role(role: &str) -> Option<ControlMatrixDataRequirement> {
    match role {
        "etf_reference" => Some(ControlMatrixDataRequirement::EtfReference),
        "cfd_reference" => Some(ControlMatrixDataRequirement::CfdReference),
        "volatility_reference" | "vix_overlay" => Some(ControlMatrixDataRequirement::VixOverlay),
        "options_greeks" => Some(ControlMatrixDataRequirement::OptionsGreeks),
        "options_oi" => Some(ControlMatrixDataRequirement::OptionsOpenInterest),
        "options_iv" => Some(ControlMatrixDataRequirement::OptionsImpliedVolatility),
        "options_underlying" => Some(ControlMatrixDataRequirement::OptionsImpliedVolatility),
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn plan_uses_preset_and_provider_preferences() {
        let config = MarketDataHarnessPresetConfig {
            version: 1,
            markets: vec![MarketDataHarnessPreset {
                market_key: "NQ".to_string(),
                aliases: vec!["NASDAQ_FUTURES".to_string()],
                related: BTreeMap::from([
                    (
                        "etf_reference".to_string(),
                        MarketDataHarnessSymbolSpec {
                            yfinance: Some("QQQ".to_string()),
                            tradingview_mcp: Some("NASDAQ:QQQ".to_string()),
                            ..MarketDataHarnessSymbolSpec::default()
                        },
                    ),
                    (
                        "options_underlying".to_string(),
                        MarketDataHarnessSymbolSpec {
                            yfinance: Some("QQQ".to_string()),
                            tradingview_mcp: Some("NASDAQ:QQQ".to_string()),
                            ..MarketDataHarnessSymbolSpec::default()
                        },
                    ),
                ]),
            }],
        };
        let plan = build_market_data_harness_plan(
            MarketDataHarnessRequest {
                market_key: "NQ".to_string(),
                primary_data_path: None,
                interval: Some("1d".to_string()),
                start: Some(Utc::now() - TimeDelta::days(10)),
                end: Some(Utc::now()),
                count: Some(20),
                related_roles: vec!["etf_reference".to_string(), "options_underlying".to_string()],
                provider_preferences: BTreeMap::from([(
                    "options_underlying".to_string(),
                    "tradingview_mcp".to_string(),
                )]),
                symbol_overrides: BTreeMap::new(),
            },
            &config,
        )
        .unwrap();
        assert_eq!(plan.tasks.len(), 2);
        assert!(plan
            .tasks
            .iter()
            .any(|task| task.role == "etf_reference" && task.provider == "yfinance"));
        assert!(plan
            .tasks
            .iter()
            .any(|task| task.role == "options_underlying" && task.provider == "tradingview_mcp"));
    }
}
