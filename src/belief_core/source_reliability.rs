use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::state::{
    structural_source_observed_outcome_likelihood, structural_source_reliability_em_diagnostics,
    structural_source_reliability_em_fit_from_state, StructuralPriorLearningState,
    StructuralPriorStats, StructuralSourceReliabilityPosterior,
    STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_MULTI_SOURCE_ITEMS,
};

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

pub fn structural_resolved_smoothed_prior(
    prior_stats: Option<&StructuralPriorStats>,
    structural_prior_state: &StructuralPriorLearningState,
    fallback: f64,
) -> f64 {
    prior_stats
        .map(|stats| {
            structural_panel_derived_smoothed_prior(stats, structural_prior_state)
                .unwrap_or(stats.smoothed_prior)
        })
        .unwrap_or(fallback)
}

pub fn structural_panel_derived_smoothed_prior(
    stats: &StructuralPriorStats,
    structural_prior_state: &StructuralPriorLearningState,
) -> Option<f64> {
    let em_fit = structural_source_reliability_em_fit_from_state(structural_prior_state);
    let em_source_reliability = if em_fit.iteration_count == 0 {
        None
    } else {
        Some(&em_fit.source_reliability)
    };
    let success_mass: f64 = stats
        .source_panel_summaries
        .iter()
        .map(|(source_label, summary)| {
            summary.weighted_success_mass.max(0.0)
                * structural_source_reliability_multiplier(
                    structural_prior_state,
                    source_label,
                    em_source_reliability,
                )
        })
        .sum();
    let failure_mass: f64 = stats
        .source_panel_summaries
        .iter()
        .map(|(source_label, summary)| {
            summary.weighted_failure_mass.max(0.0)
                * structural_source_reliability_multiplier(
                    structural_prior_state,
                    source_label,
                    em_source_reliability,
                )
        })
        .sum();
    if success_mass <= f64::EPSILON && failure_mass <= f64::EPSILON {
        return None;
    }
    let alpha = 1.0 + success_mass;
    let beta = 1.0 + failure_mass;
    Some((alpha / (alpha + beta)).clamp(0.0, 1.0))
}

pub fn structural_source_reliability_multiplier(
    structural_prior_state: &StructuralPriorLearningState,
    source_label: &str,
    em_source_reliability: Option<&BTreeMap<String, f64>>,
) -> f64 {
    let posterior = structural_prior_state
        .source_reliability_posteriors
        .get(source_label);
    let posterior_multiplier = posterior
        .map(|posterior| {
            if posterior.observations == 0 && posterior.weighted_observation_mass <= f64::EPSILON {
                1.0
            } else {
                posterior.posterior_reliability.clamp(0.0, 1.0)
                    * structural_source_confusion_concentration_multiplier(posterior)
                        .unwrap_or(1.0)
            }
        })
        .unwrap_or(1.0);
    let Some(em_multiplier) = em_source_reliability
        .and_then(|source_reliability| source_reliability.get(source_label))
        .copied()
        .map(|value| value.clamp(0.0, 1.0))
    else {
        return posterior_multiplier;
    };

    if posterior.is_some() {
        (posterior_multiplier * 0.5 + em_multiplier * 0.5).clamp(0.0, 1.0)
    } else {
        em_multiplier
    }
}

pub fn structural_source_confusion_concentration_multiplier(
    posterior: &StructuralSourceReliabilityPosterior,
) -> Option<f64> {
    let mut weighted_likelihood_mass = 0.0;
    let mut weighted_observation_mass = 0.0;
    for cell in posterior.outcome_confusion.values() {
        let cell_mass = cell.weighted_observation_mass.max(0.0);
        if cell_mass <= f64::EPSILON {
            continue;
        }
        weighted_likelihood_mass += cell_mass
            * structural_source_observed_outcome_likelihood(
                posterior,
                &cell.credit_class,
                &cell.observed_outcome,
            );
        weighted_observation_mass += cell_mass;
    }

    if weighted_observation_mass <= f64::EPSILON {
        None
    } else {
        Some((weighted_likelihood_mass / weighted_observation_mass).clamp(0.0, 1.0))
    }
}

pub fn structural_source_reliability_em_readiness(
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralSourceReliabilityEmReadiness {
    let diagnostics = structural_source_reliability_em_diagnostics(structural_prior_state);
    let ready = diagnostics.distinct_source_count >= 2
        && diagnostics.multi_source_item_count
            >= STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_MULTI_SOURCE_ITEMS;
    let status = if ready {
        "ready"
    } else if diagnostics.distinct_source_count < 2 {
        "needs_multiple_sources"
    } else {
        "needs_multi_source_overlap"
    };
    StructuralSourceReliabilityEmReadiness {
        ready,
        status: status.to_string(),
        candidate_item_count: diagnostics.candidate_item_count,
        labeled_item_count: diagnostics.labeled_item_count,
        multi_source_item_count: diagnostics.multi_source_item_count,
        distinct_source_count: diagnostics.distinct_source_count,
        observed_label_count: diagnostics.observed_label_count,
        max_sources_per_item: diagnostics.max_sources_per_item,
        min_multi_source_items: STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_MULTI_SOURCE_ITEMS,
        consensus_item_count: diagnostics.consensus_item_count,
        conflict_item_count: diagnostics.conflict_item_count,
        avg_consensus_confidence: diagnostics.avg_consensus_confidence,
        min_consensus_confidence: diagnostics.min_consensus_confidence,
        em_iteration_count: diagnostics.fit.iteration_count,
        em_latent_item_count: diagnostics.fit.latent_item_count,
        em_distinct_label_count: diagnostics.fit.distinct_label_count,
        em_confusion_cell_count: diagnostics.fit.confusion_cell_count,
        avg_em_latent_confidence: diagnostics.fit.avg_latent_confidence,
        min_em_latent_confidence: diagnostics.fit.min_latent_confidence,
        avg_em_source_reliability: diagnostics.fit.avg_source_reliability,
        min_em_source_reliability: diagnostics.fit.min_source_reliability,
        persisted_source_summary_count: diagnostics.persisted_source_summary_count,
        persisted_confusion_cell_count: diagnostics.persisted_confusion_cell_count,
        avg_persisted_source_reliability: diagnostics.avg_persisted_source_reliability,
        min_persisted_source_reliability: diagnostics.min_persisted_source_reliability,
        em_calibration_status: diagnostics
            .calibration
            .as_ref()
            .map(|calibration| calibration.status.clone()),
        em_calibration_observation_count: diagnostics
            .calibration
            .as_ref()
            .map(|calibration| calibration.observation_count)
            .unwrap_or_default(),
        em_calibration_source_count: diagnostics
            .calibration
            .as_ref()
            .map(|calibration| calibration.source_count)
            .unwrap_or_default(),
        em_calibration_min_observations: diagnostics
            .calibration
            .as_ref()
            .map(|calibration| calibration.min_observations)
            .unwrap_or_default(),
        em_calibration_brier_score: diagnostics
            .calibration
            .as_ref()
            .and_then(|calibration| calibration.brier_score),
        em_calibration_log_loss: diagnostics
            .calibration
            .as_ref()
            .and_then(|calibration| calibration.log_loss),
    }
}
