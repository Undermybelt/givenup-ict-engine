use super::*;

pub(crate) fn feedback_record_from_artifact(
    artifact: PendingUpdateArtifact,
    outcome_label: &str,
    pnl: Option<f64>,
    regime: Option<&str>,
    direction: Option<&str>,
) -> FeedbackRecord {
    let mut feedback = artifact.template_feedback;
    feedback.realized_outcome = outcome_label.to_string();
    feedback.pnl = pnl.unwrap_or_else(|| match outcome_label {
        "win" => 0.01,
        "loss" => -0.01,
        _ => 0.0,
    });
    if let Some(regime) = regime {
        feedback.regime_at_entry = normalize_regime_label(regime);
    }
    if let Some(direction) = direction {
        feedback.model_probabilities_before_trade.selected_direction =
            normalize_direction_label(direction);
    }
    feedback
}

pub(crate) fn latest_execution_candidate_for_source_run(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Option<ExecutionCandidateArtifact>> {
    let Some(source_run_id) = source_run_id else {
        return Ok(None);
    };
    Ok(load_execution_candidate_history(state_dir, symbol)?
        .into_iter()
        .rev()
        .find(|artifact| artifact.source_run_id.as_deref() == Some(source_run_id)))
}

pub(crate) fn latest_ensemble_vote_for_source_run(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Option<EnsembleVoteRecord>> {
    let Some(source_run_id) = source_run_id else {
        return Ok(None);
    };
    Ok(load_ensemble_vote_history(state_dir, symbol)?
        .into_iter()
        .rev()
        .find(|artifact| artifact.source_run_id.as_deref() == Some(source_run_id)))
}

pub(crate) fn derive_executor_scorecards_from_summaries(
    executor_summaries: &[String],
) -> Vec<EnsembleExecutorScorecard> {
    executor_summaries
        .iter()
        .map(|summary| EnsembleExecutorScorecard {
            executor: summary
                .split_whitespace()
                .find_map(|part| part.strip_prefix("executor="))
                .unwrap_or("executor_unavailable")
                .to_string(),
            latest_weight_hint: summary
                .split_whitespace()
                .find_map(|part| part.strip_prefix("weight="))
                .and_then(|value| value.parse::<f64>().ok()),
            ..EnsembleExecutorScorecard::default()
        })
        .collect()
}

pub(crate) fn load_canonical_executor_scorecards(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Vec<EnsembleExecutorScorecard>> {
    let persisted = load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    if !persisted.is_empty() {
        return Ok(persisted);
    }
    Ok(
        latest_ensemble_vote_for_source_run(state_dir, symbol, source_run_id)?
            .map(|artifact| {
                if artifact.executor_scorecards.is_empty() {
                    derive_executor_scorecards_from_summaries(&artifact.executor_summaries)
                } else {
                    artifact.executor_scorecards
                }
            })
            .unwrap_or_default(),
    )
}

pub(crate) fn apply_update_outcome_to_executor_scorecards(
    scorecards: &mut [EnsembleExecutorScorecard],
    realized_outcome: &str,
    quality_adjustment: i64,
) {
    for scorecard in scorecards {
        match realized_outcome {
            "win" => scorecard.wins += 1,
            "loss" => scorecard.losses += 1,
            _ => scorecard.breakevens += 1,
        }
        match realized_outcome {
            "win" => scorecard.validated_positive += 1,
            "loss" => scorecard.validated_negative += 1,
            _ => {}
        }
        scorecard.cumulative_quality_score += quality_adjustment;
        scorecard.last_outcome = Some(realized_outcome.to_string());
        scorecard.last_updated_at = Some(Utc::now());
    }
}

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
