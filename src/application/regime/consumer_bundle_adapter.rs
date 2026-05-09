use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::Path;

const EXPECTED_SCHEMA_VERSION: &str = "regime-consumer-bundle/v1";

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
            let message = "invalid regime consumer bundle: missing latest_decision or consumer_hints"
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

    pub fn trace_entries(&self, path: Option<&Path>) -> Vec<String> {
        let mut entries = vec![format!("regime_bundle_status={}", self.status.as_trace_value())];
        if let Some(path) = path {
            entries.push(format!("regime_bundle_path={}", path.display()));
        }
        if let Some(error) = self.error.as_ref() {
            entries.push(format!("regime_bundle_error={}", compact_trace_value(error)));
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
        entries
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

fn compact_trace_value(value: &str) -> String {
    value.split_whitespace().collect::<Vec<_>>().join("_")
}
