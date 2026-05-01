use anyhow::Result;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::net::{SocketAddr, TcpStream};
use std::time::Duration;

use super::structural_playbook::{
    build_structural_branch_history_artifact,
    build_structural_branch_set_artifact_with_prior_state,
    build_structural_experience_prior_surface_artifact_with_prior_state,
    build_structural_feedback_template_artifact, build_structural_history_summary_artifact,
    build_structural_node_artifact_with_prior_state,
    build_structural_node_history_artifact, build_structural_path_history_artifact,
    build_structural_path_plan_artifact_with_prior_state,
    build_structural_recommended_path_bundle_artifact_with_prior_state,
    build_structural_playbook_bundle_with_prior_state, build_structural_scenario_history_artifact,
    build_structural_scenario_playbook_artifact_with_prior_state,
    build_structural_top_path_candidates_artifact_with_prior_state,
    resolved_ensemble_vote_for_snapshot, resolved_latest_ensemble_vote,
    StructuralRecommendedPathBundleArtifact,
};
use crate::application::belief::{
    jump_calibration_gate_workflow_summary, jump_model_workflow_summary,
};
use crate::application::output_foundation::{
    print_redacted_json, redact_local_paths_in_human_text, redact_local_paths_in_value,
    short_workflow_phase_summary,
};
use crate::application::provider_catalog::{
    build_workflow_provider_support, provider_status_agent_surface, ProviderCatalogAgentSurface,
};
use crate::application::release_closure::workflow_next_step_view;
use crate::config::shell_quote;
use crate::state::{
    ArtifactConsumedImpactSummary, ArtifactDecisionSummary, ArtifactFactorTrendSummary,
    ArtifactFamilyTrendSummary, ArtifactHistorySummary, ArtifactLineageSummary,
    ArtifactRuleBreakEffect, ArtifactRuleBreakFactorImpact, ArtifactRuleBreakFamilyImpact,
    DatasetComparability, EnsembleExecutorScorecard, EnsembleVoteRecord,
    ExecutionCandidateArtifactSummary, PendingUpdateArtifactSummary, PreBayesEntryQualityBridge,
    PreBayesEntryQualityBridgeDiff, PreBayesEvidencePolicy, PreBayesPolicyDiff,
    PreBayesPolicyLineageSummary, PreBayesPolicyRecord, PreBayesSoftEvidenceNodeDiff,
    RunProvenance, StructuralPriorLearningState, WorkflowSnapshot,
};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowEnsembleVoteSurface {
    pub artifact_id: String,
    pub generated_at: chrono::DateTime<chrono::Utc>,
    pub symbol: String,
    pub source_phase: String,
    pub source_run_id: Option<String>,
    pub provenance: RunProvenance,
    pub dataset_comparability: DatasetComparability,
    pub ensemble_version: String,
    pub final_action: String,
    pub recommended_command: String,
    pub human_next_triage: String,
    pub hard_block: super::EnsembleHardBlockArtifact,
    pub confidence: f64,
    pub consensus_strength: f64,
    pub disagreement_flags: Vec<String>,
    pub executor_summaries: Vec<String>,
    pub split_explanations: Vec<String>,
    pub executor_scorecards: Vec<EnsembleExecutorScorecard>,
    pub executor_scorecard_source: String,
    pub posterior_fingerprint: String,
    pub posterior_normalization_status: String,
    pub posterior_active_regime: String,
    pub posterior_confidence: Option<f64>,
    pub posterior_probabilities: std::collections::BTreeMap<String, f64>,
    pub posterior_evidence: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowEnsembleVoteHistoryRow {
    pub artifact_id: String,
    pub generated_at: chrono::DateTime<chrono::Utc>,
    pub symbol: String,
    pub source_phase: String,
    pub source_run_id: Option<String>,
    pub final_action: String,
    pub recommended_command: String,
    pub human_next_triage: String,
    pub hard_block: super::EnsembleHardBlockArtifact,
    pub executor_scorecards: Vec<EnsembleExecutorScorecard>,
    pub executor_scorecard_source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowHardBlockReasonCount {
    pub reason: String,
    pub count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowHardBlockSummary {
    pub count: usize,
    pub reason_leaderboard: Vec<WorkflowHardBlockReasonCount>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowEnsembleVoteHistoryView {
    pub history: Vec<WorkflowEnsembleVoteHistoryRow>,
    pub hard_block_only: Vec<WorkflowEnsembleVoteHistoryRow>,
    pub hard_block_summary: WorkflowHardBlockSummary,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowAuxiliaryArtifactSurfaces {
    pub pending_update: Option<PendingUpdateArtifactSummary>,
    pub pending_update_history: Vec<PendingUpdateArtifactSummary>,
    pub execution_candidate: Option<ExecutionCandidateArtifactSummary>,
    pub execution_candidate_history: Vec<ExecutionCandidateArtifactSummary>,
    pub artifact_history_summary: ArtifactHistorySummary,
    pub artifact_factor_trends: Vec<ArtifactFactorTrendSummary>,
    pub artifact_family_trends: Vec<ArtifactFamilyTrendSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowArtifactReportSurfaces {
    pub artifact_consumed_gate: Value,
    pub artifact_factor_consumed_validation: Vec<ArtifactFactorTrendSummary>,
    pub artifact_family_consumed_validation: Vec<ArtifactFamilyTrendSummary>,
    pub artifact_lineage_summaries: Vec<ArtifactLineageSummary>,
    pub artifact_decision_summary: ArtifactDecisionSummary,
    pub artifact_rule_breaks: Vec<ArtifactLineageSummary>,
    pub artifact_rule_break_effects: Vec<ArtifactRuleBreakEffect>,
    pub artifact_factor_rule_break_impacts: Vec<ArtifactRuleBreakFactorImpact>,
    pub artifact_family_rule_break_impacts: Vec<ArtifactRuleBreakFamilyImpact>,
    pub artifact_impact_leaderboard: Value,
    pub artifact_impact_consumed: Value,
    pub artifact_impact_consumed_trend: ArtifactConsumedImpactSummary,
    pub artifact_review_rules: crate::state::ArtifactReviewRules,
    pub artifact_review_rule_sources: crate::state::ArtifactReviewRuleSources,
    pub disagreements: Vec<crate::state::WorkflowDisagreement>,
    pub diffs: Vec<crate::state::WorkflowFieldDiff>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowPreBayesSurfaces {
    pub pre_bayes_policy: Option<PreBayesEvidencePolicy>,
    pub pre_bayes_policy_history: Vec<PreBayesPolicyRecord>,
    pub pre_bayes_policy_diff: Option<PreBayesPolicyDiff>,
    pub pre_bayes_policy_lineage: Option<PreBayesPolicyLineageSummary>,
    pub pre_bayes_entry_quality_bridge: Option<PreBayesEntryQualityBridge>,
    pub pre_bayes_entry_quality_bridge_diff: Option<PreBayesEntryQualityBridgeDiff>,
    pub canonical_structural_active_regime: Option<String>,
    pub canonical_structural_confidence: Option<f64>,
    pub canonical_structural_probabilities: std::collections::BTreeMap<String, f64>,
    pub pre_bayes_soft_evidence:
        Option<std::collections::BTreeMap<String, std::collections::BTreeMap<String, f64>>>,
    pub pre_bayes_soft_evidence_diff: Vec<PreBayesSoftEvidenceNodeDiff>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WorkflowPhaseSnapshotSurfaces {
    pub train: Option<crate::state::WorkflowPhaseSnapshot>,
    pub analyze: Option<crate::state::WorkflowPhaseSnapshot>,
    pub research: Option<crate::state::WorkflowPhaseSnapshot>,
    pub backtest: Option<crate::state::WorkflowPhaseSnapshot>,
    pub update: Option<crate::state::WorkflowPhaseSnapshot>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapView {
    pub symbol: String,
    pub project_role: String,
    pub closed_loop_chain: Vec<String>,
    pub agent_brief: Vec<String>,
    pub guardrails: Vec<String>,
    pub detected_paths: AgentBootstrapPaths,
    pub input_acquisition: AgentBootstrapInputs,
    pub commands: AgentBootstrapCommands,
    pub latest_snapshot: AgentBootstrapSnapshot,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapPaths {
    pub tomac_history_root: Option<String>,
    pub multi_timeframe_clean_root: Option<String>,
    pub state_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapCommands {
    pub clean_multi_timeframe: String,
    pub train: String,
    pub analyze: String,
    pub futures_sop: String,
    pub expansion_sop: String,
    pub workflow_status: String,
    pub provider_status: String,
    pub recommended_next_command: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapSnapshot {
    pub current_focus_phase: String,
    pub current_focus_reason: String,
    pub blocking_truth: crate::state::WorkflowBlockingTruth,
    pub latest_train_phase: Option<String>,
    pub latest_analyze_phase: Option<String>,
    pub latest_pre_bayes_gate_status: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapInputs {
    pub backtest: AgentBootstrapBacktestInput,
    pub live: AgentBootstrapLiveInput,
}

#[derive(Debug, Clone, Copy)]
pub struct WorkflowStatusDispatchInput<'a> {
    pub phase: Option<&'a str>,
    pub actionable_only: bool,
    pub conflicts_only: bool,
    pub latest_promotable: bool,
    pub hard_block_only: bool,
    pub hard_block_reason: Option<&'a str>,
    pub limit: Option<usize>,
    pub output_format: &'a str,
    pub stable: bool,
}

#[derive(Debug, Clone)]
pub struct WorkflowStatusBootstrapInput<'a> {
    pub symbol: &'a str,
    pub state_dir: &'a str,
    pub detected_tomac_root: Option<String>,
    pub multi_timeframe_clean_root: Option<String>,
    pub tomac_root_placeholder: String,
}

#[derive(Debug, Clone)]
struct AgentBootstrapBuildInput<'a> {
    symbol: &'a str,
    state_dir: &'a str,
    snapshot: &'a WorkflowSnapshot,
    provider_status_agent: &'a ProviderCatalogAgentSurface,
    detected_tomac_root: Option<String>,
    multi_timeframe_clean_root: Option<String>,
    tomac_root_placeholder: &'a str,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapBacktestInput {
    pub local_discovery_order: Vec<String>,
    pub preferred_user_inputs: Vec<String>,
    pub fallback_user_inputs: Vec<String>,
    pub should_ask_download_link_if_local_missing: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapLiveInput {
    pub minimum_required_user_inputs: Vec<String>,
    pub inferable_defaults:
        std::collections::BTreeMap<String, std::collections::BTreeMap<String, String>>,
    pub additional_user_inputs_if_not_inferable: Vec<String>,
    pub provider_access_requests: Vec<String>,
    pub provider_status_agent: ProviderCatalogAgentSurface,
    pub provider_status_command: String,
    pub ibkr_gateway_summary: AgentBootstrapIbkrGatewaySummary,
    pub ibkr_gateway_candidates: Vec<AgentBootstrapIbkrGatewayCandidate>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapIbkrGatewayCandidate {
    pub label: String,
    pub host: String,
    pub port: u16,
    pub reachable: bool,
    pub recommended: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AgentBootstrapIbkrGatewaySummary {
    pub preferred_label: Option<String>,
    pub preferred_port: Option<u16>,
    pub reachable_candidate_count: usize,
    pub occupied_judgement: String,
    pub recommended_action: String,
}

pub fn build_phase_snapshot_surfaces(snapshot: &WorkflowSnapshot) -> WorkflowPhaseSnapshotSurfaces {
    WorkflowPhaseSnapshotSurfaces {
        train: snapshot.latest_train.clone(),
        analyze: snapshot.latest_analyze.clone(),
        research: snapshot.latest_research.clone(),
        backtest: snapshot.latest_backtest.clone(),
        update: snapshot.latest_update.clone(),
    }
}

pub fn factor_autoresearch_status_value_for_empty_state(symbol: &str, state_dir: &str) -> Value {
    let recommended_next_step = format!(
        "ict-engine factor-autoresearch --symbol {} --state-dir {}",
        shell_quote(symbol),
        shell_quote(state_dir)
    );
    json!({
        "symbol": symbol,
        "state_dir": state_dir,
        "status": "no_autoresearch_state",
        "live_snapshot": Value::Null,
        "sessions": [],
        "attempts": [],
        "final_summary_exists": false,
        "recommended_next_step": recommended_next_step,
    })
}

const NO_WORKFLOW_STATE: &str = "no_workflow_state";
const NO_WORKFLOW_PHASE_SUMMARY: &str = "No workflow phase summary available yet.";
const WORKFLOW_STATUS_FOCUS_PHASE: &str = "workflow_status";

fn workflow_status_empty_state(snapshot: &WorkflowSnapshot) -> bool {
    snapshot.latest_update.is_none()
        && snapshot.latest_research.is_none()
        && snapshot.latest_analyze.is_none()
        && snapshot.latest_backtest.is_none()
        && snapshot.latest_train.is_none()
}

fn workflow_status_focus_phase(snapshot: &WorkflowSnapshot) -> String {
    if snapshot.current_focus_phase.trim().is_empty() {
        WORKFLOW_STATUS_FOCUS_PHASE.to_string()
    } else {
        snapshot.current_focus_phase.clone()
    }
}

pub fn humanize_workflow_command(command: &str) -> String {
    let trimmed = command.trim();
    if trimmed.is_empty()
        || trimmed == "recommended_command_unavailable"
        || trimmed == "next_command_unavailable"
    {
        return "No actionable command available.".to_string();
    }
    if let Some(rest) = trimmed.strip_prefix("ask-user: ") {
        let mut parts = rest.split(" | blocked until user_selected_historical_data | then ");
        let ask = parts.next().unwrap_or("").trim();
        let then = parts.next().unwrap_or("").trim();
        if then.is_empty() || then == "choose historical dataset with user before running command" {
            return format!("Ask the user to choose the historical dataset. {}", ask);
        }
        return format!(
            "Ask the user to choose the historical dataset. {} Then run: {}",
            ask, then
        );
    }
    if trimmed.starts_with("blocked:") {
        return format!("Blocked: {}", trimmed.trim_start_matches("blocked:").trim());
    }
    format!("Next step: {}", trimmed)
}

fn workflow_human_deferred_command(command: &str) -> Option<String> {
    let trimmed = command.trim();
    if trimmed.is_empty()
        || trimmed == "recommended_command_unavailable"
        || trimmed == "next_command_unavailable"
    {
        return None;
    }
    if let Some(rest) = trimmed.strip_prefix("ask-user: ") {
        return rest
            .split(" | then ")
            .nth(1)
            .map(str::trim)
            .filter(|value| {
                !value.is_empty()
                    && *value != "choose historical dataset with user before running command"
            })
            .map(str::to_string);
    }
    if trimmed.starts_with("blocked:") {
        return None;
    }
    Some(trimmed.to_string())
}

pub fn executor_scorecard_surface(
    persisted_scorecards: &[EnsembleExecutorScorecard],
    fallback_scorecards: &[EnsembleExecutorScorecard],
) -> (Vec<EnsembleExecutorScorecard>, &'static str) {
    if persisted_scorecards.is_empty() {
        (fallback_scorecards.to_vec(), "fallback")
    } else {
        (persisted_scorecards.to_vec(), "persisted")
    }
}

pub fn resolved_vote_scorecards(
    persisted_scorecards: &[EnsembleExecutorScorecard],
    vote: &EnsembleVoteRecord,
) -> (Vec<EnsembleExecutorScorecard>, &'static str) {
    executor_scorecard_surface(persisted_scorecards, &vote.executor_scorecards)
}

fn push_paths_from_command_text(candidates: &mut Vec<String>, command: &str) {
    let tokens = command
        .split(|ch: char| ch.is_whitespace() || ch == ',' || ch == '|' || ch == ';')
        .map(|token| token.trim_matches(|ch| ch == '\'' || ch == '"'));
    for token in tokens {
        if (token.starts_with('/') || token.starts_with("./") || token.starts_with("../"))
            && (token.ends_with(".json") || token.ends_with(".csv"))
            && !candidates.iter().any(|existing| existing == token)
        {
            candidates.push(token.to_string());
        }
    }
}

fn historical_data_candidates(snapshot: &WorkflowSnapshot) -> Vec<String> {
    let mut candidates = Vec::new();
    if let Some(update) = &snapshot.latest_update {
        for line in &update.multi_timeframe_summary {
            if let Some(path) = line.split("path=").nth(1) {
                push_paths_from_command_text(&mut candidates, path);
                let trimmed = path.trim();
                if !trimmed.is_empty() && !candidates.iter().any(|existing| existing == trimmed) {
                    candidates.push(trimmed.to_string());
                }
            }
        }
    }

    push_paths_from_command_text(&mut candidates, &snapshot.blocking_truth.next_command);
    push_paths_from_command_text(&mut candidates, &snapshot.recommended_next_command);
    for phase in [
        snapshot.latest_update.as_ref(),
        snapshot.latest_research.as_ref(),
        snapshot.latest_analyze.as_ref(),
        snapshot.latest_backtest.as_ref(),
        snapshot.latest_train.as_ref(),
    ]
    .into_iter()
    .flatten()
    {
        push_paths_from_command_text(&mut candidates, &phase.recommended_next_command);
    }

    candidates.sort();
    candidates.dedup();
    candidates
}

fn latest_workflow_phase(
    snapshot: &WorkflowSnapshot,
) -> Option<&crate::state::WorkflowPhaseSnapshot> {
    [
        snapshot.latest_update.as_ref(),
        snapshot.latest_research.as_ref(),
        snapshot.latest_analyze.as_ref(),
        snapshot.latest_backtest.as_ref(),
        snapshot.latest_train.as_ref(),
    ]
    .into_iter()
    .flatten()
    .max_by(|left, right| left.timestamp.cmp(&right.timestamp))
}

pub fn build_human_workflow_status_view(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
) -> Value {
    let provider_status_agent = provider_status_agent_surface(None, None, None).unwrap_or_default();
    build_human_workflow_status_view_with_provider_agent_and_structural_prior_state(
        snapshot,
        persisted_scorecards,
        &provider_status_agent,
        &[],
        &StructuralPriorLearningState::default(),
    )
}

fn build_human_workflow_status_view_with_provider_agent(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
) -> Value {
    build_human_workflow_status_view_with_provider_agent_and_structural_prior_state(
        snapshot,
        persisted_scorecards,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

fn build_human_workflow_status_view_with_provider_agent_and_structural_prior_state(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Value {
    let no_workflow_state = workflow_status_empty_state(snapshot);
    let latest_phase = latest_workflow_phase(snapshot);
    let latest_phase_label = latest_phase
        .map(|phase| phase.phase.clone())
        .unwrap_or_else(|| NO_WORKFLOW_STATE.to_string());
    let latest_phase_summary = latest_phase
        .map(|phase| phase.phase_summary.clone())
        .unwrap_or_else(|| NO_WORKFLOW_PHASE_SUMMARY.to_string());
    let latest_pda_cluster = latest_phase
        .and_then(|phase| phase.pda_cluster_label.clone())
        .unwrap_or_else(|| "unavailable".to_string());
    let latest_duration_model = latest_phase
        .and_then(|phase| phase.hybrid_duration_model.clone())
        .unwrap_or_else(|| "unavailable".to_string());
    let latest_remaining_bars = latest_phase
        .and_then(|phase| phase.hybrid_remaining_expected_bars)
        .map(|value| format!("{value:.2}"))
        .unwrap_or_else(|| "unavailable".to_string());
    // Round 2 §3.4: surface spectral / sparsity / segment gate on the main
    // summary line so operators can spot a chaotic-regime or sparsity-collapse
    // without hunting through artifact files.
    let latest_spectral_entropy = latest_phase
        .and_then(|phase| phase.spectral_entropy)
        .map(|value| format!("{value:.3}"))
        .unwrap_or_else(|| "unavailable".to_string());
    let latest_sparsity_ratio = latest_phase
        .and_then(|phase| phase.sparsity_ratio)
        .map(|value| format!("{value:.3}"))
        .unwrap_or_else(|| "unavailable".to_string());
    let latest_segments_gate = latest_phase
        .and_then(|phase| phase.segments_gate.clone())
        .unwrap_or_else(|| "unavailable".to_string());
    let latest_phase_summary_short = latest_phase
        .map(short_human_phase_summary)
        .unwrap_or_else(|| NO_WORKFLOW_PHASE_SUMMARY.to_string());
    let selected_data_candidates = historical_data_candidates(snapshot);
    let hard_block_statuses = [
        "blocked",
        "bridge_needs_confirmation",
        "validated_regressing",
        "credibility_gate_blocked",
    ];
    let hard_block_active = hard_block_statuses
        .iter()
        .any(|status| snapshot.blocking_truth.status == *status);
    let top_level_command = if hard_block_active {
        snapshot.blocking_truth.next_command.clone()
    } else {
        snapshot.recommended_next_command.clone()
    };
    let provider_status_command = "ict-engine provider-status --agent".to_string();
    let historical_data_gate_active = !selected_data_candidates.is_empty()
        && (top_level_command.contains("factor-research")
            || top_level_command.contains("factor-backtest")
            || snapshot
                .recommended_next_command
                .contains("factor-research")
            || snapshot
                .recommended_next_command
                .contains("factor-backtest"));
    let historical_data_request_template = if !selected_data_candidates.is_empty() {
        format!(
            "Please choose one historical data path for the next research/backtest run: {}",
            selected_data_candidates.join(", ")
        )
    } else {
        String::new()
    };
    let user_path_input_prompt = if !selected_data_candidates.is_empty() {
        format!(
            "Reply with one path from the list, or paste another valid file path. Candidates: {}",
            selected_data_candidates.join(", ")
        )
    } else {
        "Reply with a historical data file path to continue research/backtest.".to_string()
    };
    let user_selection_pending = historical_data_gate_active
        || top_level_command.contains("user_selected_historical_data")
        || snapshot
            .blocking_truth
            .reason
            .contains("user_selected_historical_data_missing");
    let deferred_user_selection_command = workflow_human_deferred_command(&top_level_command);
    let base_human_next_action = if user_selection_pending {
        if !historical_data_request_template.is_empty() {
            match deferred_user_selection_command.as_deref() {
                Some(command) => format!(
                    "Ask the user to choose the historical dataset. {} {} Then run: {}",
                    historical_data_request_template, user_path_input_prompt, command
                ),
                None => format!(
                    "Ask the user to choose the historical dataset. {} {}",
                    historical_data_request_template, user_path_input_prompt
                ),
            }
        } else {
            match deferred_user_selection_command.as_deref() {
                Some(command) => format!(
                    "Ask the user to provide the historical data path before running research/backtest. Then run: {}",
                    command
                ),
                None => {
                    "Ask the user to provide the historical data path before running research/backtest."
                        .to_string()
                }
            }
        }
    } else {
        humanize_workflow_command(&top_level_command)
    };
    let action_status_label = if user_selection_pending {
        "action_blocked".to_string()
    } else if no_workflow_state {
        NO_WORKFLOW_STATE.to_string()
    } else if snapshot.blocking_truth.status.is_empty() {
        "unblocked".to_string()
    } else {
        snapshot.blocking_truth.status.clone()
    };
    let gate_reason_label = if user_selection_pending {
        "user_selected_historical_data_missing".to_string()
    } else if no_workflow_state {
        NO_WORKFLOW_STATE.to_string()
    } else if hard_block_active && !snapshot.blocking_truth.reason.is_empty() {
        snapshot.blocking_truth.reason.clone()
    } else {
        "none".to_string()
    };
    let provider_support_reason =
        if gate_reason_label != "none" && gate_reason_label != NO_WORKFLOW_STATE {
            Some(gate_reason_label.as_str())
        } else if !snapshot.current_focus_reason.is_empty() {
            Some(snapshot.current_focus_reason.as_str())
        } else {
            None
        };
    let provider_support = build_workflow_provider_support(
        provider_status_agent,
        &top_level_command,
        provider_support_reason,
    );
    let human_next_action = if provider_support.active {
        format!(
            "Resolve provider prerequisites for {} before continuing. {}",
            provider_support.pending_providers.join(", "),
            base_human_next_action
        )
    } else {
        base_human_next_action
    };
    let provider_line = if provider_support.active {
        let prompt_summary = provider_support
            .install_prompts
            .iter()
            .take(2)
            .cloned()
            .collect::<Vec<_>>()
            .join(" ");
        Some(format!(
            "Provider: {} pending. {} Check: {}",
            provider_support.pending_providers.join(", "),
            prompt_summary,
            provider_status_command
        ))
    } else {
        None
    };
    let mut summary_parts = vec![
        snapshot.symbol.clone(),
        workflow_status_focus_phase(snapshot),
        action_status_label.clone(),
    ];
    if latest_pda_cluster != "unavailable" {
        summary_parts.push(format!("pda_cluster={latest_pda_cluster}"));
    }
    if latest_duration_model != "unavailable" {
        summary_parts.push(format!("duration={latest_duration_model}"));
    }
    if latest_remaining_bars != "unavailable" {
        summary_parts.push(format!("remaining_bars={latest_remaining_bars}"));
    }
    if latest_spectral_entropy != "unavailable" {
        summary_parts.push(format!("spectral_entropy={latest_spectral_entropy}"));
    }
    if latest_sparsity_ratio != "unavailable" {
        summary_parts.push(format!("sparsity={latest_sparsity_ratio}"));
    }
    if latest_segments_gate != "unavailable" {
        summary_parts.push(format!("segments_gate={latest_segments_gate}"));
    }
    let summary_line = summary_parts.join(" | ");
    let blocking_line = format!("Block: {}", gate_reason_label);
    let next_action_display = human_next_action
        .strip_prefix("Next step: ")
        .unwrap_or(&human_next_action);
    let next_action_line = format!("Next: {}", next_action_display);
    let phase_summary_line = format!(
        "Latest: {} | {}",
        latest_phase_label, latest_phase_summary_short
    );
    let structural_feedback_line = snapshot
        .latest_update
        .as_ref()
        .and_then(|phase| phase.structural_feedback.as_ref())
        .map(|feedback| {
            format!(
                "Feedback: recommendation={} path={} followed={} exit={}",
                feedback.recommendation_id,
                feedback.path_id,
                feedback.followed_path,
                feedback
                    .exit_reason
                    .clone()
                    .unwrap_or_else(|| "unreported".to_string())
            )
        });
    let structural_path_line = snapshot
        .latest_update
        .as_ref()
        .and_then(|phase| phase.structural_feedback.as_ref())
        .and_then(|feedback| {
            build_structural_path_history_artifact(snapshot, feedback_history)
                .paths
                .into_iter()
                .find(|path| path.path_id == feedback.path_id)
        })
        .map(|path| {
            format!(
                "Path: {} total={} wins={} losses={} invalidated={} avg_pnl={:.4}",
                path.path_id, path.total_records, path.wins, path.losses, path.invalidated, path.avg_pnl
            )
        });
    let structural_history_summary = build_structural_history_summary_artifact(snapshot, feedback_history);
    let experience_prior_surface = build_structural_experience_prior_surface_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let experience_prior_line = experience_prior_surface.path.as_ref().map(|path| {
        format!(
            "Experience: path_prior={:.3} path_score={:.3} total={} wins={}",
            path.experience_prior,
            path.composite_score,
            path.historical_total_records,
            ((path.historical_win_rate.unwrap_or(0.0)
                * path.historical_followed_count as f64)
                .round()) as usize
        )
    });
    let top_path_candidates = build_structural_top_path_candidates_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let recommended_path_bundle = build_structural_recommended_path_bundle_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let execution_contract_active =
        !hard_block_active && !historical_data_gate_active && !provider_support.active;
    let top_path_candidates_line = if top_path_candidates.candidates.is_empty() {
        None
    } else {
        Some(format!(
            "Candidates: {}",
            top_path_candidates
                .candidates
                .iter()
                .take(2)
                .map(|candidate| format!(
                    "{} score={:.3} prior={:.3} post={:.3}",
                    candidate.path_label,
                    candidate.composite_score,
                    candidate.experience_prior,
                    candidate.current_posterior
                ))
                .collect::<Vec<_>>()
                .join(" | ")
        ))
    };
    let recommended_path_line = recommended_path_bundle.as_ref().map(|bundle| {
        format!(
            "Recommended: {} score={:.3} trigger={} stop={} invalidation={}",
            bundle.path_label,
            bundle.composite_score,
            bundle.trigger_summary,
            bundle.stop_summary,
            bundle.invalidation_summary
        )
    });
    let human_next_action = if execution_contract_active {
        match recommended_path_bundle.as_ref() {
            Some(bundle) => format!(
                "{} Execution contract: path={} trigger={} stop={} invalidation={} why={}",
                human_next_action,
                bundle.path_label,
                bundle.trigger_summary,
                bundle.stop_summary,
                bundle.invalidation_summary,
                bundle.why_this_path
            ),
            None => human_next_action,
        }
    } else {
        human_next_action
    };
    let recommended_path_contract_line = recommended_path_bundle.as_ref().map(|bundle| {
        format!(
            "Contract: path={} trigger={} stop={} invalidation={} why={}",
            bundle.path_label,
            bundle.trigger_summary,
            bundle.stop_summary,
            bundle.invalidation_summary,
            bundle.why_this_path
        )
    });
    let recommended_path_contract =
        workflow_status_recommended_path_contract_value(recommended_path_bundle.as_ref());
    let recommended_next_step = workflow_status_next_step_with_execution_contract(
        &top_level_command,
        if hard_block_active || historical_data_gate_active {
            Some(gate_reason_label.as_str())
        } else {
            None
        },
        if execution_contract_active {
            recommended_path_contract.clone()
        } else {
            None
        },
    );
    let structural_history_line = if structural_history_summary.total_records > 0 {
        Some(format!(
            "History: nodes={} branches={} scenarios={} paths={} latest_path={}",
            structural_history_summary.distinct_nodes,
            structural_history_summary.distinct_branches,
            structural_history_summary.distinct_scenarios,
            structural_history_summary.distinct_paths,
            structural_history_summary
                .latest_path_id
                .clone()
                .unwrap_or_else(|| "unknown".to_string())
        ))
    } else {
        None
    };
    let credibility_risks = snapshot
        .risk_flags
        .iter()
        .filter(|flag| {
            flag.contains("conformal_coverage_low")
                || flag.contains("regime_break_penalty_high")
                || flag.contains("structural_break_detected")
                || flag.contains("conformal_credibility")
        })
        .cloned()
        .collect::<Vec<_>>();
    let ensemble_summary = resolved_latest_ensemble_vote(snapshot).as_ref().map(|vote| {
        let surface = build_ensemble_vote_surface(vote, persisted_scorecards);
        serde_json::to_value(surface).unwrap_or_default()
    });
    let agent_fill_path_instructions = if selected_data_candidates.is_empty() {
        Vec::new()
    } else {
        selected_data_candidates
            .iter()
            .map(|path| {
                format!(
                    "Ask user to confirm --data {} before running factor-research/factor-backtest.",
                    path
                )
            })
            .collect::<Vec<_>>()
    };
    let mut value = serde_json::json!({
        "status": if no_workflow_state {
            serde_json::Value::String(NO_WORKFLOW_STATE.to_string())
        } else {
            serde_json::Value::Null
        },
        "summary_line": summary_line,
        "blocking_line": blocking_line,
        "next_action_line": next_action_line,
        "provider_line": provider_line,
        "structural_feedback_line": structural_feedback_line,
        "structural_path_line": structural_path_line,
        "experience_prior_line": experience_prior_line,
        "top_path_candidates_line": top_path_candidates_line,
        "structural_history_line": structural_history_line,
        "phase_summary_line": phase_summary_line,
        "symbol": snapshot.symbol,
        "pda_cluster_label": if latest_pda_cluster == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_pda_cluster.clone())
        },
        "hybrid_duration_model": if latest_duration_model == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_duration_model.clone())
        },
        "hybrid_remaining_expected_bars": if latest_remaining_bars == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_remaining_bars.clone())
        },
        "spectral_entropy": if latest_spectral_entropy == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_spectral_entropy.clone())
        },
        "sparsity_ratio": if latest_sparsity_ratio == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_sparsity_ratio.clone())
        },
        "segments_gate": if latest_segments_gate == "unavailable" {
            serde_json::Value::Null
        } else {
            serde_json::Value::String(latest_segments_gate.clone())
        },
        "current_status": {
            "focus_phase": workflow_status_focus_phase(snapshot),
            "focus_reason": snapshot.current_focus_reason,
            "blocking_stage": if historical_data_gate_active {
                workflow_status_focus_phase(snapshot)
            } else {
                snapshot.blocking_truth.stage.clone()
            },
            "blocking_status": action_status_label,
            "blocking_reason": gate_reason_label,
            "hard_block_active": hard_block_active || historical_data_gate_active,
            "top_level_command_source": if historical_data_gate_active {
                "historical_data_selection_gate"
            } else if hard_block_active {
                "blocking_truth"
            } else {
                "recommended_next_command"
            },
        },
        "hard_block": if hard_block_active || historical_data_gate_active {
            serde_json::json!({
                "active": true,
                "stage": if historical_data_gate_active {
                    snapshot.current_focus_phase.clone()
                } else {
                    snapshot.blocking_truth.stage.clone()
                },
                "status": action_status_label,
                "reason": gate_reason_label,
                "evidence": if historical_data_gate_active {
                    Vec::<String>::new()
                } else {
                    snapshot.blocking_truth.evidence.clone()
                },
                "command": if hard_block_active {
                    serde_json::Value::String(snapshot.blocking_truth.next_command.clone())
                } else {
                    serde_json::Value::Null
                },
                "human_action": human_next_action,
            })
        } else {
            serde_json::json!({
                "active": false,
                "stage": serde_json::Value::Null,
                "status": serde_json::Value::Null,
                "reason": serde_json::Value::Null,
                "evidence": Vec::<String>::new(),
                "command": serde_json::Value::Null,
                "human_action": serde_json::Value::Null,
            })
        },
        "what_you_should_do_now": human_next_action,
        "what_you_should_do_now_source": if historical_data_gate_active {
            "historical_data_selection_gate"
        } else if hard_block_active {
            "blocking_truth"
        } else {
            "recommended_next_command"
        },
        "latest_stage": {
            "phase": latest_phase_label,
            "summary": latest_phase_summary,
            "summary_short": latest_phase_summary_short,
        },
        "ensemble_consensus": ensemble_summary,
        "credibility_risks": credibility_risks,
        "pending_actions": snapshot.pending_actions,
        "risk_flags": snapshot.risk_flags,
        "historical_data_candidates": selected_data_candidates,
        "historical_data_request_template": historical_data_request_template,
        "user_path_input_prompt": user_path_input_prompt,
        "agent_fill_path_instructions": agent_fill_path_instructions,
        "jump_model": jump_model_workflow_summary(snapshot),
        "jump_calibration_gate": jump_calibration_gate_workflow_summary(snapshot),
        "latest_structural_feedback": snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.clone()),
        "structural_history_summary": structural_history_summary,
        "structural_path_summary": snapshot
            .latest_update
            .as_ref()
            .and_then(|phase| phase.structural_feedback.as_ref())
            .and_then(|feedback| {
                build_structural_path_history_artifact(snapshot, feedback_history)
                    .paths
                    .into_iter()
                    .find(|path| path.path_id == feedback.path_id)
            }),
        "jump_disagreement": snapshot
            .latest_ensemble_vote
            .as_ref()
            .and_then(|vote| {
                vote.executor_summaries
                    .iter()
                    .find(|line| line.contains("jump_disagreement"))
                    .cloned()
            }),
        "provider_support": {
            "command": provider_status_command,
            "agent_summary": provider_status_agent,
            "workflow_support": provider_support,
        },
    });
    if let Value::Object(map) = &mut value {
        map.insert(
            "recommended_path_line".to_string(),
            serde_json::to_value(recommended_path_line).unwrap_or_default(),
        );
        map.insert(
            "recommended_path_contract_line".to_string(),
            serde_json::to_value(recommended_path_contract_line).unwrap_or_default(),
        );
        map.insert(
            "recommended_next_step".to_string(),
            recommended_next_step,
        );
    }
    value
}

pub fn build_compact_workflow_status_view(snapshot: &WorkflowSnapshot) -> Value {
    let blocking_status = if snapshot.blocking_truth.status.is_empty() {
        "unblocked".to_string()
    } else {
        snapshot.blocking_truth.status.clone()
    };
    let blocking_reason = if snapshot.blocking_truth.status.is_empty() {
        "none".to_string()
    } else {
        snapshot.blocking_truth.reason.clone()
    };
    let latest_phase = latest_workflow_phase(snapshot);
    let latest_phase_label = latest_phase
        .map(|phase| phase.phase.clone())
        .unwrap_or_else(|| "workflow_phase_unavailable".to_string());
    let latest_phase_summary = latest_phase
        .map(short_workflow_phase_summary)
        .unwrap_or_else(|| "workflow_phase_summary_unavailable".to_string());
    let top_actionable = snapshot.actionable_artifacts.first().map(|artifact| {
        serde_json::json!({
            "artifact_id": artifact.artifact_id,
            "artifact_kind": artifact.artifact_kind,
            "decision_hint": artifact.decision_hint,
            "generated_at": artifact.generated_at,
        })
    });
    let top_disagreement = snapshot.disagreements.first().map(|item| {
        serde_json::json!({
            "id": item.id,
            "severity": item.severity,
            "summary": item.summary,
        })
    });
    serde_json::json!({
        "symbol": snapshot.symbol,
        "generated_at": snapshot.generated_at,
        "focus_phase": snapshot.current_focus_phase,
        "focus_reason": snapshot.current_focus_reason,
        "latest_phase": latest_phase_label,
        "latest_phase_summary": latest_phase_summary,
        "blocking_status": blocking_status,
        "blocking_reason": blocking_reason,
        "next_command": snapshot.recommended_next_command,
        "pda_cluster_label": latest_phase.and_then(|phase| phase.pda_cluster_label.clone()),
        "pending_actions": snapshot.pending_actions.iter().take(3).cloned().collect::<Vec<_>>(),
        "risk_flags": snapshot.risk_flags.iter().take(3).cloned().collect::<Vec<_>>(),
        "top_actionable": top_actionable,
        "top_disagreement": top_disagreement,
    })
}

pub fn build_agent_workflow_status_view(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
) -> Value {
    let provider_status_agent = provider_status_agent_surface(None, None, None).unwrap_or_default();
    build_agent_workflow_status_view_with_provider_agent_and_structural_prior_state(
        snapshot,
        persisted_scorecards,
        &provider_status_agent,
        &[],
        &StructuralPriorLearningState::default(),
    )
}

#[cfg(test)]
fn build_agent_workflow_status_view_with_provider_agent(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
) -> Value {
    build_agent_workflow_status_view_with_provider_agent_and_structural_prior_state(
        snapshot,
        persisted_scorecards,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
    )
}

fn build_agent_workflow_status_view_with_provider_agent_and_structural_prior_state(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Value {
    let no_workflow_state = workflow_status_empty_state(snapshot);
    let latest_phase = latest_workflow_phase(snapshot);
    let latest_phase_label = latest_phase
        .map(|phase| phase.phase.clone())
        .unwrap_or_else(|| NO_WORKFLOW_STATE.to_string());
    let latest_phase_summary_short = latest_phase
        .map(short_workflow_phase_summary)
        .unwrap_or_else(|| NO_WORKFLOW_PHASE_SUMMARY.to_string());
    let hard_block_statuses = [
        "blocked",
        "bridge_needs_confirmation",
        "validated_regressing",
        "credibility_gate_blocked",
    ];
    let hard_block_active = hard_block_statuses
        .iter()
        .any(|status| snapshot.blocking_truth.status == *status);
    let command_source = if hard_block_active {
        "blocking_truth"
    } else {
        "recommended_next_command"
    };
    let next_command = if hard_block_active {
        snapshot.blocking_truth.next_command.clone()
    } else {
        snapshot.recommended_next_command.clone()
    };
    let next_command_value = if no_workflow_state && next_command.trim().is_empty() {
        serde_json::Value::Null
    } else {
        serde_json::Value::String(next_command.clone())
    };
    let blocking_status = if hard_block_active {
        snapshot.blocking_truth.status.clone()
    } else if no_workflow_state {
        NO_WORKFLOW_STATE.to_string()
    } else {
        "unblocked".to_string()
    };
    let blocking_reason = if hard_block_active {
        snapshot.blocking_truth.reason.clone()
    } else if no_workflow_state {
        NO_WORKFLOW_STATE.to_string()
    } else {
        "none".to_string()
    };
    let top_disagreement = snapshot.disagreements.first().map(|item| {
        serde_json::json!({
            "id": item.id,
            "severity": item.severity,
            "summary": item.summary,
            "recommended_action": item.recommended_action,
        })
    });
    let top_actionable = snapshot.actionable_artifacts.first().map(|artifact| {
        serde_json::json!({
            "artifact_id": artifact.artifact_id,
            "artifact_kind": artifact.artifact_kind,
            "decision_hint": artifact.decision_hint,
        })
    });
    let ensemble_summary = resolved_latest_ensemble_vote(snapshot).as_ref().map(|vote| {
        let (scorecards, scorecard_source) = resolved_vote_scorecards(persisted_scorecards, vote);
        serde_json::json!({
            "final_action": vote.final_action,
            "confidence": vote.confidence,
            "consensus_strength": vote.consensus_strength,
            "hard_block_active": vote.hard_block.active,
            "hard_block_reason": vote.hard_block.reason,
            "recommended_command": vote.recommended_command,
            "executor_scorecard_source": scorecard_source,
            "top_executor": scorecards.first().map(|item| {
                serde_json::json!({
                    "executor": item.executor,
                    "latest_weight_hint": item.latest_weight_hint,
                    "wins": item.wins,
                })
            }),
        })
    });
    let provider_support_reason =
        if blocking_reason != "none" && blocking_reason != NO_WORKFLOW_STATE {
            Some(blocking_reason.as_str())
        } else if !snapshot.current_focus_reason.is_empty() {
            Some(snapshot.current_focus_reason.as_str())
        } else {
            None
        };
    let provider_support = build_workflow_provider_support(
        provider_status_agent,
        &next_command,
        provider_support_reason,
    );
    let execution_contract_active = !hard_block_active && !provider_support.active;
    let latest_structural_feedback = snapshot
        .latest_update
        .as_ref()
        .and_then(|phase| phase.structural_feedback.clone());
    let structural_path_summary = snapshot
        .latest_update
        .as_ref()
        .and_then(|phase| phase.structural_feedback.as_ref())
        .and_then(|feedback| {
            build_structural_path_history_artifact(snapshot, feedback_history)
                .paths
                .into_iter()
                .find(|path| path.path_id == feedback.path_id)
        });
    let structural_history_summary = build_structural_history_summary_artifact(snapshot, feedback_history);
    let experience_prior_surface = build_structural_experience_prior_surface_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let top_path_candidates = build_structural_top_path_candidates_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let recommended_path_bundle = build_structural_recommended_path_bundle_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let recommended_path_contract =
        workflow_status_recommended_path_contract_value(recommended_path_bundle.as_ref());
    let next_step = workflow_status_next_step_with_execution_contract(
        &next_command,
        if hard_block_active {
            Some(blocking_reason.as_str())
        } else {
            None
        },
        if execution_contract_active {
            recommended_path_contract.clone()
        } else {
            None
        },
    );
    let mut value = serde_json::json!({
        "status": if no_workflow_state {
            serde_json::Value::String(NO_WORKFLOW_STATE.to_string())
        } else {
            serde_json::Value::Null
        },
        "symbol": snapshot.symbol,
        "generated_at": snapshot.generated_at,
        "focus_phase": workflow_status_focus_phase(snapshot),
        "focus_reason": snapshot.current_focus_reason,
        "latest_phase": latest_phase_label,
        "latest_phase_summary": latest_phase_summary_short,
        "blocking_status": blocking_status,
        "blocking_reason": blocking_reason,
        "hard_block_active": hard_block_active,
        "next_command": next_command_value,
        "next_command_source": command_source,
        "pda_cluster_label": latest_phase.and_then(|phase| phase.pda_cluster_label.clone()),
        "hybrid_duration_model": latest_phase.and_then(|phase| phase.hybrid_duration_model.clone()),
        "hybrid_remaining_expected_bars": latest_phase.and_then(|phase| phase.hybrid_remaining_expected_bars),
        "next_step": next_step,
        "pending_actions": snapshot.pending_actions.iter().take(3).cloned().collect::<Vec<_>>(),
        "risk_flags": snapshot.risk_flags.iter().take(3).cloned().collect::<Vec<_>>(),
        "top_disagreement": top_disagreement,
        "top_actionable": top_actionable,
        "ensemble": ensemble_summary,
        "provider_support": provider_support,
        "latest_structural_feedback": latest_structural_feedback,
        "experience_prior_surface": experience_prior_surface,
        "top_path_candidates": top_path_candidates.candidates,
        "structural_history_summary": structural_history_summary,
        "structural_path_summary": structural_path_summary,
    });
    if let Value::Object(map) = &mut value {
        map.insert(
            "recommended_path_bundle".to_string(),
            serde_json::to_value(recommended_path_bundle).unwrap_or_default(),
        );
        map.insert(
            "recommended_path_contract".to_string(),
            serde_json::to_value(recommended_path_contract).unwrap_or_default(),
        );
        map.insert("recommended_next_step".to_string(), next_step.clone());
    }
    value
}

fn normalize_workflow_status_value_for_stability(value: &mut Value) {
    match value {
        Value::Object(map) => {
            for key in [
                "generated_at",
                "timestamp",
                "updated_at",
                "last_updated_at",
                "fetched_at",
            ] {
                map.remove(key);
            }
            for child in map.values_mut() {
                normalize_workflow_status_value_for_stability(child);
            }
        }
        Value::Array(items) => {
            for item in items {
                normalize_workflow_status_value_for_stability(item);
            }
        }
        _ => {}
    }
}

pub fn emit_workflow_status_output(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    output_format: &str,
    stable: bool,
) -> Result<()> {
    match output_format.trim().to_ascii_lowercase().as_str() {
        "json" => {
            let mut value = serde_json::to_value(snapshot)?;
            if stable {
                normalize_workflow_status_value_for_stability(&mut value);
            }
            redact_local_paths_in_value(&mut value);
            println!("{}", serde_json::to_string_pretty(&value)?);
        }
        "compact" => {
            let mut value = build_compact_workflow_status_view(snapshot);
            if stable {
                normalize_workflow_status_value_for_stability(&mut value);
            }
            redact_local_paths_in_value(&mut value);
            println!("{}", serde_json::to_string_pretty(&value)?);
        }
        "agent" => {
            let mut value =
                build_agent_workflow_status_view_with_provider_agent_and_structural_prior_state(
                snapshot,
                persisted_scorecards,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            if stable {
                normalize_workflow_status_value_for_stability(&mut value);
            }
            redact_local_paths_in_value(&mut value);
            println!("{}", serde_json::to_string_pretty(&value)?);
        }
        "human" => {
            let value =
                build_human_workflow_status_view_with_provider_agent_and_structural_prior_state(
                snapshot,
                persisted_scorecards,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            if let Some(summary) = value.get("summary_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(summary));
            }
            if let Some(blocking) = value.get("blocking_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(blocking));
            }
            if let Some(latest) = value.get("phase_summary_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(latest));
            }
            if let Some(next) = value.get("next_action_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(next));
            }
            if let Some(provider) = value.get("provider_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(provider));
            }
            if let Some(feedback) = value
                .get("structural_feedback_line")
                .and_then(Value::as_str)
            {
                println!("{}", redact_local_paths_in_human_text(feedback));
            }
            if let Some(path) = value.get("structural_path_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(path));
            }
            if let Some(history) = value.get("structural_history_line").and_then(Value::as_str) {
                println!("{}", redact_local_paths_in_human_text(history));
            }
        }
        other => anyhow::bail!("unsupported output format '{}'", other),
    }
    Ok(())
}

pub fn dispatch_workflow_status(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    input: WorkflowStatusDispatchInput<'_>,
    bootstrap: WorkflowStatusBootstrapInput<'_>,
) -> Result<()> {
    let filter_count = input.actionable_only as u8
        + input.conflicts_only as u8
        + input.latest_promotable as u8
        + input.hard_block_only as u8
        + input.hard_block_reason.is_some() as u8
        + input.limit.is_some() as u8;
    if input.phase.is_some() && filter_count > 0 {
        anyhow::bail!("workflow-status phase and filter flags are mutually exclusive");
    }
    if input.actionable_only as u8 + input.conflicts_only as u8 + input.latest_promotable as u8 > 1
    {
        anyhow::bail!("workflow-status accepts at most one artifact filter flag");
    }
    if input.actionable_only {
        print_redacted_json(&snapshot.actionable_artifacts)?;
        return Ok(());
    }
    if input.conflicts_only {
        print_redacted_json(&snapshot.disagreements)?;
        return Ok(());
    }
    if input.latest_promotable {
        print_redacted_json(&snapshot.latest_promotable_artifact)?;
        return Ok(());
    }
    if input.hard_block_only || input.hard_block_reason.is_some() || input.limit.is_some() {
        let history = filter_hard_block_rows(
            snapshot,
            persisted_scorecards,
            input.hard_block_only,
            input.hard_block_reason,
            input.limit,
        );
        let mut value = serde_json::to_value(history)?;
        if input.stable {
            normalize_workflow_status_value_for_stability(&mut value);
        }
        redact_local_paths_in_value(&mut value);
        println!("{}", serde_json::to_string_pretty(&value)?);
        return Ok(());
    }
    if let Some(phase) = input.phase {
        let phase_key = phase.trim().to_ascii_lowercase();
        let mut value = match phase_key.as_str() {
            "agent-bootstrap" | "bootstrap" => build_workflow_status_bootstrap_phase_value(
                bootstrap.symbol,
                bootstrap.state_dir,
                snapshot,
                provider_status_agent,
                bootstrap.detected_tomac_root,
                bootstrap.multi_timeframe_clean_root,
                &bootstrap.tomac_root_placeholder,
            )?,
            other => build_workflow_status_phase_value_with_structural_prior_state(
                snapshot,
                persisted_scorecards,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
                other,
            )?,
        };
        if input.stable {
            normalize_workflow_status_value_for_stability(&mut value);
        }
        if phase_key != "agent-bootstrap" && phase_key != "bootstrap" {
            redact_local_paths_in_value(&mut value);
        }
        println!("{}", serde_json::to_string_pretty(&value)?);
    } else {
        emit_workflow_status_output(
            snapshot,
            persisted_scorecards,
            provider_status_agent,
            feedback_history,
            structural_prior_state,
            input.output_format,
            input.stable,
        )?;
    }
    Ok(())
}

fn build_agent_bootstrap_view(input: AgentBootstrapBuildInput<'_>) -> AgentBootstrapView {
    build_agent_bootstrap_view_with_candidates(input, build_ibkr_gateway_candidates())
}

fn build_agent_bootstrap_view_with_candidates(
    input: AgentBootstrapBuildInput<'_>,
    ibkr_gateway_candidates: Vec<AgentBootstrapIbkrGatewayCandidate>,
) -> AgentBootstrapView {
    let AgentBootstrapBuildInput {
        symbol,
        state_dir,
        snapshot,
        provider_status_agent,
        detected_tomac_root,
        multi_timeframe_clean_root,
        tomac_root_placeholder,
    } = input;
    let ibkr_gateway_summary = build_ibkr_gateway_summary(&ibkr_gateway_candidates);
    let provider_status_command = "ict-engine provider-status --agent".to_string();
    let agent_brief = vec![
        "mission: formalize factor-pipeline debug from latest signal through pre-bayes / bridge / resonance".to_string(),
        "priority: promote expansion_manipulation to SOP-tier objective, not research-only".to_string(),
        "guardrail: do not blind-tune structure_ict before evidence pinpoints the blocking surface".to_string(),
        "success: either find a real structure_ict mutation win or prove near-local-optimum then shift to label refinement / market fork".to_string(),
        "live-provider prerequisite: if IBKR or TradingViewRemix MCP is needed, ask the user for local runtime/API access before attempting provider calls".to_string(),
    ];
    let analyze_command = if let Some(clean_root) = &multi_timeframe_clean_root {
        format!(
            "ict-engine analyze --symbol {} --data-root {} --state-dir {}",
            shell_quote(symbol),
            shell_quote(clean_root),
            shell_quote(state_dir)
        )
    } else {
        "ict-engine analyze --symbol <symbol> --data-root <clean-root> --state-dir <state-dir>"
            .to_string()
    };
    let train_command = if let Some(clean_root) = &multi_timeframe_clean_root {
        format!(
            "ict-engine train --symbol {} --data {}/cleaned-15m/{}.continuous-15m.json --epochs 200 --state-dir {}",
            shell_quote(symbol),
            shell_quote(clean_root),
            symbol.to_ascii_lowercase(),
            shell_quote(state_dir)
        )
    } else {
        "ict-engine train --symbol <symbol> --data <clean-root>/cleaned-15m/<market>.continuous-15m.json --epochs 200 --state-dir <state-dir>".to_string()
    };
    let clean_command = if let Some(root) = &detected_tomac_root {
        format!(
            "ict-engine clean-futures --root {} --output-dir {} --multi-timeframe",
            shell_quote(root),
            shell_quote(
                &multi_timeframe_clean_root
                    .clone()
                    .unwrap_or_else(|| format!("{}/ict-engine-mtf", root))
            )
        )
    } else {
        "ict-engine clean-futures --root <tomac-root> --output-dir <output-dir> --multi-timeframe"
            .to_string()
    };
    let inferable_live_defaults = std::collections::BTreeMap::new();
    AgentBootstrapView {
        symbol: symbol.to_string(),
        project_role: "closed_loop_multi_timeframe_pre_bayes_bbn_engine".to_string(),
        closed_loop_chain: vec![
            "tomac_history -> clean-futures".to_string(),
            "clean-futures -> train/research/backtest/analyze".to_string(),
            "analyze -> pre-bayes-filter -> bridge -> bbn".to_string(),
            "analyze -> pending/execution artifacts".to_string(),
            "artifacts -> update -> learning feedback".to_string(),
        ],
        agent_brief,
        guardrails: vec![
            "do_not_bypass_pre_bayes_evidence_filter".to_string(),
            "do_not_feed_raw_factor_labels_directly_into_bbn".to_string(),
            "treat_factors_as_evidence_not_triggers".to_string(),
            "keep_six_timeframe_resonance_in_train_analyze_bridge_artifact_update".to_string(),
        ],
        detected_paths: AgentBootstrapPaths {
            tomac_history_root: detected_tomac_root,
            multi_timeframe_clean_root: multi_timeframe_clean_root.clone(),
            state_dir: state_dir.to_string(),
        },
        input_acquisition: AgentBootstrapInputs {
            backtest: AgentBootstrapBacktestInput {
                local_discovery_order: vec![
                    "multi_timeframe_clean_root".to_string(),
                    "tomac_history_root".to_string(),
                    "direct_backtest_file".to_string(),
                ],
                preferred_user_inputs: vec![
                    "multi_timeframe_clean_root".to_string(),
                    "tomac_history_root".to_string(),
                ],
                fallback_user_inputs: vec![
                    "single_backtest_file_path".to_string(),
                    "download_link_to_backtest_file_or_directory".to_string(),
                ],
                should_ask_download_link_if_local_missing: true,
            },
            live: AgentBootstrapLiveInput {
                minimum_required_user_inputs: vec![],
                inferable_defaults: inferable_live_defaults,
                additional_user_inputs_if_not_inferable: vec![
                    "spot_symbol".to_string(),
                    "options_symbol".to_string(),
                    "spot_kind".to_string(),
                    "futures_backend".to_string(),
                    "aux_backend".to_string(),
                    "backend_base_urls_if_non_default".to_string(),
                ],
                provider_access_requests: provider_status_agent.install_prompts.clone(),
                provider_status_agent: provider_status_agent.clone(),
                provider_status_command,
                ibkr_gateway_summary,
                ibkr_gateway_candidates,
            },
        },
        commands: AgentBootstrapCommands {
            clean_multi_timeframe: clean_command,
            train: train_command,
            analyze: analyze_command,
            futures_sop: format!(
                "ict-engine futures-sop --root {} --output-dir {} --interval 15m",
                shell_quote(tomac_root_placeholder),
                shell_quote(
                    &multi_timeframe_clean_root
                        .clone()
                        .unwrap_or_else(|| "<output-dir>".to_string())
                )
            ),
            expansion_sop: format!(
                "ict-engine expansion-sop --root {} --output-dir {} --interval 15m --lookback 20 --atr-multiplier 1.50",
                shell_quote(tomac_root_placeholder),
                shell_quote(
                    &multi_timeframe_clean_root
                        .clone()
                        .unwrap_or_else(|| "<output-dir>".to_string())
                )
            ),
            workflow_status: format!(
                "ict-engine workflow-status --symbol {} --state-dir {}",
                shell_quote(symbol),
                shell_quote(state_dir)
            ),
            provider_status: "ict-engine provider-status --agent".to_string(),
            recommended_next_command: snapshot.recommended_next_command.clone(),
        },
        latest_snapshot: AgentBootstrapSnapshot {
            current_focus_phase: snapshot.current_focus_phase.clone(),
            current_focus_reason: snapshot.current_focus_reason.clone(),
            blocking_truth: snapshot.blocking_truth.clone(),
            latest_train_phase: snapshot.latest_train.as_ref().map(|phase| phase.phase.clone()),
            latest_analyze_phase: snapshot.latest_analyze.as_ref().map(|phase| phase.phase.clone()),
            latest_pre_bayes_gate_status: snapshot
                .latest_analyze
                .as_ref()
                .map(|phase| phase.pre_bayes_gate_status.clone()),
        },
    }
}

#[cfg(test)]
fn build_agent_bootstrap_view_with_probe<F>(
    input: AgentBootstrapBuildInput<'_>,
    probe: &F,
) -> AgentBootstrapView
where
    F: Fn(&str, u16) -> bool,
{
    build_agent_bootstrap_view_with_candidates(
        input,
        build_ibkr_gateway_candidates_with_probe("127.0.0.1", probe),
    )
}

fn build_ibkr_gateway_candidates() -> Vec<AgentBootstrapIbkrGatewayCandidate> {
    build_ibkr_gateway_candidates_with_probe("127.0.0.1", &|host, port| {
        let Ok(addr) = format!("{host}:{port}").parse::<SocketAddr>() else {
            return false;
        };
        TcpStream::connect_timeout(&addr, Duration::from_millis(150)).is_ok()
    })
}

fn build_ibkr_gateway_candidates_with_probe<F>(
    host: &str,
    probe: &F,
) -> Vec<AgentBootstrapIbkrGatewayCandidate>
where
    F: Fn(&str, u16) -> bool,
{
    let specs = [
        ("TWS paper", 7497u16),
        ("TWS live", 7496u16),
        ("IB Gateway paper", 4002u16),
        ("IB Gateway live", 4001u16),
    ];
    let recommended_port = specs
        .iter()
        .map(|(_, port)| *port)
        .find(|port| probe(host, *port));
    specs
        .into_iter()
        .map(|(label, port)| AgentBootstrapIbkrGatewayCandidate {
            label: label.to_string(),
            host: host.to_string(),
            port,
            reachable: probe(host, port),
            recommended: recommended_port == Some(port),
        })
        .collect()
}

fn build_ibkr_gateway_summary(
    candidates: &[AgentBootstrapIbkrGatewayCandidate],
) -> AgentBootstrapIbkrGatewaySummary {
    let reachable_candidate_count = candidates
        .iter()
        .filter(|candidate| candidate.reachable)
        .count();
    let preferred = candidates.iter().find(|candidate| candidate.recommended);
    let occupied_judgement = match reachable_candidate_count {
        0 => "no_reachable_candidate",
        1 => "single_reachable_candidate",
        _ => "multiple_reachable_candidates_choose_explicit_port",
    }
    .to_string();
    let recommended_action = match reachable_candidate_count {
        0 => "Ask the user to launch TWS or IB Gateway, then rerun setup/status or pass --gateway-port once the local API port is known.".to_string(),
        1 => format!(
            "Use the single reachable local IBKR runtime on port {} unless the user says otherwise.",
            preferred.map(|candidate| candidate.port).unwrap_or_default()
        ),
        _ => format!(
            "Multiple reachable local IBKR runtimes detected; ask the user which one to use and pass --gateway-port {} or the chosen alternative explicitly.",
            preferred.map(|candidate| candidate.port).unwrap_or_default()
        ),
    };
    AgentBootstrapIbkrGatewaySummary {
        preferred_label: preferred.map(|candidate| candidate.label.clone()),
        preferred_port: preferred.map(|candidate| candidate.port),
        reachable_candidate_count,
        occupied_judgement,
        recommended_action,
    }
}

fn short_human_phase_summary(phase: &crate::state::WorkflowPhaseSnapshot) -> String {
    let mut parts = Vec::new();
    if let Some(direction) = &phase.selected_direction {
        parts.push(format!("direction={direction}"));
    }
    if let Some(entry) = &phase.selected_entry_quality {
        parts.push(format!("entry={entry}"));
    }
    if !phase.pre_bayes_gate_status.is_empty()
        && phase.pre_bayes_gate_status != "pre_bayes_gate_unavailable"
    {
        parts.push(format!("gate={}", phase.pre_bayes_gate_status));
    }
    if phase.pre_bayes_evidence_quality_score > 0.0 {
        parts.push(format!(
            "quality={:.3}",
            phase.pre_bayes_evidence_quality_score
        ));
    }
    if parts.is_empty() {
        compact_human_phase_summary(phase).unwrap_or_else(|| phase.phase_summary.clone())
    } else {
        parts.join(" ")
    }
}

fn compact_human_phase_summary(phase: &crate::state::WorkflowPhaseSnapshot) -> Option<String> {
    let wanted_keys: &[&str] = match phase.phase.as_str() {
        "research" => &[
            "objective",
            "best_factor",
            "aggregate_return",
            "feedback_applied",
            "execution_gate",
        ],
        "backtest" => &[
            "total_return",
            "trade_count",
            "coverage_1sigma",
            "execution_gate",
        ],
        _ => return None,
    };
    let mut selected = Vec::new();
    for token in phase.phase_summary.split_whitespace() {
        if let Some((key, value)) = token.split_once('=') {
            if wanted_keys.contains(&key) {
                let normalized = if key == "best_factor" {
                    value
                        .strip_prefix("Some(\"")
                        .and_then(|item| item.strip_suffix("\")"))
                        .unwrap_or(value)
                        .to_string()
                } else {
                    value.to_string()
                };
                selected.push(format!("{key}={normalized}"));
            }
        }
    }
    if selected.is_empty() {
        None
    } else {
        Some(selected.join(" "))
    }
}

pub fn build_ensemble_vote_surface(
    vote: &EnsembleVoteRecord,
    persisted_scorecards: &[EnsembleExecutorScorecard],
) -> WorkflowEnsembleVoteSurface {
    let (scorecards, scorecard_source) = resolved_vote_scorecards(persisted_scorecards, vote);
    WorkflowEnsembleVoteSurface {
        artifact_id: vote.artifact_id.clone(),
        generated_at: vote.generated_at,
        symbol: vote.symbol.clone(),
        source_phase: vote.source_phase.clone(),
        source_run_id: vote.source_run_id.clone(),
        provenance: vote.provenance.clone(),
        dataset_comparability: vote.dataset_comparability.clone(),
        ensemble_version: vote.ensemble_version.clone(),
        final_action: vote.final_action.clone(),
        recommended_command: vote.recommended_command.clone(),
        human_next_triage: vote.human_next_triage.clone(),
        hard_block: vote.hard_block.clone(),
        confidence: vote.confidence,
        consensus_strength: vote.consensus_strength,
        disagreement_flags: vote.disagreement_flags.clone(),
        executor_summaries: vote.executor_summaries.clone(),
        split_explanations: vote.split_explanations.clone(),
        executor_scorecards: scorecards,
        executor_scorecard_source: scorecard_source.to_string(),
        posterior_fingerprint: vote.posterior_fingerprint.clone(),
        posterior_normalization_status: vote.posterior_normalization_status.clone(),
        posterior_active_regime: vote.posterior_active_regime.clone(),
        posterior_confidence: vote.posterior_confidence,
        posterior_probabilities: vote.posterior_probabilities.clone(),
        posterior_evidence: vote.posterior_evidence.clone(),
    }
}

fn workflow_status_recommended_path_contract_value(
    recommended_path_bundle: Option<&StructuralRecommendedPathBundleArtifact>,
) -> Option<Value> {
    recommended_path_bundle.map(|bundle| {
        serde_json::json!({
            "path_id": bundle.path_id,
            "path_label": bundle.path_label,
            "trigger": bundle.trigger_summary,
            "confirmation": bundle.confirmation_summary,
            "stop": bundle.stop_summary,
            "invalidation": bundle.invalidation_summary,
            "why": bundle.why_this_path,
            "recommended_command": bundle.recommended_command,
        })
    })
}

fn workflow_status_next_step_with_execution_contract(
    command: &str,
    blocked_reason: Option<&str>,
    execution_contract: Option<Value>,
) -> Value {
    let mut next_step = workflow_next_step_view(command, blocked_reason);
    if let Value::Object(map) = &mut next_step {
        map.insert(
            "execution_contract".to_string(),
            execution_contract.unwrap_or(Value::Null),
        );
    }
    next_step
}

fn workflow_status_value_with_recommended_next_step(
    mut value: Value,
    recommended_next_step: Value,
) -> Value {
    if let Value::Object(map) = &mut value {
        map.insert("recommended_next_step".to_string(), recommended_next_step);
    }
    value
}

fn workflow_status_structural_recommended_next_step(
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
) -> Value {
    let hard_block_active = matches!(
        snapshot.blocking_truth.status.as_str(),
        "blocked"
            | "bridge_needs_confirmation"
            | "validated_regressing"
            | "credibility_gate_blocked"
    );
    let top_level_command = if hard_block_active {
        snapshot.blocking_truth.next_command.clone()
    } else {
        snapshot.recommended_next_command.clone()
    };
    let selected_data_candidates = historical_data_candidates(snapshot);
    let historical_data_gate_active = !selected_data_candidates.is_empty()
        && (top_level_command.contains("factor-research")
            || top_level_command.contains("factor-backtest")
            || snapshot
                .recommended_next_command
                .contains("factor-research")
            || snapshot
                .recommended_next_command
                .contains("factor-backtest"));
    let provider_support_reason = if hard_block_active && !snapshot.blocking_truth.reason.is_empty()
    {
        Some(snapshot.blocking_truth.reason.as_str())
    } else if !snapshot.current_focus_reason.is_empty() {
        Some(snapshot.current_focus_reason.as_str())
    } else {
        None
    };
    let provider_support = build_workflow_provider_support(
        provider_status_agent,
        &top_level_command,
        provider_support_reason,
    );
    let recommended_path_bundle = build_structural_recommended_path_bundle_artifact_with_prior_state(
        snapshot,
        provider_status_agent,
        feedback_history,
        structural_prior_state,
    );
    let recommended_path_contract =
        workflow_status_recommended_path_contract_value(recommended_path_bundle.as_ref());
    workflow_status_next_step_with_execution_contract(
        &top_level_command,
        if hard_block_active || historical_data_gate_active {
            if hard_block_active && !snapshot.blocking_truth.reason.is_empty() {
                Some(snapshot.blocking_truth.reason.as_str())
            } else if historical_data_gate_active {
                Some("user_selected_historical_data_missing")
            } else {
                None
            }
        } else {
            None
        },
        if !hard_block_active && !historical_data_gate_active && !provider_support.active {
            recommended_path_contract
        } else {
            None
        },
    )
}

pub fn build_workflow_status_phase_value(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    phase: &str,
) -> Result<Value> {
    build_workflow_status_phase_value_with_structural_prior_state(
        snapshot,
        persisted_scorecards,
        provider_status_agent,
        feedback_history,
        &StructuralPriorLearningState::default(),
        phase,
    )
}

pub fn build_workflow_status_phase_value_with_structural_prior_state(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    provider_status_agent: &ProviderCatalogAgentSurface,
    feedback_history: &[crate::state::FeedbackRecord],
    structural_prior_state: &StructuralPriorLearningState,
    phase: &str,
) -> Result<Value> {
    Ok(match phase.trim().to_ascii_lowercase().as_str() {
        "human" | "human-next" | "human-next-action" => {
            build_human_workflow_status_view_with_provider_agent(
                snapshot,
                persisted_scorecards,
                provider_status_agent,
                feedback_history,
            )
        }
        "structural-playbook" => {
            let bundle = build_structural_playbook_bundle_with_prior_state(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            let recommended_next_step = workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(bundle)?,
                recommended_next_step,
            )
        }
        "structural-node" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_node_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                structural_prior_state,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-branch-set" | "structural-branches" => {
            let node = build_structural_node_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(build_structural_branch_set_artifact_with_prior_state(
                    snapshot,
                    provider_status_agent,
                    &node,
                    &build_structural_branch_history_artifact(snapshot, feedback_history),
                    structural_prior_state,
                ))?,
                workflow_status_structural_recommended_next_step(
                    snapshot,
                    provider_status_agent,
                    feedback_history,
                    structural_prior_state,
                ),
            )
        }
        "structural-scenario-playbook" | "structural-scenarios" => {
            let node = build_structural_node_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                structural_prior_state,
            );
            let branch_history = build_structural_branch_history_artifact(snapshot, feedback_history);
            let branch_set = build_structural_branch_set_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &node,
                &branch_history,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(build_structural_scenario_playbook_artifact_with_prior_state(
                    snapshot,
                    provider_status_agent,
                    &branch_set,
                    &build_structural_scenario_history_artifact(snapshot, feedback_history),
                    structural_prior_state,
                ))?,
                workflow_status_structural_recommended_next_step(
                    snapshot,
                    provider_status_agent,
                    feedback_history,
                    structural_prior_state,
                ),
            )
        }
        "structural-path-plan" | "structural-paths" => {
            let hard_block_active = matches!(
                snapshot.blocking_truth.status.as_str(),
                "blocked"
                    | "bridge_needs_confirmation"
                    | "validated_regressing"
                    | "credibility_gate_blocked"
            );
            let node = build_structural_node_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                structural_prior_state,
            );
            let branch_history = build_structural_branch_history_artifact(snapshot, feedback_history);
            let branch_set = build_structural_branch_set_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &node,
                &branch_history,
                structural_prior_state,
            );
            let scenario_history =
                build_structural_scenario_history_artifact(snapshot, feedback_history);
            let scenario_playbook = build_structural_scenario_playbook_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &branch_set,
                &scenario_history,
                structural_prior_state,
            );
            let provider_support = build_workflow_provider_support(
                provider_status_agent,
                if hard_block_active {
                    &snapshot.blocking_truth.next_command
                } else {
                    &snapshot.recommended_next_command
                },
                if snapshot.blocking_truth.reason.trim().is_empty() {
                    if snapshot.current_focus_reason.trim().is_empty() {
                        None
                    } else {
                        Some(snapshot.current_focus_reason.as_str())
                    }
                } else {
                    Some(snapshot.blocking_truth.reason.as_str())
                },
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(build_structural_path_plan_artifact_with_prior_state(
                    snapshot,
                    provider_status_agent,
                    &provider_support,
                    &scenario_playbook,
                    &build_structural_path_history_artifact(snapshot, feedback_history),
                    structural_prior_state,
                ))?,
                workflow_status_structural_recommended_next_step(
                    snapshot,
                    provider_status_agent,
                    feedback_history,
                    structural_prior_state,
                ),
            )
        }
        "structural-path-history" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_path_history_artifact(
                snapshot,
                feedback_history,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-path-outcome-summary" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_path_history_artifact(snapshot, feedback_history).summary)?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-node-history" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_node_history_artifact(
                snapshot,
                feedback_history,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-branch-history" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_branch_history_artifact(
                snapshot,
                feedback_history,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-scenario-history" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_scenario_history_artifact(
                snapshot,
                feedback_history,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-history-summary" => workflow_status_value_with_recommended_next_step(
            serde_json::to_value(build_structural_history_summary_artifact(
                snapshot,
                feedback_history,
            ))?,
            workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            ),
        ),
        "structural-experience-priors" | "structural-experience-prior-surface" => {
            let artifact = build_structural_experience_prior_surface_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            let recommended_next_step = workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(artifact)?,
                recommended_next_step,
            )
        }
        "structural-top-path-candidates" | "structural-top-paths" => {
            let artifact = build_structural_top_path_candidates_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            let recommended_next_step = workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(artifact)?,
                recommended_next_step,
            )
        }
        "structural-recommended-path-bundle" | "structural-recommended-path" => {
            let bundle = build_structural_recommended_path_bundle_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            let recommended_next_step = workflow_status_structural_recommended_next_step(
                snapshot,
                provider_status_agent,
                feedback_history,
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(bundle)?,
                recommended_next_step,
            )
        }
        "structural-feedback-template" | "structural-feedback" => {
            let node = build_structural_node_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                structural_prior_state,
            );
            let branch_history = build_structural_branch_history_artifact(snapshot, feedback_history);
            let branch_set = build_structural_branch_set_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &node,
                &branch_history,
                structural_prior_state,
            );
            let scenario_history =
                build_structural_scenario_history_artifact(snapshot, feedback_history);
            let scenario_playbook = build_structural_scenario_playbook_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &branch_set,
                &scenario_history,
                structural_prior_state,
            );
            let hard_block_active = matches!(
                snapshot.blocking_truth.status.as_str(),
                "blocked"
                    | "bridge_needs_confirmation"
                    | "validated_regressing"
                    | "credibility_gate_blocked"
            );
            let provider_support = build_workflow_provider_support(
                provider_status_agent,
                if hard_block_active {
                    &snapshot.blocking_truth.next_command
                } else {
                    &snapshot.recommended_next_command
                },
                if snapshot.blocking_truth.reason.trim().is_empty() {
                    if snapshot.current_focus_reason.trim().is_empty() {
                        None
                    } else {
                        Some(snapshot.current_focus_reason.as_str())
                    }
                } else {
                    Some(snapshot.blocking_truth.reason.as_str())
                },
            );
            let path_plan = build_structural_path_plan_artifact_with_prior_state(
                snapshot,
                provider_status_agent,
                &provider_support,
                &scenario_playbook,
                &build_structural_path_history_artifact(snapshot, feedback_history),
                structural_prior_state,
            );
            workflow_status_value_with_recommended_next_step(
                serde_json::to_value(build_structural_feedback_template_artifact(
                    snapshot,
                    &node,
                    &branch_set,
                    &scenario_playbook,
                    &path_plan,
                ))?,
                workflow_status_structural_recommended_next_step(
                    snapshot,
                    provider_status_agent,
                    feedback_history,
                    structural_prior_state,
                ),
            )
        }
        "train" => serde_json::to_value(&build_phase_snapshot_surfaces(snapshot).train)?,
        "analyze" => serde_json::to_value(&build_phase_snapshot_surfaces(snapshot).analyze)?,
        "research" => serde_json::to_value(&build_phase_snapshot_surfaces(snapshot).research)?,
        "backtest" => serde_json::to_value(&build_phase_snapshot_surfaces(snapshot).backtest)?,
        "update" => serde_json::to_value(&build_phase_snapshot_surfaces(snapshot).update)?,
        "pre-bayes-policy" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_policy)?
        }
        "pre-bayes-policy-history" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_policy_history)?
        }
        "pre-bayes-policy-diff" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_policy_diff)?
        }
        "pre-bayes-policy-lineage" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_policy_lineage)?
        }
        "pre-bayes-entry-quality-bridge" => serde_json::to_value(
            &build_pre_bayes_surfaces(snapshot).pre_bayes_entry_quality_bridge,
        )?,
        "pre-bayes-entry-quality-bridge-diff" => serde_json::to_value(
            &build_pre_bayes_surfaces(snapshot).pre_bayes_entry_quality_bridge_diff,
        )?,
        "pre-bayes-soft-evidence" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_soft_evidence)?
        }
        "pre-bayes-soft-evidence-diff" => {
            serde_json::to_value(&build_pre_bayes_surfaces(snapshot).pre_bayes_soft_evidence_diff)?
        }
        "pending-update" => {
            serde_json::to_value(&build_auxiliary_artifact_surfaces(snapshot).pending_update)?
        }
        "pending-update-history" => serde_json::to_value(
            &build_auxiliary_artifact_surfaces(snapshot).pending_update_history,
        )?,
        "execution-candidate" => {
            serde_json::to_value(&build_auxiliary_artifact_surfaces(snapshot).execution_candidate)?
        }
        "execution-candidate-history" => serde_json::to_value(
            &build_auxiliary_artifact_surfaces(snapshot).execution_candidate_history,
        )?,
        "ensemble-vote" => serde_json::to_value(
            resolved_latest_ensemble_vote(snapshot)
                .as_ref()
                .map(|vote| build_ensemble_vote_surface(vote, persisted_scorecards)),
        )?,
        "ensemble-vote-history" => serde_json::to_value(build_ensemble_vote_history_view(
            snapshot,
            persisted_scorecards,
        ))?,
        "ensemble-scorecards" | "ensemble-executor-scorecards" => {
            serde_json::to_value(persisted_scorecards)?
        }
        "artifact-history-summary" => serde_json::to_value(
            &build_auxiliary_artifact_surfaces(snapshot).artifact_history_summary,
        )?,
        "artifact-factor-trends" => serde_json::to_value(
            &build_auxiliary_artifact_surfaces(snapshot).artifact_factor_trends,
        )?,
        "artifact-family-trends" => serde_json::to_value(
            &build_auxiliary_artifact_surfaces(snapshot).artifact_family_trends,
        )?,
        "artifact-consumed-gate" => {
            serde_json::to_value(&build_artifact_report_surfaces(snapshot).artifact_consumed_gate)?
        }
        "artifact-factor-consumed-validation" | "artifact-factor-consumed-leaderboard" => {
            serde_json::to_value(
                &build_artifact_report_surfaces(snapshot).artifact_factor_consumed_validation,
            )?
        }
        "artifact-family-consumed-validation" | "artifact-family-consumed-leaderboard" => {
            serde_json::to_value(
                &build_artifact_report_surfaces(snapshot).artifact_family_consumed_validation,
            )?
        }
        "artifact-lineage-summaries" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_lineage_summaries,
        )?,
        "artifact-decision-summary" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_decision_summary,
        )?,
        "artifact-rule-breaks" => {
            serde_json::to_value(&build_artifact_report_surfaces(snapshot).artifact_rule_breaks)?
        }
        "artifact-rule-break-effects" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_rule_break_effects,
        )?,
        "artifact-factor-rule-break-impacts" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_factor_rule_break_impacts,
        )?,
        "artifact-family-rule-break-impacts" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_family_rule_break_impacts,
        )?,
        "artifact-impact-leaderboard" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_impact_leaderboard,
        )?,
        "artifact-impact-consumed" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_impact_consumed,
        )?,
        "artifact-impact-consumed-trend" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_impact_consumed_trend,
        )?,
        "artifact-review-rules" => {
            serde_json::to_value(&build_artifact_report_surfaces(snapshot).artifact_review_rules)?
        }
        "artifact-review-rule-sources" => serde_json::to_value(
            &build_artifact_report_surfaces(snapshot).artifact_review_rule_sources,
        )?,
        "disagreements" => {
            serde_json::to_value(&build_artifact_report_surfaces(snapshot).disagreements)?
        }
        "diffs" => serde_json::to_value(&build_artifact_report_surfaces(snapshot).diffs)?,
        other => anyhow::bail!("unsupported workflow-status phase '{}'", other),
    })
}

pub fn build_pre_bayes_status_value(
    snapshot: &WorkflowSnapshot,
    section: Option<&str>,
) -> Result<Value> {
    let pre = build_pre_bayes_surfaces(snapshot);
    let latest_phase = latest_pre_bayes_phase(snapshot);
    Ok(
        match section.map(|value| value.trim().to_ascii_lowercase()) {
            None => serde_json::to_value(json!({
                "latest_policy": pre.pre_bayes_policy,
                "latest_bridge": pre.pre_bayes_entry_quality_bridge,
                "latest_bridge_diff": pre.pre_bayes_entry_quality_bridge_diff,
                "latest_policy_diff": pre.pre_bayes_policy_diff,
                "latest_policy_lineage": pre.pre_bayes_policy_lineage,
                "latest_gate_status": latest_phase.map(|phase| phase.pre_bayes_gate_status.clone()),
                "latest_policy_version": latest_phase.map(|phase| phase.pre_bayes_policy_version.clone()),
                "latest_uses_soft_evidence": latest_phase.map(|phase| phase.pre_bayes_uses_soft_evidence),
                "latest_canonical_structural_active_regime": pre.canonical_structural_active_regime,
                "latest_canonical_structural_confidence": pre.canonical_structural_confidence,
                "latest_canonical_structural_probabilities": pre.canonical_structural_probabilities,
                "latest_soft_evidence_diff": pre.pre_bayes_soft_evidence_diff,
                "latest_soft_evidence": latest_phase.map(|phase| phase.pre_bayes_soft_evidence.clone()),
            }))?,
            Some(section) if section == "policy" => serde_json::to_value(&pre.pre_bayes_policy)?,
            Some(section) if section == "bridge" => {
                serde_json::to_value(&pre.pre_bayes_entry_quality_bridge)?
            }
            Some(section) if section == "bridge-diff" => {
                serde_json::to_value(&pre.pre_bayes_entry_quality_bridge_diff)?
            }
            Some(section) if section == "history" => {
                serde_json::to_value(&pre.pre_bayes_policy_history)?
            }
            Some(section) if section == "diff" => serde_json::to_value(&pre.pre_bayes_policy_diff)?,
            Some(section) if section == "lineage" => {
                serde_json::to_value(&pre.pre_bayes_policy_lineage)?
            }
            Some(section) if section == "gate" => serde_json::to_value(json!({
                "status": latest_phase.map(|phase| phase.pre_bayes_gate_status.clone()),
                "policy_version": latest_phase.map(|phase| phase.pre_bayes_policy_version.clone()),
                "uses_soft_evidence": latest_phase.map(|phase| phase.pre_bayes_uses_soft_evidence),
                "canonical_structural_active_regime": pre.canonical_structural_active_regime,
                "canonical_structural_confidence": pre.canonical_structural_confidence,
                "canonical_structural_probabilities": pre.canonical_structural_probabilities,
            }))?,
            Some(section) if section == "soft" || section == "soft-evidence" => {
                serde_json::to_value(
                    latest_phase.map(|phase| phase.pre_bayes_soft_evidence.clone()),
                )?
            }
            Some(section) if section == "soft-diff" => {
                serde_json::to_value(&pre.pre_bayes_soft_evidence_diff)?
            }
            Some(other) => anyhow::bail!("unsupported pre-bayes-status section '{}'", other),
        },
    )
}

pub fn emit_pre_bayes_status_output(
    snapshot: &WorkflowSnapshot,
    section: Option<&str>,
) -> Result<()> {
    let value = build_pre_bayes_status_value(snapshot, section)?;
    print_redacted_json(&value)
}

pub fn build_pre_bayes_diff_value(snapshot: &WorkflowSnapshot) -> Value {
    let latest_phase = latest_pre_bayes_phase(snapshot);
    json!({
        "latest_policy_diff": snapshot.latest_pre_bayes_policy_diff,
        "latest_policy_lineage": snapshot.latest_pre_bayes_policy_lineage,
        "latest_gate_status": latest_phase.map(|phase| phase.pre_bayes_gate_status.clone()),
        "latest_policy_version": latest_phase.map(|phase| phase.pre_bayes_policy_version.clone()),
        "latest_uses_soft_evidence": latest_phase.map(|phase| phase.pre_bayes_uses_soft_evidence),
        "latest_canonical_structural_active_regime": latest_phase.and_then(|phase| phase.canonical_structural_active_regime.clone()),
        "latest_canonical_structural_confidence": latest_phase.and_then(|phase| phase.canonical_structural_confidence),
        "latest_canonical_structural_probabilities": latest_phase.map(|phase| phase.canonical_structural_probabilities.clone()),
        "latest_soft_evidence_diff": snapshot.latest_pre_bayes_soft_evidence_diff,
        "latest_bridge": snapshot.latest_pre_bayes_entry_quality_bridge,
        "latest_bridge_diff": snapshot.latest_pre_bayes_entry_quality_bridge_diff,
    })
}

pub fn emit_pre_bayes_diff_output(snapshot: &WorkflowSnapshot) -> Result<()> {
    let value = build_pre_bayes_diff_value(snapshot);
    print_redacted_json(&value)
}

pub fn build_workflow_status_bootstrap_phase_value(
    symbol: &str,
    state_dir: &str,
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    detected_tomac_root: Option<String>,
    multi_timeframe_clean_root: Option<String>,
    tomac_root_placeholder: &str,
) -> Result<Value> {
    Ok(serde_json::to_value(build_agent_bootstrap_view(
        AgentBootstrapBuildInput {
            symbol,
            state_dir,
            snapshot,
            provider_status_agent,
            detected_tomac_root,
            multi_timeframe_clean_root,
            tomac_root_placeholder,
        },
    ))?)
}

#[cfg(test)]
fn build_workflow_status_bootstrap_phase_value_with_probe<F>(
    bootstrap: WorkflowStatusBootstrapInput<'_>,
    snapshot: &WorkflowSnapshot,
    provider_status_agent: &ProviderCatalogAgentSurface,
    probe: &F,
) -> Result<Value>
where
    F: Fn(&str, u16) -> bool,
{
    Ok(serde_json::to_value(
        build_agent_bootstrap_view_with_probe(
            AgentBootstrapBuildInput {
                symbol: bootstrap.symbol,
                state_dir: bootstrap.state_dir,
                snapshot,
                provider_status_agent,
                detected_tomac_root: bootstrap.detected_tomac_root,
                multi_timeframe_clean_root: bootstrap.multi_timeframe_clean_root,
                tomac_root_placeholder: &bootstrap.tomac_root_placeholder,
            },
            probe,
        ),
    )?)
}

pub fn build_ensemble_vote_history_view(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
) -> WorkflowEnsembleVoteHistoryView {
    let history = snapshot
        .recent_ensemble_votes
        .iter()
        .map(|vote| {
            let vote = resolved_ensemble_vote_for_snapshot(snapshot, vote)
                .unwrap_or_else(|| vote.clone());
            let surface = build_ensemble_vote_surface(&vote, persisted_scorecards);
            WorkflowEnsembleVoteHistoryRow {
                artifact_id: surface.artifact_id,
                generated_at: surface.generated_at,
                symbol: surface.symbol,
                source_phase: surface.source_phase,
                source_run_id: surface.source_run_id,
                final_action: surface.final_action,
                recommended_command: surface.recommended_command,
                human_next_triage: surface.human_next_triage,
                hard_block: surface.hard_block,
                executor_scorecards: surface.executor_scorecards,
                executor_scorecard_source: surface.executor_scorecard_source,
            }
        })
        .collect::<Vec<_>>();

    let hard_block_only = history
        .iter()
        .filter(|row| row.hard_block.active)
        .cloned()
        .collect::<Vec<_>>();

    let mut reason_counts = std::collections::BTreeMap::<String, usize>::new();
    for row in &hard_block_only {
        let reason = row
            .hard_block
            .reason
            .clone()
            .unwrap_or_else(|| "hard_block_reason_unavailable".to_string());
        *reason_counts.entry(reason).or_insert(0) += 1;
    }

    let reason_leaderboard = reason_counts
        .into_iter()
        .map(|(reason, count)| WorkflowHardBlockReasonCount { reason, count })
        .collect::<Vec<_>>();

    WorkflowEnsembleVoteHistoryView {
        hard_block_summary: WorkflowHardBlockSummary {
            count: hard_block_only.len(),
            reason_leaderboard,
        },
        history,
        hard_block_only,
    }
}

pub fn filter_hard_block_rows(
    snapshot: &WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
    hard_block_only: bool,
    hard_block_reason: Option<&str>,
    limit: Option<usize>,
) -> Vec<WorkflowEnsembleVoteHistoryRow> {
    build_ensemble_vote_history_view(snapshot, persisted_scorecards)
        .history
        .into_iter()
        .filter(|row| !hard_block_only || row.hard_block.active)
        .filter(|row| {
            hard_block_reason.is_none_or(|reason| row.hard_block.reason.as_deref() == Some(reason))
        })
        .take(limit.unwrap_or(usize::MAX))
        .collect()
}

pub fn build_auxiliary_artifact_surfaces(
    snapshot: &WorkflowSnapshot,
) -> WorkflowAuxiliaryArtifactSurfaces {
    WorkflowAuxiliaryArtifactSurfaces {
        pending_update: snapshot.latest_pending_update.clone(),
        pending_update_history: snapshot.recent_pending_updates.clone(),
        execution_candidate: snapshot.latest_execution_candidate.clone(),
        execution_candidate_history: snapshot.recent_execution_candidates.clone(),
        artifact_history_summary: snapshot.artifact_history_summary.clone(),
        artifact_factor_trends: snapshot.artifact_factor_trends.clone(),
        artifact_family_trends: snapshot.artifact_family_trends.clone(),
    }
}

pub fn sorted_artifact_factor_consumed_validation(
    snapshot: &WorkflowSnapshot,
) -> Vec<ArtifactFactorTrendSummary> {
    let mut items = snapshot.artifact_factor_trends.clone();
    items.sort_by(|a, b| {
        b.consumed_entries
            .cmp(&a.consumed_entries)
            .then_with(|| b.entries.cmp(&a.entries))
            .then_with(|| a.factor_name.cmp(&b.factor_name))
    });
    items
}

pub fn sorted_artifact_family_consumed_validation(
    snapshot: &WorkflowSnapshot,
) -> Vec<ArtifactFamilyTrendSummary> {
    let mut items = snapshot.artifact_family_trends.clone();
    items.sort_by(|a, b| {
        b.consumed_entries
            .cmp(&a.consumed_entries)
            .then_with(|| b.entries.cmp(&a.entries))
            .then_with(|| a.family.cmp(&b.family))
    });
    items
}

pub fn build_pre_bayes_surfaces(snapshot: &WorkflowSnapshot) -> WorkflowPreBayesSurfaces {
    let latest_phase = latest_pre_bayes_phase(snapshot);
    WorkflowPreBayesSurfaces {
        pre_bayes_policy: snapshot.latest_pre_bayes_policy.clone(),
        pre_bayes_policy_history: snapshot.recent_pre_bayes_policies.clone(),
        pre_bayes_policy_diff: snapshot.latest_pre_bayes_policy_diff.clone(),
        pre_bayes_policy_lineage: snapshot.latest_pre_bayes_policy_lineage.clone(),
        pre_bayes_entry_quality_bridge: snapshot.latest_pre_bayes_entry_quality_bridge.clone(),
        pre_bayes_entry_quality_bridge_diff: snapshot
            .latest_pre_bayes_entry_quality_bridge_diff
            .clone(),
        canonical_structural_active_regime: latest_phase
            .and_then(|phase| phase.canonical_structural_active_regime.clone()),
        canonical_structural_confidence: latest_phase
            .and_then(|phase| phase.canonical_structural_confidence),
        canonical_structural_probabilities: latest_phase
            .map(|phase| phase.canonical_structural_probabilities.clone())
            .unwrap_or_default(),
        pre_bayes_soft_evidence: latest_phase.map(|phase| phase.pre_bayes_soft_evidence.clone()),
        pre_bayes_soft_evidence_diff: snapshot.latest_pre_bayes_soft_evidence_diff.clone(),
    }
}

fn latest_pre_bayes_phase(
    snapshot: &WorkflowSnapshot,
) -> Option<&crate::state::WorkflowPhaseSnapshot> {
    [
        snapshot.latest_update.as_ref(),
        snapshot.latest_research.as_ref(),
        snapshot.latest_analyze.as_ref(),
        snapshot.latest_backtest.as_ref(),
    ]
    .into_iter()
    .flatten()
    .filter(|phase| {
        !phase.pre_bayes_gate_status.is_empty()
            || !phase.pre_bayes_policy_version.is_empty()
            || phase.pre_bayes_uses_soft_evidence
            || !phase.pre_bayes_soft_evidence.is_empty()
            || phase.canonical_structural_active_regime.is_some()
            || phase.canonical_structural_confidence.is_some()
            || !phase.canonical_structural_probabilities.is_empty()
    })
    .max_by(|left, right| left.timestamp.cmp(&right.timestamp))
}

pub fn build_artifact_report_surfaces(
    snapshot: &WorkflowSnapshot,
) -> WorkflowArtifactReportSurfaces {
    WorkflowArtifactReportSurfaces {
        artifact_consumed_gate: serde_json::json!({
            "status": snapshot.artifact_decision_summary.consumed_trend_status,
            "reason": snapshot.artifact_decision_summary.consumed_trend_reason,
            "target_kinds": snapshot.artifact_decision_summary.consumed_target_kinds,
            "promotion_strength": snapshot.artifact_decision_summary.promotion_strength,
            "rollback_strength": snapshot.artifact_decision_summary.rollback_strength,
        }),
        artifact_factor_consumed_validation: sorted_artifact_factor_consumed_validation(snapshot),
        artifact_family_consumed_validation: sorted_artifact_family_consumed_validation(snapshot),
        artifact_lineage_summaries: snapshot.artifact_lineage_summaries.clone(),
        artifact_decision_summary: snapshot.artifact_decision_summary.clone(),
        artifact_rule_breaks: snapshot
            .artifact_lineage_summaries
            .iter()
            .filter(|summary| summary.review_rule_break_count > 0)
            .cloned()
            .collect(),
        artifact_rule_break_effects: snapshot.artifact_rule_break_effects.clone(),
        artifact_factor_rule_break_impacts: snapshot.artifact_factor_rule_break_impacts.clone(),
        artifact_family_rule_break_impacts: snapshot.artifact_family_rule_break_impacts.clone(),
        artifact_impact_leaderboard: serde_json::json!({
            "factor": snapshot.artifact_factor_rule_break_impacts,
            "family": snapshot.artifact_family_rule_break_impacts,
        }),
        artifact_impact_consumed: serde_json::json!({
            "factor": snapshot
                .artifact_factor_rule_break_impacts
                .iter()
                .filter(|impact| impact.consumed_breaks > 0)
                .cloned()
                .collect::<Vec<_>>(),
            "family": snapshot
                .artifact_family_rule_break_impacts
                .iter()
                .filter(|impact| impact.consumed_breaks > 0)
                .cloned()
                .collect::<Vec<_>>(),
        }),
        artifact_impact_consumed_trend: snapshot.artifact_consumed_impact_summary.clone(),
        artifact_review_rules: snapshot.artifact_review_rules.clone(),
        artifact_review_rule_sources: snapshot.artifact_review_rule_sources.clone(),
        disagreements: snapshot.disagreements.clone(),
        diffs: snapshot.field_diffs.clone(),
    }
}

pub fn sample_human_workflow_snapshot() -> WorkflowSnapshot {
    let mut snapshot = WorkflowSnapshot::default();
    snapshot.symbol = "NQ".to_string();
    snapshot.current_focus_phase = "update".to_string();
    snapshot.current_focus_reason = "waiting_for_user_data_choice".to_string();
    snapshot.blocking_truth = crate::state::WorkflowBlockingTruth {
        stage: "research".to_string(),
        status: "blocked".to_string(),
        reason: "user_selected_historical_data_missing".to_string(),
        evidence: vec!["need user choice".to_string()],
        next_command: "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string(),
    };
    snapshot.recommended_next_command = "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string();
    snapshot.pending_actions = vec!["research:choose data".to_string()];
    snapshot.risk_flags = vec!["human_gate_active".to_string()];
    snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
        artifact_id: "ensemble-vote:update:test".to_string(),
        generated_at: Utc::now(),
        symbol: "NQ".to_string(),
        source_phase: "update".to_string(),
        source_run_id: Some("run-1".to_string()),
        provenance: RunProvenance::default(),
        dataset_comparability: DatasetComparability::default(),
        ensemble_version: "ensemble-audit-v1".to_string(),
        final_action: "observe".to_string(),
        recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next".to_string(),
        human_next_triage: "hard_blocked=true ensemble_action=observe consensus=0.500 regime=research hard_block_reason=user_selected_historical_data_missing command=ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string(),
        hard_block: super::EnsembleHardBlockArtifact {
            active: true,
            stage: Some("research".to_string()),
            status: Some("blocked".to_string()),
            reason: Some("user_selected_historical_data_missing".to_string()),
            evidence: vec!["need user choice".to_string()],
            command: Some("ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string()),
            human_action: Some("Ask the user to choose the historical dataset. Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json Then run: ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string()),
        },
        confidence: 0.5,
        consensus_strength: 0.5,
        disagreement_flags: Vec::new(),
        executor_summaries: vec![
            "executor=catboost_stub action=observe confidence=0.500".to_string(),
            "jump_model active_state=jump_transition confidence=0.500 transition_risk=0.500"
                .to_string(),
            "jump_calibration_gate outcome=accepted sample_count=4 cooldown_status=ready"
                .to_string(),
            "jump_disagreement=jump_transition_vs_hmm_only".to_string(),
        ],
        split_explanations: vec!["active_regime=research".to_string()],
        executor_scorecards: vec![EnsembleExecutorScorecard {
            executor: "catboost_stub".to_string(),
            latest_weight_hint: Some(0.55),
            ..EnsembleExecutorScorecard::default()
        }],
        executor_scorecards_source: Some("fallback".to_string()),
        posterior_fingerprint: "fp-test".to_string(),
        posterior_normalization_status: "normalized".to_string(),
        posterior_active_regime: "research".to_string(),
        posterior_confidence: Some(0.5),
        posterior_probabilities: std::collections::BTreeMap::new(),
        posterior_evidence: vec!["mtf=test".to_string()],
    });
    snapshot.latest_update = Some(crate::state::WorkflowPhaseSnapshot {
        phase: "update".to_string(),
        workflow_reason: "waiting_for_data_choice".to_string(),
        phase_summary: "latest update complete".to_string(),
        top_actions: vec!["update:review".to_string()],
        risk_flags: vec!["human_gate_active".to_string()],
        multi_timeframe_summary: vec![
            "15m:80 bars path=/tmp/a.json".to_string(),
            "1h:80 bars path=/tmp/b.json".to_string(),
        ],
        pre_bayes_gate_status: "pass_neutralized".to_string(),
        pre_bayes_uses_soft_evidence: true,
        pre_bayes_policy_version: "v1".to_string(),
        pre_bayes_evidence_quality_score: 0.5,
        pre_bayes_multi_timeframe_direction_bias: "bullish".to_string(),
        pre_bayes_multi_timeframe_alignment_score: Some(0.8),
        pre_bayes_multi_timeframe_entry_alignment_score: Some(0.8),
        selected_entry_quality: Some("medium".to_string()),
        pre_bayes_bridge_selected_entry_quality: Some("medium".to_string()),
        pre_bayes_bridge_probability_gap: Some(0.01),
        hybrid_duration_model: Some("negative_binomial".to_string()),
        hybrid_remaining_expected_bars: Some(2.5),
        comparable_to_previous: true,
        comparison_class: "same_data_different_config".to_string(),
        recommended_next_command: snapshot.recommended_next_command.clone(),
        pda_cluster_label: Some("cluster_1".to_string()),
        realized_outcome: Some("win".to_string()),
        objective_market_credibility_shrink: None,
        ..crate::state::WorkflowPhaseSnapshot::default()
    });
    snapshot
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::TimeZone;
    use crate::application::orchestration::EnsembleHardBlockArtifact;
    use crate::application::provider_catalog::{
        ProviderCatalogAgentSurface, ProviderCatalogPendingAgentItem,
    };

    fn sample_provider_agent_surface() -> ProviderCatalogAgentSurface {
        ProviderCatalogAgentSurface {
            summary_line: "live_runtime:1/3 ready".to_string(),
            ready_by_domain: std::collections::BTreeMap::from([(
                "live_runtime".to_string(),
                "1/3".to_string(),
            )]),
            ready_providers: vec!["openbb".to_string()],
            pending_providers: vec![
                "openalice@live_runtime:operator_runtime_required:base_url_and_service_required"
                    .to_string(),
                "nofx@live_runtime:operator_runtime_required:base_url_and_service_required"
                    .to_string(),
            ],
            pending_provider_details: vec![
                ProviderCatalogPendingAgentItem {
                    provider_id: "openalice".to_string(),
                    domain: "live_runtime".to_string(),
                    status: "operator_runtime_required".to_string(),
                    reason: "base_url_and_service_required".to_string(),
                    install_prompts: vec![
                        "Ask whether the user wants zero-config openbb or openalice.".to_string(),
                    ],
                },
                ProviderCatalogPendingAgentItem {
                    provider_id: "nofx".to_string(),
                    domain: "live_runtime".to_string(),
                    status: "operator_runtime_required".to_string(),
                    reason: "base_url_and_service_required".to_string(),
                    install_prompts: vec![
                        "Ask whether the user wants zero-config openbb or nofx.".to_string()
                    ],
                },
            ],
            selectable_providers: vec!["openalice".to_string(), "nofx".to_string()],
            default_enabled_providers: vec!["openbb".to_string()],
            install_prompts: vec![
                "Ask whether the user wants zero-config openbb or openalice.".to_string(),
                "Ask whether the user wants zero-config openbb or nofx.".to_string(),
                "Ask the user for a TradingViewRemix MCP API key before attempting TradingViewRemix-backed live or options workflows. Search keywords: TradingViewRemix MCP API key.".to_string(),
                "Ask the user to install IBKR TWS or IB Gateway and enable the local API before attempting IBKR-backed live workflows. Search keywords: Interactive Brokers TWS download, IB Gateway download.".to_string(),
            ],
            selected_profile: None,
        }
    }

    fn sample_provider_agent_surface_with_profile() -> ProviderCatalogAgentSurface {
        let mut surface = sample_provider_agent_surface();
        surface.selected_profile = Some(
            crate::application::provider_catalog::ProviderProfileSelectionSurface {
                profile_id: "thrill3r_nq_closed_loop_v1".to_string(),
                display_name: "Thrill3r NQ Closed Loop v1".to_string(),
                opt_in_only: true,
                source: "repo-example".to_string(),
                summary: "Personal NQ workflow".to_string(),
                data_contracts: vec![
                    crate::application::provider_catalog::ProviderProfileDataContract {
                        contract_id: "tomac_clean_root".to_string(),
                        category: "historical".to_string(),
                        required: true,
                        label: "Tomac cleaned multi-timeframe futures root".to_string(),
                        symbols: vec!["NQ".to_string()],
                        timeframes: vec!["1d".to_string(), "1h".to_string(), "15m".to_string()],
                        path_hint: None,
                        notes: Vec::new(),
                    },
                    crate::application::provider_catalog::ProviderProfileDataContract {
                        contract_id: "qqq_options_surface".to_string(),
                        category: "options".to_string(),
                        required: true,
                        label: "QQQ options Greeks / IV / OI".to_string(),
                        symbols: vec!["QQQ".to_string()],
                        timeframes: vec!["snapshot".to_string()],
                        path_hint: None,
                        notes: Vec::new(),
                    },
                ],
                data_contract_labels: vec![
                    "Tomac cleaned multi-timeframe futures root".to_string(),
                    "QQQ options Greeks / IV / OI".to_string(),
                ],
                track_details: vec![
                    crate::application::provider_catalog::ProviderProfileTrackSelection {
                        track_id: "research_zero_config".to_string(),
                        label: "Zero-config research companion data".to_string(),
                        required: true,
                        mode: "any_of".to_string(),
                        activation_hints: vec!["research".to_string(), "backtest".to_string()],
                        status: "ready".to_string(),
                        ready_provider_ids: vec!["openbb".to_string()],
                        pending_provider_ids: Vec::new(),
                        install_prompts: Vec::new(),
                        notes: Vec::new(),
                    },
                    crate::application::provider_catalog::ProviderProfileTrackSelection {
                        track_id: "options_enriched".to_string(),
                        label: "Options enrichment".to_string(),
                        required: true,
                        mode: "any_of".to_string(),
                        activation_hints: vec!["research".to_string(), "options".to_string()],
                        status: "pending".to_string(),
                        ready_provider_ids: Vec::new(),
                        pending_provider_ids: vec!["tradingview_mcp".to_string()],
                        install_prompts: vec!["Ask for TradingViewRemix MCP API key.".to_string()],
                        notes: Vec::new(),
                    },
                ],
                track_statuses: vec![
                    "research_zero_config:ready:openbb,yfinance".to_string(),
                    "options_enriched:pending:tradingview_mcp".to_string(),
                ],
                ready_provider_ids: vec!["openbb".to_string()],
                pending_provider_ids: vec!["tradingview_mcp".to_string()],
                install_prompts: vec!["Ask for TradingViewRemix MCP API key.".to_string()],
            },
        );
        surface
    }

    fn sample_structural_feedback_history() -> Vec<crate::state::FeedbackRecord> {
        let timestamp = Utc::with_ymd_and_hms(&Utc, 2026, 4, 29, 0, 0, 0).unwrap();
        vec![
            crate::state::FeedbackRecord {
                timestamp,
                symbol: "NQ".to_string(),
                source: "structural_feedback_submission".to_string(),
                run_id: Some("run-1".to_string()),
                trade_id: None,
                prompt_version: Some("structural-feedback-v1".to_string()),
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: crate::state::ModelProbabilitySnapshot {
                    selected_direction: crate::types::Direction::Bull,
                    selected_probability: 0.72,
                    long_score: 0.72,
                    short_score: 0.28,
                    win_prob_long: 0.72,
                    win_prob_short: 0.28,
                    uncertainty: 0.28,
                },
                realized_outcome: "win".to_string(),
                pnl: 0.03,
                regime_at_entry: crate::types::Regime::ManipulationExpansion,
                structural_feedback: Some(crate::state::StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "structural-feedback:NQ:node:path".to_string(),
                    recommended_at: "2026-04-29T00:00:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id:
                        "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
                            .to_string(),
                    followed_path: true,
                    exit_reason: Some("target_hit".to_string()),
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
            crate::state::FeedbackRecord {
                timestamp: timestamp + chrono::Duration::minutes(5),
                symbol: "NQ".to_string(),
                source: "structural_feedback_submission".to_string(),
                run_id: Some("run-2".to_string()),
                trade_id: None,
                prompt_version: Some("structural-feedback-v1".to_string()),
                factor_version: None,
                data_fingerprint: None,
                factors_used: Vec::new(),
                model_probabilities_before_trade: crate::state::ModelProbabilitySnapshot {
                    selected_direction: crate::types::Direction::Bull,
                    selected_probability: 0.70,
                    long_score: 0.70,
                    short_score: 0.30,
                    win_prob_long: 0.70,
                    win_prob_short: 0.30,
                    uncertainty: 0.30,
                },
                realized_outcome: "invalidated".to_string(),
                pnl: -0.01,
                regime_at_entry: crate::types::Regime::ManipulationExpansion,
                structural_feedback: Some(crate::state::StructuralFeedbackRefs {
                    protocol_version: "structural-feedback-v1".to_string(),
                    recommendation_id: "structural-feedback:NQ:node:path-2".to_string(),
                    recommended_at: "2026-04-29T00:05:00Z".to_string(),
                    node_id: "NQ:belief_regime_node:trend".to_string(),
                    branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                    scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                        .to_string(),
                    path_id:
                        "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
                            .to_string(),
                    followed_path: true,
                    exit_reason: Some("invalidated".to_string()),
                    notes: None,
                }),
                reflection_mismatch_tags: Vec::new(),
            },
        ]
    }
    use crate::application::output_foundation::redact_local_paths_in_value;
    use crate::state::WorkflowPhaseSnapshot;

    #[test]
    fn build_pre_bayes_status_value_matches_main_policy_section() {
        let snapshot = WorkflowSnapshot {
            latest_pre_bayes_policy: Some(PreBayesEvidencePolicy {
                version: "v-policy".to_string(),
                ..PreBayesEvidencePolicy::default()
            }),
            ..WorkflowSnapshot::default()
        };
        let value = build_pre_bayes_status_value(&snapshot, Some("policy")).unwrap();
        assert_eq!(value["version"], "v-policy");
    }

    #[test]
    fn build_pre_bayes_status_value_default_includes_gate_and_soft_evidence() {
        let analyze = WorkflowPhaseSnapshot {
            pre_bayes_gate_status: "pass_neutralized".to_string(),
            pre_bayes_policy_version: "v2".to_string(),
            pre_bayes_uses_soft_evidence: true,
            canonical_structural_active_regime: Some("trend".to_string()),
            canonical_structural_confidence: Some(0.78),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.78),
                ("range".to_string(), 0.14),
                ("transition".to_string(), 0.08),
            ]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "node".to_string(),
                std::collections::BTreeMap::from([("state".to_string(), 0.25)]),
            )]),
            ..WorkflowPhaseSnapshot::default()
        };
        let snapshot = WorkflowSnapshot {
            latest_analyze: Some(analyze),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };
        let value = build_pre_bayes_status_value(&snapshot, None).unwrap();
        assert_eq!(value["latest_gate_status"], "pass_neutralized");
        assert_eq!(value["latest_policy_version"], "v2");
        assert_eq!(value["latest_uses_soft_evidence"], true);
        assert_eq!(value["latest_soft_evidence"]["node"]["state"], 0.25);
        assert_eq!(value["latest_canonical_structural_active_regime"], "trend");
        assert_eq!(value["latest_canonical_structural_confidence"], 0.78);
        assert_eq!(value["latest_canonical_structural_probabilities"]["trend"], 0.78);
        assert_eq!(
            value["latest_soft_evidence_diff"].as_array().unwrap().len(),
            1
        );
    }

    #[test]
    fn build_pre_bayes_diff_value_matches_main_surface() {
        let analyze = WorkflowPhaseSnapshot {
            pre_bayes_gate_status: "blocked".to_string(),
            pre_bayes_policy_version: "v3".to_string(),
            pre_bayes_uses_soft_evidence: false,
            canonical_structural_active_regime: Some("range".to_string()),
            canonical_structural_confidence: Some(0.61),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.21),
                ("range".to_string(), 0.61),
                ("transition".to_string(), 0.18),
            ]),
            ..WorkflowPhaseSnapshot::default()
        };
        let snapshot = WorkflowSnapshot {
            latest_analyze: Some(analyze),
            latest_pre_bayes_policy_diff: Some(PreBayesPolicyDiff::default()),
            latest_pre_bayes_policy_lineage: Some(PreBayesPolicyLineageSummary::default()),
            latest_pre_bayes_entry_quality_bridge: Some(PreBayesEntryQualityBridge::default()),
            latest_pre_bayes_entry_quality_bridge_diff: Some(
                PreBayesEntryQualityBridgeDiff::default(),
            ),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };
        let value = build_pre_bayes_diff_value(&snapshot);
        assert_eq!(value["latest_gate_status"], "blocked");
        assert_eq!(value["latest_policy_version"], "v3");
        assert_eq!(value["latest_uses_soft_evidence"], false);
        assert_eq!(value["latest_canonical_structural_active_regime"], "range");
        assert_eq!(value["latest_canonical_structural_confidence"], 0.61);
        assert_eq!(value["latest_canonical_structural_probabilities"]["range"], 0.61);
        assert_eq!(
            value["latest_soft_evidence_diff"].as_array().unwrap().len(),
            1
        );
    }

    #[test]
    fn build_pre_bayes_status_value_prefers_latest_update_phase_when_analyze_missing() {
        let update = WorkflowPhaseSnapshot {
            pre_bayes_gate_status: "pass_hard".to_string(),
            pre_bayes_policy_version: "v-update".to_string(),
            pre_bayes_uses_soft_evidence: true,
            canonical_structural_active_regime: Some("range".to_string()),
            canonical_structural_confidence: Some(0.61),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.21),
                ("range".to_string(), 0.61),
                ("transition".to_string(), 0.18),
            ]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("range".to_string(), 0.61),
                    ("trend".to_string(), 0.21),
                    ("transition".to_string(), 0.18),
                ]),
            )]),
            ..WorkflowPhaseSnapshot::default()
        };
        let snapshot = WorkflowSnapshot {
            latest_update: Some(update),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };

        let value = build_pre_bayes_status_value(&snapshot, None).unwrap();

        assert_eq!(value["latest_gate_status"], "pass_hard");
        assert_eq!(value["latest_policy_version"], "v-update");
        assert_eq!(value["latest_canonical_structural_active_regime"], "range");
        assert_eq!(value["latest_canonical_structural_confidence"], 0.61);
        assert_eq!(value["latest_soft_evidence"]["market_regime"]["range"], 0.61);
    }

    #[test]
    fn build_pre_bayes_status_value_falls_back_to_analyze_when_latest_update_has_no_structural_or_pre_bayes_surface(
    ) {
        let analyze = WorkflowPhaseSnapshot {
            pre_bayes_gate_status: "pass_neutralized".to_string(),
            pre_bayes_policy_version: "v-analyze".to_string(),
            pre_bayes_uses_soft_evidence: true,
            canonical_structural_active_regime: Some("trend".to_string()),
            canonical_structural_confidence: Some(0.78),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.78),
                ("range".to_string(), 0.14),
                ("transition".to_string(), 0.08),
            ]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("trend".to_string(), 0.78),
                    ("range".to_string(), 0.14),
                    ("transition".to_string(), 0.08),
                ]),
            )]),
            ..WorkflowPhaseSnapshot::default()
        };
        let update = WorkflowPhaseSnapshot {
            phase: "update".to_string(),
            pre_bayes_gate_status: String::new(),
            pre_bayes_policy_version: String::new(),
            pre_bayes_uses_soft_evidence: false,
            canonical_structural_active_regime: None,
            canonical_structural_confidence: None,
            canonical_structural_probabilities: std::collections::BTreeMap::new(),
            pre_bayes_soft_evidence: std::collections::BTreeMap::new(),
            ..WorkflowPhaseSnapshot::default()
        };
        let snapshot = WorkflowSnapshot {
            latest_analyze: Some(analyze),
            latest_update: Some(update),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };

        let value = build_pre_bayes_status_value(&snapshot, None).unwrap();

        assert_eq!(value["latest_gate_status"], "pass_neutralized");
        assert_eq!(value["latest_policy_version"], "v-analyze");
        assert_eq!(value["latest_canonical_structural_active_regime"], "trend");
        assert_eq!(value["latest_canonical_structural_confidence"], 0.78);
        assert_eq!(value["latest_soft_evidence"]["market_regime"]["trend"], 0.78);
    }

    #[test]
    fn build_pre_bayes_status_value_prefers_newest_populated_phase_over_fixed_update_priority() {
        let update = WorkflowPhaseSnapshot {
            phase: "update".to_string(),
            timestamp: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
            pre_bayes_gate_status: "pass_hard".to_string(),
            pre_bayes_policy_version: "v-update".to_string(),
            canonical_structural_active_regime: Some("range".to_string()),
            canonical_structural_confidence: Some(0.61),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.21),
                ("range".to_string(), 0.61),
                ("transition".to_string(), 0.18),
            ]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("range".to_string(), 0.61),
                    ("trend".to_string(), 0.21),
                    ("transition".to_string(), 0.18),
                ]),
            )]),
            ..WorkflowPhaseSnapshot::default()
        };
        let research = WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            timestamp: Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap(),
            pre_bayes_gate_status: "observe".to_string(),
            pre_bayes_policy_version: "v-research".to_string(),
            canonical_structural_active_regime: Some("trend".to_string()),
            canonical_structural_confidence: Some(0.78),
            canonical_structural_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.78),
                ("range".to_string(), 0.14),
                ("transition".to_string(), 0.08),
            ]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("trend".to_string(), 0.78),
                    ("range".to_string(), 0.14),
                    ("transition".to_string(), 0.08),
                ]),
            )]),
            ..WorkflowPhaseSnapshot::default()
        };
        let snapshot = WorkflowSnapshot {
            latest_update: Some(update),
            latest_research: Some(research),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };

        let value = build_pre_bayes_status_value(&snapshot, None).unwrap();

        assert_eq!(value["latest_gate_status"], "observe");
        assert_eq!(value["latest_policy_version"], "v-research");
        assert_eq!(value["latest_canonical_structural_active_regime"], "trend");
        assert_eq!(value["latest_canonical_structural_confidence"], 0.78);
        assert_eq!(value["latest_soft_evidence"]["market_regime"]["trend"], 0.78);
    }

    #[test]
    fn build_workflow_status_bootstrap_phase_value_matches_bootstrap_view() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_workflow_status_bootstrap_phase_value_with_probe(
            WorkflowStatusBootstrapInput {
                symbol: "NQ",
                state_dir: "state",
                detected_tomac_root: Some("/tmp/tomac".to_string()),
                multi_timeframe_clean_root: Some("/tmp/clean".to_string()),
                tomac_root_placeholder: "<root>".to_string(),
            },
            &snapshot,
            &sample_provider_agent_surface(),
            &|_, port| port == 4002,
        )
        .unwrap();
        assert_eq!(value["symbol"], "NQ");
        assert_eq!(value["detected_paths"]["state_dir"], "state");
        assert_eq!(
            value["commands"]["workflow_status"],
            "ict-engine workflow-status --symbol NQ --state-dir state"
        );
        assert!(
            value["input_acquisition"]["live"]["provider_access_requests"]
                .as_array()
                .unwrap()
                .iter()
                .any(|item| item
                    .as_str()
                    .unwrap()
                    .contains("TradingViewRemix MCP API key"))
        );
        assert!(
            value["input_acquisition"]["live"]["provider_access_requests"]
                .as_array()
                .unwrap()
                .iter()
                .any(|item| item.as_str().unwrap().contains("IBKR TWS or IB Gateway"))
        );
        assert_eq!(
            value["input_acquisition"]["live"]["ibkr_gateway_summary"]["occupied_judgement"],
            "single_reachable_candidate"
        );
        assert_eq!(
            value["input_acquisition"]["live"]["ibkr_gateway_candidates"]
                .as_array()
                .unwrap()
                .len(),
            4
        );
    }

    #[test]
    fn build_ibkr_gateway_candidates_marks_first_reachable_as_recommended() {
        let candidates = build_ibkr_gateway_candidates_with_probe("127.0.0.1", &|_, port| {
            matches!(port, 4002 | 4001)
        });

        assert_eq!(candidates.len(), 4);
        assert!(
            candidates
                .iter()
                .find(|candidate| candidate.port == 4002)
                .unwrap()
                .recommended
        );
        assert!(
            candidates
                .iter()
                .find(|candidate| candidate.port == 4001)
                .unwrap()
                .reachable
        );
        assert!(
            !candidates
                .iter()
                .find(|candidate| candidate.port == 4001)
                .unwrap()
                .recommended
        );
    }

    #[test]
    fn build_ibkr_gateway_summary_flags_multiple_reachable_candidates() {
        let candidates = vec![
            AgentBootstrapIbkrGatewayCandidate {
                label: "TWS paper".to_string(),
                host: "127.0.0.1".to_string(),
                port: 7497,
                reachable: true,
                recommended: true,
            },
            AgentBootstrapIbkrGatewayCandidate {
                label: "IB Gateway paper".to_string(),
                host: "127.0.0.1".to_string(),
                port: 4002,
                reachable: true,
                recommended: false,
            },
        ];

        let summary = build_ibkr_gateway_summary(&candidates);
        assert_eq!(
            summary.occupied_judgement,
            "multiple_reachable_candidates_choose_explicit_port"
        );
        assert_eq!(summary.preferred_port, Some(7497));
        assert!(summary.recommended_action.contains("--gateway-port 7497"));
    }

    #[test]
    fn build_workflow_status_phase_value_matches_human_surface() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "human",
        )
        .unwrap();
        assert_eq!(
            value["summary_line"],
            "NQ | update | action_blocked | pda_cluster=cluster_1 | duration=negative_binomial | remaining_bars=2.50"
        );
        assert_eq!(value["current_status"]["focus_phase"], "update");
    }

    #[test]
    fn build_workflow_status_phase_value_supports_artifact_alias() {
        let snapshot = WorkflowSnapshot {
            artifact_factor_trends: vec![ArtifactFactorTrendSummary {
                factor_name: "fvg_rebalance".to_string(),
                consumed_entries: 2,
                entries: 3,
                ..ArtifactFactorTrendSummary::default()
            }],
            ..WorkflowSnapshot::default()
        };

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "artifact-factor-consumed-leaderboard",
        )
        .unwrap();
        assert_eq!(value.as_array().unwrap()[0]["factor_name"], "fvg_rebalance");
    }

    #[test]
    fn build_workflow_status_phase_value_rejects_unknown_phase() {
        let err = build_workflow_status_phase_value(
            &WorkflowSnapshot::default(),
            &[],
            &sample_provider_agent_surface(),
            &[],
            "wat",
        )
        .unwrap_err();
        assert!(err
            .to_string()
            .contains("unsupported workflow-status phase 'wat'"));
    }

    #[test]
    fn build_workflow_status_phase_value_preserves_redactable_paths() {
        let snapshot = sample_human_workflow_snapshot();
        let mut value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "human",
        )
        .unwrap();
        redact_local_paths_in_value(&mut value);
        let rendered = serde_json::to_string(&value).unwrap();
        assert!(rendered.contains("<local-path>"));
    }

    #[test]
    fn dispatch_workflow_status_rejects_phase_and_filter_mix() {
        let error = dispatch_workflow_status(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &[],
            &StructuralPriorLearningState::default(),
            WorkflowStatusDispatchInput {
                phase: Some("human"),
                actionable_only: true,
                conflicts_only: false,
                latest_promotable: false,
                hard_block_only: false,
                hard_block_reason: None,
                limit: None,
                output_format: "json",
                stable: false,
            },
            WorkflowStatusBootstrapInput {
                symbol: "NQ",
                state_dir: "/tmp/state",
                detected_tomac_root: None,
                multi_timeframe_clean_root: None,
                tomac_root_placeholder: "<tomac-root>".to_string(),
            },
        )
        .unwrap_err();

        assert!(error
            .to_string()
            .contains("phase and filter flags are mutually exclusive"));
    }

    #[test]
    fn dispatch_workflow_status_rejects_multiple_artifact_filters() {
        let error = dispatch_workflow_status(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &[],
            &StructuralPriorLearningState::default(),
            WorkflowStatusDispatchInput {
                phase: None,
                actionable_only: true,
                conflicts_only: true,
                latest_promotable: false,
                hard_block_only: false,
                hard_block_reason: None,
                limit: None,
                output_format: "json",
                stable: false,
            },
            WorkflowStatusBootstrapInput {
                symbol: "NQ",
                state_dir: "/tmp/state",
                detected_tomac_root: None,
                multi_timeframe_clean_root: None,
                tomac_root_placeholder: "<tomac-root>".to_string(),
            },
        )
        .unwrap_err();

        assert!(error
            .to_string()
            .contains("accepts at most one artifact filter flag"));
    }

    #[test]
    fn normalize_workflow_status_value_for_stability_removes_timestamp_like_fields() {
        let mut value = serde_json::json!({
            "generated_at": "2024-01-01T00:00:00Z",
            "timestamp": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "last_updated_at": "2024-01-01T00:00:00Z",
            "fetched_at": "2024-01-01T00:00:00Z",
            "kept": "yes",
            "nested": {
                "generated_at": "2024-01-01T00:00:00Z",
                "kept": "still-here"
            },
            "items": [
                {
                    "generated_at": "2024-01-01T00:00:00Z",
                    "kept": 1
                }
            ]
        });

        normalize_workflow_status_value_for_stability(&mut value);

        assert!(value.get("generated_at").is_none());
        assert!(value.get("timestamp").is_none());
        assert!(value.get("updated_at").is_none());
        assert!(value.get("last_updated_at").is_none());
        assert!(value.get("fetched_at").is_none());
        assert_eq!(value["kept"], "yes");
        assert!(value["nested"].get("generated_at").is_none());
        assert_eq!(value["nested"]["kept"], "still-here");
        assert!(value["items"][0].get("generated_at").is_none());
        assert_eq!(value["items"][0]["kept"], 1);
    }

    #[test]
    fn human_workflow_status_view_exposes_candidates() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_human_workflow_status_view(&snapshot, &[]);
        assert_eq!(value["symbol"], "NQ");
        assert_eq!(value["current_status"]["focus_phase"], "update");
        assert_eq!(value["pda_cluster_label"], "cluster_1");
        assert_eq!(value["hard_block"]["active"], true);
        assert_eq!(value["hard_block"]["status"], "action_blocked");
        assert_eq!(
            value["hard_block"]["reason"],
            "user_selected_historical_data_missing"
        );
        assert!(value["hard_block"]["human_action"]
            .as_str()
            .unwrap()
            .contains("Ask the user to choose the historical dataset"));
        assert!(value["what_you_should_do_now"]
            .as_str()
            .unwrap()
            .contains("Ask the user to choose the historical dataset"));
        assert_eq!(value["historical_data_candidates"][0], "/tmp/a.json");
        assert_eq!(value["ensemble_consensus"]["final_action"], "observe");
        assert_eq!(value["ensemble_consensus"]["hard_block"]["active"], true);
        assert_eq!(
            value["ensemble_consensus"]["hard_block"]["reason"],
            "user_selected_historical_data_missing"
        );
    }

    #[test]
    fn jump_workflow_summaries_surface_calibration_gate() {
        let snapshot = sample_human_workflow_snapshot();
        assert_eq!(
            jump_model_workflow_summary(&snapshot).as_deref(),
            Some(
                "jump_model active_state=jump_transition confidence=0.500 transition_risk=0.500; jump_calibration_gate outcome=accepted sample_count=4 cooldown_status=ready"
            )
        );
        assert_eq!(
            jump_calibration_gate_workflow_summary(&snapshot).as_deref(),
            Some("jump_calibration_gate outcome=accepted sample_count=4 cooldown_status=ready")
        );
    }

    #[test]
    fn workflow_status_human_view_prefers_persisted_scorecards() {
        let snapshot = sample_human_workflow_snapshot();
        let persisted = vec![EnsembleExecutorScorecard {
            executor: "xgboost_file".to_string(),
            latest_weight_hint: Some(0.72),
            ..EnsembleExecutorScorecard::default()
        }];
        let value = build_human_workflow_status_view(&snapshot, &persisted);
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecards"][0]["executor"],
            "xgboost_file"
        );
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecard_source"],
            "persisted"
        );
    }

    #[test]
    fn human_workflow_status_view_exposes_human_summary_fields() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_human_workflow_status_view(&snapshot, &[]);
        assert_eq!(
            value["summary_line"],
            "NQ | update | action_blocked | pda_cluster=cluster_1 | duration=negative_binomial | remaining_bars=2.50"
        );
        assert_eq!(
            value["next_action_line"],
            "Next: Ask the user to choose the historical dataset. Please choose one historical data path for the next research/backtest run: /tmp/a.json, /tmp/b.json Reply with one path from the list, or paste another valid file path. Candidates: /tmp/a.json, /tmp/b.json Then run: ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state"
        );
        assert_eq!(
            value["blocking_line"],
            "Block: user_selected_historical_data_missing"
        );
        assert_eq!(
            value["phase_summary_line"],
            "Latest: update | entry=medium gate=pass_neutralized quality=0.500"
        );
        assert_eq!(value["hybrid_duration_model"], "negative_binomial");
        assert_eq!(value["hybrid_remaining_expected_bars"], "2.50");
    }

    #[test]
    fn human_workflow_status_next_line_does_not_duplicate_next_prefix() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "DEMO".to_string();
        snapshot.current_focus_phase = "research".to_string();
        snapshot.recommended_next_command =
            "ict-engine factor-research --symbol DEMO --backend native".to_string();
        snapshot.latest_research = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            phase_summary: "research ready".to_string(),
            recommended_next_command: snapshot.recommended_next_command.clone(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });

        let value = build_human_workflow_status_view(&snapshot, &[]);

        assert_eq!(
            value["next_action_line"],
            "Next: ict-engine factor-research --symbol DEMO --backend native"
        );
    }

    #[test]
    fn human_workflow_status_hides_unavailable_pre_bayes_gate_sentinel() {
        let snapshot = WorkflowSnapshot {
            symbol: "DEMO".to_string(),
            current_focus_phase: "research".to_string(),
            blocking_truth: crate::state::WorkflowBlockingTruth {
                status: "pass_neutralized".to_string(),
                ..crate::state::WorkflowBlockingTruth::default()
            },
            latest_research: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "research".to_string(),
                phase_summary: "research_ready".to_string(),
                pre_bayes_gate_status: "pre_bayes_gate_unavailable".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_human_workflow_status_view(&snapshot, &[]);

        assert_eq!(
            value["phase_summary_line"],
            "Latest: research | research_ready"
        );
        assert!(!value["phase_summary_line"]
            .as_str()
            .unwrap()
            .contains("pre_bayes_gate_unavailable"));
    }

    #[test]
    fn human_workflow_status_compacts_research_phase_summary() {
        let snapshot = WorkflowSnapshot {
            symbol: "DEMO".to_string(),
            current_focus_phase: "research".to_string(),
            latest_research: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "research".to_string(),
                phase_summary: "objective=expansion_manipulation best_factor=Some(\"trend_momentum\") aggregate_return=0.0017 feedback_applied=46 credibility=conformal_credibility:unavailable mtf_source=primary_only execution_gate=execution_observe_only".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_human_workflow_status_view(&snapshot, &[]);
        assert_eq!(
            value["phase_summary_line"],
            "Latest: research | objective=expansion_manipulation best_factor=trend_momentum aggregate_return=0.0017 feedback_applied=46 execution_gate=execution_observe_only"
        );
    }

    #[test]
    fn human_workflow_status_empty_state_uses_explicit_no_state_contract() {
        let value = build_human_workflow_status_view(&WorkflowSnapshot::default(), &[]);
        assert_eq!(value["status"], "no_workflow_state");
        assert_eq!(value["current_status"]["focus_phase"], "workflow_status");
        assert_eq!(
            value["current_status"]["blocking_status"],
            "no_workflow_state"
        );
        assert_eq!(value["latest_stage"]["phase"], "no_workflow_state");
        assert_eq!(
            value["latest_stage"]["summary_short"],
            "No workflow phase summary available yet."
        );
    }

    #[test]
    fn human_workflow_status_prefers_newest_phase_over_fixed_update_priority() {
        let snapshot = WorkflowSnapshot {
            latest_update: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "update".to_string(),
                timestamp: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                phase_summary: "older_update_summary".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_research: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "research".to_string(),
                timestamp: Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap(),
                phase_summary: "newer_research_summary".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_human_workflow_status_view(&snapshot, &[]);

        assert_eq!(value["latest_stage"]["phase"], "research");
        assert_eq!(value["latest_stage"]["summary"], "newer_research_summary");
    }

    #[test]
    fn agent_workflow_status_empty_state_uses_explicit_no_state_contract() {
        let value = build_agent_workflow_status_view(&WorkflowSnapshot::default(), &[]);
        assert_eq!(value["status"], "no_workflow_state");
        assert_eq!(value["latest_phase"], "no_workflow_state");
        assert_eq!(value["blocking_status"], "no_workflow_state");
        assert_eq!(value["blocking_reason"], "no_workflow_state");
        assert!(value["next_command"].is_null());
        assert_eq!(value["next_step"]["action_type"], "none");
    }

    #[test]
    fn agent_workflow_status_view_exposes_relevant_provider_support() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            current_focus_phase: "analyze_live".to_string(),
            current_focus_reason: "provider_runtime_required".to_string(),
            blocking_truth: crate::state::WorkflowBlockingTruth {
                status: "blocked".to_string(),
                reason: "provider_runtime_required".to_string(),
                next_command: "ict-engine analyze-live --symbol NQ --futures-symbol NQ=F --spot-symbol QQQ --options-symbol QQQ --futures-backend openalice --aux-backend nofx".to_string(),
                ..crate::state::WorkflowBlockingTruth::default()
            },
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze_live".to_string(),
                phase_summary: "live_provider_runtime_pending".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );

        assert_eq!(value["provider_support"]["active"], true);
        assert_eq!(value["provider_support"]["profile_id"], "workflow_auto");
        assert_eq!(value["provider_support"]["pending_providers"][0], "nofx");
        assert!(value["provider_support"]["install_prompts"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item.as_str().unwrap().contains("zero-config openbb")));
    }

    #[test]
    fn human_workflow_status_view_adds_provider_line_for_missing_runtime() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            current_focus_phase: "analyze_live".to_string(),
            current_focus_reason: "provider_runtime_required".to_string(),
            recommended_next_command: "ict-engine analyze-live --symbol NQ --futures-symbol NQ=F --spot-symbol QQQ --options-symbol QQQ --futures-backend openalice --aux-backend nofx".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze_live".to_string(),
                phase_summary: "live_provider_runtime_pending".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );

        assert!(value["provider_line"]
            .as_str()
            .unwrap()
            .contains("openalice"));
        assert!(value["provider_line"].as_str().unwrap().contains("nofx"));
        assert!(value["provider_line"]
            .as_str()
            .unwrap()
            .contains("zero-config openbb"));
        assert_eq!(
            value["provider_support"]["workflow_support"]["active"],
            true
        );
    }

    #[test]
    fn workflow_status_phase_structural_node_exposes_current_blocker() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-node",
        )
        .unwrap();

        assert_eq!(value["node_family"], "data_selection_gate");
        assert_eq!(value["node_label"], "user_selected_historical_data_missing");
        assert!(value["supporting_evidence"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item.as_str().unwrap().contains("need user choice")));
        assert!(value["recommended_next_step"]["execution_contract"].is_null());
    }

    #[test]
    fn structural_node_prefers_active_regime_label_over_focus_reason_when_actionable() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.current_focus_reason =
            "market_policy=NQ hostile_liquidity_penalty=0.100 favorable_liquidity_bonus=0.040"
                .to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-node",
        )
        .unwrap();

        assert_eq!(value["node_family"], "belief_regime_node");
        assert_eq!(value["node_label"], "trend");
        assert_eq!(value["node_id"], "NQ:belief_regime_node:trend");
    }

    #[test]
    fn structural_node_prefers_posterior_probability_key_when_active_regime_string_is_dirty() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime:
                "market_policy=NQ hostile_liquidity_penalty=0.100 favorable_liquidity_bonus=0.040"
                    .to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-node",
        )
        .unwrap();

        assert_eq!(value["node_label"], "trend");
        assert_eq!(value["node_id"], "NQ:belief_regime_node:trend");
    }

    #[test]
    fn structural_node_falls_back_to_latest_analyze_anchor_when_latest_ensemble_vote_is_non_structural()
     {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "backtest".to_string();
        snapshot.current_focus_reason = "no_previous_run".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                "bull".to_string(),
            )]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.66),
                    ("range".to_string(), 0.24),
                    ("transition".to_string(), 0.10),
                ]),
            )]),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:non-structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "factor-research".to_string(),
            source_run_id: Some("run-non-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "observe_only".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=observe_only".to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.51,
            consensus_strength: 0.49,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: Some("fallback".to_string()),
            posterior_fingerprint: "fp-non-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "research_iteration".to_string(),
            posterior_confidence: Some(0.51),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("fallback".to_string(), 0.51),
                ("research_iteration".to_string(), 0.49),
            ]),
            posterior_evidence: vec!["objective=generic".to_string()],
        });

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-node",
        )
        .unwrap();

        assert_eq!(value["node_family"], "belief_regime_node");
        assert_eq!(value["node_label"], "trend");
        assert_eq!(value["node_id"], "NQ:belief_regime_node:trend");
    }

    #[test]
    fn structural_node_uses_duration_prior_to_adjust_posterior_confidence() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let mut structural_prior_state = crate::state::StructuralPriorLearningState::default();
        structural_prior_state.node_duration_priors.insert(
            "NQ:belief_regime_node:trend".to_string(),
            crate::state::StructuralNodeDurationPrior {
                observations: 6,
                streak_count: 3,
                weighted_streak_mass: 2.4,
                total_streak_length: 6,
                avg_streak_length: 2.0,
                max_streak_length: 3,
                last_streak_length: 3,
                persistence_prior: 0.9,
                last_recommended_at: Some("2026-04-30T03:00:00Z".to_string()),
            },
        );

        let value = build_workflow_status_phase_value_with_structural_prior_state(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            &structural_prior_state,
            "structural-node",
        )
        .unwrap();

        assert_eq!(value["node_id"], "NQ:belief_regime_node:trend");
        assert!(value["posterior_confidence"].as_f64().unwrap() > 0.72);
        assert_eq!(
            value["belief_posterior"].as_f64().unwrap(),
            value["posterior_confidence"].as_f64().unwrap()
        );
    }

    #[test]
    fn structural_playbook_falls_back_to_latest_analyze_anchor_when_latest_ensemble_vote_is_non_structural(
    ) {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "backtest".to_string();
        snapshot.current_focus_reason = "no_previous_run".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                "bull".to_string(),
            )]),
            pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                "market_regime".to_string(),
                std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.66),
                    ("range".to_string(), 0.24),
                    ("transition".to_string(), 0.10),
                ]),
            )]),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:non-structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "factor-research".to_string(),
            source_run_id: Some("run-non-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "observe_only".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=observe_only".to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.51,
            consensus_strength: 0.49,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: Some("fallback".to_string()),
            posterior_fingerprint: "fp-non-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "research_iteration".to_string(),
            posterior_confidence: Some(0.51),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("fallback".to_string(), 0.51),
                ("research_iteration".to_string(), 0.49),
            ]),
            posterior_evidence: vec!["objective=generic".to_string()],
        });

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-playbook",
        )
        .unwrap();

        assert_eq!(value["node"]["node_id"], "NQ:belief_regime_node:trend");
        assert_eq!(
            value["branch_set"]["branches"][0]["branch_label"],
            "trend_follow_through"
        );
        assert_eq!(
            value["scenario_playbook"]["scenarios"][0]["scenario_label"],
            "trend_follow_through"
        );
    }

    #[test]
    fn structural_playbook_prefers_canonical_analyze_ensemble_surface_when_latest_vote_is_raw_analyze() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            current_focus_phase: "analyze".to_string(),
            recommended_next_command:
                "ict-engine workflow-status --symbol NQ --phase human-next".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                run_id: "analyze:1".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    "trend".to_string(),
                )]),
                pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    std::collections::BTreeMap::from([
                        ("trend".to_string(), 0.78),
                        ("range".to_string(), 0.14),
                        ("transition".to_string(), 0.08),
                    ]),
                )]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_ensemble_vote: Some(EnsembleVoteRecord {
                artifact_id: "ensemble-vote:analyze:test".to_string(),
                generated_at: Utc::now(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                provenance: RunProvenance::default(),
                dataset_comparability: DatasetComparability::default(),
                ensemble_version: "ensemble-audit-v2".to_string(),
                final_action: "execute_follow_through".to_string(),
                recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                    .to_string(),
                human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                    .to_string(),
                hard_block: EnsembleHardBlockArtifact::default(),
                confidence: 0.55,
                consensus_strength: 0.55,
                disagreement_flags: Vec::new(),
                executor_summaries: Vec::new(),
                split_explanations: Vec::new(),
                executor_scorecards: Vec::new(),
                executor_scorecards_source: None,
                posterior_fingerprint: "fp-raw".to_string(),
                posterior_normalization_status: "normalized".to_string(),
                posterior_active_regime: "bull".to_string(),
                posterior_confidence: Some(0.55),
                posterior_probabilities: std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.55),
                    ("range".to_string(), 0.30),
                    ("transition".to_string(), 0.15),
                ]),
                posterior_evidence: vec!["raw".to_string()],
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-playbook",
        )
        .unwrap();

        assert_eq!(value["node"]["node_id"], "NQ:belief_regime_node:trend");
        assert_eq!(value["node"]["posterior_confidence"], 0.78);
        assert_eq!(
            value["branch_set"]["branches"][0]["posterior_probability"],
            0.78
        );
        assert!(value["node"]["market_context"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item.as_str().unwrap().contains("posterior_active_regime=trend")));
    }

    #[test]
    fn workflow_status_phase_structural_playbook_surfaces_selected_profile_contracts() {
        let snapshot = WorkflowSnapshot::default();
        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface_with_profile(),
            &[],
            "structural-playbook",
        )
        .unwrap();

        assert_eq!(value["selected_profile_id"], "thrill3r_nq_closed_loop_v1");
        assert!(value["selected_profile_data_contracts"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item
                .as_str()
                .unwrap()
                .contains("Tomac cleaned multi-timeframe futures root")));
        assert!(value["path_plan"]["paths"]
            .as_array()
            .unwrap()
            .iter()
            .all(|path| path.get("path_id").is_some()));
    }

    #[test]
    fn workflow_status_phase_structural_playbook_exposes_recommended_path_bundle() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-playbook",
        )
        .unwrap();

        assert_eq!(value["recommended_path_bundle"]["rank"], 1);
        assert!(value["recommended_path_bundle"]["why_this_path"]
            .as_str()
            .unwrap()
            .contains("posterior"));
        assert_eq!(
            value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
    }

    #[test]
    fn workflow_status_phase_structural_branches_use_posterior_probabilities() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "structural-branches",
        )
        .unwrap();

        assert_eq!(value["branches"].as_array().unwrap().len(), 3);
        assert_eq!(value["branches"][0]["branch_label"], "trend_follow_through");
        assert_eq!(value["branches"][0]["posterior_probability"], 0.72);
    }

    #[test]
    fn structural_branches_use_transition_priors_from_latest_structural_feedback() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_update = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "update".to_string(),
            structural_feedback: Some(crate::state::StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: "rec-prev".to_string(),
                recommended_at: "2026-04-30T01:00:00Z".to_string(),
                node_id: "NQ:belief_regime_node:trend".to_string(),
                branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                scenario_id:
                    "scenario:NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                path_id:
                    "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
                        .to_string(),
                followed_path: true,
                exit_reason: Some("target_hit".to_string()),
                notes: None,
            }),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let mut structural_prior_state = crate::state::StructuralPriorLearningState::default();
        structural_prior_state.branch_transition_priors.insert(
            "NQ:belief_regime_node:trend:trend_follow_through=>NQ:belief_regime_node:trend:transition_confirmation".to_string(),
            crate::state::StructuralBranchTransitionPrior {
                from_node_id: "NQ:belief_regime_node:trend".to_string(),
                to_node_id: "NQ:belief_regime_node:trend".to_string(),
                from_branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                to_branch_id: "NQ:belief_regime_node:trend:transition_confirmation".to_string(),
                observations: 3,
                weighted_observation_mass: 2.4,
                wins: 2,
                losses: 1,
                invalidated: 0,
                transition_prior: 0.8,
                last_recommended_at: Some("2026-04-30T02:00:00Z".to_string()),
            },
        );

        let value = build_workflow_status_phase_value_with_structural_prior_state(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            &structural_prior_state,
            "structural-branches",
        )
        .unwrap();

        let branch = value["branches"]
            .as_array()
            .unwrap()
            .iter()
            .find(|item| item["branch_label"] == "transition_confirmation")
            .expect("transition branch");
        assert_eq!(branch["transition_prior"], 0.8);
        assert_eq!(branch["transition_weighted_observation_mass"], 2.4);
        assert!(branch["prior_probability"].as_f64().unwrap() > 0.6);
        assert!(branch["posterior_probability"].as_f64().unwrap() > 0.10);
    }

    #[test]
    fn workflow_status_phase_ensemble_vote_prefers_canonical_analyze_regime_surface() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                run_id: "analyze:1".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    "trend".to_string(),
                )]),
                pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    std::collections::BTreeMap::from([
                        ("trend".to_string(), 0.78),
                        ("range".to_string(), 0.14),
                        ("transition".to_string(), 0.08),
                    ]),
                )]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_ensemble_vote: Some(EnsembleVoteRecord {
                artifact_id: "ensemble-vote:analyze:test".to_string(),
                generated_at: Utc::now(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                provenance: RunProvenance::default(),
                dataset_comparability: DatasetComparability::default(),
                ensemble_version: "ensemble-audit-v2".to_string(),
                final_action: "execute_follow_through".to_string(),
                recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                    .to_string(),
                human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                    .to_string(),
                hard_block: EnsembleHardBlockArtifact::default(),
                confidence: 0.55,
                consensus_strength: 0.55,
                disagreement_flags: Vec::new(),
                executor_summaries: Vec::new(),
                split_explanations: Vec::new(),
                executor_scorecards: Vec::new(),
                executor_scorecards_source: None,
                posterior_fingerprint: "fp-raw".to_string(),
                posterior_normalization_status: "normalized".to_string(),
                posterior_active_regime: "bull".to_string(),
                posterior_confidence: Some(0.55),
                posterior_probabilities: std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.55),
                    ("range".to_string(), 0.30),
                    ("transition".to_string(), 0.15),
                ]),
                posterior_evidence: vec!["raw".to_string()],
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "ensemble-vote",
        )
        .unwrap();

        assert_eq!(value["posterior_active_regime"], "trend");
        assert_eq!(value["posterior_confidence"], 0.78);
        assert_eq!(value["posterior_probabilities"]["trend"], 0.78);
    }

    #[test]
    fn workflow_status_phase_ensemble_vote_prefers_canonical_research_regime_surface() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_research: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "research".to_string(),
                run_id: "research:1".to_string(),
                canonical_structural_active_regime: Some("range".to_string()),
                canonical_structural_confidence: Some(0.61),
                canonical_structural_probabilities: std::collections::BTreeMap::from([
                    ("trend".to_string(), 0.21),
                    ("range".to_string(), 0.61),
                    ("transition".to_string(), 0.18),
                ]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_ensemble_vote: Some(EnsembleVoteRecord {
                artifact_id: "ensemble-vote:research:test".to_string(),
                generated_at: Utc::now(),
                symbol: "NQ".to_string(),
                source_phase: "research".to_string(),
                source_run_id: Some("research:1".to_string()),
                provenance: RunProvenance::default(),
                dataset_comparability: DatasetComparability::default(),
                ensemble_version: "ensemble-audit-v2".to_string(),
                final_action: "observe".to_string(),
                recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                    .to_string(),
                human_next_triage: "hard_blocked=false ensemble_action=observe".to_string(),
                hard_block: EnsembleHardBlockArtifact::default(),
                confidence: 0.20,
                consensus_strength: 0.20,
                disagreement_flags: Vec::new(),
                executor_summaries: Vec::new(),
                split_explanations: Vec::new(),
                executor_scorecards: Vec::new(),
                executor_scorecards_source: None,
                posterior_fingerprint: "fp-raw".to_string(),
                posterior_normalization_status: "normalized".to_string(),
                posterior_active_regime: "bull".to_string(),
                posterior_confidence: Some(0.20),
                posterior_probabilities: std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.20),
                    ("range".to_string(), 0.60),
                    ("transition".to_string(), 0.20),
                ]),
                posterior_evidence: vec!["raw".to_string()],
            }),
            ..WorkflowSnapshot::default()
        };

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            "ensemble-vote",
        )
        .unwrap();

        assert_eq!(value["posterior_active_regime"], "range");
        assert_eq!(value["posterior_confidence"], 0.61);
        assert_eq!(value["posterior_probabilities"]["range"], 0.61);
    }

    #[test]
    fn workflow_status_phase_structural_feedback_template_exposes_stable_ids() {
        let snapshot = sample_human_workflow_snapshot();
        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface_with_profile(),
            &[],
            "structural-feedback-template",
        )
        .unwrap();

        assert!(value["recommendation_id"]
            .as_str()
            .unwrap()
            .contains("structural-feedback"));
        assert!(value["node_id"].as_str().unwrap().contains("NQ"));
        assert!(value["branch_id"]
            .as_str()
            .unwrap()
            .contains("choose_historical_dataset"));
        assert!(value["feedback_fields"]
            .as_array()
            .unwrap()
            .iter()
            .any(|field| field["field_id"] == "realized_outcome"));
        assert!(value["allowed_outcomes"]
            .as_array()
            .unwrap()
            .iter()
            .any(|item| item.as_str().unwrap() == "invalidated"));
    }

    #[test]
    fn workflow_status_phase_structural_path_history_aggregates_feedback() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = sample_structural_feedback_history()[1]
                .structural_feedback
                .clone();
        }
        let history = sample_structural_feedback_history();
        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-path-history",
        )
        .unwrap();

        assert_eq!(value["summary"]["total_records"], 2);
        assert_eq!(value["summary"]["distinct_paths"], 1);
        assert_eq!(
            value["paths"][0]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert_eq!(value["paths"][0]["wins"], 1);
        assert_eq!(value["paths"][0]["invalidated"], 1);
    }

    #[test]
    fn workflow_status_phase_structural_path_outcome_summary_is_token_friendly() {
        let history = sample_structural_feedback_history();
        let value = build_workflow_status_phase_value(
            &WorkflowSnapshot::default(),
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-path-outcome-summary",
        )
        .unwrap();

        assert_eq!(value["total_records"], 2);
        assert_eq!(value["distinct_paths"], 1);
    }

    #[test]
    fn structural_playbook_uses_history_to_raise_path_prior() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-paths",
        )
        .unwrap();

        assert_eq!(
            value["paths"][0]["historical_total_records"],
            3
        );
        assert!(value["paths"][0]["path_prior"].as_f64().unwrap() > 0.5);
        assert!(value["paths"][0]["composite_preference_score"]
            .as_f64()
            .unwrap()
            >= value["paths"][0]["path_posterior"].as_f64().unwrap() * 0.7);
    }

    #[test]
    fn structural_playbook_uses_persisted_structural_prior_state_for_path_prior() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let mut structural_prior_state = crate::state::StructuralPriorLearningState::default();
        structural_prior_state.paths.insert(
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary".to_string(),
            crate::state::StructuralPriorStats {
                observations: 4,
                followed_count: 4,
                wins: 3,
                losses: 0,
                breakevens: 1,
                invalidated: 0,
                abandoned: 0,
                not_followed: 0,
                avg_pnl: 0.028,
                weighted_followed_mass: 4.0,
                weighted_success_mass: 3.5,
                weighted_failure_mass: 0.5,
                weighted_invalidation_mass: 0.0,
                smoothed_prior: 0.75,
                source_panel_summaries: std::collections::BTreeMap::new(),
                last_offline_seed_source: None,
            },
        );

        let value = build_workflow_status_phase_value_with_structural_prior_state(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            &structural_prior_state,
            "structural-paths",
        )
        .unwrap();

        assert_eq!(value["paths"][0]["historical_total_records"], 4);
        assert_eq!(value["paths"][0]["historical_followed_count"], 4);
        assert_eq!(value["paths"][0]["path_prior"], 0.82);
    }

    #[test]
    fn structural_playbook_uses_history_to_adjust_branch_and_scenario_scores() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let branches = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-branches",
        )
        .unwrap();
        let scenarios = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-scenarios",
        )
        .unwrap();

        assert_eq!(branches["branches"][0]["historical_total_records"], 3);
        assert_eq!(branches["branches"][0]["historical_followed_count"], 3);
        assert!(
            branches["branches"][0]["prior_probability"]
                .as_f64()
                .unwrap()
                < branches["branches"][0]["posterior_probability"]
                    .as_f64()
                    .unwrap()
        );
        assert_eq!(scenarios["scenarios"][0]["historical_total_records"], 3);
        assert_eq!(scenarios["scenarios"][0]["historical_followed_count"], 3);
        assert!(
            scenarios["scenarios"][0]["composite_scenario_score"]
                .as_f64()
                .unwrap()
                < scenarios["scenarios"][0]["posterior_probability"]
                    .as_f64()
                    .unwrap()
        );
    }

    #[test]
    fn workflow_status_phase_structural_branch_history_aggregates_feedback() {
        let history = sample_structural_feedback_history();
        let value = build_workflow_status_phase_value(
            &WorkflowSnapshot::default(),
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-branch-history",
        )
        .unwrap();

        assert_eq!(value["summary"]["total_records"], 2);
        assert_eq!(value["summary"]["distinct_entities"], 1);
        assert_eq!(
            value["branches"][0]["branch_id"],
            "NQ:belief_regime_node:trend:trend_follow_through"
        );
        assert_eq!(value["branches"][0]["wins"], 1);
    }

    #[test]
    fn workflow_status_phase_structural_experience_priors_tracks_current_lineage() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        if let Some(analyze) = snapshot.latest_analyze.as_mut() {
            analyze.structural_feedback = sample_structural_feedback_history()[1]
                .structural_feedback
                .clone();
        }
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];
        let mut structural_prior_state = crate::state::StructuralPriorLearningState::default();
        structural_prior_state.paths.insert(
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary".to_string(),
            crate::state::StructuralPriorStats {
                observations: 3,
                followed_count: 3,
                wins: 2,
                losses: 1,
                breakevens: 0,
                invalidated: 0,
                abandoned: 0,
                not_followed: 0,
                avg_pnl: 0.01,
                weighted_followed_mass: 2.05,
                weighted_success_mass: 1.30,
                weighted_failure_mass: 0.75,
                weighted_invalidation_mass: 0.0,
                smoothed_prior: 0.5483870968,
                source_panel_summaries: std::collections::BTreeMap::from([
                    (
                        "analyze".to_string(),
                        crate::state::StructuralPriorSourceSummary {
                            observations: 1,
                            followed_count: 1,
                            wins: 1,
                            losses: 0,
                            breakevens: 0,
                            invalidated: 0,
                            abandoned: 0,
                            not_followed: 0,
                            avg_pnl: 0.01,
                            weighted_followed_mass: 0.30,
                            weighted_success_mass: 0.30,
                            weighted_failure_mass: 0.0,
                            weighted_invalidation_mass: 0.0,
                            smoothed_prior: 0.5652173913,
                            last_tempering_coefficient: None,
                            last_recommendation_id: Some("rec-analyze".to_string()),
                            last_recommended_at: Some("2026-04-30T00:00:00Z".to_string()),
                            last_note: Some("analyze_run_structural_prior_seed".to_string()),
                        },
                    ),
                    (
                        "backtest".to_string(),
                        crate::state::StructuralPriorSourceSummary {
                            observations: 2,
                            followed_count: 2,
                            wins: 1,
                            losses: 1,
                            breakevens: 0,
                            invalidated: 0,
                            abandoned: 0,
                            not_followed: 0,
                            avg_pnl: 0.01,
                            weighted_followed_mass: 1.50,
                            weighted_success_mass: 0.75,
                            weighted_failure_mass: 0.75,
                            weighted_invalidation_mass: 0.0,
                            smoothed_prior: 0.5,
                            last_tempering_coefficient: None,
                            last_recommendation_id: Some("rec-backtest".to_string()),
                            last_recommended_at: Some("2026-04-30T01:00:00Z".to_string()),
                            last_note: Some("backtest_run_structural_prior_seed".to_string()),
                        },
                    ),
                ]),
                last_offline_seed_source: Some("backtest".to_string()),
            },
        );
        structural_prior_state.node_duration_priors.insert(
            "NQ:belief_regime_node:trend".to_string(),
            crate::state::StructuralNodeDurationPrior {
                observations: 3,
                streak_count: 2,
                weighted_streak_mass: 1.85,
                total_streak_length: 3,
                avg_streak_length: 1.5,
                max_streak_length: 2,
                last_streak_length: 1,
                persistence_prior: 0.6,
                last_recommended_at: Some("2026-04-30T03:00:00Z".to_string()),
            },
        );

        let value = build_workflow_status_phase_value_with_structural_prior_state(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            &structural_prior_state,
            "structural-experience-priors",
        )
        .unwrap();

        assert_eq!(value["symbol"], "NQ");
        assert_eq!(
            value["path"]["entity_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert_eq!(value["path"]["historical_total_records"], 3);
        assert!(value["path"]["experience_prior"].as_f64().unwrap() > 0.5);
        assert_eq!(value["path"]["source_panel_count"], 2);
        assert_eq!(value["path"]["last_offline_seed_source"], "backtest");
        assert_eq!(value["path"]["dominant_source_panel"], "backtest");
        assert!(value["path"]["dominant_source_share"]
            .as_f64()
            .unwrap()
            > 0.80);
        assert_eq!(value["path"]["dominant_source_prior"], 0.5);
        assert_eq!(value["node"]["duration_streak_count"], 2);
        assert_eq!(value["node"]["duration_avg_streak_length"], 1.5);
        assert_eq!(value["node"]["duration_persistence_prior"], 0.6);
        assert_eq!(value["node"]["duration_weighted_streak_mass"], 1.85);
        assert_eq!(
            value["branch"]["entity_id"],
            "NQ:belief_regime_node:trend:trend_follow_through"
        );
        assert!(value["branch"]["composite_score"].as_f64().unwrap() > 0.6);
        assert_eq!(
            value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );

        let blocked_value = build_workflow_status_phase_value_with_structural_prior_state(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
            &structural_prior_state,
            "structural-experience-priors",
        )
        .unwrap();
        assert!(blocked_value["recommended_next_step"]["execution_contract"].is_null());
    }

    #[test]
    fn structural_experience_prior_surface_prefers_panel_derived_prior_over_stale_aggregate_prior() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let mut structural_prior_state = crate::state::StructuralPriorLearningState::default();
        structural_prior_state.paths.insert(
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary".to_string(),
            crate::state::StructuralPriorStats {
                observations: 3,
                followed_count: 3,
                wins: 2,
                losses: 1,
                breakevens: 0,
                invalidated: 0,
                abandoned: 0,
                not_followed: 0,
                avg_pnl: 0.01,
                weighted_followed_mass: 1.8,
                weighted_success_mass: 0.9,
                weighted_failure_mass: 0.9,
                weighted_invalidation_mass: 0.0,
                smoothed_prior: 0.95,
                source_panel_summaries: std::collections::BTreeMap::from([
                    (
                        "analyze".to_string(),
                        crate::state::StructuralPriorSourceSummary {
                            observations: 1,
                            followed_count: 1,
                            wins: 1,
                            losses: 0,
                            breakevens: 0,
                            invalidated: 0,
                            abandoned: 0,
                            not_followed: 0,
                            avg_pnl: 0.01,
                            weighted_followed_mass: 0.3,
                            weighted_success_mass: 0.3,
                            weighted_failure_mass: 0.0,
                            weighted_invalidation_mass: 0.0,
                            smoothed_prior: 0.5652173913,
                            last_tempering_coefficient: None,
                            last_recommendation_id: None,
                            last_recommended_at: None,
                            last_note: None,
                        },
                    ),
                    (
                        "backtest".to_string(),
                        crate::state::StructuralPriorSourceSummary {
                            observations: 2,
                            followed_count: 2,
                            wins: 1,
                            losses: 1,
                            breakevens: 0,
                            invalidated: 0,
                            abandoned: 0,
                            not_followed: 0,
                            avg_pnl: 0.01,
                            weighted_followed_mass: 1.5,
                            weighted_success_mass: 0.6,
                            weighted_failure_mass: 0.9,
                            weighted_invalidation_mass: 0.0,
                            smoothed_prior: 0.4444444444,
                            last_tempering_coefficient: None,
                            last_recommendation_id: None,
                            last_recommended_at: None,
                            last_note: None,
                        },
                    ),
                ]),
                last_offline_seed_source: Some("backtest".to_string()),
            },
        );

        let value = build_workflow_status_phase_value_with_structural_prior_state(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
            &structural_prior_state,
            "structural-experience-priors",
        )
        .unwrap();

        let prior = value["path"]["experience_prior"].as_f64().unwrap();
        assert!(prior < 0.60);
        assert!(prior > 0.45);
    }

    #[test]
    fn workflow_status_phase_structural_top_path_candidates_ranks_paths() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-top-path-candidates",
        )
        .unwrap();

        assert_eq!(value["symbol"], "NQ");
        assert_eq!(value["candidate_count"], 3);
        assert_eq!(
            value["candidates"][0]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(value["candidates"][0]["composite_score"].as_f64().unwrap()
            >= value["candidates"][1]["composite_score"].as_f64().unwrap());
        assert!(value["candidates"][0]["experience_prior"].as_f64().unwrap() > 0.5);
    }

    #[test]
    fn workflow_status_phase_structural_top_path_candidates_exposes_recommended_next_step_contract() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-top-path-candidates",
        )
        .unwrap();

        assert_eq!(
            value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );

        let blocked_value = build_workflow_status_phase_value(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-top-path-candidates",
        )
        .unwrap();
        assert!(blocked_value["recommended_next_step"]["execution_contract"].is_null());
    }

    #[test]
    fn workflow_status_structural_detail_phases_share_recommended_next_step_contract() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];
        let phases = [
            "structural-node",
            "structural-branches",
            "structural-scenarios",
            "structural-paths",
            "structural-history-summary",
            "structural-feedback-template",
        ];

        for phase in phases {
            let value = build_workflow_status_phase_value(
                &snapshot,
                &[],
                &sample_provider_agent_surface(),
                &history,
                phase,
            )
            .unwrap();
            assert_eq!(
                value["recommended_next_step"]["execution_contract"]["path_id"],
                "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary",
                "phase={phase}"
            );
        }
    }

    #[test]
    fn workflow_status_phase_structural_recommended_path_bundle_is_token_friendly() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let value = build_workflow_status_phase_value(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
            "structural-recommended-path-bundle",
        )
        .unwrap();

        assert_eq!(value["symbol"], "NQ");
        assert_eq!(value["rank"], 1);
        assert_eq!(
            value["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(value["trigger_summary"].as_str().unwrap().contains("regime"));
        assert!(value["stop_summary"].as_str().unwrap().len() > 4);
        assert!(value["confirmation_summary"].as_str().unwrap().len() > 4);
        assert!(value["invalidation_summary"].as_str().unwrap().len() > 4);
        assert_eq!(
            value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
    }

    #[test]
    fn agent_workflow_status_view_exposes_latest_structural_feedback() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = Some(crate::state::StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: "structural-feedback:NQ:node:path".to_string(),
                recommended_at: "2026-04-29T00:00:00Z".to_string(),
                node_id: "NQ:belief_regime_node:trend".to_string(),
                branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                    .to_string(),
                path_id:
                    "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
                        .to_string(),
                followed_path: true,
                exit_reason: Some("target_hit".to_string()),
                notes: Some("user followed structural path".to_string()),
            });
        }

        let value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );

        assert_eq!(
            value["latest_structural_feedback"]["recommendation_id"],
            "structural-feedback:NQ:node:path"
        );
        assert_eq!(
            value["latest_structural_feedback"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
    }

    #[test]
    fn agent_workflow_status_view_exposes_structural_path_summary() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = sample_structural_feedback_history()[1]
                .structural_feedback
                .clone();
        }
        let history = sample_structural_feedback_history();

        let value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(
            value["structural_path_summary"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert_eq!(value["structural_path_summary"]["total_records"], 2);
        assert_eq!(value["structural_path_summary"]["invalidated"], 1);
    }

    #[test]
    fn agent_workflow_status_view_exposes_structural_history_summary() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = sample_structural_feedback_history()[1]
                .structural_feedback
                .clone();
        }
        let history = sample_structural_feedback_history();

        let value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(value["structural_history_summary"]["total_records"], 2);
        assert_eq!(value["structural_history_summary"]["distinct_paths"], 1);
        assert_eq!(
            value["structural_history_summary"]["latest_path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
    }

    #[test]
    fn agent_and_human_workflow_status_views_expose_experience_prior_surface() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = sample_structural_feedback_history()[1]
                .structural_feedback
                .clone();
        }
        let history = sample_structural_feedback_history();

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(
            agent_value["experience_prior_surface"]["path"]["entity_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert_eq!(
            agent_value["experience_prior_surface"]["path"]["historical_total_records"],
            2
        );
        assert!(human_value["experience_prior_line"]
            .as_str()
            .unwrap()
            .contains("path_prior="));
    }

    #[test]
    fn agent_and_human_workflow_status_views_expose_top_path_candidates() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(agent_value["top_path_candidates"][0]["rank"], 1);
        assert_eq!(
            agent_value["top_path_candidates"][0]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(human_value["top_path_candidates_line"]
            .as_str()
            .unwrap()
            .contains("trend_follow_through"));
    }

    #[test]
    fn agent_and_human_workflow_status_views_expose_recommended_path_bundle() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(agent_value["recommended_path_bundle"]["rank"], 1);
        assert_eq!(
            agent_value["recommended_path_bundle"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(agent_value["recommended_path_bundle"]["why_this_path"]
            .as_str()
            .unwrap()
            .contains("posterior"));
        assert!(human_value["recommended_path_line"]
            .as_str()
            .unwrap()
            .contains("trend_follow_through"));
    }

    #[test]
    fn agent_and_human_workflow_status_views_expose_recommended_path_contract() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(
            agent_value["recommended_path_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(agent_value["recommended_path_contract"]["why"]
            .as_str()
            .unwrap()
            .contains("posterior"));
        assert!(human_value["recommended_path_contract_line"]
            .as_str()
            .unwrap()
            .contains("trigger="));
        assert!(human_value["recommended_path_contract_line"]
            .as_str()
            .unwrap()
            .contains("stop="));
    }

    #[test]
    fn agent_and_human_workflow_status_views_prefer_canonical_analyze_ensemble_surface() {
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                run_id: "analyze:1".to_string(),
                pre_bayes_filtered_assignments: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    "trend".to_string(),
                )]),
                pre_bayes_soft_evidence: std::collections::BTreeMap::from([(
                    "market_regime".to_string(),
                    std::collections::BTreeMap::from([
                        ("trend".to_string(), 0.78),
                        ("range".to_string(), 0.14),
                        ("transition".to_string(), 0.08),
                    ]),
                )]),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_ensemble_vote: Some(EnsembleVoteRecord {
                artifact_id: "ensemble-vote:analyze:test".to_string(),
                generated_at: Utc::now(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                provenance: RunProvenance::default(),
                dataset_comparability: DatasetComparability::default(),
                ensemble_version: "ensemble-audit-v2".to_string(),
                final_action: "execute_follow_through".to_string(),
                recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                    .to_string(),
                human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                    .to_string(),
                hard_block: EnsembleHardBlockArtifact::default(),
                confidence: 0.55,
                consensus_strength: 0.55,
                disagreement_flags: Vec::new(),
                executor_summaries: Vec::new(),
                split_explanations: Vec::new(),
                executor_scorecards: Vec::new(),
                executor_scorecards_source: None,
                posterior_fingerprint: "fp-raw".to_string(),
                posterior_normalization_status: "normalized".to_string(),
                posterior_active_regime: "bull".to_string(),
                posterior_confidence: Some(0.55),
                posterior_probabilities: std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.55),
                    ("range".to_string(), 0.30),
                    ("transition".to_string(), 0.15),
                ]),
                posterior_evidence: vec!["raw".to_string()],
            }),
            ..WorkflowSnapshot::default()
        };

        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );
        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );

        assert_eq!(
            human_value["ensemble_consensus"]["posterior_active_regime"],
            "trend"
        );
        assert_eq!(human_value["ensemble_consensus"]["posterior_confidence"], 0.78);
        assert_eq!(agent_value["ensemble"]["confidence"], 0.78);
    }

    #[test]
    fn human_and_agent_workflow_status_inline_execution_contract_only_when_not_blocked() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(
            agent_value["next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert!(human_value["what_you_should_do_now"]
            .as_str()
            .unwrap()
            .contains("Execution contract:"));

        let blocked_human = build_human_workflow_status_view_with_provider_agent(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let blocked_agent = build_agent_workflow_status_view_with_provider_agent(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert!(!blocked_human["what_you_should_do_now"]
            .as_str()
            .unwrap()
            .contains("Execution contract:"));
        assert!(blocked_agent["next_step"]["execution_contract"].is_null());
    }

    #[test]
    fn human_and_agent_workflow_status_expose_recommended_next_step_contract() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.symbol = "NQ".to_string();
        snapshot.current_focus_phase = "analyze".to_string();
        snapshot.recommended_next_command =
            "ict-engine workflow-status --symbol NQ --phase human-next".to_string();
        snapshot.latest_analyze = Some(crate::state::WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            phase_summary: "belief regime available".to_string(),
            ..crate::state::WorkflowPhaseSnapshot::default()
        });
        snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
            artifact_id: "ensemble-vote:structural".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-structural".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2".to_string(),
            final_action: "execute_follow_through".to_string(),
            recommended_command: snapshot.recommended_next_command.clone(),
            human_next_triage: "hard_blocked=false ensemble_action=execute_follow_through"
                .to_string(),
            hard_block: EnsembleHardBlockArtifact::default(),
            confidence: 0.72,
            consensus_strength: 0.64,
            disagreement_flags: Vec::new(),
            executor_summaries: Vec::new(),
            split_explanations: Vec::new(),
            executor_scorecards: Vec::new(),
            executor_scorecards_source: None,
            posterior_fingerprint: "fp-structural".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "trend".to_string(),
            posterior_confidence: Some(0.72),
            posterior_probabilities: std::collections::BTreeMap::from([
                ("trend".to_string(), 0.72),
                ("range".to_string(), 0.18),
                ("transition".to_string(), 0.10),
            ]),
            posterior_evidence: vec!["mtf=aligned".to_string()],
        });
        let history = vec![
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[0].clone(),
            sample_structural_feedback_history()[1].clone(),
        ];

        let agent_value = build_agent_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let human_value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert_eq!(
            agent_value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );
        assert_eq!(
            human_value["recommended_next_step"]["execution_contract"]["path_id"],
            "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
        );

        let blocked_human = build_human_workflow_status_view_with_provider_agent(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
        );
        let blocked_agent = build_agent_workflow_status_view_with_provider_agent(
            &sample_human_workflow_snapshot(),
            &[],
            &sample_provider_agent_surface(),
            &history,
        );

        assert!(blocked_human["recommended_next_step"]["execution_contract"].is_null());
        assert!(blocked_agent["recommended_next_step"]["execution_contract"].is_null());
    }

    #[test]
    fn human_workflow_status_view_exposes_structural_feedback_line() {
        let mut snapshot = sample_human_workflow_snapshot();
        if let Some(update) = snapshot.latest_update.as_mut() {
            update.structural_feedback = Some(crate::state::StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: "structural-feedback:NQ:node:path".to_string(),
                recommended_at: "2026-04-29T00:00:00Z".to_string(),
                node_id: "NQ:belief_regime_node:trend".to_string(),
                branch_id: "NQ:belief_regime_node:trend:trend_follow_through".to_string(),
                scenario_id: "scenario:NQ:belief_regime_node:trend:trend_follow_through"
                    .to_string(),
                path_id:
                    "path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"
                        .to_string(),
                followed_path: true,
                exit_reason: Some("target_hit".to_string()),
                notes: Some("user followed structural path".to_string()),
            });
        }

        let value = build_human_workflow_status_view_with_provider_agent(
            &snapshot,
            &[],
            &sample_provider_agent_surface(),
            &[],
        );

        assert!(value["structural_feedback_line"]
            .as_str()
            .unwrap()
            .contains("recommendation=structural-feedback:NQ:node:path"));
        assert!(value["structural_feedback_line"]
            .as_str()
            .unwrap()
            .contains("path=path:scenario:NQ:belief_regime_node:trend:trend_follow_through:primary"));
    }

    #[test]
    fn ensemble_vote_history_view_uses_resolved_scorecard_source() {
        let vote = sample_human_workflow_snapshot()
            .latest_ensemble_vote
            .expect("sample ensemble vote");
        let persisted = vec![EnsembleExecutorScorecard {
            executor: "xgboost_file".to_string(),
            latest_weight_hint: Some(0.80),
            ..EnsembleExecutorScorecard::default()
        }];
        let value = build_ensemble_vote_history_view(
            &WorkflowSnapshot {
                recent_ensemble_votes: vec![vote.clone()],
                ..WorkflowSnapshot::default()
            },
            &persisted,
        );
        assert_eq!(value.history[0].executor_scorecard_source, "persisted");
        assert_eq!(
            value.history[0].executor_scorecards[0].executor,
            "xgboost_file"
        );
        assert_eq!(value.hard_block_only[0].artifact_id, vote.artifact_id);
        assert_eq!(value.hard_block_summary.count, 1);
    }

    #[test]
    fn auxiliary_artifact_surfaces_clone_snapshot_fields() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.artifact_history_summary.total_entries = 3;
        snapshot.artifact_factor_trends = vec![ArtifactFactorTrendSummary::default()];
        snapshot.artifact_family_trends = vec![ArtifactFamilyTrendSummary::default()];
        let surfaces = build_auxiliary_artifact_surfaces(&snapshot);
        assert_eq!(surfaces.artifact_history_summary.total_entries, 3);
        assert_eq!(surfaces.artifact_factor_trends.len(), 1);
        assert_eq!(surfaces.artifact_family_trends.len(), 1);
    }

    #[test]
    fn artifact_report_surfaces_build_expected_views() {
        let mut snapshot = WorkflowSnapshot::default();
        snapshot.artifact_decision_summary.consumed_trend_status =
            "validated_regressing".to_string();
        snapshot.artifact_decision_summary.consumed_trend_reason = "quality_down".to_string();
        snapshot.artifact_lineage_summaries = vec![ArtifactLineageSummary {
            review_rule_break_count: 1,
            ..ArtifactLineageSummary::default()
        }];
        snapshot.artifact_factor_trends = vec![ArtifactFactorTrendSummary {
            factor_name: "f1".to_string(),
            consumed_entries: 2,
            entries: 3,
            ..ArtifactFactorTrendSummary::default()
        }];
        snapshot.artifact_family_trends = vec![ArtifactFamilyTrendSummary {
            family: "fam".to_string(),
            consumed_entries: 1,
            entries: 2,
            ..ArtifactFamilyTrendSummary::default()
        }];
        let report = build_artifact_report_surfaces(&snapshot);
        assert_eq!(
            report.artifact_consumed_gate["status"],
            "validated_regressing"
        );
        assert_eq!(report.artifact_rule_breaks.len(), 1);
        assert_eq!(
            report.artifact_factor_consumed_validation[0].factor_name,
            "f1"
        );
        assert_eq!(report.artifact_family_consumed_validation[0].family, "fam");
    }

    #[test]
    fn pre_bayes_surfaces_clone_snapshot_fields() {
        let mut snapshot = WorkflowSnapshot {
            latest_pre_bayes_policy: Some(PreBayesEvidencePolicy {
                version: "v2".to_string(),
                ..PreBayesEvidencePolicy::default()
            }),
            recent_pre_bayes_policies: vec![PreBayesPolicyRecord {
                policy: PreBayesEvidencePolicy {
                    version: "v1".to_string(),
                    ..PreBayesEvidencePolicy::default()
                },
                ..PreBayesPolicyRecord::default()
            }],
            latest_pre_bayes_policy_diff: Some(PreBayesPolicyDiff::default()),
            latest_pre_bayes_policy_lineage: Some(PreBayesPolicyLineageSummary::default()),
            latest_pre_bayes_entry_quality_bridge: Some(PreBayesEntryQualityBridge::default()),
            latest_pre_bayes_entry_quality_bridge_diff: Some(
                PreBayesEntryQualityBridgeDiff::default(),
            ),
            latest_pre_bayes_soft_evidence_diff: vec![PreBayesSoftEvidenceNodeDiff::default()],
            ..WorkflowSnapshot::default()
        };
        let mut analyze = crate::state::WorkflowPhaseSnapshot::default();
        let mut soft_evidence = std::collections::BTreeMap::new();
        soft_evidence.insert("a".to_string(), {
            let mut inner = std::collections::BTreeMap::new();
            inner.insert("b".to_string(), 0.5);
            inner
        });
        analyze.pre_bayes_soft_evidence = soft_evidence;
        snapshot.latest_analyze = Some(analyze);

        let pre = build_pre_bayes_surfaces(&snapshot);
        assert_eq!(pre.pre_bayes_policy.as_ref().unwrap().version, "v2");
        assert_eq!(pre.pre_bayes_policy_history.len(), 1);
        assert_eq!(pre.pre_bayes_policy_history[0].policy.version, "v1");
        assert!(pre.pre_bayes_policy_diff.is_some());
        assert!(pre.pre_bayes_policy_lineage.is_some());
        assert!(pre.pre_bayes_entry_quality_bridge.is_some());
        assert!(pre.pre_bayes_entry_quality_bridge_diff.is_some());
        assert_eq!(pre.pre_bayes_soft_evidence_diff.len(), 1);
        assert_eq!(
            pre.pre_bayes_soft_evidence
                .as_ref()
                .unwrap()
                .get("a")
                .unwrap()
                .get("b"),
            Some(&0.5)
        );
    }

    #[test]
    fn phase_snapshot_surfaces_clone_snapshot_fields() {
        let snapshot = WorkflowSnapshot {
            latest_train: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "train".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_analyze: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "analyze".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_research: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "research".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_backtest: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "backtest".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            latest_update: Some(crate::state::WorkflowPhaseSnapshot {
                phase: "update".to_string(),
                ..crate::state::WorkflowPhaseSnapshot::default()
            }),
            ..WorkflowSnapshot::default()
        };
        let phases = build_phase_snapshot_surfaces(&snapshot);
        assert_eq!(phases.train.as_ref().unwrap().phase, "train");
        assert_eq!(phases.analyze.as_ref().unwrap().phase, "analyze");
        assert_eq!(phases.research.as_ref().unwrap().phase, "research");
        assert_eq!(phases.backtest.as_ref().unwrap().phase, "backtest");
        assert_eq!(phases.update.as_ref().unwrap().phase, "update");
    }

    #[test]
    fn factor_autoresearch_status_empty_state_returns_explicit_no_state_contract() {
        let value = factor_autoresearch_status_value_for_empty_state("DEMO", "state");
        assert_eq!(value["status"], "no_autoresearch_state");
        assert!(value["live_snapshot"].is_null());
        assert!(value["sessions"].as_array().unwrap().is_empty());
        assert!(value["attempts"].as_array().unwrap().is_empty());
        assert!(value["recommended_next_step"]
            .as_str()
            .unwrap()
            .contains("ict-engine factor-autoresearch"));
    }
}
