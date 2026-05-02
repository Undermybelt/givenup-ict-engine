use std::collections::BTreeMap;

use crate::state::{
    StructuralBranchTemporalPosteriorState, StructuralBranchTransitionPrior,
    StructuralNodeDurationPrior, StructuralNodeTemporalPosteriorState,
    StructuralNodeTransitionPosteriorState,
};

const NODE_TRANSITION_TWO_STEP_DISCOUNT: f64 = 0.5;

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
    let (Some(blend_weight), Some(temporal_support)) =
        (blend_weight, temporal_support)
    else {
        return base_posterior;
    };
    ((1.0 - blend_weight) * base_posterior
        + blend_weight * temporal_support)
        .clamp(0.0, 1.0)
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
        weighted.push((branch_id, (*probability * transition_weight).clamp(0.0, 1.0)));
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
        .or_else(|| latest_branch_id.rsplit_once(':').map(|(node_id, _)| node_id));
    if let Some(latest_node_id) = latest_node_id {
        let two_step_posteriors =
            structural_two_step_node_transition_posteriors(latest_node_id, node_transition_posteriors);
        let mut normalized_posterior = Vec::new();
        let mut missing_posterior_candidates = Vec::new();
        let mut used_two_step_fallback = false;
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
                _ if two_step_posteriors
                    .get(&node_id)
                    .copied()
                    .unwrap_or_default()
                    > f64::EPSILON =>
                {
                    used_two_step_fallback = true;
                    normalized_posterior.push((
                        regime.clone(),
                        (two_step_posteriors
                            .get(&node_id)
                            .copied()
                            .unwrap_or_default()
                            * NODE_TRANSITION_TWO_STEP_DISCOUNT)
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
            if total > f64::EPSILON && (used_two_step_fallback || residual > f64::EPSILON) {
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

fn structural_two_step_node_transition_posteriors(
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
    let mut two_step = BTreeMap::<String, f64>::new();
    let Some(first_hops) = adjacency.get(latest_node_id) else {
        return two_step;
    };
    for (intermediate_node, first_probability) in first_hops {
        let Some(second_hops) = adjacency.get(*intermediate_node) else {
            continue;
        };
        for (target_node, second_probability) in second_hops {
            *two_step.entry((*target_node).to_string()).or_insert(0.0) +=
                first_probability * second_probability;
        }
    }
    two_step
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn transition_adjusted_branch_posteriors_respects_transition_outcome_support() {
        let mut priors = BTreeMap::new();
        priors.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            StructuralBranchTransitionPrior {
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:trend".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 2,
                weighted_observation_mass: 1.5,
                wins: 2,
                losses: 0,
                invalidated: 0,
                transition_prior: 0.5,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.59,
                weighted_success_mass: 1.5,
                weighted_failure_mass: 0.0,
                last_recommended_at: None,
            },
        );
        priors.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:range_mean_reversion".to_string(),
            StructuralBranchTransitionPrior {
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:trend".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:range_mean_reversion".to_string(),
                observations: 2,
                weighted_observation_mass: 1.5,
                wins: 0,
                losses: 2,
                invalidated: 0,
                transition_prior: 0.5,
                transition_outcome_support: 0.2,
                temporal_posterior_support: 0.41,
                weighted_success_mass: 0.0,
                weighted_failure_mass: 1.5,
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_branch_posteriors(
            "NQ:belief_regime_node:trend",
            &[
                ("transition".to_string(), 0.2),
                ("range".to_string(), 0.2),
                ("trend".to_string(), 0.6),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &priors,
            &BTreeMap::new(),
            |regime| match regime {
                "transition" => "transition_confirmation",
                "range" => "range_mean_reversion",
                _ => "trend_follow_through",
            },
        );

        assert!(
            adjusted["NQ:belief_regime_node:trend:transition_confirmation"]
                > adjusted["NQ:belief_regime_node:trend:range_mean_reversion"]
        );
    }

    #[test]
    fn blend_node_posterior_prefers_persisted_temporal_state_over_duration_prior() {
        let duration_prior = StructuralNodeDurationPrior {
            observations: 6,
            streak_count: 3,
            weighted_streak_mass: 2.4,
            weighted_success_mass: 2.4,
            weighted_failure_mass: 0.0,
            total_streak_length: 6,
            avg_streak_length: 2.0,
            max_streak_length: 3,
            last_streak_length: 3,
            persistence_prior: 0.90,
            duration_outcome_support: 0.77,
            temporal_posterior_support: 0.86,
            last_recommended_at: None,
            ..StructuralNodeDurationPrior::default()
        };
        let temporal_state = StructuralNodeTemporalPosteriorState {
            node_id: "NQ:belief_regime_node:trend".to_string(),
            observations: 6,
            streak_count: 3,
            weighted_streak_mass: 2.4,
            duration_outcome_support: 0.20,
            temporal_posterior_support: 0.30,
            posterior_blend_weight: 0.5,
            summary_line: "duration_mass=2.400 duration_support=0.200 duration_temporal=0.300 blend=0.500".to_string(),
            last_recommended_at: None,
            ..StructuralNodeTemporalPosteriorState::default()
        };

        let blended = blend_node_posterior_with_duration_prior(0.60, Some(&duration_prior), Some(&temporal_state));

        assert!((blended - 0.45).abs() < 1e-9);
    }

    #[test]
    fn transition_adjusted_branch_posteriors_prefers_persisted_temporal_state_over_transition_prior() {
        let mut priors = BTreeMap::new();
        priors.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            StructuralBranchTransitionPrior {
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:trend".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 2,
                weighted_observation_mass: 1.5,
                wins: 2,
                losses: 0,
                invalidated: 0,
                transition_prior: 0.8,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.86,
                weighted_success_mass: 1.5,
                weighted_failure_mass: 0.0,
                last_recommended_at: None,
            },
        );
        let mut temporal_states = BTreeMap::new();
        temporal_states.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            StructuralBranchTemporalPosteriorState {
                transition_key: "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 2,
                weighted_observation_mass: 1.5,
                transition_prior: 0.8,
                transition_outcome_support: 0.20,
                temporal_posterior_support: 0.30,
                posterior_multiplier: 0.6,
                normalized_transition_posterior: 0.8,
                summary_line: "transition_mass=1.500 transition_support=0.200 transition_temporal=0.300 multiplier=0.600".to_string(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_branch_posteriors(
            "NQ:belief_regime_node:trend",
            &[
                ("transition".to_string(), 0.4),
                ("trend".to_string(), 0.6),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &priors,
            &temporal_states,
            |regime| match regime {
                "transition" => "transition_confirmation",
                _ => "trend_follow_through",
            },
        );

        assert!(
            (adjusted["NQ:belief_regime_node:trend:transition_confirmation"] - 0.8).abs() < 1e-9
        );
        assert!(
            (adjusted["NQ:belief_regime_node:trend:trend_follow_through"] - 0.2).abs() < 1e-9
        );
    }

    #[test]
    fn transition_adjusted_branch_posteriors_prefers_complete_normalized_posterior_state() {
        let mut temporal_states = BTreeMap::new();
        temporal_states.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            StructuralBranchTemporalPosteriorState {
                transition_key: "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                transition_prior: 0.5,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                posterior_multiplier: 1.0,
                normalized_transition_posterior: 0.8,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );
        temporal_states.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:trend_follow_through".to_string(),
            StructuralBranchTemporalPosteriorState {
                transition_key: "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                observations: 1,
                weighted_observation_mass: 0.5,
                transition_prior: 0.5,
                transition_outcome_support: 0.5,
                temporal_posterior_support: 0.5,
                posterior_multiplier: 1.0,
                normalized_transition_posterior: 0.2,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_branch_posteriors(
            "NQ:belief_regime_node:trend",
            &[
                ("transition".to_string(), 0.5),
                ("trend".to_string(), 0.5),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &BTreeMap::new(),
            &temporal_states,
            |regime| match regime {
                "transition" => "transition_confirmation",
                _ => "trend_follow_through",
            },
        );

        assert!(
            (adjusted["NQ:belief_regime_node:trend:transition_confirmation"] - 0.8).abs() < 1e-9
        );
        assert!(
            (adjusted["NQ:belief_regime_node:trend:trend_follow_through"] - 0.2).abs() < 1e-9
        );
    }

    #[test]
    fn transition_adjusted_branch_posteriors_uses_partial_normalized_posterior_state() {
        let mut temporal_states = BTreeMap::new();
        temporal_states.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            StructuralBranchTemporalPosteriorState {
                transition_key: "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                transition_prior: 0.7,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                posterior_multiplier: 0.2,
                normalized_transition_posterior: 0.7,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_branch_posteriors(
            "NQ:belief_regime_node:trend",
            &[
                ("transition".to_string(), 0.4),
                ("range".to_string(), 0.3),
                ("trend".to_string(), 0.3),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &BTreeMap::new(),
            &temporal_states,
            |regime| match regime {
                "transition" => "transition_confirmation",
                "range" => "range_mean_reversion",
                _ => "trend_follow_through",
            },
        );

        assert!(
            (adjusted["NQ:belief_regime_node:trend:transition_confirmation"] - 0.7).abs()
                < 1e-9
        );
        assert!(
            (adjusted["NQ:belief_regime_node:trend:range_mean_reversion"] - 0.15).abs()
                < 1e-9
        );
        assert!(
            (adjusted["NQ:belief_regime_node:trend:trend_follow_through"] - 0.15).abs()
                < 1e-9
        );
    }

    #[test]
    fn transition_adjusted_node_posteriors_use_maintained_branch_transition_state() {
        let mut transition_priors = BTreeMap::new();
        let key = "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:transition:transition_confirmation".to_string();
        transition_priors.insert(
            key.clone(),
            StructuralBranchTransitionPrior {
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:transition".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:transition:transition_confirmation".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                wins: 2,
                losses: 1,
                invalidated: 0,
                transition_prior: 0.7,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                weighted_success_mass: 1.4,
                weighted_failure_mass: 0.7,
                last_recommended_at: None,
            },
        );
        let mut temporal_states = BTreeMap::new();
        temporal_states.insert(
            key.clone(),
            StructuralBranchTemporalPosteriorState {
                transition_key: key,
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:transition:transition_confirmation".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                transition_prior: 0.7,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                posterior_multiplier: 0.2,
                normalized_transition_posterior: 0.7,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_node_posteriors(
            "NQ",
            &[
                ("trend".to_string(), 0.6),
                ("range".to_string(), 0.2),
                ("transition".to_string(), 0.2),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &transition_priors,
            &temporal_states,
            &BTreeMap::new(),
        );

        assert!((adjusted["transition"] - 0.7).abs() < 1e-9);
        assert!((adjusted["trend"] - 0.225).abs() < 1e-9);
        assert!((adjusted["range"] - 0.075).abs() < 1e-9);
    }

    #[test]
    fn transition_adjusted_node_posteriors_prefer_node_transition_state() {
        let mut node_states = BTreeMap::new();
        node_states.insert(
            "NQ:belief_regime_node:trend=>NQ:belief_regime_node:transition".to_string(),
            StructuralNodeTransitionPosteriorState {
                transition_key:
                    "NQ:belief_regime_node:trend=>NQ:belief_regime_node:transition".to_string(),
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:transition".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                transition_prior: 0.7,
                weighted_success_mass: 1.4,
                weighted_failure_mass: 0.7,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                posterior_multiplier: 1.2,
                normalized_transition_posterior: 0.8,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_node_posteriors(
            "NQ",
            &[
                ("trend".to_string(), 0.6),
                ("range".to_string(), 0.2),
                ("transition".to_string(), 0.2),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &BTreeMap::new(),
            &BTreeMap::new(),
            &node_states,
        );

        assert!((adjusted["transition"] - 0.8).abs() < 1e-9);
        assert!((adjusted["trend"] - 0.15).abs() < 1e-9);
        assert!((adjusted["range"] - 0.05).abs() < 1e-9);
    }

    #[test]
    fn transition_adjusted_node_posteriors_use_discounted_two_step_fallback() {
        let mut node_states = BTreeMap::new();
        node_states.insert(
            "NQ:belief_regime_node:trend=>NQ:belief_regime_node:transition".to_string(),
            StructuralNodeTransitionPosteriorState {
                transition_key:
                    "NQ:belief_regime_node:trend=>NQ:belief_regime_node:transition".to_string(),
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:transition".to_string(),
                observations: 3,
                weighted_observation_mass: 2.1,
                transition_prior: 0.7,
                weighted_success_mass: 1.4,
                weighted_failure_mass: 0.7,
                transition_outcome_support: 0.8,
                temporal_posterior_support: 0.7,
                posterior_multiplier: 1.2,
                normalized_transition_posterior: 0.7,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );
        node_states.insert(
            "NQ:belief_regime_node:transition=>NQ:belief_regime_node:range".to_string(),
            StructuralNodeTransitionPosteriorState {
                transition_key:
                    "NQ:belief_regime_node:transition=>NQ:belief_regime_node:range".to_string(),
                from_node_id: "NQ:belief_regime_node:transition".to_string(),
                to_node_id: "NQ:belief_regime_node:range".to_string(),
                observations: 2,
                weighted_observation_mass: 1.6,
                transition_prior: 0.8,
                weighted_success_mass: 1.2,
                weighted_failure_mass: 0.4,
                transition_outcome_support: 0.75,
                temporal_posterior_support: 0.78,
                posterior_multiplier: 1.1,
                normalized_transition_posterior: 0.8,
                summary_line: String::new(),
                last_recommended_at: None,
            },
        );

        let adjusted = transition_adjusted_node_posteriors(
            "NQ",
            &[
                ("trend".to_string(), 0.6),
                ("range".to_string(), 0.2),
                ("transition".to_string(), 0.2),
            ],
            Some("NQ:belief_regime_node:trend:trend_follow_through"),
            &BTreeMap::new(),
            &BTreeMap::new(),
            &node_states,
        );

        assert!((adjusted["transition"] - 0.7).abs() < 1e-9);
        assert!((adjusted["range"] - 0.28).abs() < 1e-9);
        assert!((adjusted["trend"] - 0.02).abs() < 1e-9);
    }
}
