use std::collections::BTreeMap;

use crate::state::{StructuralBranchTransitionPrior, StructuralNodeDurationPrior};

pub fn blend_node_posterior_with_duration_prior(
    base_posterior: f64,
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> f64 {
    let Some(duration_prior) = duration_prior else {
        return base_posterior;
    };
    let observation_weight = (duration_prior.weighted_streak_mass / 3.0).min(1.0);
    let streak_weight = (duration_prior.streak_count as f64 / 3.0).min(1.0);
    let blend_weight = (observation_weight * streak_weight * 0.5).clamp(0.0, 0.5);
    ((1.0 - blend_weight) * base_posterior
        + blend_weight * duration_prior.temporal_posterior_support)
        .clamp(0.0, 1.0)
}

pub fn blend_branch_prior_with_transition_prior(
    base_prior: f64,
    transition_prior: Option<&StructuralBranchTransitionPrior>,
) -> f64 {
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

    let mut weighted = Vec::new();
    for (regime, probability) in regime_probabilities {
        let branch_id = format!("{node_id}:{}", branch_label_for_regime(regime));
        let transition_key = format!("{latest_branch_id}=>{branch_id}");
        let transition_prior = transition_priors.get(&transition_key);
        let transition_weight = transition_prior
            .map(|prior| {
                let sample_weight = (prior.weighted_observation_mass / 3.0).min(1.0);
                let temporal_bias = (prior.temporal_posterior_support - 0.5) * 2.0;
                (1.0 + temporal_bias * sample_weight)
                    .clamp(0.05, 2.0)
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
}
