use super::*;

pub(crate) fn emit_update_output(report: &UpdateReport, ensemble: bool) -> Result<()> {
    let reflection_evidence = report
        .agent_prompts
        .prompts
        .iter()
        .map(|prompt| format!("{}:{}:{}", prompt.stage, prompt.id, prompt.objective))
        .collect::<Vec<_>>();
    let reflection_next_candidates = report
        .recommended_next_command
        .split(';')
        .map(str::trim)
        .filter(|candidate| !candidate.is_empty())
        .map(str::to_string)
        .collect::<Vec<_>>();
    let reflection_bundle = build_reflection_bundle(ReflectionBundleInput {
        symbol: report.symbol.clone(),
        timestamp: report.provenance.data_fingerprint.clone(),
        objective: report.agent_prompts.workflow.clone(),
        expected_regime: report.workflow_state.phase.clone(),
        expected_direction: report
            .agent_action_plan
            .items
            .first()
            .map(|item| item.title.clone())
            .filter(|title| !title.is_empty())
            .unwrap_or_else(|| report.realized_outcome.clone()),
        realized_outcome: report.realized_outcome.clone(),
        evidence: reflection_evidence,
        next_candidates: reflection_next_candidates,
    });
    let mut reflection_bundle = reflection_bundle;
    if let Ok(artifact) = load_state_or_default::<ExecutionTreeArtifact, _>(
        &report.state_dir,
        &report.symbol,
        EXECUTION_TREE_TRACE_FILE,
    ) {
        reflection_bundle.execution_shap_top_k = artifact.execution_shap_top_k;
    }
    if let Ok(artifact) =
        ict_engine::pda_sequence::load_pda_sequence_analysis(&report.state_dir, &report.symbol)
    {
        ict_engine::application::reflection::apply_pda_sequence_artifact_to_reflection_bundle(
            &mut reflection_bundle,
            &artifact,
        );
    }
    let ensemble_surface = if ensemble {
        report
            .workflow_snapshot
            .latest_ensemble_vote
            .as_ref()
            .map(|vote| {
                let persisted_scorecards =
                    load_ensemble_executor_scorecards(&report.state_dir, &report.symbol)
                        .unwrap_or_default();
                let (scorecards, scorecard_source) =
                    resolved_vote_scorecards(&persisted_scorecards, vote);
                serde_json::json!({
                    "ensemble_vote": vote,
                    "executor_scorecards": scorecards,
                    "executor_scorecard_source": scorecard_source,
                })
            })
    } else {
        None
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "reflection_bundle": reflection_bundle,
            "ensemble": ensemble_surface,
        }))?
    );
    Ok(())
}
