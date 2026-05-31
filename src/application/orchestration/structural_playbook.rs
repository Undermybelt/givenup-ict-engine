use anyhow::Result;
use chrono::{SecondsFormat, Utc};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;

use crate::application::auto_quant::AgentMaterialRankArtifact;
use crate::application::belief::{
    blend_branch_prior_with_transition_prior, blend_node_posterior_with_duration_prior,
    transition_adjusted_branch_posteriors,
};
use crate::application::provider_catalog::{
    build_workflow_provider_support, ProviderCatalogAgentSurface,
};
pub use crate::belief_core::ranking_label::{
    apply_structural_path_probability_bins, apply_structural_path_probability_calibration,
    apply_structural_path_ranking_execution_gates,
    clear_structural_path_ranking_target_row_outputs,
    evaluate_structural_path_probability_calibration_rows,
    load_structural_path_ranker_runtime_artifact_metadata,
    load_structural_path_ranker_runtime_artifact_rows,
    load_structural_path_ranking_runtime_selection, load_structural_path_ranking_target_rows,
    rebase_structural_path_ranking_target_export_summary_paths,
    render_structural_path_ranking_target_csv, render_structural_path_ranking_target_jsonl,
    render_structural_path_ranking_target_rows_csv,
    render_structural_path_ranking_target_rows_jsonl,
    score_structural_path_ranker_runtime_rows_with_direct_model,
    score_structural_path_ranker_runtime_rows_with_explicit_family,
    score_structural_path_ranker_runtime_rows_with_service,
    structural_path_ranker_supports_direct_model_family,
    structural_path_ranker_supports_explicit_family,
    structural_path_ranker_supports_service_family, structural_path_ranking_beta_lower_bound,
    structural_path_ranking_beta_mean, structural_path_ranking_candidate_path_score_key,
    structural_path_ranking_ips_weight, structural_path_ranking_propensity_estimate,
    structural_path_ranking_propensity_evaluation_weight, structural_path_ranking_reward_label,
    structural_path_ranking_runtime_selection_path, structural_path_ranking_target_export_summary,
    structural_path_ranking_target_row_history_key, structural_path_ranking_target_row_score_key,
    structural_path_ranking_trainer_manifest, structural_path_ranking_training_weight,
    upsert_structural_path_ranking_target_history, StructuralPathProbabilityCalibrationBin,
    StructuralPathProbabilityCalibrationEvaluationBin,
    StructuralPathProbabilityCalibrationEvaluationReport,
    StructuralPathProbabilityCalibrationReport, StructuralPathRankerRuntimeRow,
    StructuralPathRankerRuntimeSurface, StructuralPathRankingExternalScoreInput,
    StructuralPathRankingRuntimeSelection, StructuralPathRankingTargetArtifact,
    StructuralPathRankingTargetExportSummary, StructuralPathRankingTargetExportSummaryInput,
    StructuralPathRankingTargetRow, StructuralPathRankingTrainerManifest,
    STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
    STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY,
    STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_FILE,
    STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_PROTOCOL_VERSION,
};
pub use crate::belief_core::regime_filter::StructuralTemporalSummaryArtifact;
use crate::belief_core::regime_filter::StructuralTemporalSummaryArtifactInput;
pub use crate::belief_core::regime_filter::{
    build_structural_temporal_summary_artifact, structural_duration_avg_streak_length,
    structural_duration_bocpd_break_probability, structural_duration_bocpd_continue_probability,
    structural_duration_bocpd_evidence_weight, structural_duration_bocpd_raw_break_probability,
    structural_duration_bocpd_recursive_reset_probability,
    structural_duration_bocpd_recursive_run_length_entropy,
    structural_duration_bocpd_recursive_run_length_expected_value,
    structural_duration_bocpd_recursive_run_length_mode,
    structural_duration_bocpd_recursive_run_length_mode_probability,
    structural_duration_bocpd_run_length_mode,
    structural_duration_bocpd_run_length_mode_probability,
    structural_duration_bocpd_run_length_observation_mass,
    structural_duration_bocpd_run_length_tail_probability,
    structural_duration_bocpd_sequence_break_probability,
    structural_duration_bocpd_sequence_change_intensity,
    structural_duration_bocpd_sequence_recursive_reset_probability,
    structural_duration_bocpd_sequence_recursive_run_length_entropy,
    structural_duration_bocpd_sequence_recursive_run_length_expected_value,
    structural_duration_bocpd_sequence_recursive_run_length_mode,
    structural_duration_bocpd_sequence_recursive_run_length_mode_probability,
    structural_duration_bocpd_surprise, structural_duration_break_hazard,
    structural_duration_distribution_entropy, structural_duration_empirical_completion_hazard,
    structural_duration_empirical_survival, structural_duration_expected_dwell_steps,
    structural_duration_outcome_support, structural_duration_persistence_prior,
    structural_duration_remaining_dwell_steps, structural_duration_sticky_self_transition_strength,
    structural_duration_streak_count, structural_duration_temporal_posterior_support,
    structural_duration_weighted_streak_mass,
};
pub use crate::belief_core::source_reliability::{
    structural_branch_history_invalidation_rate, structural_branch_history_win_rate,
    structural_composite_preference_score, structural_delayed_reward_replay_validation,
    structural_dominant_source_panel, structural_experience_prior_runtime_metrics,
    structural_history_adjusted_branch_prior, structural_history_adjusted_node_prior,
    structural_history_adjusted_path_prior, structural_history_adjusted_scenario_prior,
    structural_history_invalidation_rate, structural_history_win_rate,
    structural_last_offline_seed_source, structural_node_history_invalidation_rate,
    structural_node_history_win_rate, structural_panel_derived_smoothed_prior,
    structural_prior_behavior_policy_probability,
    structural_prior_behavior_policy_probability_variance,
    structural_prior_censoring_adjusted_reward_lower_bound,
    structural_prior_censoring_adjusted_reward_prior, structural_prior_censoring_rate,
    structural_prior_counterfactual_reward_prior,
    structural_prior_delayed_reward_abandonment_competing_risk,
    structural_prior_delayed_reward_abandonment_cumulative_incidence_4h,
    structural_prior_delayed_reward_abandonment_hazard_per_hour,
    structural_prior_delayed_reward_avg_elapsed_hours,
    structural_prior_delayed_reward_censoring_probability,
    structural_prior_delayed_reward_competing_risk_entropy,
    structural_prior_delayed_reward_elapsed_feedback_count,
    structural_prior_delayed_reward_elapsed_hours_at_risk,
    structural_prior_delayed_reward_expected_resolution_hours,
    structural_prior_delayed_reward_failure_competing_risk,
    structural_prior_delayed_reward_failure_cumulative_incidence_4h,
    structural_prior_delayed_reward_failure_hazard_per_hour,
    structural_prior_delayed_reward_invalidation_competing_risk,
    structural_prior_delayed_reward_invalidation_cumulative_incidence_4h,
    structural_prior_delayed_reward_invalidation_hazard_per_hour,
    structural_prior_delayed_reward_resolution_hazard_per_hour,
    structural_prior_delayed_reward_resolution_horizon_1h_count,
    structural_prior_delayed_reward_resolution_horizon_24h_count,
    structural_prior_delayed_reward_resolution_horizon_4h_count,
    structural_prior_delayed_reward_resolution_probability,
    structural_prior_delayed_reward_resolution_probability_1h,
    structural_prior_delayed_reward_resolution_probability_24h,
    structural_prior_delayed_reward_resolution_probability_4h,
    structural_prior_delayed_reward_resolution_within_1h_count,
    structural_prior_delayed_reward_resolution_within_24h_count,
    structural_prior_delayed_reward_resolution_within_4h_count,
    structural_prior_delayed_reward_success_competing_risk,
    structural_prior_delayed_reward_success_cumulative_incidence_4h,
    structural_prior_delayed_reward_success_hazard_per_hour,
    structural_prior_delayed_reward_survival_probability_1h,
    structural_prior_delayed_reward_survival_probability_24h,
    structural_prior_delayed_reward_survival_probability_4h,
    structural_prior_doubly_robust_reward_prior, structural_prior_execution_propensity,
    structural_prior_ips_weight, structural_prior_matured_feedback_count,
    structural_prior_maturity_coverage, structural_prior_off_policy_adjusted_prior,
    structural_prior_positive_count, structural_prior_positive_value,
    structural_prior_snips_effective_sample_size, structural_prior_snips_reward_prior,
    structural_prior_snips_weight_mass, structural_prior_snips_weight_squared_mass,
    structural_prior_target_policy_calibration_weight,
    structural_prior_target_policy_probability_brier_score,
    structural_prior_target_policy_probability_calibration_error,
    structural_prior_target_policy_probability_confidence,
    structural_prior_target_policy_probability_lower_bound,
    structural_prior_target_policy_reward_lower_bound, structural_prior_target_policy_reward_prior,
    structural_prior_target_policy_variance_penalty, structural_prior_unresolved_feedback_count,
    structural_resolved_avg_pnl, structural_resolved_branch_invalidation_rate,
    structural_resolved_branch_win_rate, structural_resolved_followed_count,
    structural_resolved_node_invalidation_rate, structural_resolved_node_win_rate,
    structural_resolved_observations, structural_resolved_path_invalidation_rate,
    structural_resolved_path_win_rate, structural_resolved_scenario_invalidation_rate,
    structural_resolved_scenario_win_rate, structural_resolved_smoothed_prior,
    structural_scenario_history_invalidation_rate, structural_scenario_history_win_rate,
    structural_source_confusion_concentration_multiplier, structural_source_panel_count,
    structural_source_reliability_em_readiness, structural_source_reliability_multiplier,
    structural_target_policy_context_surface, structural_target_policy_context_surfaces,
    StructuralExperiencePriorEntry, StructuralExperiencePriorSurfaceArtifact,
    StructuralSourceReliabilityEmReadiness, StructuralTargetPolicyContextSurface,
};
pub use crate::belief_core::structural_state::{
    StructuralBranchArtifact, StructuralBranchHistoryArtifact, StructuralBranchOutcomeSummary,
    StructuralBranchSetArtifact, StructuralEntityHistorySummary, StructuralFeedbackField,
    StructuralFeedbackSubmission, StructuralFeedbackTemplateArtifact,
    StructuralHistorySummaryArtifact, StructuralNodeArtifact, StructuralNodeHistoryArtifact,
    StructuralNodeOutcomeSummary, StructuralPathArtifact, StructuralPathHistoryArtifact,
    StructuralPathHistorySummary, StructuralPathOutcomeSummary, StructuralPathPlanArtifact,
    StructuralPlaybookBundle, StructuralRecommendedPathBundleArtifact, StructuralScenarioArtifact,
    StructuralScenarioHistoryArtifact, StructuralScenarioOutcomeSummary,
    StructuralScenarioPlaybookArtifact, StructuralTopPathCandidate,
    StructuralTopPathCandidatesArtifact,
};
use crate::state::{
    recommended_next_command_meta, save_text_state, structural_feedback_learning_outcome,
    structural_feedback_outcome_is_unresolved, FeedbackFactorUsage, FeedbackRecord,
    ModelProbabilitySnapshot, StructuralFeedbackLearningOutcome, StructuralFeedbackRefs,
    StructuralPriorLearningState, WorkflowSnapshot,
};
use crate::types::{Direction, Regime};

#[cfg(test)]
use crate::state::StructuralPriorStats;

const STRUCTURAL_PLAYBOOK_ARTIFACT_VERSION: &str = "structural-playbook-v1";
const STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR: &str = "policy_training";
pub const STRUCTURAL_PATH_RANKING_TARGET_CSV_FILE: &str = "structural_path_ranking_target.csv";
pub const STRUCTURAL_PATH_RANKING_TARGET_JSONL_FILE: &str = "structural_path_ranking_target.jsonl";
pub const STRUCTURAL_PATH_RANKING_TARGET_HISTORY_CSV_FILE: &str =
    "structural_path_ranking_target_history.csv";
pub const STRUCTURAL_PATH_RANKING_TARGET_HISTORY_JSONL_FILE: &str =
    "structural_path_ranking_target_history.jsonl";
pub const STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE: &str =
    "structural_path_ranking_target_summary.json";

#[derive(Debug, Clone, Default)]
pub(crate) struct StructuralPathRankerRuntimeContext<'a> {
    pub(crate) state_dir: Option<&'a str>,
}

#[derive(Debug, Clone, Default)]
struct StructuralRankedPathSelection {
    candidate_set_id: String,
    candidate_paths: Vec<StructuralPathArtifact>,
    runtime: Option<StructuralPathRankerRuntimeSurface>,
}

#[derive(Debug, Clone)]
struct StructuralPathRankerRuntimeRowMatch {
    source: &'static str,
    row: StructuralPathRankerRuntimeRow,
}

fn structural_path_ranker_runtime_row_with_history_gate_metadata(
    mut row: StructuralPathRankerRuntimeRow,
    history_row: Option<&StructuralPathRankerRuntimeRow>,
) -> StructuralPathRankerRuntimeRow {
    let Some(history_row) = history_row else {
        return row;
    };
    if row.calibrated_path_prob.is_none() {
        row.calibrated_path_prob = history_row.calibrated_path_prob;
    }
    if row.path_prob_lower_bound.is_none() {
        row.path_prob_lower_bound = history_row.path_prob_lower_bound;
    }
    if row.execution_gate_status.is_none() {
        row.execution_gate_status = history_row.execution_gate_status.clone();
    }
    row
}

fn structural_path_ranker_candidate_row_key(row: &StructuralPathRankingTargetRow) -> String {
    format!("{}|{}", row.candidate_set_id, row.path_id)
}

fn structural_path_ranker_runtime_candidate_row_key(
    row: &StructuralPathRankerRuntimeRow,
) -> String {
    format!("{}|{}", row.candidate_set_id, row.path_id)
}

pub fn resolved_latest_ensemble_vote(
    snapshot: &WorkflowSnapshot,
) -> Option<crate::state::EnsembleVoteRecord> {
    snapshot
        .latest_ensemble_vote
        .as_ref()
        .and_then(|vote| resolved_ensemble_vote_for_snapshot(snapshot, vote))
}

pub fn resolved_ensemble_vote_for_snapshot(
    snapshot: &WorkflowSnapshot,
    vote: &crate::state::EnsembleVoteRecord,
) -> Option<crate::state::EnsembleVoteRecord> {
    let mut vote = vote.clone();
    let Some(phase) = matching_phase_snapshot_for_ensemble_vote(snapshot, &vote) else {
        return Some(vote);
    };
    let Some((active_regime, probabilities, confidence)) = canonical_phase_regime_surface(phase)
    else {
        return Some(vote);
    };
    vote.posterior_active_regime = active_regime;
    vote.posterior_probabilities = probabilities;
    vote.posterior_confidence = Some(confidence);
    vote.confidence = confidence;
    vote.consensus_strength = confidence;
    vote.posterior_normalization_status = "canonical_structural_regime_posterior".to_string();
    Some(vote)
}

fn matching_phase_snapshot_for_ensemble_vote<'a>(
    snapshot: &'a WorkflowSnapshot,
    vote: &crate::state::EnsembleVoteRecord,
) -> Option<&'a crate::state::WorkflowPhaseSnapshot> {
    [
        snapshot.latest_update.as_ref(),
        snapshot.latest_research.as_ref(),
        snapshot.latest_analyze.as_ref(),
        snapshot.latest_backtest.as_ref(),
        snapshot.latest_train.as_ref(),
    ]
    .into_iter()
    .flatten()
    .find(|phase| {
        let phase_matches = vote.source_phase == phase.phase
            || (phase.phase == "research" && vote.source_phase == "factor-research")
            || (phase.phase == "backtest" && vote.source_phase == "factor-backtest");
        phase_matches
            && vote
                .source_run_id
                .as_deref()
                .map(|run_id| run_id == phase.run_id)
                .unwrap_or(false)
    })
}

pub fn canonical_phase_regime_surface(
    phase: &crate::state::WorkflowPhaseSnapshot,
) -> Option<(String, std::collections::BTreeMap<String, f64>, f64)> {
    if !phase.canonical_structural_probabilities.is_empty() {
        let active_regime = phase
            .canonical_structural_active_regime
            .clone()
            .or_else(|| {
                phase
                    .canonical_structural_probabilities
                    .iter()
                    .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                    .map(|(label, _)| label.clone())
            })?;
        let confidence = phase.canonical_structural_confidence.unwrap_or_else(|| {
            phase
                .canonical_structural_probabilities
                .get(&active_regime)
                .copied()
                .unwrap_or(0.0)
        });
        return Some((
            active_regime,
            phase.canonical_structural_probabilities.clone(),
            confidence,
        ));
    }
    let distribution = phase.pre_bayes_soft_evidence.get("market_regime")?;
    let mut probabilities = std::collections::BTreeMap::new();
    for (label, probability) in distribution {
        if let Some(canonical) = canonical_structural_regime_label(label) {
            *probabilities.entry(canonical).or_insert(0.0) += *probability;
        }
    }
    if probabilities.is_empty() {
        return None;
    }
    let active_regime = phase
        .pre_bayes_filtered_assignments
        .get("market_regime")
        .and_then(|value| canonical_structural_regime_label(value))
        .or_else(|| {
            probabilities
                .iter()
                .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                .map(|(label, _)| label.clone())
        })?;
    let confidence = probabilities.get(&active_regime).copied().unwrap_or(0.0);
    Some((active_regime, probabilities, confidence))
}

pub fn canonical_analyze_regime_surface(
    analyze: &crate::state::WorkflowPhaseSnapshot,
) -> Option<(String, std::collections::BTreeMap<String, f64>, f64)> {
    canonical_phase_regime_surface(analyze)
}

pub fn build_structural_playbook_bundle(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> StructuralPlaybookBundle {
    build_structural_playbook_bundle_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_playbook_bundle_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralPlaybookBundle {
    build_structural_playbook_bundle_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    )
}

pub(crate) fn build_structural_playbook_bundle_with_runtime_context_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    runtime_context: StructuralPathRankerRuntimeContext<'_>,
) -> StructuralPlaybookBundle {
    let command = top_level_command(snapshot);
    let support_reason = structural_support_reason(snapshot);
    let provider_support =
        build_workflow_provider_support(provider_status_agent, &command, support_reason.as_deref());
    let focus_phase = structural_focus_phase(snapshot);
    let node = build_structural_node_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        structural_prior_state,
    );
    let branch_history = build_structural_branch_history_artifact(snapshot, feedback_history);
    let scenario_history = build_structural_scenario_history_artifact(snapshot, feedback_history);
    let path_history = build_structural_path_history_artifact(snapshot, feedback_history);
    let branch_set = build_structural_branch_set_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &node,
        &branch_history,
        structural_prior_state,
    );
    let scenario_playbook = build_structural_scenario_playbook_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &branch_set,
        &scenario_history,
        structural_prior_state,
    );
    let path_plan = build_structural_path_plan_artifact_with_runtime_context_and_prior_state(
        StructuralPathPlanArtifactInput {
            snapshot,
            provider_status_agent,
            provider_support: &provider_support,
            scenarios: &scenario_playbook,
            feedback_history,
            path_history: &path_history,
            structural_prior_state,
            runtime_context: runtime_context.clone(),
        },
    );
    let feedback_template = build_structural_feedback_template_artifact(
        snapshot,
        &node,
        &branch_set,
        &scenario_playbook,
        &path_plan,
    );
    let recommended_path_bundle =
        build_structural_recommended_path_bundle_artifact_with_runtime_context_and_prior_state(
            snapshot,
            provider_status_agent,
            feedback_history,
            structural_prior_state,
            runtime_context,
        );
    let history_summary = build_structural_history_summary_artifact(snapshot, feedback_history);
    let node_history = build_structural_node_history_artifact(snapshot, feedback_history);
    StructuralPlaybookBundle {
        artifact_version: STRUCTURAL_PLAYBOOK_ARTIFACT_VERSION.to_string(),
        symbol: structural_symbol(snapshot),
        selected_profile_id: provider_status_agent
            .selected_profile
            .as_ref()
            .map(|profile| profile.profile_id.clone()),
        selected_profile_data_contracts: structural_relevant_profile_data_contracts(
            snapshot,
            provider_status_agent,
        ),
        selected_profile_track_statuses: structural_relevant_profile_track_statuses(
            snapshot,
            provider_status_agent,
        ),
        node: StructuralNodeArtifact {
            focus_phase,
            ..node
        },
        branch_set,
        scenario_playbook,
        path_plan,
        history_summary,
        node_history,
        branch_history,
        scenario_history,
        path_history,
        recommended_path_bundle,
        feedback_template,
    }
}

pub fn build_structural_experience_prior_surface_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> StructuralExperiencePriorSurfaceArtifact {
    build_structural_experience_prior_surface_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

fn structural_feedback_records_for_path<'a>(
    feedback_history: &'a [FeedbackRecord],
    path_id: &str,
) -> Vec<&'a FeedbackRecord> {
    feedback_history
        .iter()
        .filter(|record| {
            record
                .structural_feedback
                .as_ref()
                .map(|refs| refs.path_id == path_id)
                .unwrap_or(false)
        })
        .collect()
}

pub fn build_structural_experience_prior_surface_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralExperiencePriorSurfaceArtifact {
    let playbook = build_structural_playbook_bundle_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let latest_feedback = structural_latest_feedback_refs(snapshot);
    let node_id = latest_feedback
        .as_ref()
        .map(|refs| refs.node_id.as_str())
        .unwrap_or(playbook.node.node_id.as_str());
    let branch_id = latest_feedback
        .as_ref()
        .map(|refs| refs.branch_id.as_str())
        .or_else(|| {
            playbook
                .branch_set
                .branches
                .first()
                .map(|branch| branch.branch_id.as_str())
        });
    let scenario_id = latest_feedback
        .as_ref()
        .map(|refs| refs.scenario_id.as_str())
        .or_else(|| {
            playbook
                .scenario_playbook
                .scenarios
                .first()
                .map(|scenario| scenario.scenario_id.as_str())
        });
    let path_id = latest_feedback
        .as_ref()
        .map(|refs| refs.path_id.as_str())
        .or_else(|| {
            playbook
                .path_plan
                .paths
                .first()
                .map(|path| path.path_id.as_str())
        });
    let node_summary = playbook
        .node_history
        .nodes
        .iter()
        .find(|node| node.node_id == node_id);
    let branch_summary = branch_id.and_then(|id| {
        playbook
            .branch_history
            .branches
            .iter()
            .find(|branch| branch.branch_id == id)
    });
    let scenario_summary = scenario_id.and_then(|id| {
        playbook
            .scenario_history
            .scenarios
            .iter()
            .find(|scenario| scenario.scenario_id == id)
    });
    let path_summary = path_id.and_then(|id| {
        playbook
            .path_history
            .paths
            .iter()
            .find(|path| path.path_id == id)
    });
    let branch = branch_id.and_then(|id| {
        let prior_stats = structural_prior_state.branches.get(id);
        let (dominant_source_panel, dominant_source_share, dominant_source_prior) =
            structural_dominant_source_panel(prior_stats);
        playbook
            .branch_set
            .branches
            .iter()
            .find(|branch| branch.branch_id == id)
            .map(|branch| StructuralExperiencePriorEntry {
                entity_kind: "branch".to_string(),
                entity_id: branch.branch_id.clone(),
                historical_total_records: branch.historical_total_records,
                historical_followed_count: branch.historical_followed_count,
                historical_win_rate: branch.historical_win_rate,
                historical_invalidation_rate: branch.historical_invalidation_rate,
                historical_avg_pnl: branch.historical_avg_pnl,
                experience_prior: branch.prior_probability,
                current_posterior: Some(branch.posterior_probability),
                composite_score: branch.composite_branch_score,
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: branch.transition_weighted_observation_mass,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: branch.transition_outcome_support,
                transition_temporal_posterior_support: branch.transition_temporal_posterior_support,
                ..structural_experience_prior_runtime_metrics(prior_stats, None)
            })
            .or_else(|| {
                branch_summary.map(|summary| {
                    let experience_prior =
                        structural_history_adjusted_branch_prior(0.5, Some(summary));
                    StructuralExperiencePriorEntry {
                        entity_kind: "branch".to_string(),
                        entity_id: summary.branch_id.clone(),
                        historical_total_records: summary.total_records,
                        historical_followed_count: summary.followed_count,
                        historical_win_rate: structural_branch_history_win_rate(Some(summary)),
                        historical_invalidation_rate: structural_branch_history_invalidation_rate(
                            Some(summary),
                        ),
                        historical_avg_pnl: Some(summary.avg_pnl),
                        experience_prior,
                        current_posterior: None,
                        composite_score: experience_prior,
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
                        ..structural_experience_prior_runtime_metrics(prior_stats, None)
                    }
                })
            })
    });
    let scenario = scenario_id.and_then(|id| {
        let prior_stats = structural_prior_state.scenarios.get(id);
        let (dominant_source_panel, dominant_source_share, dominant_source_prior) =
            structural_dominant_source_panel(prior_stats);
        playbook
            .scenario_playbook
            .scenarios
            .iter()
            .find(|scenario| scenario.scenario_id == id)
            .map(|scenario| StructuralExperiencePriorEntry {
                entity_kind: "scenario".to_string(),
                entity_id: scenario.scenario_id.clone(),
                historical_total_records: scenario.historical_total_records,
                historical_followed_count: scenario.historical_followed_count,
                historical_win_rate: scenario.historical_win_rate,
                historical_invalidation_rate: scenario.historical_invalidation_rate,
                historical_avg_pnl: scenario.historical_avg_pnl,
                experience_prior: scenario.prior_probability,
                current_posterior: Some(scenario.posterior_probability),
                composite_score: scenario.composite_scenario_score,
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: None,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
                ..structural_experience_prior_runtime_metrics(prior_stats, None)
            })
            .or_else(|| {
                scenario_summary.map(|summary| {
                    let experience_prior =
                        structural_history_adjusted_scenario_prior(0.5, Some(summary));
                    StructuralExperiencePriorEntry {
                        entity_kind: "scenario".to_string(),
                        entity_id: summary.scenario_id.clone(),
                        historical_total_records: summary.total_records,
                        historical_followed_count: summary.followed_count,
                        historical_win_rate: structural_scenario_history_win_rate(Some(summary)),
                        historical_invalidation_rate: structural_scenario_history_invalidation_rate(
                            Some(summary),
                        ),
                        historical_avg_pnl: Some(summary.avg_pnl),
                        experience_prior,
                        current_posterior: None,
                        composite_score: experience_prior,
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
                        ..structural_experience_prior_runtime_metrics(prior_stats, None)
                    }
                })
            })
    });
    let path = path_id.and_then(|id| {
        let prior_stats = structural_prior_state.paths.get(id);
        let delayed_reward_replay_validation = structural_delayed_reward_replay_validation(
            &structural_feedback_records_for_path(feedback_history, id),
        );
        let (dominant_source_panel, dominant_source_share, dominant_source_prior) =
            structural_dominant_source_panel(prior_stats);
        playbook
            .path_plan
            .paths
            .iter()
            .find(|path| path.path_id == id)
            .map(|path| StructuralExperiencePriorEntry {
                entity_kind: "path".to_string(),
                entity_id: path.path_id.clone(),
                historical_total_records: path.historical_total_records,
                historical_followed_count: path.historical_followed_count,
                historical_win_rate: path.historical_win_rate,
                historical_invalidation_rate: path.historical_invalidation_rate,
                historical_avg_pnl: path.historical_avg_pnl,
                experience_prior: path.path_prior,
                current_posterior: Some(path.path_posterior),
                composite_score: path.composite_preference_score,
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: None,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
                ..structural_experience_prior_runtime_metrics(
                    prior_stats,
                    delayed_reward_replay_validation.clone(),
                )
            })
            .or_else(|| {
                path_summary.map(|summary| {
                    let experience_prior =
                        structural_history_adjusted_path_prior(0.5, Some(summary));
                    StructuralExperiencePriorEntry {
                        entity_kind: "path".to_string(),
                        entity_id: summary.path_id.clone(),
                        historical_total_records: summary.total_records,
                        historical_followed_count: summary.followed_count,
                        historical_win_rate: structural_history_win_rate(Some(summary)),
                        historical_invalidation_rate: structural_history_invalidation_rate(Some(
                            summary,
                        )),
                        historical_avg_pnl: Some(summary.avg_pnl),
                        experience_prior,
                        current_posterior: None,
                        composite_score: experience_prior,
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
                        ..structural_experience_prior_runtime_metrics(
                            prior_stats,
                            delayed_reward_replay_validation.clone(),
                        )
                    }
                })
            })
    });
    let node_prior_stats = structural_prior_state.nodes.get(node_id);
    let (dominant_source_panel, dominant_source_share, dominant_source_prior) =
        structural_dominant_source_panel(node_prior_stats);
    let node_duration_prior = structural_prior_state.node_duration_priors.get(node_id);
    let node_temporal_state = structural_prior_state.node_temporal_posteriors.get(node_id);
    StructuralExperiencePriorSurfaceArtifact {
        symbol: structural_symbol(snapshot),
        source_reliability_em: structural_source_reliability_em_readiness(structural_prior_state),
        target_policy_contexts: structural_target_policy_context_surfaces(structural_prior_state),
        node: Some(StructuralExperiencePriorEntry {
            entity_kind: "node".to_string(),
            entity_id: node_id.to_string(),
            historical_total_records: node_summary
                .map(|summary| summary.total_records)
                .unwrap_or(0),
            historical_followed_count: node_summary
                .map(|summary| summary.followed_count)
                .unwrap_or(0),
            historical_win_rate: structural_resolved_node_win_rate(
                structural_prior_state.nodes.get(node_id),
                node_summary,
            ),
            historical_invalidation_rate: structural_resolved_node_invalidation_rate(
                structural_prior_state.nodes.get(node_id),
                node_summary,
            ),
            historical_avg_pnl: structural_resolved_avg_pnl(
                structural_prior_state.nodes.get(node_id),
                node_summary.map(|summary| summary.avg_pnl),
            ),
            experience_prior: structural_resolved_smoothed_prior(
                structural_prior_state.nodes.get(node_id),
                structural_prior_state,
                structural_history_adjusted_node_prior(playbook.node.belief_prior, node_summary),
            ),
            current_posterior: Some(playbook.node.posterior_confidence),
            composite_score: structural_composite_preference_score(
                playbook.node.posterior_confidence,
                structural_resolved_smoothed_prior(
                    structural_prior_state.nodes.get(node_id),
                    structural_prior_state,
                    structural_history_adjusted_node_prior(
                        playbook.node.belief_prior,
                        node_summary,
                    ),
                ),
            ),
            dominant_source_panel,
            dominant_source_share,
            dominant_source_prior,
            duration_streak_count: node_temporal_state
                .map(|state| state.streak_count)
                .or_else(|| structural_duration_streak_count(node_duration_prior)),
            duration_avg_streak_length: structural_duration_avg_streak_length(node_duration_prior),
            duration_persistence_prior: structural_duration_persistence_prior(node_duration_prior),
            duration_weighted_streak_mass: node_temporal_state
                .map(|state| state.weighted_streak_mass)
                .or_else(|| structural_duration_weighted_streak_mass(node_duration_prior)),
            transition_weighted_observation_mass: None,
            duration_outcome_support: node_temporal_state
                .map(|state| state.duration_outcome_support)
                .or_else(|| structural_duration_outcome_support(node_duration_prior)),
            duration_temporal_posterior_support: node_temporal_state
                .map(|state| state.temporal_posterior_support)
                .or_else(|| structural_duration_temporal_posterior_support(node_duration_prior)),
            transition_outcome_support: None,
            transition_temporal_posterior_support: None,
            ..structural_experience_prior_runtime_metrics(node_prior_stats, None)
        }),
        branch,
        scenario,
        path,
    }
}

pub fn build_structural_temporal_summary_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralTemporalSummaryArtifact {
    let node = build_structural_node_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        structural_prior_state,
    );
    let node_duration_prior = structural_prior_state
        .node_duration_priors
        .get(&node.node_id);
    let node_temporal_state = structural_prior_state
        .node_temporal_posteriors
        .get(&node.node_id);
    let active_regime = structural_active_regime(snapshot);
    let to_branch_id = active_regime.as_ref().map(|regime| {
        format!(
            "{}:{}",
            node.node_id,
            structural_branch_label_for_regime(regime)
        )
    });
    let latest_feedback = structural_latest_feedback_refs(snapshot);
    let branch_temporal_state = latest_feedback.as_ref().and_then(|refs| {
        to_branch_id.as_ref().and_then(|branch_id| {
            structural_prior_state
                .branch_temporal_posteriors
                .get(&format!("{}=>{}", refs.branch_id, branch_id))
        })
    });
    let node_transition_state = latest_feedback.as_ref().and_then(|refs| {
        structural_prior_state
            .node_transition_posteriors
            .get(&format!("{}=>{}", refs.node_id, node.node_id))
    });
    let transition_prior = latest_feedback.as_ref().and_then(|refs| {
        to_branch_id.as_ref().and_then(|branch_id| {
            structural_branch_transition_prior(structural_prior_state, &refs.branch_id, branch_id)
        })
    });
    build_structural_temporal_summary_artifact(StructuralTemporalSummaryArtifactInput {
        symbol: structural_symbol(snapshot),
        node_id: node.node_id,
        from_branch_id: latest_feedback.as_ref().map(|refs| refs.branch_id.clone()),
        to_branch_id,
        node_duration_prior,
        node_temporal_state,
        branch_temporal_state,
        node_transition_state,
        transition_prior,
    })
}

pub fn build_structural_top_path_candidates_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> StructuralTopPathCandidatesArtifact {
    let structural_prior_state = StructuralPriorLearningState::default();
    let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    );
    let candidate_paths = selection.candidate_paths;
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = selection.candidate_set_id;
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let candidate_count = candidate_paths.len();
    let candidates = candidate_paths
        .into_iter()
        .enumerate()
        .map(|(index, path)| {
            let behavior_policy_probability = structural_candidate_policy_probability(
                path.composite_preference_score,
                denominator,
                candidate_count,
            );
            StructuralTopPathCandidate {
                rank: index + 1,
                candidate_set_id: candidate_set_id.clone(),
                behavior_policy_probability,
                path_id: path.path_id,
                scenario_id: path.scenario_id,
                path_label: path.path_label,
                direction: path.direction,
                experience_prior: path.path_prior,
                current_posterior: path.path_posterior,
                composite_score: path.composite_preference_score,
                historical_total_records: path.historical_total_records,
                historical_followed_count: path.historical_followed_count,
                historical_invalidation_rate: path.historical_invalidation_rate,
                path_ranker_raw_score: path.catboost_score,
                path_ranker_calibrated_path_prob: path.path_ranker_calibrated_path_prob,
                path_ranker_path_prob_lower_bound: path.path_ranker_path_prob_lower_bound,
                path_ranker_execution_gate_status: path.path_ranker_execution_gate_status,
                path_ranker_runtime_source: path.path_ranker_runtime_source,
                recommended_command: path.recommended_command,
            }
        })
        .collect::<Vec<_>>();
    StructuralTopPathCandidatesArtifact {
        symbol,
        candidate_set_id,
        candidate_count,
        path_ranker_runtime: None,
        candidates,
    }
}

pub fn build_structural_top_path_candidates_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralTopPathCandidatesArtifact {
    build_structural_top_path_candidates_artifact_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    )
}

pub(crate) fn build_structural_top_path_candidates_artifact_with_runtime_context_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    runtime_context: StructuralPathRankerRuntimeContext<'_>,
) -> StructuralTopPathCandidatesArtifact {
    let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        runtime_context,
    );
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = selection.candidate_set_id;
    let candidate_paths = selection.candidate_paths;
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let candidate_count = candidate_paths.len();
    let candidates = candidate_paths
        .into_iter()
        .enumerate()
        .map(|(index, path)| {
            let behavior_policy_probability = structural_candidate_policy_probability(
                path.composite_preference_score,
                denominator,
                candidate_count,
            );
            StructuralTopPathCandidate {
                rank: index + 1,
                candidate_set_id: candidate_set_id.clone(),
                behavior_policy_probability,
                path_id: path.path_id,
                scenario_id: path.scenario_id,
                path_label: path.path_label,
                direction: path.direction,
                experience_prior: path.path_prior,
                current_posterior: path.path_posterior,
                composite_score: path.composite_preference_score,
                historical_total_records: path.historical_total_records,
                historical_followed_count: path.historical_followed_count,
                historical_invalidation_rate: path.historical_invalidation_rate,
                path_ranker_raw_score: path.catboost_score,
                path_ranker_calibrated_path_prob: path.path_ranker_calibrated_path_prob,
                path_ranker_path_prob_lower_bound: path.path_ranker_path_prob_lower_bound,
                path_ranker_execution_gate_status: path.path_ranker_execution_gate_status,
                path_ranker_runtime_source: path.path_ranker_runtime_source,
                recommended_command: path.recommended_command,
            }
        })
        .collect::<Vec<_>>();
    StructuralTopPathCandidatesArtifact {
        symbol,
        candidate_set_id,
        candidate_count,
        path_ranker_runtime: selection.runtime.clone(),
        candidates,
    }
}

pub fn build_structural_path_ranking_target_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> StructuralPathRankingTargetArtifact {
    build_structural_path_ranking_target_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_path_ranking_target_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralPathRankingTargetArtifact {
    build_structural_path_ranking_target_artifact_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    )
}

fn structural_path_ranking_target_artifact_from_candidates(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    candidate_paths: Vec<StructuralPathArtifact>,
    candidate_set_id: Option<String>,
) -> StructuralPathRankingTargetArtifact {
    let symbol = structural_symbol(snapshot);
    let candidate_set_id =
        candidate_set_id.unwrap_or_else(|| structural_candidate_set_id(&symbol, &candidate_paths));
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let candidate_set_size = candidate_paths.len();
    let regime_aux_context = StructuralRegimeAuxContext::from_snapshot(snapshot);
    let rows = candidate_paths
        .into_iter()
        .enumerate()
        .map(|(index, path)| {
            let regime_calibration_bucket =
                structural_path_ranking_regime_bucket_for_path(snapshot, &path.path_id);
            let behavior_policy_probability = structural_candidate_policy_probability(
                path.composite_preference_score,
                denominator,
                candidate_set_size,
            );
            let pending_reward_state =
                structural_path_ranking_pending_reward_state(&path.path_id, feedback_history);
            let calibrated_label = structural_path_ranking_reward_label(&pending_reward_state);
            let maturity_mask = calibrated_label.is_some();
            let maturity_weight = if maturity_mask { 1.0 } else { 0.0 };
            let propensity_estimate = structural_path_ranking_propensity_estimate(
                path.execution_propensity,
                behavior_policy_probability,
            );
            let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
            let training_weight = structural_path_ranking_training_weight(
                calibrated_label,
                maturity_weight,
                ips_weight,
            );
            let prior_stats = structural_prior_state.paths.get(&path.path_id);
            let mut row = StructuralPathRankingTargetRow {
                rank: index + 1,
                candidate_set_id: candidate_set_id.clone(),
                candidate_set_size,
                path_id: path.path_id.clone(),
                scenario_id: path.scenario_id,
                path_label: path.path_label,
                regime_profit_branch_path: None,
                parent_regime_root: None,
                main_regime: None,
                sub_regime: None,
                sub_sub_regime_or_profit_factor: None,
                profit_factor: None,
                direction: path.direction,
                raw_path_score: path.catboost_score,
                calibrated_path_prob: None,
                path_prob_lower_bound: None,
                execution_gate_status: None,
                execution_gate_min_path_prob: None,
                execution_gate_reason: None,
                pending_reward_state,
                maturity_mask,
                maturity_weight,
                calibrated_label,
                propensity_estimate,
                ips_weight,
                training_weight,
                regime_calibration_bucket,
                behavior_policy_probability,
                execution_propensity: path.execution_propensity,
                target_policy_probability_confidence:
                    structural_prior_target_policy_probability_confidence(prior_stats),
                target_policy_probability_lower_bound:
                    structural_prior_target_policy_probability_lower_bound(prior_stats),
                target_policy_reward_prior: structural_prior_target_policy_reward_prior(
                    prior_stats,
                ),
                target_policy_reward_lower_bound: structural_prior_target_policy_reward_lower_bound(
                    prior_stats,
                ),
                experience_prior: path.path_prior,
                current_posterior: path.path_posterior,
                structural_baseline_score: path.composite_preference_score,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: None,
                score_source_kind: None,
                score_model_artifact_uri: None,
                score_generator: None,
            };
            structural_populate_regime_profit_branch_fields(&mut row);
            regime_aux_context.apply_to_row(&mut row);
            structural_apply_order_block_variant_context(snapshot, &mut row);
            structural_apply_reference_liquidity_levels_context(snapshot, &mut row);
            row
        })
        .collect::<Vec<_>>();
    let mut artifact = StructuralPathRankingTargetArtifact {
        protocol_version: "structural-path-ranking-target-v1".to_string(),
        symbol,
        candidate_set_id,
        candidate_set_size,
        generated_at: snapshot
            .generated_at
            .to_rfc3339_opts(SecondsFormat::Secs, true),
        rows,
    };
    apply_structural_path_probability_calibration(&mut artifact);
    artifact
}

fn structural_apply_order_block_variant_context(
    snapshot: &WorkflowSnapshot,
    row: &mut StructuralPathRankingTargetRow,
) {
    let Some(evidence) = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.order_block_variant.as_ref())
    else {
        return;
    };
    row.ob_variant = Some(evidence.variant.clone());
    row.ob_direction = Some(format!("{:?}", evidence.direction));
    row.ob_validation_state = Some(evidence.validation_state.clone());
    row.ob_high = evidence.high;
    row.ob_low = evidence.low;
    row.ob_midpoint = evidence.midpoint;
    row.ob_mitigation_count = Some(evidence.mitigation_count as f64);
    row.ob_breaker_confirmed = Some(if evidence.breaker_confirmed { 1.0 } else { 0.0 });
    row.ob_rejection_confirmed = Some(if evidence.rejection_confirmed {
        1.0
    } else {
        0.0
    });
    row.ob_confidence = Some(evidence.confidence);
    row.ob_fail_closed_reason = evidence.fail_closed_reason.clone();
    let branch_path =
        "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1";
    if evidence.factor_name == "order_block_variant_classifier"
        && (row.path_id == branch_path
            || row.regime_profit_branch_path.as_deref() == Some(branch_path))
    {
        row.regime_profit_branch_path = Some(branch_path.to_string());
        row.parent_regime_root = Some("Transition".to_string());
        row.main_regime = Some("Transition".to_string());
        row.sub_regime = Some("OrderBlockVariant".to_string());
        row.sub_sub_regime_or_profit_factor = Some("ob_mitigation_breaker_rejection".to_string());
        row.profit_factor = Some("order_block_variant_classifier_v1".to_string());
    }
}

fn structural_apply_reference_liquidity_levels_context(
    snapshot: &WorkflowSnapshot,
    row: &mut StructuralPathRankingTargetRow,
) {
    let Some(evidence) = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.reference_liquidity_levels.as_ref())
    else {
        return;
    };
    row.ref_previous_day_high = evidence.previous_day_high;
    row.ref_previous_day_low = evidence.previous_day_low;
    row.ref_previous_day_close = evidence.previous_day_close;
    row.ref_current_day_open = evidence.current_day_open;
    row.ref_previous_week_high = evidence.previous_week_high;
    row.ref_previous_week_low = evidence.previous_week_low;
    row.ref_previous_week_close = evidence.previous_week_close;
    row.ref_current_week_open = evidence.current_week_open;
    row.ref_previous_month_high = evidence.previous_month_high;
    row.ref_previous_month_low = evidence.previous_month_low;
    row.ref_current_day_gap_upper = evidence.current_day_gap.as_ref().and_then(|gap| gap.upper);
    row.ref_current_day_gap_lower = evidence.current_day_gap.as_ref().and_then(|gap| gap.lower);
    row.ref_current_week_gap_upper = evidence.current_week_gap.as_ref().and_then(|gap| gap.upper);
    row.ref_current_week_gap_lower = evidence.current_week_gap.as_ref().and_then(|gap| gap.lower);
    row.ref_recent_week_gap_levels = if evidence.recent_week_open_gaps.is_empty() {
        None
    } else {
        serde_json::to_string(&evidence.recent_week_open_gaps).ok()
    };
}

fn structural_path_ranking_pending_reward_state_from_feedback(
    record: &FeedbackRecord,
    refs: &StructuralFeedbackRefs,
) -> Option<String> {
    if structural_feedback_outcome_is_unresolved(&record.realized_outcome) {
        return None;
    }
    if crate::state::structural_feedback_is_infrastructure_negative(record) {
        return None;
    }
    if !refs.followed_path
        || record
            .realized_outcome
            .trim()
            .eq_ignore_ascii_case("not_followed")
    {
        return None;
    }
    if record
        .realized_outcome
        .trim()
        .eq_ignore_ascii_case("invalidated")
    {
        return Some("matured_invalidated".to_string());
    }
    match structural_feedback_learning_outcome(record) {
        Some(StructuralFeedbackLearningOutcome::Positive) => Some("matured_success".to_string()),
        Some(StructuralFeedbackLearningOutcome::Neutral)
        | Some(StructuralFeedbackLearningOutcome::Negative) => Some("matured_failure".to_string()),
        None => None,
    }
}

fn structural_feedback_runtime_candidate_set_id(
    symbol: &str,
    refs: &StructuralFeedbackRefs,
) -> String {
    let prefix = format!("structural-feedback:{symbol}:");
    if let Some(rest) = refs.recommendation_id.strip_prefix(&prefix) {
        if let Some((candidate_set_id, _)) = rest.split_once(":path:") {
            let candidate_set_id = candidate_set_id.trim();
            if !candidate_set_id.is_empty() {
                return candidate_set_id.to_string();
            }
        }
    }
    format!(
        "structural-feedback-history:{symbol}:{:016x}",
        structural_stable_hash64(&refs.path_id)
    )
}

fn structural_feedback_direction_label(direction: Direction) -> &'static str {
    match direction {
        Direction::Bull => "bull",
        Direction::Bear => "bear",
        Direction::Neutral => "neutral",
    }
}

fn structural_feedback_regime_bucket(symbol: &str, regime: Regime, path_id: &str) -> String {
    let regime = match regime {
        Regime::Accumulation => "accumulation",
        Regime::ManipulationExpansion => "manipulation_expansion",
        Regime::Distribution => "distribution",
    };
    format!("{symbol}:{regime}:{path_id}")
}

fn structural_path_ranking_feedback_target_rows(
    symbol: &str,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Vec<StructuralPathRankingTargetRow> {
    feedback_history
        .iter()
        .enumerate()
        .filter_map(|(index, record)| {
            if record.symbol.trim() != symbol {
                return None;
            }
            let refs = record.structural_feedback.as_ref()?;
            let pending_reward_state =
                structural_path_ranking_pending_reward_state_from_feedback(record, refs)?;
            let selected_probability = record
                .model_probabilities_before_trade
                .selected_probability
                .clamp(0.0, 1.0);
            let prior_stats = structural_prior_state.paths.get(&refs.path_id);
            let neutral_behavior_probability =
                structural_prior_target_policy_reward_prior(prior_stats)
                    .or_else(|| prior_stats.map(|stats| stats.smoothed_prior.clamp(0.0, 1.0)))
                    .unwrap_or(0.5);
            let raw_path_score = if selected_probability > f64::EPSILON {
                selected_probability
            } else {
                neutral_behavior_probability
            };
            let calibrated_label = structural_path_ranking_reward_label(&pending_reward_state)?;
            let behavior_policy_probability = raw_path_score.clamp(0.01, 1.0);
            let execution_propensity = Some(1.0);
            let propensity_estimate = structural_path_ranking_propensity_estimate(
                execution_propensity,
                behavior_policy_probability,
            );
            let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
            let maturity_weight = 1.0;
            let training_weight = structural_path_ranking_training_weight(
                Some(calibrated_label),
                maturity_weight,
                ips_weight,
            );
            let experience_prior = prior_stats
                .map(|stats| stats.smoothed_prior.clamp(0.0, 1.0))
                .unwrap_or(behavior_policy_probability);
            let current_posterior = structural_prior_target_policy_reward_prior(prior_stats)
                .unwrap_or(behavior_policy_probability);
            let mut row = StructuralPathRankingTargetRow {
                rank: index + 1,
                candidate_set_id: structural_feedback_runtime_candidate_set_id(symbol, refs),
                candidate_set_size: 1,
                path_id: refs.path_id.clone(),
                scenario_id: refs.scenario_id.clone(),
                path_label: refs.path_id.clone(),
                regime_profit_branch_path: None,
                parent_regime_root: None,
                main_regime: None,
                sub_regime: None,
                sub_sub_regime_or_profit_factor: None,
                profit_factor: None,
                direction: structural_feedback_direction_label(
                    record.model_probabilities_before_trade.selected_direction,
                )
                .to_string(),
                raw_path_score: Some(raw_path_score),
                calibrated_path_prob: None,
                path_prob_lower_bound: None,
                execution_gate_status: None,
                execution_gate_min_path_prob: None,
                execution_gate_reason: None,
                pending_reward_state,
                maturity_mask: true,
                maturity_weight,
                calibrated_label: Some(calibrated_label),
                propensity_estimate,
                ips_weight,
                training_weight,
                regime_calibration_bucket: structural_feedback_regime_bucket(
                    symbol,
                    record.regime_at_entry,
                    &refs.path_id,
                ),
                behavior_policy_probability,
                execution_propensity,
                target_policy_probability_confidence:
                    structural_prior_target_policy_probability_confidence(prior_stats),
                target_policy_probability_lower_bound:
                    structural_prior_target_policy_probability_lower_bound(prior_stats),
                target_policy_reward_prior: structural_prior_target_policy_reward_prior(
                    prior_stats,
                ),
                target_policy_reward_lower_bound: structural_prior_target_policy_reward_lower_bound(
                    prior_stats,
                ),
                experience_prior,
                current_posterior,
                structural_baseline_score: behavior_policy_probability,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: None,
                score_source_kind: None,
                score_model_artifact_uri: None,
                score_generator: None,
            };
            structural_populate_regime_profit_branch_fields(&mut row);
            Some(row)
        })
        .collect()
}

#[derive(Debug, Clone)]
struct StructuralFeedbackAggregateStats {
    refs: StructuralFeedbackRefs,
    direction: Direction,
    count: usize,
    accepted_execution_feedback_count: usize,
    accepted_execution_feedback_kind: Option<&'static str>,
    pnl_sum: f64,
    gross_profit: f64,
    gross_loss_abs: f64,
    probability_sum: f64,
}

impl StructuralFeedbackAggregateStats {
    fn push(&mut self, record: &FeedbackRecord) {
        self.count += 1;
        if let Some(kind) = structural_feedback_execution_feedback_kind(&record.source) {
            self.accepted_execution_feedback_count += 1;
            self.accepted_execution_feedback_kind = match self.accepted_execution_feedback_kind {
                None => Some(kind),
                Some(existing) if existing == kind => Some(existing),
                Some(_) => Some("mixed_execution_feedback"),
            };
        }
        self.pnl_sum += record.pnl;
        if record.pnl > 0.0 {
            self.gross_profit += record.pnl;
        } else if record.pnl < 0.0 {
            self.gross_loss_abs += record.pnl.abs();
        }
        self.probability_sum += record
            .model_probabilities_before_trade
            .selected_probability
            .clamp(0.0, 1.0);
    }

    fn profit_factor_score(&self) -> f64 {
        if self.gross_profit <= f64::EPSILON && self.gross_loss_abs <= f64::EPSILON {
            return 0.5;
        }
        if self.gross_loss_abs <= f64::EPSILON {
            return 0.95;
        }
        let profit_factor = (self.gross_profit / self.gross_loss_abs).clamp(0.0, 20.0);
        (profit_factor / (1.0 + profit_factor)).clamp(0.01, 0.99)
    }

    fn average_probability(&self) -> f64 {
        if self.count == 0 {
            return 0.5;
        }
        (self.probability_sum / self.count as f64).clamp(0.01, 1.0)
    }

    fn live_trade_usable_source_kind(&self) -> Option<&'static str> {
        if self.count >= 30
            && self.accepted_execution_feedback_count == self.count
            && self.pnl_sum > 0.0
        {
            return self.accepted_execution_feedback_kind;
        }
        None
    }
}

fn structural_feedback_execution_feedback_kind(source: &str) -> Option<&'static str> {
    let text = source.trim().to_ascii_lowercase();
    if text.is_empty()
        || text.contains("simulated")
        || text.contains("simulation")
        || text.contains("retained_real_event_label")
    {
        return None;
    }
    [
        "paper_execution_feedback",
        "live_execution_feedback",
        "paper_trade_feedback",
        "live_trade_feedback",
        "broker_execution_feedback",
    ]
    .into_iter()
    .find(|marker| source_marker_has_accepted_execution_feedback(&text, marker))
}

fn source_marker_tokens(text: &str) -> Vec<&str> {
    text.split(|ch: char| !(ch.is_ascii_alphanumeric() || ch == '_'))
        .filter(|token| !token.is_empty())
        .collect()
}

fn source_marker_has_accepted_execution_feedback(text: &str, marker: &str) -> bool {
    let tokens = source_marker_tokens(text);
    tokens.iter().enumerate().any(|(index, token)| {
        token == &marker
            && !tokens[index.saturating_sub(3)..index]
                .iter()
                .any(|previous| {
                    matches!(
                        *previous,
                        "not"
                            | "no"
                            | "non"
                            | "without"
                            | "missing"
                            | "absent"
                            | "fake"
                            | "spoofed"
                    )
                })
    })
}

fn structural_path_ranking_apply_execution_feedback_lifecycle_gates(
    rows: &mut [StructuralPathRankingTargetRow],
) {
    for row in rows {
        let accepted_kind = row
            .score_source_kind
            .as_deref()
            .and_then(structural_feedback_execution_feedback_kind);
        let Some(kind) = accepted_kind else {
            continue;
        };
        if row.pending_reward_state != "matured_success"
            || !row.maturity_mask
            || !row.calibrated_label.is_some_and(|label| label > 0.0)
            || !row.training_weight.is_some_and(|weight| weight > 0.0)
        {
            continue;
        }
        row.execution_gate_status = Some("live_trade_usable".to_string());
        row.execution_gate_reason = Some(format!(
            "accepted_execution_feedback_source={kind} pending_reward_state=matured_success training_weight={:.6}",
            row.training_weight.unwrap_or_default()
        ));
    }
}

fn structural_path_ranking_feedback_aggregate_target_rows(
    symbol: &str,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Vec<StructuralPathRankingTargetRow> {
    let mut aggregate_by_path = BTreeMap::<String, StructuralFeedbackAggregateStats>::new();
    for record in feedback_history {
        if record.symbol.trim() != symbol {
            continue;
        }
        if crate::state::structural_feedback_is_infrastructure_negative(record) {
            continue;
        }
        let Some(refs) = record.structural_feedback.as_ref() else {
            continue;
        };
        if structural_path_ranking_pending_reward_state_from_feedback(record, refs).is_none() {
            continue;
        }
        aggregate_by_path
            .entry(refs.path_id.clone())
            .and_modify(|stats| stats.push(record))
            .or_insert_with(|| {
                let mut stats = StructuralFeedbackAggregateStats {
                    refs: refs.clone(),
                    direction: record.model_probabilities_before_trade.selected_direction,
                    count: 0,
                    accepted_execution_feedback_count: 0,
                    accepted_execution_feedback_kind: None,
                    pnl_sum: 0.0,
                    gross_profit: 0.0,
                    gross_loss_abs: 0.0,
                    probability_sum: 0.0,
                };
                stats.push(record);
                stats
            });
    }

    aggregate_by_path
        .into_iter()
        .filter(|(_, stats)| stats.count >= 30)
        .enumerate()
        .map(|(index, (path_id, stats))| {
            let pending_reward_state = if stats.pnl_sum > 0.0 {
                "matured_success"
            } else {
                "matured_failure"
            };
            let live_trade_usable_source_kind = stats.live_trade_usable_source_kind();
            let calibrated_label = structural_path_ranking_reward_label(pending_reward_state);
            let raw_path_score = stats.profit_factor_score();
            let behavior_policy_probability = stats.average_probability();
            let prior_stats = structural_prior_state.paths.get(&path_id);
            let propensity_estimate = structural_path_ranking_propensity_estimate(
                Some(behavior_policy_probability),
                behavior_policy_probability,
            );
            let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
            let maturity_weight = 1.0;
            let training_weight = structural_path_ranking_training_weight(
                calibrated_label,
                maturity_weight,
                ips_weight,
            );
            let experience_prior = prior_stats
                .map(|prior| prior.smoothed_prior.clamp(0.0, 1.0))
                .unwrap_or(raw_path_score);
            let current_posterior =
                structural_prior_target_policy_reward_prior(prior_stats).unwrap_or(raw_path_score);
            let mut row = StructuralPathRankingTargetRow {
                rank: index + 1,
                candidate_set_id: format!(
                    "structural-feedback-aggregate:{symbol}:{:016x}",
                    structural_stable_hash64(&path_id)
                ),
                candidate_set_size: 1,
                path_id: path_id.clone(),
                scenario_id: format!(
                    "structural-feedback-aggregate:{:016x}",
                    structural_stable_hash64(&format!("{symbol}|{path_id}|{}", stats.count))
                ),
                path_label: format!("aggregate_feedback:{path_id}"),
                regime_profit_branch_path: Some(path_id.clone())
                    .filter(|path| path.contains(" -> ")),
                parent_regime_root: None,
                main_regime: None,
                sub_regime: None,
                sub_sub_regime_or_profit_factor: None,
                profit_factor: None,
                direction: structural_feedback_direction_label(stats.direction).to_string(),
                raw_path_score: Some(raw_path_score),
                calibrated_path_prob: Some(raw_path_score),
                path_prob_lower_bound: None,
                execution_gate_status: None,
                execution_gate_min_path_prob: None,
                execution_gate_reason: None,
                pending_reward_state: pending_reward_state.to_string(),
                maturity_mask: true,
                maturity_weight,
                calibrated_label,
                propensity_estimate,
                ips_weight,
                training_weight,
                regime_calibration_bucket: structural_feedback_regime_bucket(
                    symbol,
                    Regime::ManipulationExpansion,
                    &path_id,
                ),
                behavior_policy_probability,
                execution_propensity: Some(behavior_policy_probability),
                target_policy_probability_confidence:
                    structural_prior_target_policy_probability_confidence(prior_stats),
                target_policy_probability_lower_bound:
                    structural_prior_target_policy_probability_lower_bound(prior_stats),
                target_policy_reward_prior: structural_prior_target_policy_reward_prior(
                    prior_stats,
                ),
                target_policy_reward_lower_bound: structural_prior_target_policy_reward_lower_bound(
                    prior_stats,
                ),
                experience_prior,
                current_posterior,
                structural_baseline_score: raw_path_score,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: None,
                score_source_kind: live_trade_usable_source_kind.map(str::to_string),
                score_model_artifact_uri: None,
                score_generator: live_trade_usable_source_kind.map(|kind| {
                    format!(
                        "accepted_execution_feedback_aggregate:{kind}:count={}",
                        stats.count
                    )
                }),
            };
            row.parent_regime_root = Some(stats.refs.node_id.clone());
            structural_populate_regime_profit_branch_fields(&mut row);
            row
        })
        .collect()
}

fn structural_path_ranking_current_feedback_target_rows(
    feedback_target_rows: &[StructuralPathRankingTargetRow],
    current_rows: &[StructuralPathRankingTargetRow],
) -> Vec<StructuralPathRankingTargetRow> {
    let mut by_path = BTreeMap::new();
    for row in feedback_target_rows {
        if current_rows.iter().any(|current| {
            current.candidate_set_id == row.candidate_set_id && current.path_id == row.path_id
        }) {
            continue;
        }
        by_path
            .entry(row.path_id.clone())
            .and_modify(|existing: &mut StructuralPathRankingTargetRow| {
                if row.raw_path_score.unwrap_or(0.0) >= existing.raw_path_score.unwrap_or(0.0) {
                    *existing = row.clone();
                }
            })
            .or_insert_with(|| row.clone());
    }
    by_path
        .into_values()
        .enumerate()
        .map(|(index, mut row)| {
            row.rank = current_rows.len() + index + 1;
            row
        })
        .collect()
}

fn structural_path_ranking_carry_forward_score_metadata(
    row: &mut StructuralPathRankingTargetRow,
    existing_history_score_map: &BTreeMap<String, StructuralPathRankingTargetRow>,
) {
    if let Some(scored_row) =
        existing_history_score_map.get(&structural_path_ranking_target_row_score_key(row))
    {
        row.raw_path_score = scored_row.raw_path_score;
        row.score_model_family = scored_row.score_model_family.clone();
        row.score_source_kind = scored_row.score_source_kind.clone();
        row.score_model_artifact_uri = scored_row.score_model_artifact_uri.clone();
        row.score_generator = scored_row.score_generator.clone();
        clear_structural_path_ranking_target_row_outputs(row);
    }
}

fn structural_runtime_context_prefers_history(
    runtime_context: &StructuralPathRankerRuntimeContext<'_>,
    symbol: &str,
) -> bool {
    runtime_context
        .state_dir
        .and_then(|state_dir| load_structural_path_ranking_runtime_selection(state_dir, symbol))
        .is_some_and(|selection| {
            selection.enabled
                && selection.reuse_mode == STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY
        })
}

fn structural_exact_feedback_path_priority(path: &StructuralPathArtifact) -> u8 {
    let exact_branch_shape = !path.path_id.starts_with("path:") && path.path_id.contains(" -> ");
    if exact_branch_shape
        || path.entry_style == "structural_feedback_path"
        || path.entry_style == "regime_bundle_branch_path"
    {
        0
    } else {
        1
    }
}

fn structural_path_plan_order(
    left: &StructuralPathArtifact,
    right: &StructuralPathArtifact,
    prefer_history_runtime: bool,
) -> std::cmp::Ordering {
    let history_order = if prefer_history_runtime {
        structural_exact_feedback_path_priority(left)
            .cmp(&structural_exact_feedback_path_priority(right))
    } else {
        std::cmp::Ordering::Equal
    };
    history_order
        .then_with(|| {
            right
                .composite_preference_score
                .total_cmp(&left.composite_preference_score)
        })
        .then_with(|| right.path_posterior.total_cmp(&left.path_posterior))
        .then_with(|| right.path_prior.total_cmp(&left.path_prior))
}

fn structural_populate_regime_profit_branch_fields(row: &mut StructuralPathRankingTargetRow) {
    let segments = row
        .path_id
        .split(" -> ")
        .map(str::trim)
        .filter(|segment| !segment.is_empty())
        .collect::<Vec<_>>();
    if segments.len() < 4 {
        return;
    }
    row.regime_profit_branch_path = Some(row.path_id.clone());
    row.parent_regime_root = Some(segments[0].to_string());
    row.main_regime = Some(segments[0].to_string());
    row.sub_regime = Some(segments[1].to_string());
    row.sub_sub_regime_or_profit_factor = Some(segments[2].to_string());
    row.profit_factor = Some(segments[3..].join(" -> "));
}

fn structural_regime_bundle_branch_paths(snapshot: &WorkflowSnapshot) -> Vec<String> {
    let Some(assignments) = snapshot
        .latest_analyze
        .as_ref()
        .map(|phase| &phase.pre_bayes_filtered_assignments)
    else {
        return Vec::new();
    };
    let mut paths = Vec::new();
    if let Some(raw_paths) = assignments.get("regime_bundle_branch_paths_json") {
        if let Ok(parsed_paths) = serde_json::from_str::<Vec<String>>(raw_paths) {
            paths.extend(parsed_paths);
        }
    }
    for key in [
        "regime_profit_branch_path",
        "regime_bundle_branch_path",
        "regime_refinement_branch_path",
        "selected_regime_profit_branch_path",
        "read_only_regime_bbn_label_set",
        "regime_bbn_label_set",
    ] {
        if let Some(raw) = assignments.get(key) {
            paths.extend(raw.split(',').map(str::to_string));
        }
    }
    if let Some(path) = structural_order_block_variant_runtime_branch_path(snapshot) {
        paths.push(path);
    }
    if let Some(path) = structural_liquidity_pool_texture_runtime_branch_path(snapshot) {
        paths.push(path);
    }
    let mut seen = BTreeSet::new();
    paths
        .into_iter()
        .map(|path| {
            path.trim()
                .replace("_->_", " -> ")
                .replace("->", " -> ")
                .split_whitespace()
                .collect::<Vec<_>>()
                .join(" ")
        })
        .filter(|path| path.contains(" -> ") && seen.insert(path.clone()))
        .collect()
}

fn structural_order_block_variant_runtime_branch_path(
    snapshot: &WorkflowSnapshot,
) -> Option<String> {
    let evidence = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.order_block_variant.as_ref())?;
    if evidence.confidence <= 0.0
        || evidence.validation_state.trim().is_empty()
        || evidence.validation_state == "fail_closed"
        || evidence.fail_closed_reason.is_some()
    {
        return None;
    }
    let factor_name = evidence.factor_name.trim();
    if factor_name != "order_block_variant_classifier" {
        return None;
    }
    Some(
        "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
            .to_string(),
    )
}

fn structural_liquidity_pool_texture_runtime_branch_path(
    snapshot: &WorkflowSnapshot,
) -> Option<String> {
    let evidence = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.liquidity_pool_texture.as_ref())?;
    if evidence.confidence <= 0.0
        || evidence.texture.trim().is_empty()
        || evidence.texture == "none"
        || evidence.fail_closed_reason.is_some()
    {
        return None;
    }
    let factor_name = evidence.factor_name.trim();
    if factor_name != "liquidity_pool_texture" {
        return None;
    }
    Some(
        "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1"
            .to_string(),
    )
}

fn structural_regime_bundle_branch_score(snapshot: &WorkflowSnapshot) -> f64 {
    let score = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| {
            phase
                .pre_bayes_filtered_assignments
                .get("regime_bundle_stable_profit_score")
                .or_else(|| {
                    phase
                        .pre_bayes_filtered_assignments
                        .get("stable_profit_score")
                })
                .or_else(|| {
                    phase
                        .pre_bayes_filtered_assignments
                        .get("read_only_regime_bbn_soft_evidence_weight")
                })
        })
        .and_then(|value| value.trim().parse::<f64>().ok())
        .map(|value| if value > 1.0 { value / 100.0 } else { value })
        .unwrap_or_else(|| structural_posterior_confidence(snapshot));
    score.clamp(0.0, 1.0)
}

#[derive(Debug, Clone, Default)]
struct StructuralRegimeAuxContext {
    qqq_hv_level: Option<f64>,
    nq_vs_200d_pct: Option<f64>,
    vix3m_level: Option<f64>,
    qqq_hv_pct_rank_252: Option<f64>,
    vvix_over_vix: Option<f64>,
}

impl StructuralRegimeAuxContext {
    fn from_snapshot(snapshot: &WorkflowSnapshot) -> Self {
        let Some(assignments) = snapshot
            .latest_analyze
            .as_ref()
            .map(|phase| &phase.pre_bayes_filtered_assignments)
        else {
            return Self::default();
        };
        Self {
            qqq_hv_level: structural_assignment_f64(assignments, "regime_aux_qqq_hv_level"),
            nq_vs_200d_pct: structural_assignment_f64(assignments, "regime_aux_nq_vs_200d_pct"),
            vix3m_level: structural_assignment_f64(assignments, "regime_aux_vix3m_level"),
            qqq_hv_pct_rank_252: structural_assignment_f64(
                assignments,
                "regime_aux_qqq_hv_pct_rank_252",
            ),
            vvix_over_vix: structural_assignment_f64(assignments, "regime_aux_vvix_over_vix"),
        }
    }

    fn apply_to_row(&self, row: &mut StructuralPathRankingTargetRow) {
        row.regime_aux_qqq_hv_level = self.qqq_hv_level;
        row.regime_aux_nq_vs_200d_pct = self.nq_vs_200d_pct;
        row.regime_aux_vix3m_level = self.vix3m_level;
        row.regime_aux_qqq_hv_pct_rank_252 = self.qqq_hv_pct_rank_252;
        row.regime_aux_vvix_over_vix = self.vvix_over_vix;
    }
}

fn structural_assignment_f64(assignments: &BTreeMap<String, String>, key: &str) -> Option<f64> {
    assignments
        .get(key)
        .and_then(|value| value.trim().parse::<f64>().ok())
}

fn structural_regime_bundle_branch_path_candidates(
    snapshot: &WorkflowSnapshot,
    structural_prior_state: &StructuralPriorLearningState,
) -> Vec<StructuralPathArtifact> {
    let branch_paths = structural_regime_bundle_branch_paths(snapshot);
    if branch_paths.is_empty() {
        return Vec::new();
    }
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    let selected_entry_quality = structural_selected_entry_quality(snapshot);
    let selected_entry_quality_probability =
        structural_selected_entry_quality_probability(snapshot);
    let pre_bayes_gate_status = structural_pre_bayes_gate_status(snapshot);
    let multi_timeframe_direction_bias = structural_multi_timeframe_direction_bias(snapshot);
    let execution_candidate_status = snapshot
        .latest_execution_candidate
        .as_ref()
        .map(|candidate| candidate.candidate_status.clone())
        .filter(|value| !value.trim().is_empty());
    let execution_candidate_artifact_id = snapshot
        .latest_execution_candidate
        .as_ref()
        .map(|candidate| candidate.artifact_id.clone());
    let score = structural_regime_bundle_branch_score(snapshot);

    branch_paths
        .into_iter()
        .map(|path_id| {
            let prior_stats = structural_prior_state.paths.get(&path_id);
            let resolved_prior =
                structural_resolved_smoothed_prior(prior_stats, structural_prior_state, score);
            let path_posterior =
                structural_prior_target_policy_reward_prior(prior_stats).unwrap_or(score);
            let composite_preference_score =
                structural_composite_preference_score(path_posterior, resolved_prior);
            let scenario_id = format!(
                "regime-bundle-branch:{:016x}",
                structural_stable_hash64(&path_id)
            );
            StructuralPathArtifact {
                path_id: path_id.clone(),
                scenario_id,
                path_label: path_id.clone(),
                direction: structural_feedback_path_direction_label(&path_id, None, snapshot),
                entry_style: "regime_bundle_branch_path".to_string(),
                selected_entry_quality: selected_entry_quality.clone(),
                selected_entry_quality_probability,
                pre_bayes_gate_status: pre_bayes_gate_status.clone(),
                multi_timeframe_direction_bias: multi_timeframe_direction_bias.clone(),
                execution_candidate_status: execution_candidate_status.clone(),
                execution_candidate_artifact_id: execution_candidate_artifact_id.clone(),
                execution_readiness: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_readiness),
                prediction_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.prediction_edge_share),
                execution_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_edge_share),
                historical_total_records: structural_resolved_observations(prior_stats, 0),
                historical_followed_count: structural_resolved_followed_count(prior_stats, 0),
                execution_propensity: structural_prior_execution_propensity(prior_stats)
                    .or(Some(1.0)),
                historical_win_rate: structural_resolved_path_win_rate(prior_stats, None),
                historical_invalidation_rate: structural_resolved_path_invalidation_rate(
                    prior_stats,
                    None,
                ),
                historical_avg_pnl: structural_resolved_avg_pnl(prior_stats, None),
                trigger_conditions: vec![format!(
                    "preserve exact regime_profit_branch_path {path_id}"
                )],
                confirmation_conditions: vec![
                    "same rooted branch path must reach downstream runtime".to_string(),
                ],
                stop_definition: "use the branch-specific stop contract".to_string(),
                target_definition: format!("regime_bundle_stable_profit_score={score:.6}"),
                invalidation_conditions: vec![
                    "do not collapse this branch into a generic structural runtime path"
                        .to_string(),
                ],
                expected_failure_mode:
                    "regime bundle branch path not consumed by downstream execution surface"
                        .to_string(),
                max_time_in_trade: "use branch horizon from the regime bundle".to_string(),
                path_prior: resolved_prior,
                path_posterior,
                bbn_support_score: path_posterior,
                catboost_score: Some(score),
                path_ranker_calibrated_path_prob: None,
                path_ranker_path_prob_lower_bound: None,
                path_ranker_execution_gate_status: None,
                path_ranker_runtime_source: None,
                composite_preference_score,
                recommended_command: next_meta.executable_command.clone().or_else(|| {
                    if command.trim().is_empty() {
                        None
                    } else {
                        Some(command.clone())
                    }
                }),
            }
        })
        .collect()
}

fn structural_path_ranking_regime_bundle_target_rows(
    snapshot: &WorkflowSnapshot,
    structural_prior_state: &StructuralPriorLearningState,
    candidate_set_id: &str,
    candidate_set_size: usize,
) -> Vec<StructuralPathRankingTargetRow> {
    let candidate_paths =
        structural_regime_bundle_branch_path_candidates(snapshot, structural_prior_state);
    if candidate_paths.is_empty() {
        return Vec::new();
    }
    let mut rows = structural_path_ranking_target_artifact_from_candidates(
        snapshot,
        &[],
        structural_prior_state,
        candidate_paths,
        Some(candidate_set_id.to_string()),
    )
    .rows;
    for row in &mut rows {
        row.candidate_set_size = candidate_set_size;
    }
    rows
}

fn structural_path_ranking_agent_material_rank_target_rows(
    snapshot: &WorkflowSnapshot,
    structural_prior_state: &StructuralPriorLearningState,
    rank_artifact: &AgentMaterialRankArtifact,
) -> Vec<StructuralPathRankingTargetRow> {
    let ranked_branch_rows = rank_artifact
        .ranking
        .iter()
        .enumerate()
        .filter_map(|(source_index, row)| {
            row.regime_profit_branch_path
                .as_ref()
                .or(row.branch_path.as_ref())
                .map(|path| {
                    path.trim()
                        .replace("_->_", " -> ")
                        .replace("->", " -> ")
                        .split_whitespace()
                        .collect::<Vec<_>>()
                        .join(" ")
                })
                .filter(|path| path.contains(" -> "))
                .map(|path| (path, source_index, row))
        })
        .collect::<Vec<_>>();
    let mut branch_counts = BTreeMap::<String, usize>::new();
    let mut branch_has_dense_observation = BTreeMap::<String, bool>::new();
    for (path, _, row) in &ranked_branch_rows {
        *branch_counts.entry(path.clone()).or_default() += 1;
        if structural_agent_material_rank_row_has_dense_observation(row) {
            branch_has_dense_observation.insert(path.clone(), true);
        }
    }
    let mut seen_unobserved = BTreeSet::new();
    let branch_paths = ranked_branch_rows
        .into_iter()
        .filter(|(path, _, row)| {
            let dense_observation = structural_agent_material_rank_row_has_dense_observation(row);
            if dense_observation {
                return true;
            }
            if branch_has_dense_observation
                .get(path)
                .copied()
                .unwrap_or_default()
            {
                return false;
            }
            seen_unobserved.insert(path.clone())
        })
        .collect::<Vec<_>>();
    if branch_paths.is_empty() {
        return Vec::new();
    }
    let mut kept_branch_counts = BTreeMap::<String, usize>::new();
    for (path, _, _) in &branch_paths {
        *kept_branch_counts.entry(path.clone()).or_default() += 1;
    }

    let candidate_set_id = rank_artifact.artifact_id.clone();
    let candidate_set_size = branch_paths.len();
    let denominator = branch_paths
        .iter()
        .map(|(_, _, row)| structural_agent_material_rank_row_score(row).max(0.0))
        .sum::<f64>();
    let regime_aux_context = StructuralRegimeAuxContext::from_snapshot(snapshot);
    branch_paths
        .into_iter()
        .enumerate()
        .map(|(index, (branch_path, source_index, rank_row))| {
            let regime_calibration_bucket =
                structural_path_ranking_regime_bucket_for_path(snapshot, &branch_path);
            let row_score = structural_agent_material_rank_row_score(rank_row);
            let behavior_policy_probability =
                structural_candidate_policy_probability(row_score, denominator, candidate_set_size);
            let completed_rank_row = rank_row.status == "completed";
            let dense_rank_observation =
                completed_rank_row && rank_row.trade_count.unwrap_or(0) >= 30;
            let profit_observation = dense_rank_observation && rank_row.total_profit_pct.is_some();
            let score_observation =
                dense_rank_observation && !profit_observation && rank_row.sharpe.is_some();
            let pending_reward_state = if profit_observation
                && rank_row.total_profit_pct.is_some_and(|value| value > 0.0)
            {
                "matured_success"
            } else if profit_observation {
                "matured_failure"
            } else if score_observation && rank_row.sharpe.is_some_and(|value| value > 0.0) {
                "matured_success"
            } else if score_observation {
                "matured_failure"
            } else {
                "unobserved"
            };
            let calibrated_label = structural_path_ranking_reward_label(pending_reward_state);
            let maturity_mask = calibrated_label.is_some();
            let maturity_weight = if profit_observation {
                1.0
            } else if score_observation {
                0.5
            } else {
                0.0
            };
            let propensity_estimate = maturity_mask.then_some(behavior_policy_probability);
            let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
            let training_weight = structural_path_ranking_training_weight(
                calibrated_label,
                maturity_weight,
                ips_weight,
            );
            let prior_stats = structural_prior_state.paths.get(&branch_path);
            let experience_prior =
                structural_resolved_smoothed_prior(prior_stats, structural_prior_state, row_score);
            let row_candidate_set_id = if kept_branch_counts
                .get(&branch_path)
                .copied()
                .unwrap_or_default()
                > 1
            {
                format!(
                    "{}:rank-row:{:016x}",
                    candidate_set_id,
                    structural_stable_hash64(&format!(
                        "{}|{}|{}|{}",
                        candidate_set_id, branch_path, source_index, rank_row.unit_label
                    ))
                )
            } else {
                candidate_set_id.clone()
            };
            let mut row = StructuralPathRankingTargetRow {
                rank: index + 1,
                candidate_set_id: row_candidate_set_id.clone(),
                candidate_set_size,
                path_id: branch_path.clone(),
                scenario_id: format!(
                    "auto-quant-agent-material-rank:{:016x}",
                    structural_stable_hash64(&format!("{}|{}", row_candidate_set_id, branch_path))
                ),
                path_label: rank_row.unit_label.clone(),
                regime_profit_branch_path: Some(branch_path.clone()),
                parent_regime_root: None,
                main_regime: rank_row.main_regime.clone(),
                sub_regime: rank_row.sub_regime.clone(),
                sub_sub_regime_or_profit_factor: rank_row.sub_sub_regime_or_profit_factor.clone(),
                profit_factor: rank_row.profit_factor.clone(),
                direction: structural_feedback_path_direction_label(&branch_path, None, snapshot),
                raw_path_score: None,
                calibrated_path_prob: maturity_mask.then_some(row_score),
                path_prob_lower_bound: None,
                execution_gate_status: None,
                execution_gate_min_path_prob: None,
                execution_gate_reason: None,
                pending_reward_state: pending_reward_state.to_string(),
                maturity_mask,
                maturity_weight,
                calibrated_label,
                propensity_estimate: propensity_estimate.or(Some(behavior_policy_probability)),
                ips_weight,
                training_weight,
                regime_calibration_bucket,
                behavior_policy_probability,
                execution_propensity: Some(behavior_policy_probability),
                target_policy_probability_confidence:
                    structural_prior_target_policy_probability_confidence(prior_stats),
                target_policy_probability_lower_bound:
                    structural_prior_target_policy_probability_lower_bound(prior_stats),
                target_policy_reward_prior: structural_prior_target_policy_reward_prior(
                    prior_stats,
                ),
                target_policy_reward_lower_bound: structural_prior_target_policy_reward_lower_bound(
                    prior_stats,
                ),
                experience_prior,
                current_posterior: row_score,
                structural_baseline_score: row_score,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: Some("auto_quant_agent_material_rank".to_string()),
                score_source_kind: Some("agent_material_rank".to_string()),
                score_model_artifact_uri: Some(rank_artifact.artifact_id.clone()),
                score_generator: Some("ict-engine-auto-quant-rank-adapter-v1".to_string()),
            };
            structural_populate_regime_profit_branch_fields(&mut row);
            regime_aux_context.apply_to_row(&mut row);
            row
        })
        .collect()
}

fn structural_path_ranking_row_is_auto_quant_material_rank(
    row: &StructuralPathRankingTargetRow,
) -> bool {
    row.score_source_kind.as_deref() == Some("agent_material_rank")
        || row.score_model_family.as_deref() == Some("auto_quant_agent_material_rank")
        || row
            .candidate_set_id
            .starts_with("auto-quant-agent-material-rank:")
        || row
            .scenario_id
            .starts_with("auto-quant-agent-material-rank:")
}

fn structural_current_auto_quant_material_rank_target_rows(
    state_dir: Option<&str>,
    symbol: &str,
) -> Vec<StructuralPathRankingTargetRow> {
    let Some(state_dir) = state_dir else {
        return Vec::new();
    };
    let summary_path = Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR)
        .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    let Ok(raw_summary) = fs::read_to_string(&summary_path) else {
        return Vec::new();
    };
    let Ok(summary) = serde_json::from_str::<StructuralPathRankingTargetExportSummary>(
        &raw_summary,
    )
    .map(|summary| {
        rebase_structural_path_ranking_target_export_summary_paths(state_dir, symbol, summary)
    }) else {
        return Vec::new();
    };
    load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path))
        .unwrap_or_default()
        .into_iter()
        .filter(structural_path_ranking_row_is_auto_quant_material_rank)
        .collect()
}

fn structural_persisted_target_rows(
    state_dir: Option<&str>,
    symbol: &str,
) -> Vec<StructuralPathRankingTargetRow> {
    let Some(state_dir) = state_dir else {
        return Vec::new();
    };
    let summary_path = Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR)
        .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    let Ok(raw_summary) = fs::read_to_string(&summary_path) else {
        return Vec::new();
    };
    let Ok(summary) = serde_json::from_str::<StructuralPathRankingTargetExportSummary>(
        &raw_summary,
    )
    .map(|summary| {
        rebase_structural_path_ranking_target_export_summary_paths(state_dir, symbol, summary)
    }) else {
        return Vec::new();
    };
    let mut rows = load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path))
        .unwrap_or_default();
    rows.extend(
        load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
            .unwrap_or_default(),
    );
    rows
}

fn structural_persisted_exact_feedback_target_rows(
    state_dir: Option<&str>,
    symbol: &str,
) -> Vec<StructuralPathRankingTargetRow> {
    let mut by_path = BTreeMap::<String, StructuralPathRankingTargetRow>::new();
    for row in structural_persisted_target_rows(state_dir, symbol) {
        if !row.path_id.contains(" -> ") || row.path_id.starts_with("path:") {
            continue;
        }
        let feedback_or_mature = row.candidate_set_id.starts_with("structural-feedback-")
            || row.training_weight.unwrap_or(0.0) > 0.0
            || matches!(
                row.pending_reward_state.as_str(),
                "matured_success" | "matured_failure" | "matured_invalidated"
            );
        if !feedback_or_mature {
            continue;
        }
        by_path
            .entry(row.path_id.clone())
            .and_modify(|existing| {
                if structural_persisted_exact_feedback_row_priority(&row)
                    > structural_persisted_exact_feedback_row_priority(existing)
                {
                    *existing = row.clone();
                }
            })
            .or_insert(row);
    }
    by_path.into_values().collect()
}

fn structural_persisted_exact_feedback_row_priority(
    row: &StructuralPathRankingTargetRow,
) -> (u8, u8, u8, u8) {
    let mature = matches!(
        row.pending_reward_state.as_str(),
        "matured_success" | "matured_failure" | "matured_invalidated"
    ) as u8;
    let weighted = (row.training_weight.unwrap_or(0.0) > 0.0) as u8;
    let gated = row.execution_gate_status.is_some() as u8;
    let aggregate = row
        .candidate_set_id
        .starts_with("structural-feedback-aggregate:") as u8;
    (mature, weighted, gated, aggregate)
}

fn structural_persisted_exact_feedback_candidate_from_row(
    snapshot: &WorkflowSnapshot,
    row: &StructuralPathRankingTargetRow,
) -> Option<StructuralPathArtifact> {
    let path_id = structural_normalize_branch_path(&row.path_id)?;
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    let score = row
        .path_prob_lower_bound
        .or(row.calibrated_path_prob)
        .or(row.raw_path_score)
        .unwrap_or(row.structural_baseline_score)
        .clamp(0.0, 1.0);
    Some(StructuralPathArtifact {
        path_id: path_id.clone(),
        scenario_id: row.scenario_id.clone(),
        path_label: if row.path_label.trim().is_empty() {
            path_id.clone()
        } else {
            row.path_label.clone()
        },
        direction: row.direction.clone(),
        entry_style: "structural_feedback_path".to_string(),
        selected_entry_quality: structural_selected_entry_quality(snapshot),
        selected_entry_quality_probability: structural_selected_entry_quality_probability(snapshot),
        pre_bayes_gate_status: structural_pre_bayes_gate_status(snapshot),
        multi_timeframe_direction_bias: structural_multi_timeframe_direction_bias(snapshot),
        execution_candidate_status: snapshot
            .latest_execution_candidate
            .as_ref()
            .map(|candidate| candidate.candidate_status.clone())
            .filter(|value| !value.trim().is_empty()),
        execution_candidate_artifact_id: snapshot
            .latest_execution_candidate
            .as_ref()
            .map(|candidate| candidate.artifact_id.clone()),
        execution_readiness: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.execution_readiness),
        prediction_edge_share: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.prediction_edge_share),
        execution_edge_share: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.execution_edge_share),
        historical_total_records: if row.training_weight.unwrap_or(0.0) > 0.0 {
            30
        } else {
            1
        },
        historical_followed_count: if row.training_weight.unwrap_or(0.0) > 0.0 {
            30
        } else {
            1
        },
        execution_propensity: row.execution_propensity,
        historical_win_rate: row.calibrated_label,
        historical_invalidation_rate: None,
        historical_avg_pnl: row.raw_path_score,
        trigger_conditions: vec![format!(
            "preserve persisted exact structural feedback path {path_id}"
        )],
        confirmation_conditions: vec![format!(
            "pending_reward_state={} execution_gate_status={}",
            row.pending_reward_state,
            row.execution_gate_status.as_deref().unwrap_or("none")
        )],
        stop_definition: "use the recorded branch feedback stop/exit contract".to_string(),
        target_definition: format!("persisted_feedback_score={score:.6}"),
        invalidation_conditions: vec![
            "do not collapse exact feedback path into a generic structural path".to_string(),
        ],
        expected_failure_mode:
            "persisted exact feedback path not consumed by downstream execution surface".to_string(),
        max_time_in_trade: "use persisted feedback horizon when available".to_string(),
        path_prior: row.experience_prior.clamp(0.0, 1.0),
        path_posterior: row.current_posterior.clamp(0.0, 1.0),
        bbn_support_score: row.current_posterior.clamp(0.0, 1.0),
        catboost_score: row.raw_path_score,
        path_ranker_calibrated_path_prob: row.calibrated_path_prob,
        path_ranker_path_prob_lower_bound: row.path_prob_lower_bound,
        path_ranker_execution_gate_status: row.execution_gate_status.clone(),
        path_ranker_runtime_source: Some("persisted_feedback_target".to_string()),
        composite_preference_score: score,
        recommended_command: next_meta.executable_command.clone().or_else(|| {
            if command.trim().is_empty() {
                None
            } else {
                Some(command)
            }
        }),
    })
}

fn structural_auto_quant_material_rank_candidate_from_row(
    snapshot: &WorkflowSnapshot,
    row: &StructuralPathRankingTargetRow,
) -> Option<StructuralPathArtifact> {
    let path_id = row
        .regime_profit_branch_path
        .as_deref()
        .and_then(structural_normalize_branch_path)
        .or_else(|| structural_normalize_branch_path(&row.path_id))?;
    let score = row
        .raw_path_score
        .or(row.calibrated_path_prob)
        .unwrap_or(row.structural_baseline_score)
        .clamp(0.0, 1.0);
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    StructuralPathArtifact {
        path_id: path_id.clone(),
        scenario_id: row.scenario_id.clone(),
        path_label: if row.path_label.trim().is_empty() {
            path_id.clone()
        } else {
            row.path_label.clone()
        },
        direction: row.direction.clone(),
        entry_style: "auto_quant_agent_material_rank".to_string(),
        selected_entry_quality: structural_selected_entry_quality(snapshot),
        selected_entry_quality_probability: structural_selected_entry_quality_probability(snapshot),
        pre_bayes_gate_status: structural_pre_bayes_gate_status(snapshot),
        multi_timeframe_direction_bias: structural_multi_timeframe_direction_bias(snapshot),
        execution_candidate_status: snapshot
            .latest_execution_candidate
            .as_ref()
            .map(|candidate| candidate.candidate_status.clone())
            .filter(|value| !value.trim().is_empty()),
        execution_candidate_artifact_id: snapshot
            .latest_execution_candidate
            .as_ref()
            .map(|candidate| candidate.artifact_id.clone()),
        execution_readiness: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.execution_readiness),
        prediction_edge_share: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.prediction_edge_share),
        execution_edge_share: snapshot
            .latest_analyze
            .as_ref()
            .and_then(|phase| phase.execution_edge_share),
        historical_total_records: 0,
        historical_followed_count: 0,
        execution_propensity: row.execution_propensity,
        historical_win_rate: None,
        historical_invalidation_rate: None,
        historical_avg_pnl: None,
        trigger_conditions: vec![format!(
            "preserve current Auto-Quant material-rank branch {path_id}"
        )],
        confirmation_conditions: vec![
            "ranked Auto-Quant material row must remain selectable by runtime".to_string(),
        ],
        stop_definition: "use the Auto-Quant material branch stop contract".to_string(),
        target_definition: format!("auto_quant_material_rank_score={score:.6}"),
        invalidation_conditions: vec![
            "do not collapse this branch into a generic structural runtime path".to_string(),
        ],
        expected_failure_mode:
            "Auto-Quant material-rank branch exported but not admitted as runtime candidate"
                .to_string(),
        max_time_in_trade: "use Auto-Quant material horizon".to_string(),
        path_prior: row.experience_prior.clamp(0.0, 1.0),
        path_posterior: row.current_posterior.clamp(0.0, 1.0),
        bbn_support_score: row.current_posterior.clamp(0.0, 1.0),
        catboost_score: row.raw_path_score,
        path_ranker_calibrated_path_prob: row.calibrated_path_prob,
        path_ranker_path_prob_lower_bound: row.path_prob_lower_bound,
        path_ranker_execution_gate_status: row.execution_gate_status.clone(),
        path_ranker_runtime_source: None,
        composite_preference_score: score,
        recommended_command: next_meta.executable_command.clone().or_else(|| {
            if command.trim().is_empty() {
                None
            } else {
                Some(command)
            }
        }),
    }
    .into()
}

fn structural_agent_material_rank_row_has_dense_observation(
    row: &crate::application::auto_quant::AgentMaterialRankRow,
) -> bool {
    row.status == "completed"
        && row.trade_count.unwrap_or(0) >= 30
        && (row.total_profit_pct.is_some() || row.sharpe.is_some())
}

fn structural_agent_material_rank_row_score(
    row: &crate::application::auto_quant::AgentMaterialRankRow,
) -> f64 {
    row.win_rate_pct
        .map(|value| value / 100.0)
        .or(row.total_profit_pct.map(|value| value / 100.0))
        .or(row.sharpe.map(|value| value / 10.0))
        .unwrap_or(0.0)
        .clamp(0.0, 1.0)
}

fn structural_required_candidate_paths(
    snapshot: &WorkflowSnapshot,
    ranked_paths: Vec<StructuralPathArtifact>,
    min_top_count: usize,
) -> Vec<StructuralPathArtifact> {
    let required_branch_paths = structural_regime_bundle_branch_paths(snapshot)
        .into_iter()
        .collect::<BTreeSet<_>>();

    let mut selected = Vec::new();
    let mut seen_path_ids = BTreeSet::new();
    for path in ranked_paths.iter().take(min_top_count) {
        if seen_path_ids.insert(path.path_id.clone()) {
            selected.push(path.clone());
        }
    }
    for path in &ranked_paths {
        if required_branch_paths.contains(&path.path_id)
            && seen_path_ids.insert(path.path_id.clone())
        {
            selected.push(path.clone());
        }
    }
    for path in ranked_paths {
        if path.entry_style == "auto_quant_agent_material_rank"
            && seen_path_ids.insert(path.path_id.clone())
        {
            selected.push(path);
        }
    }
    selected
}

pub(crate) fn build_structural_path_ranking_target_artifact_with_runtime_context_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    runtime_context: StructuralPathRankerRuntimeContext<'_>,
) -> StructuralPathRankingTargetArtifact {
    let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        runtime_context,
    );
    structural_path_ranking_target_artifact_from_candidates(
        snapshot,
        feedback_history,
        structural_prior_state,
        selection.candidate_paths,
        Some(selection.candidate_set_id),
    )
}

pub fn export_structural_path_ranking_target(
    state_dir: &str,
    symbol: &str,
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Result<StructuralPathRankingTargetExportSummary> {
    export_structural_path_ranking_target_with_agent_material_rank(
        state_dir,
        symbol,
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        None,
    )
}

pub fn export_structural_path_ranking_target_with_agent_material_rank(
    state_dir: &str,
    symbol: &str,
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    agent_material_rank: Option<&AgentMaterialRankArtifact>,
) -> Result<StructuralPathRankingTargetExportSummary> {
    let mut artifact = build_structural_path_ranking_target_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let symbol_dir = Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR);
    fs::create_dir_all(&symbol_dir)?;
    let csv_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_CSV_FILE}"
    );
    let jsonl_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_JSONL_FILE}"
    );
    let history_csv_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_HISTORY_CSV_FILE}"
    );
    let history_jsonl_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_HISTORY_JSONL_FILE}"
    );
    let summary_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE}"
    );
    let history_jsonl_path = Path::new(state_dir).join(symbol).join(&history_jsonl_name);
    let existing_history_rows = load_structural_path_ranking_target_rows(&history_jsonl_path)?;
    let feedback_target_rows = structural_path_ranking_feedback_target_rows(
        symbol,
        feedback_history,
        structural_prior_state,
    );
    let feedback_aggregate_target_rows = structural_path_ranking_feedback_aggregate_target_rows(
        symbol,
        feedback_history,
        structural_prior_state,
    );
    let regime_bundle_target_rows = structural_path_ranking_regime_bundle_target_rows(
        snapshot,
        structural_prior_state,
        &artifact.candidate_set_id,
        artifact.candidate_set_size,
    );
    let mut agent_material_rank_target_rows = agent_material_rank
        .map(|rank| {
            structural_path_ranking_agent_material_rank_target_rows(
                snapshot,
                structural_prior_state,
                rank,
            )
        })
        .unwrap_or_default();
    let existing_history_score_map = existing_history_rows
        .iter()
        .filter_map(|row| {
            row.raw_path_score.map(|_| {
                (
                    structural_path_ranking_target_row_score_key(row),
                    row.clone(),
                )
            })
        })
        .collect::<BTreeMap<_, _>>();
    for row in &mut artifact.rows {
        structural_path_ranking_carry_forward_score_metadata(row, &existing_history_score_map);
    }
    for row in &mut agent_material_rank_target_rows {
        structural_path_ranking_carry_forward_score_metadata(row, &existing_history_score_map);
    }
    let mut rows_for_history = artifact.rows.clone();
    rows_for_history.extend(feedback_target_rows.clone());
    rows_for_history.extend(feedback_aggregate_target_rows.clone());
    rows_for_history.extend(regime_bundle_target_rows.clone());
    rows_for_history.extend(agent_material_rank_target_rows.clone());
    let history_rows =
        upsert_structural_path_ranking_target_history(&history_jsonl_path, &rows_for_history)?;
    let mut history_artifact = StructuralPathRankingTargetArtifact {
        protocol_version: artifact.protocol_version.clone(),
        symbol: artifact.symbol.clone(),
        candidate_set_id: artifact.candidate_set_id.clone(),
        candidate_set_size: artifact.candidate_set_size,
        generated_at: artifact.generated_at.clone(),
        rows: history_rows,
    };
    let history_report = apply_structural_path_probability_calibration(&mut history_artifact);
    let mut current_artifact = StructuralPathRankingTargetArtifact {
        protocol_version: artifact.protocol_version.clone(),
        symbol: artifact.symbol.clone(),
        candidate_set_id: artifact.candidate_set_id.clone(),
        candidate_set_size: artifact.candidate_set_size,
        generated_at: artifact.generated_at.clone(),
        rows: artifact.rows,
    };
    let current_feedback_target_rows = structural_path_ranking_current_feedback_target_rows(
        &feedback_target_rows,
        &current_artifact.rows,
    );
    current_artifact.rows.extend(current_feedback_target_rows);
    let current_feedback_aggregate_target_rows =
        structural_path_ranking_current_feedback_target_rows(
            &feedback_aggregate_target_rows,
            &current_artifact.rows,
        );
    current_artifact
        .rows
        .extend(current_feedback_aggregate_target_rows);
    let current_regime_bundle_target_rows = structural_path_ranking_current_feedback_target_rows(
        &regime_bundle_target_rows,
        &current_artifact.rows,
    );
    current_artifact
        .rows
        .extend(current_regime_bundle_target_rows);
    let current_agent_material_rank_target_rows =
        structural_path_ranking_current_feedback_target_rows(
            &agent_material_rank_target_rows,
            &current_artifact.rows,
        );
    current_artifact
        .rows
        .extend(current_agent_material_rank_target_rows);
    for row in &mut current_artifact.rows {
        structural_populate_regime_profit_branch_fields(row);
    }
    for row in &mut history_artifact.rows {
        structural_populate_regime_profit_branch_fields(row);
    }
    structural_path_ranking_apply_execution_feedback_lifecycle_gates(&mut history_artifact.rows);
    apply_structural_path_probability_bins(&mut current_artifact.rows, &history_report.bins);
    apply_structural_path_ranking_execution_gates(&mut current_artifact);
    structural_path_ranking_apply_execution_feedback_lifecycle_gates(&mut current_artifact.rows);
    let history_csv = render_structural_path_ranking_target_rows_csv(
        &history_artifact.protocol_version,
        &history_artifact.symbol,
        &history_artifact.generated_at,
        &history_artifact.rows,
    );
    let history_jsonl = render_structural_path_ranking_target_rows_jsonl(&history_artifact.rows)?;
    let summary = structural_path_ranking_target_export_summary(
        StructuralPathRankingTargetExportSummaryInput {
            state_dir,
            symbol,
            artifact: &current_artifact,
            csv_name: &csv_name,
            jsonl_name: &jsonl_name,
            history_csv_name: &history_csv_name,
            history_jsonl_name: &history_jsonl_name,
            history_rows: &history_artifact.rows,
            summary_name: &summary_name,
        },
    );
    let summary_json = serde_json::to_string_pretty(&summary)?;
    let csv = render_structural_path_ranking_target_csv(&current_artifact);
    let jsonl = render_structural_path_ranking_target_jsonl(&current_artifact)?;
    save_text_state(state_dir, symbol, &csv_name, &csv)?;
    save_text_state(state_dir, symbol, &jsonl_name, &jsonl)?;
    save_text_state(state_dir, symbol, &history_csv_name, &history_csv)?;
    save_text_state(state_dir, symbol, &history_jsonl_name, &history_jsonl)?;
    save_text_state(state_dir, symbol, &summary_name, &summary_json)?;
    Ok(summary)
}

pub fn apply_structural_path_ranking_external_scores(
    state_dir: &str,
    symbol: &str,
    scores: &[StructuralPathRankingExternalScoreInput],
) -> Result<StructuralPathRankingTargetExportSummary> {
    let summary_path = Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR)
        .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    let raw = fs::read_to_string(&summary_path)?;
    let summary = rebase_structural_path_ranking_target_export_summary_paths(
        state_dir,
        symbol,
        serde_json::from_str::<StructuralPathRankingTargetExportSummary>(&raw)?,
    );
    let mut current_rows =
        load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path))?;
    let history_jsonl_path = if !summary.history_jsonl_path.is_empty() {
        Path::new(&summary.history_jsonl_path).to_path_buf()
    } else {
        Path::new(&summary.jsonl_path).to_path_buf()
    };
    let mut history_rows = load_structural_path_ranking_target_rows(&history_jsonl_path)?;
    let score_map = scores
        .iter()
        .map(|item| {
            (
                structural_path_ranking_candidate_path_score_key(
                    &item.candidate_set_id,
                    &item.path_id,
                ),
                item,
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut matched = 0usize;
    for row in &mut current_rows {
        if let Some(score) = score_map.get(&structural_path_ranking_target_row_score_key(row)) {
            row.raw_path_score = Some(score.raw_path_score.clamp(0.0, 1.0));
            row.score_model_family = score
                .score_model_family
                .clone()
                .or_else(|| row.score_model_family.clone());
            row.score_source_kind = score
                .score_source_kind
                .clone()
                .or_else(|| row.score_source_kind.clone());
            row.score_model_artifact_uri = score
                .score_model_artifact_uri
                .clone()
                .or_else(|| row.score_model_artifact_uri.clone());
            row.score_generator = score
                .score_generator
                .clone()
                .or_else(|| row.score_generator.clone());
            clear_structural_path_ranking_target_row_outputs(row);
            matched += 1;
        }
    }
    for row in &mut history_rows {
        if let Some(score) = score_map.get(&structural_path_ranking_target_row_score_key(row)) {
            row.raw_path_score = Some(score.raw_path_score.clamp(0.0, 1.0));
            row.score_model_family = score
                .score_model_family
                .clone()
                .or_else(|| row.score_model_family.clone());
            row.score_source_kind = score
                .score_source_kind
                .clone()
                .or_else(|| row.score_source_kind.clone());
            row.score_model_artifact_uri = score
                .score_model_artifact_uri
                .clone()
                .or_else(|| row.score_model_artifact_uri.clone());
            row.score_generator = score
                .score_generator
                .clone()
                .or_else(|| row.score_generator.clone());
            clear_structural_path_ranking_target_row_outputs(row);
        }
    }
    if matched == 0 {
        anyhow::bail!("no structural path ranking target rows matched the supplied scores");
    }
    let generated_at = Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true);
    let mut history_artifact = StructuralPathRankingTargetArtifact {
        protocol_version: "structural-path-ranking-target-v1".to_string(),
        symbol: symbol.to_string(),
        candidate_set_id: summary.candidate_set_id.clone(),
        candidate_set_size: summary.candidate_set_size,
        generated_at: generated_at.clone(),
        rows: history_rows,
    };
    let history_report = apply_structural_path_probability_calibration(&mut history_artifact);
    let mut current_artifact = StructuralPathRankingTargetArtifact {
        protocol_version: "structural-path-ranking-target-v1".to_string(),
        symbol: symbol.to_string(),
        candidate_set_id: summary.candidate_set_id.clone(),
        candidate_set_size: summary.candidate_set_size,
        generated_at: generated_at.clone(),
        rows: current_rows,
    };
    apply_structural_path_probability_bins(&mut current_artifact.rows, &history_report.bins);
    apply_structural_path_ranking_execution_gates(&mut current_artifact);
    structural_path_ranking_apply_execution_feedback_lifecycle_gates(&mut current_artifact.rows);
    let csv_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_CSV_FILE}"
    );
    let jsonl_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_JSONL_FILE}"
    );
    let history_csv_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_HISTORY_CSV_FILE}"
    );
    let history_jsonl_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_HISTORY_JSONL_FILE}"
    );
    let summary_name = format!(
        "{STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR}/{STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE}"
    );
    let current_csv = render_structural_path_ranking_target_csv(&current_artifact);
    let current_jsonl = render_structural_path_ranking_target_jsonl(&current_artifact)?;
    let history_csv = render_structural_path_ranking_target_rows_csv(
        &current_artifact.protocol_version,
        &current_artifact.symbol,
        &current_artifact.generated_at,
        &history_artifact.rows,
    );
    let history_jsonl = render_structural_path_ranking_target_rows_jsonl(&history_artifact.rows)?;
    let updated_summary = structural_path_ranking_target_export_summary(
        StructuralPathRankingTargetExportSummaryInput {
            state_dir,
            symbol,
            artifact: &current_artifact,
            csv_name: &csv_name,
            jsonl_name: &jsonl_name,
            history_csv_name: &history_csv_name,
            history_jsonl_name: &history_jsonl_name,
            history_rows: &history_artifact.rows,
            summary_name: &summary_name,
        },
    );
    let summary_json = serde_json::to_string_pretty(&updated_summary)?;
    save_text_state(state_dir, symbol, &csv_name, &current_csv)?;
    save_text_state(state_dir, symbol, &jsonl_name, &current_jsonl)?;
    save_text_state(state_dir, symbol, &history_csv_name, &history_csv)?;
    save_text_state(state_dir, symbol, &history_jsonl_name, &history_jsonl)?;
    save_text_state(state_dir, symbol, &summary_name, &summary_json)?;
    Ok(updated_summary)
}

fn structural_candidate_policy_denominator(candidate_paths: &[StructuralPathArtifact]) -> f64 {
    candidate_paths
        .iter()
        .map(|path| path.composite_preference_score.max(0.0))
        .sum()
}

fn structural_candidate_policy_probability(
    composite_score: f64,
    denominator: f64,
    candidate_count: usize,
) -> f64 {
    if denominator > f64::EPSILON {
        (composite_score.max(0.0) / denominator).clamp(0.0, 1.0)
    } else if candidate_count > 0 {
        1.0 / candidate_count as f64
    } else {
        0.0
    }
}

fn structural_candidate_set_id(symbol: &str, candidate_paths: &[StructuralPathArtifact]) -> String {
    let mut fingerprint = String::new();
    fingerprint.push_str(symbol);
    let mut path_ids = candidate_paths
        .iter()
        .map(|path| path.path_id.as_str())
        .collect::<Vec<_>>();
    path_ids.sort_unstable();
    for path_id in path_ids {
        fingerprint.push('|');
        fingerprint.push_str(path_id);
    }
    format!(
        "structural-candidates:{symbol}:{:016x}",
        structural_stable_hash64(&fingerprint)
    )
}

fn structural_stable_hash64(value: &str) -> u64 {
    let mut hash = 0xcbf29ce484222325_u64;
    for byte in value.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn resolve_structural_path_ranker_runtime(
    state_dir: Option<&str>,
    symbol: &str,
    candidate_set_id: &str,
    current_candidate_rows: &[StructuralPathRankingTargetRow],
    candidate_paths: &mut [StructuralPathArtifact],
) -> Option<StructuralPathRankerRuntimeSurface> {
    let state_dir = state_dir?;
    let selection = load_structural_path_ranking_runtime_selection(state_dir, symbol)?;
    let reuse_mode = selection.reuse_mode.clone();
    if !selection.enabled {
        return Some(StructuralPathRankerRuntimeSurface {
            enabled: false,
            status: "disabled".to_string(),
            reuse_mode: Some(reuse_mode),
            ..StructuralPathRankerRuntimeSurface::default()
        });
    }
    let summary_path = Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR)
        .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    let Ok(raw_summary) = fs::read_to_string(&summary_path) else {
        return Some(StructuralPathRankerRuntimeSurface {
            enabled: true,
            status: "enabled_export_missing".to_string(),
            reuse_mode: Some(reuse_mode),
            ..StructuralPathRankerRuntimeSurface::default()
        });
    };
    let Ok(summary) = serde_json::from_str::<StructuralPathRankingTargetExportSummary>(
        &raw_summary,
    )
    .map(|summary| {
        rebase_structural_path_ranking_target_export_summary_paths(state_dir, symbol, summary)
    }) else {
        return Some(StructuralPathRankerRuntimeSurface {
            enabled: true,
            status: "enabled_export_invalid".to_string(),
            reuse_mode: Some(reuse_mode),
            ..StructuralPathRankerRuntimeSurface::default()
        });
    };
    let current_rows = load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path))
        .unwrap_or_default();
    let history_path = if summary.history_jsonl_path.trim().is_empty() {
        Path::new(&summary.jsonl_path).to_path_buf()
    } else {
        Path::new(&summary.history_jsonl_path).to_path_buf()
    };
    let history_rows = load_structural_path_ranking_target_rows(&history_path).unwrap_or_default();
    let artifact_metadata =
        load_structural_path_ranker_runtime_artifact_metadata(state_dir, symbol);
    let direct_model_rows = artifact_metadata
        .as_ref()
        .and_then(|artifact| {
            if !structural_path_ranker_supports_direct_model_family(&artifact.model_family) {
                return None;
            }
            score_structural_path_ranker_runtime_rows_with_direct_model(
                state_dir,
                symbol,
                &artifact.artifact_uri,
                &artifact.model_family,
                current_candidate_rows,
            )
            .ok()
        })
        .unwrap_or_default();
    let using_direct_model = !direct_model_rows.is_empty();
    let explicit_rows = artifact_metadata
        .as_ref()
        .and_then(|artifact| {
            if !structural_path_ranker_supports_explicit_family(&artifact.model_family) {
                return None;
            }
            score_structural_path_ranker_runtime_rows_with_explicit_family(
                state_dir,
                symbol,
                &artifact.model_family,
                current_candidate_rows,
            )
            .ok()
        })
        .unwrap_or_default();
    let using_explicit = !explicit_rows.is_empty();
    let service_rows = artifact_metadata
        .as_ref()
        .and_then(|artifact| {
            if !structural_path_ranker_supports_service_family(&artifact.model_family) {
                return None;
            }
            score_structural_path_ranker_runtime_rows_with_service(
                symbol,
                &artifact.artifact_uri,
                &artifact.score_column,
                &artifact.model_family,
                current_candidate_rows,
            )
            .ok()
        })
        .unwrap_or_default();
    let using_service = !service_rows.is_empty();
    let service_declared = artifact_metadata.as_ref().is_some_and(|artifact| {
        structural_path_ranker_supports_service_family(&artifact.model_family)
    });
    let artifact_rows = if using_direct_model {
        direct_model_rows
    } else if using_explicit {
        explicit_rows
    } else if using_service {
        service_rows
    } else if service_declared {
        Vec::new()
    } else {
        artifact_metadata
            .as_ref()
            .and_then(|artifact| {
                load_structural_path_ranker_runtime_artifact_rows(
                    state_dir,
                    symbol,
                    &artifact.artifact_uri,
                    &artifact.score_column,
                )
                .ok()
            })
            .unwrap_or_default()
    };
    let using_static_registered_artifact = !using_direct_model
        && !using_explicit
        && !using_service
        && !service_declared
        && artifact_metadata.is_some();
    let current_candidate_row_keys = current_candidate_rows
        .iter()
        .map(structural_path_ranker_candidate_row_key)
        .collect::<BTreeSet<_>>();
    let runtime_row_priority = |row: &StructuralPathRankerRuntimeRow| -> u8 {
        if row.candidate_set_id == candidate_set_id {
            2
        } else if current_candidate_row_keys
            .contains(&structural_path_ranker_runtime_candidate_row_key(row))
        {
            1
        } else {
            0
        }
    };
    let mut artifact_exact_matches = BTreeMap::<String, StructuralPathRankerRuntimeRow>::new();
    let mut artifact_exact_priorities = BTreeMap::<String, u8>::new();
    for row in artifact_rows.iter().filter(|row| {
        row.raw_path_score.is_some()
            && candidate_paths
                .iter()
                .any(|path| path.path_id == row.path_id)
    }) {
        let priority = runtime_row_priority(row);
        if priority == 0 {
            continue;
        }
        let existing_priority = artifact_exact_priorities
            .get(&row.path_id)
            .copied()
            .unwrap_or(0);
        if priority > existing_priority {
            artifact_exact_priorities.insert(row.path_id.clone(), priority);
            artifact_exact_matches.insert(row.path_id.clone(), row.clone());
        }
    }
    let artifact_path_matches = if using_static_registered_artifact {
        artifact_rows
            .iter()
            .filter(|row| {
                row.raw_path_score.is_some()
                    && candidate_paths
                        .iter()
                        .any(|path| path.path_id == row.path_id)
            })
            .cloned()
            .map(|row| (row.path_id.clone(), row))
            .collect::<BTreeMap<_, _>>()
    } else {
        BTreeMap::new()
    };
    let mut artifact_history_matches = BTreeMap::<String, StructuralPathRankerRuntimeRow>::new();
    for row in &artifact_rows {
        if row.raw_path_score.is_none() {
            continue;
        }
        if candidate_paths
            .iter()
            .any(|path| path.path_id == row.path_id)
        {
            artifact_history_matches.insert(row.path_id.clone(), row.clone());
        }
    }

    let exact_matches = history_rows
        .iter()
        .chain(current_rows.iter())
        .filter(|row| {
            let row_key = structural_path_ranker_candidate_row_key(row);
            (row.candidate_set_id == candidate_set_id
                || current_candidate_row_keys.contains(&row_key))
                && row.raw_path_score.is_some()
                && candidate_paths
                    .iter()
                    .any(|path| path.path_id == row.path_id)
        })
        .map(|row| {
            (
                row.path_id.clone(),
                StructuralPathRankerRuntimeRow {
                    candidate_set_id: row.candidate_set_id.clone(),
                    path_id: row.path_id.clone(),
                    raw_path_score: row.raw_path_score,
                    calibrated_path_prob: row.calibrated_path_prob,
                    path_prob_lower_bound: row.path_prob_lower_bound,
                    execution_gate_status: row.execution_gate_status.clone(),
                    score_model_family: row.score_model_family.clone(),
                    score_source_kind: row.score_source_kind.clone(),
                    score_model_artifact_uri: row.score_model_artifact_uri.clone(),
                    score_generator: row.score_generator.clone(),
                },
            )
        })
        .collect::<BTreeMap<_, _>>();

    let mut latest_history_matches = BTreeMap::<String, StructuralPathRankerRuntimeRow>::new();
    let mut history_gate_metadata_matches =
        BTreeMap::<String, StructuralPathRankerRuntimeRow>::new();
    for row in &history_rows {
        if row.calibrated_path_prob.is_none()
            && row.path_prob_lower_bound.is_none()
            && row.execution_gate_status.is_none()
        {
            continue;
        }
        if candidate_paths
            .iter()
            .any(|path| path.path_id == row.path_id)
        {
            history_gate_metadata_matches.insert(
                row.path_id.clone(),
                StructuralPathRankerRuntimeRow {
                    candidate_set_id: row.candidate_set_id.clone(),
                    path_id: row.path_id.clone(),
                    raw_path_score: row.raw_path_score,
                    calibrated_path_prob: row.calibrated_path_prob,
                    path_prob_lower_bound: row.path_prob_lower_bound,
                    execution_gate_status: row.execution_gate_status.clone(),
                    score_model_family: row.score_model_family.clone(),
                    score_source_kind: row.score_source_kind.clone(),
                    score_model_artifact_uri: row.score_model_artifact_uri.clone(),
                    score_generator: row.score_generator.clone(),
                },
            );
        }
    }
    for row in history_rows.iter().chain(current_rows.iter()) {
        if row.raw_path_score.is_none() {
            continue;
        }
        if candidate_paths
            .iter()
            .any(|path| path.path_id == row.path_id)
        {
            latest_history_matches.insert(
                row.path_id.clone(),
                StructuralPathRankerRuntimeRow {
                    candidate_set_id: row.candidate_set_id.clone(),
                    path_id: row.path_id.clone(),
                    raw_path_score: row.raw_path_score,
                    calibrated_path_prob: row.calibrated_path_prob,
                    path_prob_lower_bound: row.path_prob_lower_bound,
                    execution_gate_status: row.execution_gate_status.clone(),
                    score_model_family: row.score_model_family.clone(),
                    score_source_kind: row.score_source_kind.clone(),
                    score_model_artifact_uri: row.score_model_artifact_uri.clone(),
                    score_generator: row.score_generator.clone(),
                },
            );
        }
    }

    let mut applied_path_count = 0usize;
    let mut artifact_match_count = 0usize;
    let mut history_match_count = 0usize;
    let mut candidate_set_match_count = 0usize;
    let mut score_model_families = BTreeSet::<String>::new();
    let mut score_source_kinds = BTreeSet::<String>::new();
    let mut score_model_artifact_uris = BTreeSet::<String>::new();
    let mut score_generators = BTreeSet::<String>::new();
    for path in candidate_paths {
        let artifact_history_match = if !using_direct_model
            && !using_service
            && reuse_mode == STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY
        {
            artifact_history_matches.get(&path.path_id).cloned()
        } else {
            None
        };
        let matched = if let Some(row) = artifact_exact_matches.get(&path.path_id) {
            artifact_match_count += 1;
            Some(StructuralPathRankerRuntimeRowMatch {
                source: if using_direct_model {
                    "registered_model_artifact"
                } else if using_explicit {
                    "registered_explicit_artifact"
                } else if using_service {
                    "registered_service"
                } else {
                    "registered_artifact"
                },
                row: structural_path_ranker_runtime_row_with_history_gate_metadata(
                    row.clone(),
                    history_gate_metadata_matches.get(&path.path_id),
                ),
            })
        } else if let Some(row) = artifact_history_match {
            artifact_match_count += 1;
            Some(StructuralPathRankerRuntimeRowMatch {
                source: "registered_artifact_history",
                row,
            })
        } else if let Some(row) = artifact_path_matches.get(&path.path_id) {
            artifact_match_count += 1;
            Some(StructuralPathRankerRuntimeRowMatch {
                source: "registered_artifact_path",
                row: structural_path_ranker_runtime_row_with_history_gate_metadata(
                    row.clone(),
                    history_gate_metadata_matches.get(&path.path_id),
                ),
            })
        } else if let Some(row) = exact_matches.get(&path.path_id) {
            candidate_set_match_count += 1;
            Some(StructuralPathRankerRuntimeRowMatch {
                source: "candidate_set",
                row: structural_path_ranker_runtime_row_with_history_gate_metadata(
                    row.clone(),
                    history_gate_metadata_matches.get(&path.path_id),
                ),
            })
        } else if reuse_mode == STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY {
            latest_history_matches
                .get(&path.path_id)
                .cloned()
                .map(|row| {
                    history_match_count += 1;
                    StructuralPathRankerRuntimeRowMatch {
                        source: "history_path",
                        row: structural_path_ranker_runtime_row_with_history_gate_metadata(
                            row,
                            history_gate_metadata_matches.get(&path.path_id),
                        ),
                    }
                })
        } else {
            None
        };

        let Some(matched) = matched else {
            continue;
        };
        let Some(raw_score) = matched.row.raw_path_score else {
            continue;
        };
        let external_signal = matched
            .row
            .path_prob_lower_bound
            .or(matched.row.calibrated_path_prob)
            .or(matched.row.raw_path_score)
            .unwrap_or(raw_score)
            .clamp(0.0, 1.0);
        let blend_weight = if matched.source.starts_with("registered_artifact")
            || matched.source == "registered_explicit_artifact"
        {
            if matched.row.path_prob_lower_bound.is_some() {
                0.45
            } else if matched.row.calibrated_path_prob.is_some() {
                0.35
            } else {
                0.25
            }
        } else if matched.source == "candidate_set" {
            if matched.row.path_prob_lower_bound.is_some() {
                0.35
            } else if matched.row.calibrated_path_prob.is_some() {
                0.25
            } else {
                0.15
            }
        } else if matched.row.path_prob_lower_bound.is_some() {
            0.20
        } else if matched.row.calibrated_path_prob.is_some() {
            0.15
        } else {
            0.10
        };
        let blended_score = ((1.0 - blend_weight) * path.composite_preference_score
            + blend_weight * external_signal)
            .clamp(0.0, 1.0);
        path.catboost_score = Some(raw_score.clamp(0.0, 1.0));
        path.path_ranker_calibrated_path_prob = matched.row.calibrated_path_prob;
        path.path_ranker_path_prob_lower_bound = matched.row.path_prob_lower_bound;
        path.path_ranker_execution_gate_status = matched.row.execution_gate_status.clone();
        path.path_ranker_runtime_source = Some(matched.source.to_string());
        if let Some(value) = matched
            .row
            .score_model_family
            .as_deref()
            .filter(|value| !value.trim().is_empty())
        {
            score_model_families.insert(value.to_string());
        }
        if let Some(value) = matched
            .row
            .score_source_kind
            .as_deref()
            .filter(|value| !value.trim().is_empty())
        {
            score_source_kinds.insert(value.to_string());
        }
        if let Some(value) = matched
            .row
            .score_model_artifact_uri
            .as_deref()
            .filter(|value| !value.trim().is_empty())
        {
            score_model_artifact_uris.insert(value.to_string());
        }
        if let Some(value) = matched
            .row
            .score_generator
            .as_deref()
            .filter(|value| !value.trim().is_empty())
        {
            score_generators.insert(value.to_string());
        }
        path.composite_preference_score =
            if matched.row.execution_gate_status.as_deref() == Some("observe") {
                blended_score.min(path.composite_preference_score)
            } else {
                blended_score
            };
        applied_path_count += 1;
    }

    let single_or_mixed = |values: BTreeSet<String>| -> Option<String> {
        if values.is_empty() {
            None
        } else if values.len() == 1 {
            values.into_iter().next()
        } else {
            Some("mixed".to_string())
        }
    };

    Some(StructuralPathRankerRuntimeSurface {
        enabled: true,
        status: if using_direct_model && artifact_match_count > 0 {
            "using_registered_model_artifact".to_string()
        } else if using_explicit && artifact_match_count > 0 {
            "using_registered_explicit_artifact".to_string()
        } else if using_service && artifact_match_count > 0 {
            "using_registered_service_scores".to_string()
        } else if artifact_match_count > 0 {
            "using_registered_artifact_scores".to_string()
        } else if reuse_mode == STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY
            && history_match_count > 0
        {
            "using_history_scores".to_string()
        } else if candidate_set_match_count > 0 {
            "using_candidate_set_scores".to_string()
        } else if history_match_count > 0 {
            "using_history_scores".to_string()
        } else {
            "enabled_no_matching_scores".to_string()
        },
        reuse_mode: Some(reuse_mode),
        artifact_match_count,
        candidate_set_match_count,
        history_match_count,
        applied_path_count,
        score_model_family: single_or_mixed(score_model_families),
        score_source_kind: single_or_mixed(score_source_kinds),
        score_model_artifact_uri: single_or_mixed(score_model_artifact_uris),
        score_generator: single_or_mixed(score_generators),
    })
}

fn structural_path_ranking_regime_bucket_for_path(
    snapshot: &WorkflowSnapshot,
    path_id: &str,
) -> String {
    let symbol = structural_symbol(snapshot);
    let regime = structural_active_regime(snapshot).unwrap_or_else(|| "unknown".to_string());
    format!("{symbol}:{regime}:{path_id}")
}

fn structural_path_ranking_pending_reward_state(
    path_id: &str,
    feedback_history: &[FeedbackRecord],
) -> String {
    let Some(record) = feedback_history
        .iter()
        .filter(|record| {
            record
                .structural_feedback
                .as_ref()
                .map(|refs| refs.path_id == path_id)
                .unwrap_or(false)
        })
        .max_by_key(|record| record.timestamp)
    else {
        return "unobserved".to_string();
    };
    if structural_feedback_outcome_is_unresolved(&record.realized_outcome) {
        return "pending".to_string();
    }
    if crate::state::structural_feedback_is_infrastructure_negative(record) {
        return "unobserved".to_string();
    }
    let followed = record
        .structural_feedback
        .as_ref()
        .map(|refs| refs.followed_path)
        .unwrap_or(true);
    if !followed
        || record
            .realized_outcome
            .trim()
            .eq_ignore_ascii_case("not_followed")
    {
        return "not_followed".to_string();
    }
    if record
        .realized_outcome
        .trim()
        .eq_ignore_ascii_case("invalidated")
    {
        return "matured_invalidated".to_string();
    }
    match structural_feedback_learning_outcome(record) {
        Some(StructuralFeedbackLearningOutcome::Positive) => "matured_success".to_string(),
        Some(StructuralFeedbackLearningOutcome::Neutral)
        | Some(StructuralFeedbackLearningOutcome::Negative) => "matured_failure".to_string(),
        None => "unobserved".to_string(),
    }
}

pub fn build_structural_recommended_path_bundle_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let structural_prior_state = StructuralPriorLearningState::default();
    let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    );
    let symbol = structural_symbol(snapshot);
    structural_recommended_path_bundle_from_candidates(
        symbol,
        selection.candidate_set_id,
        None,
        structural_current_pre_bayes_regime_profit_branch_path(snapshot).as_deref(),
        selection.candidate_paths,
    )
}

fn structural_recommended_path_bundle_from_candidates(
    symbol: String,
    candidate_set_id: String,
    path_ranker_runtime: Option<StructuralPathRankerRuntimeSurface>,
    current_pre_bayes_branch_path: Option<&str>,
    candidate_paths: Vec<StructuralPathArtifact>,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let candidate_set_size = candidate_paths.len();
    let prefer_history_paths =
        structural_runtime_surface_prefers_history(path_ranker_runtime.as_ref());
    let current_pre_bayes_branch_path =
        current_pre_bayes_branch_path.and_then(structural_normalize_rooted_branch_path);
    let path = current_pre_bayes_branch_path
        .as_deref()
        .and_then(|branch_path| {
            candidate_paths
                .iter()
                .filter(|path| structural_path_matches_current_pre_bayes_branch(path, branch_path))
                .max_by(|left, right| {
                    structural_current_pre_bayes_branch_priority(left)
                        .cmp(&structural_current_pre_bayes_branch_priority(right))
                        .then_with(|| structural_path_selection_order(left, right, false))
                })
        })
        .or_else(|| {
            if prefer_history_paths {
                candidate_paths
                    .iter()
                    .filter(|path| structural_prefer_history_path_priority(path, true) > 0)
                    .max_by(|left, right| structural_path_selection_order(left, right, true))
            } else {
                None
            }
        })
        .or_else(|| {
            candidate_paths
                .iter()
                .filter(|path| path.path_ranker_execution_gate_status.as_deref() == Some("pass"))
                .max_by(|left, right| structural_path_selection_order(left, right, false))
        })
        .or_else(|| candidate_paths.first())?;
    let selected_path_probability = structural_candidate_policy_probability(
        path.composite_preference_score,
        denominator,
        candidate_set_size,
    );
    let why_this_path = structural_why_this_path_summary(path);
    let selected_path_id = structural_normalize_rooted_branch_path(&path.path_id)
        .unwrap_or_else(|| path.path_id.clone());
    let selected_path_label = if selected_path_id != path.path_id {
        selected_path_id.clone()
    } else {
        path.path_label.clone()
    };
    Some(StructuralRecommendedPathBundleArtifact {
        symbol,
        rank: 1,
        candidate_set_id,
        candidate_set_size,
        path_ranker_runtime,
        selected_path_probability,
        path_id: selected_path_id,
        scenario_id: path.scenario_id.clone(),
        path_label: selected_path_label,
        direction: path.direction.clone(),
        experience_prior: path.path_prior,
        current_posterior: path.path_posterior,
        composite_score: path.composite_preference_score,
        historical_total_records: path.historical_total_records,
        historical_invalidation_rate: path.historical_invalidation_rate,
        path_ranker_raw_score: path.catboost_score,
        path_ranker_calibrated_path_prob: path.path_ranker_calibrated_path_prob,
        path_ranker_path_prob_lower_bound: path.path_ranker_path_prob_lower_bound,
        path_ranker_execution_gate_status: path.path_ranker_execution_gate_status.clone(),
        path_ranker_runtime_source: path.path_ranker_runtime_source.clone(),
        why_this_path,
        trigger_summary: structural_short_rule_summary(
            &path.trigger_conditions,
            "trigger_not_available",
        ),
        confirmation_summary: structural_short_rule_summary(
            &path.confirmation_conditions,
            "confirmation_not_available",
        ),
        stop_summary: structural_scalar_rule_summary(&path.stop_definition, "stop_not_available"),
        invalidation_summary: structural_short_rule_summary(
            &path.invalidation_conditions,
            "invalidation_not_available",
        ),
        recommended_command: path.recommended_command.clone(),
    })
}

fn structural_runtime_surface_prefers_history(
    runtime: Option<&StructuralPathRankerRuntimeSurface>,
) -> bool {
    runtime
        .and_then(|runtime| runtime.reuse_mode.as_deref())
        .is_some_and(|mode| mode == STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY)
}

fn structural_current_pre_bayes_regime_profit_branch_path(
    snapshot: &WorkflowSnapshot,
) -> Option<String> {
    snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| {
            phase
                .pre_bayes_filtered_assignments
                .get("regime_profit_branch_path")
        })
        .and_then(|path| structural_normalize_branch_path(path))
}

fn structural_normalize_branch_path(raw: &str) -> Option<String> {
    let path = raw
        .trim()
        .replace("_->_", " -> ")
        .replace("->", " -> ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");
    if path.contains(" -> ") {
        Some(path)
    } else {
        None
    }
}

fn structural_normalize_rooted_branch_path(raw: &str) -> Option<String> {
    let path = structural_normalize_branch_path(raw)?;
    let parts = path
        .split(" -> ")
        .map(str::trim)
        .filter(|part| !part.is_empty())
        .collect::<Vec<_>>();
    let root_start = parts
        .iter()
        .position(|part| structural_is_regime_root_label(part))?;
    if root_start == 0 {
        Some(path)
    } else {
        Some(parts[root_start..].join(" -> "))
    }
}

fn structural_is_regime_root_label(label: &str) -> bool {
    matches!(
        label,
        "Bull"
            | "Bear"
            | "Sideways"
            | "Crisis"
            | "Transition"
            | "SessionRhythm"
            | "TrendExpansion"
            | "RangeExpansion"
            | "RangeConsolidation"
            | "RangeReversion"
    )
}

fn structural_path_matches_current_pre_bayes_branch(
    path: &StructuralPathArtifact,
    current_pre_bayes_branch_path: &str,
) -> bool {
    structural_normalize_rooted_branch_path(&path.path_id).as_deref()
        == Some(current_pre_bayes_branch_path)
}

fn structural_current_pre_bayes_branch_priority(path: &StructuralPathArtifact) -> u8 {
    let exact_branch_shape = !path.path_id.starts_with("path:") && path.path_id.contains(" -> ");
    if !exact_branch_shape {
        return 0;
    }
    if path.historical_total_records >= 30 {
        3
    } else if path.catboost_score.is_some()
        || path.path_ranker_calibrated_path_prob.is_some()
        || path.path_ranker_path_prob_lower_bound.is_some()
        || path.path_ranker_runtime_source.is_some()
    {
        2
    } else {
        1
    }
}

fn structural_path_runtime_source_is_history(source: Option<&str>) -> bool {
    matches!(source, Some("history_path" | "registered_artifact_history"))
}

fn structural_current_auto_quant_material_rank_path_priority(path: &StructuralPathArtifact) -> u8 {
    let runtime_source = path.path_ranker_runtime_source.as_deref();
    let exact_branch_shape = !path.path_id.starts_with("path:") && path.path_id.contains(" -> ");
    if path.entry_style == "auto_quant_agent_material_rank"
        && exact_branch_shape
        && path.catboost_score.is_some()
        && runtime_source.is_some()
        && !structural_path_runtime_source_is_history(runtime_source)
    {
        3
    } else {
        0
    }
}

fn structural_prefer_history_path_priority(
    path: &StructuralPathArtifact,
    prefer_history_paths: bool,
) -> u8 {
    if !prefer_history_paths {
        return 0;
    }
    let current_auto_quant_material_rank_priority =
        structural_current_auto_quant_material_rank_path_priority(path);
    if current_auto_quant_material_rank_priority > 0 {
        return current_auto_quant_material_rank_priority;
    }
    if structural_observed_feedback_branch_priority(path) >= 2 {
        return 4;
    }
    let runtime_source = path.path_ranker_runtime_source.as_deref();
    let has_runtime_score = path.catboost_score.is_some()
        || path.path_ranker_calibrated_path_prob.is_some()
        || path.path_ranker_path_prob_lower_bound.is_some()
        || runtime_source.is_some();
    if structural_path_runtime_source_is_history(runtime_source) {
        3
    } else if runtime_source == Some("persisted_feedback_target") {
        4
    } else if structural_exact_feedback_path_priority(path) == 0 && runtime_source.is_some() {
        2
    } else if structural_exact_feedback_path_priority(path) == 0 && has_runtime_score {
        1
    } else {
        0
    }
}

fn structural_path_selection_score(path: &StructuralPathArtifact) -> f64 {
    path.path_ranker_path_prob_lower_bound
        .or(path.path_ranker_calibrated_path_prob)
        .or(path.catboost_score)
        .unwrap_or(path.composite_preference_score)
}

fn structural_branch_family_prefix(path: &StructuralPathArtifact) -> Option<(String, String)> {
    let mut parts = path
        .path_id
        .split(" -> ")
        .map(str::trim)
        .filter(|part| !part.is_empty());
    let first = parts.next()?.to_string();
    let second = parts.next()?.to_string();
    Some((first, second))
}

fn structural_is_provider_specific_exact_path(path: &StructuralPathArtifact) -> bool {
    let lowered = path.path_id.to_ascii_lowercase();
    lowered.contains("_tvr_")
        || lowered.contains("_ibkr_")
        || lowered.contains("_yf_")
        || lowered.contains("_kraken_")
}

fn structural_should_include_feedback_paths(
    prefer_history_runtime: bool,
    regime_bundle_candidates: &[StructuralPathArtifact],
    feedback_candidates: &[StructuralPathArtifact],
) -> bool {
    if prefer_history_runtime || regime_bundle_candidates.is_empty() {
        return true;
    }
    let bundle_families = regime_bundle_candidates
        .iter()
        .filter_map(structural_branch_family_prefix)
        .collect::<BTreeSet<_>>();
    feedback_candidates.iter().any(|path| {
        structural_branch_family_prefix(path).is_some_and(|family| {
            bundle_families.contains(&family)
                && (structural_exact_feedback_path_priority(path) == 0
                    || structural_is_provider_specific_exact_path(path))
        })
    })
}

fn structural_path_selection_order(
    left: &StructuralPathArtifact,
    right: &StructuralPathArtifact,
    prefer_history_paths: bool,
) -> std::cmp::Ordering {
    let left_score = structural_path_selection_score(left);
    let right_score = structural_path_selection_score(right);
    let near_tied = (left_score - right_score).abs() <= 0.01;
    let same_branch_family =
        structural_branch_family_prefix(left) == structural_branch_family_prefix(right);
    structural_prefer_history_path_priority(left, prefer_history_paths)
        .cmp(&structural_prefer_history_path_priority(
            right,
            prefer_history_paths,
        ))
        .then_with(|| {
            structural_observed_feedback_branch_priority(left)
                .cmp(&structural_observed_feedback_branch_priority(right))
        })
        .then_with(|| structural_observed_exact_path_order(left, right))
        .then_with(|| {
            if near_tied && same_branch_family {
                structural_is_provider_specific_exact_path(left)
                    .cmp(&structural_is_provider_specific_exact_path(right))
            } else {
                std::cmp::Ordering::Equal
            }
        })
        .then_with(|| left_score.total_cmp(&right_score))
        .then_with(|| {
            left.composite_preference_score
                .total_cmp(&right.composite_preference_score)
        })
        .then_with(|| left.path_posterior.total_cmp(&right.path_posterior))
        .then_with(|| left.path_prior.total_cmp(&right.path_prior))
}

fn structural_observed_exact_path_order(
    left: &StructuralPathArtifact,
    right: &StructuralPathArtifact,
) -> std::cmp::Ordering {
    let left_exact = structural_is_provider_specific_exact_path(left);
    let right_exact = structural_is_provider_specific_exact_path(right);
    if left_exact == right_exact {
        return std::cmp::Ordering::Equal;
    }
    if left_exact && left.historical_total_records > right.historical_total_records {
        return std::cmp::Ordering::Greater;
    }
    if right_exact && right.historical_total_records > left.historical_total_records {
        return std::cmp::Ordering::Less;
    }
    std::cmp::Ordering::Equal
}

fn structural_observed_feedback_branch_priority(path: &StructuralPathArtifact) -> u8 {
    let exact_branch_shape = !path.path_id.starts_with("path:") && path.path_id.contains(" -> ");
    if exact_branch_shape
        && path.entry_style == "structural_feedback_path"
        && path.historical_total_records >= 30
    {
        2
    } else if exact_branch_shape
        && path.entry_style == "structural_feedback_path"
        && path.historical_total_records > 0
    {
        1
    } else {
        0
    }
}

pub fn build_structural_recommended_path_bundle_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    build_structural_recommended_path_bundle_artifact_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        StructuralPathRankerRuntimeContext::default(),
    )
}

pub fn build_structural_recommended_path_bundle_artifact_with_state_dir_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    state_dir: Option<&str>,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    build_structural_recommended_path_bundle_artifact_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        StructuralPathRankerRuntimeContext { state_dir },
    )
}

pub(crate) fn build_structural_recommended_path_bundle_artifact_with_runtime_context_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    runtime_context: StructuralPathRankerRuntimeContext<'_>,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
        runtime_context,
    );
    let symbol = structural_symbol(snapshot);
    structural_recommended_path_bundle_from_candidates(
        symbol,
        selection.candidate_set_id,
        selection.runtime,
        structural_current_pre_bayes_regime_profit_branch_path(snapshot).as_deref(),
        selection.candidate_paths,
    )
}

pub fn build_structural_node_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
) -> StructuralNodeArtifact {
    build_structural_node_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_node_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralNodeArtifact {
    let symbol = structural_symbol(snapshot);
    let command = top_level_command(snapshot);
    let support_reason = structural_support_reason(snapshot);
    let provider_support =
        build_workflow_provider_support(provider_status_agent, &command, support_reason.as_deref());
    let supporting_evidence = structural_supporting_evidence(snapshot, &provider_support);
    let active_regime = structural_active_regime(snapshot);
    let node_family = if structural_no_workflow_state(snapshot) {
        "bootstrap".to_string()
    } else if active_regime.is_some() {
        "belief_regime_node".to_string()
    } else if provider_support.active {
        "provider_gate".to_string()
    } else if support_reason.as_deref() == Some("user_selected_historical_data_missing") {
        "data_selection_gate".to_string()
    } else if structural_hard_block_active(snapshot) {
        "workflow_gate".to_string()
    } else {
        structural_focus_phase(snapshot)
    };
    let node_label = if structural_no_workflow_state(snapshot) {
        "no_workflow_state".to_string()
    } else if let Some(active_regime) = active_regime.as_ref() {
        active_regime.to_string()
    } else if provider_support.active
        || support_reason.as_deref() == Some("user_selected_historical_data_missing")
        || structural_hard_block_active(snapshot)
    {
        support_reason
            .clone()
            .filter(|value| !value.is_empty() && value != "none")
            .unwrap_or_else(|| "actionable".to_string())
    } else {
        "actionable".to_string()
    };
    let provisional_node_id = format!("{symbol}:{node_family}:{node_label}");
    let node_duration_prior = structural_prior_state
        .node_duration_priors
        .get(&provisional_node_id);
    let node_temporal_state = structural_prior_state
        .node_temporal_posteriors
        .get(&provisional_node_id);
    let posterior_confidence = if node_family == "belief_regime_node" {
        blend_node_posterior_with_duration_prior(
            structural_primary_probability(snapshot),
            node_duration_prior,
            node_temporal_state,
        )
    } else {
        structural_primary_probability(snapshot)
    };
    let belief_prior = structural_resolved_smoothed_prior(
        structural_prior_state.nodes.get(&provisional_node_id),
        structural_prior_state,
        structural_primary_prior(snapshot),
    );
    StructuralNodeArtifact {
        node_id: provisional_node_id,
        node_family,
        node_label,
        focus_phase: structural_focus_phase(snapshot),
        market_context: structural_market_context(snapshot),
        timeframe_scope: structural_timeframe_scope(snapshot),
        supporting_evidence,
        invalidating_evidence: structural_invalidating_evidence(snapshot, &provider_support),
        belief_prior,
        belief_posterior: posterior_confidence,
        posterior_confidence,
        origin_artifacts: structural_origin_artifacts(snapshot),
    }
}

pub fn build_structural_branch_set_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    node: &StructuralNodeArtifact,
    branch_history: &StructuralBranchHistoryArtifact,
) -> StructuralBranchSetArtifact {
    build_structural_branch_set_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        node,
        branch_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_branch_set_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    node: &StructuralNodeArtifact,
    branch_history: &StructuralBranchHistoryArtifact,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralBranchSetArtifact {
    let command = top_level_command(snapshot);
    let support_reason = structural_support_reason(snapshot);
    let provider_support =
        build_workflow_provider_support(provider_status_agent, &command, support_reason.as_deref());
    let mut branches = Vec::new();
    if structural_no_workflow_state(snapshot) {
        branches.push(StructuralBranchArtifact {
            branch_id: format!("{}:bootstrap_collect_inputs", node.node_id),
            target_node_id: format!("{}:bootstrap_ready", structural_symbol(snapshot)),
            branch_label: "collect_initial_inputs".to_string(),
            prior_probability: 1.0,
            transition_prior: None,
            transition_weighted_observation_mass: None,
            transition_outcome_support: None,
            transition_temporal_posterior_support: None,
            posterior_probability: 1.0,
            historical_total_records: 0,
            historical_followed_count: 0,
            historical_win_rate: None,
            historical_invalidation_rate: None,
            historical_avg_pnl: None,
            composite_branch_score: 1.0,
            activation_conditions: vec!["No workflow snapshot exists yet.".to_string()],
            failure_conditions: vec![
                "Required market data or state inputs stay missing.".to_string()
            ],
            supporting_evidence: vec!["workflow_status has no persisted phase state".to_string()],
        });
    } else if provider_support.active && structural_active_regime(snapshot).is_none() {
        branches.push(StructuralBranchArtifact {
            branch_id: format!("{}:resolve_provider_gate", node.node_id),
            target_node_id: format!("{}:provider_ready", structural_symbol(snapshot)),
            branch_label: "resolve_provider_prerequisites".to_string(),
            prior_probability: 0.7,
            transition_prior: None,
            transition_weighted_observation_mass: None,
            transition_outcome_support: None,
            transition_temporal_posterior_support: None,
            posterior_probability: 0.7,
            historical_total_records: 0,
            historical_followed_count: 0,
            historical_win_rate: None,
            historical_invalidation_rate: None,
            historical_avg_pnl: None,
            composite_branch_score: 0.7,
            activation_conditions: provider_support.pending_providers.clone(),
            failure_conditions: vec!["User declines provider/runtime setup.".to_string()],
            supporting_evidence: provider_support
                .install_prompts
                .iter()
                .take(2)
                .cloned()
                .collect(),
        });
        branches.push(StructuralBranchArtifact {
            branch_id: format!("{}:defer_external_runtime", node.node_id),
            target_node_id: format!("{}:observe_only", structural_symbol(snapshot)),
            branch_label: "defer_and_observe".to_string(),
            prior_probability: 0.3,
            transition_prior: None,
            transition_weighted_observation_mass: None,
            transition_outcome_support: None,
            transition_temporal_posterior_support: None,
            posterior_probability: 0.3,
            historical_total_records: 0,
            historical_followed_count: 0,
            historical_win_rate: None,
            historical_invalidation_rate: None,
            historical_avg_pnl: None,
            composite_branch_score: 0.3,
            activation_conditions: vec!["Provider runtime is optional for this path.".to_string()],
            failure_conditions: vec!["Execution requires unavailable external runtime.".to_string()],
            supporting_evidence: vec!["zero_config_fallback_may_still_exist".to_string()],
        });
    } else if support_reason.as_deref() == Some("user_selected_historical_data_missing")
        && structural_active_regime(snapshot).is_none()
    {
        branches.push(StructuralBranchArtifact {
            branch_id: format!("{}:choose_historical_dataset", node.node_id),
            target_node_id: format!("{}:research_ready", structural_symbol(snapshot)),
            branch_label: "choose_historical_dataset".to_string(),
            prior_probability: 0.75,
            transition_prior: None,
            transition_weighted_observation_mass: None,
            transition_outcome_support: None,
            transition_temporal_posterior_support: None,
            posterior_probability: 0.75,
            historical_total_records: 0,
            historical_followed_count: 0,
            historical_win_rate: None,
            historical_invalidation_rate: None,
            historical_avg_pnl: None,
            composite_branch_score: 0.75,
            activation_conditions: recommended_next_command_meta(&command).recorded_data_paths,
            failure_conditions: vec!["User does not confirm a valid dataset path.".to_string()],
            supporting_evidence: snapshot.blocking_truth.evidence.clone(),
        });
    } else {
        let regime_probabilities = structural_regime_probabilities(snapshot);
        let latest_feedback = structural_latest_feedback_refs(snapshot);
        let adjusted_posteriors = transition_adjusted_branch_posteriors(
            &node.node_id,
            &regime_probabilities,
            latest_feedback.as_ref().map(|refs| refs.branch_id.as_str()),
            &structural_prior_state.branch_transition_priors,
            &structural_prior_state.branch_temporal_posteriors,
            structural_branch_label_for_regime,
        );
        if !regime_probabilities.is_empty() {
            for (regime, probability) in regime_probabilities {
                let branch_label = structural_branch_label_for_regime(regime.as_str());
                let branch_id = format!("{}:{}", node.node_id, branch_label);
                let historical_summary = branch_history
                    .branches
                    .iter()
                    .find(|branch| branch.branch_id == branch_id);
                let history_adjusted_prior =
                    structural_history_adjusted_branch_prior(probability, historical_summary);
                let prior_stats = structural_prior_state.branches.get(&branch_id);
                let transition_prior = latest_feedback.as_ref().and_then(|refs| {
                    structural_branch_transition_prior(
                        structural_prior_state,
                        &refs.branch_id,
                        &branch_id,
                    )
                });
                let posterior_probability = adjusted_posteriors
                    .get(&branch_id)
                    .copied()
                    .unwrap_or(probability);
                let resolved_prior = structural_resolved_smoothed_prior(
                    prior_stats,
                    structural_prior_state,
                    history_adjusted_prior,
                );
                let blended_prior = blend_branch_prior_with_transition_prior(
                    resolved_prior,
                    transition_prior,
                    latest_feedback.as_ref().and_then(|refs| {
                        structural_prior_state
                            .branch_temporal_posteriors
                            .get(&format!("{}=>{}", refs.branch_id, branch_id))
                    }),
                );
                let branch_temporal_state = latest_feedback.as_ref().and_then(|refs| {
                    structural_prior_state
                        .branch_temporal_posteriors
                        .get(&format!("{}=>{}", refs.branch_id, branch_id))
                });
                branches.push(StructuralBranchArtifact {
                    branch_id,
                    target_node_id: format!("{}:{}:candidate", structural_symbol(snapshot), regime),
                    branch_label: branch_label.to_string(),
                    prior_probability: blended_prior,
                    transition_prior: transition_prior.map(|item| item.transition_prior),
                    transition_weighted_observation_mass: branch_temporal_state
                        .map(|state| state.weighted_observation_mass)
                        .or_else(|| transition_prior.map(|item| item.weighted_observation_mass)),
                    transition_outcome_support: branch_temporal_state
                        .map(|state| state.transition_outcome_support)
                        .or_else(|| transition_prior.map(|item| item.transition_outcome_support)),
                    transition_temporal_posterior_support: branch_temporal_state
                        .map(|state| state.temporal_posterior_support)
                        .or_else(|| transition_prior.map(|item| item.temporal_posterior_support)),
                    posterior_probability,
                    historical_total_records: structural_resolved_observations(
                        prior_stats,
                        historical_summary.map(|summary| summary.total_records).unwrap_or(0),
                    ),
                    historical_followed_count: structural_resolved_followed_count(
                        prior_stats,
                        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
                    ),
                    historical_win_rate: structural_resolved_branch_win_rate(
                        prior_stats,
                        historical_summary,
                    ),
                    historical_invalidation_rate: structural_resolved_branch_invalidation_rate(
                        prior_stats,
                        historical_summary,
                    ),
                    historical_avg_pnl: structural_resolved_avg_pnl(
                        prior_stats,
                        historical_summary.map(|summary| summary.avg_pnl),
                    ),
                    composite_branch_score: structural_composite_preference_score(
                        posterior_probability,
                        blended_prior,
                    ),
                    activation_conditions: vec![format!("regime_posterior={regime}:{probability:.3}")],
                    failure_conditions: vec![format!(
                        "regime branch {regime} loses posterior support or invalidates before trigger"
                    )],
                    supporting_evidence: structural_regime_supporting_evidence(
                        snapshot,
                        &provider_support,
                        regime.as_str(),
                        probability,
                    ),
                });
            }
        } else {
            branches.push(StructuralBranchArtifact {
                branch_id: format!("{}:execute_recommended_path", node.node_id),
                target_node_id: format!("{}:next_phase", structural_symbol(snapshot)),
                branch_label: "execute_recommended_path".to_string(),
                prior_probability: 0.6,
                transition_prior: None,
                transition_weighted_observation_mass: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
                posterior_probability: structural_primary_probability(snapshot),
                historical_total_records: 0,
                historical_followed_count: 0,
                historical_win_rate: None,
                historical_invalidation_rate: None,
                historical_avg_pnl: None,
                composite_branch_score: structural_primary_probability(snapshot),
                activation_conditions: vec![command.clone()],
                failure_conditions: vec!["Recommended path invalidates before trigger.".to_string()],
                supporting_evidence: structural_supporting_evidence(snapshot, &provider_support),
            });
            branches.push(StructuralBranchArtifact {
                branch_id: format!("{}:observe_only", node.node_id),
                target_node_id: format!("{}:observe_only", structural_symbol(snapshot)),
                branch_label: "observe_only".to_string(),
                prior_probability: 0.4,
                transition_prior: None,
                transition_weighted_observation_mass: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
                posterior_probability: (1.0 - structural_primary_probability(snapshot))
                    .clamp(0.0, 1.0),
                historical_total_records: 0,
                historical_followed_count: 0,
                historical_win_rate: None,
                historical_invalidation_rate: None,
                historical_avg_pnl: None,
                composite_branch_score: (1.0 - structural_primary_probability(snapshot))
                    .clamp(0.0, 1.0),
                activation_conditions: vec!["Confidence remains mixed or weak.".to_string()],
                failure_conditions: vec![
                    "Missed high-conviction trigger while observing.".to_string()
                ],
                supporting_evidence: snapshot.risk_flags.iter().take(2).cloned().collect(),
            });
        }
    }
    StructuralBranchSetArtifact {
        from_node_id: node.node_id.clone(),
        branches,
    }
}

pub fn build_structural_scenario_playbook_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    branches: &StructuralBranchSetArtifact,
    scenario_history: &StructuralScenarioHistoryArtifact,
) -> StructuralScenarioPlaybookArtifact {
    build_structural_scenario_playbook_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        branches,
        scenario_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_scenario_playbook_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    branches: &StructuralBranchSetArtifact,
    scenario_history: &StructuralScenarioHistoryArtifact,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralScenarioPlaybookArtifact {
    let command = top_level_command(snapshot);
    let support_reason = structural_support_reason(snapshot);
    let provider_support =
        build_workflow_provider_support(provider_status_agent, &command, support_reason.as_deref());
    let scenarios = branches
        .branches
        .iter()
        .map(|branch| {
            let (scenario_label, narrative) = if branch.branch_label == "collect_initial_inputs" {
                (
                    "bootstrap_readiness".to_string(),
                    "Collect the minimum inputs needed to create the first workflow state."
                        .to_string(),
                )
            } else if branch.branch_label == "resolve_provider_prerequisites" {
                (
                    "provider_runtime_enablement".to_string(),
                    format!(
                        "Enable the missing provider/runtime track before attempting the dependent path: {}.",
                        provider_support.pending_providers.join(", ")
                    ),
                )
            } else if branch.branch_label == "choose_historical_dataset" {
                (
                    "historical_dataset_selection".to_string(),
                    "Ask the user to choose the approved historical dataset before research/backtest continues."
                        .to_string(),
                )
            } else if branch.branch_label == "trend_follow_through" {
                (
                    "trend_follow_through".to_string(),
                    "Continuation branch: wait for aligned confirmation, then follow the dominant directional path."
                        .to_string(),
                )
            } else if branch.branch_label == "transition_confirmation" {
                (
                    "transition_confirmation".to_string(),
                    "Transition branch: wait for resolution evidence before committing to the next directional leg."
                        .to_string(),
                )
            } else if branch.branch_label == "range_mean_reversion" {
                (
                    "range_mean_reversion".to_string(),
                    "Range branch: fade extremes only after explicit confirmation and invalidation boundaries are known."
                        .to_string(),
                )
            } else if branch.branch_label == "stress_de_risk" {
                (
                    "stress_de_risk".to_string(),
                    "Stress branch: preserve capital, reduce aggression, and require stronger confirmation."
                        .to_string(),
                )
            } else if branch.branch_label == "observe_only" {
                (
                    "observe_and_wait".to_string(),
                    "Stay flat and wait for cleaner structural confirmation.".to_string(),
                )
            } else {
                (
                    "recommended_execution".to_string(),
                    "Follow the current recommended command path while monitoring invalidation pressure."
                        .to_string(),
                )
            };
            let scenario_id = format!("scenario:{}", branch.branch_id);
            let historical_summary = scenario_history
                .scenarios
                .iter()
                .find(|scenario| scenario.scenario_id == scenario_id);
            let history_adjusted_prior =
                structural_history_adjusted_scenario_prior(
                    branch.posterior_probability,
                    historical_summary,
                );
            let prior_stats = structural_prior_state.scenarios.get(&scenario_id);
            StructuralScenarioArtifact {
                scenario_id: scenario_id.clone(),
                branch_id: branch.branch_id.clone(),
                scenario_label,
                narrative,
                prior_probability: structural_resolved_smoothed_prior(
                    prior_stats,
                    structural_prior_state,
                    history_adjusted_prior,
                ),
                posterior_probability: branch.posterior_probability,
                historical_total_records: structural_resolved_observations(
                    prior_stats,
                    historical_summary.map(|summary| summary.total_records).unwrap_or(0),
                ),
                historical_followed_count: structural_resolved_followed_count(
                    prior_stats,
                    historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
                ),
                historical_win_rate: structural_resolved_scenario_win_rate(
                    prior_stats,
                    historical_summary,
                ),
                historical_invalidation_rate: structural_resolved_scenario_invalidation_rate(
                    prior_stats,
                    historical_summary,
                ),
                historical_avg_pnl: structural_resolved_avg_pnl(
                    prior_stats,
                    historical_summary.map(|summary| summary.avg_pnl),
                ),
                composite_scenario_score: structural_composite_preference_score(
                    branch.posterior_probability,
                    structural_resolved_smoothed_prior(
                        prior_stats,
                        structural_prior_state,
                        history_adjusted_prior,
                    ),
                ),
                required_confirmations: branch.activation_conditions.clone(),
                hard_invalidations: branch.failure_conditions.clone(),
                timing_constraints: vec!["re-evaluate on the next workflow refresh".to_string()],
                path_ids: vec![format!("path:{scenario_id}:primary")],
            }
        })
        .collect::<Vec<_>>();
    StructuralScenarioPlaybookArtifact { scenarios }
}

pub fn build_structural_path_plan_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenarios: &StructuralScenarioPlaybookArtifact,
    feedback_history: &[FeedbackRecord],
    path_history: &StructuralPathHistoryArtifact,
) -> StructuralPathPlanArtifact {
    build_structural_path_plan_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        provider_support,
        scenarios,
        feedback_history,
        path_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_path_plan_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenarios: &StructuralScenarioPlaybookArtifact,
    feedback_history: &[FeedbackRecord],
    path_history: &StructuralPathHistoryArtifact,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralPathPlanArtifact {
    build_structural_path_plan_artifact_with_runtime_context_and_prior_state(
        StructuralPathPlanArtifactInput {
            snapshot,
            provider_status_agent,
            provider_support,
            scenarios,
            feedback_history,
            path_history,
            structural_prior_state,
            runtime_context: StructuralPathRankerRuntimeContext::default(),
        },
    )
}

pub(crate) struct StructuralPathPlanArtifactInput<'a> {
    pub snapshot: &'a WorkflowSnapshot,
    pub provider_status_agent: &'a ProviderCatalogAgentSurface,
    pub provider_support: &'a crate::application::provider_catalog::WorkflowProviderSupportSurface,
    pub scenarios: &'a StructuralScenarioPlaybookArtifact,
    pub feedback_history: &'a [FeedbackRecord],
    pub path_history: &'a StructuralPathHistoryArtifact,
    pub structural_prior_state: &'a StructuralPriorLearningState,
    pub runtime_context: StructuralPathRankerRuntimeContext<'a>,
}

pub(crate) fn build_structural_path_plan_artifact_with_runtime_context_and_prior_state(
    input: StructuralPathPlanArtifactInput<'_>,
) -> StructuralPathPlanArtifact {
    let StructuralPathPlanArtifactInput {
        snapshot,
        provider_status_agent,
        provider_support,
        scenarios,
        feedback_history,
        path_history,
        structural_prior_state,
        runtime_context,
    } = input;
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    let symbol = structural_symbol(snapshot);
    let mut paths = scenarios
        .scenarios
        .iter()
        .map(|scenario| {
            let path_id = format!("path:{}:primary", scenario.scenario_id);
            let historical_summary = path_history
                .paths
                .iter()
                .find(|path| path.path_id == path_id);
            let selected_entry_quality = structural_selected_entry_quality(snapshot);
            let selected_entry_quality_probability =
                structural_selected_entry_quality_probability(snapshot);
            let pre_bayes_gate_status = structural_pre_bayes_gate_status(snapshot);
            let multi_timeframe_direction_bias =
                structural_multi_timeframe_direction_bias(snapshot);
            let execution_candidate_status = snapshot
                .latest_execution_candidate
                .as_ref()
                .map(|candidate| candidate.candidate_status.clone())
                .filter(|value| !value.trim().is_empty());
            let execution_candidate_artifact_id = snapshot
                .latest_execution_candidate
                .as_ref()
                .map(|candidate| candidate.artifact_id.clone());
            let base_prior = structural_primary_prior(snapshot);
            let history_adjusted_prior =
                structural_history_adjusted_path_prior(base_prior, historical_summary);
            let prior_stats = structural_prior_state.paths.get(&path_id);
            let resolved_prior = structural_resolved_smoothed_prior(
                prior_stats,
                structural_prior_state,
                history_adjusted_prior,
            );
            let composite_preference_score = structural_composite_preference_score(
                structural_posterior_confidence(snapshot),
                resolved_prior,
            );
            StructuralPathArtifact {
                path_id,
                scenario_id: scenario.scenario_id.clone(),
                path_label: scenario.scenario_label.clone(),
                direction: structural_direction(snapshot),
                entry_style: structural_entry_style(snapshot, scenario),
                selected_entry_quality,
                selected_entry_quality_probability,
                pre_bayes_gate_status,
                multi_timeframe_direction_bias,
                execution_candidate_status,
                execution_candidate_artifact_id,
                execution_readiness: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_readiness),
                prediction_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.prediction_edge_share),
                execution_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_edge_share),
                historical_total_records: structural_resolved_observations(
                    prior_stats,
                    historical_summary
                        .map(|summary| summary.total_records)
                        .unwrap_or(0),
                ),
                historical_followed_count: structural_resolved_followed_count(
                    prior_stats,
                    historical_summary
                        .map(|summary| summary.followed_count)
                        .unwrap_or(0),
                ),
                execution_propensity: structural_prior_execution_propensity(prior_stats),
                historical_win_rate: structural_resolved_path_win_rate(
                    prior_stats,
                    historical_summary,
                ),
                historical_invalidation_rate: structural_resolved_path_invalidation_rate(
                    prior_stats,
                    historical_summary,
                ),
                historical_avg_pnl: structural_resolved_avg_pnl(
                    prior_stats,
                    historical_summary.map(|summary| summary.avg_pnl),
                ),
                trigger_conditions: structural_trigger_conditions(snapshot, scenario),
                confirmation_conditions: structural_confirmation_conditions(
                    snapshot,
                    provider_support,
                    &next_meta,
                ),
                stop_definition: structural_stop_definition(snapshot, provider_support, scenario),
                target_definition: structural_target_definition(snapshot, &command, scenario),
                invalidation_conditions: structural_invalidation_conditions(snapshot, scenario),
                expected_failure_mode: structural_failure_mode(provider_support, scenario),
                max_time_in_trade: "re-evaluate on next structural node update".to_string(),
                path_prior: resolved_prior,
                path_posterior: structural_posterior_confidence(snapshot),
                bbn_support_score: structural_posterior_confidence(snapshot),
                catboost_score: None,
                path_ranker_calibrated_path_prob: None,
                path_ranker_path_prob_lower_bound: None,
                path_ranker_execution_gate_status: None,
                path_ranker_runtime_source: None,
                composite_preference_score,
                recommended_command: next_meta.executable_command.clone().or_else(|| {
                    if command.trim().is_empty() {
                        None
                    } else {
                        Some(command.clone())
                    }
                }),
            }
        })
        .collect::<Vec<_>>();
    let regime_bundle_candidates =
        structural_regime_bundle_branch_path_candidates(snapshot, structural_prior_state);
    let feedback_candidates = structural_feedback_path_candidates(
        snapshot,
        feedback_history,
        path_history,
        structural_prior_state,
    );
    let mut seen_path_ids = paths
        .iter()
        .map(|path| path.path_id.clone())
        .collect::<BTreeSet<_>>();
    for branch_path in regime_bundle_candidates.iter().cloned() {
        if seen_path_ids.insert(branch_path.path_id.clone()) {
            paths.push(branch_path);
        }
    }
    let prefer_history_runtime =
        structural_runtime_context_prefers_history(&runtime_context, &symbol);
    let include_feedback_paths = structural_should_include_feedback_paths(
        prefer_history_runtime,
        &regime_bundle_candidates,
        &feedback_candidates,
    );
    if include_feedback_paths {
        for feedback_path in feedback_candidates {
            if seen_path_ids.insert(feedback_path.path_id.clone()) {
                paths.push(feedback_path);
            }
        }
    }
    let mut persisted_feedback_paths = Vec::new();
    if prefer_history_runtime {
        persisted_feedback_paths =
            structural_persisted_exact_feedback_target_rows(runtime_context.state_dir, &symbol)
                .iter()
                .filter_map(|row| {
                    structural_persisted_exact_feedback_candidate_from_row(snapshot, row)
                })
                .collect();
        for persisted_feedback_path in persisted_feedback_paths.iter().cloned() {
            if seen_path_ids.insert(persisted_feedback_path.path_id.clone()) {
                paths.push(persisted_feedback_path);
            } else if let Some(existing) = paths
                .iter_mut()
                .find(|path| path.path_id == persisted_feedback_path.path_id)
            {
                *existing = persisted_feedback_path;
            }
        }
    }
    let auto_quant_material_rank_rows =
        structural_current_auto_quant_material_rank_target_rows(runtime_context.state_dir, &symbol);
    for material_rank_path in auto_quant_material_rank_rows
        .iter()
        .filter_map(|row| structural_auto_quant_material_rank_candidate_from_row(snapshot, row))
    {
        if seen_path_ids.insert(material_rank_path.path_id.clone()) {
            paths.push(material_rank_path);
        }
    }
    paths.sort_by(|left, right| structural_path_plan_order(left, right, include_feedback_paths));
    let mut top_candidate_paths = structural_required_candidate_paths(snapshot, paths.clone(), 3);
    let mut top_seen_path_ids = top_candidate_paths
        .iter()
        .map(|path| path.path_id.clone())
        .collect::<BTreeSet<_>>();
    for persisted_feedback_path in persisted_feedback_paths {
        if top_seen_path_ids.insert(persisted_feedback_path.path_id.clone()) {
            top_candidate_paths.push(persisted_feedback_path);
        } else if let Some(existing) = top_candidate_paths
            .iter_mut()
            .find(|path| path.path_id == persisted_feedback_path.path_id)
        {
            *existing = persisted_feedback_path;
        }
    }
    let candidate_set_id = structural_candidate_set_id(&symbol, &top_candidate_paths);
    let mut current_candidate_rows = structural_path_ranking_target_artifact_from_candidates(
        snapshot,
        feedback_history,
        structural_prior_state,
        top_candidate_paths.clone(),
        Some(candidate_set_id.clone()),
    )
    .rows;
    current_candidate_rows.extend(
        auto_quant_material_rank_rows
            .iter()
            .filter(|row| {
                top_candidate_paths
                    .iter()
                    .any(|path| path.path_id == row.path_id)
            })
            .cloned(),
    );
    let runtime = resolve_structural_path_ranker_runtime(
        runtime_context.state_dir,
        &symbol,
        &candidate_set_id,
        &current_candidate_rows,
        &mut paths,
    );
    paths.sort_by(|left, right| structural_path_plan_order(left, right, prefer_history_runtime));
    let scored_candidate_paths = top_candidate_paths
        .iter()
        .map(|candidate| {
            paths
                .iter()
                .find(|path| path.path_id == candidate.path_id)
                .cloned()
                .unwrap_or_else(|| candidate.clone())
        })
        .collect::<Vec<_>>();
    StructuralPathPlanArtifact {
        required_data_contracts: structural_relevant_profile_data_contracts(
            snapshot,
            provider_status_agent,
        ),
        required_provider_tracks: structural_relevant_profile_track_statuses(
            snapshot,
            provider_status_agent,
        ),
        candidate_set_id,
        candidate_paths: scored_candidate_paths,
        path_ranker_runtime: runtime,
        paths,
    }
}

fn structural_feedback_path_direction_label(
    path_id: &str,
    latest_record: Option<&FeedbackRecord>,
    snapshot: &WorkflowSnapshot,
) -> String {
    if let Some(record) = latest_record {
        return structural_feedback_direction_label(
            record.model_probabilities_before_trade.selected_direction,
        )
        .to_string();
    }
    if let Some(direction) = structural_current_pre_bayes_trade_direction(snapshot) {
        if structural_current_pre_bayes_regime_profit_branch_path(snapshot).as_deref()
            == Some(path_id)
        {
            return direction;
        }
    }
    let root = path_id.split(" -> ").next().unwrap_or(path_id).trim();
    match root {
        "Bull" | "Sideways" | "Crisis" => "bull".to_string(),
        "Bear" => "bear".to_string(),
        _ => structural_direction(snapshot),
    }
}

fn structural_current_pre_bayes_trade_direction(snapshot: &WorkflowSnapshot) -> Option<String> {
    let raw = snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.pre_bayes_filtered_assignments.get("trade_direction"))?;
    match raw.trim().to_ascii_lowercase().as_str() {
        "bear" | "short" | "sell" => Some("bear".to_string()),
        "bull" | "long" | "buy" => Some("bull".to_string()),
        "neutral" | "observe" => Some("neutral".to_string()),
        _ => None,
    }
}

fn structural_feedback_path_candidates(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
    path_history: &StructuralPathHistoryArtifact,
    structural_prior_state: &StructuralPriorLearningState,
) -> Vec<StructuralPathArtifact> {
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    let selected_entry_quality = structural_selected_entry_quality(snapshot);
    let selected_entry_quality_probability =
        structural_selected_entry_quality_probability(snapshot);
    let pre_bayes_gate_status = structural_pre_bayes_gate_status(snapshot);
    let multi_timeframe_direction_bias = structural_multi_timeframe_direction_bias(snapshot);
    let execution_candidate_status = snapshot
        .latest_execution_candidate
        .as_ref()
        .map(|candidate| candidate.candidate_status.clone())
        .filter(|value| !value.trim().is_empty());
    let execution_candidate_artifact_id = snapshot
        .latest_execution_candidate
        .as_ref()
        .map(|candidate| candidate.artifact_id.clone());
    let base_prior = structural_primary_prior(snapshot);

    path_history
        .paths
        .iter()
        .filter(|summary| {
            summary.followed_count > 0
                && summary.wins
                    + summary.losses
                    + summary.breakevens
                    + summary.invalidated
                    + summary.abandoned
                    > 0
        })
        .filter(|summary| {
            feedback_history.iter().any(|record| {
                record
                    .structural_feedback
                    .as_ref()
                    .is_some_and(|refs| refs.path_id == summary.path_id)
                    && !crate::state::structural_feedback_is_infrastructure_negative(record)
            })
        })
        .map(|summary| {
            let latest_record = feedback_history.iter().rev().find(|record| {
                record
                    .structural_feedback
                    .as_ref()
                    .is_some_and(|refs| refs.path_id == summary.path_id)
                    && !crate::state::structural_feedback_is_infrastructure_negative(record)
            });
            let prior_stats = structural_prior_state.paths.get(&summary.path_id);
            let history_adjusted_prior =
                structural_history_adjusted_path_prior(base_prior, Some(summary));
            let resolved_prior = structural_resolved_smoothed_prior(
                prior_stats,
                structural_prior_state,
                history_adjusted_prior,
            );
            let path_posterior = structural_prior_target_policy_reward_prior(prior_stats)
                .or_else(|| structural_resolved_path_win_rate(prior_stats, Some(summary)))
                .unwrap_or_else(|| structural_posterior_confidence(snapshot))
                .clamp(0.0, 1.0);
            let composite_preference_score =
                structural_composite_preference_score(path_posterior, resolved_prior);
            StructuralPathArtifact {
                path_id: summary.path_id.clone(),
                scenario_id: summary.scenario_id.clone(),
                path_label: summary.path_id.clone(),
                direction: structural_feedback_path_direction_label(
                    &summary.path_id,
                    latest_record,
                    snapshot,
                ),
                entry_style: "structural_feedback_path".to_string(),
                selected_entry_quality: selected_entry_quality.clone(),
                selected_entry_quality_probability,
                pre_bayes_gate_status: pre_bayes_gate_status.clone(),
                multi_timeframe_direction_bias: multi_timeframe_direction_bias.clone(),
                execution_candidate_status: execution_candidate_status.clone(),
                execution_candidate_artifact_id: execution_candidate_artifact_id.clone(),
                execution_readiness: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_readiness),
                prediction_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.prediction_edge_share),
                execution_edge_share: snapshot
                    .latest_analyze
                    .as_ref()
                    .and_then(|phase| phase.execution_edge_share),
                historical_total_records: structural_resolved_observations(
                    prior_stats,
                    summary.total_records,
                ),
                historical_followed_count: structural_resolved_followed_count(
                    prior_stats,
                    summary.followed_count,
                ),
                execution_propensity: structural_prior_execution_propensity(prior_stats)
                    .or(summary.execution_propensity),
                historical_win_rate: structural_resolved_path_win_rate(prior_stats, Some(summary)),
                historical_invalidation_rate: structural_resolved_path_invalidation_rate(
                    prior_stats,
                    Some(summary),
                ),
                historical_avg_pnl: structural_resolved_avg_pnl(prior_stats, Some(summary.avg_pnl)),
                trigger_conditions: vec![format!(
                    "preserve exact structural feedback path {}",
                    summary.path_id
                )],
                confirmation_conditions: vec![format!(
                    "history_records={} followed={}",
                    summary.total_records, summary.followed_count
                )],
                stop_definition: "use the recorded branch feedback stop/exit contract".to_string(),
                target_definition: format!("historical_avg_pnl={:.6}", summary.avg_pnl),
                invalidation_conditions: vec![
                    "do not collapse exact feedback path into a generic structural path"
                        .to_string(),
                ],
                expected_failure_mode:
                    "exact feedback path not consumed by downstream execution surface".to_string(),
                max_time_in_trade: "use feedback record horizon when available".to_string(),
                path_prior: resolved_prior,
                path_posterior,
                bbn_support_score: path_posterior,
                catboost_score: None,
                path_ranker_calibrated_path_prob: None,
                path_ranker_path_prob_lower_bound: None,
                path_ranker_execution_gate_status: None,
                path_ranker_runtime_source: None,
                composite_preference_score,
                recommended_command: next_meta.executable_command.clone().or_else(|| {
                    if command.trim().is_empty() {
                        None
                    } else {
                        Some(command.clone())
                    }
                }),
            }
        })
        .collect()
}

fn structural_ranked_paths_with_runtime_context_and_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    runtime_context: StructuralPathRankerRuntimeContext<'_>,
) -> StructuralRankedPathSelection {
    let command = top_level_command(snapshot);
    let support_reason = structural_support_reason(snapshot);
    let provider_support =
        build_workflow_provider_support(provider_status_agent, &command, support_reason.as_deref());
    let node = build_structural_node_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        structural_prior_state,
    );
    let branch_history = build_structural_branch_history_artifact(snapshot, feedback_history);
    let scenario_history = build_structural_scenario_history_artifact(snapshot, feedback_history);
    let path_history = build_structural_path_history_artifact(snapshot, feedback_history);
    let branch_set = build_structural_branch_set_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &node,
        &branch_history,
        structural_prior_state,
    );
    let scenario_playbook = build_structural_scenario_playbook_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &branch_set,
        &scenario_history,
        structural_prior_state,
    );
    let path_plan = build_structural_path_plan_artifact_with_runtime_context_and_prior_state(
        StructuralPathPlanArtifactInput {
            snapshot,
            provider_status_agent,
            provider_support: &provider_support,
            scenarios: &scenario_playbook,
            feedback_history,
            path_history: &path_history,
            structural_prior_state,
            runtime_context,
        },
    );
    StructuralRankedPathSelection {
        candidate_set_id: path_plan.candidate_set_id.clone(),
        candidate_paths: path_plan.candidate_paths.clone(),
        runtime: path_plan.path_ranker_runtime,
    }
}

fn structural_short_rule_summary(items: &[String], fallback: &str) -> String {
    items
        .first()
        .map(|value| value.trim())
        .filter(|value| !value.is_empty())
        .map(str::to_string)
        .unwrap_or_else(|| fallback.to_string())
}

fn structural_scalar_rule_summary(value: &str, fallback: &str) -> String {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        fallback.to_string()
    } else {
        trimmed.to_string()
    }
}

fn structural_why_this_path_summary(path: &StructuralPathArtifact) -> String {
    let invalidation = path
        .historical_invalidation_rate
        .map(|value| format!("{value:.3}"))
        .unwrap_or_else(|| "n/a".to_string());
    format!(
        "posterior={:.3} prior={:.3} invalidation_rate={}",
        path.path_posterior, path.path_prior, invalidation
    )
}

fn structural_branch_transition_prior<'a>(
    structural_prior_state: &'a StructuralPriorLearningState,
    from_branch_id: &str,
    to_branch_id: &str,
) -> Option<&'a crate::state::StructuralBranchTransitionPrior> {
    let key = format!("{from_branch_id}=>{to_branch_id}");
    structural_prior_state.branch_transition_priors.get(&key)
}

fn structural_symbol(snapshot: &WorkflowSnapshot) -> String {
    if snapshot.symbol.trim().is_empty() {
        "UNKNOWN".to_string()
    } else {
        snapshot.symbol.clone()
    }
}

fn structural_latest_feedback_refs(snapshot: &WorkflowSnapshot) -> Option<StructuralFeedbackRefs> {
    [
        snapshot.latest_update.as_ref(),
        snapshot.latest_research.as_ref(),
        snapshot.latest_analyze.as_ref(),
        snapshot.latest_backtest.as_ref(),
        snapshot.latest_train.as_ref(),
    ]
    .into_iter()
    .flatten()
    .find_map(|phase| phase.structural_feedback.clone())
}

fn structural_focus_phase(snapshot: &WorkflowSnapshot) -> String {
    if snapshot.current_focus_phase.trim().is_empty() {
        "workflow_status".to_string()
    } else {
        snapshot.current_focus_phase.clone()
    }
}

fn structural_no_workflow_state(snapshot: &WorkflowSnapshot) -> bool {
    snapshot.latest_update.is_none()
        && snapshot.latest_research.is_none()
        && snapshot.latest_analyze.is_none()
        && snapshot.latest_backtest.is_none()
        && snapshot.latest_train.is_none()
}

fn structural_hard_block_active(snapshot: &WorkflowSnapshot) -> bool {
    matches!(
        snapshot.blocking_truth.status.as_str(),
        "blocked"
            | "bridge_needs_confirmation"
            | "validated_regressing"
            | "credibility_gate_blocked"
    )
}

fn structural_support_reason(snapshot: &WorkflowSnapshot) -> Option<String> {
    if snapshot
        .blocking_truth
        .reason
        .contains("user_selected_historical_data_missing")
    {
        Some("user_selected_historical_data_missing".to_string())
    } else if structural_hard_block_active(snapshot)
        && !snapshot.blocking_truth.reason.trim().is_empty()
    {
        Some(snapshot.blocking_truth.reason.clone())
    } else if snapshot.current_focus_reason.contains("provider")
        || snapshot.current_focus_reason.contains("historical_data")
    {
        Some(snapshot.current_focus_reason.clone())
    } else {
        None
    }
}

fn top_level_command(snapshot: &WorkflowSnapshot) -> String {
    if structural_hard_block_active(snapshot) {
        snapshot.blocking_truth.next_command.clone()
    } else {
        snapshot.recommended_next_command.clone()
    }
}

fn structural_posterior_confidence(snapshot: &WorkflowSnapshot) -> f64 {
    resolved_latest_ensemble_vote(snapshot)
        .as_ref()
        .and_then(|vote| vote.posterior_confidence.or(Some(vote.confidence)))
        .unwrap_or_else(|| {
            if structural_no_workflow_state(snapshot) {
                0.0
            } else {
                0.5
            }
        })
}

fn structural_primary_probability(snapshot: &WorkflowSnapshot) -> f64 {
    if let Some(probability) = structural_regime_probabilities(snapshot)
        .first()
        .map(|(_, probability)| *probability)
    {
        probability
    } else {
        structural_posterior_confidence(snapshot)
    }
}

fn structural_primary_prior(snapshot: &WorkflowSnapshot) -> f64 {
    if let Some(vote) = resolved_latest_ensemble_vote(snapshot).as_ref() {
        if !vote.posterior_probabilities.is_empty() {
            return (1.0 / vote.posterior_probabilities.len() as f64).clamp(0.0, 1.0);
        }
    }
    0.5
}

fn canonical_structural_regime_label(label: &str) -> Option<String> {
    let normalized = label.trim().to_ascii_lowercase();
    let canonical = match normalized.as_str() {
        "trend" | "bull" | "bear" | "trend_impulse" | "trend_decay" => "trend",
        "range" | "range_calm" | "range_choppy" => "range",
        "stress" => "stress",
        "transition" => "transition",
        _ => return None,
    };
    Some(canonical.to_string())
}

fn structural_sorted_regime_probabilities(
    probabilities: std::collections::BTreeMap<String, f64>,
) -> Vec<(String, f64)> {
    let mut out = probabilities
        .into_iter()
        .filter(|(_, probability)| probability.is_finite() && *probability > 0.0)
        .collect::<Vec<_>>();
    out.sort_by(|a, b| {
        b.1.partial_cmp(&a.1)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| a.0.cmp(&b.0))
    });
    out
}

fn structural_ensemble_regime_probabilities(snapshot: &WorkflowSnapshot) -> Vec<(String, f64)> {
    let mut aggregated = std::collections::BTreeMap::new();
    if let Some(vote) = resolved_latest_ensemble_vote(snapshot).as_ref() {
        for (regime, probability) in &vote.posterior_probabilities {
            if let Some(canonical) = canonical_structural_regime_label(regime) {
                *aggregated.entry(canonical).or_insert(0.0) += *probability;
            }
        }
    }
    structural_sorted_regime_probabilities(aggregated)
}

fn structural_analyze_anchor_regime_probabilities(
    snapshot: &WorkflowSnapshot,
) -> Vec<(String, f64)> {
    let Some(analyze) = snapshot.latest_analyze.as_ref() else {
        return Vec::new();
    };
    canonical_analyze_regime_surface(analyze)
        .map(|(_, probabilities, _)| structural_sorted_regime_probabilities(probabilities))
        .unwrap_or_default()
}

fn structural_active_regime(snapshot: &WorkflowSnapshot) -> Option<String> {
    structural_regime_probabilities(snapshot)
        .first()
        .map(|(regime, _)| regime.clone())
        .or_else(|| {
            resolved_latest_ensemble_vote(snapshot)
                .as_ref()
                .and_then(|vote| canonical_structural_regime_label(&vote.posterior_active_regime))
        })
        .or_else(|| {
            snapshot.latest_analyze.as_ref().and_then(|analyze| {
                analyze
                    .pre_bayes_filtered_assignments
                    .get("market_regime")
                    .and_then(|value| canonical_structural_regime_label(value))
            })
        })
}

fn structural_regime_probabilities(snapshot: &WorkflowSnapshot) -> Vec<(String, f64)> {
    let ensemble = structural_ensemble_regime_probabilities(snapshot);
    if !ensemble.is_empty() {
        return ensemble;
    }

    let analyze = structural_analyze_anchor_regime_probabilities(snapshot);
    if !analyze.is_empty() {
        return analyze;
    }

    resolved_latest_ensemble_vote(snapshot)
        .as_ref()
        .and_then(|vote| canonical_structural_regime_label(&vote.posterior_active_regime))
        .map(|regime| vec![(regime, structural_posterior_confidence(snapshot))])
        .unwrap_or_default()
}

fn structural_branch_label_for_regime(regime: &str) -> &'static str {
    match regime {
        "trend" => "trend_follow_through",
        "transition" => "transition_confirmation",
        "range" => "range_mean_reversion",
        "stress" => "stress_de_risk",
        _ => "execute_recommended_path",
    }
}

fn structural_regime_supporting_evidence(
    snapshot: &WorkflowSnapshot,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    regime: &str,
    probability: f64,
) -> Vec<String> {
    let mut evidence = vec![format!("posterior_probability={regime}:{probability:.3}")];
    evidence.extend(structural_supporting_evidence(snapshot, provider_support));
    evidence
}

fn structural_market_context(snapshot: &WorkflowSnapshot) -> Vec<String> {
    let mut out = Vec::new();
    if let Some(vote) = resolved_latest_ensemble_vote(snapshot).as_ref() {
        if !vote.posterior_active_regime.trim().is_empty() {
            out.push(format!(
                "posterior_active_regime={}",
                vote.posterior_active_regime
            ));
        }
        if !vote.posterior_normalization_status.trim().is_empty() {
            out.push(format!(
                "posterior_normalization_status={}",
                vote.posterior_normalization_status
            ));
        }
        for (regime, probability) in structural_regime_probabilities(snapshot) {
            out.push(format!("posterior_probability={regime}:{probability:.3}"));
        }
    }
    out
}

fn structural_selected_entry_quality(snapshot: &WorkflowSnapshot) -> Option<String> {
    snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.selected_entry_quality.clone())
        .or_else(|| {
            snapshot
                .latest_execution_candidate
                .as_ref()
                .map(|candidate| candidate.pre_bayes_bridge_selected_entry_quality.clone())
                .filter(|value| !value.trim().is_empty())
        })
}

fn structural_selected_entry_quality_probability(snapshot: &WorkflowSnapshot) -> Option<f64> {
    snapshot
        .latest_analyze
        .as_ref()
        .and_then(|phase| phase.pre_bayes_selected_entry_quality_probability)
        .or_else(|| {
            snapshot
                .latest_pre_bayes_entry_quality_bridge
                .as_ref()
                .and_then(|bridge| {
                    bridge
                        .selected_entry_quality
                        .values()
                        .copied()
                        .max_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal))
                })
        })
}

fn structural_pre_bayes_gate_status(snapshot: &WorkflowSnapshot) -> Option<String> {
    snapshot
        .latest_analyze
        .as_ref()
        .map(|phase| phase.pre_bayes_gate_status.clone())
        .filter(|value| !value.trim().is_empty())
}

fn structural_multi_timeframe_direction_bias(snapshot: &WorkflowSnapshot) -> Option<String> {
    snapshot
        .latest_analyze
        .as_ref()
        .map(|phase| phase.pre_bayes_multi_timeframe_direction_bias.clone())
        .filter(|value| !value.trim().is_empty())
}

fn structural_context_hints(snapshot: &WorkflowSnapshot) -> Vec<String> {
    let command = top_level_command(snapshot).to_ascii_lowercase();
    let focus = structural_focus_phase(snapshot).to_ascii_lowercase();
    let reason = structural_support_reason(snapshot)
        .unwrap_or_default()
        .to_ascii_lowercase();
    let mut hints = vec![command, focus, reason];
    if structural_no_workflow_state(snapshot) {
        hints.push("bootstrap".to_string());
    }
    hints
}

fn structural_relevant_profile_data_contracts(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
) -> Vec<String> {
    let Some(profile) = provider_status_agent.selected_profile_full.as_ref() else {
        return Vec::new();
    };
    let hints = structural_context_hints(snapshot);
    let mut contracts = profile
        .data_contracts
        .iter()
        .filter(|contract| structural_contract_relevant(contract.category.as_str(), &hints))
        .map(|contract| contract.label.clone())
        .collect::<Vec<_>>();
    contracts.sort();
    contracts.dedup();
    contracts
}

fn structural_relevant_profile_track_statuses(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
) -> Vec<String> {
    let Some(profile) = provider_status_agent.selected_profile_full.as_ref() else {
        return Vec::new();
    };
    let hints = structural_context_hints(snapshot);
    let mut statuses = profile
        .track_details
        .iter()
        .filter(|track| structural_track_relevant(track.activation_hints.as_slice(), &hints))
        .map(|track| {
            let target = if !track.pending_provider_ids.is_empty() {
                track.pending_provider_ids.join(",")
            } else if !track.ready_provider_ids.is_empty() {
                track.ready_provider_ids.join(",")
            } else {
                "none".to_string()
            };
            format!("{}:{}:{}", track.track_id, track.status, target)
        })
        .collect::<Vec<_>>();
    statuses.sort();
    statuses.dedup();
    statuses
}

fn structural_contract_relevant(category: &str, hints: &[String]) -> bool {
    let wants_live = hints
        .iter()
        .any(|hint| hint.contains("analyze-live") || hint.contains("live"));
    let wants_research = hints.iter().any(|hint| {
        hint.contains("research")
            || hint.contains("backtest")
            || hint.contains("historical")
            || hint.contains("data_selection")
            || hint.contains("bootstrap")
    });
    let wants_kraken = hints
        .iter()
        .any(|hint| hint.contains("kraken") || hint.contains("crypto"));
    match category {
        "historical" => wants_research,
        "market_context" => wants_research || wants_live,
        "options" => wants_research || wants_live,
        "live" => wants_live,
        "credentials" => wants_kraken,
        _ => true,
    }
}

fn structural_track_relevant(activation_hints: &[String], hints: &[String]) -> bool {
    if activation_hints.is_empty() {
        return true;
    }
    activation_hints.iter().any(|track_hint| {
        let track_hint = track_hint.to_ascii_lowercase();
        hints.iter().any(|hint| hint.contains(track_hint.as_str()))
    })
}

fn structural_timeframe_scope(snapshot: &WorkflowSnapshot) -> Vec<String> {
    snapshot
        .latest_update
        .as_ref()
        .or(snapshot.latest_research.as_ref())
        .or(snapshot.latest_analyze.as_ref())
        .map(|phase| {
            phase
                .multi_timeframe_summary
                .iter()
                .filter_map(|line| line.split(':').next())
                .filter(|part| !part.trim().is_empty())
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default()
}

fn structural_supporting_evidence(
    snapshot: &WorkflowSnapshot,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
) -> Vec<String> {
    let mut out = Vec::new();
    out.extend(snapshot.blocking_truth.evidence.iter().take(3).cloned());
    out.extend(snapshot.pending_actions.iter().take(2).cloned());
    if provider_support.active {
        out.extend(
            provider_support
                .pending_providers
                .iter()
                .map(|provider| format!("pending_provider={provider}")),
        );
    }
    if out.is_empty() && structural_no_workflow_state(snapshot) {
        out.push("workflow snapshot not initialized".to_string());
    }
    out
}

fn structural_invalidating_evidence(
    snapshot: &WorkflowSnapshot,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
) -> Vec<String> {
    let mut out = snapshot
        .risk_flags
        .iter()
        .take(3)
        .cloned()
        .collect::<Vec<_>>();
    if provider_support.active {
        out.push("provider runtime still missing".to_string());
    }
    out
}

fn structural_origin_artifacts(snapshot: &WorkflowSnapshot) -> Vec<String> {
    let mut out = Vec::new();
    if let Some(vote) = snapshot.latest_ensemble_vote.as_ref() {
        out.push(format!("ensemble_vote:{}", vote.artifact_id));
    }
    if let Some(artifact) = snapshot.actionable_artifacts.first() {
        out.push(format!(
            "{}:{}",
            artifact.artifact_kind, artifact.artifact_id
        ));
    }
    out
}

fn structural_direction(snapshot: &WorkflowSnapshot) -> String {
    snapshot
        .latest_ensemble_vote
        .as_ref()
        .map(|vote| vote.final_action.clone())
        .filter(|value| !value.trim().is_empty())
        .unwrap_or_else(|| "observe".to_string())
}

fn structural_entry_style(
    snapshot: &WorkflowSnapshot,
    scenario: &StructuralScenarioArtifact,
) -> String {
    if scenario.scenario_label.contains("bootstrap") || scenario.scenario_label.contains("provider")
    {
        "non_trading_precondition".to_string()
    } else if structural_hard_block_active(snapshot) {
        "blocked_until_resolution".to_string()
    } else {
        "conditional_execution".to_string()
    }
}

fn structural_confirmation_conditions(
    snapshot: &WorkflowSnapshot,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    next_meta: &crate::state::RecommendedNextCommandMeta,
) -> Vec<String> {
    let mut out = Vec::new();
    if provider_support.active {
        out.push("all required provider tracks are ready".to_string());
    }
    if next_meta.requires_user_input {
        out.push("user confirms the required input".to_string());
    }
    if structural_hard_block_active(snapshot) {
        out.push("hard block is cleared on workflow refresh".to_string());
    }
    if out.is_empty() {
        out.push("recommended command remains valid on next refresh".to_string());
    }
    out
}

fn structural_trigger_conditions(
    snapshot: &WorkflowSnapshot,
    scenario: &StructuralScenarioArtifact,
) -> Vec<String> {
    let mut out = scenario.required_confirmations.clone();
    if let Some(entry_quality) = structural_selected_entry_quality(snapshot) {
        out.push(format!("selected_entry_quality={entry_quality}"));
    }
    if let Some(gate_status) = structural_pre_bayes_gate_status(snapshot) {
        out.push(format!("pre_bayes_gate_status={gate_status}"));
    }
    if let Some(direction_bias) = structural_multi_timeframe_direction_bias(snapshot) {
        out.push(format!("multi_timeframe_direction_bias={direction_bias}"));
    }
    out
}

fn structural_stop_definition(
    snapshot: &WorkflowSnapshot,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenario: &StructuralScenarioArtifact,
) -> String {
    if provider_support.active || structural_no_workflow_state(snapshot) {
        "No trade until preconditions are satisfied.".to_string()
    } else if let Some(candidate) = snapshot.latest_execution_candidate.as_ref() {
        format!(
            "Use execution candidate '{}' once actionable; current candidate_status={}.",
            candidate.artifact_id, candidate.candidate_status
        )
    } else if scenario.scenario_label.contains("observe") {
        "Stay flat; stop is the next structural invalidation review.".to_string()
    } else {
        "Use the downstream execution path stop once the path is active.".to_string()
    }
}

fn structural_target_definition(
    snapshot: &WorkflowSnapshot,
    command: &str,
    scenario: &StructuralScenarioArtifact,
) -> String {
    if structural_no_workflow_state(snapshot) {
        "Reach the first valid workflow snapshot.".to_string()
    } else if let Some(candidate) = snapshot.latest_execution_candidate.as_ref() {
        format!(
            "Advance to execution candidate '{}' while preserving candidate_status={}.",
            candidate.artifact_id, candidate.candidate_status
        )
    } else if scenario.scenario_label.contains("provider") {
        "Reach provider/runtime readiness for the requested path.".to_string()
    } else if scenario
        .scenario_label
        .contains("historical_dataset_selection")
    {
        "Reach a user-approved research/backtest dataset selection.".to_string()
    } else {
        format!("Execute or review: {}", command.trim())
    }
}

fn structural_invalidation_conditions(
    snapshot: &WorkflowSnapshot,
    scenario: &StructuralScenarioArtifact,
) -> Vec<String> {
    let mut out = scenario.hard_invalidations.clone();
    if let Some(candidate) = snapshot.latest_execution_candidate.as_ref() {
        if !candidate.review_reason.trim().is_empty() {
            out.push(format!(
                "execution_candidate_review_reason={}",
                candidate.review_reason
            ));
        }
        if !candidate.pre_bayes_gate_status.trim().is_empty() {
            out.push(format!(
                "execution_candidate_pre_bayes_gate_status={}",
                candidate.pre_bayes_gate_status
            ));
        }
    }
    out
}

fn structural_failure_mode(
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenario: &StructuralScenarioArtifact,
) -> String {
    if provider_support.active {
        "provider_prerequisite_unresolved".to_string()
    } else if scenario
        .scenario_label
        .contains("historical_dataset_selection")
    {
        "dataset_selection_not_confirmed".to_string()
    } else if scenario.scenario_label.contains("observe") {
        "opportunity_passed_without_confirmation".to_string()
    } else {
        "structural_invalidation_before_path_completion".to_string()
    }
}

pub fn build_structural_feedback_template_artifact(
    snapshot: &WorkflowSnapshot,
    node: &StructuralNodeArtifact,
    branch_set: &StructuralBranchSetArtifact,
    scenario_playbook: &StructuralScenarioPlaybookArtifact,
    path_plan: &StructuralPathPlanArtifact,
) -> StructuralFeedbackTemplateArtifact {
    let selected_branch = branch_set.branches.first();
    let selected_scenario = selected_branch.and_then(|branch| {
        scenario_playbook
            .scenarios
            .iter()
            .find(|scenario| scenario.branch_id == branch.branch_id)
    });
    let selected_path = selected_scenario.and_then(|scenario| {
        path_plan
            .paths
            .iter()
            .find(|path| path.scenario_id == scenario.scenario_id)
    });
    let candidate_paths = path_plan.candidate_paths.clone();
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = path_plan.candidate_set_id.clone();
    let candidate_set_size = candidate_paths.len();
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let selected_path_probability = selected_path
        .map(|path| {
            structural_candidate_policy_probability(
                path.composite_preference_score,
                denominator,
                candidate_set_size,
            )
        })
        .unwrap_or_default();
    let recommended_at = snapshot
        .generated_at
        .to_rfc3339_opts(SecondsFormat::Secs, true);
    let recommendation_id = format!(
        "structural-feedback:{}:{}:{}",
        structural_symbol(snapshot),
        node.node_id,
        selected_path
            .map(|path| path.path_id.as_str())
            .unwrap_or("path_unavailable")
    );
    StructuralFeedbackTemplateArtifact {
        protocol_version: "structural-feedback-v1".to_string(),
        recommendation_id,
        recommended_at,
        symbol,
        node_id: node.node_id.clone(),
        branch_id: selected_branch
            .map(|branch| branch.branch_id.clone())
            .unwrap_or_else(|| "branch_unavailable".to_string()),
        scenario_id: selected_scenario
            .map(|scenario| scenario.scenario_id.clone())
            .unwrap_or_else(|| "scenario_unavailable".to_string()),
        path_id: selected_path
            .map(|path| path.path_id.clone())
            .unwrap_or_else(|| "path_unavailable".to_string()),
        candidate_set_id,
        candidate_set_size,
        selected_path_probability,
        direction: selected_path
            .map(|path| path.direction.clone())
            .unwrap_or_else(|| "observe".to_string()),
        entry_style: selected_path
            .map(|path| path.entry_style.clone())
            .unwrap_or_else(|| "non_trading_precondition".to_string()),
        selected_entry_quality: selected_path
            .and_then(|path| path.selected_entry_quality.clone()),
        selected_entry_quality_probability: selected_path
            .and_then(|path| path.selected_entry_quality_probability),
        pre_bayes_gate_status: selected_path.and_then(|path| path.pre_bayes_gate_status.clone()),
        path_posterior: selected_path.map(|path| path.path_posterior),
        bbn_support_score: selected_path.map(|path| path.bbn_support_score),
        allowed_outcomes: vec![
            "win".to_string(),
            "loss".to_string(),
            "breakeven".to_string(),
            "invalidated".to_string(),
            "abandoned".to_string(),
            "not_followed".to_string(),
        ],
        feedback_fields: vec![
            StructuralFeedbackField {
                field_id: "followed_path".to_string(),
                label: "Followed Path".to_string(),
                value_type: "boolean".to_string(),
                required: true,
                description: "Whether the user actually followed the recommended path."
                    .to_string(),
            },
            StructuralFeedbackField {
                field_id: "realized_outcome".to_string(),
                label: "Realized Outcome".to_string(),
                value_type: "enum".to_string(),
                required: true,
                description:
                    "One of win, loss, breakeven, invalidated, abandoned, or not_followed."
                        .to_string(),
            },
            StructuralFeedbackField {
                field_id: "realized_pnl".to_string(),
                label: "Realized PnL".to_string(),
                value_type: "number".to_string(),
                required: false,
                description: "Optional realized PnL from the actual execution.".to_string(),
            },
            StructuralFeedbackField {
                field_id: "exit_reason".to_string(),
                label: "Exit Reason".to_string(),
                value_type: "string".to_string(),
                required: false,
                description:
                    "Freeform reason such as stop_hit, target_hit, invalidated, timed_out."
                        .to_string(),
            },
            StructuralFeedbackField {
                field_id: "notes".to_string(),
                label: "Notes".to_string(),
                value_type: "string".to_string(),
                required: false,
                description: "Optional operator notes about what actually happened.".to_string(),
            },
        ],
        notes: vec![
            "Preserve recommendation_id plus node/branch/scenario/path ids when recording live feedback."
                .to_string(),
            "This is a protocol contract only; canonical persistence wiring comes next."
                .to_string(),
        ],
    }
}

#[derive(Debug, Clone)]
struct StructuralFeedbackHistoryRow {
    node_id: String,
    branch_id: String,
    scenario_id: String,
    path_id: String,
    recommended_at: String,
    followed_path: bool,
    outcome: String,
    pnl: f64,
}

fn structural_feedback_history_rows(
    feedback_history: &[FeedbackRecord],
) -> Vec<StructuralFeedbackHistoryRow> {
    let mut rows = feedback_history
        .iter()
        .filter_map(|record| {
            if crate::state::structural_feedback_is_infrastructure_negative(record) {
                return None;
            }
            let refs = record.structural_feedback.as_ref()?;
            Some(StructuralFeedbackHistoryRow {
                node_id: refs.node_id.clone(),
                branch_id: refs.branch_id.clone(),
                scenario_id: refs.scenario_id.clone(),
                path_id: refs.path_id.clone(),
                recommended_at: refs.recommended_at.clone(),
                followed_path: refs.followed_path,
                outcome: record.realized_outcome.clone(),
                pnl: record.pnl,
            })
        })
        .collect::<Vec<_>>();
    rows.sort_by(|a, b| {
        a.recommended_at
            .cmp(&b.recommended_at)
            .then_with(|| a.path_id.cmp(&b.path_id))
    });
    rows
}

fn structural_history_row_not_followed(row: &StructuralFeedbackHistoryRow) -> bool {
    !row.followed_path || row.outcome.trim().eq_ignore_ascii_case("not_followed")
}

fn structural_history_execution_propensity(
    followed_count: usize,
    not_followed: usize,
) -> Option<f64> {
    let exposure = followed_count + not_followed;
    (exposure > 0)
        .then(|| ((1.0 + followed_count as f64) / (2.0 + exposure as f64)).clamp(0.0, 1.0))
}

fn structural_history_off_policy_exposure_rate(
    followed_count: usize,
    not_followed: usize,
) -> Option<f64> {
    let exposure = followed_count + not_followed;
    (exposure > 0).then(|| ((1.0 + not_followed as f64) / (2.0 + exposure as f64)).clamp(0.0, 1.0))
}

pub fn build_structural_history_summary_artifact(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
) -> StructuralHistorySummaryArtifact {
    let rows = structural_feedback_history_rows(feedback_history);
    StructuralHistorySummaryArtifact {
        total_records: rows.len(),
        distinct_nodes: rows
            .iter()
            .map(|row| row.node_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        distinct_branches: rows
            .iter()
            .map(|row| row.branch_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        distinct_scenarios: rows
            .iter()
            .map(|row| row.scenario_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        distinct_paths: rows
            .iter()
            .map(|row| row.path_id.as_str())
            .collect::<std::collections::BTreeSet<_>>()
            .len(),
        latest_node_id: snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.as_ref())
            .map(|refs| refs.node_id.clone()),
        latest_branch_id: snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.as_ref())
            .map(|refs| refs.branch_id.clone()),
        latest_scenario_id: snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.as_ref())
            .map(|refs| refs.scenario_id.clone()),
        latest_path_id: snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.as_ref())
            .map(|refs| refs.path_id.clone()),
    }
}

pub fn build_structural_node_history_artifact(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
) -> StructuralNodeHistoryArtifact {
    let mut summaries = std::collections::BTreeMap::<String, StructuralNodeOutcomeSummary>::new();
    for row in structural_feedback_history_rows(feedback_history) {
        let entry =
            summaries
                .entry(row.node_id.clone())
                .or_insert_with(|| StructuralNodeOutcomeSummary {
                    node_id: row.node_id.clone(),
                    ..StructuralNodeOutcomeSummary::default()
                });
        entry.total_records += 1;
        entry.avg_pnl += row.pnl;
        if row.followed_path {
            entry.followed_count += 1;
        }
        if structural_history_row_not_followed(&row) {
            entry.not_followed += 1;
        }
        match row.outcome.as_str() {
            "win" => entry.wins += 1,
            "loss" => entry.losses += 1,
            "breakeven" => entry.breakevens += 1,
            "invalidated" => entry.invalidated += 1,
            "abandoned" => entry.abandoned += 1,
            "not_followed" => {}
            _ => {}
        }
        entry.last_recommended_at = Some(row.recommended_at);
        entry.last_realized_outcome = Some(row.outcome);
    }
    let mut nodes = summaries.into_values().collect::<Vec<_>>();
    finalize_structural_node_summaries(&mut nodes);
    StructuralNodeHistoryArtifact {
        summary: StructuralEntityHistorySummary {
            total_records: nodes.iter().map(|node| node.total_records).sum(),
            distinct_entities: nodes.len(),
            latest_entity_id: snapshot
                .latest_update
                .as_ref()
                .and_then(|phase| phase.structural_feedback.as_ref())
                .map(|refs| refs.node_id.clone()),
        },
        nodes,
    }
}

pub fn build_structural_branch_history_artifact(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
) -> StructuralBranchHistoryArtifact {
    let mut summaries =
        std::collections::BTreeMap::<(String, String), StructuralBranchOutcomeSummary>::new();
    for row in structural_feedback_history_rows(feedback_history) {
        let entry = summaries
            .entry((row.node_id.clone(), row.branch_id.clone()))
            .or_insert_with(|| StructuralBranchOutcomeSummary {
                node_id: row.node_id.clone(),
                branch_id: row.branch_id.clone(),
                ..StructuralBranchOutcomeSummary::default()
            });
        entry.total_records += 1;
        entry.avg_pnl += row.pnl;
        if row.followed_path {
            entry.followed_count += 1;
        }
        if structural_history_row_not_followed(&row) {
            entry.not_followed += 1;
        }
        match row.outcome.as_str() {
            "win" => entry.wins += 1,
            "loss" => entry.losses += 1,
            "breakeven" => entry.breakevens += 1,
            "invalidated" => entry.invalidated += 1,
            "abandoned" => entry.abandoned += 1,
            "not_followed" => {}
            _ => {}
        }
        entry.last_recommended_at = Some(row.recommended_at);
        entry.last_realized_outcome = Some(row.outcome);
    }
    let mut branches = summaries.into_values().collect::<Vec<_>>();
    finalize_structural_branch_summaries(&mut branches);
    StructuralBranchHistoryArtifact {
        summary: StructuralEntityHistorySummary {
            total_records: branches.iter().map(|branch| branch.total_records).sum(),
            distinct_entities: branches.len(),
            latest_entity_id: snapshot
                .latest_update
                .as_ref()
                .and_then(|phase| phase.structural_feedback.as_ref())
                .map(|refs| refs.branch_id.clone()),
        },
        branches,
    }
}

pub fn build_structural_scenario_history_artifact(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
) -> StructuralScenarioHistoryArtifact {
    let mut summaries = std::collections::BTreeMap::<
        (String, String, String),
        StructuralScenarioOutcomeSummary,
    >::new();
    for row in structural_feedback_history_rows(feedback_history) {
        let entry = summaries
            .entry((
                row.node_id.clone(),
                row.branch_id.clone(),
                row.scenario_id.clone(),
            ))
            .or_insert_with(|| StructuralScenarioOutcomeSummary {
                node_id: row.node_id.clone(),
                branch_id: row.branch_id.clone(),
                scenario_id: row.scenario_id.clone(),
                ..StructuralScenarioOutcomeSummary::default()
            });
        entry.total_records += 1;
        entry.avg_pnl += row.pnl;
        if row.followed_path {
            entry.followed_count += 1;
        }
        if structural_history_row_not_followed(&row) {
            entry.not_followed += 1;
        }
        match row.outcome.as_str() {
            "win" => entry.wins += 1,
            "loss" => entry.losses += 1,
            "breakeven" => entry.breakevens += 1,
            "invalidated" => entry.invalidated += 1,
            "abandoned" => entry.abandoned += 1,
            "not_followed" => {}
            _ => {}
        }
        entry.last_recommended_at = Some(row.recommended_at);
        entry.last_realized_outcome = Some(row.outcome);
    }
    let mut scenarios = summaries.into_values().collect::<Vec<_>>();
    finalize_structural_scenario_summaries(&mut scenarios);
    StructuralScenarioHistoryArtifact {
        summary: StructuralEntityHistorySummary {
            total_records: scenarios
                .iter()
                .map(|scenario| scenario.total_records)
                .sum(),
            distinct_entities: scenarios.len(),
            latest_entity_id: snapshot
                .latest_update
                .as_ref()
                .and_then(|phase| phase.structural_feedback.as_ref())
                .map(|refs| refs.scenario_id.clone()),
        },
        scenarios,
    }
}

pub fn build_structural_path_history_artifact(
    snapshot: &WorkflowSnapshot,
    feedback_history: &[FeedbackRecord],
) -> StructuralPathHistoryArtifact {
    let rows = structural_feedback_history_rows(feedback_history);

    let mut summaries = std::collections::BTreeMap::<
        (String, String, String, String),
        StructuralPathOutcomeSummary,
    >::new();
    for row in rows {
        let entry = summaries
            .entry((
                row.node_id.clone(),
                row.branch_id.clone(),
                row.scenario_id.clone(),
                row.path_id.clone(),
            ))
            .or_insert_with(|| StructuralPathOutcomeSummary {
                node_id: row.node_id.clone(),
                branch_id: row.branch_id.clone(),
                scenario_id: row.scenario_id.clone(),
                path_id: row.path_id.clone(),
                ..StructuralPathOutcomeSummary::default()
            });
        entry.total_records += 1;
        entry.avg_pnl += row.pnl;
        if row.followed_path {
            entry.followed_count += 1;
        }
        if structural_history_row_not_followed(&row) {
            entry.not_followed += 1;
        }
        match row.outcome.as_str() {
            "win" => entry.wins += 1,
            "loss" => entry.losses += 1,
            "breakeven" => entry.breakevens += 1,
            "invalidated" => entry.invalidated += 1,
            "abandoned" => entry.abandoned += 1,
            "not_followed" => {}
            _ => {}
        }
        entry.last_recommended_at = Some(row.recommended_at);
        entry.last_realized_outcome = Some(row.outcome);
    }

    let mut paths = summaries.into_values().collect::<Vec<_>>();
    finalize_structural_path_summaries(&mut paths);

    let latest_path_id = snapshot
        .latest_update
        .as_ref()
        .and_then(|phase| phase.structural_feedback.as_ref())
        .map(|refs| refs.path_id.clone());

    StructuralPathHistoryArtifact {
        summary: StructuralPathHistorySummary {
            total_records: paths.iter().map(|path| path.total_records).sum(),
            distinct_paths: paths.len(),
            distinct_branches: paths
                .iter()
                .map(|path| path.branch_id.as_str())
                .collect::<std::collections::BTreeSet<_>>()
                .len(),
            distinct_scenarios: paths
                .iter()
                .map(|path| path.scenario_id.as_str())
                .collect::<std::collections::BTreeSet<_>>()
                .len(),
            latest_path_id,
        },
        paths,
    }
}

fn finalize_structural_node_summaries(nodes: &mut [StructuralNodeOutcomeSummary]) {
    for node in nodes.iter_mut() {
        if node.total_records > 0 {
            node.avg_pnl /= node.total_records as f64;
        }
        node.execution_propensity =
            structural_history_execution_propensity(node.followed_count, node.not_followed);
        node.off_policy_exposure_rate =
            structural_history_off_policy_exposure_rate(node.followed_count, node.not_followed);
    }
    nodes.sort_by(|a, b| {
        b.total_records
            .cmp(&a.total_records)
            .then_with(|| b.wins.cmp(&a.wins))
            .then_with(|| a.node_id.cmp(&b.node_id))
    });
}

fn finalize_structural_branch_summaries(branches: &mut [StructuralBranchOutcomeSummary]) {
    for branch in branches.iter_mut() {
        if branch.total_records > 0 {
            branch.avg_pnl /= branch.total_records as f64;
        }
        branch.execution_propensity =
            structural_history_execution_propensity(branch.followed_count, branch.not_followed);
        branch.off_policy_exposure_rate =
            structural_history_off_policy_exposure_rate(branch.followed_count, branch.not_followed);
    }
    branches.sort_by(|a, b| {
        b.total_records
            .cmp(&a.total_records)
            .then_with(|| b.wins.cmp(&a.wins))
            .then_with(|| a.branch_id.cmp(&b.branch_id))
    });
}

fn finalize_structural_scenario_summaries(scenarios: &mut [StructuralScenarioOutcomeSummary]) {
    for scenario in scenarios.iter_mut() {
        if scenario.total_records > 0 {
            scenario.avg_pnl /= scenario.total_records as f64;
        }
        scenario.execution_propensity =
            structural_history_execution_propensity(scenario.followed_count, scenario.not_followed);
        scenario.off_policy_exposure_rate = structural_history_off_policy_exposure_rate(
            scenario.followed_count,
            scenario.not_followed,
        );
    }
    scenarios.sort_by(|a, b| {
        b.total_records
            .cmp(&a.total_records)
            .then_with(|| b.wins.cmp(&a.wins))
            .then_with(|| a.scenario_id.cmp(&b.scenario_id))
    });
}

fn finalize_structural_path_summaries(paths: &mut [StructuralPathOutcomeSummary]) {
    for path in paths.iter_mut() {
        if path.total_records > 0 {
            path.avg_pnl /= path.total_records as f64;
        }
        path.execution_propensity =
            structural_history_execution_propensity(path.followed_count, path.not_followed);
        path.off_policy_exposure_rate =
            structural_history_off_policy_exposure_rate(path.followed_count, path.not_followed);
    }
    paths.sort_by(|a, b| {
        b.total_records
            .cmp(&a.total_records)
            .then_with(|| b.wins.cmp(&a.wins))
            .then_with(|| a.path_id.cmp(&b.path_id))
    });
}

pub fn feedback_record_from_structural_submission(
    submission: StructuralFeedbackSubmission,
    symbol_override: Option<&str>,
    outcome_override: Option<&str>,
    pnl_override: Option<f64>,
    regime_override: Option<Regime>,
    direction_override: Option<Direction>,
) -> FeedbackRecord {
    let selected_direction = direction_override.unwrap_or_else(|| {
        match submission.direction.trim().to_ascii_lowercase().as_str() {
            "bull" | "long" | "execute_follow_through" => Direction::Bull,
            "bear" | "short" | "stress" => Direction::Bear,
            _ => Direction::Neutral,
        }
    });
    let selected_probability = submission
        .selected_path_probability
        .or(submission.path_posterior)
        .or(submission.selected_entry_quality_probability)
        .or(submission.bbn_support_score)
        .map(|probability| probability.clamp(0.0, 1.0))
        .unwrap_or_else(|| {
            match submission
                .selected_entry_quality
                .as_deref()
                .unwrap_or("medium")
                .to_ascii_lowercase()
                .as_str()
            {
                "high" => 0.8,
                "low" => 0.2,
                _ => 0.5,
            }
        });
    let (long_score, short_score, win_prob_long, win_prob_short) = match selected_direction {
        Direction::Bull => (
            selected_probability,
            1.0 - selected_probability,
            selected_probability,
            1.0 - selected_probability,
        ),
        Direction::Bear => (
            1.0 - selected_probability,
            selected_probability,
            1.0 - selected_probability,
            selected_probability,
        ),
        Direction::Neutral => (0.0, 0.0, selected_probability, selected_probability),
    };
    let outcome = outcome_override
        .map(str::to_string)
        .unwrap_or(submission.realized_outcome.clone());
    let pnl = pnl_override
        .or(submission.realized_pnl)
        .unwrap_or_else(|| match outcome.as_str() {
            "win" => 0.01,
            "loss" => -0.01,
            _ => 0.0,
        });
    FeedbackRecord {
        timestamp: chrono::Utc::now(),
        symbol: symbol_override.unwrap_or(&submission.symbol).to_string(),
        source: "structural_feedback_submission".to_string(),
        run_id: Some(submission.recommendation_id.clone()),
        trade_id: None,
        prompt_version: Some(submission.protocol_version.clone()),
        factor_version: None,
        data_fingerprint: None,
        factors_used: Vec::<FeedbackFactorUsage>::new(),
        model_probabilities_before_trade: ModelProbabilitySnapshot {
            selected_direction,
            selected_probability,
            long_score,
            short_score,
            win_prob_long,
            win_prob_short,
            uncertainty: (1.0 - submission.bbn_support_score.unwrap_or(selected_probability))
                .clamp(0.0, 1.0),
        },
        realized_outcome: outcome,
        pnl,
        regime_at_entry: regime_override.unwrap_or(Regime::ManipulationExpansion),
        structural_feedback: Some(StructuralFeedbackRefs {
            protocol_version: submission.protocol_version,
            recommendation_id: submission.recommendation_id,
            recommended_at: submission.recommended_at,
            node_id: submission.node_id,
            branch_id: submission.branch_id,
            scenario_id: submission.scenario_id,
            path_id: submission.path_id,
            followed_path: submission.followed_path,
            exit_reason: submission.exit_reason,
            notes: submission.notes,
        }),
        reflection_mismatch_tags: Vec::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{
        structural_source_reliability_em_fit_from_state, FeedbackRecord, ModelProbabilitySnapshot,
        OrderBlockVariantRuntimeEvidence, StructuralFeedbackRefs, WorkflowPhaseSnapshot,
        STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_MULTI_SOURCE_ITEMS,
    };
    use crate::types::{Direction, Regime};
    use chrono::Utc;

    fn calibration_row(
        path_id: &str,
        raw_path_score: f64,
        pending_reward_state: &str,
    ) -> StructuralPathRankingTargetRow {
        StructuralPathRankingTargetRow {
            rank: 1,
            candidate_set_id: "structural-candidates:NQ:test".to_string(),
            candidate_set_size: 3,
            path_id: path_id.to_string(),
            scenario_id: format!("scenario:{path_id}"),
            path_label: path_id.to_string(),
            regime_profit_branch_path: None,
            parent_regime_root: None,
            main_regime: None,
            sub_regime: None,
            sub_sub_regime_or_profit_factor: None,
            profit_factor: None,
            direction: "bull".to_string(),
            raw_path_score: Some(raw_path_score),
            calibrated_path_prob: None,
            path_prob_lower_bound: None,
            execution_gate_status: None,
            execution_gate_min_path_prob: None,
            execution_gate_reason: None,
            pending_reward_state: pending_reward_state.to_string(),
            maturity_mask: matches!(
                pending_reward_state,
                "matured_success" | "matured_failure" | "matured_invalidated"
            ),
            maturity_weight: if matches!(
                pending_reward_state,
                "matured_success" | "matured_failure" | "matured_invalidated"
            ) {
                1.0
            } else {
                0.0
            },
            calibrated_label: structural_path_ranking_reward_label(pending_reward_state),
            propensity_estimate: Some(0.5),
            ips_weight: Some(2.0),
            training_weight: if structural_path_ranking_reward_label(pending_reward_state).is_some()
            {
                Some(2.0)
            } else {
                None
            },
            regime_calibration_bucket: "NQ:trend".to_string(),
            behavior_policy_probability: 0.33,
            execution_propensity: Some(0.6),
            target_policy_probability_confidence: Some(0.55),
            target_policy_probability_lower_bound: Some(0.30),
            target_policy_reward_prior: Some(0.58),
            target_policy_reward_lower_bound: Some(0.28),
            experience_prior: 0.5,
            current_posterior: 0.7,
            structural_baseline_score: 0.4,
            regime_aux_qqq_hv_level: None,
            regime_aux_nq_vs_200d_pct: None,
            regime_aux_vix3m_level: None,
            regime_aux_qqq_hv_pct_rank_252: None,
            regime_aux_vvix_over_vix: None,
            ref_previous_day_high: None,
            ref_previous_day_low: None,
            ref_previous_day_close: None,
            ref_current_day_open: None,
            ref_previous_week_high: None,
            ref_previous_week_low: None,
            ref_previous_week_close: None,
            ref_current_week_open: None,
            ref_previous_month_high: None,
            ref_previous_month_low: None,
            ref_current_day_gap_upper: None,
            ref_current_day_gap_lower: None,
            ref_current_week_gap_upper: None,
            ref_current_week_gap_lower: None,
            ref_recent_week_gap_levels: None,
            ob_variant: None,
            ob_direction: None,
            ob_validation_state: None,
            ob_high: None,
            ob_low: None,
            ob_midpoint: None,
            ob_mitigation_count: None,
            ob_breaker_confirmed: None,
            ob_rejection_confirmed: None,
            ob_confidence: None,
            ob_fail_closed_reason: None,
            score_model_family: None,
            score_source_kind: None,
            score_model_artifact_uri: None,
            score_generator: None,
        }
    }

    #[test]
    fn order_block_context_does_not_relabel_generic_candidate_rows() {
        let mut row = calibration_row(
            "path:scenario:ORDER_BLOCK_NQ_YF_NONLIVE_DIAG:belief_regime_node:trend:fill_viable",
            0.68,
            "unobserved",
        );
        let snapshot = WorkflowSnapshot {
            latest_analyze: Some(WorkflowPhaseSnapshot {
                order_block_variant: Some(OrderBlockVariantRuntimeEvidence {
                    factor_name: "order_block_variant_classifier".to_string(),
                    variant: "breaker_block".to_string(),
                    direction: Direction::Bear,
                    high: Some(715.76),
                    low: Some(715.39),
                    midpoint: Some(715.575),
                    validation_state: "breaker_confirmed".to_string(),
                    mitigation_count: 805,
                    mitigation_pct: None,
                    failed_mitigation: false,
                    partial_fill_state: "none".to_string(),
                    breaker_confirmed: true,
                    rejection_confirmed: false,
                    confidence: 0.78,
                    fail_closed_reason: None,
                }),
                ..WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        structural_apply_order_block_variant_context(&snapshot, &mut row);

        assert_eq!(row.regime_profit_branch_path, None);
        assert_eq!(row.parent_regime_root, None);
        assert_eq!(row.main_regime, None);
        assert_eq!(row.sub_regime, None);
        assert_eq!(row.sub_sub_regime_or_profit_factor, None);
        assert_eq!(row.profit_factor, None);
        assert_eq!(row.ob_variant.as_deref(), Some("breaker_block"));
        assert_eq!(
            row.ob_validation_state.as_deref(),
            Some("breaker_confirmed")
        );
    }

    #[test]
    fn order_block_owner_rows_bind_rooted_branch_fields_from_runtime_evidence() {
        let branch_path =
            "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1";
        let mut row = calibration_row(branch_path, 0.68, "unobserved");
        let snapshot = WorkflowSnapshot {
            latest_analyze: Some(WorkflowPhaseSnapshot {
                order_block_variant: Some(OrderBlockVariantRuntimeEvidence {
                    factor_name: "order_block_variant_classifier".to_string(),
                    variant: "breaker_block".to_string(),
                    direction: Direction::Bear,
                    high: Some(715.76),
                    low: Some(715.39),
                    midpoint: Some(715.575),
                    validation_state: "breaker_confirmed".to_string(),
                    mitigation_count: 805,
                    mitigation_pct: None,
                    failed_mitigation: false,
                    partial_fill_state: "none".to_string(),
                    breaker_confirmed: true,
                    rejection_confirmed: false,
                    confidence: 0.78,
                    fail_closed_reason: None,
                }),
                ..WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        structural_apply_order_block_variant_context(&snapshot, &mut row);

        assert_eq!(row.regime_profit_branch_path.as_deref(), Some(branch_path));
        assert_eq!(row.parent_regime_root.as_deref(), Some("Transition"));
        assert_eq!(row.main_regime.as_deref(), Some("Transition"));
        assert_eq!(row.sub_regime.as_deref(), Some("OrderBlockVariant"));
        assert_eq!(
            row.sub_sub_regime_or_profit_factor.as_deref(),
            Some("ob_mitigation_breaker_rejection")
        );
        assert_eq!(
            row.profit_factor.as_deref(),
            Some("order_block_variant_classifier_v1")
        );
        assert_eq!(row.ob_variant.as_deref(), Some("breaker_block"));
    }

    fn source_em_event(
        source_label: &str,
        recommendation_id: &str,
        realized_outcome: Option<&str>,
    ) -> crate::state::StructuralPriorEvent {
        crate::state::StructuralPriorEvent {
            source_label: source_label.to_string(),
            symbol: "NQ".to_string(),
            recommendation_id: recommendation_id.to_string(),
            recommended_at: "2026-05-02T00:00:00Z".to_string(),
            node_id: "node-em".to_string(),
            branch_id: "branch-em".to_string(),
            scenario_id: "scenario-em".to_string(),
            path_id: format!("path-{recommendation_id}"),
            followed_path: true,
            realized_outcome: realized_outcome.map(str::to_string),
        }
    }

    #[test]
    fn reference_liquidity_levels_context_populates_target_row() {
        let mut snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        snapshot.latest_analyze = Some(WorkflowPhaseSnapshot {
            reference_liquidity_levels: Some(crate::ict::ReferenceLiquidityLevelsEvidence {
                factor_name: "reference_liquidity_levels".to_string(),
                source_frame: "mtf".to_string(),
                timezone: "America/New_York".to_string(),
                trading_day_rollover: "ny_1700_session_date".to_string(),
                current_trading_day: Some("2026-05-15".to_string()),
                current_trading_week: Some("2026-W20".to_string()),
                current_trading_month: Some("2026-05".to_string()),
                previous_day_high: Some(18595.0),
                previous_day_low: Some(18488.0),
                previous_day_close: Some(18510.5),
                current_day_open: Some(18522.0),
                previous_week_high: Some(18620.0),
                previous_week_low: Some(18390.0),
                previous_week_close: Some(18496.0),
                current_week_open: Some(18508.5),
                previous_month_high: Some(18840.0),
                previous_month_low: Some(17655.0),
                current_day_gap: Some(crate::ict::GapReferenceLevel {
                    label: "day_open_gap".to_string(),
                    period_key: Some("2026-05-15".to_string()),
                    previous_close: Some(18510.5),
                    current_open: Some(18522.0),
                    upper: Some(18522.0),
                    lower: Some(18510.5),
                    midpoint: Some(18516.25),
                    size: Some(11.5),
                    direction: Some("up_gap".to_string()),
                    active: true,
                }),
                current_week_gap: Some(crate::ict::GapReferenceLevel {
                    label: "week_open_gap".to_string(),
                    period_key: Some("2026-W20".to_string()),
                    previous_close: Some(18496.0),
                    current_open: Some(18508.5),
                    upper: Some(18508.5),
                    lower: Some(18496.0),
                    midpoint: Some(18502.25),
                    size: Some(12.5),
                    direction: Some("up_gap".to_string()),
                    active: true,
                }),
                recent_week_open_gaps: vec![crate::ict::GapReferenceLevel {
                    label: "week_open_gap".to_string(),
                    period_key: Some("2026-W20".to_string()),
                    previous_close: Some(18496.0),
                    current_open: Some(18508.5),
                    upper: Some(18508.5),
                    lower: Some(18496.0),
                    midpoint: Some(18502.25),
                    size: Some(12.5),
                    direction: Some("up_gap".to_string()),
                    active: true,
                }],
                confidence: 0.95,
                fail_closed_reason: None,
            }),
            ..WorkflowPhaseSnapshot::default()
        });
        let mut row = calibration_row("path-live", 0.5, "unobserved");

        structural_apply_reference_liquidity_levels_context(&snapshot, &mut row);

        assert_eq!(row.ref_previous_day_high, Some(18595.0));
        assert_eq!(row.ref_previous_week_low, Some(18390.0));
        assert_eq!(row.ref_previous_month_low, Some(17655.0));
        assert_eq!(row.ref_current_day_gap_upper, Some(18522.0));
        assert_eq!(row.ref_current_week_gap_lower, Some(18496.0));
        assert!(row
            .ref_recent_week_gap_levels
            .as_deref()
            .unwrap_or_default()
            .contains("2026-W20"));
    }

    #[test]
    fn source_reliability_em_readiness_requires_multi_source_overlap() {
        let mut state = StructuralPriorLearningState::default();
        state.event_ledger.extend([
            source_em_event("backtest", "rec-1", Some("win")),
            source_em_event("live", "rec-1", Some("win")),
            source_em_event("backtest", "rec-2", Some("loss")),
            source_em_event("live", "rec-2", Some("invalidated")),
            source_em_event("backtest", "rec-3", Some("breakeven")),
            source_em_event("live", "rec-3", Some("win")),
            source_em_event("backtest", "rec-4", Some("loss")),
            source_em_event("live", "rec-4", Some("pending")),
        ]);
        crate::state::refresh_structural_source_reliability_em_state(&mut state);

        let readiness = structural_source_reliability_em_readiness(&state);

        assert!(readiness.ready);
        assert_eq!(readiness.status, "ready");
        assert_eq!(readiness.candidate_item_count, 4);
        assert_eq!(readiness.labeled_item_count, 4);
        assert_eq!(readiness.multi_source_item_count, 3);
        assert_eq!(readiness.distinct_source_count, 2);
        assert_eq!(readiness.observed_label_count, 7);
        assert_eq!(readiness.max_sources_per_item, 2);
        assert_eq!(
            readiness.min_multi_source_items,
            STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_MULTI_SOURCE_ITEMS
        );
        assert_eq!(readiness.consensus_item_count, 3);
        assert_eq!(readiness.conflict_item_count, 1);
        assert!((readiness.avg_consensus_confidence.unwrap() - (2.5 / 3.0)).abs() < 1e-9);
        assert_eq!(readiness.min_consensus_confidence, Some(0.5));
        assert_eq!(
            readiness.em_iteration_count,
            crate::state::STRUCTURAL_SOURCE_RELIABILITY_EM_ITERATIONS
        );
        assert_eq!(readiness.em_latent_item_count, 3);
        assert_eq!(readiness.em_distinct_label_count, 3);
        assert_eq!(readiness.em_confusion_cell_count, 18);
        let avg_latent_confidence = readiness.avg_em_latent_confidence.unwrap();
        let min_latent_confidence = readiness.min_em_latent_confidence.unwrap();
        let avg_source_reliability = readiness.avg_em_source_reliability.unwrap();
        let min_source_reliability = readiness.min_em_source_reliability.unwrap();
        assert!(avg_latent_confidence >= min_latent_confidence);
        assert!((0.0..=1.0).contains(&avg_latent_confidence));
        assert!((0.0..=1.0).contains(&min_latent_confidence));
        assert!(avg_source_reliability >= min_source_reliability);
        assert!((0.0..=1.0).contains(&avg_source_reliability));
        assert!((0.0..=1.0).contains(&min_source_reliability));
        assert_eq!(readiness.persisted_source_summary_count, 2);
        assert_eq!(readiness.persisted_confusion_cell_count, 18);
        assert!(readiness.avg_persisted_source_reliability.is_some());
        assert!(readiness.min_persisted_source_reliability.is_some());
        assert_eq!(readiness.em_calibration_status.as_deref(), Some("ready"));
        assert_eq!(readiness.em_calibration_observation_count, 6);
        assert_eq!(readiness.em_calibration_source_count, 2);
        assert_eq!(
            readiness.em_calibration_min_observations,
            crate::state::STRUCTURAL_SOURCE_RELIABILITY_EM_MIN_CALIBRATION_OBSERVATIONS
        );
        assert!(readiness.em_calibration_brier_score.unwrap() >= 0.0);
        assert!(readiness.em_calibration_log_loss.unwrap() >= 0.0);
    }

    #[test]
    fn experience_prior_surface_path_includes_delayed_reward_replay_validation() {
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let mut snapshot = snapshot;
        if let Some(vote) = snapshot.latest_ensemble_vote.as_mut() {
            vote.posterior_active_regime = "trend".to_string();
            vote.posterior_probabilities = BTreeMap::from([("trend".to_string(), 0.8)]);
        }
        let discovered_path_id =
            build_structural_experience_prior_surface_artifact_with_prior_state(
                &snapshot,
                &crate::application::provider_catalog::ProviderCatalogAgentSurface::default(),
                &[],
                &StructuralPriorLearningState::default(),
            )
            .path
            .as_ref()
            .map(|path| path.entity_id.clone())
            .expect("sample path id");
        let feedback_history = vec![
            FeedbackRecord {
                timestamp: chrono::DateTime::parse_from_rfc3339("2026-04-30T00:30:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                symbol: "NQ".to_string(),
                source: "live_feedback".to_string(),
                run_id: None,
                trade_id: None,
                prompt_version: None,
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: ModelProbabilitySnapshot {
                    selected_direction: Direction::Bull,
                    selected_probability: 0.6,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    uncertainty: 0.2,
                },
                realized_outcome: "win".to_string(),
                pnl: 1.0,
                regime_at_entry: Regime::Accumulation,
                structural_feedback: Some(StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "rec-1".to_string(),
                    recommended_at: "2026-04-30T00:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id: discovered_path_id.clone(),
                    followed_path: true,
                    exit_reason: None,
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
            FeedbackRecord {
                timestamp: chrono::DateTime::parse_from_rfc3339("2026-04-30T03:00:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                symbol: "NQ".to_string(),
                source: "live_feedback".to_string(),
                run_id: None,
                trade_id: None,
                prompt_version: None,
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: ModelProbabilitySnapshot {
                    selected_direction: Direction::Bull,
                    selected_probability: 0.6,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    uncertainty: 0.2,
                },
                realized_outcome: "loss".to_string(),
                pnl: -1.0,
                regime_at_entry: Regime::Accumulation,
                structural_feedback: Some(StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "rec-2".to_string(),
                    recommended_at: "2026-04-30T01:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id: discovered_path_id.clone(),
                    followed_path: true,
                    exit_reason: None,
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
            FeedbackRecord {
                timestamp: chrono::DateTime::parse_from_rfc3339("2026-04-30T08:00:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                symbol: "NQ".to_string(),
                source: "live_feedback".to_string(),
                run_id: None,
                trade_id: None,
                prompt_version: None,
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: ModelProbabilitySnapshot {
                    selected_direction: Direction::Bull,
                    selected_probability: 0.6,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    uncertainty: 0.2,
                },
                realized_outcome: "invalidated".to_string(),
                pnl: -0.5,
                regime_at_entry: Regime::Accumulation,
                structural_feedback: Some(StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "rec-3".to_string(),
                    recommended_at: "2026-04-30T02:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id: discovered_path_id.clone(),
                    followed_path: true,
                    exit_reason: None,
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
            FeedbackRecord {
                timestamp: chrono::DateTime::parse_from_rfc3339("2026-04-30T03:45:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                symbol: "NQ".to_string(),
                source: "live_feedback".to_string(),
                run_id: None,
                trade_id: None,
                prompt_version: None,
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: ModelProbabilitySnapshot {
                    selected_direction: Direction::Bull,
                    selected_probability: 0.6,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    uncertainty: 0.2,
                },
                realized_outcome: "win".to_string(),
                pnl: 1.1,
                regime_at_entry: Regime::Accumulation,
                structural_feedback: Some(StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "rec-4".to_string(),
                    recommended_at: "2026-04-30T03:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id: discovered_path_id.clone(),
                    followed_path: true,
                    exit_reason: None,
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
            FeedbackRecord {
                timestamp: chrono::DateTime::parse_from_rfc3339("2026-04-30T10:00:00Z")
                    .unwrap()
                    .with_timezone(&Utc),
                symbol: "NQ".to_string(),
                source: "live_feedback".to_string(),
                run_id: None,
                trade_id: None,
                prompt_version: None,
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: ModelProbabilitySnapshot {
                    selected_direction: Direction::Bull,
                    selected_probability: 0.6,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    uncertainty: 0.2,
                },
                realized_outcome: "loss".to_string(),
                pnl: -1.2,
                regime_at_entry: Regime::Accumulation,
                structural_feedback: Some(StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "rec-5".to_string(),
                    recommended_at: "2026-04-30T04:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id: discovered_path_id.clone(),
                    followed_path: true,
                    exit_reason: None,
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
        ];
        let surface = build_structural_experience_prior_surface_artifact_with_prior_state(
            &snapshot,
            &crate::application::provider_catalog::ProviderCatalogAgentSurface::default(),
            &feedback_history,
            &StructuralPriorLearningState::default(),
        );
        let replay = surface
            .path
            .as_ref()
            .and_then(|path| path.delayed_reward_replay_validation.as_ref())
            .expect("path replay validation");
        assert_eq!(replay.status, "ready");
        assert!(replay.training_record_count >= 3);
        assert!(replay.evaluation_record_count >= 1);
        assert!(replay.resolution_brier_score.is_some());
    }

    #[test]
    fn source_reliability_em_fit_learns_lower_reliability_for_conflicting_source() {
        let mut state = StructuralPriorLearningState::default();
        state.event_ledger.extend([
            source_em_event("backtest", "rec-1", Some("win")),
            source_em_event("live", "rec-1", Some("win")),
            source_em_event("analyze", "rec-1", Some("loss")),
            source_em_event("backtest", "rec-2", Some("loss")),
            source_em_event("live", "rec-2", Some("loss")),
            source_em_event("analyze", "rec-2", Some("win")),
            source_em_event("backtest", "rec-3", Some("win")),
            source_em_event("live", "rec-3", Some("win")),
            source_em_event("analyze", "rec-3", Some("loss")),
        ]);

        let fit = structural_source_reliability_em_fit_from_state(&state);

        assert_eq!(
            fit.iteration_count,
            crate::state::STRUCTURAL_SOURCE_RELIABILITY_EM_ITERATIONS
        );
        let backtest = fit.source_reliability["backtest"];
        let live = fit.source_reliability["live"];
        let analyze = fit.source_reliability["analyze"];
        assert!(backtest > analyze);
        assert!(live > analyze);
        assert!(
            structural_source_reliability_multiplier(
                &state,
                "backtest",
                Some(&fit.source_reliability)
            ) > structural_source_reliability_multiplier(
                &state,
                "analyze",
                Some(&fit.source_reliability)
            )
        );
    }

    #[test]
    fn panel_derived_prior_uses_persisted_source_reliability_em_summary() {
        let stats = crate::state::StructuralPriorStats {
            source_panel_summaries: BTreeMap::from([
                (
                    "analyze".to_string(),
                    crate::state::StructuralPriorSourceSummary {
                        weighted_success_mass: 1.0,
                        ..crate::state::StructuralPriorSourceSummary::default()
                    },
                ),
                (
                    "backtest".to_string(),
                    crate::state::StructuralPriorSourceSummary {
                        weighted_failure_mass: 1.0,
                        ..crate::state::StructuralPriorSourceSummary::default()
                    },
                ),
            ]),
            ..crate::state::StructuralPriorStats::default()
        };
        let state = crate::state::StructuralPriorLearningState {
            source_reliability_em_summaries: BTreeMap::from([
                (
                    "analyze".to_string(),
                    crate::state::StructuralSourceReliabilityEmSourceSummary {
                        source_label: "analyze".to_string(),
                        iteration_count: crate::state::STRUCTURAL_SOURCE_RELIABILITY_EM_ITERATIONS,
                        latent_item_count: 3,
                        distinct_label_count: 2,
                        confusion_cell_count: 4,
                        posterior_reliability: 0.2,
                        min_diagonal_probability: 0.2,
                        ..crate::state::StructuralSourceReliabilityEmSourceSummary::default()
                    },
                ),
                (
                    "backtest".to_string(),
                    crate::state::StructuralSourceReliabilityEmSourceSummary {
                        source_label: "backtest".to_string(),
                        iteration_count: crate::state::STRUCTURAL_SOURCE_RELIABILITY_EM_ITERATIONS,
                        latent_item_count: 3,
                        distinct_label_count: 2,
                        confusion_cell_count: 4,
                        posterior_reliability: 0.9,
                        min_diagonal_probability: 0.8,
                        ..crate::state::StructuralSourceReliabilityEmSourceSummary::default()
                    },
                ),
            ]),
            ..crate::state::StructuralPriorLearningState::default()
        };

        let prior = structural_panel_derived_smoothed_prior(&stats, &state)
            .expect("panel prior from persisted EM reliability");

        assert!(prior < 0.4);
        assert!(prior > 0.35);
    }

    #[test]
    fn structural_prior_maturity_diagnostics_count_unresolved_followed_feedback() {
        let stats = StructuralPriorStats {
            observations: 5,
            followed_count: 4,
            wins: 1,
            losses: 1,
            breakevens: 1,
            invalidated: 0,
            abandoned: 0,
            not_followed: 1,
            smoothed_prior: 0.5,
            target_policy_reward_prior: 0.6,
            target_policy_reward_lower_bound: 0.3,
            delayed_reward_elapsed_feedback_count: 3,
            delayed_reward_elapsed_hours_at_risk: 6.0,
            delayed_reward_avg_elapsed_hours: 2.0,
            delayed_reward_resolution_hazard_per_hour: 3.0 / 6.0,
            delayed_reward_expected_resolution_hours: 2.0,
            delayed_reward_survival_probability_1h: (-0.5_f64).exp(),
            delayed_reward_survival_probability_4h: (-2.0_f64).exp(),
            delayed_reward_survival_probability_24h: (-12.0_f64).exp(),
            delayed_reward_success_hazard_per_hour: 1.5 / 6.0,
            delayed_reward_failure_hazard_per_hour: 1.5 / 6.0,
            delayed_reward_success_cumulative_incidence_4h: 0.5 * (1.0 - (-2.0_f64).exp()),
            delayed_reward_failure_cumulative_incidence_4h: 0.5 * (1.0 - (-2.0_f64).exp()),
            delayed_reward_resolution_horizon_1h_count: 3,
            delayed_reward_resolution_within_1h_count: 1,
            delayed_reward_resolution_probability_1h: 2.0 / 5.0,
            delayed_reward_resolution_horizon_4h_count: 3,
            delayed_reward_resolution_within_4h_count: 3,
            delayed_reward_resolution_probability_4h: 4.0 / 5.0,
            delayed_reward_resolution_horizon_24h_count: 3,
            delayed_reward_resolution_within_24h_count: 3,
            delayed_reward_resolution_probability_24h: 4.0 / 5.0,
            ..StructuralPriorStats::default()
        };

        assert_eq!(
            structural_prior_matured_feedback_count(Some(&stats)),
            Some(3)
        );
        assert_eq!(
            structural_prior_unresolved_feedback_count(Some(&stats)),
            Some(1)
        );
        assert_eq!(structural_prior_maturity_coverage(Some(&stats)), Some(0.75));
        assert_eq!(structural_prior_censoring_rate(Some(&stats)), Some(0.25));
        assert_eq!(
            structural_prior_delayed_reward_resolution_probability(Some(&stats)),
            Some(4.0 / 6.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_censoring_probability(Some(&stats)),
            Some(2.0 / 6.0)
        );
        assert!(
            (structural_prior_censoring_adjusted_reward_prior(Some(&stats)).unwrap()
                - ((0.6 * (4.0 / 6.0)) + (0.5 * (2.0 / 6.0))))
                .abs()
                < 1e-9
        );
        assert!(
            (structural_prior_censoring_adjusted_reward_lower_bound(Some(&stats)).unwrap()
                - ((0.3 * (4.0 / 6.0)) + (0.5 * 0.5 * (2.0 / 6.0))))
                .abs()
                < 1e-9
        );
        let expected_competing_risks: [f64; 4] = [2.5 / 7.0, 2.5 / 7.0, 1.0 / 7.0, 1.0 / 7.0];
        let expected_competing_risk_entropy: f64 = expected_competing_risks
            .iter()
            .map(|risk| -*risk * (*risk).ln())
            .sum();
        assert_eq!(
            structural_prior_delayed_reward_success_competing_risk(Some(&stats)),
            Some(expected_competing_risks[0])
        );
        assert_eq!(
            structural_prior_delayed_reward_failure_competing_risk(Some(&stats)),
            Some(expected_competing_risks[1])
        );
        assert_eq!(
            structural_prior_delayed_reward_invalidation_competing_risk(Some(&stats)),
            Some(expected_competing_risks[2])
        );
        assert_eq!(
            structural_prior_delayed_reward_abandonment_competing_risk(Some(&stats)),
            Some(expected_competing_risks[3])
        );
        assert!(
            (structural_prior_delayed_reward_competing_risk_entropy(Some(&stats)).unwrap()
                - expected_competing_risk_entropy)
                .abs()
                < 1e-9
        );
        assert_eq!(
            structural_prior_delayed_reward_elapsed_feedback_count(Some(&stats)),
            Some(3)
        );
        assert_eq!(
            structural_prior_delayed_reward_elapsed_hours_at_risk(Some(&stats)),
            Some(6.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_avg_elapsed_hours(Some(&stats)),
            Some(2.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_hazard_per_hour(Some(&stats)),
            Some(3.0 / 6.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_expected_resolution_hours(Some(&stats)),
            Some(2.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_survival_probability_1h(Some(&stats)),
            Some((-0.5_f64).exp())
        );
        assert_eq!(
            structural_prior_delayed_reward_survival_probability_4h(Some(&stats)),
            Some((-2.0_f64).exp())
        );
        assert_eq!(
            structural_prior_delayed_reward_survival_probability_24h(Some(&stats)),
            Some((-12.0_f64).exp())
        );
        assert_eq!(
            structural_prior_delayed_reward_success_hazard_per_hour(Some(&stats)),
            Some(1.5 / 6.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_failure_hazard_per_hour(Some(&stats)),
            Some(1.5 / 6.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_success_cumulative_incidence_4h(Some(&stats)),
            Some(0.5 * (1.0 - (-2.0_f64).exp()))
        );
        assert_eq!(
            structural_prior_delayed_reward_failure_cumulative_incidence_4h(Some(&stats)),
            Some(0.5 * (1.0 - (-2.0_f64).exp()))
        );
        assert_eq!(
            structural_prior_delayed_reward_invalidation_cumulative_incidence_4h(Some(&stats)),
            None
        );
        assert_eq!(
            structural_prior_delayed_reward_abandonment_cumulative_incidence_4h(Some(&stats)),
            None
        );
        assert_eq!(
            structural_prior_delayed_reward_invalidation_hazard_per_hour(Some(&stats)),
            None
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_horizon_1h_count(Some(&stats)),
            Some(3)
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_within_1h_count(Some(&stats)),
            Some(1)
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_probability_1h(Some(&stats)),
            Some(2.0 / 5.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_probability_4h(Some(&stats)),
            Some(4.0 / 5.0)
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_probability_24h(Some(&stats)),
            Some(4.0 / 5.0)
        );

        let not_followed_only = StructuralPriorStats {
            observations: 1,
            not_followed: 1,
            ..StructuralPriorStats::default()
        };
        assert_eq!(
            structural_prior_matured_feedback_count(Some(&not_followed_only)),
            Some(0)
        );
        assert_eq!(
            structural_prior_unresolved_feedback_count(Some(&not_followed_only)),
            Some(0)
        );
        assert_eq!(
            structural_prior_maturity_coverage(Some(&not_followed_only)),
            None
        );
        assert_eq!(
            structural_prior_censoring_rate(Some(&not_followed_only)),
            None
        );
        assert_eq!(
            structural_prior_delayed_reward_resolution_probability(Some(&not_followed_only)),
            None
        );
        assert_eq!(
            structural_prior_delayed_reward_success_competing_risk(Some(&not_followed_only)),
            None
        );
    }

    #[test]
    fn panel_derived_prior_uses_source_confusion_concentration() {
        let mut stats = StructuralPriorStats::default();
        stats.source_panel_summaries.insert(
            "noisy".to_string(),
            crate::state::StructuralPriorSourceSummary {
                weighted_success_mass: 2.0,
                ..crate::state::StructuralPriorSourceSummary::default()
            },
        );
        let mut state = StructuralPriorLearningState::default();
        state.source_reliability_posteriors.insert(
            "noisy".to_string(),
            crate::state::StructuralSourceReliabilityPosterior {
                source_label: "noisy".to_string(),
                observations: 2,
                weighted_observation_mass: 2.0,
                posterior_reliability: 1.0,
                outcome_confusion: BTreeMap::from([
                    (
                        "tp->positive_executed".to_string(),
                        crate::state::StructuralSourceOutcomeConfusionCell {
                            observed_outcome: "tp".to_string(),
                            credit_class: "positive_executed".to_string(),
                            observations: 1,
                            weighted_observation_mass: 1.0,
                            weighted_success_mass: 1.0,
                            ..crate::state::StructuralSourceOutcomeConfusionCell::default()
                        },
                    ),
                    (
                        "take_profit->positive_executed".to_string(),
                        crate::state::StructuralSourceOutcomeConfusionCell {
                            observed_outcome: "take_profit".to_string(),
                            credit_class: "positive_executed".to_string(),
                            observations: 1,
                            weighted_observation_mass: 1.0,
                            weighted_success_mass: 1.0,
                            ..crate::state::StructuralSourceOutcomeConfusionCell::default()
                        },
                    ),
                ]),
                ..crate::state::StructuralSourceReliabilityPosterior::default()
            },
        );

        let prior =
            structural_panel_derived_smoothed_prior(&stats, &state).expect("panel-derived prior");

        assert!((prior - (2.0 / 3.0)).abs() < 1e-9);
    }

    fn calibrated_evaluation_row(
        path_id: &str,
        raw_path_score: f64,
        calibrated_path_prob: f64,
        pending_reward_state: &str,
        bucket: &str,
    ) -> StructuralPathRankingTargetRow {
        StructuralPathRankingTargetRow {
            calibrated_path_prob: Some(calibrated_path_prob),
            path_prob_lower_bound: Some((calibrated_path_prob - 0.1).clamp(0.0, 1.0)),
            regime_calibration_bucket: bucket.to_string(),
            ..calibration_row(path_id, raw_path_score, pending_reward_state)
        }
    }

    #[test]
    fn structural_path_probability_calibration_writes_probabilities_for_raw_scored_rows() {
        let mut artifact = StructuralPathRankingTargetArtifact {
            protocol_version: "structural-path-ranking-target-v1".to_string(),
            symbol: "NQ".to_string(),
            candidate_set_id: "structural-candidates:NQ:test".to_string(),
            candidate_set_size: 3,
            generated_at: "2026-05-02T00:00:00Z".to_string(),
            rows: vec![
                calibration_row("path-success", 0.8, "matured_success"),
                calibration_row("path-failure", 0.2, "matured_invalidated"),
                calibration_row("path-live", 0.6, "unobserved"),
                StructuralPathRankingTargetRow {
                    raw_path_score: None,
                    ..calibration_row("path-no-score", 0.4, "matured_success")
                },
            ],
        };

        let report = apply_structural_path_probability_calibration(&mut artifact);

        assert_eq!(report.status, "calibrated");
        assert_eq!(report.observed_rows, 2);
        assert_eq!(report.calibrated_rows, 3);
        assert_eq!(report.bins.len(), 1);
        assert!((report.bins[0].calibrated_path_prob - 0.5).abs() < 1e-9);
        assert!(report.bins[0].path_prob_lower_bound < 0.5);
        assert!(artifact
            .rows
            .iter()
            .filter(|row| row.raw_path_score.is_some())
            .all(|row| row.calibrated_path_prob == Some(0.5)));
        assert_eq!(
            artifact
                .rows
                .iter()
                .find(|row| row.path_id == "path-no-score")
                .and_then(|row| row.calibrated_path_prob),
            None
        );
        assert!(artifact
            .rows
            .iter()
            .filter(|row| row.raw_path_score.is_some())
            .all(|row| row.path_prob_lower_bound.is_some()));
        assert!(artifact
            .rows
            .iter()
            .filter(|row| row.raw_path_score.is_some())
            .all(|row| row.execution_gate_status.as_deref() == Some("observe")));
        assert!(artifact
            .rows
            .iter()
            .filter(|row| row.raw_path_score.is_some())
            .all(|row| row.execution_gate_min_path_prob
                == Some(
                    crate::belief_core::ranking_label::STRUCTURAL_PATH_RANKING_EXECUTION_GATE_MIN_PATH_PROB,
                )));
        assert_eq!(
            artifact
                .rows
                .iter()
                .find(|row| row.path_id == "path-no-score")
                .and_then(|row| row.execution_gate_status.as_deref()),
            None
        );
        let matured_success = artifact
            .rows
            .iter()
            .find(|row| row.path_id == "path-success")
            .unwrap();
        assert_eq!(matured_success.calibrated_label, Some(1.0));
        assert_eq!(matured_success.ips_weight, Some(2.0));
        assert_eq!(matured_success.training_weight, Some(2.0));
        assert_eq!(
            artifact
                .rows
                .iter()
                .find(|row| row.path_id == "path-live")
                .and_then(|row| row.training_weight),
            None
        );
    }

    #[test]
    fn structural_path_probability_calibration_evaluation_scores_mature_calibrated_rows() {
        let rows = vec![
            calibrated_evaluation_row("trend-win", 0.8, 0.8, "matured_success", "NQ:trend"),
            calibrated_evaluation_row("trend-loss", 0.6, 0.6, "matured_failure", "NQ:trend"),
            calibrated_evaluation_row("range-loss", 0.2, 0.2, "matured_invalidated", "NQ:range"),
            calibrated_evaluation_row("range-win", 0.4, 0.4, "matured_success", "NQ:range"),
            calibrated_evaluation_row("pending", 0.5, 0.5, "unobserved", "NQ:trend"),
            StructuralPathRankingTargetRow {
                raw_path_score: None,
                ..calibrated_evaluation_row("no-score", 0.5, 0.5, "matured_success", "NQ:trend")
            },
        ];

        let report = evaluate_structural_path_probability_calibration_rows(&rows);

        assert_eq!(report.status, "evaluated");
        assert_eq!(report.eligible_rows, 4);
        assert!((report.brier_score.unwrap() - 0.20).abs() < 1e-9);
        assert!((report.expected_calibration_error.unwrap() - 0.20).abs() < 1e-9);
        assert!((report.max_calibration_error.unwrap() - 0.20).abs() < 1e-9);
        assert_eq!(report.bins.len(), 2);
    }

    #[test]
    fn structural_path_probability_calibration_evaluation_reports_propensity_weighted_brier() {
        let mut low_propensity_loss = calibrated_evaluation_row(
            "low-propensity-loss",
            0.9,
            0.9,
            "matured_failure",
            "NQ:trend",
        );
        low_propensity_loss.propensity_estimate = Some(0.25);
        low_propensity_loss.ips_weight = Some(4.0);
        low_propensity_loss.training_weight = Some(4.0);
        let mut high_propensity_win = calibrated_evaluation_row(
            "high-propensity-win",
            0.5,
            0.5,
            "matured_success",
            "NQ:trend",
        );
        high_propensity_win.propensity_estimate = Some(1.0);
        high_propensity_win.ips_weight = Some(1.0);
        high_propensity_win.training_weight = Some(1.0);

        let report = evaluate_structural_path_probability_calibration_rows(&[
            low_propensity_loss,
            high_propensity_win,
        ]);

        assert_eq!(report.status, "evaluated");
        assert_eq!(report.eligible_rows, 2);
        assert_eq!(report.propensity_weighted_rows, 2);
        assert!((report.brier_score.unwrap() - 0.53).abs() < 1e-9);
        assert!((report.propensity_weighted_brier_score.unwrap() - 0.698).abs() < 1e-9);
    }

    fn feedback_record_for_target_export(
        recommendation_id: &str,
        path_id: &str,
        outcome: &str,
        selected_probability: f64,
    ) -> FeedbackRecord {
        FeedbackRecord {
            timestamp: Utc::now(),
            symbol: "NQ".to_string(),
            source: "structural_feedback_submission".to_string(),
            run_id: Some(recommendation_id.to_string()),
            trade_id: Some(recommendation_id.to_string()),
            prompt_version: None,
            factor_version: None,
            data_fingerprint: None,
            factors_used: Vec::new(),
            model_probabilities_before_trade: ModelProbabilitySnapshot {
                selected_direction: Direction::Bull,
                selected_probability,
                long_score: selected_probability,
                short_score: 1.0 - selected_probability,
                win_prob_long: selected_probability,
                win_prob_short: 1.0 - selected_probability,
                uncertainty: 1.0 - selected_probability,
            },
            realized_outcome: outcome.to_string(),
            pnl: if outcome == "win" { 1.0 } else { -1.0 },
            regime_at_entry: Regime::ManipulationExpansion,
            structural_feedback: Some(StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: recommendation_id.to_string(),
                recommended_at: "2026-05-09T00:00:00Z".to_string(),
                node_id: "NQ:belief_regime_node:trend".to_string(),
                branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                scenario_id: format!("scenario:{path_id}"),
                path_id: path_id.to_string(),
                followed_path: true,
                exit_reason: None,
                notes: None,
            }),
            reflection_mismatch_tags: Vec::new(),
        }
    }

    #[test]
    fn target_export_projects_mature_structural_feedback_into_history_rows() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary";
        let feedback = vec![
            feedback_record_for_target_export("rec-win", path_id, "win", 0.91),
            feedback_record_for_target_export("rec-loss", path_id, "loss", 0.24),
        ];

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();

        assert!(summary.history_mature_rows >= 2);
        assert!(summary.history_rows_with_raw_path_score >= 2);
        assert!(
            history_rows
                .iter()
                .filter(|row| row.path_id == path_id && row.maturity_mask)
                .count()
                >= 2
        );
        assert!(history_rows.iter().any(|row| {
            row.path_id == path_id
                && row.pending_reward_state == "matured_success"
                && row.raw_path_score == Some(0.91)
        }));
        assert!(history_rows.iter().any(|row| {
            row.path_id == path_id
                && row.pending_reward_state == "matured_failure"
                && row.raw_path_score == Some(0.24)
        }));
    }

    #[test]
    fn target_export_marks_aggregate_paper_execution_feedback_as_live_trade_usable() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "TrendExpansion -> IntradayMomentum -> mature_edge -> paper_exec_v1";
        let feedback = (0..30)
            .map(|index| {
                let outcome = if index < 20 { "win" } else { "loss" };
                let mut record = feedback_record_for_target_export(
                    &format!("paper-exec-{index}"),
                    path_id,
                    outcome,
                    0.72,
                );
                record.source =
                    "auto_quant_real_trades:paper_execution_feedback:nq_compound_test".to_string();
                record.pnl = if index < 20 { 1.0 } else { -0.5 };
                record
            })
            .collect::<Vec<_>>();

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let aggregate = current_rows
            .iter()
            .find(|row| {
                row.path_id == path_id
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-aggregate:")
            })
            .expect("aggregate paper execution feedback row");

        assert_eq!(aggregate.pending_reward_state, "matured_success");
        assert_eq!(
            aggregate.execution_gate_status.as_deref(),
            Some("live_trade_usable")
        );
        assert!(aggregate.training_weight.unwrap_or_default() > 0.0);

        let status = crate::application::entry_models::policy_training_status(
            temp.path().to_str().unwrap(),
            "NQ",
            None,
        )
        .unwrap();
        assert_eq!(status.factor_profitability_lifecycle.live_ready_count, 1);
        assert!(status.factor_profitability_lifecycle.trade_usable);
    }

    #[test]
    fn target_export_does_not_mark_simulated_aggregate_feedback_as_live_trade_usable() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "TrendExpansion -> IntradayMomentum -> mature_edge -> simulated_exec_v1";
        let feedback = (0..30)
            .map(|index| {
                let outcome = if index < 20 { "win" } else { "loss" };
                let mut record = feedback_record_for_target_export(
                    &format!("sim-exec-{index}"),
                    path_id,
                    outcome,
                    0.72,
                );
                record.source =
                    "auto_quant_replay:simulated_backtest:retained_real_event_label".to_string();
                record.pnl = if index < 20 { 1.0 } else { -0.5 };
                record
            })
            .collect::<Vec<_>>();

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let aggregate = current_rows
            .iter()
            .find(|row| {
                row.path_id == path_id
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-aggregate:")
            })
            .expect("aggregate simulated feedback row");

        assert_eq!(aggregate.pending_reward_state, "matured_success");
        assert_ne!(
            aggregate.execution_gate_status.as_deref(),
            Some("live_trade_usable")
        );

        let status = crate::application::entry_models::policy_training_status(
            temp.path().to_str().unwrap(),
            "NQ",
            None,
        )
        .unwrap();
        assert_eq!(status.factor_profitability_lifecycle.live_ready_count, 0);
        assert!(!status.factor_profitability_lifecycle.trade_usable);
    }

    #[test]
    fn target_export_does_not_mark_spoofed_aggregate_feedback_substring_as_live_trade_usable() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "TrendExpansion -> IntradayMomentum -> mature_edge -> spoofed_exec_v1";
        let feedback = (0..30)
            .map(|index| {
                let outcome = if index < 20 { "win" } else { "loss" };
                let mut record = feedback_record_for_target_export(
                    &format!("spoofed-exec-{index}"),
                    path_id,
                    outcome,
                    0.72,
                );
                record.source =
                    "auto_quant_real_trades:without-broker-paper_execution_feedback:nq_compound_test"
                        .to_string();
                record.pnl = if index < 20 { 1.0 } else { -0.5 };
                record
            })
            .collect::<Vec<_>>();

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let aggregate = current_rows
            .iter()
            .find(|row| {
                row.path_id == path_id
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-aggregate:")
            })
            .expect("aggregate spoofed feedback row");

        assert_eq!(aggregate.pending_reward_state, "matured_success");
        assert_ne!(
            aggregate.execution_gate_status.as_deref(),
            Some("live_trade_usable")
        );

        let status = crate::application::entry_models::policy_training_status(
            temp.path().to_str().unwrap(),
            "NQ",
            None,
        )
        .unwrap();
        assert_eq!(status.factor_profitability_lifecycle.live_ready_count, 0);
        assert!(!status.factor_profitability_lifecycle.trade_usable);
    }

    #[test]
    fn target_export_skips_infrastructure_negative_feedback_rows() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "TrendExpansion -> PullbackContinuation -> mss_cisd_pullback_reclaim -> trend_pullback_reclaim_v1";
        let mut infrastructure_negative =
            feedback_record_for_target_export("rec-provider-failure", path_id, "loss", 0.62);
        if let Some(refs) = infrastructure_negative.structural_feedback.as_mut() {
            refs.exit_reason = Some("infrastructure_negative_sample:provider_failure".to_string());
            refs.notes = Some("negative_sample_type=provider_authority".to_string());
        }

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[infrastructure_negative],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();

        assert!(
            history_rows.iter().all(|row| row.path_id != path_id),
            "provider/bootstrap failures must not become strategy boundary negatives"
        );
        assert_eq!(summary.history_mature_rows, 0);
        assert_eq!(summary.history_rows_with_training_weight, 0);
    }

    #[test]
    fn path_history_skips_infrastructure_negative_but_keeps_strategy_negative() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id = "TrendExpansion -> PullbackContinuation -> mss_cisd_pullback_reclaim -> trend_pullback_reclaim_v1";
        let mut infrastructure_negative =
            feedback_record_for_target_export("rec-provider-failure", path_id, "loss", 0.62);
        if let Some(refs) = infrastructure_negative.structural_feedback.as_mut() {
            refs.exit_reason = Some("infrastructure_negative_sample:provider_failure".to_string());
            refs.notes = Some("negative_sample_type=provider_authority".to_string());
        }
        let mut strategy_negative =
            feedback_record_for_target_export("rec-trend-pullback-loss", path_id, "loss", 0.32);
        if let Some(refs) = strategy_negative.structural_feedback.as_mut() {
            refs.exit_reason =
                Some("negative_boundary_sample:trend_pullback_do_not_trade".to_string());
            refs.notes = Some("negative_sample_type=trend_pullback_do_not_trade".to_string());
        }

        let path_history = build_structural_path_history_artifact(
            &snapshot,
            &[infrastructure_negative, strategy_negative],
        );

        assert_eq!(path_history.summary.total_records, 1);
        let path = path_history
            .paths
            .iter()
            .find(|summary| summary.path_id == path_id)
            .expect("strategy negative should remain path-history evidence");
        assert_eq!(path.total_records, 1);
        assert_eq!(path.losses, 1);
    }

    #[test]
    fn target_export_keeps_zero_probability_feedback_as_scored_history_rows() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let path_id =
            "Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1";
        let feedback = vec![
            feedback_record_for_target_export("zero-prob-win", path_id, "win", 0.0),
            feedback_record_for_target_export("zero-prob-loss", path_id, "loss", 0.0),
        ];

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();

        let zero_probability_rows = history_rows
            .iter()
            .filter(|row| row.path_id == path_id && row.maturity_mask)
            .collect::<Vec<_>>();
        assert!(zero_probability_rows.len() >= 2);
        assert!(zero_probability_rows
            .iter()
            .any(|row| row.raw_path_score.is_some()));
        assert!(zero_probability_rows
            .iter()
            .all(|row| row.training_weight.is_some()));
        assert!(zero_probability_rows
            .iter()
            .any(|row| row.pending_reward_state == "matured_success"));
        assert!(zero_probability_rows
            .iter()
            .any(|row| row.pending_reward_state == "matured_failure"));
        assert!(summary.history_mature_rows >= 2);
        assert!(summary.history_rows_with_raw_path_score >= 2);
    }

    #[test]
    fn target_export_adds_aggregate_success_for_positive_expectancy_low_winrate_branch() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let branch_path = "TrendExpansion -> PullbackContinuation -> mss_cisd_pullback_reclaim -> trend_pullback_reclaim_v1";
        let mut feedback = Vec::new();
        for index in 0..30 {
            let win = index < 14;
            let mut record = feedback_record_for_target_export(
                &format!("trend-pullback-{index}"),
                branch_path,
                if win { "win" } else { "loss" },
                0.58,
            );
            record.pnl = if win { 2.0 } else { -1.0 };
            feedback.push(record);
        }

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();

        let aggregate = history_rows
            .iter()
            .find(|row| {
                row.path_id == branch_path
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-aggregate:NQ:")
            })
            .expect("aggregate same-root row");
        assert_eq!(aggregate.pending_reward_state, "matured_success");
        assert_eq!(aggregate.calibrated_label, Some(1.0));
        assert!(aggregate.raw_path_score.unwrap() > 0.5);
        assert_eq!(
            aggregate.regime_profit_branch_path.as_deref(),
            Some(branch_path)
        );
        assert_eq!(aggregate.main_regime.as_deref(), Some("TrendExpansion"));
        assert_eq!(
            aggregate.profit_factor.as_deref(),
            Some("trend_pullback_reclaim_v1")
        );
        assert_eq!(
            history_rows
                .iter()
                .filter(|row| row.path_id == branch_path
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-history:NQ:")
                    && row.pending_reward_state == "matured_success")
                .count(),
            14
        );
        assert_eq!(
            history_rows
                .iter()
                .filter(|row| row.path_id == branch_path
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-history:NQ:")
                    && row.pending_reward_state == "matured_failure")
                .count(),
            16
        );
    }

    #[test]
    fn prefer_history_runtime_selects_exact_feedback_branch_over_generic_pre_bayes_bundle() {
        let exact_branch_path = "TrendExpansion -> MicroTrendPullbackReclaim -> ibkr_futures_micro_trend_pullback_reclaim_gate1_v1";
        let generic_pre_bayes_path =
            "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1";
        let mut snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(WorkflowPhaseSnapshot {
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                    "regime_bundle_branch_paths_json".to_string(),
                    serde_json::to_string(&vec![generic_pre_bayes_path]).unwrap(),
                )]),
                ..WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };
        let mut feedback = Vec::new();
        for index in 0..30 {
            let mut record = feedback_record_for_target_export(
                &format!("mgc-exact-feedback-{index}"),
                exact_branch_path,
                if index < 20 { "win" } else { "loss" },
                0.62,
            );
            record.pnl = if index < 20 { 1.0 } else { -0.5 };
            feedback.push(record);
        }
        snapshot.latest_update = feedback.last().map(|record| WorkflowPhaseSnapshot {
            phase: "update".to_string(),
            run_id: "update:NQ:mgc-exact-feedback".to_string(),
            structural_feedback: record.structural_feedback.clone(),
            ..WorkflowPhaseSnapshot::default()
        });
        let temp = tempfile::tempdir().unwrap();
        export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let artifact_dir = temp
            .path()
            .join("NQ")
            .join(STRUCTURAL_PATH_RANKING_TARGET_EXPORT_DIR);
        fs::write(
            artifact_dir.join("stale_registered_scores.jsonl"),
            format!(
                "{}\n{}\n",
                serde_json::json!({
                    "candidate_set_id": "structural-candidates:NQ:stale",
                    "path_id": generic_pre_bayes_path,
                    "raw_path_score": 0.91,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_model",
                    "score_generator": "test-stale-generic-scorer"
                }),
                serde_json::json!({
                    "candidate_set_id": "structural-candidates:NQ:stale",
                    "path_id": "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1",
                    "raw_path_score": 0.90,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_model",
                    "score_generator": "test-stale-generic-scorer"
                })
            ),
        )
        .unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "stale_registered_scores.jsonl".to_string(),
                model_artifact_uri: None,
                score_column: "raw_path_score".to_string(),
                trained_rows: 4,
                history_rows: 4,
                calibration_rows: 4,
                selected_features: vec!["structural_baseline_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );
        let bundle = structural_recommended_path_bundle_from_candidates(
            "NQ".to_string(),
            selection.candidate_set_id,
            selection.runtime,
            structural_current_pre_bayes_regime_profit_branch_path(&snapshot).as_deref(),
            selection.candidate_paths,
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, exact_branch_path);
        assert_eq!(
            bundle.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
        assert_eq!(
            bundle.path_ranker_runtime_source.as_deref(),
            Some("history_path")
        );
    }

    #[test]
    fn target_export_adds_aggregate_failure_for_negative_expectancy_trend_pullback_branch() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let branch_path = "TrendExpansion -> PullbackContinuation -> mss_cisd_pullback_reclaim -> trend_pullback_reclaim_v1";
        let mut feedback = Vec::new();
        for index in 0..30 {
            let win = index < 12;
            let mut record = feedback_record_for_target_export(
                &format!("trend-pullback-neg-{index}"),
                branch_path,
                if win { "win" } else { "loss" },
                0.58,
            );
            record.pnl = if win { 1.0 } else { -1.0 };
            feedback.push(record);
        }

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();

        let aggregate = history_rows
            .iter()
            .find(|row| {
                row.path_id == branch_path
                    && row
                        .candidate_set_id
                        .starts_with("structural-feedback-aggregate:NQ:")
            })
            .expect("aggregate same-root row");
        assert_eq!(aggregate.pending_reward_state, "matured_failure");
        assert_eq!(aggregate.calibrated_label, Some(0.0));
        assert!(aggregate.raw_path_score.unwrap() < 0.5);
        assert_eq!(
            aggregate.regime_profit_branch_path.as_deref(),
            Some(branch_path)
        );
        assert_eq!(aggregate.main_regime.as_deref(), Some("TrendExpansion"));
    }

    #[test]
    fn target_export_surfaces_exact_feedback_paths_in_current_rows() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let branch_path =
            "Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12";
        let feedback = vec![
            feedback_record_for_target_export("branch-rec-win", branch_path, "win", 0.83),
            feedback_record_for_target_export("branch-rec-loss", branch_path, "loss", 0.42),
        ];

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();

        assert!(
            current_rows
                .iter()
                .filter(|row| row.path_id == branch_path)
                .count()
                >= 1,
            "current structural path-ranking target must expose the exact feedback path id"
        );
    }

    #[test]
    fn recommended_path_bundle_prefers_exact_feedback_path_when_runtime_uses_history() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let branch_path =
            "Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12";
        let feedback = vec![feedback_record_for_target_export(
            "branch-rec-win",
            branch_path,
            "win",
            0.97,
        )];

        export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY,
        )
        .unwrap();

        let bundle =
            build_structural_recommended_path_bundle_artifact_with_state_dir_and_prior_state(
                &snapshot,
                &ProviderCatalogAgentSurface::default(),
                &feedback,
                &StructuralPriorLearningState::default(),
                Some(temp.path().to_str().unwrap()),
            )
            .expect("recommended path bundle");

        assert_eq!(bundle.path_id, branch_path);
        let runtime = bundle.path_ranker_runtime.expect("runtime surface");
        assert_eq!(runtime.status, "using_history_scores");
        assert_eq!(runtime.history_match_count, 1);
    }

    #[test]
    fn recommended_path_bundle_prefers_exact_feedback_path_over_scored_generic_candidate_set_when_runtime_uses_history(
    ) {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            ..WorkflowSnapshot::default()
        };
        let branch_path =
            "Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12";
        let feedback = vec![
            feedback_record_for_target_export("branch-rec-win", branch_path, "win", 0.55),
            feedback_record_for_target_export("branch-rec-loss", branch_path, "loss", 0.45),
        ];

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &feedback,
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let generic_scores = current_rows
            .iter()
            .filter(|row| row.path_id.starts_with("path:scenario:"))
            .map(|row| StructuralPathRankingExternalScoreInput {
                candidate_set_id: row.candidate_set_id.clone(),
                path_id: row.path_id.clone(),
                raw_path_score: 0.99,
                score_model_family: Some("catboost".to_string()),
                score_source_kind: Some("external_model".to_string()),
                score_model_artifact_uri: Some("generic-candidate-set.cbm".to_string()),
                score_generator: Some("test-generic-scorer".to_string()),
            })
            .collect::<Vec<_>>();
        assert!(
            !generic_scores.is_empty(),
            "test setup must score the generic candidate-set rows"
        );
        apply_structural_path_ranking_external_scores(
            temp.path().to_str().unwrap(),
            "NQ",
            &generic_scores,
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY,
        )
        .unwrap();

        let bundle =
            build_structural_recommended_path_bundle_artifact_with_state_dir_and_prior_state(
                &snapshot,
                &ProviderCatalogAgentSurface::default(),
                &feedback,
                &StructuralPriorLearningState::default(),
                Some(temp.path().to_str().unwrap()),
            )
            .expect("recommended path bundle");

        assert_eq!(bundle.path_id, branch_path);
        let runtime = bundle.path_ranker_runtime.expect("runtime surface");
        assert_eq!(runtime.status, "using_history_scores");
        assert!(
            runtime.history_match_count >= 1,
            "exact feedback path should be sourced from history in prefer_history mode"
        );
    }

    #[test]
    fn target_export_surfaces_regime_bundle_branch_paths_in_current_rows() {
        let temp = tempfile::tempdir().unwrap();
        let branch_paths = [
            "Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12".to_string(),
            "Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12".to_string(),
            "Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12".to_string(),
            "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12".to_string(),
        ];
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([
                    (
                        "regime_bundle_branch_paths_json".to_string(),
                        serde_json::to_string(&branch_paths).unwrap(),
                    ),
                    (
                        "regime_bundle_stable_profit_score".to_string(),
                        "85.7407".to_string(),
                    ),
                ]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let branch_rows = current_rows
            .iter()
            .filter(|row| branch_paths.contains(&row.path_id))
            .collect::<Vec<_>>();

        assert_eq!(
            branch_rows.len(),
            branch_paths.len(),
            "current structural path-ranking target must expose every bundle branch path"
        );
        assert!(
            summary.candidate_set_size >= branch_paths.len(),
            "candidate set must be large enough to carry every required branch path"
        );
        assert!(
            branch_rows
                .iter()
                .all(|row| row.candidate_set_id == summary.candidate_set_id
                    && row.candidate_set_size == summary.candidate_set_size),
            "bundle branch rows must use the same candidate-set identity exported in the summary"
        );

        let bundle =
            build_structural_recommended_path_bundle_artifact_with_state_dir_and_prior_state(
                &snapshot,
                &ProviderCatalogAgentSurface::default(),
                &[],
                &StructuralPriorLearningState::default(),
                Some(temp.path().to_str().unwrap()),
            )
            .expect("recommended path bundle");
        assert!(
            branch_paths.contains(&bundle.path_id),
            "recommended path must preserve a regime bundle branch path"
        );
    }

    #[test]
    fn structural_path_selection_prefers_provider_specific_exact_path_when_calibrated_scores_are_nearly_tied(
    ) {
        let generic = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim -> dense_kline_upbar_reclaim_long_v1".to_string(),
            path_ranker_calibrated_path_prob: Some(0.4269102990033223),
            composite_preference_score: 0.4269102990033223,
            ..StructuralPathArtifact::default()
        };
        let tvr = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_tvr_5m -> dense_kline_upbar_reclaim_tvr_qqq_5m_v1".to_string(),
            path_ranker_calibrated_path_prob: Some(0.4223107569721116),
            composite_preference_score: 0.4223107569721116,
            ..StructuralPathArtifact::default()
        };

        let best = vec![generic, tvr]
            .into_iter()
            .max_by(|left, right| structural_path_selection_order(left, right, false))
            .expect("best path");

        assert_eq!(
            best.path_id,
            "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_tvr_5m -> dense_kline_upbar_reclaim_tvr_qqq_5m_v1"
        );
    }

    #[test]
    fn feedback_paths_are_included_when_bundle_branch_is_generic_but_exact_same_family_exists() {
        let generic_bundle = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim -> dense_kline_upbar_reclaim_long_v1".to_string(),
            ..StructuralPathArtifact::default()
        };
        let exact_feedback = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_kraken_1m -> dense_kline_upbar_reclaim_kraken_xbtusd_1m_v1".to_string(),
            ..StructuralPathArtifact::default()
        };

        assert!(structural_should_include_feedback_paths(
            false,
            &[generic_bundle],
            &[exact_feedback],
        ));
    }

    #[test]
    fn structural_path_selection_keeps_generic_when_calibrated_gap_is_not_near_tied() {
        let generic = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim -> dense_kline_upbar_reclaim_long_v1".to_string(),
            path_ranker_calibrated_path_prob: Some(0.60),
            composite_preference_score: 0.60,
            ..StructuralPathArtifact::default()
        };
        let tvr = StructuralPathArtifact {
            path_id: "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_tvr_5m -> dense_kline_upbar_reclaim_tvr_qqq_5m_v1".to_string(),
            path_ranker_calibrated_path_prob: Some(0.42),
            composite_preference_score: 0.42,
            ..StructuralPathArtifact::default()
        };

        let best = vec![generic, tvr]
            .into_iter()
            .max_by(|left, right| structural_path_selection_order(left, right, false))
            .expect("best path");

        assert_eq!(
            best.path_id,
            "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim -> dense_kline_upbar_reclaim_long_v1"
        );
    }

    #[test]
    fn recommended_bundle_strips_market_provenance_from_rooted_path_identity() {
        let canonical_branch = "RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1";
        let prefixed_branch = format!("US_EQ -> single_stock -> CRWD -> 5m -> {canonical_branch}");
        let bundle = structural_recommended_path_bundle_from_candidates(
            "CRWD".to_string(),
            "candidate-set:crwd".to_string(),
            None,
            Some(&prefixed_branch),
            vec![StructuralPathArtifact {
                path_id: prefixed_branch.clone(),
                path_label: "CRWD 5m branch-local execution candidate".to_string(),
                path_posterior: 0.62,
                path_prior: 0.50,
                composite_preference_score: 0.67,
                ..StructuralPathArtifact::default()
            }],
        )
        .expect("recommended bundle");

        assert_eq!(bundle.path_id, canonical_branch);
        assert_eq!(bundle.path_label, canonical_branch);
        assert!(!bundle.path_id.starts_with("US_EQ ->"));
    }

    #[test]
    fn recommended_bundle_preserves_session_rhythm_current_pre_bayes_branch() {
        let tomac_branch = "SessionRhythm -> TimeOfDaySeasonality -> BalancedAdaptiveSlotPortfolio -> tomac_tod_balanced_adaptive_slot_portfolio_exact_v1";
        let bundle = structural_recommended_path_bundle_from_candidates(
            "TOMAC_TOD_BALANCED_PORTFOLIO_CAP65_DOWNSTREAM_V1".to_string(),
            "candidate-set:tomac-cap65".to_string(),
            Some(StructuralPathRankerRuntimeSurface {
                reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY.to_string()),
                ..StructuralPathRankerRuntimeSurface::default()
            }),
            Some(tomac_branch),
            vec![
                StructuralPathArtifact {
                    path_id: tomac_branch.to_string(),
                    path_label: tomac_branch.to_string(),
                    catboost_score: Some(0.8241877907929633),
                    path_ranker_execution_gate_status: Some("observe".to_string()),
                    path_ranker_runtime_source: Some("registered_artifact".to_string()),
                    composite_preference_score: 0.3812965015029336,
                    path_posterior: 0.470696,
                    path_prior: 0.47077903941171856,
                    historical_total_records: 1641,
                    ..StructuralPathArtifact::default()
                },
                StructuralPathArtifact {
                    path_id: "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1".to_string(),
                    path_label: "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1".to_string(),
                    catboost_score: Some(0.7674295989242353),
                    path_ranker_runtime_source: Some("registered_artifact_history".to_string()),
                    composite_preference_score: 0.5448793997310588,
                    path_posterior: 0.470696,
                    path_prior: 0.470696,
                    ..StructuralPathArtifact::default()
                },
            ],
        )
        .expect("recommended bundle");

        assert_eq!(bundle.path_id, tomac_branch);
        assert_eq!(bundle.path_ranker_raw_score, Some(0.8241877907929633));
    }

    #[test]
    fn target_export_surfaces_branch_segments_as_catboost_features() {
        let temp = tempfile::tempdir().unwrap();
        let branch_path = "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12";
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([
                    (
                        "regime_profit_branch_path".to_string(),
                        branch_path.to_string(),
                    ),
                    (
                        "regime_bundle_stable_profit_score".to_string(),
                        "0.857407".to_string(),
                    ),
                ]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let branch_row = current_rows
            .iter()
            .find(|row| row.path_id == branch_path)
            .expect("exported branch row");
        let row_value = serde_json::to_value(branch_row).unwrap();

        assert_eq!(row_value["regime_profit_branch_path"], branch_path);
        assert_eq!(row_value["parent_regime_root"], "Crisis");
        assert_eq!(row_value["main_regime"], "Crisis");
        assert_eq!(row_value["sub_regime"], "CrisisReliefCarry");
        assert_eq!(
            row_value["sub_sub_regime_or_profit_factor"],
            "StopManagedPanicRecovery"
        );
        assert_eq!(
            row_value["profit_factor"],
            "SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12"
        );

        let csv = std::fs::read_to_string(&summary.csv_path).unwrap();
        let header = csv.lines().next().unwrap_or_default();
        assert!(header.contains("regime_profit_branch_path"));
        assert!(header.contains("parent_regime_root"));
        assert!(header.contains("profit_factor"));
        for feature in [
            "regime_profit_branch_path",
            "parent_regime_root",
            "main_regime",
            "sub_regime",
            "sub_sub_regime_or_profit_factor",
            "profit_factor",
        ] {
            assert!(
                summary
                    .trainer_manifest
                    .feature_columns
                    .contains(&feature.to_string()),
                "trainer manifest must expose {feature} as a CatBoost/path-ranker feature"
            );
        }
    }

    #[test]
    fn target_export_binds_order_block_runtime_context_to_rooted_branch() {
        let temp = tempfile::tempdir().unwrap();
        let branch_path = "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1";
        let snapshot = WorkflowSnapshot {
            symbol: "ORDER_BLOCK_NQ_YF_NONLIVE_DIAG".to_string(),
            latest_analyze: Some(WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                order_block_variant: Some(OrderBlockVariantRuntimeEvidence {
                    factor_name: "order_block_variant_classifier".to_string(),
                    variant: "breaker_block".to_string(),
                    direction: Direction::Bull,
                    high: Some(29243.25),
                    low: Some(29172.25),
                    midpoint: Some(29207.75),
                    validation_state: "breaker_confirmed".to_string(),
                    mitigation_count: 368,
                    mitigation_pct: None,
                    failed_mitigation: false,
                    partial_fill_state: "none".to_string(),
                    breaker_confirmed: true,
                    rejection_confirmed: false,
                    confidence: 0.78,
                    fail_closed_reason: None,
                }),
                ..WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "ORDER_BLOCK_NQ_YF_NONLIVE_DIAG",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let branch_row = current_rows
            .iter()
            .find(|row| row.path_id == branch_path)
            .expect("order-block rooted branch row");

        assert_eq!(
            branch_row.regime_profit_branch_path.as_deref(),
            Some(branch_path)
        );
        assert_eq!(branch_row.main_regime.as_deref(), Some("Transition"));
        assert_eq!(branch_row.sub_regime.as_deref(), Some("OrderBlockVariant"));
        assert_eq!(
            branch_row.sub_sub_regime_or_profit_factor.as_deref(),
            Some("ob_mitigation_breaker_rejection")
        );
        assert_eq!(
            branch_row.profit_factor.as_deref(),
            Some("order_block_variant_classifier_v1")
        );
        assert_eq!(branch_row.ob_variant.as_deref(), Some("breaker_block"));
        assert_eq!(
            branch_row.ob_validation_state.as_deref(),
            Some("breaker_confirmed")
        );
        assert_eq!(branch_row.ob_confidence, Some(0.78));
    }

    #[test]
    fn target_export_binds_liquidity_texture_runtime_context_to_rooted_branch() {
        let temp = tempfile::tempdir().unwrap();
        let branch_path =
            "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1";
        let snapshot = WorkflowSnapshot {
            symbol: "LPT_IBKR_TLT_FEEDBACK".to_string(),
            latest_analyze: Some(WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                liquidity_pool_texture: Some(crate::state::LiquidityPoolTextureRuntimeEvidence {
                    factor_name: "liquidity_pool_texture".to_string(),
                    texture: "smooth".to_string(),
                    subtype: "equal_high_pool".to_string(),
                    level: Some(94.25),
                    high: Some(94.40),
                    low: Some(94.05),
                    touch_count: 6,
                    spacing_consistency: Some(0.77),
                    clean_sweep_likelihood: Some(0.63),
                    confidence: 0.71,
                    fail_closed_reason: None,
                }),
                ..WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "LPT_IBKR_TLT_FEEDBACK",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let branch_row = current_rows
            .iter()
            .find(|row| row.path_id == branch_path)
            .expect("liquidity texture rooted branch row");

        assert_eq!(
            branch_row.regime_profit_branch_path.as_deref(),
            Some(branch_path)
        );
        assert_eq!(branch_row.main_regime.as_deref(), Some("Transition"));
        assert_eq!(branch_row.sub_regime.as_deref(), Some("LiquidityMap"));
        assert_eq!(
            branch_row.sub_sub_regime_or_profit_factor.as_deref(),
            Some("liquidity_pool_texture")
        );
        assert_eq!(
            branch_row.profit_factor.as_deref(),
            Some("liquidity_pool_texture:observation_v1")
        );
    }

    #[test]
    fn agent_material_rank_rows_export_as_structural_score_targets() {
        let branch_path =
            "Transition -> RuntimeEvidenceDensity -> upbar_reclaim -> runtime_density_upbar_reclaim_long_v1";
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id: "auto-quant-agent-material-rank:HDR_205900:20260512T132018.388Z"
                .to_string(),
            generated_at: Utc::now(),
            symbol: "HDR_205900".to_string(),
            source_dispatch_artifact_id: "dispatch-1".to_string(),
            ranking: vec![
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "ranked upbar reclaim".to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(branch_path.to_string()),
                    main_regime: Some("Transition".to_string()),
                    sub_regime: Some("RuntimeEvidenceDensity".to_string()),
                    sub_sub_regime_or_profit_factor: Some("upbar_reclaim".to_string()),
                    profit_factor: Some("runtime_density_upbar_reclaim_long_v1".to_string()),
                    win_rate_pct: Some(30.6691),
                    sharpe: Some(-1.833),
                    total_profit_pct: Some(-19.44),
                    trade_count: Some(538),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "duplicate provider row".to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(branch_path.to_string()),
                    trade_count: Some(583),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
            ],
        };
        let rows = structural_path_ranking_agent_material_rank_target_rows(
            &WorkflowSnapshot {
                symbol: "HDR_205900".to_string(),
                ..WorkflowSnapshot::default()
            },
            &StructuralPriorLearningState::default(),
            &rank_artifact,
        );

        assert_eq!(
            rows.len(),
            1,
            "rank adapter must expose one structural candidate per branch path"
        );
        let row = &rows[0];
        assert_eq!(row.candidate_set_id, rank_artifact.artifact_id);
        assert_eq!(row.path_id, branch_path);
        assert_eq!(row.regime_profit_branch_path.as_deref(), Some(branch_path));
        assert_eq!(row.main_regime.as_deref(), Some("Transition"));
        assert_eq!(row.sub_regime.as_deref(), Some("RuntimeEvidenceDensity"));
        assert_eq!(
            row.sub_sub_regime_or_profit_factor.as_deref(),
            Some("upbar_reclaim")
        );
        assert_eq!(
            row.profit_factor.as_deref(),
            Some("runtime_density_upbar_reclaim_long_v1")
        );
        assert_eq!(
            structural_path_ranking_target_row_score_key(row),
            format!("{}|{}", rank_artifact.artifact_id, branch_path)
        );
    }

    #[test]
    fn completed_agent_material_rank_rows_with_density_become_trainable_structural_targets() {
        let winning_branch =
            "TrendExpansion -> MomentumPersistence -> elder_impulse_macd -> elder_impulse_v1";
        let losing_branch =
            "TrendExpansion -> MomentumPersistence -> elder_impulse_macd -> elder_impulse_loser_v1";
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id: "auto-quant-agent-material-rank:ELDER:20260517T133032.892Z".to_string(),
            generated_at: Utc::now(),
            symbol: "ELDER".to_string(),
            source_dispatch_artifact_id: "dispatch-elder".to_string(),
            ranking: vec![
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "elder impulse positive".to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(winning_branch.to_string()),
                    main_regime: Some("TrendExpansion".to_string()),
                    sub_regime: Some("MomentumPersistence".to_string()),
                    sub_sub_regime_or_profit_factor: Some("elder_impulse_macd".to_string()),
                    profit_factor: Some("elder_impulse_v1".to_string()),
                    win_rate_pct: Some(48.6111),
                    sharpe: Some(1.947),
                    total_profit_pct: Some(3.31),
                    trade_count: Some(72),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "elder impulse negative".to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(losing_branch.to_string()),
                    main_regime: Some("TrendExpansion".to_string()),
                    sub_regime: Some("MomentumPersistence".to_string()),
                    sub_sub_regime_or_profit_factor: Some("elder_impulse_macd".to_string()),
                    profit_factor: Some("elder_impulse_loser_v1".to_string()),
                    win_rate_pct: Some(39.2857),
                    sharpe: Some(-1.1328),
                    total_profit_pct: Some(-0.40),
                    trade_count: Some(56),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
            ],
        };

        let rows = structural_path_ranking_agent_material_rank_target_rows(
            &WorkflowSnapshot {
                symbol: "ELDER".to_string(),
                ..WorkflowSnapshot::default()
            },
            &StructuralPriorLearningState::default(),
            &rank_artifact,
        );

        let winning = rows
            .iter()
            .find(|row| row.path_id == winning_branch)
            .expect("winning branch row");
        assert_eq!(winning.pending_reward_state, "matured_success");
        assert!(winning.maturity_mask);
        assert_eq!(winning.calibrated_label, Some(1.0));
        assert!(winning.training_weight.is_some());
        assert!(winning.calibrated_path_prob.is_some());

        let losing = rows
            .iter()
            .find(|row| row.path_id == losing_branch)
            .expect("losing branch row");
        assert_eq!(losing.pending_reward_state, "matured_failure");
        assert!(losing.maturity_mask);
        assert_eq!(losing.calibrated_label, Some(0.0));
        assert!(losing.training_weight.is_some());
    }

    #[test]
    fn same_branch_agent_material_rank_timeframes_remain_distinct_trainable_observations() {
        let branch =
            "TrendExpansion -> MomentumPersistence -> public_elder_impulse_macd_histogram -> ibkr_public_elder_impulse_macd_histogram_v1";
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id:
                "auto-quant-agent-material-rank:IBKR_PUBLIC_ELDER_IMPULSE_MACD_QQQ:20260517T133032.892Z"
                    .to_string(),
            generated_at: Utc::now(),
            symbol: "IBKR_PUBLIC_ELDER_IMPULSE_MACD_QQQ".to_string(),
            source_dispatch_artifact_id: "dispatch-elder".to_string(),
            ranking: vec![
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "IBKR public Elder Impulse MACD histogram - QQQ 1m 7 D"
                        .to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(branch.to_string()),
                    main_regime: Some("TrendExpansion".to_string()),
                    sub_regime: Some("MomentumPersistence".to_string()),
                    sub_sub_regime_or_profit_factor: Some(
                        "public_elder_impulse_macd_histogram".to_string(),
                    ),
                    profit_factor: Some("ibkr_public_elder_impulse_macd_histogram_v1".to_string()),
                    win_rate_pct: Some(41.841),
                    sharpe: Some(65.9252),
                    total_profit_pct: Some(1.20),
                    trade_count: Some(239),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "IBKR public Elder Impulse MACD histogram - QQQ 5m 1 M"
                        .to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(branch.to_string()),
                    main_regime: Some("TrendExpansion".to_string()),
                    sub_regime: Some("MomentumPersistence".to_string()),
                    sub_sub_regime_or_profit_factor: Some(
                        "public_elder_impulse_macd_histogram".to_string(),
                    ),
                    profit_factor: Some("ibkr_public_elder_impulse_macd_histogram_v1".to_string()),
                    win_rate_pct: Some(40.1198),
                    sharpe: Some(14.6117),
                    total_profit_pct: Some(2.56),
                    trade_count: Some(167),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
                crate::application::auto_quant::AgentMaterialRankRow {
                    unit_label: "IBKR public Elder Impulse MACD histogram - QQQ 15m 1 M"
                        .to_string(),
                    status: "completed".to_string(),
                    regime_profit_branch_path: Some(branch.to_string()),
                    main_regime: Some("TrendExpansion".to_string()),
                    sub_regime: Some("MomentumPersistence".to_string()),
                    sub_sub_regime_or_profit_factor: Some(
                        "public_elder_impulse_macd_histogram".to_string(),
                    ),
                    profit_factor: Some("ibkr_public_elder_impulse_macd_histogram_v1".to_string()),
                    win_rate_pct: Some(39.2857),
                    sharpe: Some(-1.1328),
                    total_profit_pct: Some(-0.40),
                    trade_count: Some(56),
                    ..crate::application::auto_quant::AgentMaterialRankRow::default()
                },
            ],
        };

        let rows = structural_path_ranking_agent_material_rank_target_rows(
            &WorkflowSnapshot {
                symbol: "IBKR_PUBLIC_ELDER_IMPULSE_MACD_QQQ".to_string(),
                ..WorkflowSnapshot::default()
            },
            &StructuralPriorLearningState::default(),
            &rank_artifact,
        );

        assert_eq!(
            rows.len(),
            3,
            "same branch rows from different timeframes must stay distinct observations"
        );
        assert!(rows
            .iter()
            .all(|row| row.path_id == branch
                && row.regime_profit_branch_path.as_deref() == Some(branch)));
        assert_eq!(
            rows.iter()
                .filter(|row| row.pending_reward_state == "matured_success")
                .count(),
            2
        );
        assert_eq!(
            rows.iter()
                .filter(|row| row.pending_reward_state == "matured_failure")
                .count(),
            1
        );
        let score_keys = rows
            .iter()
            .map(structural_path_ranking_target_row_score_key)
            .collect::<BTreeSet<_>>();
        assert_eq!(
            score_keys.len(),
            3,
            "each timeframe row needs a unique score key"
        );
    }

    #[test]
    fn target_export_surfaces_read_only_bbn_label_set_branch_paths_in_current_rows() {
        let temp = tempfile::tempdir().unwrap();
        let branch_paths = [
            "Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12".to_string(),
            "Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12".to_string(),
            "Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12".to_string(),
            "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12".to_string(),
        ];
        let label_set = branch_paths
            .iter()
            .map(|path| path.replace(" -> ", "_->_"))
            .collect::<Vec<_>>()
            .join(",");
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([
                    ("read_only_regime_bbn_label_set".to_string(), label_set),
                    (
                        "read_only_regime_bbn_trade_usable".to_string(),
                        "true".to_string(),
                    ),
                    (
                        "read_only_regime_bbn_reasons".to_string(),
                        "branch_rc_spa_all_price_roots_passed".to_string(),
                    ),
                ]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();

        assert_eq!(
            current_rows
                .iter()
                .filter(|row| branch_paths.contains(&row.path_id))
                .count(),
            branch_paths.len(),
            "current target must preserve exact branch paths from read-only BBN label sets"
        );
    }

    #[test]
    fn target_export_surfaces_regime_refinement_branch_path_in_current_rows() {
        let temp = tempfile::tempdir().unwrap();
        let branch_path =
            "TrendExpansion -> BullTrendExhaustion -> lowtf_range_flip -> trend_to_range_flip_kraken_tao_1m_v1";
        let snapshot = WorkflowSnapshot {
            symbol: "KRAKEN_TAO".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([
                    (
                        "regime_refinement_branch_path".to_string(),
                        branch_path.to_string(),
                    ),
                    ("main_regime".to_string(), "TrendExpansion".to_string()),
                    ("sub_regime".to_string(), "BullTrendExhaustion".to_string()),
                    (
                        "sub_sub_regime_or_refinement_factor".to_string(),
                        "lowtf_range_flip".to_string(),
                    ),
                    (
                        "refinement_factor".to_string(),
                        "trend_to_range_flip_kraken_tao_1m_v1".to_string(),
                    ),
                ]),
                order_block_variant: Some(OrderBlockVariantRuntimeEvidence {
                    factor_name: "order_block_variant_classifier".to_string(),
                    variant: "breaker_block".to_string(),
                    direction: Direction::Bull,
                    high: Some(276.17),
                    low: Some(275.97),
                    midpoint: Some(276.07),
                    validation_state: "breaker_confirmed".to_string(),
                    mitigation_count: 15,
                    mitigation_pct: None,
                    failed_mitigation: false,
                    partial_fill_state: "none".to_string(),
                    breaker_confirmed: true,
                    rejection_confirmed: false,
                    confidence: 0.78,
                    fail_closed_reason: None,
                }),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "KRAKEN_TAO",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let refinement_row = current_rows
            .iter()
            .find(|row| row.path_id == branch_path)
            .expect("refinement branch row should be first-class target row");

        assert_eq!(
            refinement_row.regime_profit_branch_path.as_deref(),
            Some(branch_path)
        );
        assert_eq!(
            refinement_row.main_regime.as_deref(),
            Some("TrendExpansion")
        );
        assert_eq!(
            refinement_row.sub_regime.as_deref(),
            Some("BullTrendExhaustion")
        );
        assert_eq!(
            refinement_row.sub_sub_regime_or_profit_factor.as_deref(),
            Some("lowtf_range_flip")
        );
        assert_eq!(
            refinement_row.profit_factor.as_deref(),
            Some("trend_to_range_flip_kraken_tao_1m_v1")
        );
    }

    #[test]
    fn target_export_uses_exact_branch_trade_direction_over_snapshot_fallback() {
        let temp = tempfile::tempdir().unwrap();
        let branch_path = "FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_7d_gate1_v1";
        let snapshot = WorkflowSnapshot {
            symbol: "M2K".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                selected_direction: Some("Bull".to_string()),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([
                    (
                        "regime_profit_branch_path".to_string(),
                        branch_path.to_string(),
                    ),
                    ("trade_direction".to_string(), "Bear".to_string()),
                ]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "M2K",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let branch_row = current_rows
            .iter()
            .find(|row| row.path_id == branch_path)
            .expect("exact M2K branch should be exported as a current target row");

        assert_eq!(branch_row.direction, "bear");
    }

    #[test]
    fn path_ranker_runtime_falls_back_to_history_when_registered_artifact_misses_path() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let mut history_score_row = current_rows.first().expect("current row").clone();
        let path_id = history_score_row.path_id.clone();
        history_score_row.candidate_set_id = "structural-candidates:NQ:history".to_string();
        history_score_row.raw_path_score = Some(0.91);
        history_score_row.calibrated_path_prob = None;
        history_score_row.path_prob_lower_bound = None;
        history_score_row.execution_gate_status = None;
        let mut history_gate_row = history_score_row.clone();
        history_gate_row.candidate_set_id =
            "structural-feedback-history:NQ:history-gate".to_string();
        history_gate_row.raw_path_score = None;
        history_gate_row.calibrated_path_prob = Some(0.61);
        history_gate_row.path_prob_lower_bound = Some(0.44);
        history_gate_row.execution_gate_status = Some("pass".to_string());
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&[
                history_score_row,
                history_gate_row,
            ])
            .unwrap(),
        )
        .unwrap();
        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        fs::write(
            artifact_dir.join("artifact_scores.jsonl"),
            format!(
                "{}\n",
                serde_json::json!({
                    "candidate_set_id": "structural-candidates:NQ:other",
                    "path_id": "path:scenario:NQ:belief_regime_node:range:range_mean_reversion:primary",
                    "raw_path_score": 0.12
                })
            ),
        )
        .unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "artifact_scores.jsonl".to_string(),
                model_artifact_uri: None,
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        let runtime = selection.runtime.expect("runtime surface");
        assert_eq!(runtime.status, "using_history_scores");
        assert_eq!(runtime.artifact_match_count, 0);
        assert_eq!(runtime.history_match_count, 1);
        assert_eq!(runtime.applied_path_count, 1);
        assert_eq!(
            selection
                .candidate_paths
                .iter()
                .find(|path| path.path_id == path_id)
                .and_then(|path| path.path_ranker_runtime_source.as_deref()),
            Some("history_path")
        );
        let selected = selection
            .candidate_paths
            .iter()
            .find(|path| path.path_id == path_id)
            .expect("history path should be selected");
        assert_eq!(selected.path_ranker_calibrated_path_prob, Some(0.61));
        assert_eq!(selected.path_ranker_path_prob_lower_bound, Some(0.44));
        assert_eq!(
            selected.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
    }

    #[test]
    fn path_ranker_runtime_applies_registered_artifact_scores_to_ranked_paths() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        let score_lines = current_rows
            .iter()
            .enumerate()
            .map(|(index, row)| {
                serde_json::json!({
                    "candidate_set_id": row.candidate_set_id,
                    "path_id": row.path_id,
                    "raw_path_score": 0.91 - index as f64 * 0.04,
                    "calibrated_path_prob": 0.86 - index as f64 * 0.03,
                    "path_prob_lower_bound": 0.74 - index as f64 * 0.02,
                    "execution_gate_status": if index == 0 { "pass" } else { "observe" },
                })
                .to_string()
            })
            .collect::<Vec<_>>()
            .join("\n");
        fs::write(
            artifact_dir.join("artifact_scores.jsonl"),
            format!("{score_lines}\n"),
        )
        .unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "artifact_scores.jsonl".to_string(),
                model_artifact_uri: None,
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string(), "raw_path_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        let runtime = selection.runtime.expect("runtime surface");
        assert_eq!(runtime.status, "using_registered_artifact_scores");
        assert_eq!(runtime.artifact_match_count, current_rows.len());
        assert_eq!(runtime.applied_path_count, current_rows.len());
        let expected_first = current_rows.first().expect("first row");
        let selected = selection
            .candidate_paths
            .iter()
            .find(|path| path.path_id == expected_first.path_id)
            .expect("ranked path with registered score");
        assert_eq!(
            selected.path_ranker_runtime_source.as_deref(),
            Some("registered_artifact")
        );
        assert_eq!(selected.catboost_score, Some(0.91));
        assert_eq!(
            selected.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
    }

    #[test]
    fn path_ranker_runtime_uses_persisted_current_target_scores_when_model_artifact_is_rowless() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        for (index, row) in current_rows.iter_mut().enumerate() {
            row.raw_path_score = Some(0.81 - index as f64 * 0.03);
            row.score_model_family = Some("catboost".to_string());
            row.score_source_kind = Some("external_model".to_string());
            row.score_model_artifact_uri = Some("catboost_model/catboost_model.cbm".to_string());
            row.score_generator = Some("test-current-target-scorer".to_string());
        }
        fs::write(
            &summary.jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&current_rows).unwrap(),
        )
        .unwrap();
        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        fs::create_dir_all(artifact_dir.join("catboost_model")).unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "catboost_model".to_string(),
                model_artifact_uri: Some("catboost_model/catboost_model.cbm".to_string()),
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string(), "structural_baseline_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        assert_eq!(selection.candidate_set_id, summary.candidate_set_id);
        assert_eq!(selection.candidate_paths.len(), current_rows.len());
        assert!(selection.candidate_paths.iter().all(|path| {
            current_rows.iter().any(|row| {
                row.path_id == path.path_id && row.candidate_set_id == summary.candidate_set_id
            })
        }));
        assert!(selection
            .candidate_paths
            .iter()
            .any(|path| path.path_ranker_runtime_source.as_deref() == Some("candidate_set")));
        let runtime = selection.runtime.expect("runtime surface");
        assert_eq!(runtime.status, "using_candidate_set_scores");
        assert_eq!(runtime.artifact_match_count, 0);
        assert_eq!(runtime.candidate_set_match_count, current_rows.len());
        assert_eq!(runtime.applied_path_count, current_rows.len());
        let expected_first = current_rows.first().expect("first row");
        let selected = selection
            .candidate_paths
            .iter()
            .find(|path| path.path_id == expected_first.path_id)
            .expect("ranked path with persisted current target score");
        assert_eq!(
            selected.path_ranker_runtime_source.as_deref(),
            Some("candidate_set")
        );
        assert_eq!(selected.catboost_score, Some(0.81));
    }

    #[test]
    fn path_ranker_runtime_backfills_current_score_with_same_path_history_gate_metadata() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let mut history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        let target = current_rows.first_mut().expect("current target row");
        let candidate_set_id = target.candidate_set_id.clone();
        let path_id = target.path_id.clone();
        target.raw_path_score = Some(0.835725);
        target.calibrated_path_prob = None;
        target.path_prob_lower_bound = None;
        target.execution_gate_status = None;
        target.score_model_family = Some("catboost".to_string());
        target.score_source_kind = Some("external_model".to_string());
        target.score_model_artifact_uri = Some("catboost_model/catboost_model.cbm".to_string());
        target.score_generator = Some("test-current-scorer".to_string());

        let history_target = history_rows
            .iter_mut()
            .find(|row| row.path_id == path_id)
            .expect("same path should exist in history rows");
        history_target.candidate_set_id = format!("{candidate_set_id}:prior");
        history_target.raw_path_score = Some(0.890452);
        history_target.calibrated_path_prob = Some(0.619048);
        history_target.path_prob_lower_bound = Some(0.449251);
        history_target.execution_gate_status = Some("pass".to_string());
        history_target.score_model_family = Some("catboost".to_string());
        history_target.score_source_kind = Some("external_model".to_string());
        history_target.score_model_artifact_uri = Some("catboost_model/prior.cbm".to_string());
        history_target.score_generator = Some("test-history-scorer".to_string());

        fs::write(
            &summary.jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&current_rows).unwrap(),
        )
        .unwrap();
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&history_rows).unwrap(),
        )
        .unwrap();
        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        fs::create_dir_all(artifact_dir.join("catboost_model")).unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "catboost_model".to_string(),
                model_artifact_uri: Some("catboost_model/catboost_model.cbm".to_string()),
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string(), "raw_path_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        let selected = selection
            .candidate_paths
            .iter()
            .find(|path| path.path_id == path_id)
            .expect("ranked path with current score");
        assert_eq!(
            selected.path_ranker_runtime_source.as_deref(),
            Some("candidate_set")
        );
        assert_eq!(selected.catboost_score, Some(0.835725));
        assert_eq!(selected.path_ranker_calibrated_path_prob, Some(0.619048));
        assert_eq!(selected.path_ranker_path_prob_lower_bound, Some(0.449251));
        assert_eq!(
            selected.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
    }

    #[test]
    fn path_ranker_runtime_backfills_duplicate_current_score_with_history_gate_metadata() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let mut history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        let target = current_rows.first_mut().expect("current target row");
        let candidate_set_id = target.candidate_set_id.clone();
        let path_id = target.path_id.clone();
        target.raw_path_score = Some(0.835725);
        target.calibrated_path_prob = Some(0.619048);
        target.path_prob_lower_bound = Some(0.449251);
        target.execution_gate_status = Some("pass".to_string());
        target.score_model_family = Some("catboost".to_string());
        target.score_source_kind = Some("external_model".to_string());
        target.score_model_artifact_uri = Some("catboost_model/gated.cbm".to_string());
        target.score_generator = Some("test-current-gated-scorer".to_string());

        let mut later_score_without_gate = target.clone();
        later_score_without_gate.raw_path_score = Some(0.850571);
        later_score_without_gate.calibrated_path_prob = None;
        later_score_without_gate.path_prob_lower_bound = None;
        later_score_without_gate.execution_gate_status = None;
        later_score_without_gate.score_model_artifact_uri =
            Some("catboost_model/latest-score.cbm".to_string());
        later_score_without_gate.score_generator = Some("test-current-latest-score".to_string());
        current_rows.push(later_score_without_gate);

        let history_target = history_rows
            .iter_mut()
            .find(|row| row.path_id == path_id)
            .expect("same path should exist in history rows");
        history_target.candidate_set_id = format!("{candidate_set_id}:prior");
        history_target.raw_path_score = Some(0.769455);
        history_target.calibrated_path_prob = Some(0.727273);
        history_target.path_prob_lower_bound = Some(0.516426);
        history_target.execution_gate_status = Some("pass".to_string());
        history_target.score_model_family = Some("catboost".to_string());
        history_target.score_source_kind = Some("external_model".to_string());
        history_target.score_model_artifact_uri = Some("catboost_model/prior.cbm".to_string());
        history_target.score_generator = Some("test-history-gated-scorer".to_string());

        fs::write(
            &summary.jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&current_rows).unwrap(),
        )
        .unwrap();
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&history_rows).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        let selected = selection
            .candidate_paths
            .iter()
            .find(|path| path.path_id == path_id)
            .expect("ranked path with duplicate current score");
        assert_eq!(
            selected.path_ranker_runtime_source.as_deref(),
            Some("candidate_set")
        );
        assert_eq!(selected.catboost_score, Some(0.850571));
        assert_eq!(selected.path_ranker_calibrated_path_prob, Some(0.727273));
        assert_eq!(selected.path_ranker_path_prob_lower_bound, Some(0.516426));
        assert_eq!(
            selected.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
    }

    #[test]
    fn path_ranker_runtime_prefers_current_candidate_row_over_stale_duplicate_artifact_row() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        let target = current_rows.first().expect("current target row");
        let candidate_set_id = target.candidate_set_id.clone();
        let path_id = target.path_id.clone();
        let stale_material_candidate_set_id =
            format!("auto-quant-agent-material-rank:{candidate_set_id}:stale");
        let mut current_candidate_rows = current_rows.clone();
        let mut stale_material_row = target.clone();
        stale_material_row.candidate_set_id = stale_material_candidate_set_id.clone();
        current_candidate_rows.push(stale_material_row);

        let mut history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();
        let mut history_gate_row = target.clone();
        history_gate_row.raw_path_score = None;
        history_gate_row.calibrated_path_prob = Some(0.857143);
        history_gate_row.path_prob_lower_bound = Some(0.654245);
        history_gate_row.execution_gate_status = Some("pass".to_string());
        history_rows.push(history_gate_row);
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&history_rows).unwrap(),
        )
        .unwrap();

        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        fs::write(
            artifact_dir.join("artifact_scores.jsonl"),
            format!(
                "{}\n{}\n",
                serde_json::json!({
                    "candidate_set_id": candidate_set_id,
                    "path_id": path_id,
                    "raw_path_score": 0.8030589351441021,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_artifact",
                    "score_model_artifact_uri": "artifact_scores.jsonl",
                    "score_generator": "test-current-candidate-score"
                }),
                serde_json::json!({
                    "candidate_set_id": stale_material_candidate_set_id,
                    "path_id": path_id,
                    "raw_path_score": 0.36742166703440915,
                    "score_model_family": "catboost",
                    "score_source_kind": "external_artifact",
                    "score_model_artifact_uri": "artifact_scores.jsonl",
                    "score_generator": "test-stale-material-score"
                })
            ),
        )
        .unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "artifact_scores.jsonl".to_string(),
                model_artifact_uri: None,
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string(), "raw_path_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let mut candidate_paths = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext { state_dir: None },
        )
        .candidate_paths;

        let runtime = resolve_structural_path_ranker_runtime(
            Some(temp.path().to_str().unwrap()),
            "NQ",
            &candidate_set_id,
            &current_candidate_rows,
            &mut candidate_paths,
        )
        .expect("runtime surface");

        assert_eq!(runtime.status, "using_registered_artifact_scores");
        let selected = candidate_paths
            .iter()
            .find(|path| path.path_id == path_id)
            .expect("ranked path with registered score");
        assert_eq!(
            selected.path_ranker_runtime_source.as_deref(),
            Some("registered_artifact")
        );
        assert_eq!(selected.catboost_score, Some(0.8030589351441021));
        assert_eq!(selected.path_ranker_calibrated_path_prob, Some(0.857143));
        assert_eq!(selected.path_ranker_path_prob_lower_bound, Some(0.654245));
        assert_eq!(
            selected.path_ranker_execution_gate_status.as_deref(),
            Some("pass")
        );
    }

    #[test]
    fn apply_external_scores_preserves_existing_metadata_when_score_file_omits_it() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let mut history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();
        let target = current_rows.first_mut().expect("current target row");
        target.raw_path_score = Some(0.42);
        target.score_model_family = Some("catboost".to_string());
        target.score_source_kind = Some("external_model".to_string());
        target.score_model_artifact_uri = Some("catboost_model/current.cbm".to_string());
        target.score_generator = Some("preexisting-current-scorer".to_string());
        let candidate_set_id = target.candidate_set_id.clone();
        let path_id = target.path_id.clone();
        let target_key = format!("{candidate_set_id}|{path_id}");
        for row in &mut history_rows {
            if format!("{}|{}", row.candidate_set_id, row.path_id) == target_key {
                row.raw_path_score = Some(0.42);
                row.score_model_family = Some("catboost".to_string());
                row.score_source_kind = Some("external_model".to_string());
                row.score_model_artifact_uri = Some("catboost_model/current.cbm".to_string());
                row.score_generator = Some("preexisting-current-scorer".to_string());
            }
        }
        fs::write(
            &summary.jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&current_rows).unwrap(),
        )
        .unwrap();
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&history_rows).unwrap(),
        )
        .unwrap();

        apply_structural_path_ranking_external_scores(
            temp.path().to_str().unwrap(),
            "NQ",
            &[StructuralPathRankingExternalScoreInput {
                candidate_set_id: candidate_set_id.clone(),
                path_id: path_id.clone(),
                raw_path_score: 0.91,
                score_model_family: None,
                score_source_kind: None,
                score_model_artifact_uri: None,
                score_generator: None,
            }],
        )
        .unwrap();

        let persisted_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        let persisted = persisted_rows
            .iter()
            .find(|row| row.candidate_set_id == candidate_set_id && row.path_id == path_id)
            .expect("updated current row");
        assert_eq!(persisted.raw_path_score, Some(0.91));
        assert_eq!(persisted.score_model_family.as_deref(), Some("catboost"));
        assert_eq!(
            persisted.score_source_kind.as_deref(),
            Some("external_model")
        );
        assert_eq!(
            persisted.score_model_artifact_uri.as_deref(),
            Some("catboost_model/current.cbm")
        );
        assert_eq!(
            persisted.score_generator.as_deref(),
            Some("preexisting-current-scorer")
        );
    }

    #[test]
    fn apply_external_scores_matches_provenance_prefixed_rows_from_canonical_branch_input() {
        let temp = tempfile::tempdir().unwrap();
        let symbol = "M2K";
        let legacy_path = "FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1";
        let canonical_path = "RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_pda_consistency_floor_v1";
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id: "auto-quant-agent-material-rank:strategy-library:M2K:test".to_string(),
            generated_at: Utc::now(),
            symbol: symbol.to_string(),
            source_dispatch_artifact_id: "dispatch-m2k".to_string(),
            ranking: vec![crate::application::auto_quant::AgentMaterialRankRow {
                unit_label: "M2K legacy provenance branch".to_string(),
                status: "completed".to_string(),
                regime_profit_branch_path: Some(legacy_path.to_string()),
                main_regime: Some("FUTURES".to_string()),
                sub_regime: Some("equity_index".to_string()),
                sub_sub_regime_or_profit_factor: Some("M2K".to_string()),
                profit_factor: Some(format!("1m -> {canonical_path}")),
                win_rate_pct: Some(61.5),
                sharpe: Some(1.11),
                total_profit_pct: Some(0.88),
                trade_count: Some(17),
                ..crate::application::auto_quant::AgentMaterialRankRow::default()
            }],
        };

        let summary = export_structural_path_ranking_target_with_agent_material_rank(
            temp.path().to_str().unwrap(),
            symbol,
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            Some(&rank_artifact),
        )
        .unwrap();

        apply_structural_path_ranking_external_scores(
            temp.path().to_str().unwrap(),
            symbol,
            &[StructuralPathRankingExternalScoreInput {
                candidate_set_id: rank_artifact.artifact_id.clone(),
                path_id: canonical_path.to_string(),
                raw_path_score: 0.812288,
                score_model_family: Some("catboost".to_string()),
                score_source_kind: Some("external_model".to_string()),
                score_model_artifact_uri: Some("path_ranker_model/catboost_model.cbm".to_string()),
                score_generator: Some("test-canonical-branch-scorer".to_string()),
            }],
        )
        .unwrap();

        for path in [&summary.jsonl_path, &summary.history_jsonl_path] {
            let rows = load_structural_path_ranking_target_rows(Path::new(path)).unwrap();
            let matched = rows
                .iter()
                .find(|row| {
                    row.candidate_set_id == rank_artifact.artifact_id && row.path_id == legacy_path
                })
                .expect("legacy provenance row should still exist");
            assert_eq!(matched.raw_path_score, Some(0.812288));
            assert_eq!(matched.score_model_family.as_deref(), Some("catboost"));
            assert_eq!(matched.score_source_kind.as_deref(), Some("external_model"));
            assert_eq!(
                matched.score_model_artifact_uri.as_deref(),
                Some("path_ranker_model/catboost_model.cbm")
            );
            assert_eq!(
                matched.score_generator.as_deref(),
                Some("test-canonical-branch-scorer")
            );
            assert_eq!(
                matched.regime_profit_branch_path.as_deref(),
                Some(legacy_path)
            );
        }
    }

    #[test]
    fn target_export_preserves_existing_score_metadata_from_history() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut history_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.history_jsonl_path))
                .unwrap();
        let target = history_rows.first_mut().expect("history target row");
        let candidate_set_id = target.candidate_set_id.clone();
        let path_id = target.path_id.clone();
        target.raw_path_score = Some(0.84);
        target.score_model_family = Some("catboost".to_string());
        target.score_source_kind = Some("external_model".to_string());
        target.score_model_artifact_uri = Some("catboost_model/history.cbm".to_string());
        target.score_generator = Some("history-scorer".to_string());
        fs::write(
            &summary.history_jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&history_rows).unwrap(),
        )
        .unwrap();

        let refreshed = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let current_rows =
            load_structural_path_ranking_target_rows(Path::new(&refreshed.jsonl_path)).unwrap();
        let current = current_rows
            .iter()
            .find(|row| row.candidate_set_id == candidate_set_id && row.path_id == path_id)
            .expect("refreshed current row");
        assert_eq!(current.raw_path_score, Some(0.84));
        assert_eq!(current.score_model_family.as_deref(), Some("catboost"));
        assert_eq!(current.score_source_kind.as_deref(), Some("external_model"));
        assert_eq!(
            current.score_model_artifact_uri.as_deref(),
            Some("catboost_model/history.cbm")
        );
        assert_eq!(current.score_generator.as_deref(), Some("history-scorer"));
    }

    #[test]
    fn path_ranker_runtime_rejects_stale_current_target_scores_from_prior_candidate_set() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let summary = export_structural_path_ranking_target(
            temp.path().to_str().unwrap(),
            "NQ",
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
        )
        .unwrap();
        let mut current_rows =
            load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path)).unwrap();
        assert!(!current_rows.is_empty(), "expected structural target rows");
        for (index, row) in current_rows.iter_mut().enumerate() {
            row.candidate_set_id = format!("{}:stale", row.candidate_set_id);
            row.raw_path_score = Some(0.81 - index as f64 * 0.03);
            row.score_model_family = Some("catboost".to_string());
            row.score_source_kind = Some("external_model".to_string());
            row.score_model_artifact_uri = Some("catboost_model/catboost_model.cbm".to_string());
            row.score_generator = Some("test-stale-current-target-scorer".to_string());
        }
        fs::write(
            &summary.jsonl_path,
            render_structural_path_ranking_target_rows_jsonl(&current_rows).unwrap(),
        )
        .unwrap();
        let artifact_dir = Path::new(&summary.summary_path)
            .parent()
            .expect("summary parent")
            .to_path_buf();
        fs::create_dir_all(artifact_dir.join("catboost_model")).unwrap();
        let artifact =
            crate::application::entry_models::training_export::StructuralPathRankingTrainerArtifact {
                protocol_version: "structural-path-ranking-trainer-artifact-v1".to_string(),
                dataset_role: "external_path_ranker_training_dataset".to_string(),
                model_family: "catboost".to_string(),
                artifact_uri: "catboost_model".to_string(),
                model_artifact_uri: Some("catboost_model/catboost_model.cbm".to_string()),
                score_column: "raw_path_score".to_string(),
                trained_rows: 42,
                history_rows: 42,
                calibration_rows: 12,
                selected_features: vec!["rank".to_string(), "structural_baseline_score".to_string()],
                validation_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerValidationMetrics::default(),
                calibration_metrics:
                    crate::belief_core::ranking_label::StructuralPathRankerCalibrationMetrics::default(),
                rule_list: Vec::new(),
                tree_json: None,
                created_at: None,
                notes: vec![],
            };
        fs::write(
            artifact_dir.join("structural_path_ranking_trainer_artifact.json"),
            serde_json::to_string_pretty(&artifact).unwrap(),
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            "NQ",
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let selection = structural_ranked_paths_with_runtime_context_and_prior_state(
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            StructuralPathRankerRuntimeContext {
                state_dir: Some(temp.path().to_str().unwrap()),
            },
        );

        let runtime = selection.runtime.expect("runtime surface");
        assert_eq!(runtime.status, "enabled_no_matching_scores");
        assert_eq!(runtime.artifact_match_count, 0);
        assert_eq!(runtime.candidate_set_match_count, 0);
        assert_eq!(runtime.applied_path_count, 0);
        assert!(selection
            .candidate_paths
            .iter()
            .all(|path| path.path_ranker_runtime_source.is_none()));
    }

    #[test]
    fn recommended_path_bundle_prefers_observed_exact_branch_over_unobserved_generic_scenario_when_scores_are_close(
    ) {
        let runtime = StructuralPathRankerRuntimeSurface {
            enabled: true,
            reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY.to_string()),
            status: "using_registered_model_artifact".to_string(),
            artifact_match_count: 3,
            candidate_set_match_count: 3,
            history_match_count: 0,
            applied_path_count: 3,
            score_model_family: None,
            score_source_kind: None,
            score_model_artifact_uri: None,
            score_generator: None,
        };
        let exact_path = StructuralPathArtifact {
            path_id:
                "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_kraken_1m -> dense_kline_upbar_reclaim_kraken_xbtusd_1m_v1"
                    .to_string(),
            scenario_id: "scenario:exact-kraken".to_string(),
            path_label:
                "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_kraken_1m -> dense_kline_upbar_reclaim_kraken_xbtusd_1m_v1"
                    .to_string(),
            direction: "bull".to_string(),
            entry_style: "structural_feedback_path".to_string(),
            historical_total_records: 349,
            historical_followed_count: 349,
            catboost_score: Some(0.5267362986603144),
            path_ranker_execution_gate_status: Some("pass".to_string()),
            path_ranker_runtime_source: Some("registered_artifact".to_string()),
            path_prior: 0.35201149425287354,
            path_posterior: 0.34770114942528735,
            bbn_support_score: 0.34770114942528735,
            composite_preference_score: 0.348994,
            stop_definition: "exact-stop".to_string(),
            target_definition: "exact-target".to_string(),
            expected_failure_mode: "exact-fail".to_string(),
            max_time_in_trade: "1h".to_string(),
            ..StructuralPathArtifact::default()
        };
        let generic_scenario = StructuralPathArtifact {
            path_id:
                "path:scenario:DENSE_KLINE_BRANCH:belief_regime_node:trend:trend_follow_through:primary"
                    .to_string(),
            scenario_id: "scenario:generic".to_string(),
            path_label: "trend_follow_through".to_string(),
            direction: "bull".to_string(),
            entry_style: "belief_regime_node".to_string(),
            historical_total_records: 4,
            historical_followed_count: 0,
            catboost_score: Some(0.52),
            path_ranker_execution_gate_status: Some("pass".to_string()),
            path_ranker_runtime_source: Some("registered_artifact".to_string()),
            path_prior: 0.5,
            path_posterior: 0.36,
            bbn_support_score: 0.36,
            composite_preference_score: 0.355,
            stop_definition: "generic-stop".to_string(),
            target_definition: "generic-target".to_string(),
            expected_failure_mode: "generic-fail".to_string(),
            max_time_in_trade: "1h".to_string(),
            ..StructuralPathArtifact::default()
        };

        let bundle = structural_recommended_path_bundle_from_candidates(
            "DENSE_KLINE_BRANCH".to_string(),
            "structural-candidates:DENSE_KLINE_BRANCH:test".to_string(),
            Some(runtime),
            None,
            vec![generic_scenario, exact_path.clone()],
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, exact_path.path_id);
    }

    #[test]
    fn recommended_path_bundle_prefers_observed_feedback_branch_over_generic_branch_when_history_is_strong(
    ) {
        let runtime = StructuralPathRankerRuntimeSurface {
            enabled: true,
            reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY.to_string()),
            status: "using_history_scores".to_string(),
            artifact_match_count: 0,
            candidate_set_match_count: 2,
            history_match_count: 2,
            applied_path_count: 2,
            score_model_family: Some("catboost".to_string()),
            score_source_kind: Some("external_model".to_string()),
            score_model_artifact_uri: None,
            score_generator: None,
        };
        let exact_sweep_branch = StructuralPathArtifact {
            path_id:
                "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
                    .to_string(),
            scenario_id: "scenario:exact-sweep".to_string(),
            path_label:
                "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
                    .to_string(),
            direction: "Observe".to_string(),
            entry_style: "structural_feedback_path".to_string(),
            historical_total_records: 62,
            historical_followed_count: 62,
            catboost_score: Some(0.384),
            path_ranker_runtime_source: Some("history_path".to_string()),
            path_prior: 0.48,
            path_posterior: 0.384,
            bbn_support_score: 0.384,
            composite_preference_score: 0.414,
            stop_definition: "sweep-stop".to_string(),
            target_definition: "sweep-target".to_string(),
            expected_failure_mode: "sweep-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };
        let generic_order_block_branch = StructuralPathArtifact {
            path_id:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            scenario_id: "scenario:order-block".to_string(),
            path_label:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            direction: "Observe".to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            historical_total_records: 1,
            historical_followed_count: 0,
            catboost_score: Some(0.5),
            path_ranker_runtime_source: Some("history_path".to_string()),
            path_prior: 0.49,
            path_posterior: 0.384,
            bbn_support_score: 0.384,
            composite_preference_score: 0.415,
            stop_definition: "generic-stop".to_string(),
            target_definition: "generic-target".to_string(),
            expected_failure_mode: "generic-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };

        let bundle = structural_recommended_path_bundle_from_candidates(
            "SMALLCYCLE_SWEEP_NQ4H_CONFIRMATION".to_string(),
            "structural-candidates:SMALLCYCLE_SWEEP_NQ4H_CONFIRMATION:test".to_string(),
            Some(runtime),
            None,
            vec![generic_order_block_branch, exact_sweep_branch.clone()],
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, exact_sweep_branch.path_id);
    }

    #[test]
    fn recommended_path_bundle_prefers_history_scored_feedback_branch_over_synthetic_regime_branch()
    {
        let runtime = StructuralPathRankerRuntimeSurface {
            enabled: true,
            reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY.to_string()),
            status: "using_history_scores".to_string(),
            history_match_count: 1,
            applied_path_count: 1,
            score_model_family: Some("catboost".to_string()),
            score_source_kind: Some("external_model".to_string()),
            ..StructuralPathRankerRuntimeSurface::default()
        };
        let exact_sweep_branch = StructuralPathArtifact {
            path_id:
                "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
                    .to_string(),
            scenario_id: "scenario:exact-sweep".to_string(),
            path_label:
                "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
                    .to_string(),
            direction: "bull".to_string(),
            entry_style: "structural_feedback_path".to_string(),
            historical_total_records: 62,
            historical_followed_count: 62,
            catboost_score: Some(0.965975),
            path_ranker_calibrated_path_prob: Some(0.484375),
            path_ranker_path_prob_lower_bound: Some(0.382716),
            path_ranker_execution_gate_status: Some("observe".to_string()),
            path_ranker_runtime_source: Some("history_path".to_string()),
            path_prior: 0.485765,
            path_posterior: 0.483886,
            bbn_support_score: 0.483886,
            composite_preference_score: 0.464103,
            stop_definition: "sweep-stop".to_string(),
            target_definition: "sweep-target".to_string(),
            expected_failure_mode: "sweep-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };
        let synthetic_order_block_branch = StructuralPathArtifact {
            path_id:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            scenario_id: "scenario:order-block".to_string(),
            path_label:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            direction: "bear".to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            historical_total_records: 1,
            historical_followed_count: 0,
            catboost_score: Some(0.384068),
            path_ranker_runtime_source: None,
            path_prior: 0.486983,
            path_posterior: 0.384068,
            bbn_support_score: 0.384068,
            composite_preference_score: 0.414943,
            stop_definition: "order-block-stop".to_string(),
            target_definition: "order-block-target".to_string(),
            expected_failure_mode: "order-block-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };

        let bundle = structural_recommended_path_bundle_from_candidates(
            "SMALLCYCLE_SWEEP_NQ4H_CONFIRMATION".to_string(),
            "structural-candidates:SMALLCYCLE_SWEEP_NQ4H_CONFIRMATION:test".to_string(),
            Some(runtime),
            None,
            vec![synthetic_order_block_branch, exact_sweep_branch.clone()],
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, exact_sweep_branch.path_id);
        assert_eq!(
            bundle.path_ranker_runtime_source.as_deref(),
            Some("history_path")
        );
    }

    #[test]
    fn recommended_path_bundle_prefers_current_pre_bayes_branch_over_unrelated_higher_score() {
        let runtime = StructuralPathRankerRuntimeSurface {
            enabled: true,
            reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY.to_string()),
            status: "using_candidate_set_scores".to_string(),
            candidate_set_match_count: 3,
            applied_path_count: 3,
            score_model_family: Some("catboost".to_string()),
            score_source_kind: Some("external_model".to_string()),
            ..StructuralPathRankerRuntimeSurface::default()
        };
        let liquidity_branch =
            "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1";
        let liquidity_path = StructuralPathArtifact {
            path_id: liquidity_branch.to_string(),
            scenario_id: "scenario:liquidity-texture".to_string(),
            path_label: liquidity_branch.to_string(),
            direction: "Observe".to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            historical_total_records: 30,
            historical_followed_count: 30,
            catboost_score: Some(0.538345),
            path_ranker_runtime_source: Some("candidate_set".to_string()),
            path_prior: 0.665,
            path_posterior: 0.537,
            bbn_support_score: 0.537,
            composite_preference_score: 0.576,
            stop_definition: "liquidity-stop".to_string(),
            target_definition: "liquidity-target".to_string(),
            expected_failure_mode: "liquidity-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };
        let order_block_path = StructuralPathArtifact {
            path_id:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            scenario_id: "scenario:order-block".to_string(),
            path_label:
                "Transition -> OrderBlockVariant -> ob_mitigation_breaker_rejection -> order_block_variant_classifier_v1"
                    .to_string(),
            direction: "Observe".to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            historical_total_records: 49,
            historical_followed_count: 49,
            catboost_score: Some(0.700935),
            path_ranker_runtime_source: Some("candidate_set".to_string()),
            path_prior: 0.665,
            path_posterior: 0.537,
            bbn_support_score: 0.537,
            composite_preference_score: 0.594,
            stop_definition: "order-block-stop".to_string(),
            target_definition: "order-block-target".to_string(),
            expected_failure_mode: "order-block-fail".to_string(),
            max_time_in_trade: "15m".to_string(),
            ..StructuralPathArtifact::default()
        };

        let bundle = structural_recommended_path_bundle_from_candidates(
            "LPT_IBKR_TLT_FEEDBACK_193517".to_string(),
            "structural-candidates:LPT_IBKR_TLT_FEEDBACK_193517:test".to_string(),
            Some(runtime),
            Some(liquidity_branch),
            vec![order_block_path, liquidity_path.clone()],
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, liquidity_path.path_id);
    }

    #[test]
    fn recommended_path_bundle_can_select_current_auto_quant_material_rank_branch() {
        let temp = tempfile::tempdir().unwrap();
        let symbol = "NQ";
        let branch_path = "RangeConsolidation -> TightRangeBandExpansionFade -> ibkr_si5m_tight_range_band_expansion_fade_1m_gate1_v1";
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id: "auto-quant-agent-material-rank:strategy-library:NQ:test".to_string(),
            generated_at: Utc::now(),
            symbol: symbol.to_string(),
            source_dispatch_artifact_id: "dispatch-si5m".to_string(),
            ranking: vec![crate::application::auto_quant::AgentMaterialRankRow {
                unit_label: "SI dense fade".to_string(),
                status: "completed".to_string(),
                regime_profit_branch_path: Some(branch_path.to_string()),
                main_regime: Some("RangeConsolidation".to_string()),
                sub_regime: Some("TightRangeBandExpansionFade".to_string()),
                sub_sub_regime_or_profit_factor: Some(
                    "ibkr_si5m_tight_range_band_expansion_fade_1m_gate1_v1".to_string(),
                ),
                profit_factor: Some(
                    "ibkr_si5m_tight_range_band_expansion_fade_1m_gate1_v1".to_string(),
                ),
                win_rate_pct: Some(77.7),
                sharpe: Some(1.42),
                total_profit_pct: Some(1.33),
                trade_count: Some(42),
                ..crate::application::auto_quant::AgentMaterialRankRow::default()
            }],
        };
        let summary = export_structural_path_ranking_target_with_agent_material_rank(
            temp.path().to_str().unwrap(),
            symbol,
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            Some(&rank_artifact),
        )
        .unwrap();
        apply_structural_path_ranking_external_scores(
            temp.path().to_str().unwrap(),
            symbol,
            &[StructuralPathRankingExternalScoreInput {
                candidate_set_id: rank_artifact.artifact_id.clone(),
                path_id: branch_path.to_string(),
                raw_path_score: 0.91,
                score_model_family: Some("catboost".to_string()),
                score_source_kind: Some("external_model".to_string()),
                score_model_artifact_uri: Some("path_ranker_model/catboost_model.cbm".to_string()),
                score_generator: Some("test-auto-quant-material-scorer".to_string()),
            }],
        )
        .unwrap();
        crate::application::entry_models::enable_structural_path_ranking_runtime_command(
            temp.path().to_str().unwrap(),
            symbol,
            STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
        )
        .unwrap();

        let rows = load_structural_path_ranking_target_rows(Path::new(&summary.jsonl_path))
            .expect("target rows");
        assert!(
            rows.iter().any(|row| {
                row.candidate_set_id == rank_artifact.artifact_id
                    && row.path_id == branch_path
                    && row.raw_path_score == Some(0.91)
            }),
            "test setup must persist the exact Auto-Quant material branch score"
        );

        let bundle =
            build_structural_recommended_path_bundle_artifact_with_state_dir_and_prior_state(
                &snapshot,
                &ProviderCatalogAgentSurface::default(),
                &[],
                &StructuralPriorLearningState::default(),
                Some(temp.path().to_str().unwrap()),
            )
            .expect("recommended path bundle");

        assert_eq!(bundle.path_id, branch_path);
        assert_eq!(bundle.path_ranker_raw_score, Some(0.91));
        assert_eq!(
            bundle.path_ranker_runtime_source.as_deref(),
            Some("candidate_set")
        );
    }

    #[test]
    fn target_export_preserves_applied_auto_quant_material_rank_score_after_refresh() {
        let temp = tempfile::tempdir().unwrap();
        let symbol = "TRX";
        let branch_path = "TrendExpansion -> CryptoIchimokuCloudContinuation -> bybit_trxusdt_ichimoku_cloud_continuation_4h_exact_v1";
        let snapshot =
            crate::application::orchestration::workflow_status::sample_human_workflow_snapshot();
        let rank_artifact = crate::application::auto_quant::AgentMaterialRankArtifact {
            artifact_id: "auto-quant-agent-material-rank:strategy-library:TRX:test".to_string(),
            generated_at: Utc::now(),
            symbol: symbol.to_string(),
            source_dispatch_artifact_id: "dispatch-trx4h".to_string(),
            ranking: vec![crate::application::auto_quant::AgentMaterialRankRow {
                unit_label: "TRXUSDT Ichimoku 4h exact".to_string(),
                status: "completed".to_string(),
                regime_profit_branch_path: Some(branch_path.to_string()),
                main_regime: Some("TrendExpansion".to_string()),
                sub_regime: Some("CryptoIchimokuCloudContinuation".to_string()),
                sub_sub_regime_or_profit_factor: Some(
                    "bybit_trxusdt_ichimoku_cloud_continuation_4h_exact_v1".to_string(),
                ),
                profit_factor: Some(
                    "bybit_trxusdt_ichimoku_cloud_continuation_4h_exact_v1".to_string(),
                ),
                win_rate_pct: Some(66.7),
                sharpe: Some(1.84),
                total_profit_pct: Some(2.45),
                trade_count: Some(12),
                ..crate::application::auto_quant::AgentMaterialRankRow::default()
            }],
        };
        export_structural_path_ranking_target_with_agent_material_rank(
            temp.path().to_str().unwrap(),
            symbol,
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            Some(&rank_artifact),
        )
        .unwrap();
        apply_structural_path_ranking_external_scores(
            temp.path().to_str().unwrap(),
            symbol,
            &[StructuralPathRankingExternalScoreInput {
                candidate_set_id: rank_artifact.artifact_id.clone(),
                path_id: branch_path.to_string(),
                raw_path_score: 0.8298382441725878,
                score_model_family: Some("catboost".to_string()),
                score_source_kind: Some("external_model".to_string()),
                score_model_artifact_uri: Some("path_ranker_model/catboost_model.cbm".to_string()),
                score_generator: Some("pandas_path_ranker_trainer.py".to_string()),
            }],
        )
        .unwrap();

        let refreshed = export_structural_path_ranking_target_with_agent_material_rank(
            temp.path().to_str().unwrap(),
            symbol,
            &snapshot,
            &ProviderCatalogAgentSurface::default(),
            &[],
            &StructuralPriorLearningState::default(),
            Some(&rank_artifact),
        )
        .unwrap();

        for path in [&refreshed.jsonl_path, &refreshed.history_jsonl_path] {
            let rows = load_structural_path_ranking_target_rows(Path::new(path)).unwrap();
            let exact = rows
                .iter()
                .find(|row| {
                    row.candidate_set_id == rank_artifact.artifact_id && row.path_id == branch_path
                })
                .expect("refreshed exact Auto-Quant material row");
            assert_eq!(exact.raw_path_score, Some(0.8298382441725878));
            assert_eq!(exact.score_model_family.as_deref(), Some("catboost"));
            assert_eq!(exact.score_source_kind.as_deref(), Some("external_model"));
            assert_eq!(
                exact.score_model_artifact_uri.as_deref(),
                Some("path_ranker_model/catboost_model.cbm")
            );
            assert_eq!(
                exact.score_generator.as_deref(),
                Some("pandas_path_ranker_trainer.py")
            );
        }
    }

    #[test]
    fn recommended_path_bundle_prefers_higher_scored_current_auto_quant_material_rank_branch_under_registered_artifact_runtime(
    ) {
        let runtime = StructuralPathRankerRuntimeSurface {
            enabled: true,
            reuse_mode: Some(STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY.to_string()),
            status: "using_registered_artifact_scores".to_string(),
            artifact_match_count: 3,
            candidate_set_match_count: 1,
            history_match_count: 0,
            applied_path_count: 3,
            score_model_family: Some("catboost".to_string()),
            score_source_kind: Some("external_model".to_string()),
            score_model_artifact_uri: Some("path_ranker_model/catboost_model.cbm".to_string()),
            score_generator: Some("pandas_path_ranker_trainer.py".to_string()),
        };
        let liquidity_branch =
            "Transition -> LiquidityMap -> liquidity_pool_texture -> liquidity_pool_texture:observation_v1";
        let exact_aq_branch = "RangeConsolidation -> TightRangeBandExpansionFade -> ibkr_si5m_tight_range_band_expansion_fade_1m_gate1_v1";
        let liquidity_path = StructuralPathArtifact {
            path_id: liquidity_branch.to_string(),
            scenario_id: "regime-bundle-branch:3f508910efe0520f".to_string(),
            path_label: liquidity_branch.to_string(),
            direction: "favor_mean_reversion_only".to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            historical_total_records: 2,
            historical_followed_count: 2,
            catboost_score: Some(0.8264553496921968),
            path_ranker_runtime_source: Some("registered_artifact_history".to_string()),
            path_prior: 0.5220524826481612,
            path_posterior: 0.6102018853814164,
            bbn_support_score: 0.6102018853814164,
            composite_preference_score: 0.6102018853814164,
            stop_definition: "liquidity-stop".to_string(),
            target_definition: "liquidity-target".to_string(),
            expected_failure_mode: "liquidity-fail".to_string(),
            max_time_in_trade: "5m".to_string(),
            ..StructuralPathArtifact::default()
        };
        let exact_aq_path = StructuralPathArtifact {
            path_id: exact_aq_branch.to_string(),
            scenario_id: "auto-quant-agent-material-rank:971588fa6a418f00".to_string(),
            path_label: "ibkr_si5m_tight_range_band_expansion_fade_dense_fade_v1".to_string(),
            direction: "favor_mean_reversion_only".to_string(),
            entry_style: "auto_quant_agent_material_rank".to_string(),
            historical_total_records: 0,
            historical_followed_count: 0,
            catboost_score: Some(0.8298382441725878),
            path_ranker_runtime_source: Some("registered_artifact".to_string()),
            path_prior: 0.75,
            path_posterior: 0.75,
            bbn_support_score: 0.75,
            composite_preference_score: 0.75,
            stop_definition: "auto-quant-stop".to_string(),
            target_definition: "auto-quant-target".to_string(),
            expected_failure_mode: "auto-quant-fail".to_string(),
            max_time_in_trade: "5m".to_string(),
            ..StructuralPathArtifact::default()
        };

        let bundle = structural_recommended_path_bundle_from_candidates(
            "IBKR_SI5M_TIGHT_RANGE_CANONICAL_EXACT_DOWNSTREAM_V1".to_string(),
            "structural-candidates:IBKR_SI5M_TIGHT_RANGE_CANONICAL_EXACT_DOWNSTREAM_V1:c4be2410dbb5696c"
                .to_string(),
            Some(runtime),
            None,
            vec![liquidity_path, exact_aq_path.clone()],
        )
        .expect("recommended path bundle");

        assert_eq!(bundle.path_id, exact_aq_path.path_id);
        assert_eq!(bundle.path_ranker_raw_score, Some(0.8298382441725878));
        assert_eq!(
            bundle.path_ranker_runtime_source.as_deref(),
            Some("registered_artifact")
        );
    }

    #[test]
    fn default_runtime_includes_same_family_regime_profit_feedback_paths() {
        let branch_path = "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1";
        let regime_bundle = vec![StructuralPathArtifact {
            path_id: branch_path.to_string(),
            scenario_id: "scenario:regime-bundle".to_string(),
            path_label: branch_path.to_string(),
            entry_style: "regime_bundle_branch_path".to_string(),
            ..StructuralPathArtifact::default()
        }];
        let feedback_paths = vec![StructuralPathArtifact {
            path_id: branch_path.to_string(),
            scenario_id: "scenario:feedback".to_string(),
            path_label: branch_path.to_string(),
            entry_style: "structural_feedback_path".to_string(),
            historical_total_records: 2,
            ..StructuralPathArtifact::default()
        }];

        assert!(structural_should_include_feedback_paths(
            false,
            &regime_bundle,
            &feedback_paths,
        ));
    }

    #[test]
    fn target_export_keeps_exact_split_current_rows_when_candidate_set_differs() {
        let exact_path =
            "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim_ibkr_5m -> dense_kline_upbar_reclaim_ibkr_qqq_5m_v1";
        let generic_path =
            "TrendExpansion -> SessionLiquidity -> dense_kline_upbar_reclaim -> dense_kline_upbar_reclaim_long_v1";
        let mk_row =
            |candidate_set_id: &str,
             path_id: &str,
             pending_reward_state: &str,
             current_posterior: f64,
             raw_path_score: Option<f64>| StructuralPathRankingTargetRow {
                rank: 1,
                candidate_set_id: candidate_set_id.to_string(),
                candidate_set_size: 1,
                path_id: path_id.to_string(),
                scenario_id: format!("scenario:{path_id}"),
                path_label: path_id.to_string(),
                regime_profit_branch_path: None,
                parent_regime_root: None,
                main_regime: None,
                sub_regime: None,
                sub_sub_regime_or_profit_factor: None,
                profit_factor: None,
                direction: "Observe".to_string(),
                raw_path_score,
                calibrated_path_prob: raw_path_score,
                path_prob_lower_bound: raw_path_score.map(|score| (score - 0.1).clamp(0.0, 1.0)),
                execution_gate_status: None,
                execution_gate_min_path_prob: None,
                execution_gate_reason: None,
                pending_reward_state: pending_reward_state.to_string(),
                maturity_mask: true,
                maturity_weight: 1.0,
                calibrated_label: structural_path_ranking_reward_label(pending_reward_state),
                propensity_estimate: Some(0.5),
                ips_weight: Some(2.0),
                training_weight: structural_path_ranking_reward_label(pending_reward_state)
                    .map(|_| 2.0),
                regime_calibration_bucket: "DENSE_KLINE_BRANCH:trend".to_string(),
                behavior_policy_probability: 0.5,
                execution_propensity: Some(0.5),
                target_policy_probability_confidence: Some(0.55),
                target_policy_probability_lower_bound: Some(0.30),
                target_policy_reward_prior: Some(0.58),
                target_policy_reward_lower_bound: Some(0.28),
                experience_prior: 0.5,
                current_posterior,
                structural_baseline_score: 0.5,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: None,
                score_source_kind: None,
                score_model_artifact_uri: None,
                score_generator: None,
            };
        let current_rows = vec![mk_row(
            "structural-candidates:DENSE_KLINE_BRANCH:current",
            generic_path,
            "matured_success",
            0.88,
            None,
        )];
        let feedback_rows = vec![
            mk_row(
                "structural-feedback-history:DENSE_KLINE_BRANCH:exact",
                exact_path,
                "matured_failure",
                0.5,
                Some(0.5),
            ),
            mk_row(
                "structural-candidates:DENSE_KLINE_BRANCH:current",
                generic_path,
                "matured_success",
                0.88,
                Some(0.75),
            ),
        ];

        let merged =
            structural_path_ranking_current_feedback_target_rows(&feedback_rows, &current_rows);

        assert!(merged.iter().any(|row| {
            row.candidate_set_id == "structural-feedback-history:DENSE_KLINE_BRANCH:exact"
                && row.path_id == exact_path
                && row.raw_path_score == Some(0.5)
        }));
        assert!(!merged.iter().any(|row| {
            row.candidate_set_id == "structural-candidates:DENSE_KLINE_BRANCH:current"
                && row.path_id == generic_path
        }));
    }
}
