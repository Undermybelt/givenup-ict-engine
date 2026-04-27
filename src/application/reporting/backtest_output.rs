use anyhow::Result;
use serde::Serialize;
use serde_json::Value;

use crate::application::backtest::{BacktestCompareReport, ControlMatrixResearchArtifact};
use crate::application::output_foundation::{
    print_redacted_json, redact_local_paths_in_human_text,
};
use crate::application::reporting::{build_compact_backtest_report, humanize_next_step_line};
use crate::backtest_report_shell::BacktestReport;
use crate::factor_lab::BacktestResult as FactorBacktestRunResult;

pub fn build_compact_compare_report(
    compare: Option<&BacktestCompareReport>,
) -> Option<crate::application::reporting::CompactBacktestReport> {
    compare.map(|compare| {
        build_compact_backtest_report(
            compare.summary.clone(),
            &compare.shrink_comparison_summary,
            &compare.duration_sizing_delta_surface,
            &compare.regressions,
            &compare.recommended_actions,
        )
    })
}

pub fn human_compare_summary(compare: Option<&BacktestCompareReport>) -> Option<String> {
    compare.map(|compare| {
        let duration = compare
            .duration_sizing_delta_surface
            .iter()
            .find(|line| line.starts_with("duration_sizing_direction="))
            .cloned()
            .unwrap_or_else(|| "duration_sizing_direction=unchanged".to_string());
        let risk = compare
            .regressions
            .first()
            .cloned()
            .unwrap_or_else(|| "no_material_regressions".to_string());
        let action = compare
            .recommended_actions
            .first()
            .cloned()
            .unwrap_or_else(|| "no_follow_up_action".to_string());
        format!("Compare: {} | risk={} | next={}", duration, risk, action)
    })
}

pub fn human_backtest_compare_summary(compare: Option<&BacktestCompareReport>) -> Option<String> {
    human_compare_summary(compare)
        .map(|summary| summary.replacen("Compare:", "Backtest compare:", 1))
}

pub fn human_research_compare_summary(compare: Option<&BacktestCompareReport>) -> Option<String> {
    human_compare_summary(compare)
        .map(|summary| summary.replacen("Compare:", "Research compare:", 1))
}

pub fn render_factor_backtest_human_output(
    report: &FactorBacktestRunResult,
    compare: Option<&BacktestCompareReport>,
) -> String {
    let best = report.best_factor.as_deref().unwrap_or("n/a");
    let aggregate_return_pct = report.aggregate_return * 100.0;
    let total_trades: usize = report
        .factor_results
        .iter()
        .map(|result| result.metrics.trade_count)
        .sum();
    let top = report.factor_results.first();
    let top_coverage = top
        .map(|result| result.metrics.conformal_coverage_1sigma)
        .unwrap_or_default();
    let top_regime_penalty = top
        .map(|result| result.metrics.regime_break_penalty)
        .unwrap_or_default();
    let top_structural_break = top
        .map(|result| result.metrics.structural_break_detected)
        .unwrap_or(false);

    let mut lines = vec![
        "Factor backtest summary".to_string(),
        format!("- Best factor: {best}"),
        format!("- Aggregate return: {aggregate_return_pct:+.2}%"),
        format!("- Trades: {total_trades}"),
    ];
    let mut credibility_parts = vec![
        format!("conformal_coverage_1sigma={top_coverage:.3}"),
        format!("regime_break_penalty={top_regime_penalty:.3}"),
    ];
    if top_structural_break {
        credibility_parts.push("structural_break=detected".to_string());
    }
    lines.push(format!("- Credibility: {}", credibility_parts.join(" | ")));
    lines.push(format!(
        "- Next: {}",
        humanize_next_step_line(&report.recommended_next_command)
    ));

    if let Some(compare_summary) = human_backtest_compare_summary(compare) {
        lines.push(String::new());
        lines.push(compare_summary);
    }
    redact_local_paths_in_human_text(&lines.join("\n"))
}

pub fn render_factor_research_human_output(
    report: &impl Serialize,
    compare: Option<&BacktestCompareReport>,
) -> String {
    let report_value = serde_json::to_value(report).unwrap_or(Value::Null);
    let mut lines = vec!["Factor research summary".to_string()];

    if let Some(objective) = report_value
        .get("research_objective")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
    {
        lines.push(format!("- Objective: {objective}"));
    }

    let best_factor = report_value
        .get("best_factor")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty())
        .unwrap_or("n/a");
    lines.push(format!("- Best factor: {best_factor}"));

    if let Some(aggregate_return) = report_value.get("aggregate_return").and_then(Value::as_f64) {
        lines.push(format!(
            "- Aggregate return: {:+.2}%",
            aggregate_return * 100.0
        ));
    }

    let feedback_generated = report_value
        .get("feedback_records_generated")
        .and_then(Value::as_u64)
        .unwrap_or_default();
    let feedback_applied = report_value
        .get("feedback_records_applied")
        .and_then(Value::as_u64)
        .unwrap_or_default();
    lines.push(format!(
        "- Feedback: generated={} applied={}",
        feedback_generated, feedback_applied
    ));

    if let Some(scorecards) = report_value
        .get("backtest")
        .and_then(|backtest| backtest.get("scorecards"))
        .and_then(Value::as_array)
    {
        let top_factors = scorecards
            .iter()
            .take(3)
            .filter_map(|scorecard| {
                let factor_name = scorecard.get("factor_name").and_then(Value::as_str)?;
                let composite_score = scorecard.get("composite_score").and_then(Value::as_f64)?;
                let iteration_action = scorecard
                    .get("iteration_action")
                    .and_then(Value::as_str)
                    .unwrap_or("n/a");
                let grade = scorecard
                    .get("grade")
                    .and_then(Value::as_str)
                    .unwrap_or("n/a");
                Some(format!(
                    "{}={:.3} {} {}",
                    factor_name, composite_score, iteration_action, grade
                ))
            })
            .collect::<Vec<_>>();
        if !top_factors.is_empty() {
            lines.push(format!("- Top factors: {}", top_factors.join("; ")));
        }
    }

    let next_command = report_value
        .get("recommended_next_command")
        .and_then(Value::as_str)
        .unwrap_or_default();
    lines.push(format!("- Next: {}", humanize_next_step_line(next_command)));

    if let Some(compare_summary) = human_research_compare_summary(compare) {
        lines.push(String::new());
        lines.push(compare_summary);
    }
    redact_local_paths_in_human_text(&lines.join("\n"))
}

pub fn build_backtest_output_payload(
    report: &BacktestReport,
    compact_backtest_report: &impl Serialize,
    compare: Option<BacktestCompareReport>,
    human_backtest_summary: String,
) -> Value {
    let compact_compare_report = build_compact_compare_report(compare.as_ref());
    let human_backtest_compare_summary = human_backtest_compare_summary(compare.as_ref());
    let human_output = render_backtest_human_output(report, compare.as_ref());
    serde_json::json!({
        "report": report,
        "compact_backtest_report": compact_backtest_report,
        "backtest_compare_report": compare,
        "compact_compare_report": compact_compare_report,
        "human_backtest_compare_summary": human_backtest_compare_summary,
        "human_backtest_summary": human_backtest_summary,
        "human_output": human_output,
    })
}

pub fn render_backtest_human_output(
    report: &BacktestReport,
    compare: Option<&BacktestCompareReport>,
) -> String {
    let mut lines = vec![if report.trades == 0 {
        format!(
            "Backtest ran with execution_realism=spread:{:.2}bps slippage:{:.2}bps fee:{:.2}bps policy={} trades={} comparable={} and produced no trades under the current constraints.",
            report.spread_bps,
            report.slippage_bps,
            report.fee_bps,
            report.ambiguous_bar_policy,
            report.trades,
            report.dataset_comparability.comparable
        )
    } else {
        format!(
            "Backtest ran with execution_realism=spread:{:.2}bps slippage:{:.2}bps fee:{:.2}bps policy={} trades={} comparable={} and produced {} trades.",
            report.spread_bps,
            report.slippage_bps,
            report.fee_bps,
            report.ambiguous_bar_policy,
            report.trades,
            report.dataset_comparability.comparable,
            report.trades
        )
    }];
    if let Some(compare_summary) = human_backtest_compare_summary(compare) {
        lines.push(compare_summary);
    }
    lines.join("\n")
}

pub fn build_factor_backtest_output_payload(
    report: &FactorBacktestRunResult,
    compact_backtest_report: &impl Serialize,
    compare: Option<BacktestCompareReport>,
    credibility_summary: Value,
    ensemble_surface: Option<Value>,
    suggested_update_command: &str,
) -> Value {
    let compact_compare_report = build_compact_compare_report(compare.as_ref());
    let human_backtest_compare_summary = human_backtest_compare_summary(compare.as_ref());
    let human_output = render_factor_backtest_human_output(report, compare.as_ref());
    serde_json::json!({
        "report": report,
        "compact_backtest_report": compact_backtest_report,
        "backtest_compare_report": compare,
        "compact_compare_report": compact_compare_report,
        "human_backtest_compare_summary": human_backtest_compare_summary,
        "credibility_summary": credibility_summary,
        "ensemble": ensemble_surface,
        "human_output": human_output,
        "suggested_update_command": suggested_update_command,
    })
}

pub fn build_factor_research_output_payload(
    report: &impl Serialize,
    compare: Option<BacktestCompareReport>,
    reflection_bundle: Value,
    ensemble_surface: Option<Value>,
    factor_lifecycle: Value,
    control_matrix_plan: Option<Value>,
) -> Value {
    let compact_compare_report = build_compact_compare_report(compare.as_ref());
    let human_research_compare_summary = human_research_compare_summary(compare.as_ref());
    let human_output = render_factor_research_human_output(report, compare.as_ref());
    serde_json::json!({
        "report": report,
        "research_compare_report": compare,
        "compact_compare_report": compact_compare_report,
        "human_research_compare_summary": human_research_compare_summary,
        "reflection_bundle": reflection_bundle,
        "ensemble": ensemble_surface,
        "factor_lifecycle": factor_lifecycle,
        "control_matrix_plan": control_matrix_plan,
        "human_output": human_output,
    })
}

fn format_control_matrix_run_summary(
    run: &crate::application::backtest::ControlMatrixResearchRunSummary,
) -> String {
    let best_factor = run.best_factor.as_deref().unwrap_or("n/a");
    let toggles = if run.enabled_toggles.is_empty() {
        "none".to_string()
    } else {
        run.enabled_toggles.join(",")
    };
    format!(
        "{} return={:+.2}% best_factor={} toggles={}",
        run.run_label,
        run.aggregate_return * 100.0,
        best_factor,
        toggles
    )
}

pub fn render_control_matrix_research_human_output(
    artifact: &ControlMatrixResearchArtifact,
) -> String {
    let mut lines = vec![
        "PB12 control-matrix research summary".to_string(),
        format!("- Objective: {}", artifact.research_objective),
        format!(
            "- Sweep: {} runs={} kind={}",
            artifact.sweep_id,
            artifact.run_count,
            artifact.control_matrix_plan.kind.as_str()
        ),
    ];
    if let Some(baseline) = artifact.baseline_run.as_ref() {
        lines.push(format!(
            "- Baseline: {}",
            format_control_matrix_run_summary(baseline)
        ));
    }
    if !artifact.top_runs.is_empty() {
        lines.push(format!(
            "- Top runs: {}",
            artifact
                .top_runs
                .iter()
                .map(format_control_matrix_run_summary)
                .collect::<Vec<_>>()
                .join("; ")
        ));
    }
    if let Some(discovery_baseline) = artifact.discovery_summary.baseline.as_ref() {
        lines.push(format!(
            "- Discovery baseline: source={} win_rate={:.2}% strategies={} trades={}",
            discovery_baseline.source,
            discovery_baseline.weighted_win_rate * 100.0,
            discovery_baseline.strategy_count,
            discovery_baseline.total_trade_count
        ));
    } else {
        lines.push(format!(
            "- Discovery baseline: unavailable status={}",
            artifact.discovery_summary.status
        ));
    }
    if !artifact.discovery_summary.top_candidates.is_empty() {
        lines.push(format!(
            "- Discovery top candidates: {}",
            artifact
                .discovery_summary
                .top_candidates
                .iter()
                .map(|candidate| {
                    format!(
                        "{} samples={} win_rate={:.2}% p>{:.0}%={:.3}",
                        candidate.sequence_label,
                        candidate.sample_count,
                        candidate.posterior_mean_win_rate * 100.0,
                        artifact.discovery_summary.threshold_probability * 100.0,
                        candidate.posterior_prob_beats_baseline.unwrap_or_default()
                    )
                })
                .collect::<Vec<_>>()
                .join("; ")
        ));
    }
    redact_local_paths_in_human_text(&lines.join("\n"))
}

pub fn build_control_matrix_research_output_payload(
    artifact: &ControlMatrixResearchArtifact,
) -> Value {
    serde_json::json!({
        "control_matrix_research_run": artifact,
        "control_matrix_plan": artifact.control_matrix_plan,
        "baseline_run": artifact.baseline_run,
        "top_runs": artifact.top_runs,
        "discovery_summary": artifact.discovery_summary,
        "human_output": render_control_matrix_research_human_output(artifact),
    })
}

pub fn emit_structured_output_payload(
    output_format: &str,
    payload: &Value,
    compact_surface: &impl Serialize,
) -> Result<()> {
    match output_format.trim().to_ascii_lowercase().as_str() {
        "json" | "agent" => println!("{}", serde_json::to_string_pretty(payload)?),
        "compact" => print_redacted_json(compact_surface)?,
        "human" => println!(
            "{}",
            redact_local_paths_in_human_text(payload["human_output"].as_str().unwrap_or_default())
        ),
        other => anyhow::bail!("unsupported output format '{}'", other),
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::backtest::{
        build_control_matrix_research_artifact, ControlMatrixDiscoveryBaseline,
        ControlMatrixDiscoveryCandidate, ControlMatrixDiscoverySummary, ControlMatrixPlan,
        ControlMatrixResearchArtifactInput, ControlMatrixResearchRunSummary,
    };
    use crate::factor_lab::research::ResearchReport;
    use crate::state::PersistedFactorRanking;
    use chrono::Utc;

    #[test]
    fn factor_research_human_output_is_short_text_not_json_dump() {
        let mut report = ResearchReport {
            factor_count: 2,
            research_objective: "expansion_manipulation".to_string(),
            best_factor: Some("trend_momentum".to_string()),
            aggregate_return: 0.0123,
            feedback_records_generated: 8,
            feedback_records_applied: 5,
            recommended_next_command:
                "ict-engine factor-research --symbol DEMO --data /tmp/demo.json --state-dir /tmp/state"
                    .to_string(),
            ..ResearchReport::default()
        };
        report.backtest.scorecards = vec![
            PersistedFactorRanking {
                factor_name: "trend_momentum".to_string(),
                composite_score: 0.82,
                grade: "B".to_string(),
                iteration_action: "keep".to_string(),
                ..PersistedFactorRanking::default()
            },
            PersistedFactorRanking {
                factor_name: "structure_ict".to_string(),
                composite_score: 0.49,
                grade: "D".to_string(),
                iteration_action: "observe".to_string(),
                ..PersistedFactorRanking::default()
            },
        ];

        let rendered = render_factor_research_human_output(&report, None);

        assert!(
            !rendered.contains("Factor research summary: {"),
            "human output must not be a serialized JSON dump:\n{rendered}"
        );
        assert!(rendered.starts_with("Factor research summary\n"));
        assert!(rendered.contains("- Objective: expansion_manipulation"));
        assert!(rendered.contains("- Best factor: trend_momentum"));
        assert!(rendered.contains("- Aggregate return: +1.23%"));
        assert!(rendered.contains("- Feedback: generated=8 applied=5"));
        assert!(rendered
            .contains("- Top factors: trend_momentum=0.820 keep B; structure_ict=0.490 observe D"));
        assert!(rendered.contains(
            "- Next: ict-engine factor-research --symbol DEMO --data /tmp/demo.json --state-dir /tmp/state"
        ));
        assert!(rendered.contains("/tmp/demo.json"));
        assert!(!rendered.contains("<local-path>"));
    }

    #[test]
    fn test_factor_research_output_payload_includes_pb12_sweep_summary() {
        let artifact = build_control_matrix_research_artifact(ControlMatrixResearchArtifactInput {
            symbol: "NQ",
            sweep_id: "pb12:NQ:test",
            research_objective: "generic",
            generated_at: Utc::now(),
            control_matrix_plan: ControlMatrixPlan::pb12(),
            discovery_summary: ControlMatrixDiscoverySummary {
                status: "candidates_above_threshold".to_string(),
                threshold_probability: 0.95,
                hold_bars: 6,
                candidate_horizon_bars: 30,
                evaluated_candidate_count: 4,
                promoted_candidate_count: 1,
                baseline: Some(ControlMatrixDiscoveryBaseline {
                    source: "strategy_library_weighted_win_rate".to_string(),
                    weighted_win_rate: 0.52,
                    strategy_count: 2,
                    total_trade_count: 100,
                }),
                top_candidates: vec![ControlMatrixDiscoveryCandidate {
                    sequence_label: "liquidity_sweep -> market_structure_shift".to_string(),
                    direction: crate::types::Direction::Bull,
                    sample_count: 5,
                    win_count: 5,
                    empirical_win_rate: 1.0,
                    posterior_mean_win_rate: 0.8571,
                    posterior_prob_beats_baseline: Some(0.980),
                    average_signed_return: 0.009,
                    first_confirm_bar: 10,
                    latest_confirm_bar: 34,
                }],
            },
            runs: vec![
                ControlMatrixResearchRunSummary {
                    run_number: 1,
                    run_label: "pb12_run_01".to_string(),
                    baseline: false,
                    enabled_toggles: vec!["use_greeks".to_string(), "use_oi".to_string()],
                    disabled_toggles: vec!["use_iv".to_string()],
                    best_factor: Some("trend".to_string()),
                    aggregate_return: 0.0175,
                    feedback_records_generated: 12,
                    feedback_records_applied: 12,
                    dataset_comparable: true,
                    recommended_next_command: "ict-engine factor-research".to_string(),
                },
                ControlMatrixResearchRunSummary {
                    run_number: 12,
                    run_label: "pb12_run_12_baseline".to_string(),
                    baseline: true,
                    enabled_toggles: Vec::new(),
                    disabled_toggles: vec!["use_greeks".to_string()],
                    best_factor: Some("baseline".to_string()),
                    aggregate_return: 0.0045,
                    feedback_records_generated: 6,
                    feedback_records_applied: 6,
                    dataset_comparable: true,
                    recommended_next_command: "ict-engine factor-research".to_string(),
                },
            ],
        });

        let payload = build_control_matrix_research_output_payload(&artifact);

        assert_eq!(
            payload["control_matrix_plan"]["kind"],
            serde_json::json!("pb12")
        );
        assert_eq!(
            payload["control_matrix_research_run"]["run_count"],
            serde_json::json!(2)
        );
        assert_eq!(
            payload["baseline_run"]["run_label"],
            serde_json::json!("pb12_run_12_baseline")
        );
        assert_eq!(
            payload["discovery_summary"]["status"],
            serde_json::json!("candidates_above_threshold")
        );
        let human_output = payload["human_output"].as_str().unwrap_or_default();
        assert!(human_output.contains("PB12 control-matrix research summary"));
        assert!(human_output.contains("pb12_run_01"));
        assert!(human_output.contains("pb12_run_12_baseline"));
        assert!(human_output.contains("Discovery top candidates"));
    }
}
