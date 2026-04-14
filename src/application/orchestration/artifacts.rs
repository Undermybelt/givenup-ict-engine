use serde::{Deserialize, Serialize};

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
pub struct ExecutionPlanArtifact {
    pub stage: String,
    pub plan_status: String,
    pub selected_direction: String,
    pub summary: String,
}
