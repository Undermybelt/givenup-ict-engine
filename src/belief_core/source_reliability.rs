use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralExperiencePriorSurfaceArtifact {
    pub symbol: String,
    #[serde(default)]
    pub source_reliability_em: StructuralSourceReliabilityEmReadiness,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub target_policy_contexts: Vec<StructuralTargetPolicyContextSurface>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub branch: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scenario: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path: Option<StructuralExperiencePriorEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructuralTargetPolicyContextSurface {
    pub context_key: String,
    pub observations: usize,
    pub weighted_observation_mass: f64,
    pub behavior_policy_probability: f64,
    pub behavior_policy_probability_variance: f64,
    pub learned_target_policy_probability: f64,
    pub learned_target_policy_probability_lower_bound: f64,
    pub learned_target_policy_probability_confidence: f64,
    pub calibrated_target_policy_probability: f64,
    pub calibrated_target_policy_probability_lower_bound: f64,
    pub target_policy_probability_brier_score: f64,
    pub target_policy_probability_calibration_error: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recommendation_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralSourceReliabilityEmReadiness {
    pub ready: bool,
    pub status: String,
    pub candidate_item_count: usize,
    pub labeled_item_count: usize,
    pub multi_source_item_count: usize,
    pub distinct_source_count: usize,
    pub observed_label_count: usize,
    pub max_sources_per_item: usize,
    pub min_multi_source_items: usize,
    #[serde(default)]
    pub consensus_item_count: usize,
    #[serde(default)]
    pub conflict_item_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub avg_consensus_confidence: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_consensus_confidence: Option<f64>,
    #[serde(default)]
    pub em_iteration_count: usize,
    #[serde(default)]
    pub em_latent_item_count: usize,
    #[serde(default)]
    pub em_distinct_label_count: usize,
    #[serde(default)]
    pub em_confusion_cell_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub avg_em_latent_confidence: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_em_latent_confidence: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub avg_em_source_reliability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_em_source_reliability: Option<f64>,
    #[serde(default)]
    pub persisted_source_summary_count: usize,
    #[serde(default)]
    pub persisted_confusion_cell_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub avg_persisted_source_reliability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub min_persisted_source_reliability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub em_calibration_status: Option<String>,
    #[serde(default)]
    pub em_calibration_observation_count: usize,
    #[serde(default)]
    pub em_calibration_source_count: usize,
    #[serde(default)]
    pub em_calibration_min_observations: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub em_calibration_brier_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub em_calibration_log_loss: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralExperiencePriorEntry {
    pub entity_kind: String,
    pub entity_id: String,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default)]
    pub historical_followed_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_win_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_avg_pnl: Option<f64>,
    pub experience_prior: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub current_posterior: Option<f64>,
    pub composite_score: f64,
    #[serde(default)]
    pub source_panel_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_offline_seed_source: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dominant_source_panel: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dominant_source_share: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dominant_source_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ips_weight: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub counterfactual_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub off_policy_adjusted_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub behavior_policy_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub behavior_policy_probability_variance: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_confidence: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_brier_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_calibration_error: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snips_weight_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snips_weight_squared_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snips_effective_sample_size: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snips_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub doubly_robust_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_calibration_weight: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_variance_penalty: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_reward_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub matured_feedback_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub unresolved_feedback_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub maturity_coverage: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub censoring_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_censoring_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub censoring_adjusted_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub censoring_adjusted_reward_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_success_competing_risk: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_failure_competing_risk: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_invalidation_competing_risk: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_abandonment_competing_risk: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_competing_risk_entropy: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_elapsed_feedback_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_elapsed_hours_at_risk: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_avg_elapsed_hours: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_hazard_per_hour: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_expected_resolution_hours: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_survival_probability_1h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_survival_probability_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_survival_probability_24h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_success_hazard_per_hour: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_failure_hazard_per_hour: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_invalidation_hazard_per_hour: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_abandonment_hazard_per_hour: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_success_cumulative_incidence_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_failure_cumulative_incidence_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_invalidation_cumulative_incidence_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_abandonment_cumulative_incidence_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_horizon_1h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_within_1h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_probability_1h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_horizon_4h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_within_4h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_probability_4h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_horizon_24h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_within_24h_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub delayed_reward_resolution_probability_24h: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_streak_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_avg_streak_length: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_persistence_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_weighted_streak_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_weighted_observation_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_temporal_posterior_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_temporal_posterior_support: Option<f64>,
}
