use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

use crate::application::data_sources::{
    build_provider_summary_for_requirements, ControlMatrixDataRequirement,
    IBKR_CAPABILITIES_RELATIVE_PATH, IBKR_CONSENT_RELATIVE_PATH,
};
use crate::application::entry_models::{entry_model_providers, ConsumerDefaultMode};
use crate::config::shell_quote;

const PROVIDER_STATUS_AGENT_COMMAND: &str = "ict-engine provider-status --agent";
const OPENALICE_DEFAULT_URL: &str = "http://127.0.0.1:6901/api/v1";
const NOFX_DEFAULT_URL: &str = "http://127.0.0.1:8080";
const PROVIDER_PROFILE_SCHEMA_VERSION: &str = "provider-profile/v1";
const REPO_PROVIDER_PROFILE_DIR: &str = "examples/provider_profiles";
const KRAKEN_API_KEY_ENV: &str = "KRAKEN_API_KEY";
const KRAKEN_API_SECRET_ENV: &str = "KRAKEN_API_SECRET";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ProviderCatalogDomain {
    MarketData,
    LiveRuntime,
    LocalRuntime,
    EntryModel,
}

impl ProviderCatalogDomain {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::MarketData => "market_data",
            Self::LiveRuntime => "live_runtime",
            Self::LocalRuntime => "local_runtime",
            Self::EntryModel => "entry_model",
        }
    }

    pub fn parse(value: &str) -> Result<Self> {
        match value.trim().to_ascii_lowercase().as_str() {
            "market_data" | "market-data" => Ok(Self::MarketData),
            "live_runtime" | "live-runtime" => Ok(Self::LiveRuntime),
            "local_runtime" | "local-runtime" | "local_bridge" | "local-bridge" => {
                Ok(Self::LocalRuntime)
            }
            "entry_model" | "entry-model" => Ok(Self::EntryModel),
            other => bail!(
                "unsupported provider-status domain '{}'; available: market_data, live_runtime, local_runtime, entry_model",
                other
            ),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProviderCatalogItem {
    pub provider_id: String,
    pub domain: String,
    pub selectable_by_user: bool,
    pub adopted_by_default: bool,
    pub access_mode: String,
    pub ready: bool,
    pub status: String,
    pub reason: String,
    pub capabilities: Vec<String>,
    pub notes: Vec<String>,
    pub install_prompts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderCatalogDomainSummary {
    pub domain: String,
    pub total: usize,
    pub ready: usize,
    pub selectable: usize,
    pub default_enabled: usize,
    pub provider_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderCatalogSurface {
    pub providers: Vec<ProviderCatalogItem>,
    pub domains: Vec<ProviderCatalogDomainSummary>,
    pub summary_line: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_profile: Option<ProviderProfileSelectionSurface>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderCatalogAgentSurface {
    pub summary_line: String,
    pub ready_by_domain: BTreeMap<String, String>,
    pub ready_providers: Vec<String>,
    pub pending_providers: Vec<String>,
    pub pending_provider_details: Vec<ProviderCatalogPendingAgentItem>,
    pub selectable_providers: Vec<String>,
    pub default_enabled_providers: Vec<String>,
    pub install_prompts: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_profile: Option<ProviderProfileSelectionSurface>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderCatalogPendingAgentItem {
    pub provider_id: String,
    pub domain: String,
    pub status: String,
    pub reason: String,
    pub install_prompts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct WorkflowProviderSupportSurface {
    pub active: bool,
    pub profile_id: String,
    pub support_reason: String,
    pub provider_status_command: String,
    pub summary_line: String,
    pub pending_providers: Vec<String>,
    pub pending_provider_details: Vec<ProviderCatalogPendingAgentItem>,
    pub install_prompts: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_profile: Option<ProviderProfileSelectionSurface>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProviderProfileDocument {
    pub schema_version: String,
    pub profile_id: String,
    pub display_name: String,
    pub opt_in_only: bool,
    pub summary: String,
    #[serde(default)]
    pub data_contracts: Vec<ProviderProfileDataContract>,
    #[serde(default)]
    pub provider_tracks: Vec<ProviderProfileTrack>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProviderProfileDataContract {
    pub contract_id: String,
    pub category: String,
    pub required: bool,
    pub label: String,
    #[serde(default)]
    pub symbols: Vec<String>,
    #[serde(default)]
    pub timeframes: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_hint: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ProviderProfileTrackMode {
    AnyOf,
    AllOf,
}

impl ProviderProfileTrackMode {
    fn as_str(self) -> &'static str {
        match self {
            Self::AnyOf => "any_of",
            Self::AllOf => "all_of",
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProviderProfileTrack {
    pub track_id: String,
    pub label: String,
    pub required: bool,
    pub mode: ProviderProfileTrackMode,
    #[serde(default)]
    pub provider_ids: Vec<String>,
    #[serde(default)]
    pub activation_hints: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderProfileTrackSelection {
    pub track_id: String,
    pub label: String,
    pub required: bool,
    pub mode: String,
    pub activation_hints: Vec<String>,
    pub status: String,
    pub ready_provider_ids: Vec<String>,
    pub pending_provider_ids: Vec<String>,
    pub install_prompts: Vec<String>,
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ProviderProfileSelectionSurface {
    pub profile_id: String,
    pub display_name: String,
    pub opt_in_only: bool,
    pub source: String,
    pub selector: String,
    pub summary: String,
    pub data_contracts: Vec<ProviderProfileDataContract>,
    pub data_contract_labels: Vec<String>,
    pub track_details: Vec<ProviderProfileTrackSelection>,
    pub track_statuses: Vec<String>,
    pub ready_provider_ids: Vec<String>,
    pub pending_provider_ids: Vec<String>,
    pub install_prompts: Vec<String>,
}

pub trait ProviderCatalogSource {
    fn domain(&self) -> ProviderCatalogDomain;
    fn collect_items(&self) -> Result<Vec<ProviderCatalogItem>>;
}

pub fn provider_catalog_sources() -> Vec<Box<dyn ProviderCatalogSource>> {
    vec![
        Box::new(MarketDataProviderCatalogSource),
        Box::new(LiveRuntimeProviderCatalogSource),
        Box::new(LocalRuntimeProviderCatalogSource),
        Box::new(EntryModelProviderCatalogSource),
    ]
}

pub fn provider_status_surface(
    domain_filter: Option<&str>,
    provider_filter: Option<&str>,
    profile_selector: Option<&str>,
) -> Result<ProviderCatalogSurface> {
    let parsed_domain = domain_filter
        .map(ProviderCatalogDomain::parse)
        .transpose()?;
    let mut providers = Vec::new();
    for source in provider_catalog_sources() {
        if parsed_domain
            .map(|domain| domain == source.domain())
            .unwrap_or(true)
        {
            providers.extend(source.collect_items()?);
        }
    }
    let selected_profile = if let Some(selector) = profile_selector {
        let (profile, source_path) = load_provider_profile_with_source(selector)?;
        let source = source_path.to_string_lossy().to_string();
        let command_selector = provider_profile_command_selector(&source_path);
        Some(build_selected_profile_surface_from_items(
            &providers,
            &profile,
            &source,
            &command_selector,
        )?)
    } else {
        None
    };
    if let Some(filter) = provider_filter {
        providers.retain(|item| item.provider_id == filter);
        if providers.is_empty() {
            bail!("unknown provider id '{}'", filter);
        }
    }
    providers.sort_by(|a, b| {
        a.domain
            .cmp(&b.domain)
            .then(a.provider_id.cmp(&b.provider_id))
    });

    let mut grouped = BTreeMap::<String, Vec<&ProviderCatalogItem>>::new();
    for item in &providers {
        grouped.entry(item.domain.clone()).or_default().push(item);
    }
    let domains = grouped
        .into_iter()
        .map(|(domain, items)| ProviderCatalogDomainSummary {
            domain,
            total: items.len(),
            ready: items.iter().filter(|item| item.ready).count(),
            selectable: items.iter().filter(|item| item.selectable_by_user).count(),
            default_enabled: items.iter().filter(|item| item.adopted_by_default).count(),
            provider_ids: items
                .iter()
                .map(|item| item.provider_id.clone())
                .collect::<Vec<_>>(),
        })
        .collect::<Vec<_>>();

    let summary_line = domains
        .iter()
        .map(|domain| format!("{}:{}/{} ready", domain.domain, domain.ready, domain.total))
        .collect::<Vec<_>>()
        .join(" | ");

    Ok(ProviderCatalogSurface {
        providers,
        domains,
        summary_line,
        selected_profile,
    })
}

pub fn provider_status_command(
    domain_filter: Option<&str>,
    provider_filter: Option<&str>,
    compact: bool,
    agent: bool,
    jsonl: bool,
    profile_selector: Option<&str>,
) -> Result<()> {
    let surface = provider_status_surface(domain_filter, provider_filter, profile_selector)?;
    if agent {
        println!(
            "{}",
            serde_json::to_string_pretty(&build_provider_catalog_agent_surface(&surface))?
        );
    } else if jsonl {
        print!("{}", render_provider_catalog_jsonl(&surface)?);
    } else if compact {
        println!("{}", render_provider_catalog_compact(&surface));
    } else {
        println!("{}", serde_json::to_string_pretty(&surface)?);
    }
    Ok(())
}

#[derive(Debug, Clone, Copy, Default)]
struct MarketDataProviderCatalogSource;

impl ProviderCatalogSource for MarketDataProviderCatalogSource {
    fn domain(&self) -> ProviderCatalogDomain {
        ProviderCatalogDomain::MarketData
    }

    fn collect_items(&self) -> Result<Vec<ProviderCatalogItem>> {
        let summary = build_provider_summary_for_requirements(all_market_data_requirements());
        let mut items = summary
            .provider_statuses
            .into_iter()
            .map(|status| ProviderCatalogItem {
                provider_id: status.provider,
                domain: self.domain().as_str().to_string(),
                selectable_by_user: true,
                adopted_by_default: false,
                access_mode: market_data_access_mode(&status.status, &status.reason),
                ready: status.healthy,
                status: status.status,
                reason: status.reason,
                capabilities: status.supported_requirements,
                notes: Vec::new(),
                install_prompts: status.install_prompts,
            })
            .collect::<Vec<_>>();

        let public_fetch_ready = provider_fetch_script_exists() && python3_exists();
        items.extend([
            public_provider_item(
                "binance_public",
                public_fetch_ready,
                vec!["ohlcv".to_string(), "options_chain".to_string()],
                vec!["public_rest".to_string(), "no_api_key_required".to_string()],
            ),
            public_provider_item(
                "bybit_public",
                public_fetch_ready,
                vec!["ohlcv".to_string(), "options_chain".to_string()],
                vec!["public_rest".to_string(), "no_api_key_required".to_string()],
            ),
            public_provider_item(
                "kraken_public",
                public_fetch_ready,
                vec![
                    "ohlcv".to_string(),
                    "spot".to_string(),
                    "futures".to_string(),
                    "tokenized_equity".to_string(),
                ],
                vec!["public_rest".to_string(), "no_api_key_required".to_string()],
            ),
            public_provider_item(
                "polymarket_public",
                public_fetch_ready,
                vec!["prediction_market_history".to_string()],
                vec![
                    "public_rest".to_string(),
                    "network_path_dependent".to_string(),
                ],
            ),
        ]);
        Ok(items)
    }
}

#[derive(Debug, Clone, Copy, Default)]
struct LiveRuntimeProviderCatalogSource;

impl ProviderCatalogSource for LiveRuntimeProviderCatalogSource {
    fn domain(&self) -> ProviderCatalogDomain {
        ProviderCatalogDomain::LiveRuntime
    }

    fn collect_items(&self) -> Result<Vec<ProviderCatalogItem>> {
        Ok(vec![
            ProviderCatalogItem {
                provider_id: "openbb".to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: true,
                adopted_by_default: true,
                access_mode: "local_library".to_string(),
                ready: true,
                status: "ready".to_string(),
                reason: "native_openbb_backend_available".to_string(),
                capabilities: vec![
                    "futures_candles".to_string(),
                    "spot_candles".to_string(),
                    "options_summary".to_string(),
                ],
                notes: vec!["yfinance alias routes through openbb".to_string()],
                install_prompts: Vec::new(),
            },
            ProviderCatalogItem {
                provider_id: "openalice".to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: true,
                adopted_by_default: false,
                access_mode: "external_http_runtime".to_string(),
                ready: false,
                status: "operator_runtime_required".to_string(),
                reason: "base_url_and_service_required".to_string(),
                capabilities: vec![
                    "futures_candles".to_string(),
                    "spot_candles".to_string(),
                    "options_summary".to_string(),
                ],
                notes: vec!["usable when operator supplies running service".to_string()],
                install_prompts: vec![
                    "Consumer agent request: ask whether the user wants zero-config openbb or an OpenAlice-compatible live runtime."
                        .to_string(),
                    format!(
                        "Consumer agent follow-up: if the user chooses OpenAlice, keep the openalice backend and pass --openalice-base-url <url> (default {}).",
                        OPENALICE_DEFAULT_URL
                    ),
                ],
            },
            ProviderCatalogItem {
                provider_id: "nofx".to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: true,
                adopted_by_default: false,
                access_mode: "external_http_runtime".to_string(),
                ready: false,
                status: "operator_runtime_required".to_string(),
                reason: "base_url_and_service_required".to_string(),
                capabilities: vec![
                    "futures_candles".to_string(),
                    "spot_candles".to_string(),
                    "options_summary".to_string(),
                ],
                notes: vec!["usable when operator supplies running service".to_string()],
                install_prompts: vec![
                    "Consumer agent request: ask whether the user wants zero-config openbb or a NoFX-compatible live runtime."
                        .to_string(),
                    format!(
                        "Consumer agent follow-up: if the user chooses NoFX, keep the nofx backend and pass --nofx-base-url <url> (default {}).",
                        NOFX_DEFAULT_URL
                    ),
                ],
            },
        ])
    }
}

#[derive(Debug, Clone, Copy, Default)]
struct LocalRuntimeProviderCatalogSource;

impl ProviderCatalogSource for LocalRuntimeProviderCatalogSource {
    fn domain(&self) -> ProviderCatalogDomain {
        ProviderCatalogDomain::LocalRuntime
    }

    fn collect_items(&self) -> Result<Vec<ProviderCatalogItem>> {
        let ibkr_probe = probe_ibkr_bridge();
        let kraken_probe = probe_kraken_cli();
        Ok(vec![
            ProviderCatalogItem {
                provider_id: "ibkr_bridge".to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: false,
                adopted_by_default: false,
                access_mode: "local_consent_runtime".to_string(),
                ready: ibkr_probe.ready,
                status: ibkr_probe.status,
                reason: ibkr_probe.reason,
                capabilities: vec![
                    "local_ibkr_historical".to_string(),
                    "local_ibkr_stream".to_string(),
                ],
                notes: ibkr_probe.notes,
                install_prompts: ibkr_probe.install_prompts,
            },
            ProviderCatalogItem {
                provider_id: "kraken_cli".to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: false,
                adopted_by_default: false,
                access_mode: "local_cli_runtime".to_string(),
                ready: kraken_probe.ready,
                status: kraken_probe.status,
                reason: kraken_probe.reason,
                capabilities: vec![
                    "local_cli_execution".to_string(),
                    "operator_wallet_flow".to_string(),
                ],
                notes: kraken_probe.notes,
                install_prompts: kraken_probe.install_prompts,
            },
        ])
    }
}

#[derive(Debug, Clone, Copy, Default)]
struct EntryModelProviderCatalogSource;

impl ProviderCatalogSource for EntryModelProviderCatalogSource {
    fn domain(&self) -> ProviderCatalogDomain {
        ProviderCatalogDomain::EntryModel
    }

    fn collect_items(&self) -> Result<Vec<ProviderCatalogItem>> {
        Ok(entry_model_providers()
            .into_iter()
            .map(|provider| ProviderCatalogItem {
                provider_id: provider.provider_id().to_string(),
                domain: self.domain().as_str().to_string(),
                selectable_by_user: !matches!(
                    provider.consumer_default_mode(),
                    ConsumerDefaultMode::InternalTrainingOnly
                ),
                adopted_by_default: provider.consumer_default_mode().adopted_by_default(),
                access_mode: "internal_model_registry".to_string(),
                ready: true,
                status: "registered".to_string(),
                reason: "entry_model_registry_member".to_string(),
                capabilities: vec!["training_rows".to_string(), "status_surface".to_string()],
                notes: vec![provider.consumer_default_mode().effect_label().to_string()],
                install_prompts: Vec::new(),
            })
            .collect())
    }
}

fn all_market_data_requirements() -> std::collections::BTreeSet<ControlMatrixDataRequirement> {
    [
        ControlMatrixDataRequirement::EtfReference,
        ControlMatrixDataRequirement::CfdReference,
        ControlMatrixDataRequirement::VixOverlay,
        ControlMatrixDataRequirement::OptionsGreeks,
        ControlMatrixDataRequirement::OptionsOpenInterest,
        ControlMatrixDataRequirement::OptionsImpliedVolatility,
    ]
    .into_iter()
    .collect()
}

fn market_data_access_mode(status: &str, reason: &str) -> String {
    if status == "ready" && reason.contains("consent") {
        "local_consent_runtime".to_string()
    } else if status == "ready" {
        "public_or_env_ready".to_string()
    } else if reason.contains("api_key") {
        "api_key_required".to_string()
    } else {
        "operator_runtime_required".to_string()
    }
}

fn public_provider_item(
    provider_id: &str,
    ready: bool,
    capabilities: Vec<String>,
    notes: Vec<String>,
) -> ProviderCatalogItem {
    ProviderCatalogItem {
        provider_id: provider_id.to_string(),
        domain: ProviderCatalogDomain::MarketData.as_str().to_string(),
        selectable_by_user: true,
        adopted_by_default: false,
        access_mode: "public_script_adapter".to_string(),
        ready,
        status: if ready {
            "ready".to_string()
        } else {
            "script_or_python_missing".to_string()
        },
        reason: if ready {
            "fetch_external_script_available".to_string()
        } else {
            "missing_fetch_external_runtime".to_string()
        },
        capabilities,
        notes,
        install_prompts: Vec::new(),
    }
}

fn provider_fetch_script_exists() -> bool {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("scripts/auto_quant_external/fetch_external.py")
        .exists()
}

fn python3_exists() -> bool {
    command_exists(&["python3"])
}

#[derive(Debug, Clone)]
struct LocalRuntimeProbe {
    ready: bool,
    status: String,
    reason: String,
    notes: Vec<String>,
    install_prompts: Vec<String>,
}

fn probe_ibkr_bridge() -> LocalRuntimeProbe {
    let script_present = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("scripts/ibkr_bridge/__init__.py")
        .exists();
    let home = home_dir();
    let consent_present = home
        .as_ref()
        .map(|root| root.join(IBKR_CONSENT_RELATIVE_PATH).exists())
        .unwrap_or(false);
    let capabilities_present = home
        .as_ref()
        .map(|root| root.join(IBKR_CAPABILITIES_RELATIVE_PATH).exists())
        .unwrap_or(false);
    let runtime_ready = ibkr_bridge_runtime_ready();
    let (ready, status, reason) = if !script_present || !python3_exists() {
        (
            false,
            "install_required".to_string(),
            "ibkr_bridge_not_installed".to_string(),
        )
    } else if !consent_present && !capabilities_present {
        (
            false,
            "installed_unconfigured".to_string(),
            "ibkr_bridge_installed_but_consent_missing".to_string(),
        )
    } else if !runtime_ready {
        (
            false,
            "configured_runtime_unhealthy".to_string(),
            "ibkr_bridge_config_present_but_runtime_probe_failed".to_string(),
        )
    } else {
        (
            true,
            "ready".to_string(),
            "local_ibkr_bridge_ready".to_string(),
        )
    };
    LocalRuntimeProbe {
        ready,
        status,
        reason,
        notes: vec![
            "reused by ibkr market-data provider".to_string(),
            format!("consent_present={}", consent_present),
            format!("capabilities_present={}", capabilities_present),
        ],
        install_prompts: if ready {
            Vec::new()
        } else {
            vec![
                "Install and enable the local IBKR bridge if you want IBKR-backed workflows."
                    .to_string(),
            ]
        },
    }
}

fn ibkr_bridge_runtime_ready() -> bool {
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

fn probe_kraken_cli() -> LocalRuntimeProbe {
    let binary_on_path = command_exists(&["kraken", "kraken-cli"]);
    let local_binary = find_kraken_cli_local_binary();
    let installed = binary_on_path || local_binary.is_some();
    let configured = kraken_cli_config_present();
    let (ready, status, reason) = if !installed {
        (
            false,
            "install_required".to_string(),
            "kraken_cli_not_found_on_path".to_string(),
        )
    } else if !binary_on_path {
        (
            false,
            "installed_off_path".to_string(),
            "kraken_cli_binary_found_off_path".to_string(),
        )
    } else if !configured {
        (
            false,
            "installed_unconfigured".to_string(),
            "kraken_cli_installed_but_config_missing".to_string(),
        )
    } else {
        (
            true,
            "ready".to_string(),
            "kraken_cli_config_detected".to_string(),
        )
    };
    LocalRuntimeProbe {
        ready,
        status,
        reason,
        notes: {
            let mut notes = vec!["see docs/external/kraken-cli-agent-patterns.md".to_string()];
            if let Some(path) = local_binary {
                notes.push(format!("local_binary={}", path.display()));
            }
            notes
        },
        install_prompts: if ready {
            Vec::new()
        } else {
            vec![
                "Consumer agent request: ask the user to install kraken-cli from https://github.com/krakenfx/kraken-cli if Kraken workflows are needed.".to_string(),
                "Consumer agent request: ask the user to create or retrieve Kraken API credentials before authenticated kraken-cli use.".to_string(),
                format!(
                    "Consumer agent follow-up: configure kraken-cli with {} / {} or ~/.config/kraken/config.toml once the user approves.",
                    KRAKEN_API_KEY_ENV, KRAKEN_API_SECRET_ENV
                ),
            ]
        },
    }
}

fn kraken_cli_config_present() -> bool {
    let env_config = [KRAKEN_API_KEY_ENV, KRAKEN_API_SECRET_ENV]
        .into_iter()
        .all(|name| env::var_os(name).is_some());
    if env_config {
        return true;
    }
    if kraken_cli_auth_present_from_cli() {
        return true;
    }
    let Some(home) = home_dir() else {
        return false;
    };
    [
        ".config/kraken-cli",
        ".config/kraken",
        ".kraken-cli",
        ".kraken",
    ]
    .into_iter()
    .map(|rel| home.join(rel))
    .any(|path| path.exists())
}

fn kraken_cli_auth_present_from_cli() -> bool {
    let Ok(output) = std::process::Command::new("kraken")
        .args(["auth", "show", "-o", "json"])
        .output()
    else {
        return false;
    };
    if !output.status.success() {
        return false;
    }
    let Ok(value) = serde_json::from_slice::<serde_json::Value>(&output.stdout) else {
        return false;
    };
    value
        .get("api_key")
        .and_then(|api_key| api_key.get("present"))
        .and_then(serde_json::Value::as_bool)
        .unwrap_or(false)
}

fn find_kraken_cli_local_binary() -> Option<PathBuf> {
    let home = home_dir()?;
    let candidates = [
        home.join(".cargo/bin/kraken"),
        home.join(".cargo/bin/kraken-cli"),
        home.join("kraken-cli/target/debug/kraken"),
        home.join("kraken-cli/target/release/kraken"),
        home.join("kraken-cli/target/debug/kraken-cli"),
        home.join("kraken-cli/target/release/kraken-cli"),
    ];
    candidates.into_iter().find(|path| path.exists())
}

fn home_dir() -> Option<PathBuf> {
    env::var_os("HOME").map(PathBuf::from)
}

fn command_exists(names: &[&str]) -> bool {
    let Some(path_os) = env::var_os("PATH") else {
        return false;
    };
    env::split_paths(&path_os).any(|dir| {
        names
            .iter()
            .map(|name| dir.join(name))
            .any(|candidate| candidate.exists())
    })
}

fn render_provider_catalog_compact(surface: &ProviderCatalogSurface) -> String {
    let mut lines = Vec::new();
    lines.push(surface.summary_line.clone());
    if let Some(profile) = surface.selected_profile.as_ref() {
        lines.push(format!(
            "profile: {} pending {}",
            profile.profile_id,
            profile.pending_provider_ids.join(", ")
        ));
        lines.push(format!("  summary: {}", profile.summary));
        if !profile.data_contract_labels.is_empty() {
            lines.push(format!(
                "  data_contracts: {}",
                profile
                    .data_contract_labels
                    .iter()
                    .take(3)
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(" | ")
            ));
        }
        if !profile.track_statuses.is_empty() {
            lines.push(format!(
                "  tracks: {}",
                profile
                    .track_statuses
                    .iter()
                    .take(4)
                    .cloned()
                    .collect::<Vec<_>>()
                    .join(" | ")
            ));
        }
    }
    for domain in &surface.domains {
        lines.push(format!(
            "{}: ready {}/{} selectable {} default {}",
            domain.domain, domain.ready, domain.total, domain.selectable, domain.default_enabled
        ));
        let ready = surface
            .providers
            .iter()
            .filter(|provider| provider.domain == domain.domain && provider.ready)
            .map(|provider| provider.provider_id.clone())
            .collect::<Vec<_>>();
        let pending = surface
            .providers
            .iter()
            .filter(|provider| provider.domain == domain.domain && !provider.ready)
            .map(|provider| {
                format!(
                    "{}({}:{})",
                    provider.provider_id, provider.status, provider.reason
                )
            })
            .collect::<Vec<_>>();
        if !ready.is_empty() {
            lines.push(format!("  ready: {}", ready.join(", ")));
        }
        if !pending.is_empty() {
            lines.push(format!("  pending: {}", pending.join(", ")));
        }
    }
    lines.join("\n")
}

fn build_provider_catalog_agent_surface(
    surface: &ProviderCatalogSurface,
) -> ProviderCatalogAgentSurface {
    let ready_by_domain = surface
        .domains
        .iter()
        .map(|domain| {
            (
                domain.domain.clone(),
                format!("{}/{}", domain.ready, domain.total),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let ready_providers = surface
        .providers
        .iter()
        .filter(|provider| provider.ready)
        .map(|provider| provider.provider_id.clone())
        .collect::<Vec<_>>();
    let pending_providers = surface
        .providers
        .iter()
        .filter(|provider| !provider.ready)
        .map(|provider| {
            format!(
                "{}@{}:{}:{}",
                provider.provider_id, provider.domain, provider.status, provider.reason
            )
        })
        .collect::<Vec<_>>();
    let pending_provider_details = surface
        .providers
        .iter()
        .filter(|provider| !provider.ready)
        .map(|provider| ProviderCatalogPendingAgentItem {
            provider_id: provider.provider_id.clone(),
            domain: provider.domain.clone(),
            status: provider.status.clone(),
            reason: provider.reason.clone(),
            install_prompts: provider.install_prompts.clone(),
        })
        .collect::<Vec<_>>();
    let selectable_providers = surface
        .providers
        .iter()
        .filter(|provider| provider.selectable_by_user)
        .map(|provider| provider.provider_id.clone())
        .collect::<Vec<_>>();
    let default_enabled_providers = surface
        .providers
        .iter()
        .filter(|provider| provider.adopted_by_default)
        .map(|provider| provider.provider_id.clone())
        .collect::<Vec<_>>();
    let install_prompts = surface
        .providers
        .iter()
        .flat_map(|provider| provider.install_prompts.iter().cloned())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();

    ProviderCatalogAgentSurface {
        summary_line: surface.summary_line.clone(),
        ready_by_domain,
        ready_providers,
        pending_providers,
        pending_provider_details,
        selectable_providers,
        default_enabled_providers,
        install_prompts,
        selected_profile: surface.selected_profile.clone(),
    }
}

pub fn provider_status_agent_surface(
    domain_filter: Option<&str>,
    provider_filter: Option<&str>,
    profile_selector: Option<&str>,
) -> Result<ProviderCatalogAgentSurface> {
    let surface = provider_status_surface(domain_filter, provider_filter, profile_selector)?;
    Ok(build_provider_catalog_agent_surface(&surface))
}

pub fn build_workflow_provider_support(
    surface: &ProviderCatalogAgentSurface,
    next_command: &str,
    blocking_reason: Option<&str>,
) -> WorkflowProviderSupportSurface {
    let selected_profile = surface.selected_profile.clone();
    let relevant_provider_ids = workflow_relevant_provider_ids(next_command, blocking_reason);
    let mut support = WorkflowProviderSupportSurface {
        profile_id: selected_profile
            .as_ref()
            .map(|profile| profile.profile_id.clone())
            .unwrap_or_else(|| "workflow_auto".to_string()),
        support_reason: blocking_reason.unwrap_or_default().to_string(),
        provider_status_command: provider_status_agent_command_for_surface(surface),
        summary_line: surface.summary_line.clone(),
        selected_profile,
        ..WorkflowProviderSupportSurface::default()
    };
    if relevant_provider_ids.is_empty() {
        return support;
    }

    let mut pending_provider_details = surface
        .pending_provider_details
        .iter()
        .filter(|provider| relevant_provider_ids.contains(provider.provider_id.as_str()))
        .cloned()
        .collect::<Vec<_>>();
    pending_provider_details.sort_by(|a, b| a.provider_id.cmp(&b.provider_id));
    if pending_provider_details.is_empty() {
        return support;
    }

    let pending_providers = pending_provider_details
        .iter()
        .map(|provider| provider.provider_id.clone())
        .collect::<Vec<_>>();
    let install_prompts = pending_provider_details
        .iter()
        .flat_map(|provider| provider.install_prompts.iter().cloned())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    support.active = true;
    support.pending_providers = pending_providers;
    support.pending_provider_details = pending_provider_details;
    support.install_prompts = install_prompts;
    support
}

pub fn provider_status_agent_command_for_surface(surface: &ProviderCatalogAgentSurface) -> String {
    provider_status_agent_command(surface.selected_profile.as_ref())
}

pub fn provider_status_agent_command(
    selected_profile: Option<&ProviderProfileSelectionSurface>,
) -> String {
    if let Some(profile) = selected_profile {
        return format!(
            "{} --profile {}",
            PROVIDER_STATUS_AGENT_COMMAND,
            shell_quote(&profile.selector)
        );
    }
    PROVIDER_STATUS_AGENT_COMMAND.to_string()
}

fn workflow_relevant_provider_ids(
    next_command: &str,
    blocking_reason: Option<&str>,
) -> std::collections::BTreeSet<&'static str> {
    let haystack = format!(
        "{} {}",
        next_command.to_ascii_lowercase(),
        blocking_reason.unwrap_or_default().to_ascii_lowercase()
    );
    let mut ids = std::collections::BTreeSet::new();

    if haystack.contains("--futures-backend openalice")
        || haystack.contains("--aux-backend openalice")
        || haystack.contains("openalice_base_url")
    {
        ids.insert("openalice");
    }
    if haystack.contains("--futures-backend nofx")
        || haystack.contains("--aux-backend nofx")
        || haystack.contains("nofx_base_url")
    {
        ids.insert("nofx");
    }
    if haystack.contains("tradingview") {
        ids.insert("tradingview_mcp");
    }
    if haystack.contains("ibkr") || haystack.contains("gateway") || haystack.contains("tws") {
        ids.insert("ibkr");
        ids.insert("ibkr_bridge");
    }
    if haystack.contains("kraken") {
        ids.insert("kraken_cli");
    }
    if ids.is_empty()
        && haystack.contains("provider_runtime_required")
        && haystack.contains("analyze-live")
    {
        ids.insert("openalice");
        ids.insert("nofx");
    }

    ids
}

fn render_provider_catalog_jsonl(surface: &ProviderCatalogSurface) -> Result<String> {
    let mut lines = Vec::new();
    lines.push(serde_json::to_string(&serde_json::json!({
        "type": "summary",
        "summary_line": surface.summary_line,
        "domains": surface.domains,
        "selected_profile": surface.selected_profile,
    }))?);
    for provider in &surface.providers {
        lines.push(serde_json::to_string(&serde_json::json!({
            "type": "provider",
            "provider_id": provider.provider_id,
            "domain": provider.domain,
            "selectable_by_user": provider.selectable_by_user,
            "adopted_by_default": provider.adopted_by_default,
            "access_mode": provider.access_mode,
            "ready": provider.ready,
            "status": provider.status,
            "reason": provider.reason,
            "capabilities": provider.capabilities,
            "notes": provider.notes,
            "install_prompts": provider.install_prompts,
        }))?);
    }
    Ok(lines.join("\n"))
}

pub fn load_provider_profile(selector: &str) -> Result<ProviderProfileDocument> {
    load_provider_profile_with_source(selector).map(|(profile, _)| profile)
}

fn load_provider_profile_with_source(selector: &str) -> Result<(ProviderProfileDocument, PathBuf)> {
    let path = resolve_provider_profile_path(selector)?;
    let raw = fs::read_to_string(&path)?;
    let profile: ProviderProfileDocument = serde_json::from_str(&raw)?;
    if profile.schema_version != PROVIDER_PROFILE_SCHEMA_VERSION {
        bail!(
            "unsupported provider profile schema_version '{}'; expected '{}'",
            profile.schema_version,
            PROVIDER_PROFILE_SCHEMA_VERSION
        );
    }
    if profile.profile_id.trim().is_empty() {
        bail!("provider profile id must not be empty");
    }
    Ok((profile, path))
}

fn provider_profile_command_selector(path: &Path) -> String {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(REPO_PROVIDER_PROFILE_DIR);
    if path.starts_with(&repo_root) {
        return path
            .file_stem()
            .and_then(|stem| stem.to_str())
            .map(ToString::to_string)
            .unwrap_or_else(|| path.to_string_lossy().to_string());
    }
    path.to_string_lossy().to_string()
}

fn resolve_provider_profile_path(selector: &str) -> Result<PathBuf> {
    let trimmed = selector.trim();
    if trimmed.is_empty() {
        bail!("provider profile selector must not be empty");
    }
    let direct = PathBuf::from(trimmed);
    if direct.exists() {
        return Ok(direct);
    }
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join(REPO_PROVIDER_PROFILE_DIR);
    let repo_exact = repo_root.join(trimmed);
    if repo_exact.exists() {
        return Ok(repo_exact);
    }
    let repo_json = repo_root.join(format!("{trimmed}.json"));
    if repo_json.exists() {
        return Ok(repo_json);
    }
    bail!(
        "unknown provider profile '{}'; pass a JSON path or a repo example id from {}",
        trimmed,
        REPO_PROVIDER_PROFILE_DIR
    )
}

fn build_selected_profile_surface_from_items(
    items: &[ProviderCatalogItem],
    profile: &ProviderProfileDocument,
    source: &str,
    selector: &str,
) -> Result<ProviderProfileSelectionSurface> {
    let item_map = items
        .iter()
        .map(|item| (item.provider_id.as_str(), item))
        .collect::<BTreeMap<_, _>>();
    let mut ready_provider_ids = Vec::new();
    let mut pending_provider_ids = Vec::new();
    let mut install_prompts = std::collections::BTreeSet::new();
    let mut track_details = Vec::new();
    let mut track_statuses = Vec::new();

    for track in &profile.provider_tracks {
        let mut ready = Vec::new();
        let mut pending = Vec::new();
        let mut track_prompts = std::collections::BTreeSet::new();
        for provider_id in &track.provider_ids {
            match item_map.get(provider_id.as_str()) {
                Some(item) if item.ready => ready.push(provider_id.clone()),
                Some(item) => {
                    pending.push(provider_id.clone());
                    for prompt in &item.install_prompts {
                        track_prompts.insert(prompt.clone());
                    }
                }
                None => pending.push(provider_id.clone()),
            }
        }
        let status = match track.mode {
            ProviderProfileTrackMode::AnyOf => {
                if ready.is_empty() {
                    "pending"
                } else {
                    "ready"
                }
            }
            ProviderProfileTrackMode::AllOf => {
                if pending.is_empty() {
                    "ready"
                } else if ready.is_empty() {
                    "pending"
                } else {
                    "partial"
                }
            }
        };
        ready_provider_ids.extend(ready.iter().cloned());
        pending_provider_ids.extend(pending.iter().cloned());
        install_prompts.extend(track_prompts.iter().cloned());
        let status_target = if !pending.is_empty() {
            pending.join(",")
        } else if !ready.is_empty() {
            ready.join(",")
        } else {
            "none".to_string()
        };
        track_statuses.push(format!("{}:{}:{}", track.track_id, status, status_target));
        track_details.push(ProviderProfileTrackSelection {
            track_id: track.track_id.clone(),
            label: track.label.clone(),
            required: track.required,
            mode: track.mode.as_str().to_string(),
            activation_hints: track.activation_hints.clone(),
            status: status.to_string(),
            ready_provider_ids: ready,
            pending_provider_ids: pending,
            install_prompts: track_prompts.into_iter().collect(),
            notes: track.notes.clone(),
        });
    }

    ready_provider_ids.sort();
    ready_provider_ids.dedup();
    pending_provider_ids.sort();
    pending_provider_ids.dedup();
    track_statuses.sort();

    Ok(ProviderProfileSelectionSurface {
        profile_id: profile.profile_id.clone(),
        display_name: profile.display_name.clone(),
        opt_in_only: profile.opt_in_only,
        source: source.to_string(),
        selector: selector.to_string(),
        summary: profile.summary.clone(),
        data_contracts: profile.data_contracts.clone(),
        data_contract_labels: profile
            .data_contracts
            .iter()
            .map(|contract| contract.label.clone())
            .collect(),
        track_details,
        track_statuses,
        ready_provider_ids,
        pending_provider_ids,
        install_prompts: install_prompts.into_iter().collect(),
    })
}

#[cfg(test)]
fn build_selected_profile_surface(
    surface: &ProviderCatalogSurface,
    profile: &ProviderProfileDocument,
    source: &str,
    selector: &str,
) -> Result<ProviderProfileSelectionSurface> {
    build_selected_profile_surface_from_items(&surface.providers, profile, source, selector)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_surface() -> ProviderCatalogSurface {
        ProviderCatalogSurface {
            providers: vec![
                ProviderCatalogItem {
                    provider_id: "yfinance".to_string(),
                    domain: "market_data".to_string(),
                    selectable_by_user: true,
                    adopted_by_default: false,
                    access_mode: "public".to_string(),
                    ready: true,
                    status: "ready".to_string(),
                    reason: "ok".to_string(),
                    capabilities: vec!["ohlcv".to_string()],
                    notes: vec![],
                    install_prompts: vec![],
                },
                ProviderCatalogItem {
                    provider_id: "ibkr".to_string(),
                    domain: "market_data".to_string(),
                    selectable_by_user: true,
                    adopted_by_default: false,
                    access_mode: "local_consent_runtime".to_string(),
                    ready: false,
                    status: "install_required".to_string(),
                    reason: "missing_runtime".to_string(),
                    capabilities: vec!["ohlcv".to_string()],
                    notes: vec![],
                    install_prompts: vec!["install ibkr".to_string()],
                },
            ],
            domains: vec![ProviderCatalogDomainSummary {
                domain: "market_data".to_string(),
                total: 2,
                ready: 1,
                selectable: 2,
                default_enabled: 0,
                provider_ids: vec!["yfinance".to_string(), "ibkr".to_string()],
            }],
            summary_line: "market_data:1/2 ready".to_string(),
            selected_profile: None,
        }
    }

    #[test]
    fn agent_surface_keeps_low_token_summary() {
        let agent = build_provider_catalog_agent_surface(&sample_surface());
        assert_eq!(agent.summary_line, "market_data:1/2 ready");
        assert_eq!(
            agent.ready_by_domain.get("market_data").map(String::as_str),
            Some("1/2")
        );
        assert!(agent.ready_providers.contains(&"yfinance".to_string()));
        assert!(agent
            .pending_providers
            .iter()
            .any(|item| item.contains("ibkr@market_data")));
    }

    #[test]
    fn compact_surface_summarizes_selected_profile_contracts_and_tracks() {
        let mut surface = sample_surface();
        let profile = load_provider_profile("thrill3r-nq-closed-loop-v1").unwrap();
        surface.selected_profile = Some(
            build_selected_profile_surface(
                &surface,
                &profile,
                "repo-example",
                "thrill3r-nq-closed-loop-v1",
            )
            .unwrap(),
        );

        let compact = render_provider_catalog_compact(&surface);

        assert!(compact.contains("profile: thrill3r_nq_closed_loop_v1"));
        assert!(compact.contains("summary: Personal NQ workflow"));
        assert!(compact.contains("data_contracts:"));
        assert!(compact.contains("Tomac cleaned multi-timeframe futures root"));
        assert!(compact.contains("tracks:"));
        assert!(compact.contains("live_zero_config:pending:openbb"));
    }

    #[test]
    fn jsonl_surface_starts_with_summary_record() {
        let jsonl = render_provider_catalog_jsonl(&sample_surface()).unwrap();
        let mut lines = jsonl.lines();
        let first = lines.next().unwrap_or("");
        assert!(first.contains("\"type\":\"summary\""));
        let second = lines.next().unwrap_or("");
        assert!(second.contains("\"type\":\"provider\""));
    }

    #[test]
    fn workflow_provider_support_filters_to_relevant_pending_runtime_providers() {
        let support = build_workflow_provider_support(
            &ProviderCatalogAgentSurface {
                summary_line: "live_runtime:1/3 ready | local_runtime:0/2 ready".to_string(),
                ready_by_domain: BTreeMap::from([
                    ("live_runtime".to_string(), "1/3".to_string()),
                    ("local_runtime".to_string(), "0/2".to_string()),
                ]),
                ready_providers: vec!["openbb".to_string()],
                pending_providers: vec![
                    "openalice@live_runtime:operator_runtime_required:base_url_and_service_required"
                        .to_string(),
                    "nofx@live_runtime:operator_runtime_required:base_url_and_service_required"
                        .to_string(),
                    "ibkr_bridge@local_runtime:configured_runtime_unhealthy:ibkr_bridge_config_present_but_runtime_probe_failed"
                        .to_string(),
                ],
                pending_provider_details: vec![
                    ProviderCatalogPendingAgentItem {
                        provider_id: "openalice".to_string(),
                        domain: "live_runtime".to_string(),
                        status: "operator_runtime_required".to_string(),
                        reason: "base_url_and_service_required".to_string(),
                        install_prompts: vec![
                            "ask whether the user wants zero-config openbb or openalice"
                                .to_string(),
                        ],
                    },
                    ProviderCatalogPendingAgentItem {
                        provider_id: "nofx".to_string(),
                        domain: "live_runtime".to_string(),
                        status: "operator_runtime_required".to_string(),
                        reason: "base_url_and_service_required".to_string(),
                        install_prompts: vec![
                            "ask whether the user wants zero-config openbb or nofx"
                                .to_string(),
                        ],
                    },
                    ProviderCatalogPendingAgentItem {
                        provider_id: "ibkr_bridge".to_string(),
                        domain: "local_runtime".to_string(),
                        status: "configured_runtime_unhealthy".to_string(),
                        reason: "ibkr_bridge_config_present_but_runtime_probe_failed".to_string(),
                        install_prompts: vec!["start ibkr bridge".to_string()],
                    },
                ],
                selectable_providers: vec!["openalice".to_string(), "nofx".to_string()],
                default_enabled_providers: vec!["openbb".to_string()],
                install_prompts: vec![],
                selected_profile: None,
            },
            "ict-engine analyze-live --symbol NQ --futures-backend openalice --aux-backend nofx",
            Some("provider_runtime_required"),
        );

        assert!(support.active);
        assert_eq!(support.profile_id, "workflow_auto");
        assert_eq!(support.pending_providers.len(), 2);
        assert!(support
            .pending_providers
            .iter()
            .all(|item| item.contains("openalice") || item.contains("nofx")));
        assert!(support
            .install_prompts
            .iter()
            .any(|prompt| prompt.contains("zero-config openbb")));
        assert!(!support
            .pending_providers
            .iter()
            .any(|item| item.contains("ibkr_bridge")));
    }

    #[test]
    fn workflow_provider_support_stays_inactive_when_command_has_no_provider_gap() {
        let support = build_workflow_provider_support(
            &ProviderCatalogAgentSurface {
                summary_line: "market_data:5/7 ready".to_string(),
                ready_by_domain: BTreeMap::new(),
                ready_providers: vec!["yfinance".to_string()],
                pending_providers: vec![
                    "tradingview_mcp@market_data:install_required:missing_tradingview_mcp_api_key"
                        .to_string(),
                ],
                pending_provider_details: vec![ProviderCatalogPendingAgentItem {
                    provider_id: "tradingview_mcp".to_string(),
                    domain: "market_data".to_string(),
                    status: "install_required".to_string(),
                    reason: "missing_tradingview_mcp_api_key".to_string(),
                    install_prompts: vec!["ask for key".to_string()],
                }],
                selectable_providers: vec!["tradingview_mcp".to_string()],
                default_enabled_providers: vec!["yfinance".to_string()],
                install_prompts: vec!["ask for key".to_string()],
                selected_profile: None,
            },
            "ict-engine factor-research --symbol NQ --backend native",
            None,
        );

        assert!(!support.active);
        assert!(support.pending_providers.is_empty());
        assert!(support.install_prompts.is_empty());
    }

    #[test]
    fn provider_status_agent_command_is_profile_aware_only_when_opted_in() {
        let default_command = provider_status_agent_command(None);
        assert_eq!(default_command, "ict-engine provider-status --agent");

        let command = provider_status_agent_command(Some(&ProviderProfileSelectionSurface {
            profile_id: "thrill3r_nq_closed_loop_v1".to_string(),
            display_name: "Thrill3r NQ Closed Loop v1".to_string(),
            opt_in_only: true,
            source: "/tmp/provider profile.json".to_string(),
            selector: "/tmp/provider profile.json".to_string(),
            summary: "Personal NQ workflow".to_string(),
            data_contracts: Vec::new(),
            data_contract_labels: Vec::new(),
            track_details: Vec::new(),
            track_statuses: Vec::new(),
            ready_provider_ids: Vec::new(),
            pending_provider_ids: Vec::new(),
            install_prompts: Vec::new(),
        }));
        assert_eq!(
            command,
            "ict-engine provider-status --agent --profile '/tmp/provider profile.json'"
        );
    }

    #[test]
    fn repo_example_profile_can_be_loaded_by_id() {
        let profile = load_provider_profile("thrill3r-nq-closed-loop-v1").unwrap();
        assert_eq!(profile.profile_id, "thrill3r_nq_closed_loop_v1");
        assert!(profile.opt_in_only);
        assert!(profile
            .data_contracts
            .iter()
            .any(|contract| contract.label.contains("Tomac cleaned")));
    }

    #[test]
    fn selected_profile_surface_marks_missing_options_track_pending() {
        let mut surface = sample_surface();
        surface.providers.push(ProviderCatalogItem {
            provider_id: "tradingview_mcp".to_string(),
            domain: "market_data".to_string(),
            selectable_by_user: true,
            adopted_by_default: false,
            access_mode: "api_key_required".to_string(),
            ready: false,
            status: "install_required".to_string(),
            reason: "missing_tradingview_mcp_api_key".to_string(),
            capabilities: vec![
                "options_greeks".to_string(),
                "options_implied_volatility".to_string(),
            ],
            notes: vec![],
            install_prompts: vec![
                "Consumer agent request: ask the user for a TradingViewRemix MCP API key."
                    .to_string(),
            ],
        });
        let profile = load_provider_profile("thrill3r-nq-closed-loop-v1").unwrap();
        let selected = build_selected_profile_surface(
            &surface,
            &profile,
            "repo-example",
            "thrill3r-nq-closed-loop-v1",
        )
        .unwrap();

        assert_eq!(selected.profile_id, "thrill3r_nq_closed_loop_v1");
        assert_eq!(selected.selector, "thrill3r-nq-closed-loop-v1");
        assert!(selected
            .track_statuses
            .iter()
            .any(|track| track.contains("options_enriched:pending:tradingview_mcp")));
        assert!(selected
            .install_prompts
            .iter()
            .any(|prompt| prompt.contains("TradingViewRemix MCP API key")));
    }
}
