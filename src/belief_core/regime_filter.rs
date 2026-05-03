use std::collections::BTreeMap;

use crate::belief_core::beta_dirichlet_update::{beta_posterior_mean, dirichlet_component_mean};
use crate::state::{
    StructuralBranchTemporalPosteriorState, StructuralBranchTransitionPrior,
    StructuralNodeDurationPrior, StructuralNodeTemporalPosteriorState,
    StructuralNodeTransitionPosteriorState,
};
use serde::{Deserialize, Serialize};

const NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT: f64 = 0.5;
const NODE_TRANSITION_RECURSIVE_MAX_DEPTH: usize = 4;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralTemporalSummaryArtifact {
    pub symbol: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub from_branch_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub to_branch_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_streak_count: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_avg_streak_length: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_persistence_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_expected_dwell_steps: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_remaining_dwell_steps: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_break_hazard: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_sticky_self_transition_strength: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_weighted_streak_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_temporal_posterior_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_distribution_entropy: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub empirical_duration_survival: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub empirical_duration_completion_hazard: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_duration_surprise: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_evidence_weight: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_raw_break_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_break_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_continue_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_run_length_mode: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_run_length_mode_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_run_length_tail_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_run_length_observation_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_recursive_reset_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_recursive_run_length_mode: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_recursive_run_length_mode_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_recursive_run_length_expected_value: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_recursive_run_length_entropy: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_change_intensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_break_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_recursive_reset_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_recursive_run_length_mode: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_recursive_run_length_mode_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_recursive_run_length_expected_value: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bocpd_sequence_recursive_run_length_entropy: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_posterior_blend_weight: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_weighted_observation_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_temporal_posterior_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_posterior_multiplier: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_normalized_posterior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node_transition_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node_transition_temporal_posterior_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node_transition_posterior_multiplier: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node_transition_normalized_posterior: Option<f64>,
    pub summary_line: String,
}

pub fn blend_node_posterior_with_duration_prior(
    base_posterior: f64,
    duration_prior: Option<&StructuralNodeDurationPrior>,
    temporal_state: Option<&StructuralNodeTemporalPosteriorState>,
) -> f64 {
    let temporal_support = temporal_state
        .map(|state| state.temporal_posterior_support)
        .or_else(|| duration_prior.map(|prior| prior.temporal_posterior_support));
    let blend_weight = temporal_state
        .map(|state| state.posterior_blend_weight)
        .or_else(|| {
            duration_prior.map(|prior| {
                let observation_weight = (prior.weighted_streak_mass / 3.0).min(1.0);
                let streak_weight = (prior.streak_count as f64 / 3.0).min(1.0);
                (observation_weight * streak_weight * 0.5).clamp(0.0, 0.5)
            })
        });
    let (Some(blend_weight), Some(temporal_support)) = (blend_weight, temporal_support) else {
        return base_posterior;
    };
    ((1.0 - blend_weight) * base_posterior + blend_weight * temporal_support).clamp(0.0, 1.0)
}

pub fn blend_branch_prior_with_transition_prior(
    base_prior: f64,
    transition_prior: Option<&StructuralBranchTransitionPrior>,
    temporal_state: Option<&StructuralBranchTemporalPosteriorState>,
) -> f64 {
    if let Some(state) = temporal_state {
        return ((1.0 - (state.weighted_observation_mass / 3.0).min(1.0)) * base_prior
            + (state.weighted_observation_mass / 3.0).min(1.0) * state.temporal_posterior_support)
            .clamp(0.0, 1.0);
    }
    let Some(transition_prior) = transition_prior else {
        return base_prior;
    };
    let transition_weight = (transition_prior.weighted_observation_mass / 3.0).min(1.0);
    ((1.0 - transition_weight) * base_prior
        + transition_weight * transition_prior.temporal_posterior_support)
        .clamp(0.0, 1.0)
}

pub fn transition_adjusted_branch_posteriors(
    node_id: &str,
    regime_probabilities: &[(String, f64)],
    latest_branch_id: Option<&str>,
    transition_priors: &BTreeMap<String, StructuralBranchTransitionPrior>,
    branch_temporal_posteriors: &BTreeMap<String, StructuralBranchTemporalPosteriorState>,
    branch_label_for_regime: impl Fn(&str) -> &'static str,
) -> BTreeMap<String, f64> {
    let Some(latest_branch_id) = latest_branch_id else {
        return regime_probabilities
            .iter()
            .map(|(regime, probability)| {
                (
                    format!("{node_id}:{}", branch_label_for_regime(regime)),
                    *probability,
                )
            })
            .collect();
    };

    let recursive_branch_posteriors = structural_recursive_branch_transition_posteriors(
        latest_branch_id,
        branch_temporal_posteriors,
    );
    let mut normalized_posterior = Vec::new();
    let mut missing_posterior_candidates = Vec::new();
    for (regime, probability) in regime_probabilities {
        let branch_id = format!("{node_id}:{}", branch_label_for_regime(regime));
        let transition_key = format!("{latest_branch_id}=>{branch_id}");
        match branch_temporal_posteriors.get(&transition_key) {
            Some(state) if state.normalized_transition_posterior > f64::EPSILON => {
                normalized_posterior.push((
                    branch_id,
                    state.normalized_transition_posterior.clamp(0.0, 1.0),
                ));
            }
            _ if recursive_branch_posteriors
                .get(&branch_id)
                .copied()
                .unwrap_or_default()
                > f64::EPSILON =>
            {
                let recursive_weight = recursive_branch_posteriors
                    .get(&branch_id)
                    .copied()
                    .unwrap_or_default()
                    .clamp(0.0, 1.0);
                normalized_posterior.push((branch_id, recursive_weight));
            }
            _ => {
                missing_posterior_candidates.push((branch_id, (*probability).max(0.0)));
            }
        }
    }
    if !normalized_posterior.is_empty() {
        let known_total: f64 = normalized_posterior
            .iter()
            .map(|(_, posterior)| *posterior)
            .sum();
        let residual = (1.0 - known_total).max(0.0);
        let missing_total: f64 = missing_posterior_candidates
            .iter()
            .map(|(_, probability)| *probability)
            .sum();
        let missing_count = missing_posterior_candidates.len().max(1) as f64;
        for (branch_id, probability) in missing_posterior_candidates {
            let residual_weight = if missing_total > f64::EPSILON {
                residual * probability / missing_total
            } else {
                residual / missing_count
            };
            normalized_posterior.push((branch_id, residual_weight.clamp(0.0, 1.0)));
        }
        let total: f64 = normalized_posterior.iter().map(|(_, weight)| *weight).sum();
        if total > f64::EPSILON {
            return normalized_posterior
                .into_iter()
                .map(|(branch_id, weight)| (branch_id, (weight / total).clamp(0.0, 1.0)))
                .collect();
        }
    }

    let mut weighted = Vec::new();
    for (regime, probability) in regime_probabilities {
        let branch_id = format!("{node_id}:{}", branch_label_for_regime(regime));
        let transition_key = format!("{latest_branch_id}=>{branch_id}");
        let transition_prior = transition_priors.get(&transition_key);
        let temporal_state = branch_temporal_posteriors.get(&transition_key);
        let transition_weight = temporal_state
            .map(|state| state.posterior_multiplier)
            .or_else(|| {
                transition_prior.map(|prior| {
                    let sample_weight = (prior.weighted_observation_mass / 3.0).min(1.0);
                    let temporal_bias = (prior.temporal_posterior_support - 0.5) * 2.0;
                    (1.0 + temporal_bias * sample_weight).clamp(0.05, 2.0)
                })
            })
            .unwrap_or(1.0);
        weighted.push((
            branch_id,
            (*probability * transition_weight).clamp(0.0, 1.0),
        ));
    }

    let total: f64 = weighted.iter().map(|(_, weight)| *weight).sum();
    if total <= f64::EPSILON {
        return regime_probabilities
            .iter()
            .map(|(regime, probability)| {
                (
                    format!("{node_id}:{}", branch_label_for_regime(regime)),
                    *probability,
                )
            })
            .collect();
    }

    weighted
        .into_iter()
        .map(|(branch_id, weight)| (branch_id, (weight / total).clamp(0.0, 1.0)))
        .collect()
}

pub fn transition_adjusted_node_posteriors(
    symbol: &str,
    regime_probabilities: &[(String, f64)],
    latest_branch_id: Option<&str>,
    transition_priors: &BTreeMap<String, StructuralBranchTransitionPrior>,
    branch_temporal_posteriors: &BTreeMap<String, StructuralBranchTemporalPosteriorState>,
    node_transition_posteriors: &BTreeMap<String, StructuralNodeTransitionPosteriorState>,
) -> BTreeMap<String, f64> {
    let Some(latest_branch_id) = latest_branch_id else {
        return regime_probabilities
            .iter()
            .map(|(regime, probability)| (regime.clone(), *probability))
            .collect();
    };

    let latest_node_id = transition_priors
        .values()
        .find(|prior| prior.from_branch_id == latest_branch_id)
        .map(|prior| prior.from_node_id.as_str())
        .or_else(|| {
            latest_branch_id
                .rsplit_once(':')
                .map(|(node_id, _)| node_id)
        });
    if let Some(latest_node_id) = latest_node_id {
        let recursive_posteriors = structural_recursive_node_transition_posteriors(
            latest_node_id,
            node_transition_posteriors,
        );
        let mut normalized_posterior = Vec::new();
        let mut missing_posterior_candidates = Vec::new();
        for (regime, probability) in regime_probabilities {
            let node_id = format!("{symbol}:belief_regime_node:{regime}");
            let transition_key = format!("{latest_node_id}=>{node_id}");
            match node_transition_posteriors.get(&transition_key) {
                Some(state) if state.normalized_transition_posterior > f64::EPSILON => {
                    normalized_posterior.push((
                        regime.clone(),
                        state.normalized_transition_posterior.clamp(0.0, 1.0),
                    ));
                }
                _ if recursive_posteriors
                    .get(&node_id)
                    .copied()
                    .unwrap_or_default()
                    > f64::EPSILON =>
                {
                    normalized_posterior.push((
                        regime.clone(),
                        recursive_posteriors
                            .get(&node_id)
                            .copied()
                            .unwrap_or_default()
                            .clamp(0.0, 1.0),
                    ));
                }
                _ => {
                    missing_posterior_candidates.push((regime.clone(), (*probability).max(0.0)));
                }
            }
        }
        if !normalized_posterior.is_empty() {
            let known_total: f64 = normalized_posterior
                .iter()
                .map(|(_, posterior)| *posterior)
                .sum();
            let residual = (1.0 - known_total).max(0.0);
            let missing_total: f64 = missing_posterior_candidates
                .iter()
                .map(|(_, probability)| *probability)
                .sum();
            let missing_count = missing_posterior_candidates.len().max(1) as f64;
            for (regime, probability) in missing_posterior_candidates {
                let residual_weight = if missing_total > f64::EPSILON {
                    residual * probability / missing_total
                } else {
                    residual / missing_count
                };
                normalized_posterior.push((regime, residual_weight.clamp(0.0, 1.0)));
            }
            let total: f64 = normalized_posterior.iter().map(|(_, weight)| *weight).sum();
            if total > f64::EPSILON {
                return normalized_posterior
                    .into_iter()
                    .map(|(regime, weight)| (regime, (weight / total).clamp(0.0, 1.0)))
                    .collect();
            }
        }
    }

    let mut normalized_posterior = Vec::new();
    let mut missing_posterior_candidates = Vec::new();
    for (regime, probability) in regime_probabilities {
        let node_id = format!("{symbol}:belief_regime_node:{regime}");
        let node_posterior = branch_temporal_posteriors
            .iter()
            .filter_map(|(transition_key, state)| {
                let transition_prior = transition_priors.get(transition_key)?;
                if transition_prior.from_branch_id == latest_branch_id
                    && transition_prior.to_node_id == node_id
                    && state.normalized_transition_posterior > f64::EPSILON
                {
                    Some(state.normalized_transition_posterior.clamp(0.0, 1.0))
                } else {
                    None
                }
            })
            .sum::<f64>();
        if node_posterior > f64::EPSILON {
            normalized_posterior.push((regime.clone(), node_posterior.clamp(0.0, 1.0)));
        } else {
            missing_posterior_candidates.push((regime.clone(), (*probability).max(0.0)));
        }
    }
    if normalized_posterior.is_empty() {
        return regime_probabilities
            .iter()
            .map(|(regime, probability)| (regime.clone(), *probability))
            .collect();
    }

    let known_total: f64 = normalized_posterior
        .iter()
        .map(|(_, posterior)| *posterior)
        .sum();
    let residual = (1.0 - known_total).max(0.0);
    let missing_total: f64 = missing_posterior_candidates
        .iter()
        .map(|(_, probability)| *probability)
        .sum();
    let missing_count = missing_posterior_candidates.len().max(1) as f64;
    for (regime, probability) in missing_posterior_candidates {
        let residual_weight = if missing_total > f64::EPSILON {
            residual * probability / missing_total
        } else {
            residual / missing_count
        };
        normalized_posterior.push((regime, residual_weight.clamp(0.0, 1.0)));
    }

    let total: f64 = normalized_posterior.iter().map(|(_, weight)| *weight).sum();
    if total <= f64::EPSILON {
        return regime_probabilities
            .iter()
            .map(|(regime, probability)| (regime.clone(), *probability))
            .collect();
    }
    normalized_posterior
        .into_iter()
        .map(|(regime, weight)| (regime, (weight / total).clamp(0.0, 1.0)))
        .collect()
}

pub fn build_structural_temporal_summary_artifact(
    symbol: String,
    node_id: String,
    from_branch_id: Option<String>,
    to_branch_id: Option<String>,
    node_duration_prior: Option<&StructuralNodeDurationPrior>,
    node_temporal_state: Option<&StructuralNodeTemporalPosteriorState>,
    branch_temporal_state: Option<&StructuralBranchTemporalPosteriorState>,
    node_transition_state: Option<&StructuralNodeTransitionPosteriorState>,
    transition_prior: Option<&StructuralBranchTransitionPrior>,
) -> StructuralTemporalSummaryArtifact {
    let duration_summary = node_temporal_state
        .map(|state| state.summary_line.clone())
        .unwrap_or_else(|| {
            format!(
                "duration_mass={:.3} expected_dwell={:.3} break_hazard={:.3} sequence_break={:.3} sequence_reset={:.3} sticky_self_transition={:.3} duration_support={:.3} duration_temporal={:.3} blend=0.000",
                structural_duration_weighted_streak_mass(node_duration_prior).unwrap_or_default(),
                structural_duration_expected_dwell_steps(node_duration_prior).unwrap_or_default(),
                structural_duration_break_hazard(node_duration_prior).unwrap_or_default(),
                structural_duration_bocpd_sequence_break_probability(node_duration_prior)
                    .unwrap_or_default(),
                structural_duration_bocpd_sequence_recursive_reset_probability(node_duration_prior)
                    .unwrap_or_default(),
                structural_duration_sticky_self_transition_strength(node_duration_prior)
                    .unwrap_or_default(),
                structural_duration_outcome_support(node_duration_prior).unwrap_or_default(),
                structural_duration_temporal_posterior_support(node_duration_prior)
                    .unwrap_or_default()
            )
        });
    let transition_summary = branch_temporal_state
        .map(|state| state.summary_line.clone())
        .unwrap_or_else(|| {
            format!(
                "transition_mass={:.3} transition_support={:.3} transition_temporal={:.3} multiplier=1.000",
                transition_prior
                    .map(|prior| prior.weighted_observation_mass)
                    .unwrap_or_default(),
                transition_prior
                    .map(|prior| prior.transition_outcome_support)
                    .unwrap_or_default(),
                transition_prior
                    .map(|prior| prior.temporal_posterior_support)
                    .unwrap_or_default()
            )
        });
    let summary_line = format!(
        "{} duration_prior={:.3} | {} transition_prior={:.3}",
        duration_summary,
        structural_duration_persistence_prior(node_duration_prior).unwrap_or_default(),
        transition_summary,
        transition_prior
            .map(|prior| prior.transition_prior)
            .unwrap_or_default()
    );

    StructuralTemporalSummaryArtifact {
        symbol,
        node_id: Some(node_id),
        from_branch_id,
        to_branch_id,
        duration_streak_count: node_temporal_state
            .map(|state| state.streak_count)
            .or_else(|| structural_duration_streak_count(node_duration_prior)),
        duration_avg_streak_length: structural_duration_avg_streak_length(node_duration_prior),
        duration_persistence_prior: structural_duration_persistence_prior(node_duration_prior),
        duration_expected_dwell_steps: node_temporal_state
            .map(|state| state.expected_dwell_steps)
            .or_else(|| structural_duration_expected_dwell_steps(node_duration_prior)),
        duration_remaining_dwell_steps: node_temporal_state
            .map(|state| state.remaining_dwell_steps)
            .or_else(|| structural_duration_remaining_dwell_steps(node_duration_prior)),
        duration_break_hazard: node_temporal_state
            .map(|state| state.break_hazard)
            .or_else(|| structural_duration_break_hazard(node_duration_prior)),
        duration_sticky_self_transition_strength: node_temporal_state
            .map(|state| state.sticky_self_transition_strength)
            .or_else(|| structural_duration_sticky_self_transition_strength(node_duration_prior)),
        duration_weighted_streak_mass: node_temporal_state
            .map(|state| state.weighted_streak_mass)
            .or_else(|| structural_duration_weighted_streak_mass(node_duration_prior)),
        duration_outcome_support: node_temporal_state
            .map(|state| state.duration_outcome_support)
            .or_else(|| structural_duration_outcome_support(node_duration_prior)),
        duration_temporal_posterior_support: node_temporal_state
            .map(|state| state.temporal_posterior_support)
            .or_else(|| structural_duration_temporal_posterior_support(node_duration_prior)),
        duration_distribution_entropy: structural_duration_distribution_entropy(
            node_duration_prior,
        ),
        empirical_duration_survival: structural_duration_empirical_survival(node_duration_prior),
        empirical_duration_completion_hazard: structural_duration_empirical_completion_hazard(
            node_duration_prior,
        ),
        bocpd_duration_surprise: structural_duration_bocpd_surprise(node_duration_prior),
        bocpd_evidence_weight: structural_duration_bocpd_evidence_weight(node_duration_prior),
        bocpd_raw_break_probability: structural_duration_bocpd_raw_break_probability(
            node_duration_prior,
        ),
        bocpd_break_probability: structural_duration_bocpd_break_probability(node_duration_prior),
        bocpd_continue_probability: structural_duration_bocpd_continue_probability(
            node_duration_prior,
        ),
        bocpd_run_length_mode: structural_duration_bocpd_run_length_mode(node_duration_prior),
        bocpd_run_length_mode_probability: structural_duration_bocpd_run_length_mode_probability(
            node_duration_prior,
        ),
        bocpd_run_length_tail_probability: structural_duration_bocpd_run_length_tail_probability(
            node_duration_prior,
        ),
        bocpd_run_length_observation_mass: structural_duration_bocpd_run_length_observation_mass(
            node_duration_prior,
        ),
        bocpd_recursive_reset_probability: node_temporal_state
            .and_then(|state| structural_positive_f64(state.bocpd_recursive_reset_probability))
            .or_else(|| structural_duration_bocpd_recursive_reset_probability(node_duration_prior)),
        bocpd_recursive_run_length_mode: node_temporal_state
            .and_then(|state| {
                structural_run_length_mode(
                    state.bocpd_recursive_run_length_mode,
                    state.bocpd_recursive_run_length_mode_probability,
                )
            })
            .or_else(|| structural_duration_bocpd_recursive_run_length_mode(node_duration_prior)),
        bocpd_recursive_run_length_mode_probability: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_recursive_run_length_mode_probability)
            })
            .or_else(|| {
                structural_duration_bocpd_recursive_run_length_mode_probability(node_duration_prior)
            }),
        bocpd_recursive_run_length_expected_value: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_recursive_run_length_expected_value)
            })
            .or_else(|| {
                structural_duration_bocpd_recursive_run_length_expected_value(node_duration_prior)
            }),
        bocpd_recursive_run_length_entropy: node_temporal_state
            .and_then(|state| structural_positive_f64(state.bocpd_recursive_run_length_entropy))
            .or_else(|| {
                structural_duration_bocpd_recursive_run_length_entropy(node_duration_prior)
            }),
        bocpd_sequence_change_intensity: node_temporal_state
            .and_then(|state| structural_positive_f64(state.bocpd_sequence_change_intensity))
            .or_else(|| structural_duration_bocpd_sequence_change_intensity(node_duration_prior)),
        bocpd_sequence_break_probability: node_temporal_state
            .and_then(|state| structural_positive_f64(state.bocpd_sequence_break_probability))
            .or_else(|| structural_duration_bocpd_sequence_break_probability(node_duration_prior)),
        bocpd_sequence_recursive_reset_probability: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_sequence_recursive_reset_probability)
            })
            .or_else(|| {
                structural_duration_bocpd_sequence_recursive_reset_probability(node_duration_prior)
            }),
        bocpd_sequence_recursive_run_length_mode: node_temporal_state
            .and_then(|state| {
                structural_run_length_mode(
                    state.bocpd_sequence_recursive_run_length_mode,
                    state.bocpd_sequence_recursive_run_length_mode_probability,
                )
            })
            .or_else(|| {
                structural_duration_bocpd_sequence_recursive_run_length_mode(node_duration_prior)
            }),
        bocpd_sequence_recursive_run_length_mode_probability: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_sequence_recursive_run_length_mode_probability)
            })
            .or_else(|| {
                structural_duration_bocpd_sequence_recursive_run_length_mode_probability(
                    node_duration_prior,
                )
            }),
        bocpd_sequence_recursive_run_length_expected_value: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_sequence_recursive_run_length_expected_value)
            })
            .or_else(|| {
                structural_duration_bocpd_sequence_recursive_run_length_expected_value(
                    node_duration_prior,
                )
            }),
        bocpd_sequence_recursive_run_length_entropy: node_temporal_state
            .and_then(|state| {
                structural_positive_f64(state.bocpd_sequence_recursive_run_length_entropy)
            })
            .or_else(|| {
                structural_duration_bocpd_sequence_recursive_run_length_entropy(node_duration_prior)
            }),
        duration_posterior_blend_weight: node_temporal_state
            .map(|state| state.posterior_blend_weight),
        transition_prior: transition_prior.map(|prior| prior.transition_prior),
        transition_weighted_observation_mass: branch_temporal_state
            .map(|state| state.weighted_observation_mass)
            .or_else(|| transition_prior.map(|prior| prior.weighted_observation_mass)),
        transition_outcome_support: branch_temporal_state
            .map(|state| state.transition_outcome_support)
            .or_else(|| transition_prior.map(|prior| prior.transition_outcome_support)),
        transition_temporal_posterior_support: branch_temporal_state
            .map(|state| state.temporal_posterior_support)
            .or_else(|| transition_prior.map(|prior| prior.temporal_posterior_support)),
        transition_posterior_multiplier: branch_temporal_state
            .map(|state| state.posterior_multiplier),
        transition_normalized_posterior: branch_temporal_state
            .map(|state| state.normalized_transition_posterior),
        node_transition_prior: node_transition_state.map(|state| state.transition_prior),
        node_transition_temporal_posterior_support: node_transition_state
            .map(|state| state.temporal_posterior_support),
        node_transition_posterior_multiplier: node_transition_state
            .map(|state| state.posterior_multiplier),
        node_transition_normalized_posterior: node_transition_state
            .map(|state| state.normalized_transition_posterior),
        summary_line,
    }
}

pub fn structural_duration_streak_count(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<usize> {
    duration_prior
        .map(|prior| prior.streak_count)
        .filter(|count| *count > 0)
}

pub fn structural_duration_avg_streak_length(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(prior.avg_streak_length))
}

pub fn structural_duration_persistence_prior(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(prior.persistence_prior))
}

pub fn structural_duration_expected_dwell_steps(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(prior.expected_dwell_steps))
}

pub fn structural_duration_remaining_dwell_steps(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(prior.remaining_dwell_steps))
}

pub fn structural_duration_break_hazard(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(prior.break_hazard))
}

pub fn structural_duration_sticky_self_transition_strength(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.sticky_self_transition_strength)
}

pub fn structural_duration_weighted_streak_mass(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.weighted_streak_mass)
}

pub fn structural_duration_outcome_support(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.duration_outcome_support)
}

pub fn structural_duration_temporal_posterior_support(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.temporal_posterior_support)
}

pub fn structural_duration_distribution_entropy(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.duration_distribution_entropy)
}

pub fn structural_duration_empirical_survival(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.empirical_duration_survival)
}

pub fn structural_duration_empirical_completion_hazard(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.empirical_duration_completion_hazard
    })
}

pub fn structural_duration_bocpd_surprise(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.bocpd_duration_surprise)
}

pub fn structural_duration_bocpd_evidence_weight(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.bocpd_evidence_weight)
}

pub fn structural_duration_bocpd_raw_break_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.bocpd_raw_break_probability)
}

pub fn structural_duration_bocpd_break_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.bocpd_break_probability)
}

pub fn structural_duration_bocpd_continue_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| prior.bocpd_continue_probability)
}

pub fn structural_duration_bocpd_run_length_mode(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<usize> {
    duration_prior
        .map(|prior| prior.bocpd_run_length_mode)
        .filter(|mode| *mode > 0)
}

pub fn structural_duration_bocpd_run_length_mode_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_run_length_mode_probability
    })
}

pub fn structural_duration_bocpd_run_length_tail_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_run_length_tail_probability
    })
}

pub fn structural_duration_bocpd_run_length_observation_mass(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_run_length_observation_mass
    })
}

pub fn structural_duration_bocpd_recursive_reset_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_recursive_reset_probability
    })
}

pub fn structural_duration_bocpd_recursive_run_length_mode(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<usize> {
    duration_prior.and_then(|prior| {
        structural_run_length_mode(
            prior.bocpd_recursive_run_length_mode,
            prior.bocpd_recursive_run_length_mode_probability,
        )
    })
}

pub fn structural_duration_bocpd_recursive_run_length_mode_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_recursive_run_length_mode_probability
    })
}

pub fn structural_duration_bocpd_recursive_run_length_expected_value(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_recursive_run_length_expected_value
    })
}

pub fn structural_duration_bocpd_recursive_run_length_entropy(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_recursive_run_length_entropy
    })
}

pub fn structural_duration_bocpd_sequence_change_intensity(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_change_intensity
    })
}

pub fn structural_duration_bocpd_sequence_break_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_break_probability
    })
}

pub fn structural_duration_bocpd_sequence_recursive_reset_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_recursive_reset_probability
    })
}

pub fn structural_duration_bocpd_sequence_recursive_run_length_mode(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<usize> {
    duration_prior.and_then(|prior| {
        structural_run_length_mode(
            prior.bocpd_sequence_recursive_run_length_mode,
            prior.bocpd_sequence_recursive_run_length_mode_probability,
        )
    })
}

pub fn structural_duration_bocpd_sequence_recursive_run_length_mode_probability(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_recursive_run_length_mode_probability
    })
}

pub fn structural_duration_bocpd_sequence_recursive_run_length_expected_value(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_recursive_run_length_expected_value
    })
}

pub fn structural_duration_bocpd_sequence_recursive_run_length_entropy(
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> Option<f64> {
    structural_duration_positive_value(duration_prior, |prior| {
        prior.bocpd_sequence_recursive_run_length_entropy
    })
}

pub(crate) fn structural_run_length_mode(mode: usize, probability: f64) -> Option<usize> {
    if probability.is_finite() && probability > f64::EPSILON {
        Some(mode)
    } else {
        None
    }
}

pub(crate) fn structural_positive_f64(value: f64) -> Option<f64> {
    if value.is_finite() && value > f64::EPSILON {
        Some(value)
    } else {
        None
    }
}

pub fn refresh_node_transition_posteriors(
    node_transition_posteriors: &mut BTreeMap<String, StructuralNodeTransitionPosteriorState>,
) {
    let mut outgoing_node_mass = BTreeMap::<String, f64>::new();
    for transition in node_transition_posteriors.values() {
        *outgoing_node_mass
            .entry(transition.from_node_id.clone())
            .or_insert(0.0) += transition.weighted_observation_mass;
    }
    for transition in node_transition_posteriors.values_mut() {
        let total = outgoing_node_mass
            .get(&transition.from_node_id)
            .copied()
            .unwrap_or_default();
        transition.transition_prior =
            dirichlet_component_mean(transition.weighted_observation_mass, total);
        transition.transition_outcome_support = beta_posterior_mean(
            transition.weighted_success_mass,
            transition.weighted_failure_mass,
        );
        transition.temporal_posterior_support = (transition.transition_prior * 0.7
            + transition.transition_outcome_support * 0.3)
            .clamp(0.0, 1.0);
    }

    let mut posterior_weights = BTreeMap::<String, f64>::new();
    let mut posterior_multipliers = BTreeMap::<String, f64>::new();
    let mut outgoing_posterior_weight = BTreeMap::<String, f64>::new();
    for (transition_key, transition) in node_transition_posteriors.iter() {
        let sample_weight = (transition.weighted_observation_mass / 3.0).min(1.0);
        let temporal_bias = (transition.temporal_posterior_support - 0.5) * 2.0;
        let posterior_multiplier = (1.0 + temporal_bias * sample_weight).clamp(0.05, 2.0);
        let posterior_weight = (transition.transition_prior * posterior_multiplier).max(0.0);
        posterior_weights.insert(transition_key.clone(), posterior_weight);
        posterior_multipliers.insert(transition_key.clone(), posterior_multiplier);
        *outgoing_posterior_weight
            .entry(transition.from_node_id.clone())
            .or_insert(0.0) += posterior_weight;
    }

    for (transition_key, transition) in node_transition_posteriors.iter_mut() {
        let posterior_multiplier = posterior_multipliers
            .get(transition_key)
            .copied()
            .unwrap_or(1.0);
        let posterior_weight = posterior_weights
            .get(transition_key)
            .copied()
            .unwrap_or_default();
        let posterior_total = outgoing_posterior_weight
            .get(&transition.from_node_id)
            .copied()
            .unwrap_or_default();
        let normalized_transition_posterior = if posterior_total <= f64::EPSILON {
            transition.transition_prior
        } else {
            (posterior_weight / posterior_total).clamp(0.0, 1.0)
        };
        transition.posterior_multiplier = posterior_multiplier;
        transition.normalized_transition_posterior = normalized_transition_posterior;
        transition.summary_line = format!(
            "node_transition_mass={:.3} node_transition_prior={:.3} node_transition_support={:.3} node_transition_temporal={:.3} multiplier={:.3} normalized_posterior={:.3}",
            transition.weighted_observation_mass,
            transition.transition_prior,
            transition.transition_outcome_support,
            transition.temporal_posterior_support,
            posterior_multiplier,
            normalized_transition_posterior
        );
    }
}

pub fn refresh_branch_transition_posteriors(
    branch_transition_priors: &mut BTreeMap<String, StructuralBranchTransitionPrior>,
    branch_temporal_posteriors: &mut BTreeMap<String, StructuralBranchTemporalPosteriorState>,
) {
    let mut outgoing_mass = BTreeMap::<String, f64>::new();
    for transition in branch_transition_priors.values() {
        *outgoing_mass
            .entry(transition.from_branch_id.clone())
            .or_insert(0.0) += transition.weighted_observation_mass;
    }
    for transition in branch_transition_priors.values_mut() {
        let total = outgoing_mass
            .get(&transition.from_branch_id)
            .copied()
            .unwrap_or_default();
        transition.transition_prior =
            dirichlet_component_mean(transition.weighted_observation_mass, total);
        transition.transition_outcome_support = beta_posterior_mean(
            transition.weighted_success_mass,
            transition.weighted_failure_mass,
        );
        transition.temporal_posterior_support = (transition.transition_prior * 0.7
            + transition.transition_outcome_support * 0.3)
            .clamp(0.0, 1.0);
    }

    let mut posterior_weights = BTreeMap::<String, f64>::new();
    let mut posterior_multipliers = BTreeMap::<String, f64>::new();
    let mut outgoing_posterior_weight = BTreeMap::<String, f64>::new();
    for (transition_key, transition) in branch_transition_priors.iter() {
        let sample_weight = (transition.weighted_observation_mass / 3.0).min(1.0);
        let temporal_bias = (transition.temporal_posterior_support - 0.5) * 2.0;
        let posterior_multiplier = (1.0 + temporal_bias * sample_weight).clamp(0.05, 2.0);
        let posterior_weight = (transition.transition_prior * posterior_multiplier).max(0.0);
        posterior_weights.insert(transition_key.clone(), posterior_weight);
        posterior_multipliers.insert(transition_key.clone(), posterior_multiplier);
        *outgoing_posterior_weight
            .entry(transition.from_branch_id.clone())
            .or_insert(0.0) += posterior_weight;
    }

    branch_temporal_posteriors.clear();
    for (transition_key, transition) in branch_transition_priors.iter() {
        let posterior_multiplier = posterior_multipliers
            .get(transition_key)
            .copied()
            .unwrap_or(1.0);
        let posterior_weight = posterior_weights
            .get(transition_key)
            .copied()
            .unwrap_or_default();
        let posterior_total = outgoing_posterior_weight
            .get(&transition.from_branch_id)
            .copied()
            .unwrap_or_default();
        let normalized_transition_posterior = if posterior_total <= f64::EPSILON {
            transition.transition_prior
        } else {
            (posterior_weight / posterior_total).clamp(0.0, 1.0)
        };
        branch_temporal_posteriors.insert(
            transition_key.clone(),
            StructuralBranchTemporalPosteriorState {
                transition_key: transition_key.clone(),
                from_branch_id: transition.from_branch_id.clone(),
                to_branch_id: transition.to_branch_id.clone(),
                observations: transition.observations,
                weighted_observation_mass: transition.weighted_observation_mass,
                transition_prior: transition.transition_prior,
                transition_outcome_support: transition.transition_outcome_support,
                temporal_posterior_support: transition.temporal_posterior_support,
                posterior_multiplier,
                normalized_transition_posterior,
                summary_line: format!(
                    "transition_mass={:.3} transition_prior={:.3} transition_support={:.3} transition_temporal={:.3} multiplier={:.3} normalized_posterior={:.3}",
                    transition.weighted_observation_mass,
                    transition.transition_prior,
                    transition.transition_outcome_support,
                    transition.temporal_posterior_support,
                    posterior_multiplier,
                    normalized_transition_posterior
                ),
                last_recommended_at: transition.last_recommended_at.clone(),
            },
        );
    }
}

fn structural_duration_positive_value(
    duration_prior: Option<&StructuralNodeDurationPrior>,
    value: impl FnOnce(&StructuralNodeDurationPrior) -> f64,
) -> Option<f64> {
    duration_prior.and_then(|prior| structural_positive_f64(value(prior)))
}

fn structural_recursive_branch_transition_posteriors(
    latest_branch_id: &str,
    branch_temporal_posteriors: &BTreeMap<String, StructuralBranchTemporalPosteriorState>,
) -> BTreeMap<String, f64> {
    let adjacency = branch_temporal_posteriors
        .values()
        .filter(|state| state.normalized_transition_posterior > f64::EPSILON)
        .fold(
            BTreeMap::<String, Vec<(&str, f64)>>::new(),
            |mut acc, state| {
                acc.entry(state.from_branch_id.clone()).or_default().push((
                    state.to_branch_id.as_str(),
                    state.normalized_transition_posterior.clamp(0.0, 1.0),
                ));
                acc
            },
        );
    let mut recursive = BTreeMap::<String, f64>::new();
    let mut frontier = BTreeMap::<String, f64>::from([(latest_branch_id.to_string(), 1.0)]);
    for depth in 1..=NODE_TRANSITION_RECURSIVE_MAX_DEPTH {
        let mut next_frontier = BTreeMap::<String, f64>::new();
        for (source_branch, source_mass) in &frontier {
            let Some(targets) = adjacency.get(source_branch) else {
                continue;
            };
            for (target_branch, edge_probability) in targets {
                *next_frontier
                    .entry((*target_branch).to_string())
                    .or_insert(0.0) += source_mass * edge_probability;
            }
        }
        if depth >= 2 {
            let depth_discount = NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT.powi((depth - 1) as i32);
            for (target_branch, path_probability) in &next_frontier {
                *recursive.entry(target_branch.clone()).or_insert(0.0) +=
                    path_probability * depth_discount;
            }
        }
        frontier = next_frontier;
        if frontier.is_empty() {
            break;
        }
    }
    recursive
}

fn structural_recursive_node_transition_posteriors(
    latest_node_id: &str,
    node_transition_posteriors: &BTreeMap<String, StructuralNodeTransitionPosteriorState>,
) -> BTreeMap<String, f64> {
    let adjacency = node_transition_posteriors
        .values()
        .filter(|state| state.normalized_transition_posterior > f64::EPSILON)
        .fold(
            BTreeMap::<String, Vec<(&str, f64)>>::new(),
            |mut acc, state| {
                acc.entry(state.from_node_id.clone()).or_default().push((
                    state.to_node_id.as_str(),
                    state.normalized_transition_posterior.clamp(0.0, 1.0),
                ));
                acc
            },
        );
    let mut recursive = BTreeMap::<String, f64>::new();
    let mut frontier = BTreeMap::<String, f64>::from([(latest_node_id.to_string(), 1.0)]);
    for depth in 1..=NODE_TRANSITION_RECURSIVE_MAX_DEPTH {
        let mut next_frontier = BTreeMap::<String, f64>::new();
        for (source_node, source_mass) in &frontier {
            let Some(targets) = adjacency.get(source_node) else {
                continue;
            };
            for (target_node, edge_probability) in targets {
                *next_frontier
                    .entry((*target_node).to_string())
                    .or_insert(0.0) += source_mass * edge_probability;
            }
        }
        if depth >= 2 {
            let depth_discount = NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT.powi((depth - 1) as i32);
            for (target_node, path_probability) in &next_frontier {
                *recursive.entry(target_node.clone()).or_insert(0.0) +=
                    path_probability * depth_discount;
            }
        }
        frontier = next_frontier;
        if frontier.is_empty() {
            break;
        }
    }
    recursive
}
