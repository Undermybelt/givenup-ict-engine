use std::collections::BTreeMap;

use crate::state::{
    StructuralBranchTemporalPosteriorState, StructuralBranchTransitionPrior,
    StructuralNodeDurationPrior, StructuralNodeTemporalPosteriorState,
};

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
}
