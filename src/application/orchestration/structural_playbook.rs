use chrono::SecondsFormat;
use serde::{Deserialize, Serialize};

use crate::application::belief::{
    blend_branch_prior_with_transition_prior, blend_node_posterior_with_duration_prior,
    transition_adjusted_branch_posteriors,
};
use crate::application::provider_catalog::{
    build_workflow_provider_support, ProviderCatalogAgentSurface,
};
use crate::state::{
    recommended_next_command_meta, FeedbackFactorUsage, FeedbackRecord, ModelProbabilitySnapshot,
    StructuralFeedbackRefs, StructuralPriorLearningState, StructuralPriorStats, WorkflowSnapshot,
};
use crate::types::{Direction, Regime};

const STRUCTURAL_PLAYBOOK_ARTIFACT_VERSION: &str = "structural-playbook-v1";

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPlaybookBundle {
    pub artifact_version: String,
    pub symbol: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_profile_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub selected_profile_data_contracts: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub selected_profile_track_statuses: Vec<String>,
    pub node: StructuralNodeArtifact,
    pub branch_set: StructuralBranchSetArtifact,
    pub scenario_playbook: StructuralScenarioPlaybookArtifact,
    pub path_plan: StructuralPathPlanArtifact,
    pub history_summary: StructuralHistorySummaryArtifact,
    pub node_history: StructuralNodeHistoryArtifact,
    pub branch_history: StructuralBranchHistoryArtifact,
    pub scenario_history: StructuralScenarioHistoryArtifact,
    pub path_history: StructuralPathHistoryArtifact,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_path_bundle: Option<StructuralRecommendedPathBundleArtifact>,
    pub feedback_template: StructuralFeedbackTemplateArtifact,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralNodeArtifact {
    pub node_id: String,
    pub node_family: String,
    pub node_label: String,
    pub focus_phase: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub market_context: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub timeframe_scope: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub supporting_evidence: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub invalidating_evidence: Vec<String>,
    pub belief_prior: f64,
    pub belief_posterior: f64,
    pub posterior_confidence: f64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub origin_artifacts: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralBranchSetArtifact {
    pub from_node_id: String,
    pub branches: Vec<StructuralBranchArtifact>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralBranchArtifact {
    pub branch_id: String,
    pub target_node_id: String,
    pub branch_label: String,
    pub prior_probability: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_weighted_observation_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transition_temporal_posterior_support: Option<f64>,
    pub posterior_probability: f64,
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
    pub composite_branch_score: f64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub activation_conditions: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub failure_conditions: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub supporting_evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralScenarioPlaybookArtifact {
    pub scenarios: Vec<StructuralScenarioArtifact>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralScenarioArtifact {
    pub scenario_id: String,
    pub branch_id: String,
    pub scenario_label: String,
    pub narrative: String,
    pub prior_probability: f64,
    pub posterior_probability: f64,
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
    pub composite_scenario_score: f64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_confirmations: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub hard_invalidations: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub timing_constraints: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub path_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathPlanArtifact {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_data_contracts: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_provider_tracks: Vec<String>,
    pub paths: Vec<StructuralPathArtifact>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathHistoryArtifact {
    pub summary: StructuralPathHistorySummary,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub paths: Vec<StructuralPathOutcomeSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralHistorySummaryArtifact {
    pub total_records: usize,
    pub distinct_nodes: usize,
    pub distinct_branches: usize,
    pub distinct_scenarios: usize,
    pub distinct_paths: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_node_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_branch_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_scenario_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_path_id: Option<String>,
}

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
    pub duration_weighted_streak_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_outcome_support: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub duration_temporal_posterior_support: Option<f64>,
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
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralExperiencePriorSurfaceArtifact {
    pub symbol: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub node: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub branch: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub scenario: Option<StructuralExperiencePriorEntry>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path: Option<StructuralExperiencePriorEntry>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralTopPathCandidatesArtifact {
    pub symbol: String,
    pub candidate_set_id: String,
    pub candidate_count: usize,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub candidates: Vec<StructuralTopPathCandidate>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralRecommendedPathBundleArtifact {
    pub symbol: String,
    pub rank: usize,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    pub selected_path_probability: f64,
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub experience_prior: f64,
    pub current_posterior: f64,
    pub composite_score: f64,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    pub why_this_path: String,
    pub trigger_summary: String,
    pub confirmation_summary: String,
    pub stop_summary: String,
    pub invalidation_summary: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralTopPathCandidate {
    pub rank: usize,
    pub candidate_set_id: String,
    pub behavior_policy_probability: f64,
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub experience_prior: f64,
    pub current_posterior: f64,
    pub composite_score: f64,
    #[serde(default)]
    pub historical_total_records: usize,
    #[serde(default)]
    pub historical_followed_count: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub historical_invalidation_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
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
    pub snips_weight_mass: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub snips_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub doubly_robust_reward_prior: Option<f64>,
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

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralNodeHistoryArtifact {
    pub summary: StructuralEntityHistorySummary,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub nodes: Vec<StructuralNodeOutcomeSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralBranchHistoryArtifact {
    pub summary: StructuralEntityHistorySummary,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub branches: Vec<StructuralBranchOutcomeSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralScenarioHistoryArtifact {
    pub summary: StructuralEntityHistorySummary,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub scenarios: Vec<StructuralScenarioOutcomeSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralEntityHistorySummary {
    pub total_records: usize,
    pub distinct_entities: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_entity_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralNodeOutcomeSummary {
    pub node_id: String,
    pub total_records: usize,
    pub followed_count: usize,
    pub wins: usize,
    pub losses: usize,
    pub breakevens: usize,
    pub invalidated: usize,
    pub abandoned: usize,
    pub not_followed: usize,
    pub avg_pnl: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub off_policy_exposure_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recommended_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_realized_outcome: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralBranchOutcomeSummary {
    pub node_id: String,
    pub branch_id: String,
    pub total_records: usize,
    pub followed_count: usize,
    pub wins: usize,
    pub losses: usize,
    pub breakevens: usize,
    pub invalidated: usize,
    pub abandoned: usize,
    pub not_followed: usize,
    pub avg_pnl: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub off_policy_exposure_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recommended_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_realized_outcome: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralScenarioOutcomeSummary {
    pub node_id: String,
    pub branch_id: String,
    pub scenario_id: String,
    pub total_records: usize,
    pub followed_count: usize,
    pub wins: usize,
    pub losses: usize,
    pub breakevens: usize,
    pub invalidated: usize,
    pub abandoned: usize,
    pub not_followed: usize,
    pub avg_pnl: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub off_policy_exposure_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recommended_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_realized_outcome: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathHistorySummary {
    pub total_records: usize,
    pub distinct_paths: usize,
    pub distinct_branches: usize,
    pub distinct_scenarios: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub latest_path_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathOutcomeSummary {
    pub node_id: String,
    pub branch_id: String,
    pub scenario_id: String,
    pub path_id: String,
    pub total_records: usize,
    pub followed_count: usize,
    pub wins: usize,
    pub losses: usize,
    pub breakevens: usize,
    pub invalidated: usize,
    pub abandoned: usize,
    pub not_followed: usize,
    pub avg_pnl: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub off_policy_exposure_rate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_recommended_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_realized_outcome: Option<String>,
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
    let Some((active_regime, probabilities, confidence)) =
        canonical_phase_regime_surface(phase)
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

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathArtifact {
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    pub entry_style: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pre_bayes_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub multi_timeframe_direction_bias: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_candidate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_candidate_artifact_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_readiness: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub prediction_edge_share: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_edge_share: Option<f64>,
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
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub trigger_conditions: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub confirmation_conditions: Vec<String>,
    pub stop_definition: String,
    pub target_definition: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub invalidation_conditions: Vec<String>,
    pub expected_failure_mode: String,
    pub max_time_in_trade: String,
    pub path_prior: f64,
    pub path_posterior: f64,
    pub bbn_support_score: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub catboost_score: Option<f64>,
    pub composite_preference_score: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub recommended_command: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralFeedbackTemplateArtifact {
    pub protocol_version: String,
    pub recommendation_id: String,
    pub recommended_at: String,
    pub symbol: String,
    pub node_id: String,
    pub branch_id: String,
    pub scenario_id: String,
    pub path_id: String,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    pub selected_path_probability: f64,
    pub direction: String,
    pub entry_style: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pre_bayes_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_posterior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bbn_support_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub allowed_outcomes: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub feedback_fields: Vec<StructuralFeedbackField>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralFeedbackField {
    pub field_id: String,
    pub label: String,
    pub value_type: String,
    pub required: bool,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralFeedbackSubmission {
    pub protocol_version: String,
    pub recommendation_id: String,
    pub recommended_at: String,
    pub symbol: String,
    pub node_id: String,
    pub branch_id: String,
    pub scenario_id: String,
    pub path_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub candidate_set_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub candidate_set_size: Option<usize>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_path_probability: Option<f64>,
    pub direction: String,
    pub entry_style: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_entry_quality_probability: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pre_bayes_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_posterior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub bbn_support_score: Option<f64>,
    pub followed_path: bool,
    pub realized_outcome: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub realized_pnl: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub exit_reason: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub notes: Option<String>,
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
    let scenario_history =
        build_structural_scenario_history_artifact(snapshot, feedback_history);
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
    let path_plan = build_structural_path_plan_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &provider_support,
        &scenario_playbook,
        &path_history,
        structural_prior_state,
    );
    let feedback_template = build_structural_feedback_template_artifact(
        snapshot,
        &node,
        &branch_set,
        &scenario_playbook,
        &path_plan,
    );
    let recommended_path_bundle = build_structural_recommended_path_bundle_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
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
        .or_else(|| playbook.branch_set.branches.first().map(|branch| branch.branch_id.as_str()));
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
        .or_else(|| playbook.path_plan.paths.first().map(|path| path.path_id.as_str()));
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
                source_panel_count: structural_source_panel_count(prior_stats),
                last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                execution_propensity: structural_prior_execution_propensity(prior_stats),
                ips_weight: structural_prior_ips_weight(prior_stats),
                counterfactual_reward_prior: structural_prior_counterfactual_reward_prior(
                    prior_stats,
                ),
                off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                    prior_stats,
                ),
                behavior_policy_probability: structural_prior_behavior_policy_probability(
                    prior_stats,
                ),
                snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                    prior_stats,
                ),
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: branch.transition_weighted_observation_mass,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: branch.transition_outcome_support,
                transition_temporal_posterior_support: branch.transition_temporal_posterior_support,
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
                        source_panel_count: structural_source_panel_count(prior_stats),
                        last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        execution_propensity: structural_prior_execution_propensity(prior_stats),
                        ips_weight: structural_prior_ips_weight(prior_stats),
                        counterfactual_reward_prior:
                            structural_prior_counterfactual_reward_prior(prior_stats),
                        off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                            prior_stats,
                        ),
                        behavior_policy_probability: structural_prior_behavior_policy_probability(
                            prior_stats,
                        ),
                        snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                        snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                        doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                            prior_stats,
                        ),
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
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
                source_panel_count: structural_source_panel_count(prior_stats),
                last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                execution_propensity: structural_prior_execution_propensity(prior_stats),
                ips_weight: structural_prior_ips_weight(prior_stats),
                counterfactual_reward_prior: structural_prior_counterfactual_reward_prior(
                    prior_stats,
                ),
                off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                    prior_stats,
                ),
                behavior_policy_probability: structural_prior_behavior_policy_probability(
                    prior_stats,
                ),
                snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                    prior_stats,
                ),
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: None,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
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
                        historical_invalidation_rate:
                            structural_scenario_history_invalidation_rate(Some(summary)),
                        historical_avg_pnl: Some(summary.avg_pnl),
                        experience_prior,
                        current_posterior: None,
                        composite_score: experience_prior,
                        source_panel_count: structural_source_panel_count(prior_stats),
                        last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        execution_propensity: structural_prior_execution_propensity(prior_stats),
                        ips_weight: structural_prior_ips_weight(prior_stats),
                        counterfactual_reward_prior:
                            structural_prior_counterfactual_reward_prior(prior_stats),
                        off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                            prior_stats,
                        ),
                        behavior_policy_probability: structural_prior_behavior_policy_probability(
                            prior_stats,
                        ),
                        snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                        snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                        doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                            prior_stats,
                        ),
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
                    }
                })
            })
    });
    let path = path_id.and_then(|id| {
        let prior_stats = structural_prior_state.paths.get(id);
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
                source_panel_count: structural_source_panel_count(prior_stats),
                last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                dominant_source_panel: dominant_source_panel.clone(),
                dominant_source_share,
                dominant_source_prior,
                execution_propensity: structural_prior_execution_propensity(prior_stats),
                ips_weight: structural_prior_ips_weight(prior_stats),
                counterfactual_reward_prior: structural_prior_counterfactual_reward_prior(
                    prior_stats,
                ),
                off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                    prior_stats,
                ),
                behavior_policy_probability: structural_prior_behavior_policy_probability(
                    prior_stats,
                ),
                snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                    prior_stats,
                ),
                duration_streak_count: None,
                duration_avg_streak_length: None,
                duration_persistence_prior: None,
                duration_weighted_streak_mass: None,
                transition_weighted_observation_mass: None,
                duration_outcome_support: None,
                duration_temporal_posterior_support: None,
                transition_outcome_support: None,
                transition_temporal_posterior_support: None,
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
                        historical_invalidation_rate: structural_history_invalidation_rate(
                            Some(summary),
                        ),
                        historical_avg_pnl: Some(summary.avg_pnl),
                        experience_prior,
                        current_posterior: None,
                        composite_score: experience_prior,
                        source_panel_count: structural_source_panel_count(prior_stats),
                        last_offline_seed_source: structural_last_offline_seed_source(prior_stats),
                        dominant_source_panel: dominant_source_panel.clone(),
                        dominant_source_share,
                        dominant_source_prior,
                        execution_propensity: structural_prior_execution_propensity(prior_stats),
                        ips_weight: structural_prior_ips_weight(prior_stats),
                        counterfactual_reward_prior:
                            structural_prior_counterfactual_reward_prior(prior_stats),
                        off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                            prior_stats,
                        ),
                        behavior_policy_probability: structural_prior_behavior_policy_probability(
                            prior_stats,
                        ),
                        snips_weight_mass: structural_prior_snips_weight_mass(prior_stats),
                        snips_reward_prior: structural_prior_snips_reward_prior(prior_stats),
                        doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                            prior_stats,
                        ),
                        duration_streak_count: None,
                        duration_avg_streak_length: None,
                        duration_persistence_prior: None,
                        duration_weighted_streak_mass: None,
                        transition_weighted_observation_mass: None,
                        duration_outcome_support: None,
                        duration_temporal_posterior_support: None,
                        transition_outcome_support: None,
                        transition_temporal_posterior_support: None,
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
        node: Some(StructuralExperiencePriorEntry {
            entity_kind: "node".to_string(),
            entity_id: node_id.to_string(),
            historical_total_records: node_summary.map(|summary| summary.total_records).unwrap_or(0),
            historical_followed_count: node_summary.map(|summary| summary.followed_count).unwrap_or(0),
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
                    structural_history_adjusted_node_prior(playbook.node.belief_prior, node_summary),
                ),
            ),
            source_panel_count: structural_source_panel_count(
                node_prior_stats,
            ),
            last_offline_seed_source: structural_last_offline_seed_source(
                node_prior_stats,
            ),
            dominant_source_panel,
            dominant_source_share,
            dominant_source_prior,
            execution_propensity: structural_prior_execution_propensity(node_prior_stats),
            ips_weight: structural_prior_ips_weight(node_prior_stats),
            counterfactual_reward_prior: structural_prior_counterfactual_reward_prior(
                node_prior_stats,
            ),
            off_policy_adjusted_prior: structural_prior_off_policy_adjusted_prior(
                node_prior_stats,
            ),
            behavior_policy_probability: structural_prior_behavior_policy_probability(
                node_prior_stats,
            ),
            snips_weight_mass: structural_prior_snips_weight_mass(node_prior_stats),
            snips_reward_prior: structural_prior_snips_reward_prior(node_prior_stats),
            doubly_robust_reward_prior: structural_prior_doubly_robust_reward_prior(
                node_prior_stats,
            ),
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
    let node =
        build_structural_node_artifact_with_prior_state(snapshot, provider_status_agent, structural_prior_state);
    let node_duration_prior = structural_prior_state.node_duration_priors.get(&node.node_id);
    let node_temporal_state = structural_prior_state.node_temporal_posteriors.get(&node.node_id);
    let active_regime = structural_active_regime(snapshot);
    let to_branch_id = active_regime
        .as_ref()
        .map(|regime| format!("{}:{}", node.node_id, structural_branch_label_for_regime(regime)));
    let latest_feedback = structural_latest_feedback_refs(snapshot);
    let branch_temporal_state = latest_feedback.as_ref().and_then(|refs| {
        to_branch_id.as_ref().and_then(|branch_id| {
            structural_prior_state
                .branch_temporal_posteriors
                .get(&format!("{}=>{}", refs.branch_id, branch_id))
        })
    });
    let transition_prior = latest_feedback
        .as_ref()
        .and_then(|refs| {
            to_branch_id.as_ref().and_then(|branch_id| {
                structural_branch_transition_prior(structural_prior_state, &refs.branch_id, branch_id)
            })
        });
    let duration_summary = node_temporal_state
        .map(|state| state.summary_line.clone())
        .unwrap_or_else(|| {
            format!(
                "duration_mass={:.3} duration_support={:.3} duration_temporal={:.3} blend=0.000",
                structural_duration_weighted_streak_mass(node_duration_prior).unwrap_or_default(),
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
        transition_prior.map(|prior| prior.transition_prior).unwrap_or_default()
    );

    StructuralTemporalSummaryArtifact {
        symbol: structural_symbol(snapshot),
        node_id: Some(node.node_id),
        from_branch_id: latest_feedback.as_ref().map(|refs| refs.branch_id.clone()),
        to_branch_id,
        duration_streak_count: node_temporal_state
            .map(|state| state.streak_count)
            .or_else(|| structural_duration_streak_count(node_duration_prior)),
        duration_avg_streak_length: structural_duration_avg_streak_length(node_duration_prior),
        duration_persistence_prior: structural_duration_persistence_prior(node_duration_prior),
        duration_weighted_streak_mass: node_temporal_state
            .map(|state| state.weighted_streak_mass)
            .or_else(|| structural_duration_weighted_streak_mass(node_duration_prior)),
        duration_outcome_support: node_temporal_state
            .map(|state| state.duration_outcome_support)
            .or_else(|| structural_duration_outcome_support(node_duration_prior)),
        duration_temporal_posterior_support: node_temporal_state
            .map(|state| state.temporal_posterior_support)
            .or_else(|| structural_duration_temporal_posterior_support(node_duration_prior)),
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
        summary_line,
    }
}

pub fn build_structural_top_path_candidates_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> StructuralTopPathCandidatesArtifact {
    let candidate_paths = structural_ranked_paths(snapshot, provider_status_agent, feedback_history)
        .into_iter()
        .take(3)
        .collect::<Vec<_>>();
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = structural_candidate_set_id(&symbol, &candidate_paths);
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
                recommended_command: path.recommended_command,
            }
        })
        .collect::<Vec<_>>();
    StructuralTopPathCandidatesArtifact {
        symbol,
        candidate_set_id,
        candidate_count,
        candidates,
    }
}

pub fn build_structural_top_path_candidates_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralTopPathCandidatesArtifact {
    let candidate_paths = structural_ranked_paths_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    )
    .into_iter()
    .take(3)
    .collect::<Vec<_>>();
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = structural_candidate_set_id(&symbol, &candidate_paths);
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
                recommended_command: path.recommended_command,
            }
        })
        .collect::<Vec<_>>();
    StructuralTopPathCandidatesArtifact {
        symbol,
        candidate_set_id,
        candidate_count,
        candidates,
    }
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
    for path in candidate_paths {
        fingerprint.push('|');
        fingerprint.push_str(&path.path_id);
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

pub fn build_structural_recommended_path_bundle_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let candidate_paths = structural_ranked_paths(snapshot, provider_status_agent, feedback_history)
        .into_iter()
        .take(3)
        .collect::<Vec<_>>();
    let symbol = structural_symbol(snapshot);
    structural_recommended_path_bundle_from_candidates(symbol, candidate_paths)
}

fn structural_recommended_path_bundle_from_candidates(
    symbol: String,
    candidate_paths: Vec<StructuralPathArtifact>,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let candidate_set_id = structural_candidate_set_id(&symbol, &candidate_paths);
    let denominator = structural_candidate_policy_denominator(&candidate_paths);
    let candidate_set_size = candidate_paths.len();
    let path = candidate_paths.first()?;
    let selected_path_probability = structural_candidate_policy_probability(
        path.composite_preference_score,
        denominator,
        candidate_set_size,
    );
    let why_this_path = structural_why_this_path_summary(path);
    Some(StructuralRecommendedPathBundleArtifact {
        symbol,
        rank: 1,
        candidate_set_id,
        candidate_set_size,
        selected_path_probability,
        path_id: path.path_id.clone(),
        scenario_id: path.scenario_id.clone(),
        path_label: path.path_label.clone(),
        direction: path.direction.clone(),
        experience_prior: path.path_prior,
        current_posterior: path.path_posterior,
        composite_score: path.composite_preference_score,
        historical_total_records: path.historical_total_records,
        historical_invalidation_rate: path.historical_invalidation_rate,
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

pub fn build_structural_recommended_path_bundle_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Option<StructuralRecommendedPathBundleArtifact> {
    let candidate_paths = structural_ranked_paths_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    )
    .into_iter()
    .take(3)
    .collect::<Vec<_>>();
    structural_recommended_path_bundle_from_candidates(structural_symbol(snapshot), candidate_paths)
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
                let resolved_prior =
                    structural_resolved_smoothed_prior(
                        prior_stats,
                        structural_prior_state,
                        history_adjusted_prior,
                    );
                let blended_prior =
                    blend_branch_prior_with_transition_prior(
                        resolved_prior,
                        transition_prior,
                        latest_feedback.as_ref().and_then(|refs| {
                            structural_prior_state.branch_temporal_posteriors.get(
                                &format!("{}=>{}", refs.branch_id, branch_id),
                            )
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
        .collect();
    StructuralScenarioPlaybookArtifact { scenarios }
}

pub fn build_structural_path_plan_artifact(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenarios: &StructuralScenarioPlaybookArtifact,
    path_history: &StructuralPathHistoryArtifact,
) -> StructuralPathPlanArtifact {
    build_structural_path_plan_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        provider_support,
        scenarios,
        path_history,
        &StructuralPriorLearningState::default(),
    )
}

pub fn build_structural_path_plan_artifact_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    provider_support: &crate::application::provider_catalog::WorkflowProviderSupportSurface,
    scenarios: &StructuralScenarioPlaybookArtifact,
    path_history: &StructuralPathHistoryArtifact,
    structural_prior_state: &StructuralPriorLearningState,
) -> StructuralPathPlanArtifact {
    let command = top_level_command(snapshot);
    let next_meta = recommended_next_command_meta(&command);
    let paths = scenarios
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
            let resolved_prior =
                structural_resolved_smoothed_prior(
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
                    historical_summary.map(|summary| summary.total_records).unwrap_or(0),
                ),
                historical_followed_count: structural_resolved_followed_count(
                    prior_stats,
                    historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
                ),
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
        .collect();
    StructuralPathPlanArtifact {
        required_data_contracts: structural_relevant_profile_data_contracts(
            snapshot,
            provider_status_agent,
        ),
        required_provider_tracks: structural_relevant_profile_track_statuses(
            snapshot,
            provider_status_agent,
        ),
        paths,
    }
}

fn structural_ranked_paths(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
) -> Vec<StructuralPathArtifact> {
    structural_ranked_paths_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

fn structural_ranked_paths_with_prior_state(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Vec<StructuralPathArtifact> {
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
    let scenario_history =
        build_structural_scenario_history_artifact(snapshot, feedback_history);
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
    let mut paths = build_structural_path_plan_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        &provider_support,
        &scenario_playbook,
        &path_history,
        structural_prior_state,
    )
    .paths;
    paths.sort_by(|left, right| {
        right
            .composite_preference_score
            .total_cmp(&left.composite_preference_score)
            .then_with(|| right.path_posterior.total_cmp(&left.path_posterior))
            .then_with(|| right.path_prior.total_cmp(&left.path_prior))
    });
    paths
}

fn structural_resolved_smoothed_prior(
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

fn structural_panel_derived_smoothed_prior(
    stats: &StructuralPriorStats,
    structural_prior_state: &StructuralPriorLearningState,
) -> Option<f64> {
    let success_mass: f64 = stats
        .source_panel_summaries
        .iter()
        .map(|(source_label, summary)| {
            summary.weighted_success_mass.max(0.0)
                * structural_source_reliability_multiplier(structural_prior_state, source_label)
        })
        .sum();
    let failure_mass: f64 = stats
        .source_panel_summaries
        .iter()
        .map(|(source_label, summary)| {
            summary.weighted_failure_mass.max(0.0)
                * structural_source_reliability_multiplier(structural_prior_state, source_label)
        })
        .sum();
    if success_mass <= f64::EPSILON && failure_mass <= f64::EPSILON {
        return None;
    }
    let alpha = 1.0 + success_mass;
    let beta = 1.0 + failure_mass;
    Some((alpha / (alpha + beta)).clamp(0.0, 1.0))
}

fn structural_source_reliability_multiplier(
    structural_prior_state: &StructuralPriorLearningState,
    source_label: &str,
) -> f64 {
    structural_prior_state
        .source_reliability_posteriors
        .get(source_label)
        .map(|posterior| {
            if posterior.observations == 0
                && posterior.weighted_observation_mass <= f64::EPSILON
            {
                1.0
            } else {
                posterior.posterior_reliability.clamp(0.0, 1.0)
            }
        })
        .unwrap_or(1.0)
}

fn structural_resolved_observations(
    prior_stats: Option<&StructuralPriorStats>,
    fallback: usize,
) -> usize {
    prior_stats.map(|stats| stats.observations).unwrap_or(fallback)
}

fn structural_resolved_followed_count(
    prior_stats: Option<&StructuralPriorStats>,
    fallback: usize,
) -> usize {
    prior_stats
        .map(|stats| stats.followed_count)
        .unwrap_or(fallback)
}

fn structural_prior_stats_win_rate(prior_stats: Option<&StructuralPriorStats>) -> Option<f64> {
    let stats = prior_stats?;
    if stats.followed_count == 0 {
        None
    } else {
        Some(stats.wins as f64 / stats.followed_count as f64)
    }
}

fn structural_prior_stats_invalidation_rate(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    let stats = prior_stats?;
    if stats.followed_count == 0 {
        None
    } else {
        Some(stats.invalidated as f64 / stats.followed_count as f64)
    }
}

fn structural_resolved_avg_pnl(
    prior_stats: Option<&StructuralPriorStats>,
    fallback: Option<f64>,
) -> Option<f64> {
    prior_stats.map(|stats| stats.avg_pnl).or(fallback)
}

fn structural_resolved_node_win_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralNodeOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_win_rate(prior_stats)
        .or_else(|| structural_node_history_win_rate(historical_summary))
}

fn structural_resolved_node_invalidation_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralNodeOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_invalidation_rate(prior_stats)
        .or_else(|| structural_node_history_invalidation_rate(historical_summary))
}

fn structural_resolved_branch_win_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralBranchOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_win_rate(prior_stats)
        .or_else(|| structural_branch_history_win_rate(historical_summary))
}

fn structural_resolved_branch_invalidation_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralBranchOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_invalidation_rate(prior_stats)
        .or_else(|| structural_branch_history_invalidation_rate(historical_summary))
}

fn structural_resolved_scenario_win_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralScenarioOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_win_rate(prior_stats)
        .or_else(|| structural_scenario_history_win_rate(historical_summary))
}

fn structural_resolved_scenario_invalidation_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralScenarioOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_invalidation_rate(prior_stats)
        .or_else(|| structural_scenario_history_invalidation_rate(historical_summary))
}

fn structural_resolved_path_win_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralPathOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_win_rate(prior_stats)
        .or_else(|| structural_history_win_rate(historical_summary))
}

fn structural_resolved_path_invalidation_rate(
    prior_stats: Option<&StructuralPriorStats>,
    historical_summary: Option<&StructuralPathOutcomeSummary>,
) -> Option<f64> {
    structural_prior_stats_invalidation_rate(prior_stats)
        .or_else(|| structural_history_invalidation_rate(historical_summary))
}

fn structural_short_rule_summary(items: &[String], fallback: &str) -> String {
    items.first()
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
        path.path_posterior,
        path.path_prior,
        invalidation
    )
}

fn structural_history_adjusted_branch_prior(
    base_prior: f64,
    historical_summary: Option<&StructuralBranchOutcomeSummary>,
) -> f64 {
    structural_history_adjusted_prior(
        base_prior,
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
        historical_summary
            .map(|summary| summary.breakevens)
            .unwrap_or(0),
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

fn structural_history_adjusted_node_prior(
    base_prior: f64,
    historical_summary: Option<&StructuralNodeOutcomeSummary>,
) -> f64 {
    structural_history_adjusted_prior(
        base_prior,
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
        historical_summary
            .map(|summary| summary.breakevens)
            .unwrap_or(0),
    )
}

fn structural_history_adjusted_scenario_prior(
    base_prior: f64,
    historical_summary: Option<&StructuralScenarioOutcomeSummary>,
) -> f64 {
    structural_history_adjusted_prior(
        base_prior,
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
        historical_summary
            .map(|summary| summary.breakevens)
            .unwrap_or(0),
    )
}

fn structural_history_adjusted_prior(
    base_prior: f64,
    followed_count: usize,
    wins: usize,
    breakevens: usize,
) -> f64 {
    if followed_count == 0 {
        return base_prior;
    }
    let empirical_success = (wins as f64 + breakevens as f64 * 0.5) / followed_count as f64;
    let sample_weight = (followed_count as f64 / 5.0).min(1.0);
    (base_prior * (1.0 - sample_weight) + empirical_success * sample_weight).clamp(0.0, 1.0)
}

fn structural_history_win_rate_from_counts(
    followed_count: usize,
    wins: usize,
) -> Option<f64> {
    if followed_count == 0 {
        None
    } else {
        Some(wins as f64 / followed_count as f64)
    }
}

fn structural_history_invalidation_rate_from_counts(
    followed_count: usize,
    invalidated: usize,
) -> Option<f64> {
    if followed_count == 0 {
        None
    } else {
        Some(invalidated as f64 / followed_count as f64)
    }
}

fn structural_node_history_win_rate(
    historical_summary: Option<&StructuralNodeOutcomeSummary>,
) -> Option<f64> {
    structural_history_win_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
    )
}

fn structural_node_history_invalidation_rate(
    historical_summary: Option<&StructuralNodeOutcomeSummary>,
) -> Option<f64> {
    structural_history_invalidation_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.invalidated).unwrap_or(0),
    )
}

fn structural_branch_history_win_rate(
    historical_summary: Option<&StructuralBranchOutcomeSummary>,
) -> Option<f64> {
    structural_history_win_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
    )
}

fn structural_branch_history_invalidation_rate(
    historical_summary: Option<&StructuralBranchOutcomeSummary>,
) -> Option<f64> {
    structural_history_invalidation_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.invalidated).unwrap_or(0),
    )
}

fn structural_scenario_history_win_rate(
    historical_summary: Option<&StructuralScenarioOutcomeSummary>,
) -> Option<f64> {
    structural_history_win_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
    )
}

fn structural_scenario_history_invalidation_rate(
    historical_summary: Option<&StructuralScenarioOutcomeSummary>,
) -> Option<f64> {
    structural_history_invalidation_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.invalidated).unwrap_or(0),
    )
}

fn structural_history_adjusted_path_prior(
    base_prior: f64,
    historical_summary: Option<&StructuralPathOutcomeSummary>,
) -> f64 {
    let Some(summary) = historical_summary else {
        return base_prior;
    };
    structural_history_adjusted_prior(
        base_prior,
        summary.followed_count,
        summary.wins,
        summary.breakevens,
    )
}

fn structural_composite_preference_score(
    bbn_support_score: f64,
    history_adjusted_prior: f64,
) -> f64 {
    (bbn_support_score * 0.70 + history_adjusted_prior * 0.30).clamp(0.0, 1.0)
}

fn structural_history_win_rate(
    historical_summary: Option<&StructuralPathOutcomeSummary>,
) -> Option<f64> {
    structural_history_win_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.wins).unwrap_or(0),
    )
}

fn structural_history_invalidation_rate(
    historical_summary: Option<&StructuralPathOutcomeSummary>,
) -> Option<f64> {
    structural_history_invalidation_rate_from_counts(
        historical_summary.map(|summary| summary.followed_count).unwrap_or(0),
        historical_summary.map(|summary| summary.invalidated).unwrap_or(0),
    )
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
            snapshot
                .latest_analyze
                .as_ref()
                .and_then(|analyze| {
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

fn structural_source_panel_count(prior_stats: Option<&StructuralPriorStats>) -> usize {
    prior_stats
        .map(|stats| stats.source_panel_summaries.len())
        .unwrap_or(0)
}

fn structural_last_offline_seed_source(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<String> {
    prior_stats.and_then(|stats| stats.last_offline_seed_source.clone())
}

fn structural_prior_positive_value(
    prior_stats: Option<&StructuralPriorStats>,
    value: impl Fn(&StructuralPriorStats) -> f64,
) -> Option<f64> {
    prior_stats
        .map(value)
        .filter(|candidate| *candidate > f64::EPSILON)
}

fn structural_prior_execution_propensity(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.execution_propensity)
}

fn structural_prior_ips_weight(prior_stats: Option<&StructuralPriorStats>) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.ips_weight)
}

fn structural_prior_counterfactual_reward_prior(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.counterfactual_reward_prior)
}

fn structural_prior_off_policy_adjusted_prior(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.off_policy_adjusted_prior)
}

fn structural_prior_behavior_policy_probability(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.behavior_policy_probability)
}

fn structural_prior_snips_weight_mass(prior_stats: Option<&StructuralPriorStats>) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.snips_weight_mass)
}

fn structural_prior_snips_reward_prior(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.snips_reward_prior)
}

fn structural_prior_doubly_robust_reward_prior(
    prior_stats: Option<&StructuralPriorStats>,
) -> Option<f64> {
    structural_prior_positive_value(prior_stats, |stats| stats.doubly_robust_reward_prior)
}

fn structural_duration_streak_count(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<usize> {
    duration_prior.map(|prior| prior.streak_count)
}

fn structural_duration_avg_streak_length(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.avg_streak_length)
}

fn structural_duration_persistence_prior(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.persistence_prior)
}

fn structural_duration_weighted_streak_mass(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.weighted_streak_mass)
}

fn structural_duration_outcome_support(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.duration_outcome_support)
}

fn structural_duration_temporal_posterior_support(
    duration_prior: Option<&crate::state::StructuralNodeDurationPrior>,
) -> Option<f64> {
    duration_prior.map(|prior| prior.temporal_posterior_support)
}

fn structural_dominant_source_panel(
    prior_stats: Option<&StructuralPriorStats>,
) -> (Option<String>, Option<f64>, Option<f64>) {
    let Some(stats) = prior_stats else {
        return (None, None, None);
    };
    let total_mass: f64 = stats
        .source_panel_summaries
        .values()
        .map(|summary| summary.weighted_followed_mass.max(0.0))
        .sum();
    let dominant = stats
        .source_panel_summaries
        .iter()
        .max_by(|a, b| {
            a.1.weighted_followed_mass
                .partial_cmp(&b.1.weighted_followed_mass)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| a.0.cmp(b.0))
        })
        .map(|(label, summary)| {
            let share = if total_mass <= f64::EPSILON {
                None
            } else {
                Some((summary.weighted_followed_mass / total_mass).clamp(0.0, 1.0))
            };
            (Some(label.clone()), share, Some(summary.smoothed_prior))
        });
    dominant.unwrap_or((None, None, None))
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
    let Some(profile) = provider_status_agent.selected_profile.as_ref() else {
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
    let Some(profile) = provider_status_agent.selected_profile.as_ref() else {
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
    let mut candidate_paths = path_plan.paths.clone();
    candidate_paths.sort_by(|left, right| {
        right
            .composite_preference_score
            .total_cmp(&left.composite_preference_score)
            .then_with(|| right.path_posterior.total_cmp(&left.path_posterior))
            .then_with(|| right.path_prior.total_cmp(&left.path_prior))
    });
    candidate_paths.truncate(3);
    let symbol = structural_symbol(snapshot);
    let candidate_set_id = structural_candidate_set_id(&symbol, &candidate_paths);
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
    (exposure > 0).then(|| {
        ((1.0 + followed_count as f64) / (2.0 + exposure as f64)).clamp(0.0, 1.0)
    })
}

fn structural_history_off_policy_exposure_rate(
    followed_count: usize,
    not_followed: usize,
) -> Option<f64> {
    let exposure = followed_count + not_followed;
    (exposure > 0)
        .then(|| ((1.0 + not_followed as f64) / (2.0 + exposure as f64)).clamp(0.0, 1.0))
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
    let mut summaries =
        std::collections::BTreeMap::<String, StructuralNodeOutcomeSummary>::new();
    for row in structural_feedback_history_rows(feedback_history) {
        let entry = summaries
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
    let mut summaries = std::collections::BTreeMap::<
        (String, String),
        StructuralBranchOutcomeSummary,
    >::new();
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
            total_records: scenarios.iter().map(|scenario| scenario.total_records).sum(),
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
