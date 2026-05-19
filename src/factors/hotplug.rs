use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use crate::factors::registry::FactorRegistry;

pub const FACTOR_HOTPLUG_CONFIG_FILE: &str = "factor_hotplug.yaml";
pub const FACTOR_HOTPLUG_ENV_VAR: &str = "ICT_ENGINE_FACTOR_HOTPLUG_CONFIG";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FactorHotplugConfig {
    /// Map of factor family snake_case name → enabled (true/false).
    /// Missing keys default to true (family enabled).
    pub families: BTreeMap<String, bool>,
    /// Optional detector enrichment context. Absent by default; populated only
    /// when a user explicitly selects a hotplug config/profile.
    #[serde(default)]
    pub detector_context: Option<DetectorHotplugContext>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct DetectorHotplugContext {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_label: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_profile: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub volume_quality: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub symbol_context: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub calendar_context: Option<String>,
}

impl Default for FactorHotplugConfig {
    fn default() -> Self {
        let mut families = BTreeMap::new();
        for name in &[
            "trend_momentum",
            "volatility_mean_reversion",
            "structure_ict",
            "cross_market_smt",
            "options_hedging",
            "crowding_herding",
            "spectral_rhythm",
            "session_liquidity",
        ] {
            families.insert(name.to_string(), true);
        }
        Self {
            families,
            detector_context: None,
        }
    }
}

impl FactorHotplugConfig {
    pub fn is_enabled(&self, family_name: &str) -> bool {
        self.families.get(family_name).copied().unwrap_or(true)
    }

    pub fn resolve_config_path(state_dir: &str) -> PathBuf {
        if let Ok(custom) = std::env::var(FACTOR_HOTPLUG_ENV_VAR) {
            let trimmed = custom.trim();
            if !trimmed.is_empty() {
                return PathBuf::from(trimmed);
            }
        }
        Path::new(state_dir).join(FACTOR_HOTPLUG_CONFIG_FILE)
    }

    pub fn load(state_dir: &str) -> Result<Option<Self>> {
        let path = Self::resolve_config_path(state_dir);
        if !path.exists() {
            return Ok(None);
        }
        let content = std::fs::read_to_string(&path)
            .with_context(|| format!("reading factor hotplug config '{}'", path.display()))?;
        let config: Self = serde_yaml::from_str(&content)
            .with_context(|| format!("parsing factor hotplug config '{}'", path.display()))?;
        Ok(Some(config))
    }

    pub fn apply_to_registry(&self, registry: &mut FactorRegistry) {
        for (name, enabled) in &self.families {
            registry.set_enabled(name, *enabled);
        }
    }

    pub fn apply_to_registry_if_present(state_dir: &str, registry: &mut FactorRegistry) {
        if let Ok(Some(config)) = Self::load(state_dir) {
            config.apply_to_registry(registry);
        }
    }

    pub fn summary_line(&self) -> String {
        let disabled = self
            .families
            .iter()
            .filter_map(|(name, enabled)| (!enabled).then_some(name.as_str()))
            .collect::<Vec<_>>();
        let disabled_summary = if disabled.is_empty() {
            "disabled=[]".to_string()
        } else {
            format!("disabled=[{}]", disabled.join(","))
        };
        let detector_summary = self
            .detector_context
            .as_ref()
            .map(DetectorHotplugContext::summary_suffix)
            .unwrap_or_default();
        format!("Factor hotplug: config=present {disabled_summary}{detector_summary}")
    }
}

impl DetectorHotplugContext {
    pub fn summary_suffix(&self) -> String {
        let mut fields = Vec::new();
        if self.calendar_context.is_some() {
            fields.push("calendar_context");
        }
        if self.session_label.is_some() {
            fields.push("session_label");
        }
        if self.source_profile.is_some() {
            fields.push("source_profile");
        }
        if self.symbol_context.is_some() {
            fields.push("symbol_context");
        }
        if self.volume_quality.is_some() {
            fields.push("volume_quality");
        }
        if fields.is_empty() {
            " detector_context=opt_in fields=[]".to_string()
        } else {
            format!(" detector_context=opt_in fields=[{}]", fields.join(","))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config_all_enabled() {
        let config = FactorHotplugConfig::default();
        assert!(config.is_enabled("trend_momentum"));
        assert!(config.is_enabled("crowding_herding"));
        assert!(config.is_enabled("session_liquidity"));
        // Unknown families default to true
        assert!(config.is_enabled("unknown_future_factor"));
    }

    #[test]
    fn test_custom_config_disables_family() {
        let mut config = FactorHotplugConfig::default();
        config.families.insert("options_hedging".to_string(), false);
        assert!(!config.is_enabled("options_hedging"));
        assert!(config.is_enabled("trend_momentum"));
    }

    #[test]
    fn test_apply_to_registry() {
        let mut registry = FactorRegistry::default();
        assert!(registry.get("options_hedging").unwrap().enabled);
        let mut config = FactorHotplugConfig::default();
        config.families.insert("options_hedging".to_string(), false);
        config.apply_to_registry(&mut registry);
        assert!(!registry.get("options_hedging").unwrap().enabled);
    }

    #[test]
    fn test_default_config_has_no_detector_context() {
        let config = FactorHotplugConfig::default();

        assert!(config.detector_context.is_none());
    }

    #[test]
    fn test_loads_optional_detector_context_from_explicit_config() {
        let temp = tempfile::tempdir().unwrap();
        let config_path = temp.path().join(FACTOR_HOTPLUG_CONFIG_FILE);
        std::fs::write(
            &config_path,
            r#"
families:
  structure_ict: true
detector_context:
  session_label: ny_open
  source_profile: paper_session_labels_v1
  volume_quality: broker_reported
  symbol_context: nq_futures
  calendar_context: cme_regular_session
"#,
        )
        .unwrap();

        let config = FactorHotplugConfig::load(temp.path().to_str().unwrap())
            .unwrap()
            .unwrap();
        let context = config.detector_context.unwrap();

        assert_eq!(context.session_label.as_deref(), Some("ny_open"));
        assert_eq!(
            context.source_profile.as_deref(),
            Some("paper_session_labels_v1")
        );
        assert_eq!(context.volume_quality.as_deref(), Some("broker_reported"));
        assert_eq!(context.symbol_context.as_deref(), Some("nq_futures"));
        assert_eq!(
            context.calendar_context.as_deref(),
            Some("cme_regular_session")
        );
    }

    #[test]
    fn test_summary_reports_opt_in_detector_context_without_private_values() {
        let mut config = FactorHotplugConfig::default();
        config.detector_context = Some(DetectorHotplugContext {
            session_label: Some("ny_open".to_string()),
            source_profile: Some("paper_session_labels_v1".to_string()),
            volume_quality: Some("broker_reported".to_string()),
            symbol_context: Some("nq_futures".to_string()),
            calendar_context: Some("cme_regular_session".to_string()),
        });

        let summary = config.summary_line();

        assert_eq!(
            summary,
            "Factor hotplug: config=present disabled=[] detector_context=opt_in fields=[calendar_context,session_label,source_profile,symbol_context,volume_quality]"
        );
    }
}
