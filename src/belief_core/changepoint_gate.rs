use std::collections::BTreeMap;

use crate::state::StructuralNodeDurationBucket;

#[derive(Debug, Clone, Default)]
pub(crate) struct StructuralNodeStreakRecord {
    pub(crate) streak_length: usize,
    pub(crate) weighted_success_mass: f64,
    pub(crate) weighted_failure_mass: f64,
    pub(crate) last_recommended_at: Option<String>,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct StructuralNodeDurationDistributionFit {
    pub(crate) distribution: Vec<StructuralNodeDurationBucket>,
    pub(crate) entropy: f64,
    pub(crate) survival_probability: f64,
    pub(crate) completion_hazard: f64,
    pub(crate) run_length_mode: usize,
    pub(crate) run_length_mode_probability: f64,
    pub(crate) run_length_tail_probability: f64,
    pub(crate) run_length_observation_mass: f64,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct StructuralNodeBocpdRecursiveRunLengthFit {
    pub(crate) reset_probability: f64,
    pub(crate) run_length_mode: usize,
    pub(crate) run_length_mode_probability: f64,
    pub(crate) expected_run_length: f64,
    pub(crate) entropy: f64,
}

pub(crate) fn structural_duration_surprise(survival_probability: f64) -> f64 {
    if survival_probability <= f64::EPSILON {
        20.0
    } else {
        (-survival_probability.clamp(f64::EPSILON, 1.0).ln()).min(20.0)
    }
}

pub(crate) fn structural_bocpd_break_probability(
    completion_hazard: f64,
    duration_surprise: f64,
    duration_outcome_support: f64,
) -> f64 {
    let surprise_pressure = if duration_surprise <= f64::EPSILON {
        0.0
    } else {
        duration_surprise / (1.0 + duration_surprise)
    };
    let negative_outcome_pressure = (1.0 - duration_outcome_support).clamp(0.0, 1.0);
    (completion_hazard.clamp(0.0, 1.0) * 0.60
        + surprise_pressure.clamp(0.0, 1.0) * 0.25
        + negative_outcome_pressure * 0.15)
        .clamp(0.0, 1.0)
}

pub(crate) fn structural_node_duration_distribution_fit(
    duration_length_stats: &BTreeMap<usize, (usize, f64)>,
    total_weighted_streak_mass: f64,
    elapsed_dwell_steps: usize,
) -> StructuralNodeDurationDistributionFit {
    if duration_length_stats.is_empty() || total_weighted_streak_mass <= f64::EPSILON {
        return StructuralNodeDurationDistributionFit::default();
    }

    let mut entropy = 0.0;
    let mut distribution = Vec::with_capacity(duration_length_stats.len());
    let mut run_length_mode = 0;
    let mut run_length_mode_mass = 0.0;
    let mut run_length_mode_probability = 0.0;
    for (dwell_steps, (streak_count, weighted_streak_mass)) in duration_length_stats {
        let probability = (*weighted_streak_mass / total_weighted_streak_mass).clamp(0.0, 1.0);
        if probability > f64::EPSILON {
            entropy -= probability * probability.ln();
        }
        if *weighted_streak_mass > run_length_mode_mass {
            run_length_mode = *dwell_steps;
            run_length_mode_mass = *weighted_streak_mass;
            run_length_mode_probability = probability;
        }
        let survival_mass: f64 = duration_length_stats
            .iter()
            .filter(|(candidate_steps, _)| *candidate_steps >= dwell_steps)
            .map(|(_, (_, weighted_mass))| *weighted_mass)
            .sum();
        let survival_probability =
            (survival_mass / total_weighted_streak_mass).clamp(0.0, 1.0);
        let completion_hazard = if survival_mass <= f64::EPSILON {
            0.0
        } else {
            (*weighted_streak_mass / survival_mass).clamp(0.0, 1.0)
        };
        distribution.push(StructuralNodeDurationBucket {
            dwell_steps: *dwell_steps,
            streak_count: *streak_count,
            weighted_streak_mass: *weighted_streak_mass,
            probability,
            survival_probability,
            completion_hazard,
        });
    }

    let elapsed_survival_mass: f64 = duration_length_stats
        .iter()
        .filter(|(candidate_steps, _)| **candidate_steps >= elapsed_dwell_steps)
        .map(|(_, (_, weighted_mass))| *weighted_mass)
        .sum();
    let elapsed_completion_mass = duration_length_stats
        .get(&elapsed_dwell_steps)
        .map(|(_, weighted_mass)| *weighted_mass)
        .unwrap_or_default();
    let survival_probability =
        (elapsed_survival_mass / total_weighted_streak_mass).clamp(0.0, 1.0);
    let completion_hazard = if elapsed_dwell_steps == 0 {
        0.0
    } else if elapsed_survival_mass <= f64::EPSILON {
        1.0
    } else {
        (elapsed_completion_mass / elapsed_survival_mass).clamp(0.0, 1.0)
    };

    StructuralNodeDurationDistributionFit {
        distribution,
        entropy,
        survival_probability,
        completion_hazard,
        run_length_mode,
        run_length_mode_probability,
        run_length_tail_probability: survival_probability,
        run_length_observation_mass: total_weighted_streak_mass,
    }
}

pub(crate) fn structural_node_bocpd_recursive_run_length_fit(
    distribution: &[StructuralNodeDurationBucket],
    evidence_weight: f64,
    fallback_break_probability: f64,
) -> StructuralNodeBocpdRecursiveRunLengthFit {
    if distribution.is_empty() {
        return StructuralNodeBocpdRecursiveRunLengthFit::default();
    }

    let evidence_weight = evidence_weight.clamp(0.0, 1.0);
    let fallback_break_probability = fallback_break_probability.clamp(0.0, 1.0);
    let mut posterior = BTreeMap::<usize, f64>::new();
    for bucket in distribution {
        let prior_probability = bucket.probability.clamp(0.0, 1.0);
        if prior_probability <= f64::EPSILON {
            continue;
        }
        let hazard = ((1.0 - evidence_weight) * fallback_break_probability
            + evidence_weight * bucket.completion_hazard.clamp(0.0, 1.0))
            .clamp(0.0, 1.0);
        *posterior.entry(0).or_default() += prior_probability * hazard;
        *posterior
            .entry(bucket.dwell_steps.saturating_add(1))
            .or_default() += prior_probability * (1.0 - hazard);
    }

    let total_probability: f64 = posterior.values().copied().sum();
    if total_probability <= f64::EPSILON {
        return StructuralNodeBocpdRecursiveRunLengthFit::default();
    }

    let mut fit = StructuralNodeBocpdRecursiveRunLengthFit::default();
    for (run_length, probability) in posterior {
        let probability = (probability / total_probability).clamp(0.0, 1.0);
        if run_length == 0 {
            fit.reset_probability = probability;
        }
        if probability > fit.run_length_mode_probability {
            fit.run_length_mode = run_length;
            fit.run_length_mode_probability = probability;
        }
        fit.expected_run_length += run_length as f64 * probability;
        if probability > f64::EPSILON {
            fit.entropy -= probability * probability.ln();
        }
    }
    fit
}

fn structural_node_streak_outcome_support(streak: &StructuralNodeStreakRecord) -> f64 {
    let success = streak.weighted_success_mass.max(0.0);
    let failure = streak.weighted_failure_mass.max(0.0);
    ((1.0 + success) / (2.0 + success + failure)).clamp(0.0, 1.0)
}

fn structural_node_streak_pair_change(
    previous: &StructuralNodeStreakRecord,
    current: &StructuralNodeStreakRecord,
    expected_dwell_steps: f64,
) -> f64 {
    let duration_denominator = previous
        .streak_length
        .max(current.streak_length)
        .max(expected_dwell_steps.ceil() as usize)
        .max(1) as f64;
    let duration_change = (current.streak_length as f64 - previous.streak_length as f64).abs()
        / duration_denominator;
    let outcome_change = (structural_node_streak_outcome_support(current)
        - structural_node_streak_outcome_support(previous))
    .abs();
    (duration_change.clamp(0.0, 1.0) * 0.7
        + outcome_change.clamp(0.0, 1.0) * 0.3)
        .clamp(0.0, 1.0)
}

pub(crate) fn structural_node_bocpd_sequence_change_intensity(
    streaks: &[StructuralNodeStreakRecord],
    expected_dwell_steps: f64,
) -> f64 {
    if streaks.len() < 2 {
        return 0.0;
    }
    let total_streaks = streaks.len();
    let mut weighted_change_sum = 0.0;
    let mut weighted_pair_mass = 0.0;
    for index in 1..streaks.len() {
        let previous = &streaks[index - 1];
        let current = &streaks[index];
        let recency_rank = total_streaks.saturating_sub(index + 1) as f64;
        let recency_decay = 0.85_f64.powf(recency_rank);
        let pair_change =
            structural_node_streak_pair_change(previous, current, expected_dwell_steps);
        weighted_change_sum += recency_decay * pair_change;
        weighted_pair_mass += recency_decay;
    }
    if weighted_pair_mass <= f64::EPSILON {
        0.0
    } else {
        (weighted_change_sum / weighted_pair_mass).clamp(0.0, 1.0)
    }
}

pub(crate) fn structural_node_bocpd_sequence_break_probability(
    recursive_break_probability: f64,
    sequence_change_intensity: f64,
    evidence_weight: f64,
) -> f64 {
    let sequence_weight = (evidence_weight * 0.5).clamp(0.0, 0.5);
    (recursive_break_probability.clamp(0.0, 1.0) * (1.0 - sequence_weight)
        + sequence_change_intensity.clamp(0.0, 1.0) * sequence_weight)
        .clamp(0.0, 1.0)
}

pub(crate) fn structural_node_bocpd_sequence_recursive_run_length_fit(
    streaks: &[StructuralNodeStreakRecord],
    expected_dwell_steps: f64,
    fallback_break_probability: f64,
    evidence_weight: f64,
) -> StructuralNodeBocpdRecursiveRunLengthFit {
    if streaks.len() < 2 {
        return StructuralNodeBocpdRecursiveRunLengthFit::default();
    }

    let evidence_weight = evidence_weight.clamp(0.0, 1.0);
    let fallback_break_probability = fallback_break_probability.clamp(0.0, 1.0);
    let mut posterior = BTreeMap::<usize, f64>::new();
    posterior.insert(0, 1.0);
    for index in 1..streaks.len() {
        let sequence_change = structural_node_streak_pair_change(
            &streaks[index - 1],
            &streaks[index],
            expected_dwell_steps,
        );
        let adaptive_hazard = ((1.0 - evidence_weight) * fallback_break_probability
            + evidence_weight * sequence_change)
            .clamp(0.0, 1.0);
        let break_likelihood = (0.05 + sequence_change * 0.95).clamp(0.05, 1.0);
        let continue_likelihood = (0.05 + (1.0 - sequence_change) * 0.95).clamp(0.05, 1.0);
        let mut next = BTreeMap::<usize, f64>::new();
        for (run_length, probability) in posterior {
            if probability <= f64::EPSILON {
                continue;
            }
            *next.entry(0).or_default() += probability * adaptive_hazard * break_likelihood;
            *next
                .entry(run_length.saturating_add(1).min(64))
                .or_default() += probability * (1.0 - adaptive_hazard) * continue_likelihood;
        }
        let total_probability: f64 = next.values().copied().sum();
        if total_probability <= f64::EPSILON {
            return StructuralNodeBocpdRecursiveRunLengthFit::default();
        }
        posterior = next
            .into_iter()
            .map(|(run_length, probability)| {
                (run_length, (probability / total_probability).clamp(0.0, 1.0))
            })
            .collect();
    }

    let mut fit = StructuralNodeBocpdRecursiveRunLengthFit::default();
    for (run_length, probability) in posterior {
        if run_length == 0 {
            fit.reset_probability = probability;
        }
        if probability > fit.run_length_mode_probability {
            fit.run_length_mode = run_length;
            fit.run_length_mode_probability = probability;
        }
        fit.expected_run_length += run_length as f64 * probability;
        if probability > f64::EPSILON {
            fit.entropy -= probability * probability.ln();
        }
    }
    fit
}
