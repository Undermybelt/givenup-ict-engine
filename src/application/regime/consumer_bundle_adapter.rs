use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{
    collections::{BTreeMap, BTreeSet},
    path::{Path, PathBuf},
};

use crate::application::auto_quant::results::{
    load_strategy_library_manifest, StrategyLibraryEntry, StrategyLibraryEntryStatus,
    StrategyLibraryManifest, STRATEGY_LIBRARY_FILE,
};
use crate::state::PreBayesEvidenceFilter;

const EXPECTED_SCHEMA_VERSION: &str = "regime-consumer-bundle/v1";
const USER_VRP_NQ_CONTEXT_KEYS: [&str; 5] = [
    "qqq_hv_level",
    "nq_vs_200d_pct",
    "vix3m_level",
    "qqq_hv_pct_rank_252",
    "vvix_over_vix",
];

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BundleStatus {
    Disabled,
    Loaded,
    Missing,
    Invalid,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExecutionTreeHint {
    AcceptRegime,
    TransitionGuardrail,
    UnknownAbstain,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RegimeBbnEvidenceStrength {
    Strong,
    Moderate,
    Neutral,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RegimeBbnEvidenceApplicationStatus {
    Applied,
    Skipped,
}

#[derive(Debug, Clone, PartialEq)]
pub struct RegimeReadOnlyBbnSoftEvidence {
    pub strength: RegimeBbnEvidenceStrength,
    pub weight: f64,
    pub decision_state: String,
    pub trade_usable: Option<bool>,
    pub label: Option<String>,
    pub label_set: Vec<String>,
    pub transition_hazard: Option<f64>,
    pub reasons: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RegimeDecisionSummary {
    #[serde(default)]
    pub timestamp: String,
    #[serde(default)]
    pub decision_state: String,
    #[serde(default)]
    pub trade_usable: bool,
    #[serde(default)]
    pub final_label: String,
    #[serde(default)]
    pub label_set: Vec<String>,
    #[serde(default)]
    pub abstain_reasons: Vec<String>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct RegimeConsumerHints {
    #[serde(default)]
    pub execution_tree_hint: String,
    #[serde(default)]
    pub bbn_evidence_hint: Value,
    #[serde(default)]
    pub path_ranker_context: Value,
    #[serde(default)]
    pub user_vrp_nq_context: Value,
    #[serde(default)]
    pub trade_usable: bool,
}

#[derive(Debug, Clone)]
pub struct RegimeConsumerBundleAdapter {
    pub status: BundleStatus,
    pub latest_decision: Option<RegimeDecisionSummary>,
    pub consumer_hints: Option<RegimeConsumerHints>,
    pub error: Option<String>,
}

impl RegimeConsumerBundleAdapter {
    pub fn disabled() -> Self {
        Self {
            status: BundleStatus::Disabled,
            latest_decision: None,
            consumer_hints: None,
            error: None,
        }
    }

    pub fn load_optional(path: Option<&Path>, strict: bool) -> Result<Self> {
        let Some(path) = path else {
            return Ok(Self::disabled());
        };
        if !path.exists() {
            let message = format!("regime consumer bundle missing: {}", path.display());
            if strict {
                return Err(anyhow!(message));
            }
            return Ok(Self::neutral(BundleStatus::Missing, message));
        }

        let raw = match std::fs::read_to_string(path) {
            Ok(raw) => raw,
            Err(err) => {
                let message = format!("failed to read regime consumer bundle: {err}");
                if strict {
                    return Err(anyhow!(message));
                }
                return Ok(Self::neutral(BundleStatus::Invalid, message));
            }
        };
        let payload: Value = match serde_json::from_str(&raw) {
            Ok(payload) => payload,
            Err(err) => {
                let message = format!("invalid regime consumer bundle json: {err}");
                if strict {
                    return Err(anyhow!(message));
                }
                return Ok(Self::neutral(BundleStatus::Invalid, message));
            }
        };
        let schema = payload
            .get("schema_version")
            .and_then(Value::as_str)
            .unwrap_or_default();
        if schema != EXPECTED_SCHEMA_VERSION {
            let message = format!("invalid regime consumer bundle schema: {schema}");
            if strict {
                return Err(anyhow!(message));
            }
            return Ok(Self::neutral(BundleStatus::Invalid, message));
        }

        let latest_decision = payload
            .get("latest_decision")
            .cloned()
            .map(serde_json::from_value)
            .transpose()
            .map_err(|err| anyhow!("invalid latest_decision: {err}"))?;
        let consumer_hints = payload
            .get("consumer_hints")
            .cloned()
            .map(serde_json::from_value)
            .transpose()
            .map_err(|err| anyhow!("invalid consumer_hints: {err}"))?;
        if latest_decision.is_none() || consumer_hints.is_none() {
            let message =
                "invalid regime consumer bundle: missing latest_decision or consumer_hints"
                    .to_string();
            if strict {
                return Err(anyhow!(message));
            }
            return Ok(Self::neutral(BundleStatus::Invalid, message));
        }

        Ok(Self {
            status: BundleStatus::Loaded,
            latest_decision,
            consumer_hints,
            error: None,
        })
    }

    pub fn load_optional_or_strategy_library(
        path: Option<&Path>,
        strict: bool,
        state_dir: &str,
        symbol: &str,
    ) -> Result<Option<Self>> {
        if let Some(path) = path {
            return Self::load_optional(Some(path), strict).map(Some);
        }
        Self::load_from_strategy_library_state(state_dir, symbol)
    }

    fn load_from_strategy_library_state(state_dir: &str, symbol: &str) -> Result<Option<Self>> {
        for path in strategy_library_state_paths(state_dir, symbol) {
            if !path.exists() {
                continue;
            }
            let manifest = match load_strategy_library_manifest(&path) {
                Ok(manifest) => manifest,
                Err(err) => {
                    return Ok(Some(Self::neutral(
                        BundleStatus::Invalid,
                        format!(
                            "invalid auto_quant strategy library at {}: {err}",
                            path.display()
                        ),
                    )));
                }
            };
            return Ok(Self::from_strategy_library_manifest(&manifest));
        }
        Ok(None)
    }

    pub fn from_strategy_library_manifest(manifest: &StrategyLibraryManifest) -> Option<Self> {
        let context = strategy_library_branch_context(manifest)?;
        Some(strategy_library_branch_context_to_adapter(&context))
    }

    pub fn is_loaded(&self) -> bool {
        self.status == BundleStatus::Loaded
    }

    pub fn execution_tree_hint(&self) -> ExecutionTreeHint {
        let raw = self
            .consumer_hints
            .as_ref()
            .map(|hints| hints.execution_tree_hint.as_str())
            .unwrap_or_default();
        match raw {
            "accept_regime" => ExecutionTreeHint::AcceptRegime,
            "transition_guardrail" => ExecutionTreeHint::TransitionGuardrail,
            _ => ExecutionTreeHint::UnknownAbstain,
        }
    }

    pub fn bbn_evidence_hint(&self) -> Option<&Value> {
        self.consumer_hints
            .as_ref()
            .map(|hints| &hints.bbn_evidence_hint)
            .filter(|value| !value.is_null())
    }

    pub fn path_ranker_branch_paths(&self) -> Vec<String> {
        let mut seen = BTreeSet::new();
        let mut paths = Vec::new();
        let mut push_path = |raw: &str| {
            let path = raw.trim();
            if path.is_empty() || !path.contains(" -> ") {
                return;
            }
            if seen.insert(path.to_string()) {
                paths.push(path.to_string());
            }
        };

        if let Some(context) = self
            .consumer_hints
            .as_ref()
            .map(|hints| &hints.path_ranker_context)
        {
            for key in [
                "regime_profit_branch_path",
                "regime_bundle_branch_path",
                "selected_regime_profit_branch_path",
            ] {
                if let Some(path) = context.get(key).and_then(Value::as_str) {
                    push_path(path);
                }
            }
            if let Some(items) = context.get("branch_paths").and_then(Value::as_array) {
                for item in items {
                    if let Some(path) = item.as_str() {
                        push_path(path);
                    }
                }
            }
        }
        if let Some(items) = self
            .bbn_evidence_hint()
            .and_then(|value| value.get("regime_label_set"))
            .and_then(Value::as_array)
        {
            for item in items {
                if let Some(path) = item.as_str() {
                    push_path(path);
                }
            }
        }
        if let Some(decision) = self.latest_decision.as_ref() {
            for path in &decision.label_set {
                push_path(path);
            }
        }
        paths
    }

    pub fn path_ranker_stable_profit_score(&self) -> Option<f64> {
        self.consumer_hints
            .as_ref()
            .and_then(|hints| hints.path_ranker_context.get("stable_profit_score"))
            .and_then(Value::as_f64)
            .map(|score| if score > 1.0 { score / 100.0 } else { score }.clamp(0.0, 1.0))
    }

    pub fn path_ranker_assignment_entries(&self) -> Vec<(String, String)> {
        let branch_paths = self.path_ranker_branch_paths();
        let mut entries = Vec::new();
        if !branch_paths.is_empty() {
            entries.push((
                "regime_bundle_branch_paths_json".to_string(),
                serde_json::to_string(&branch_paths).unwrap_or_else(|_| "[]".to_string()),
            ));
            entries.push((
                "regime_bundle_branch_path_count".to_string(),
                branch_paths.len().to_string(),
            ));
            if let Some(primary_path) = branch_paths.first() {
                entries.extend(regime_profit_branch_assignment_entries(primary_path));
            }
        }
        if let Some(score) = self.path_ranker_stable_profit_score() {
            entries.push((
                "regime_bundle_stable_profit_score".to_string(),
                format!("{score:.6}"),
            ));
        }
        if let Some(direction) = self
            .consumer_hints
            .as_ref()
            .and_then(|hints| hints.path_ranker_context.get("trade_direction"))
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
        {
            entries.push(("trade_direction".to_string(), direction.to_string()));
        }
        entries.extend(self.user_vrp_nq_context_assignment_entries());
        entries
    }

    pub fn user_vrp_nq_context_assignment_entries(&self) -> Vec<(String, String)> {
        self.consumer_hints
            .as_ref()
            .map(|hints| &hints.user_vrp_nq_context)
            .and_then(Value::as_object)
            .map(|context| {
                USER_VRP_NQ_CONTEXT_KEYS
                    .iter()
                    .filter_map(|key| {
                        let value = context.get(*key)?;
                        let rendered = if let Some(number) = value.as_f64() {
                            format!("{number:.6}")
                        } else {
                            value.as_str()?.trim().to_string()
                        };
                        (!rendered.is_empty()).then(|| (format!("regime_aux_{key}"), rendered))
                    })
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default()
    }

    pub fn user_vrp_nq_context_trace_entries(&self) -> Vec<String> {
        self.user_vrp_nq_context_assignment_entries()
            .into_iter()
            .map(|(key, value)| format!("{key}={}", compact_trace_value(&value)))
            .collect()
    }

    pub fn to_read_only_bbn_soft_evidence(&self) -> RegimeReadOnlyBbnSoftEvidence {
        let hint = self.bbn_evidence_hint();
        let decision_state = hint
            .and_then(|value| value.get("regime_decision_state"))
            .and_then(Value::as_str)
            .or_else(|| {
                self.latest_decision
                    .as_ref()
                    .map(|decision| decision.decision_state.as_str())
            })
            .unwrap_or_default()
            .to_string();
        let trade_usable = hint
            .and_then(|value| value.get("regime_trade_usable"))
            .and_then(Value::as_bool)
            .or_else(|| {
                self.latest_decision
                    .as_ref()
                    .map(|decision| decision.trade_usable)
            });
        let label = hint
            .and_then(|value| value.get("regime_label"))
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .map(ToString::to_string)
            .or_else(|| {
                self.latest_decision
                    .as_ref()
                    .map(|decision| decision.final_label.as_str())
                    .filter(|value| !value.is_empty())
                    .map(ToString::to_string)
            });
        let label_set = hint
            .and_then(|value| value.get("regime_label_set"))
            .and_then(Value::as_array)
            .map(|items| {
                items
                    .iter()
                    .filter_map(Value::as_str)
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
            })
            .filter(|items| !items.is_empty())
            .or_else(|| {
                self.latest_decision
                    .as_ref()
                    .map(|decision| decision.label_set.clone())
            })
            .map(canonicalize_regime_bbn_label_set)
            .unwrap_or_default();
        let transition_hazard = hint
            .and_then(|value| value.get("regime_transition_hazard"))
            .and_then(Value::as_f64);
        let reasons = hint
            .and_then(|value| value.get("regime_decision_reasons"))
            .and_then(Value::as_array)
            .map(|items| {
                items
                    .iter()
                    .filter_map(Value::as_str)
                    .map(ToString::to_string)
                    .collect::<Vec<_>>()
            })
            .filter(|items| !items.is_empty())
            .or_else(|| {
                self.latest_decision
                    .as_ref()
                    .map(|decision| decision.abstain_reasons.clone())
            })
            .unwrap_or_default();
        let (strength, weight) = match (self.is_loaded(), decision_state.as_str(), trade_usable) {
            (true, "single_label_99", Some(true)) => (RegimeBbnEvidenceStrength::Strong, 0.9),
            (true, "single_label_95", Some(true)) | (true, "accepted", Some(true)) => {
                (RegimeBbnEvidenceStrength::Moderate, 0.65)
            }
            _ => (RegimeBbnEvidenceStrength::Neutral, 0.0),
        };

        RegimeReadOnlyBbnSoftEvidence {
            strength,
            weight,
            decision_state,
            trade_usable,
            label,
            label_set,
            transition_hazard,
            reasons,
        }
    }

    pub fn trace_entries(&self, path: Option<&Path>) -> Vec<String> {
        let mut entries = vec![format!(
            "regime_bundle_status={}",
            self.status.as_trace_value()
        )];
        if let Some(path) = path {
            entries.push(format!("regime_bundle_path={}", path.display()));
        }
        if let Some(error) = self.error.as_ref() {
            entries.push(format!(
                "regime_bundle_error={}",
                compact_trace_value(error)
            ));
        }
        if let Some(decision) = self.latest_decision.as_ref() {
            entries.push(format!(
                "regime_decision_state={}",
                compact_trace_value(&decision.decision_state)
            ));
            entries.push(format!("regime_trade_usable={}", decision.trade_usable));
            if !decision.final_label.is_empty() {
                entries.push(format!(
                    "regime_final_label={}",
                    compact_trace_value(&decision.final_label)
                ));
            }
        }
        entries.push(format!(
            "regime_execution_tree_hint={}",
            self.execution_tree_hint().as_trace_value()
        ));
        entries.extend(self.user_vrp_nq_context_trace_entries());
        entries
    }

    pub fn bbn_soft_evidence_trace_entries(&self) -> Vec<String> {
        let mut entries = self.to_read_only_bbn_soft_evidence().trace_entries();
        entries.extend(self.user_vrp_nq_context_trace_entries());
        entries
    }

    pub fn append_read_only_bbn_diagnostics(
        &self,
        artifact_action_summary: &mut Vec<String>,
        pre_bayes_filter: &mut PreBayesEvidenceFilter,
    ) {
        let bbn_trace_entries = self.bbn_soft_evidence_trace_entries();
        artifact_action_summary.push(format!(
            "regime_bbn_soft_evidence_trace:{}",
            bbn_trace_entries.join("|")
        ));
        artifact_action_summary.extend(bbn_trace_entries.iter().cloned());
        self.append_read_only_bbn_filter_diagnostics(pre_bayes_filter);
    }

    pub fn append_read_only_bbn_filter_diagnostics(
        &self,
        pre_bayes_filter: &mut PreBayesEvidenceFilter,
    ) {
        let bbn_trace_entries = self.bbn_soft_evidence_trace_entries();
        for entry in bbn_trace_entries {
            let rationale = format!("read_only_{entry}");
            if !pre_bayes_filter.rationale.contains(&rationale) {
                pre_bayes_filter.rationale.push(rationale);
            }
            if let Some((key, value)) = entry.split_once('=') {
                pre_bayes_filter
                    .evidence_assignments
                    .insert(format!("read_only_{key}"), value.to_string());
            }
        }
    }

    pub fn apply_bbn_soft_evidence_to_pre_bayes_filter(
        &self,
        filter: &mut PreBayesEvidenceFilter,
        opt_in: bool,
    ) -> RegimeBbnEvidenceApplicationStatus {
        if !opt_in {
            filter
                .rationale
                .push("regime_bundle_bbn_evidence_skipped=flag_disabled".to_string());
            return RegimeBbnEvidenceApplicationStatus::Skipped;
        }

        let evidence = self.to_read_only_bbn_soft_evidence();
        let Some(bbn_label) = evidence.bbn_market_regime_label() else {
            filter
                .rationale
                .push("regime_bundle_bbn_evidence_skipped=no_supported_label".to_string());
            return RegimeBbnEvidenceApplicationStatus::Skipped;
        };
        if evidence.strength == RegimeBbnEvidenceStrength::Neutral || evidence.weight <= 0.0 {
            filter.rationale.push(format!(
                "regime_bundle_bbn_evidence_skipped=strength:{}",
                evidence.strength.as_trace_value()
            ));
            return RegimeBbnEvidenceApplicationStatus::Skipped;
        }

        filter.uses_soft_evidence = true;
        filter.filtered_market_regime_label = bbn_label.to_string();
        filter
            .evidence_assignments
            .insert("market_regime".to_string(), bbn_label.to_string());
        filter.soft_market_regime_distribution =
            market_regime_distribution(bbn_label, evidence.weight);
        if evidence.trade_usable == Some(true) {
            let hard_floor = filter.policy.hard_pass_quality_threshold.max(0.75);
            let neutral_floor = filter.policy.neutralized_quality_threshold.max(0.40);
            let quality_floor = match evidence.strength {
                RegimeBbnEvidenceStrength::Strong => hard_floor.max(0.90),
                RegimeBbnEvidenceStrength::Moderate => hard_floor,
                RegimeBbnEvidenceStrength::Neutral => neutral_floor,
            };
            if filter.evidence_quality_score < quality_floor {
                filter.evidence_quality_score = quality_floor;
                filter.rationale.push(format!(
                    "regime_bundle_bbn_quality_floor_applied={:.3}",
                    quality_floor
                ));
            }
            if filter.conflict_flags.is_empty()
                && filter.evidence_quality_score >= filter.policy.hard_pass_quality_threshold
            {
                filter.gating_status = "pass_hard".to_string();
                filter.pass_to_bbn = true;
                filter
                    .rationale
                    .push("regime_bundle_bbn_evidence_promoted_gate_to_pass_hard".to_string());
            } else if filter.evidence_quality_score >= filter.policy.neutralized_quality_threshold
                && filter.gating_status == "observe_only"
            {
                filter.gating_status = "pass_neutralized".to_string();
                filter.pass_to_bbn = true;
                filter.rationale.push(
                    "regime_bundle_bbn_evidence_promoted_gate_to_pass_neutralized".to_string(),
                );
            }
        }
        filter.evidence_assignments.insert(
            "regime_bundle_bbn_evidence_application".to_string(),
            "applied".to_string(),
        );
        filter.evidence_assignments.insert(
            "regime_bundle_bbn_market_regime".to_string(),
            bbn_label.to_string(),
        );
        filter.evidence_assignments.insert(
            "regime_bundle_bbn_evidence_weight".to_string(),
            format!("{:.3}", evidence.weight),
        );
        filter.rationale.push(format!(
            "regime_bundle_bbn_evidence_applied=strength:{} label:{}",
            evidence.strength.as_trace_value(),
            evidence.label.as_deref().unwrap_or("unknown")
        ));
        RegimeBbnEvidenceApplicationStatus::Applied
    }

    fn neutral(status: BundleStatus, error: String) -> Self {
        Self {
            status,
            latest_decision: None,
            consumer_hints: None,
            error: Some(error),
        }
    }
}

#[derive(Debug, Clone)]
struct StrategyLibraryBranchContext {
    branch_path: String,
    main_regime: String,
    sub_regime: String,
    sub_sub_regime_or_profit_factor: String,
    profit_factor: String,
    trade_direction: Option<String>,
    stable_profit_score: Option<f64>,
    quality_score: f64,
    strategy_name: String,
    trade_usable: bool,
    promotion_allowed: bool,
}

fn strategy_library_branch_context(
    manifest: &StrategyLibraryManifest,
) -> Option<StrategyLibraryBranchContext> {
    let contexts = manifest
        .strategies
        .iter()
        .filter(|entry| matches!(entry.status_kind(), StrategyLibraryEntryStatus::Ok))
        .filter_map(strategy_library_entry_branch_context)
        .collect::<Vec<_>>();
    contexts.into_iter().max_by(|left, right| {
        strategy_library_branch_rank_key(left).cmp(&strategy_library_branch_rank_key(right))
    })
}

fn strategy_library_entry_branch_context(
    entry: &StrategyLibraryEntry,
) -> Option<StrategyLibraryBranchContext> {
    let metadata = &entry.metadata;
    let raw_branch_path = first_non_empty([
        metadata.regime_profit_branch_path.as_str(),
        metadata.expected_regime.as_str(),
    ])?;
    if !raw_branch_path.contains(" -> ") {
        return None;
    }
    let segments = regime_segments_for_assignment(raw_branch_path);
    if segments.len() < 4 {
        return None;
    }
    let profit_factor_fallback = segments[3..].join(" -> ");
    let branch_path = segments.join(" -> ");
    let stable_profit_score = entry.validation_metrics.as_ref().and_then(|metrics| {
        if metrics.win_rate_pct > 0.0 {
            Some(metrics.win_rate_pct)
        } else if metrics.total_profit_pct > 0.0 {
            Some(metrics.total_profit_pct)
        } else {
            None
        }
    });
    Some(StrategyLibraryBranchContext {
        branch_path,
        main_regime: first_non_empty([
            metadata.main_regime.as_str(),
            segments.first().copied().unwrap_or_default(),
        ])?
        .to_string(),
        sub_regime: first_non_empty([
            metadata.sub_regime.as_str(),
            segments.get(1).copied().unwrap_or_default(),
        ])?
        .to_string(),
        sub_sub_regime_or_profit_factor: first_non_empty([
            metadata.sub_sub_regime_or_profit_factor.as_str(),
            segments.get(2).copied().unwrap_or_default(),
        ])?
        .to_string(),
        profit_factor: first_non_empty([
            metadata.profit_factor.as_str(),
            profit_factor_fallback.as_str(),
        ])?
        .to_string(),
        trade_direction: normalized_strategy_trade_direction(metadata),
        stable_profit_score,
        quality_score: strategy_library_quality_score(entry.validation_metrics.as_ref()),
        strategy_name: entry.name.clone(),
        trade_usable: metadata.trade_usable,
        promotion_allowed: metadata.promotion_allowed,
    })
}

fn strategy_library_quality_score(
    metrics: Option<&crate::application::auto_quant::results::StrategyLibraryValidationMetrics>,
) -> f64 {
    let Some(metrics) = metrics else {
        return f64::NEG_INFINITY;
    };
    metrics.sharpe * 1000.0
        + metrics.total_profit_pct * 10.0
        + metrics.profit_factor * 100.0
        + metrics.win_rate_pct
}

fn strategy_library_branch_rank_key(
    context: &StrategyLibraryBranchContext,
) -> (i64, i64, i64, String) {
    (
        (context.quality_score * 1000.0).round() as i64,
        (context.stable_profit_score.unwrap_or(f64::NEG_INFINITY) * 1000.0).round() as i64,
        if context.trade_usable { 1 } else { 0 },
        context.strategy_name.clone(),
    )
}

fn strategy_library_branch_context_to_adapter(
    context: &StrategyLibraryBranchContext,
) -> RegimeConsumerBundleAdapter {
    // Strategy-library imports are advisory branch traces until the current
    // runtime explicitly revalidates the live plane.
    let decision_state = "auto_quant_strategy_library_branch_context";
    let runtime_trade_usable = false;
    RegimeConsumerBundleAdapter {
        status: BundleStatus::Loaded,
        latest_decision: Some(RegimeDecisionSummary {
            timestamp: String::new(),
            decision_state: decision_state.to_string(),
            trade_usable: runtime_trade_usable,
            final_label: format!("primary::{}", context.main_regime),
            label_set: vec![
                format!("primary::{}", context.main_regime),
                context.branch_path.clone(),
            ],
            abstain_reasons: vec![
                "imported_auto_quant_strategy_library".to_string(),
                if context.promotion_allowed {
                    "promotion_not_granted_by_runtime".to_string()
                } else {
                    "non_promoting_branch_trace".to_string()
                },
            ],
        }),
        consumer_hints: Some(RegimeConsumerHints {
            execution_tree_hint: "observe_branch_context".to_string(),
            bbn_evidence_hint: serde_json::json!({
                "regime_decision_state": decision_state,
                "regime_trade_usable": runtime_trade_usable,
                "regime_label": format!("primary::{}", context.main_regime),
                "regime_label_set": [
                    format!("primary::{}", context.main_regime),
                    context.branch_path
                ],
                "regime_transition_hazard": 0.0,
                "regime_decision_reasons": [
                    format!("strategy_name={}", context.strategy_name),
                    "imported_auto_quant_strategy_library",
                    if context.promotion_allowed {
                        "promotion_not_granted_by_runtime"
                    } else {
                        "non_promoting_branch_trace"
                    }
                ]
            }),
            path_ranker_context: serde_json::json!({
                "regime_profit_branch_path": context.branch_path,
                "main_regime": context.main_regime,
                "sub_regime": context.sub_regime,
                "sub_sub_regime_or_profit_factor": context.sub_sub_regime_or_profit_factor,
                "profit_factor": context.profit_factor,
                "trade_direction": context.trade_direction,
                "stable_profit_score": context.stable_profit_score
            }),
            user_vrp_nq_context: Value::Null,
            trade_usable: runtime_trade_usable,
        }),
        error: Some(format!(
            "source=auto_quant_strategy_library strategy={}",
            context.strategy_name
        )),
    }
}

fn normalized_strategy_trade_direction(
    metadata: &crate::application::auto_quant::results::StrategyLibraryMetadata,
) -> Option<String> {
    let raw = first_non_empty([
        metadata.trade_direction.as_str(),
        metadata.direction.as_str(),
    ])?;
    match raw.trim().to_ascii_lowercase().as_str() {
        "bear" | "short" | "sell" => Some("Bear".to_string()),
        "bull" | "long" | "buy" => Some("Bull".to_string()),
        "neutral" | "observe" => Some("Neutral".to_string()),
        _ => None,
    }
}

impl BundleStatus {
    fn as_trace_value(&self) -> &'static str {
        match self {
            BundleStatus::Disabled => "disabled",
            BundleStatus::Loaded => "loaded",
            BundleStatus::Missing => "missing",
            BundleStatus::Invalid => "invalid",
        }
    }
}

impl ExecutionTreeHint {
    fn as_trace_value(&self) -> &'static str {
        match self {
            ExecutionTreeHint::AcceptRegime => "accept_regime",
            ExecutionTreeHint::TransitionGuardrail => "transition_guardrail",
            ExecutionTreeHint::UnknownAbstain => "unknown_abstain",
        }
    }
}

impl RegimeBbnEvidenceStrength {
    fn as_trace_value(&self) -> &'static str {
        match self {
            RegimeBbnEvidenceStrength::Strong => "strong",
            RegimeBbnEvidenceStrength::Moderate => "moderate",
            RegimeBbnEvidenceStrength::Neutral => "neutral",
        }
    }
}

impl RegimeReadOnlyBbnSoftEvidence {
    fn trace_entries(&self) -> Vec<String> {
        let mut entries = vec![
            format!(
                "regime_bbn_soft_evidence_strength={}",
                self.strength.as_trace_value()
            ),
            format!("regime_bbn_soft_evidence_weight={:.3}", self.weight),
            format!(
                "regime_bbn_decision_state={}",
                compact_trace_value(&self.decision_state)
            ),
        ];
        if let Some(trade_usable) = self.trade_usable {
            entries.push(format!("regime_bbn_trade_usable={trade_usable}"));
        }
        if let Some(label) = self.label.as_ref() {
            entries.push(format!("regime_bbn_label={}", compact_trace_value(label)));
        }
        if !self.label_set.is_empty() {
            entries.push(format!(
                "regime_bbn_label_set={}",
                self.label_set
                    .iter()
                    .map(|label| compact_trace_value(label))
                    .collect::<Vec<_>>()
                    .join(",")
            ));
        }
        if let Some(transition_hazard) = self.transition_hazard {
            entries.push(format!(
                "regime_bbn_transition_hazard={transition_hazard:.3}"
            ));
        }
        if !self.reasons.is_empty() {
            entries.push(format!(
                "regime_bbn_reasons={}",
                self.reasons
                    .iter()
                    .map(|reason| compact_trace_value(reason))
                    .collect::<Vec<_>>()
                    .join(",")
            ));
        }
        entries
    }

    fn bbn_market_regime_label(&self) -> Option<&'static str> {
        let mut supported_labels = self
            .label
            .as_deref()
            .into_iter()
            .chain(self.label_set.iter().map(String::as_str))
            .filter_map(regime_bundle_label_to_bbn_market_regime)
            .collect::<Vec<_>>();
        supported_labels.sort_unstable();
        supported_labels.dedup();
        match supported_labels.as_slice() {
            [label] => Some(*label),
            _ => None,
        }
    }
}

fn regime_bundle_label_to_bbn_market_regime(label: &str) -> Option<&'static str> {
    let primary = label.split('/').next().unwrap_or(label).trim();
    if primary == "Bull" || primary.starts_with("Bull ->") {
        return Some("bull");
    }
    if primary == "Bear" || primary.starts_with("Bear ->") {
        return Some("bear");
    }
    if primary == "Sideways" || primary.starts_with("Sideways ->") {
        return Some("range");
    }
    if primary == "Crisis" || primary.starts_with("Crisis ->") {
        return Some("range");
    }
    match primary {
        "primary::TrendExpansion" | "TrendExpansion" => Some("bull"),
        "primary::BearReliefCarry" | "BearReliefCarry" => Some("bear"),
        "primary::RangeConsolidation" | "RangeConsolidation" => Some("range"),
        "primary::ExtremeStress" | "ExtremeStress" => Some("range"),
        "primary::ReversalBrewing" | "ReversalBrewing" => Some("range"),
        _ => None,
    }
}

fn regime_profit_branch_assignment_entries(branch_path: &str) -> Vec<(String, String)> {
    let segments = regime_segments_for_assignment(branch_path);
    let canonical_branch_path = segments.join(" -> ");
    let mut entries = vec![(
        "regime_profit_branch_path".to_string(),
        canonical_branch_path,
    )];
    if let Some(main) = segments.first() {
        entries.push(("parent_regime_root".to_string(), (*main).to_string()));
        entries.push(("main_regime".to_string(), (*main).to_string()));
    }
    if let Some(sub) = segments.get(1) {
        entries.push(("sub_regime".to_string(), (*sub).to_string()));
    }
    if let Some(sub_sub) = segments.get(2) {
        entries.push((
            "sub_sub_regime_or_profit_factor".to_string(),
            (*sub_sub).to_string(),
        ));
    }
    if segments.len() > 3 {
        entries.push(("profit_factor".to_string(), segments[3..].join(" -> ")));
    }
    entries
}

fn canonicalize_regime_bbn_label_set(labels: Vec<String>) -> Vec<String> {
    let mut seen = BTreeSet::new();
    let mut canonical = Vec::new();
    for label in labels {
        let trimmed = label.trim();
        if trimmed.is_empty() {
            continue;
        }
        let normalized = if trimmed.contains(" -> ") {
            let segments = regime_segments_for_assignment(trimmed);
            segments.join(" -> ")
        } else {
            trimmed.to_string()
        };
        if seen.insert(normalized.clone()) {
            canonical.push(normalized);
        }
    }
    canonical
}

fn branch_path_segments(branch_path: &str) -> Vec<&str> {
    branch_path
        .split(" -> ")
        .map(str::trim)
        .filter(|segment| !segment.is_empty())
        .collect()
}

fn regime_segments_for_assignment(branch_path: &str) -> Vec<&str> {
    let segments = branch_path_segments(branch_path);
    if segments.len() >= 7 && looks_like_market_rooted_branch(&segments) {
        return segments[4..].to_vec();
    }
    segments
}

fn looks_like_market_rooted_branch(segments: &[&str]) -> bool {
    matches!(
        segments.first().copied(),
        Some("FUTURES")
            | Some("FUTURES_LIKE")
            | Some("US_EQ")
            | Some("EQUITIES")
            | Some("ETF")
            | Some("CRYPTO")
            | Some("FX")
            | Some("OPTIONS")
    )
}

fn market_regime_distribution(selected: &str, weight: f64) -> BTreeMap<String, f64> {
    let clamped = weight.clamp(0.0, 1.0);
    let remainder = (1.0 - clamped) / 2.0;
    ["bull", "bear", "range"]
        .into_iter()
        .map(|state| {
            let probability = if state == selected {
                clamped
            } else {
                remainder
            };
            (state.to_string(), probability)
        })
        .collect()
}

fn compact_trace_value(value: &str) -> String {
    value.split_whitespace().collect::<Vec<_>>().join("_")
}

fn first_non_empty<'a>(values: impl IntoIterator<Item = &'a str>) -> Option<&'a str> {
    values
        .into_iter()
        .map(str::trim)
        .find(|value| !value.is_empty())
}

fn strategy_library_state_paths(state_dir: &str, symbol: &str) -> Vec<PathBuf> {
    let mut paths = Vec::new();
    paths.push(
        Path::new(state_dir)
            .join(symbol)
            .join(STRATEGY_LIBRARY_FILE),
    );
    let auto_quant_dir = auto_quant_state_dir(state_dir);
    let auto_quant_path = auto_quant_dir.join(symbol).join(STRATEGY_LIBRARY_FILE);
    if !paths.iter().any(|path| path == &auto_quant_path) {
        paths.push(auto_quant_path);
    }
    paths
}

fn auto_quant_state_dir(state_dir: &str) -> PathBuf {
    let state_dir_path = Path::new(state_dir);
    if state_dir_path.join("auto_quant_config.json").exists()
        || state_dir_path.join(".deps").join("auto-quant").exists()
    {
        return state_dir_path.to_path_buf();
    }
    if let Some(custom) = std::env::var("ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR")
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
    {
        return PathBuf::from(custom);
    }
    state_dir_path.join("auto-quant")
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::PreBayesEvidencePolicy;

    #[test]
    fn strategy_library_manifest_can_become_branch_adapter() {
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [{
                "name": "MarketStructureEventClassifierAtrCisdDirectLimitV1",
                "status": "ok",
                "metadata": {
                    "strategy": "MarketStructureEventClassifierAtrCisdDirectLimitV1",
                    "expected_regime": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                    "main_regime": "Transition",
                    "sub_regime": "MarketStructureEvent",
                    "sub_sub_regime_or_profit_factor": "atr_cisd_direct_limit",
                    "profit_factor": "market_structure_event_classifier_atr_cisd_direct_limit_v1",
                    "direction": "short",
                    "trade_direction": "Bear",
                    "regime_profit_branch_path": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                    "promotion_allowed": false,
                    "trade_usable": false
                },
                "validation_metrics": {
                    "win_rate_pct": 71.95572
                }
            }]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let assignment_map = adapter
            .path_ranker_assignment_entries()
            .into_iter()
            .collect::<BTreeMap<_, _>>();

        assert_eq!(
            assignment_map.get("regime_profit_branch_path"),
            Some(
                &"Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1"
                    .to_string()
            )
        );
        assert_eq!(
            assignment_map.get("regime_bundle_stable_profit_score"),
            Some(&"0.719557".to_string())
        );
        assert_eq!(
            assignment_map.get("main_regime"),
            Some(&"Transition".to_string())
        );
        assert_eq!(
            assignment_map.get("sub_regime"),
            Some(&"MarketStructureEvent".to_string())
        );
        assert_eq!(
            assignment_map.get("trade_direction"),
            Some(&"Bear".to_string())
        );
    }

    #[test]
    fn market_rooted_branch_uses_canonical_branch_identity_for_bbn_assignments() {
        let canonical_branch = "TrendExpansion -> OpeningVwapRvolReclaim -> ibkr_mnq_1h_opening_vwap_rvol_reclaim_exact_v1 -> pda_transition_light_guard_v1";
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [{
                "name": "IbkrMnqPdaTransitionLightGuard",
                "status": "ok",
                "metadata": {
                    "regime_profit_branch_path": "FUTURES -> equity_index -> MNQ -> 1h -> TrendExpansion -> OpeningVwapRvolReclaim -> ibkr_mnq_1h_opening_vwap_rvol_reclaim_exact_v1 -> pda_transition_light_guard_v1",
                    "main_regime": "TrendExpansion",
                    "sub_regime": "OpeningVwapRvolReclaim",
                    "sub_sub_regime_or_profit_factor": "ibkr_mnq_1h_opening_vwap_rvol_reclaim_exact_v1",
                    "profit_factor": "pda_transition_light_guard_v1",
                    "promotion_allowed": false,
                    "trade_usable": false
                },
                "validation_metrics": {
                    "win_rate_pct": 72.7273,
                    "total_profit_pct": 2.01
                }
            }]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let assignment_map = adapter
            .path_ranker_assignment_entries()
            .into_iter()
            .collect::<BTreeMap<_, _>>();

        assert_eq!(
            assignment_map.get("regime_profit_branch_path"),
            Some(&canonical_branch.to_string())
        );
        assert_eq!(
            assignment_map.get("parent_regime_root"),
            Some(&"TrendExpansion".to_string())
        );
        assert_eq!(
            assignment_map.get("main_regime"),
            Some(&"TrendExpansion".to_string())
        );
        assert_eq!(
            assignment_map.get("sub_regime"),
            Some(&"OpeningVwapRvolReclaim".to_string())
        );
        assert_eq!(
            assignment_map.get("sub_sub_regime_or_profit_factor"),
            Some(&"ibkr_mnq_1h_opening_vwap_rvol_reclaim_exact_v1".to_string())
        );
        assert_eq!(
            assignment_map.get("profit_factor"),
            Some(&"pda_transition_light_guard_v1".to_string())
        );
    }

    #[test]
    fn us_equity_rooted_branch_uses_canonical_branch_identity_for_bbn_assignments() {
        let canonical_branch = "RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1";
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [{
                "name": "YfAiSecurityCrwd5mPdaMtfSoftConfirmation",
                "status": "ok",
                "metadata": {
                    "regime_profit_branch_path": "US_EQ -> single_stock -> CRWD -> 5m -> RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1",
                    "main_regime": "RangeReversion",
                    "sub_regime": "AiSecuritySoftwareOversoldReclaim",
                    "sub_sub_regime_or_profit_factor": "rsi_vwap_reclaim_dense",
                    "profit_factor": "yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1",
                    "promotion_allowed": false,
                    "trade_usable": false
                },
                "validation_metrics": {
                    "win_rate_pct": 62.7907,
                    "total_profit_pct": 5.81
                }
            }]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let assignment_map = adapter
            .path_ranker_assignment_entries()
            .into_iter()
            .collect::<BTreeMap<_, _>>();

        assert_eq!(
            assignment_map.get("regime_profit_branch_path"),
            Some(&canonical_branch.to_string())
        );
        assert_eq!(
            assignment_map.get("parent_regime_root"),
            Some(&"RangeReversion".to_string())
        );
        assert_eq!(
            assignment_map.get("main_regime"),
            Some(&"RangeReversion".to_string())
        );
        assert_eq!(
            assignment_map.get("sub_regime"),
            Some(&"AiSecuritySoftwareOversoldReclaim".to_string())
        );
        assert_eq!(
            assignment_map.get("sub_sub_regime_or_profit_factor"),
            Some(&"rsi_vwap_reclaim_dense".to_string())
        );
        assert_eq!(
            assignment_map.get("profit_factor"),
            Some(&"yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1".to_string())
        );
        let read_only = adapter.to_read_only_bbn_soft_evidence();
        assert_eq!(
            read_only.label_set,
            vec![
                "primary::RangeReversion".to_string(),
                canonical_branch.to_string()
            ]
        );
        assert!(!read_only
            .label_set
            .iter()
            .any(|label| label.starts_with("US_EQ -> single_stock -> CRWD -> 5m ->")));
    }

    #[test]
    fn strategy_library_branch_context_prefers_profitable_strategy_over_higher_win_rate_loser() {
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [
                {
                    "name": "LosingMeanRevert",
                    "status": "ok",
                    "metadata": {
                        "expected_regime": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                        "main_regime": "Transition",
                        "sub_regime": "MarketStructureEvent",
                        "sub_sub_regime_or_profit_factor": "atr_cisd_direct_limit",
                        "profit_factor": "LosingMeanRevert",
                        "regime_profit_branch_path": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                        "promotion_allowed": false,
                        "trade_usable": false
                    },
                    "validation_metrics": {
                        "sharpe": -0.6937,
                        "sortino": -0.7246,
                        "calmar": -0.9422,
                        "total_profit_pct": -38.5,
                        "max_drawdown_pct": -42.8407,
                        "trade_count": 651,
                        "win_rate_pct": 56.6820,
                        "profit_factor": 0.7424
                    }
                },
                {
                    "name": "WinningBreakout",
                    "status": "ok",
                    "metadata": {
                        "expected_regime": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                        "main_regime": "Transition",
                        "sub_regime": "MarketStructureEvent",
                        "sub_sub_regime_or_profit_factor": "atr_cisd_direct_limit",
                        "profit_factor": "WinningBreakout",
                        "regime_profit_branch_path": "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1",
                        "promotion_allowed": false,
                        "trade_usable": false
                    },
                    "validation_metrics": {
                        "sharpe": 0.1649,
                        "sortino": 0.4788,
                        "calmar": 0.5075,
                        "total_profit_pct": 25.73,
                        "max_drawdown_pct": -53.1883,
                        "trade_count": 2835,
                        "win_rate_pct": 33.8977,
                        "profit_factor": 1.0197
                    }
                }
            ]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let read_only = adapter.to_read_only_bbn_soft_evidence();
        assert!(read_only
            .reasons
            .iter()
            .any(|reason| reason.contains("strategy_name=WinningBreakout")));
        let assignment_map = adapter
            .path_ranker_assignment_entries()
            .into_iter()
            .collect::<BTreeMap<_, _>>();
        assert_eq!(
            assignment_map.get("regime_bundle_stable_profit_score"),
            Some(&"0.338977".to_string())
        );
    }

    #[test]
    fn strategy_library_branch_context_selects_best_profitable_branch_across_multiple_paths() {
        let losing_branch =
            "TrendExpansion -> MomentumPersistence -> macd_signal_pullback -> macd_signal_pullback_continuation_v1";
        let winning_branch =
            "TrendExpansion -> MomentumPersistence -> macd_zero_line_reclaim -> macd_zero_line_reclaim_long_v1";
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [
                {
                    "name": "MacdSignalPullbackLosing",
                    "status": "ok",
                    "metadata": {
                        "main_regime": "TrendExpansion",
                        "sub_regime": "MomentumPersistence",
                        "sub_sub_regime_or_profit_factor": "macd_signal_pullback",
                        "profit_factor": "macd_signal_pullback_continuation_v1",
                        "regime_profit_branch_path": losing_branch,
                        "promotion_allowed": false,
                        "trade_usable": false
                    },
                    "validation_metrics": {
                        "sharpe": -0.4972,
                        "total_profit_pct": -2.36,
                        "trade_count": 16,
                        "win_rate_pct": 25.0,
                        "profit_factor": 0.7424
                    }
                },
                {
                    "name": "MacdZeroLineIbkrSpy",
                    "status": "ok",
                    "metadata": {
                        "main_regime": "TrendExpansion",
                        "sub_regime": "MomentumPersistence",
                        "sub_sub_regime_or_profit_factor": "macd_zero_line_reclaim",
                        "profit_factor": "macd_zero_line_reclaim_long_v1",
                        "regime_profit_branch_path": winning_branch,
                        "promotion_allowed": false,
                        "trade_usable": false
                    },
                    "validation_metrics": {
                        "sharpe": 0.6358,
                        "total_profit_pct": 3.15,
                        "trade_count": 17,
                        "win_rate_pct": 58.8235,
                        "profit_factor": 1.20
                    }
                }
            ]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let assignment_map = adapter
            .path_ranker_assignment_entries()
            .into_iter()
            .collect::<BTreeMap<_, _>>();

        assert_eq!(
            assignment_map.get("regime_profit_branch_path"),
            Some(&winning_branch.to_string())
        );
        assert_eq!(
            assignment_map.get("profit_factor"),
            Some(&"macd_zero_line_reclaim_long_v1".to_string())
        );
        let read_only = adapter.to_read_only_bbn_soft_evidence();
        assert!(read_only
            .reasons
            .iter()
            .any(|reason| reason.contains("strategy_name=MacdZeroLineIbkrSpy")));
    }

    #[test]
    fn applied_single_label_95_bundle_syncs_assignments_and_can_hard_pass_filter() {
        let file = tempfile::NamedTempFile::new().unwrap();
        std::fs::write(
            file.path(),
            serde_json::to_string(&serde_json::json!({
                "schema_version": "regime-consumer-bundle/v1",
                "latest_decision": {
                    "decision_state": "single_label_95",
                    "trade_usable": true,
                    "final_label": "Bull",
                    "label_set": ["Bull", "Bull -> AcceptedRecovery -> bull_sourcebacked_drawdown_volatility_v1 -> recovered_rule_replay"],
                    "abstain_reasons": ["recovered_accepted_regime_confidence_asset"]
                },
                "consumer_hints": {
                    "execution_tree_hint": "accept_regime",
                    "bbn_evidence_hint": {
                        "regime_decision_state": "single_label_95",
                        "regime_trade_usable": true,
                        "regime_label": "Bull",
                        "regime_label_set": ["Bull", "Bull -> AcceptedRecovery -> bull_sourcebacked_drawdown_volatility_v1 -> recovered_rule_replay"],
                        "regime_transition_hazard": 0.0,
                        "regime_decision_reasons": ["recovered_accepted_regime_confidence_asset"]
                    },
                    "path_ranker_context": {
                        "regime_profit_branch_path": "Bull -> AcceptedRecovery -> bull_sourcebacked_drawdown_volatility_v1 -> recovered_rule_replay",
                        "main_regime": "Bull",
                        "sub_regime": "AcceptedRecovery",
                        "sub_sub_regime_or_profit_factor": "bull_sourcebacked_drawdown_volatility_v1",
                        "profit_factor": "recovered_rule_replay",
                        "stable_profit_score": 0.952516
                    },
                    "user_vrp_nq_context": null,
                    "trade_usable": true
                }
            }))
            .unwrap(),
        )
        .unwrap();

        let adapter = RegimeConsumerBundleAdapter::load_optional(Some(file.path()), true).unwrap();
        let mut filter = PreBayesEvidenceFilter {
            policy: PreBayesEvidencePolicy {
                hard_pass_quality_threshold: 0.75,
                neutralized_quality_threshold: 0.40,
                ..PreBayesEvidencePolicy::default()
            },
            filtered_market_regime_label: "range".to_string(),
            filtered_liquidity_context_label: "neutral".to_string(),
            filtered_factor_alignment: "mixed".to_string(),
            filtered_factor_uncertainty: "low".to_string(),
            filtered_multi_timeframe_direction_bias: "bullish".to_string(),
            filtered_multi_timeframe_resonance_label: "aligned".to_string(),
            evidence_quality_score: 0.624,
            gating_status: "pass_neutralized".to_string(),
            pass_to_bbn: true,
            uses_soft_evidence: true,
            evidence_assignments: BTreeMap::from([
                ("market_regime".to_string(), "range".to_string()),
                ("liquidity_context".to_string(), "neutral".to_string()),
                ("factor_alignment".to_string(), "mixed".to_string()),
                ("factor_uncertainty".to_string(), "low".to_string()),
            ]),
            ..PreBayesEvidenceFilter::default()
        };

        let status = adapter.apply_bbn_soft_evidence_to_pre_bayes_filter(&mut filter, true);

        assert_eq!(status, RegimeBbnEvidenceApplicationStatus::Applied);
        assert_eq!(filter.filtered_market_regime_label, "bull");
        assert_eq!(
            filter.evidence_assignments.get("market_regime"),
            Some(&"bull".to_string())
        );
        assert!(filter.evidence_quality_score >= 0.75);
        assert_eq!(filter.gating_status, "pass_hard");
        assert!(filter
            .rationale
            .iter()
            .any(|item| item.contains("regime_bundle_bbn_evidence_promoted_gate_to_pass_hard")));
    }

    #[test]
    fn strategy_library_import_does_not_promote_practical_gate_from_metadata_flags() {
        let manifest: StrategyLibraryManifest = serde_json::from_value(serde_json::json!({
            "manifest_version": "1.0",
            "strategies": [{
                "name": "ImportedButNotRuntimeGranted",
                "status": "ok",
                "metadata": {
                    "main_regime": "TrendExpansion",
                    "sub_regime": "MomentumPersistence",
                    "sub_sub_regime_or_profit_factor": "macd_zero_line_reclaim",
                    "profit_factor": "macd_zero_line_reclaim_long_v1",
                    "regime_profit_branch_path": "TrendExpansion -> MomentumPersistence -> macd_zero_line_reclaim -> macd_zero_line_reclaim_long_v1",
                    "promotion_allowed": true,
                    "trade_usable": true
                },
                "validation_metrics": {
                    "sharpe": 0.6358,
                    "total_profit_pct": 3.15,
                    "trade_count": 17,
                    "win_rate_pct": 58.8235,
                    "profit_factor": 1.20
                }
            }]
        }))
        .unwrap();

        let adapter =
            RegimeConsumerBundleAdapter::from_strategy_library_manifest(&manifest).unwrap();
        let decision = adapter.latest_decision.as_ref().expect("latest_decision");
        assert_eq!(
            decision.decision_state,
            "auto_quant_strategy_library_branch_context"
        );
        assert!(!decision.trade_usable);
        assert_eq!(
            adapter
                .consumer_hints
                .as_ref()
                .map(|hints| hints.trade_usable),
            Some(false)
        );

        let mut filter = PreBayesEvidenceFilter {
            policy: PreBayesEvidencePolicy {
                hard_pass_quality_threshold: 0.75,
                neutralized_quality_threshold: 0.40,
                ..PreBayesEvidencePolicy::default()
            },
            filtered_market_regime_label: "range".to_string(),
            filtered_liquidity_context_label: "neutral".to_string(),
            filtered_factor_alignment: "mixed".to_string(),
            filtered_factor_uncertainty: "low".to_string(),
            filtered_multi_timeframe_direction_bias: "bullish".to_string(),
            filtered_multi_timeframe_resonance_label: "aligned".to_string(),
            evidence_quality_score: 0.624,
            gating_status: "pass_neutralized".to_string(),
            pass_to_bbn: true,
            uses_soft_evidence: true,
            evidence_assignments: BTreeMap::from([
                ("market_regime".to_string(), "range".to_string()),
                ("liquidity_context".to_string(), "neutral".to_string()),
                ("factor_alignment".to_string(), "mixed".to_string()),
                ("factor_uncertainty".to_string(), "low".to_string()),
            ]),
            ..PreBayesEvidenceFilter::default()
        };

        let status = adapter.apply_bbn_soft_evidence_to_pre_bayes_filter(&mut filter, true);

        assert_eq!(status, RegimeBbnEvidenceApplicationStatus::Skipped);
        assert_eq!(filter.gating_status, "pass_neutralized");
        assert_eq!(filter.evidence_quality_score, 0.624);
        assert!(!filter.rationale.iter().any(|item| item.contains(
            "regime_bundle_bbn_evidence_promoted_gate_to_pass_hard"
        )));
    }
}
