use std::collections::BTreeMap;

use crate::state::{StructuralBranchTransitionPrior, StructuralNodeDurationPrior};

pub fn blend_node_posterior_with_duration_prior(
    base_posterior: f64,
    duration_prior: Option<&StructuralNodeDurationPrior>,
) -> f64 {
    let Some(duration_prior) = duration_prior else {
        return base_posterior;
    };
    let observation_weight = (duration_prior.observations as f64 / 4.0).min(1.0);
    let streak_weight = (duration_prior.streak_count as f64 / 3.0).min(1.0);
    let blend_weight = (observation_weight * streak_weight * 0.5).clamp(0.0, 0.5);
    ((1.0 - blend_weight) * base_posterior
        + blend_weight * duration_prior.persistence_prior)
        .clamp(0.0, 1.0)
}

pub fn blend_branch_prior_with_transition_prior(
    base_prior: f64,
    transition_prior: Option<&StructuralBranchTransitionPrior>,
) -> f64 {
    let Some(transition_prior) = transition_prior else {
        return base_prior;
    };
    let transition_weight = (transition_prior.observations as f64 / 3.0).min(1.0);
    ((1.0 - transition_weight) * base_prior
        + transition_weight * transition_prior.transition_prior)
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
                let sample_weight = (prior.observations as f64 / 3.0).min(1.0);
                (1.0 + (prior.transition_prior - 0.5) * 2.0 * sample_weight).clamp(0.05, 2.0)
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
