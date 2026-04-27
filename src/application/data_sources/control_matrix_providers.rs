use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use crate::application::backtest::{ControlMatrixPlan, PB12_TOGGLES, Pb12Toggle};

pub const TVREMIX_MCP_DEFAULT_URL: &str = "https://tvremix.xyz/api/mcp";
pub const TVREMIX_MCP_URL_ENV: &str = "ICT_ENGINE_TVREMIX_MCP_URL";
pub const TVREMIX_MCP_API_KEY_ENV: &str = "ICT_ENGINE_TVREMIX_MCP_API_KEY";
pub const YFINANCE_ENABLED_ENV: &str = "ICT_ENGINE_YFINANCE_ENABLED";
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
    build_control_matrix_provider_summary_with_env(
        plan,
        &|name| std::env::var(name).ok(),
        home_dir(),
    )
}

fn build_control_matrix_provider_summary_with_env<F>(
    plan: &ControlMatrixPlan,
    env_lookup: &F,
    home_dir: Option<PathBuf>,
) -> ControlMatrixProviderSummary
where
    F: Fn(&str) -> Option<String>,
{
    let required = required_requirements_for_plan(plan);
    let provider_statuses = vec![
        ibkr_provider_status(&required, home_dir.as_deref()),
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
) -> ControlMatrixProviderStatus {
    let supported = [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::CfdReference,
        ControlMatrixDataRequirement::VixOverlay,
        ControlMatrixDataRequirement::OptionsGreeks,
        ControlMatrixDataRequirement::OptionsOpenInterest,
        ControlMatrixDataRequirement::OptionsImpliedVolatility,
    ];
    let consent_path = home_dir.map(|home| home.join(IBKR_CONSENT_RELATIVE_PATH));
    let capabilities_path = home_dir.map(|home| home.join(IBKR_CAPABILITIES_RELATIVE_PATH));
    let consent_present = consent_path.as_ref().map(|path| path.exists()).unwrap_or(false);
    let capabilities_present = capabilities_path
        .as_ref()
        .map(|path| path.exists())
        .unwrap_or(false);
    ControlMatrixProviderStatus {
        provider: ControlMatrixProviderKind::Ibkr.as_str().to_string(),
        status: if consent_present {
            "ready".to_string()
        } else {
            "install_required".to_string()
        },
        healthy: consent_present,
        reason: if consent_present {
            "local_ibkr_consent_present".to_string()
        } else {
            "missing_local_ibkr_consent".to_string()
        },
        supported_requirements: supported
            .into_iter()
            .filter(|item| required.contains(item))
            .map(|item| item.as_str().to_string())
            .collect(),
        install_prompts: if consent_present {
            Vec::new()
        } else {
            vec![
                "IBKR optional setup: brew install redis && brew services start redis".to_string(),
                "IBKR optional setup: python scripts/ibkr_bridge/setup.py --enable".to_string(),
                "IBKR optional bridge: python scripts/ibkr_bridge/bridge.py --config example_config.yaml".to_string(),
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

fn yfinance_provider_status<F>(
    required: &BTreeSet<ControlMatrixDataRequirement>,
    env_lookup: &F,
) -> ControlMatrixProviderStatus
where
    F: Fn(&str) -> Option<String>,
{
    let supported = [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::VixOverlay,
        ControlMatrixDataRequirement::OptionsGreeks,
        ControlMatrixDataRequirement::OptionsOpenInterest,
        ControlMatrixDataRequirement::OptionsImpliedVolatility,
    ];
    let enabled = env_lookup(YFINANCE_ENABLED_ENV)
        .map(|value| matches!(value.trim().to_ascii_lowercase().as_str(), "1" | "true" | "yes"))
        .unwrap_or(false);
    ControlMatrixProviderStatus {
        provider: ControlMatrixProviderKind::YahooFinance.as_str().to_string(),
        status: if enabled {
            "ready".to_string()
        } else {
            "install_hint_only".to_string()
        },
        healthy: enabled,
        reason: if enabled {
            "yfinance_enabled_via_env".to_string()
        } else {
            "set_ICT_ENGINE_YFINANCE_ENABLED_after_install".to_string()
        },
        supported_requirements: supported
            .into_iter()
            .filter(|item| required.contains(item))
            .map(|item| item.as_str().to_string())
            .collect(),
        install_prompts: if enabled {
            Vec::new()
        } else {
            vec![
                "yfinance optional setup: uv run --with yfinance python -c \"import yfinance\"".to_string(),
                format!(
                    "yfinance enable hint: export {}=1",
                    YFINANCE_ENABLED_ENV
                ),
            ]
        },
        redacted_config: vec![format!("{}={}", YFINANCE_ENABLED_ENV, enabled)],
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
        ControlMatrixDataRequirement::OptionsOpenInterest,
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
                    "TradingView MCP install: add an HTTP MCP server pointing at {}",
                    configured_url
                ),
                format!(
                    "TradingView MCP auth: export {}=<redacted> and configure Authorization: Bearer from that env var",
                    TVREMIX_MCP_API_KEY_ENV
                ),
                format!(
                    "TradingView MCP URL override: export {}={}",
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
        let summary = build_control_matrix_provider_summary_with_env(
            &plan,
            &|_| None,
            Some(PathBuf::from("/tmp/does-not-exist")),
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
            .any(|prompt| prompt.contains("TradingView MCP install")));
    }

    #[test]
    fn tradingview_provider_redacts_secret_value() {
        let plan = ControlMatrixPlan::pb12();
        let summary = build_control_matrix_provider_summary_with_env(
            &plan,
            &|name| match name {
                TVREMIX_MCP_API_KEY_ENV => Some("secret-token-value".to_string()),
                _ => None,
            },
            None,
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
}
