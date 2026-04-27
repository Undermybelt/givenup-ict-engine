use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, TimeDelta, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use std::path::Path;

use super::control_matrix_providers::{
    build_provider_summary_for_requirements, ControlMatrixDataRequirement, ControlMatrixProviderSummary,
};
use super::provider_fetch::{
    fetch_options_summary_for_task, fetch_reference_candles_for_task,
};
use crate::market_catalog::MarketCatalog;
use crate::types::Candle;

pub const MARKET_DATA_HARNESS_PRESETS_FILE: &str = "config/market_data_harness_presets.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessPresetConfig {
    pub version: u32,
    #[serde(default)]
    pub markets: Vec<MarketDataHarnessPreset>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketLiveDefaultsSpec {
    pub futures_symbol: String,
    pub spot_role: String,
    pub options_role: String,
    pub spot_kind: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MarketDataHarnessPreset {
    pub market_key: String,
    #[serde(default)]
    pub aliases: Vec<String>,
    #[serde(default)]
    pub live_defaults: Option<MarketLiveDefaultsSpec>,
    #[serde(default)]
    pub related: BTreeMap<String, MarketDataHarnessSymbolSpec>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum ProviderExecutionRequest {
    YahooFinance { symbol: String },
    TradingViewMcp { symbol: String },
    Ibkr { contract: MarketDataHarnessIbkrSpec },
}

impl ProviderExecutionRequest {
    pub fn symbol(&self) -> &str {
        match self {
            Self::YahooFinance { symbol } | Self::TradingViewMcp { symbol } => symbol,
            Self::Ibkr { contract } => &contract.symbol,
        }
    }

    pub fn ibkr_contract(&self) -> Option<&MarketDataHarnessIbkrSpec> {
        match self {
            Self::Ibkr { contract } => Some(contract),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDataHarnessTask {
    pub role: String,
    pub provider: String,
    pub operation: MarketDataHarnessOperation,
    pub symbol: String,
    pub request: ProviderExecutionRequest,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub fallback_options_proxy_symbol: Option<String>,
}

impl MarketDataHarnessTask {
    pub fn request_symbol(&self) -> &str {
        self.request.symbol()
    }

    pub fn ibkr_contract(&self) -> Option<&MarketDataHarnessIbkrSpec> {
        self.request.ibkr_contract()
    }
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
    catalog: &MarketCatalog,
) -> Result<MarketDataHarnessPlan> {
    let preset = find_matching_preset(&catalog.presets, &request.market_key);
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
        let provider = match resolve_provider_for_role(role, &request, &provider_summary) {
            Ok(provider) => provider,
            Err(err) => {
                missing_roles.push(role.clone());
                warnings.push(format!("missing_provider_for_role={role}"));
                warnings.push(err.to_string());
                continue;
            }
        };
        let symbol = match display_symbol_for_spec(&symbol_spec) {
            Ok(symbol) => symbol,
            Err(err) => {
                missing_roles.push(role.clone());
                warnings.push(format!("missing_display_symbol_for_role={role}"));
                warnings.push(err.to_string());
                continue;
            }
        };
        let provider_request = match build_provider_request(&symbol_spec, &provider) {
            Ok(provider_request) => provider_request,
            Err(err) => {
                missing_roles.push(role.clone());
                warnings.push(format!("missing_provider_symbol_for_role={role}"));
                warnings.push(err.to_string());
                continue;
            }
        };
        let fallback_options_proxy_symbol =
            if matches!(operation, MarketDataHarnessOperation::OptionsSummary) {
                catalog
                    .relationships(&request.market_key)
                    .and_then(|item| item.options_volatility_proxy.clone())
            } else {
                None
            };
        match operation {
            MarketDataHarnessOperation::Ohlcv | MarketDataHarnessOperation::Quote => tasks.push(
                MarketDataHarnessTask {
                    role: role.clone(),
                    provider,
                    operation,
                    symbol,
                    request: provider_request,
                    fallback_options_proxy_symbol,
                },
            ),
            MarketDataHarnessOperation::OptionsSummary => {
                tasks.push(MarketDataHarnessTask {
                    role: role.clone(),
                    provider,
                    operation,
                    symbol,
                    request: provider_request,
                    fallback_options_proxy_symbol,
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
                match fetch_reference_candles_for_task(task, &interval, start, end, count) {
                    Ok(candles) => MarketDataHarnessEnvelope {
                        ok: true,
                        provider: task.provider.clone(),
                        operation: task.operation.as_str().to_string(),
                        role: task.role.clone(),
                        symbol: Some(task.request_symbol().to_string()),
                        data: Some(serde_json::to_value(&candles)?),
                        error: None,
                    },
                    Err(err) => harness_error_envelope(task, "fetch_failed", &err.to_string(), true),
                }
            }
            MarketDataHarnessOperation::OptionsSummary => {
                match fetch_options_summary_for_task(task) {
                    Ok(summary) => MarketDataHarnessEnvelope {
                        ok: true,
                        provider: task.provider.clone(),
                        operation: task.operation.as_str().to_string(),
                        role: task.role.clone(),
                        symbol: Some(task.request_symbol().to_string()),
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
        symbol: Some(task.request_symbol().to_string()),
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
    let requirement = requirement_for_role(role);
    let available = healthy_supported_provider_names(provider_summary, requirement);
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

fn healthy_supported_provider_names(
    provider_summary: &ControlMatrixProviderSummary,
    requirement: Option<ControlMatrixDataRequirement>,
) -> Vec<&str> {
    provider_summary
        .provider_statuses
        .iter()
        .filter(|provider| provider.healthy)
        .filter(|provider| {
            requirement.is_none_or(|requirement| {
                provider
                    .supported_requirements
                    .iter()
                    .any(|item| item == requirement.as_str())
            })
        })
        .map(|provider| provider.provider.as_str())
        .collect()
}

fn choose_provider<'a>(available: &[&'a str], preferred: &[&'a str]) -> Option<&'a str> {
    preferred.iter().copied().find(|item| available.contains(item))
}

fn display_symbol_for_spec(spec: &MarketDataHarnessSymbolSpec) -> Result<String> {
    spec.display_symbol
        .clone()
        .or_else(|| spec.yfinance.clone())
        .or_else(|| spec.tradingview_mcp.clone())
        .or_else(|| spec.ibkr.as_ref().map(|item| item.symbol.clone()))
        .ok_or_else(|| anyhow!("missing display symbol"))
}

fn build_provider_request(spec: &MarketDataHarnessSymbolSpec, provider: &str) -> Result<ProviderExecutionRequest> {
    match provider {
        "yfinance" => spec
            .yfinance
            .clone()
            .map(|symbol| ProviderExecutionRequest::YahooFinance { symbol })
            .ok_or_else(|| anyhow!("missing yfinance symbol")),
        "tradingview_mcp" => spec
            .tradingview_mcp
            .clone()
            .map(|symbol| ProviderExecutionRequest::TradingViewMcp { symbol })
            .ok_or_else(|| anyhow!("missing tradingview symbol")),
        "ibkr" => spec
            .ibkr
            .as_ref()
            .cloned()
            .map(|contract| ProviderExecutionRequest::Ibkr { contract })
            .ok_or_else(|| anyhow!("missing ibkr contract")),
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
    use crate::market_catalog::{MarketCatalog, MarketRelationshipConfig};

    #[test]
    fn plan_uses_preset_and_provider_preferences() {
        let catalog = MarketCatalog {
            presets: MarketDataHarnessPresetConfig {
                version: 1,
                markets: vec![MarketDataHarnessPreset {
                market_key: "NQ".to_string(),
                aliases: vec!["NASDAQ_FUTURES".to_string()],
                live_defaults: None,
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
            },
            relationships: MarketRelationshipConfig::default(),
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
            &catalog,
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
        let etf = plan
            .tasks
            .iter()
            .find(|task| task.role == "etf_reference")
            .unwrap();
        assert_eq!(etf.request_symbol(), "QQQ");
        let options = plan
            .tasks
            .iter()
            .find(|task| task.role == "options_underlying")
            .unwrap();
        assert_eq!(options.fallback_options_proxy_symbol, None);
    }

    #[test]
    fn provider_selection_only_uses_healthy_supported_providers() {
        let summary = ControlMatrixProviderSummary {
            required_requirements: vec!["cfd_reference".to_string()],
            provider_statuses: vec![
                crate::application::data_sources::ControlMatrixProviderStatus {
                    provider: "yfinance".to_string(),
                    status: "ready".to_string(),
                    healthy: true,
                    reason: "public".to_string(),
                    supported_requirements: vec!["etf_reference".to_string()],
                    install_prompts: Vec::new(),
                    redacted_config: Vec::new(),
                },
                crate::application::data_sources::ControlMatrixProviderStatus {
                    provider: "ibkr".to_string(),
                    status: "install_required".to_string(),
                    healthy: false,
                    reason: "probe_failed".to_string(),
                    supported_requirements: vec!["cfd_reference".to_string()],
                    install_prompts: Vec::new(),
                    redacted_config: Vec::new(),
                },
            ],
            actionable_install_prompts: Vec::new(),
        };
        let request = MarketDataHarnessRequest {
            market_key: "ES".to_string(),
            primary_data_path: None,
            interval: Some("1d".to_string()),
            start: None,
            end: None,
            count: Some(10),
            related_roles: vec!["cfd_reference".to_string()],
            provider_preferences: BTreeMap::new(),
            symbol_overrides: BTreeMap::new(),
        };
        let result = resolve_provider_for_role("cfd_reference", &request, &summary);
        assert!(result.is_err());
    }
}
