use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use crate::application::backtest::{ControlMatrixPlan, PB12_TOGGLES, Pb12Toggle};

pub const TVREMIX_MCP_DEFAULT_URL: &str = "https://tvremix.xyz/api/mcp/v1";
pub const TVREMIX_MCP_URL_ENV: &str = "ICT_ENGINE_TVREMIX_MCP_URL";
pub const TVREMIX_MCP_API_KEY_ENV: &str = "ICT_ENGINE_TVREMIX_MCP_API_KEY";
pub const IBKR_CONSENT_RELATIVE_PATH: &str = ".ict-engine/ibkr_consent.json";
pub const IBKR_CAPABILITIES_RELATIVE_PATH: &str = ".ict-engine/ibkr_capabilities.json";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum ControlMatrixDataRequirement {
    EtfReference,
    CfdReference,
    VixOverlay,
    OptionsGreeks,
    OptionsOpenInterest,
    OptionsImpliedVolatility,
}

impl ControlMatrixDataRequirement {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::EtfReference => "etf_reference",
            Self::CfdReference => "cfd_reference",
            Self::VixOverlay => "vix_overlay",
            Self::OptionsGreeks => "options_greeks",
            Self::OptionsOpenInterest => "options_open_interest",
            Self::OptionsImpliedVolatility => "options_implied_volatility",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ControlMatrixProviderKind {
    Ibkr,
    YahooFinance,
    TradingViewMcp,
}

impl ControlMatrixProviderKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Ibkr => "ibkr",
            Self::YahooFinance => "yfinance",
            Self::TradingViewMcp => "tradingview_mcp",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ControlMatrixProviderStatus {
    pub provider: String,
    pub status: String,
    pub healthy: bool,
    pub reason: String,
    pub supported_requirements: Vec<String>,
    pub install_prompts: Vec<String>,
    pub redacted_config: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct ControlMatrixProviderSummary {
    pub required_requirements: Vec<String>,
    pub provider_statuses: Vec<ControlMatrixProviderStatus>,
    pub actionable_install_prompts: Vec<String>,
}

pub fn build_control_matrix_provider_summary(plan: &ControlMatrixPlan) -> ControlMatrixProviderSummary {
    build_provider_summary_for_requirements_with_env(
        required_requirements_for_plan(plan),
        &|name| std::env::var(name).ok(),
        home_dir(),
        &ibkr_runtime_ready,
    )
}

pub fn build_provider_summary_for_requirements(
    required: BTreeSet<ControlMatrixDataRequirement>,
) -> ControlMatrixProviderSummary {
    build_provider_summary_for_requirements_with_env(
        required,
        &|name| std::env::var(name).ok(),
        home_dir(),
        &ibkr_runtime_ready,
    )
}

fn build_provider_summary_for_requirements_with_env<F>(
    required: BTreeSet<ControlMatrixDataRequirement>,
    env_lookup: &F,
    home_dir: Option<PathBuf>,
    ibkr_runtime_probe: &dyn Fn() -> bool,
) -> ControlMatrixProviderSummary
where
    F: Fn(&str) -> Option<String>,
{
    let provider_statuses = vec![
        ibkr_provider_status(&required, home_dir.as_deref(), ibkr_runtime_probe()),
        yfinance_provider_status(&required, env_lookup),
        tradingview_mcp_provider_status(&required, env_lookup),
    ];
    let actionable_install_prompts = provider_statuses
        .iter()
        .flat_map(|status| status.install_prompts.iter().cloned())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    ControlMatrixProviderSummary {
        required_requirements: required.iter().map(|item| item.as_str().to_string()).collect(),
        provider_statuses,
        actionable_install_prompts,
    }
}

fn required_requirements_for_plan(plan: &ControlMatrixPlan) -> BTreeSet<ControlMatrixDataRequirement> {
    let mut required = BTreeSet::new();
    for run in &plan.runs {
        for toggle in PB12_TOGGLES {
            if run.toggle_value(toggle) {
                if let Some(requirement) = requirement_for_toggle(toggle) {
                    required.insert(requirement);
                }
            }
        }
    }
    required
}

fn requirement_for_toggle(toggle: Pb12Toggle) -> Option<ControlMatrixDataRequirement> {
    match toggle {
        Pb12Toggle::UseGreeks => Some(ControlMatrixDataRequirement::OptionsGreeks),
        Pb12Toggle::UseOi => Some(ControlMatrixDataRequirement::OptionsOpenInterest),
        Pb12Toggle::UseIv => Some(ControlMatrixDataRequirement::OptionsImpliedVolatility),
        Pb12Toggle::UseEtf => Some(ControlMatrixDataRequirement::EtfReference),
        Pb12Toggle::UseCfd => Some(ControlMatrixDataRequirement::CfdReference),
        Pb12Toggle::UseVix => Some(ControlMatrixDataRequirement::VixOverlay),
        Pb12Toggle::UseDailyStructure | Pb12Toggle::UseWeeklyStructure => None,
    }
}

fn ibkr_provider_status(
    required: &BTreeSet<ControlMatrixDataRequirement>,
    home_dir: Option<&Path>,
    runtime_ready: bool,
) -> ControlMatrixProviderStatus {
    let supported = [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::CfdReference,
        ControlMatrixDataRequirement::VixOverlay,
    ];
    let consent_path = home_dir.map(|home| home.join(IBKR_CONSENT_RELATIVE_PATH));
    let capabilities_path = home_dir.map(|home| home.join(IBKR_CAPABILITIES_RELATIVE_PATH));
    let consent_present = consent_path.as_ref().map(|path| path.exists()).unwrap_or(false);
    let capabilities_present = capabilities_path
        .as_ref()
        .map(|path| path.exists())
        .unwrap_or(false);
    let healthy = consent_present && runtime_ready;
    ControlMatrixProviderStatus {
        provider: ControlMatrixProviderKind::Ibkr.as_str().to_string(),
        status: if healthy {
            "ready".to_string()
        } else {
            "install_required".to_string()
        },
        healthy,
        reason: if !consent_present {
            "missing_local_ibkr_consent".to_string()
        } else if !runtime_ready {
            "ibkr_runtime_probe_failed".to_string()
        } else {
            "local_ibkr_runtime_ready".to_string()
        },
        supported_requirements: supported
            .into_iter()
            .filter(|item| required.contains(item))
            .map(|item| item.as_str().to_string())
            .collect(),
        install_prompts: if healthy {
            Vec::new()
        } else {
            vec![
                "Consumer agent request: ask the user to install IBKR TWS or IB Gateway, then enable the IBKR API locally. Search keywords: Interactive Brokers TWS download, IB Gateway download.".to_string(),
                "Consumer agent request: ask the user to start local Redis if IBKR bridge mode is needed: brew install redis && brew services start redis".to_string(),
                "Consumer agent follow-up: after the user installs IBKR TWS or Gateway, run python scripts/ibkr_bridge/setup.py --enable".to_string(),
                "Consumer agent follow-up: once the user-approved runtime is ready, start python scripts/ibkr_bridge/bridge.py --config example_config.yaml".to_string(),
            ]
        },
        redacted_config: vec![
            format!("consent_path={}", redact_path(consent_path.as_deref())),
            format!(
                "capabilities_path={}",
                redact_path(capabilities_path.as_deref())
            ),
            format!("consent_present={consent_present}"),
            format!("capabilities_present={capabilities_present}"),
        ],
    }
}

fn ibkr_runtime_ready() -> bool {
    let scripts_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("scripts");
    let probe = format!(
        "import sys; sys.path.insert(0, {:?}); import redis; import ibkr_bridge",
        scripts_dir.display().to_string()
    );
    std::process::Command::new("python3")
        .arg("-c")
        .arg(probe)
        .output()
        .map(|output| output.status.success())
        .unwrap_or(false)
}

fn yfinance_provider_status<F>(
    required: &BTreeSet<ControlMatrixDataRequirement>,
    _env_lookup: &F,
) -> ControlMatrixProviderStatus
where
    F: Fn(&str) -> Option<String>,
{
    let supported = [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::CfdReference,
        ControlMatrixDataRequirement::VixOverlay,
        ControlMatrixDataRequirement::OptionsOpenInterest,
        ControlMatrixDataRequirement::OptionsImpliedVolatility,
    ];
    ControlMatrixProviderStatus {
        provider: ControlMatrixProviderKind::YahooFinance.as_str().to_string(),
        status: "ready".to_string(),
        healthy: true,
        reason: "public_yahoo_http_endpoints".to_string(),
        supported_requirements: supported
            .into_iter()
            .filter(|item| required.contains(item))
            .map(|item| item.as_str().to_string())
            .collect(),
        install_prompts: Vec::new(),
        redacted_config: vec!["provider_mode=public_http".to_string()],
    }
}

fn tradingview_mcp_provider_status<F>(
    required: &BTreeSet<ControlMatrixDataRequirement>,
    env_lookup: &F,
) -> ControlMatrixProviderStatus
where
    F: Fn(&str) -> Option<String>,
{
    let supported = [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::CfdReference,
        ControlMatrixDataRequirement::VixOverlay,
        ControlMatrixDataRequirement::OptionsGreeks,
        ControlMatrixDataRequirement::OptionsImpliedVolatility,
    ];
    let configured_url = env_lookup(TVREMIX_MCP_URL_ENV)
        .filter(|value| !value.trim().is_empty())
        .unwrap_or_else(|| TVREMIX_MCP_DEFAULT_URL.to_string());
    let has_api_key = env_lookup(TVREMIX_MCP_API_KEY_ENV)
        .map(|value| !value.trim().is_empty())
        .unwrap_or(false);
    ControlMatrixProviderStatus {
        provider: ControlMatrixProviderKind::TradingViewMcp.as_str().to_string(),
        status: if has_api_key {
            "ready".to_string()
        } else {
            "install_required".to_string()
        },
        healthy: has_api_key,
        reason: if has_api_key {
            "mcp_url_and_api_key_available".to_string()
        } else {
            "missing_tradingview_mcp_api_key".to_string()
        },
        supported_requirements: supported
            .into_iter()
            .filter(|item| required.contains(item))
            .map(|item| item.as_str().to_string())
            .collect(),
        install_prompts: if has_api_key {
            Vec::new()
        } else {
            vec![
                format!(
                    "Consumer agent request: ask the user for a TradingViewRemix MCP API key, then add an HTTP MCP server pointing at {}. Search keywords: TradingViewRemix MCP API key.",
                    configured_url
                ),
                format!(
                    "Consumer agent follow-up: after the user shares the key, export {}=<redacted> and configure Authorization: Bearer from that env var",
                    TVREMIX_MCP_API_KEY_ENV
                ),
                format!(
                    "Consumer agent optional override: export {}={}",
                    TVREMIX_MCP_URL_ENV, TVREMIX_MCP_DEFAULT_URL
                ),
            ]
        },
        redacted_config: vec![
            format!("mcp_url={configured_url}"),
            format!("{}={}", TVREMIX_MCP_API_KEY_ENV, redact_secret_presence(has_api_key)),
        ],
    }
}

fn home_dir() -> Option<PathBuf> {
    std::env::var_os("HOME").map(PathBuf::from)
}

fn redact_path(path: Option<&Path>) -> String {
    path.map(|_| "<local-path>".to_string())
        .unwrap_or_else(|| "unavailable".to_string())
}

fn redact_secret_presence(present: bool) -> &'static str {
    if present {
        "<set>"
    } else {
        "<unset>"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn provider_summary_requires_install_prompts_without_local_config() {
        let plan = ControlMatrixPlan::pb12();
        let summary = build_provider_summary_for_requirements_with_env(
            required_requirements_for_plan(&plan),
            &|_| None,
            Some(PathBuf::from("/tmp/does-not-exist")),
            &|| false,
        );
        assert!(summary
            .required_requirements
            .contains(&"etf_reference".to_string()));
        assert!(summary
            .required_requirements
            .contains(&"options_greeks".to_string()));
        assert!(summary
            .provider_statuses
            .iter()
            .any(|status| status.provider == "ibkr" && status.status == "install_required"));
        assert!(summary.provider_statuses.iter().any(|status| {
            status.provider == "tradingview_mcp" && status.status == "install_required"
        }));
        assert!(summary
            .actionable_install_prompts
            .iter()
            .any(|prompt| prompt.contains("ask the user for a TradingViewRemix MCP API key")));
        assert!(summary
            .actionable_install_prompts
            .iter()
            .any(|prompt| prompt.contains("install IBKR TWS or IB Gateway")));
    }

    #[test]
    fn tradingview_provider_redacts_secret_value() {
        let plan = ControlMatrixPlan::pb12();
        let summary = build_provider_summary_for_requirements_with_env(
            required_requirements_for_plan(&plan),
            &|name| match name {
                TVREMIX_MCP_API_KEY_ENV => Some("secret-token-value".to_string()),
                _ => None,
            },
            None,
            &|| false,
        );
        let provider = summary
            .provider_statuses
            .iter()
            .find(|status| status.provider == "tradingview_mcp")
            .unwrap();
        assert_eq!(provider.status, "ready");
        assert!(
            provider
                .redacted_config
                .iter()
                .all(|item| !item.contains("secret-token-value"))
        );
        assert!(provider.redacted_config.iter().any(|item| item.contains("<set>")));
    }

    #[test]
    fn ibkr_requires_runtime_probe_even_with_consent_files() {
        let required = BTreeSet::from([ControlMatrixDataRequirement::CfdReference]);
        let summary = build_provider_summary_for_requirements_with_env(
            required,
            &|_| None,
            Some(PathBuf::from(std::env::var("HOME").unwrap())),
            &|| false,
        );
        let provider = summary
            .provider_statuses
            .iter()
            .find(|status| status.provider == "ibkr")
            .unwrap();
        assert_eq!(provider.status, "install_required");
        assert!(!provider.healthy);
        assert_eq!(provider.reason, "ibkr_runtime_probe_failed");
    }
}
