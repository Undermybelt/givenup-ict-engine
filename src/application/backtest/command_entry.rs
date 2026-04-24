use anyhow::Result;

use crate::application::backtest::{
    build_backtest_compare_report, build_backtest_result_artifact,
    build_duration_sizing_delta_surface, build_oos_quality_delta_surface,
    build_shrink_on_off_comparison_summary, BacktestResultArtifactInput,
};
use crate::application::orchestration::resolved_vote_scorecards;
use crate::config::shell_quote;
use crate::state::{
    load_ensemble_executor_scorecards, load_state_or_default, BacktestRunRecord, WorkflowSnapshot,
    BACKTEST_RUNS_FILE,
};

fn latest_duration_phase(
    snapshot: &WorkflowSnapshot,
) -> Option<&crate::state::WorkflowPhaseSnapshot> {
    snapshot
        .latest_backtest
        .as_ref()
        .or(snapshot.latest_research.as_ref())
        .or(snapshot.latest_update.as_ref())
        .or(snapshot.latest_analyze.as_ref())
}

fn parse_duration_sizing_scale(summary: &[String]) -> Option<f64> {
    summary.iter().find_map(|line| {
        line.split_whitespace().find_map(|fragment| {
            fragment
                .strip_prefix("duration_sizing_scale=")
                .and_then(|value| value.parse::<f64>().ok())
        })
    })
}

fn build_duration_surface_from_artifacts(
    snapshot: &WorkflowSnapshot,
    artifact_action_summary: &[String],
) -> Vec<String> {
    let phase = latest_duration_phase(snapshot);
    let duration_model = phase.and_then(|phase| phase.hybrid_duration_model.as_deref());
    let remaining_expected_bars = phase.and_then(|phase| phase.hybrid_remaining_expected_bars);
    let scale = parse_duration_sizing_scale(artifact_action_summary).unwrap_or(1.0);
    build_duration_sizing_delta_surface(
        1.0,
        scale,
        1.0,
        scale,
        duration_model,
        remaining_expected_bars,
    )
}

pub fn factor_backtest_command<FRun>(
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    ensemble: bool,
    state_dir: &str,
    output_format: &str,
    run_backtest: FRun,
) -> Result<()>
where
    FRun: Fn(&str, &str, Option<&str>, &str) -> Result<crate::factor_lab::BacktestResult>,
{
    let report = run_backtest(symbol, data, paired_data, state_dir)?;
    let credibility_summary = serde_json::json!({
        "conformal_coverage_1sigma": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.conformal_coverage_1sigma))
            .collect::<Vec<_>>(),
        "conformal_miscoverage_1sigma": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.conformal_miscoverage_1sigma))
            .collect::<Vec<_>>(),
        "regime_break_penalty": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.regime_break_penalty))
            .collect::<Vec<_>>(),
        "structural_break_score": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_score))
            .collect::<Vec<_>>(),
        "structural_break_detected": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_detected))
            .collect::<Vec<_>>(),
        "structural_break_index": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_index))
            .collect::<Vec<_>>(),
    });
    let shrink_comparison_summary = build_shrink_on_off_comparison_summary(
        report
            .factor_results
            .first()
            .map(|result| result.metrics.conformal_coverage_1sigma)
            .unwrap_or_default(),
        report
            .factor_results
            .first()
            .map(|result| {
                (result.metrics.conformal_coverage_1sigma + result.metrics.regime_break_penalty)
                    .clamp(0.0, 1.0)
            })
            .unwrap_or_default(),
        report.aggregate_return,
        report.aggregate_return
            + report
                .factor_results
                .first()
                .map(|result| result.metrics.regime_break_penalty)
                .unwrap_or_default(),
    );
    let oos_quality_delta_surface = build_oos_quality_delta_surface(
        report
            .factor_results
            .first()
            .map(|result| result.metrics.conformal_coverage_1sigma)
            .unwrap_or_default(),
        report
            .factor_results
            .first()
            .map(|result| {
                (result.metrics.conformal_coverage_1sigma - result.metrics.regime_break_penalty)
                    .clamp(0.0, 1.0)
            })
            .unwrap_or_default(),
        report
            .factor_results
            .iter()
            .map(|result| result.metrics.trade_count)
            .sum(),
        report
            .factor_results
            .iter()
            .map(|result| result.metrics.trade_count)
            .sum(),
    );
    let duration_sizing_delta_surface = build_duration_surface_from_artifacts(
        &report.workflow_snapshot,
        &report.artifact_action_summary,
    );
    let compact_report = build_backtest_result_artifact(BacktestResultArtifactInput {
        summary: format!("factor_backtest:{}", symbol),
        scorecards: report
            .scorecards
            .iter()
            .map(|item| format!("{}:{:.3}", item.factor_name, item.composite_score))
            .collect::<Vec<_>>(),
        shrink_comparison_summary,
        duration_sizing_delta_surface,
        oos_quality_delta_surface,
        market_breakdown: vec![
            format!("best_factor={:?}", report.best_factor),
            format!(
                "coverage_1sigma={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.conformal_coverage_1sigma)
                    .unwrap_or_default()
            ),
            format!(
                "regime_break_penalty={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.regime_break_penalty)
                    .unwrap_or_default()
            ),
            format!(
                "structural_break_detected={}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.structural_break_detected)
                    .unwrap_or(false)
            ),
            format!(
                "structural_break_score={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.structural_break_score)
                    .unwrap_or_default()
            ),
        ],
        regime_breakdown: vec![],
        window_breakdown: vec![],
        comparable: true,
        artifacts: vec![],
    });
    let persisted_backtest_runs: Vec<BacktestRunRecord> =
        load_state_or_default(state_dir, symbol, BACKTEST_RUNS_FILE)?;
    let backtest_compare_report =
        persisted_backtest_runs
            .split_last()
            .and_then(|(current, previous)| {
                previous
                    .last()
                    .and_then(|prior| build_backtest_compare_report(prior, current))
            });
    let ensemble_surface = if ensemble {
        report
            .workflow_snapshot
            .latest_ensemble_vote
            .as_ref()
            .map(|vote| {
                let persisted_scorecards =
                    load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
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
    let suggested_update_command = if !report.recommended_commands.update.command.is_empty()
        && report.recommended_commands.update.command != "recommended_command_unavailable"
    {
        report.recommended_commands.update.command.clone()
    } else {
        format!(
            "ict-engine update --symbol {} --outcome <win|loss|breakeven> --state-dir {}",
            shell_quote(symbol),
            shell_quote(state_dir)
        )
    };
    let payload = crate::application::reporting::build_factor_backtest_output_payload(
        &report,
        &compact_report,
        backtest_compare_report,
        credibility_summary,
        ensemble_surface,
        &suggested_update_command,
    );
    crate::application::reporting::emit_structured_output_payload(
        output_format,
        &payload,
        &compact_report,
    )?;
    Ok(())
}
