use serde::{Deserialize, Serialize};

use crate::belief_core::ranking_label::StructuralPathRankerRuntimeSurface;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathPlanArtifact {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_data_contracts: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_provider_tracks: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime: Option<StructuralPathRankerRuntimeSurface>,
    pub paths: Vec<StructuralPathArtifact>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralTopPathCandidatesArtifact {
    pub symbol: String,
    pub candidate_set_id: String,
    pub candidate_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime: Option<StructuralPathRankerRuntimeSurface>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub candidates: Vec<StructuralTopPathCandidate>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralRecommendedPathBundleArtifact {
    pub symbol: String,
    pub rank: usize,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime: Option<StructuralPathRankerRuntimeSurface>,
    pub selected_path_probability: f64,
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub experience_prior: f64,
    pub current_posterior: f64,
    pub composite_score: f64,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_raw_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_calibrated_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_path_prob_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_execution_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime_source: Option<String>,
    pub why_this_path: String,
    pub trigger_summary: String,
    pub confirmation_summary: String,
    pub stop_summary: String,
    pub invalidation_summary: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralTopPathCandidate {
    pub rank: usize,
    pub candidate_set_id: String,
    pub behavior_policy_probability: f64,
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub experience_prior: f64,
    pub current_posterior: f64,
    pub composite_score: f64,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default)]
    pub historical_followed_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_raw_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_calibrated_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_path_prob_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_execution_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime_source: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathArtifact {
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub entry_style: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pre_bayes_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub multi_timeframe_direction_bias: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_candidate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_candidate_artifact_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_readiness: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prediction_edge_share: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_edge_share: Option<f64>,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default)]
    pub historical_followed_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_win_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_avg_pnl: Option<f64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub trigger_conditions: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub confirmation_conditions: Vec<String>,
    pub stop_definition: String,
    pub target_definition: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub invalidation_conditions: Vec<String>,
    pub expected_failure_mode: String,
    pub max_time_in_trade: String,
    pub path_prior: f64,
    pub path_posterior: f64,
    pub bbn_support_score: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub catboost_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_calibrated_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_path_prob_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_execution_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_ranker_runtime_source: Option<String>,
    pub composite_preference_score: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
}
