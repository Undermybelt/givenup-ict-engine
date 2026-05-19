use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use crate::factors::registry::FactorRegistry;

pub const FACTOR_HOTPLUG_CONFIG_FILE: &str = "factor_hotplug.yaml";
pub const FACTOR_HOTPLUG_ENV_VAR: &str = "ICT_ENGINE_FACTOR_HOTPLUG_CONFIG";
pub const DETECTOR_GA_FEATURE_MANIFEST_SCHEMA_VERSION: &str = "ict_detector_ga_feature_manifest_v1";
pub const DETECTOR_GA_FEATURE_MANIFEST_FILE: &str = "detector_feature_manifest.json";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct FactorHotplugConfig {
    /// Map of factor family snake_case name → enabled (true/false).
    /// Missing keys default to true (family enabled).
    pub families: BTreeMap<String, bool>,
    /// Optional detector enrichment context. Absent by default; populated only
    /// when a user explicitly selects a hotplug config/profile.
    #[serde(default)]
    pub detector_context: Option<DetectorHotplugContext>,
    /// Optional detector feature bundle for downstream search/GA optimizers.
    /// This is a field-name contract only; default runtime detector execution
    /// remains candle-only and independent of external optimizer tooling.
    #[serde(default)]
    pub detector_ga_bundle: Option<DetectorGaFeatureBundle>,
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

#[derive(Debug, Clone, Default, Serialize, Deserialize, PartialEq)]
pub struct DetectorGaFeatureBundle {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bundle_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_consumer: Option<String>,
    #[serde(default)]
    pub selected_fields: Vec<String>,
    #[serde(default)]
    pub optimizer_objectives: Vec<String>,
    #[serde(default)]
    pub validation_windows: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DetectorGaFeatureManifest {
    pub schema_version: String,
    pub bundle_id: String,
    pub target_consumer: String,
    pub selected_fields: Vec<String>,
    pub optimizer_objectives: Vec<String>,
    pub validation_windows: Vec<String>,
    pub warnings: Vec<String>,
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
            detector_ga_bundle: None,
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
        let detector_ga_summary = self
            .detector_ga_bundle
            .as_ref()
            .map(DetectorGaFeatureBundle::summary_suffix)
            .unwrap_or_default();
        format!(
            "Factor hotplug: config=present {disabled_summary}{detector_summary}{detector_ga_summary}"
        )
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

impl DetectorGaFeatureBundle {
    pub fn summary_suffix(&self) -> String {
        let fields = sorted_unique_public_tokens(&self.selected_fields);

        let objectives = sorted_unique_public_tokens(&self.optimizer_objectives);

        let bundle = if self.bundle_id.as_deref().unwrap_or_default().is_empty() {
            "unset"
        } else {
            "set"
        };
        let target = compact_public_token(self.target_consumer.as_deref()).unwrap_or("unset");

        format!(
            " detector_ga_bundle=opt_in bundle={bundle} target={target} fields=[{}] objectives=[{}] validation_windows={}",
            fields.join(","),
            objectives.join(","),
            self.validation_windows.len()
        )
    }
}

impl DetectorGaFeatureManifest {
    pub fn from_bundle(bundle: &DetectorGaFeatureBundle) -> Self {
        let selected_fields = sorted_unique_public_tokens(&bundle.selected_fields);
        let optimizer_objectives = sorted_unique_public_tokens(&bundle.optimizer_objectives);
        let validation_windows = sorted_unique_public_tokens(&bundle.validation_windows);
        let mut warnings = Vec::new();

        if validation_windows.len() != bundle.validation_windows.len() {
            warnings.push("dropped_unsafe_validation_window_tokens".to_string());
        }
        if selected_fields.len() != bundle.selected_fields.len() {
            warnings.push("dropped_duplicate_or_unsafe_selected_fields".to_string());
        }
        if optimizer_objectives.len() != bundle.optimizer_objectives.len() {
            warnings.push("dropped_duplicate_or_unsafe_optimizer_objectives".to_string());
        }

        Self {
            schema_version: DETECTOR_GA_FEATURE_MANIFEST_SCHEMA_VERSION.to_string(),
            bundle_id: compact_public_token(bundle.bundle_id.as_deref())
                .unwrap_or("unset")
                .to_string(),
            target_consumer: compact_public_token(bundle.target_consumer.as_deref())
                .unwrap_or("unset")
                .to_string(),
            selected_fields,
            optimizer_objectives,
            validation_windows,
            warnings,
        }
    }
}

pub fn persist_detector_ga_feature_manifest(state_dir: &str) -> Result<Option<PathBuf>> {
    let Some(config) = FactorHotplugConfig::load(state_dir)? else {
        return Ok(None);
    };
    let Some(bundle) = config.detector_ga_bundle.as_ref() else {
        return Ok(None);
    };

    let manifest = DetectorGaFeatureManifest::from_bundle(bundle);
    let output_dir = Path::new(state_dir).join("auto-quant").join("ga_optimizer");
    std::fs::create_dir_all(&output_dir).with_context(|| {
        format!(
            "creating detector GA manifest dir '{}'",
            output_dir.display()
        )
    })?;
    let output_path = output_dir.join(DETECTOR_GA_FEATURE_MANIFEST_FILE);
    let content =
        serde_json::to_string_pretty(&manifest).context("serializing detector GA manifest")?;
    std::fs::write(&output_path, content)
        .with_context(|| format!("writing detector GA manifest '{}'", output_path.display()))?;
    Ok(Some(output_path))
}

fn compact_public_token(value: Option<&str>) -> Option<&str> {
    value.and_then(|raw| {
        let trimmed = raw.trim();
        if trimmed.is_empty()
            || trimmed.contains('/')
            || trimmed.contains('\\')
            || trimmed.contains('=')
            || trimmed.contains(':')
        {
            None
        } else {
            Some(trimmed)
        }
    })
}

fn sorted_unique_public_tokens(values: &[String]) -> Vec<String> {
    let mut out = values
        .iter()
        .filter_map(|value| compact_public_token(Some(value.as_str())).map(str::to_string))
        .collect::<Vec<_>>();
    out.sort();
    out.dedup();
    out
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

    #[test]
    fn test_default_config_has_no_detector_ga_bundle() {
        let config = FactorHotplugConfig::default();

        assert!(config.detector_ga_bundle.is_none());
    }

    #[test]
    fn test_loads_optional_detector_ga_bundle_from_explicit_config() {
        let temp = tempfile::tempdir().unwrap();
        let config_path = temp.path().join(FACTOR_HOTPLUG_CONFIG_FILE);
        std::fs::write(
            &config_path,
            r#"
families:
  structure_ict: true
detector_ga_bundle:
  bundle_id: ict_detector_ga_v1
  target_consumer: auto_quant_search
  selected_fields:
    - vi_mitigation_pct
    - fvg_mitigation_pct
    - ob_mitigation_pct
    - liquidity_pool_subtype
    - sweep_quality
  optimizer_objectives:
    - regime_conditioned_win_rate
    - cost_adjusted_expectancy
  validation_windows:
    - train_60d_validate_20d
    - walk_forward_quarterly
"#,
        )
        .unwrap();

        let config = FactorHotplugConfig::load(temp.path().to_str().unwrap())
            .unwrap()
            .unwrap();
        let bundle = config.detector_ga_bundle.unwrap();

        assert_eq!(bundle.bundle_id.as_deref(), Some("ict_detector_ga_v1"));
        assert_eq!(bundle.target_consumer.as_deref(), Some("auto_quant_search"));
        assert_eq!(
            bundle.selected_fields,
            vec![
                "vi_mitigation_pct",
                "fvg_mitigation_pct",
                "ob_mitigation_pct",
                "liquidity_pool_subtype",
                "sweep_quality"
            ]
        );
        assert_eq!(
            bundle.optimizer_objectives,
            vec!["regime_conditioned_win_rate", "cost_adjusted_expectancy"]
        );
        assert_eq!(
            bundle.validation_windows,
            vec!["train_60d_validate_20d", "walk_forward_quarterly"]
        );
    }

    #[test]
    fn test_summary_reports_detector_ga_bundle_without_private_values() {
        let mut config = FactorHotplugConfig::default();
        config.detector_ga_bundle = Some(DetectorGaFeatureBundle {
            bundle_id: Some("local/private/ga-bundle".to_string()),
            target_consumer: Some("auto_quant_search".to_string()),
            selected_fields: vec![
                "vi_mitigation_pct".to_string(),
                "fvg_mitigation_pct".to_string(),
                "ob_mitigation_pct".to_string(),
            ],
            optimizer_objectives: vec![
                "regime_conditioned_win_rate".to_string(),
                "cost_adjusted_expectancy".to_string(),
            ],
            validation_windows: vec!["local/private/window.json".to_string()],
        });

        let summary = config.summary_line();

        assert_eq!(
            summary,
            "Factor hotplug: config=present disabled=[] detector_ga_bundle=opt_in bundle=set target=auto_quant_search fields=[fvg_mitigation_pct,ob_mitigation_pct,vi_mitigation_pct] objectives=[cost_adjusted_expectancy,regime_conditioned_win_rate] validation_windows=1"
        );
        assert!(!summary.contains("local/private"));
        assert!(!summary.contains("private"));
        assert!(!summary.contains("window.json"));
    }

    #[test]
    fn test_detector_ga_manifest_export_is_noop_without_bundle() {
        let temp = tempfile::tempdir().unwrap();

        let exported = persist_detector_ga_feature_manifest(temp.path().to_str().unwrap()).unwrap();

        assert!(exported.is_none());
        assert!(!temp.path().join("auto-quant").exists());
    }

    #[test]
    fn test_detector_ga_manifest_export_writes_sanitized_feature_manifest() {
        let temp = tempfile::tempdir().unwrap();
        let config_path = temp.path().join(FACTOR_HOTPLUG_CONFIG_FILE);
        std::fs::write(
            &config_path,
            r#"
families:
  structure_ict: true
detector_ga_bundle:
  bundle_id: ict_detector_ga_v1
  target_consumer: auto_quant_search
  selected_fields:
    - vi_mitigation_pct
    - ob_mitigation_pct
    - vi_mitigation_pct
  optimizer_objectives:
    - cost_adjusted_expectancy
    - regime_conditioned_win_rate
  validation_windows:
    - train_60d_validate_20d
    - local/private/window.json
"#,
        )
        .unwrap();

        let exported = persist_detector_ga_feature_manifest(temp.path().to_str().unwrap())
            .unwrap()
            .unwrap();
        let expected = temp
            .path()
            .join("auto-quant")
            .join("ga_optimizer")
            .join("detector_feature_manifest.json");

        assert_eq!(exported, expected);
        let manifest: serde_json::Value =
            serde_json::from_str(&std::fs::read_to_string(expected).unwrap()).unwrap();

        assert_eq!(
            manifest["schema_version"],
            "ict_detector_ga_feature_manifest_v1"
        );
        assert_eq!(manifest["target_consumer"], "auto_quant_search");
        assert_eq!(manifest["bundle_id"], "ict_detector_ga_v1");
        assert_eq!(
            manifest["selected_fields"],
            serde_json::json!(["ob_mitigation_pct", "vi_mitigation_pct"])
        );
        assert_eq!(
            manifest["optimizer_objectives"],
            serde_json::json!(["cost_adjusted_expectancy", "regime_conditioned_win_rate"])
        );
        assert_eq!(
            manifest["validation_windows"],
            serde_json::json!(["train_60d_validate_20d"])
        );
        assert!(manifest["warnings"]
            .as_array()
            .unwrap()
            .iter()
            .any(|warning| warning == "dropped_unsafe_validation_window_tokens"));

        let raw = serde_json::to_string(&manifest).unwrap();
        assert!(!raw.contains("local/private"));
        assert!(!raw.contains("window.json"));
    }

    #[test]
    fn test_sanitized_example_detector_ga_bundle_parses_and_exports_manifest() {
        let repo_root = Path::new(env!("CARGO_MANIFEST_DIR"));
        let example = repo_root
            .join("support")
            .join("examples")
            .join("factor_hotplug")
            .join("detector-ga-search-v1.yaml");
        let temp = tempfile::tempdir().unwrap();
        let config_path = temp.path().join(FACTOR_HOTPLUG_CONFIG_FILE);
        std::fs::copy(&example, &config_path).unwrap();

        let config = FactorHotplugConfig::load(temp.path().to_str().unwrap())
            .unwrap()
            .unwrap();
        let summary = config.summary_line();

        assert!(summary.contains("detector_ga_bundle=opt_in"));
        assert!(summary.contains("target=auto_quant_search"));
        assert!(!summary.contains("/Users"));
        assert!(!summary.contains("credential_marker"));
        assert!(!summary.contains("token"));

        let manifest_path = persist_detector_ga_feature_manifest(temp.path().to_str().unwrap())
            .unwrap()
            .unwrap();
        let manifest: DetectorGaFeatureManifest =
            serde_json::from_str(&std::fs::read_to_string(manifest_path).unwrap()).unwrap();

        assert_eq!(
            manifest.schema_version,
            DETECTOR_GA_FEATURE_MANIFEST_SCHEMA_VERSION
        );
        assert_eq!(manifest.target_consumer, "auto_quant_search");
        assert_eq!(manifest.bundle_id, "ict_detector_ga_search_v1");
        assert_eq!(
            manifest.selected_fields,
            vec![
                "fvg_mitigation_pct",
                "liquidity_pool_subtype",
                "ob_mitigation_pct",
                "sweep_quality",
                "vi_mitigation_pct"
            ]
        );
        assert!(manifest.warnings.is_empty());

        let raw = serde_json::to_string(&manifest).unwrap();
        assert!(!raw.contains("/Users"));
        assert!(!raw.contains("credential_marker"));
        assert!(!raw.contains("token"));
    }
}
