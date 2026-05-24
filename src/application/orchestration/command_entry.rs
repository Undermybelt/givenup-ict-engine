use anyhow::Result;

use crate::application::entry_models::training_export::structural_path_ranking_read_state_dir;
use crate::application::multi_timeframe_inputs::{
    detected_multi_timeframe_clean_root, detected_tomac_root, detected_tomac_root_or_placeholder,
};
use crate::application::provider_catalog::{
    list_repo_example_profiles, load_provider_profile, provider_status_agent_surface,
    workflow_relevant_provider_ids, ProviderCatalogAgentSurface, ProviderProfileReferenceSurface,
};
use crate::state::{
    load_ensemble_executor_scorecards, load_learning_state, load_workflow_snapshot,
    migrate_ensemble_executor_scorecards, recommended_next_command_meta,
    RecommendedNextCommandKind, WorkflowSnapshot,
};

use super::{
    dispatch_workflow_status, emit_pre_bayes_diff_output, emit_pre_bayes_status_output,
    WorkflowStatusBootstrapInput, WorkflowStatusDispatchInput,
};

fn hydrate_recommended_next_command_meta(
    command: &str,
    meta: &mut crate::state::RecommendedNextCommandMeta,
) {
    if meta.kind == RecommendedNextCommandKind::Unknown && !command.is_empty() {
        *meta = recommended_next_command_meta(command);
    }
}

fn hydrate_workflow_snapshot_recommended_next_command_meta(snapshot: &mut WorkflowSnapshot) {
    hydrate_recommended_next_command_meta(
        &snapshot.recommended_next_command,
        &mut snapshot.recommended_next_command_meta,
    );
    for phase in [
        snapshot.latest_train.as_mut(),
        snapshot.latest_analyze.as_mut(),
        snapshot.latest_research.as_mut(),
        snapshot.latest_backtest.as_mut(),
        snapshot.latest_update.as_mut(),
    ]
    .into_iter()
    .flatten()
    {
        hydrate_recommended_next_command_meta(
            &phase.recommended_next_command,
            &mut phase.recommended_next_command_meta,
        );
    }
}

fn profile_reference_matches_symbol(
    profile: &ProviderProfileReferenceSurface,
    symbol: &str,
) -> bool {
    let Ok(document) = load_provider_profile(&profile.selector) else {
        return false;
    };
    document.data_contracts.iter().any(|contract| {
        contract.symbols.is_empty() || contract.symbols.iter().any(|item| item == symbol)
    })
}

fn attach_workflow_opt_in_profile_refs(
    surface: &mut ProviderCatalogAgentSurface,
    symbol: &str,
) -> Result<()> {
    if surface.selected_profile.is_some() || !surface.available_opt_in_profiles.is_empty() {
        return Ok(());
    }
    surface.available_opt_in_profiles = list_repo_example_profiles()?
        .into_iter()
        .filter(|profile| profile_reference_matches_symbol(profile, symbol))
        .collect();
    Ok(())
}

#[cfg(test)]
fn workflow_status_needs_provider_surface(
    provider_profile: Option<&str>,
    phase: Option<&str>,
    _snapshot: &WorkflowSnapshot,
) -> bool {
    if provider_profile.is_some() {
        return true;
    }
    if phase.is_some() {
        return false;
    }
    true
}

pub struct WorkflowStatusCommandInput<'a> {
    pub symbol: &'a str,
    pub state_dir: &'a str,
    pub refresh: bool,
    pub provider_profile: Option<&'a str>,
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

pub fn workflow_status_command<F>(
    input: WorkflowStatusCommandInput<'_>,
    refresh_snapshot: F,
) -> Result<()>
where
    F: Fn(&str, &str) -> Result<WorkflowSnapshot>,
{
    let WorkflowStatusCommandInput {
        symbol,
        state_dir,
        refresh,
        provider_profile,
        phase,
        actionable_only,
        conflicts_only,
        latest_promotable,
        hard_block_only,
        hard_block_reason,
        limit,
        output_format,
        stable,
    } = input;
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;
    let read_state_dir = structural_path_ranking_read_state_dir(state_dir, symbol);
    let mut snapshot = if refresh {
        refresh_snapshot(&read_state_dir, symbol)?
    } else {
        load_workflow_snapshot(&read_state_dir, symbol)?
    };
    hydrate_workflow_snapshot_recommended_next_command_meta(&mut snapshot);
    let persisted_scorecards =
        load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    let learning_state = load_learning_state(&read_state_dir, symbol).unwrap_or_default();
    let relevant_provider_ids = workflow_relevant_provider_ids(
        &snapshot.recommended_next_command,
        (!snapshot.blocking_truth.reason.is_empty())
            .then_some(snapshot.blocking_truth.reason.as_str()),
    );
    let provider_support_relevant = provider_profile.is_some() || phase.is_none();
    let provider_filter = if provider_profile.is_none() && relevant_provider_ids.len() == 1 {
        relevant_provider_ids.iter().copied().next()
    } else {
        None
    };
    let mut provider_status_agent = if provider_profile.is_some() || provider_support_relevant {
        provider_status_agent_surface(None, provider_filter, provider_profile).unwrap_or_default()
    } else {
        ProviderCatalogAgentSurface::default()
    };
    if provider_profile.is_none() && provider_support_relevant {
        attach_workflow_opt_in_profile_refs(&mut provider_status_agent, symbol)?;
    }
    let (detected_tomac_root, multi_timeframe_clean_root, tomac_root_placeholder) =
        if provider_status_agent.selected_profile.is_some() {
            let detected_tomac_root = detected_tomac_root();
            let multi_timeframe_clean_root =
                detected_multi_timeframe_clean_root(detected_tomac_root.as_deref());
            let tomac_root_placeholder = detected_tomac_root_or_placeholder();
            (
                detected_tomac_root,
                multi_timeframe_clean_root,
                tomac_root_placeholder,
            )
        } else {
            (None, None, "<tomac-root>".to_string())
        };
    dispatch_workflow_status(
        &snapshot,
        &persisted_scorecards,
        &provider_status_agent,
        learning_state.feedback_history.as_slice(),
        &learning_state.structural_prior_state,
        WorkflowStatusDispatchInput {
            phase,
            actionable_only,
            conflicts_only,
            latest_promotable,
            hard_block_only,
            hard_block_reason,
            limit,
            output_format,
            stable,
            prefer_persisted_execution_candidate: phase
                .is_some_and(|value| value.eq_ignore_ascii_case("execution-candidate"))
                && !refresh,
        },
        WorkflowStatusBootstrapInput {
            symbol,
            state_dir,
            detected_tomac_root,
            multi_timeframe_clean_root,
            tomac_root_placeholder,
        },
    )
}

pub fn pre_bayes_status_command<F>(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
    section: Option<&str>,
    output_format: &str,
    refresh_snapshot: F,
) -> Result<()>
where
    F: Fn(&str, &str) -> Result<WorkflowSnapshot>,
{
    let read_state_dir = structural_path_ranking_read_state_dir(state_dir, symbol);
    let snapshot = if refresh {
        refresh_snapshot(&read_state_dir, symbol)?
    } else {
        load_workflow_snapshot(&read_state_dir, symbol)?
    };
    emit_pre_bayes_status_output(&snapshot, section, output_format)
}

pub fn pre_bayes_diff_command<F>(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
    output_format: &str,
    refresh_snapshot: F,
) -> Result<()>
where
    F: Fn(&str, &str) -> Result<WorkflowSnapshot>,
{
    let read_state_dir = structural_path_ranking_read_state_dir(state_dir, symbol);
    let snapshot = if refresh {
        refresh_snapshot(&read_state_dir, symbol)?
    } else {
        load_workflow_snapshot(&read_state_dir, symbol)?
    };
    emit_pre_bayes_diff_output(&snapshot, output_format)
}

#[cfg(test)]
mod tests {
    use super::structural_path_ranking_read_state_dir;
    use super::workflow_status_command;
    use super::workflow_status_needs_provider_surface;
    use crate::application::entry_models::training_export::POLICY_TRAINING_DIR;
    use crate::belief_core::ranking_label::StructuralPathRankingTargetExportSummary;
    use crate::state::WorkflowSnapshot;
    use std::cell::RefCell;
    use std::path::Path;

    struct StructuralPathRankingSummaryFixture<'a> {
        summary_dir: &'a Path,
        symbol: &'a str,
        candidate_set_id: &'a str,
        rows: usize,
        mature_rows: usize,
        history_rows: usize,
        history_mature_rows: usize,
        rows_with_raw_path_score: usize,
        rows_with_propensity_estimate: usize,
    }

    fn write_structural_path_ranking_summary(fixture: StructuralPathRankingSummaryFixture<'_>) {
        let StructuralPathRankingSummaryFixture {
            summary_dir,
            symbol,
            candidate_set_id,
            rows,
            mature_rows,
            history_rows,
            history_mature_rows,
            rows_with_raw_path_score,
            rows_with_propensity_estimate,
        } = fixture;
        let summary = StructuralPathRankingTargetExportSummary {
            symbol: symbol.to_string(),
            rows,
            candidate_set_id: candidate_set_id.to_string(),
            candidate_set_size: rows,
            pending_reward_states: std::collections::BTreeMap::new(),
            mature_rows,
            rows_with_raw_path_score,
            rows_with_calibrated_path_prob: rows_with_raw_path_score,
            rows_with_path_prob_lower_bound: rows_with_raw_path_score,
            rows_with_propensity_estimate,
            csv_path: summary_dir
                .join("structural_path_ranking_target.csv")
                .to_string_lossy()
                .to_string(),
            jsonl_path: summary_dir
                .join("structural_path_ranking_target.jsonl")
                .to_string_lossy()
                .to_string(),
            history_csv_path: summary_dir
                .join("structural_path_ranking_target_history.csv")
                .to_string_lossy()
                .to_string(),
            history_jsonl_path: summary_dir
                .join("structural_path_ranking_target_history.jsonl")
                .to_string_lossy()
                .to_string(),
            history_rows,
            history_mature_rows,
            history_rows_with_raw_path_score: rows_with_raw_path_score,
            history_rows_with_calibrated_path_prob: rows_with_raw_path_score,
            history_rows_with_path_prob_lower_bound: rows_with_raw_path_score,
            history_rows_with_propensity_estimate: rows_with_propensity_estimate,
            summary_path: summary_dir
                .join("structural_path_ranking_target_summary.json")
                .to_string_lossy()
                .to_string(),
            trainer_manifest: Default::default(),
            summary_line: format!("structural_path_ranking_target rows={rows}"),
            rows_with_execution_gate_status: 0,
            rows_with_training_weight: rows_with_propensity_estimate,
            history_rows_with_training_weight: rows_with_propensity_estimate,
        };
        std::fs::create_dir_all(summary_dir).unwrap();
        std::fs::write(
            summary_dir.join("structural_path_ranking_target_summary.json"),
            serde_json::to_string_pretty(&summary).unwrap(),
        )
        .unwrap();
    }

    #[test]
    fn workflow_status_phase_read_skips_provider_surface_without_explicit_profile() {
        let snapshot = WorkflowSnapshot {
            recommended_next_command: "ict-engine analyze-live --symbol NQ --futures-symbol NQ=F"
                .to_string(),
            ..WorkflowSnapshot::default()
        };

        assert!(!workflow_status_needs_provider_surface(
            None,
            Some("execution-candidate"),
            &snapshot,
        ));
    }

    #[test]
    fn workflow_status_full_snapshot_keeps_provider_surface_when_relevant() {
        let snapshot = WorkflowSnapshot {
            recommended_next_command: "ict-engine analyze-live --symbol NQ --futures-symbol NQ=F"
                .to_string(),
            ..WorkflowSnapshot::default()
        };

        assert!(workflow_status_needs_provider_surface(
            None, None, &snapshot
        ));
    }

    #[test]
    fn workflow_status_explicit_profile_keeps_provider_surface_for_phase_reads() {
        let snapshot = WorkflowSnapshot::default();

        assert!(workflow_status_needs_provider_surface(
            Some("demo-profile"),
            Some("execution-candidate"),
            &snapshot,
        ));
    }

    #[test]
    fn workflow_status_command_refreshes_from_mature_feedback_child_root() {
        let temp = tempfile::tempdir().unwrap();
        let symbol = "BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523";
        let primary_summary_dir = temp.path().join(symbol).join(POLICY_TRAINING_DIR);
        let feedback_state_dir = temp.path().join("ict-engine-feedback");
        let feedback_summary_dir = feedback_state_dir.join(symbol).join(POLICY_TRAINING_DIR);

        write_structural_path_ranking_summary(StructuralPathRankingSummaryFixture {
            summary_dir: &primary_summary_dir,
            symbol,
            candidate_set_id: &format!("structural-candidates:{symbol}:primary"),
            rows: 1,
            mature_rows: 0,
            history_rows: 1,
            history_mature_rows: 0,
            rows_with_raw_path_score: 0,
            rows_with_propensity_estimate: 0,
        });
        write_structural_path_ranking_summary(StructuralPathRankingSummaryFixture {
            summary_dir: &feedback_summary_dir,
            symbol,
            candidate_set_id: &format!("structural-candidates:{symbol}:feedback"),
            rows: 50,
            mature_rows: 50,
            history_rows: 188,
            history_mature_rows: 185,
            rows_with_raw_path_score: 47,
            rows_with_propensity_estimate: 120,
        });

        let observed_state_dir = RefCell::new(None::<String>);
        let refresh_snapshot =
            |state_dir: &str, symbol: &str| -> anyhow::Result<WorkflowSnapshot> {
                observed_state_dir.replace(Some(state_dir.to_string()));
                Ok(WorkflowSnapshot {
                    symbol: symbol.to_string(),
                    ..WorkflowSnapshot::default()
                })
            };

        workflow_status_command(
            crate::application::orchestration::WorkflowStatusCommandInput {
                symbol,
                state_dir: temp.path().to_str().unwrap(),
                refresh: true,
                provider_profile: None,
                phase: None,
                actionable_only: false,
                conflicts_only: false,
                latest_promotable: false,
                hard_block_only: false,
                hard_block_reason: None,
                limit: None,
                output_format: "json",
                stable: false,
            },
            refresh_snapshot,
        )
        .unwrap();

        assert_eq!(
            observed_state_dir.into_inner().as_deref(),
            Some(feedback_state_dir.to_str().unwrap())
        );
        assert_eq!(
            structural_path_ranking_read_state_dir(temp.path().to_str().unwrap(), symbol),
            feedback_state_dir.to_string_lossy()
        );
    }
}
