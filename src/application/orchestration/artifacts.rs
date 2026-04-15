use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PolicyDecisionArtifact {
    pub policy_version: String,
    pub action: String,
    pub qualification: String,
    pub recommended_command: String,
    pub confidence_band: String,
    pub leaf_id: String,
    pub split_trace: Vec<String>,
    pub invalidation_triggers: Vec<String>,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AnalysisArtifact {
    pub stage: String,
    pub factor_alignment: String,
    pub factor_uncertainty: String,
    pub decision_hint: String,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct QualificationArtifact {
    pub stage: String,
    pub gating_status: String,
    pub selected_entry_quality: String,
    pub evidence_quality_score: f64,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PosteriorAuditArtifact {
    pub posterior_version: String,
    pub fingerprint: String,
    pub comparable: bool,
    pub comparison_class: String,
    pub normalization_status: String,
    pub active_regime: String,
    pub confidence: Option<f64>,
    pub probabilities: BTreeMap<String, f64>,
    pub evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EnsembleVoteArtifact {
    pub ensemble_version: String,
    pub posterior: PosteriorAuditArtifact,
    pub final_action: String,
    pub recommended_command: String,
    pub human_next_triage: String,
    pub confidence: f64,
    pub consensus_strength: f64,
    pub disagreement_flags: Vec<String>,
    pub executor_summaries: Vec<String>,
    pub split_explanations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExecutionPlanArtifact {
    pub stage: String,
    pub plan_status: String,
    pub selected_direction: String,
    pub summary: String,
}
