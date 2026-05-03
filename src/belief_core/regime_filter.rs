use std::collections::BTreeMap;

use crate::state::{
    StructuralBranchTemporalPosteriorState, StructuralBranchTransitionPrior,
    StructuralNodeTransitionPosteriorState,
};

const NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT: f64 = 0.5;
const NODE_TRANSITION_RECURSIVE_MAX_DEPTH: usize = 4;

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

    let recursive_branch_posteriors =
        structural_recursive_branch_transition_posteriors(latest_branch_id, branch_temporal_posteriors);
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
        let known_total: f64 = normalized_posterior.iter().map(|(_, posterior)| *posterior).sum();
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
            let known_total: f64 = normalized_posterior.iter().map(|(_, posterior)| *posterior).sum();
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

    let known_total: f64 = normalized_posterior.iter().map(|(_, posterior)| *posterior).sum();
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
                *next_frontier.entry((*target_branch).to_string()).or_insert(0.0) +=
                    source_mass * edge_probability;
            }
        }
        if depth >= 2 {
            let depth_discount =
                NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT.powi((depth - 1) as i32);
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
                *next_frontier.entry((*target_node).to_string()).or_insert(0.0) +=
                    source_mass * edge_probability;
            }
        }
        if depth >= 2 {
            let depth_discount =
                NODE_TRANSITION_RECURSIVE_STEP_DISCOUNT.powi((depth - 1) as i32);
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
