use super::*;
use crate::analyze_shared::AnalyzeStageTrace;
use ict_engine::application::multi_timeframe_inputs::resolve_interval_for_analyze_slot;
use ict_engine::application::regime::consumer_bundle_adapter::RegimeConsumerBundleAdapter;
use std::path::Path;

#[allow(clippy::too_many_arguments)]
pub(crate) fn analyze_command(
    symbol: &str,
    data_htf: &str,
    data_mtf: &str,
    data_ltf: &str,
    state_dir: &str,
    output_format: OutputFormat,
    inline_ledger: bool,
    execution_focus: bool,
    regime_consumer_bundle: Option<&str>,
    regime_consumer_bundle_strict: bool,
    apply_regime_bundle_bbn_soft_evidence: bool,
) -> Result<()> {
    let stage_trace = AnalyzeStageTrace::maybe_from_env();
    stage_trace.event("analyze_command:start");
    let regime_bundle_adapter = RegimeConsumerBundleAdapter::load_optional_or_strategy_library(
        regime_consumer_bundle.map(Path::new),
        regime_consumer_bundle_strict,
        state_dir,
        symbol,
    )?;
    stage_trace.event("analyze_command:regime_bundle_ready");
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;
    stage_trace.event("analyze_command:scorecards_ready");
    let htf = load_candles(data_htf)?;
    let mtf = load_candles(data_mtf)?;
    let ltf = load_candles(data_ltf)?;
    stage_trace.event("analyze_command:primary_candles_loaded");
    let resolved_multi_timeframe_inputs =
        resolve_analyze_multi_timeframe_inputs(data_htf, data_mtf, data_ltf);
    let d1_owned = resolved_multi_timeframe_inputs
        .get("1d")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let h4_owned = resolved_multi_timeframe_inputs
        .get("4h")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let h1_owned = resolved_multi_timeframe_inputs
        .get("1h")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m15_owned = resolved_multi_timeframe_inputs
        .get("15m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m30_owned = resolved_multi_timeframe_inputs
        .get("30m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m5_owned = resolved_multi_timeframe_inputs
        .get("5m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m1_owned = resolved_multi_timeframe_inputs
        .get("1m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let multi_timeframe_summary =
        build_multi_timeframe_summary(data_ltf, &resolved_multi_timeframe_inputs)?;
    let multi_timeframe_signal =
        build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?;
    let analyze_multi_timeframe_summary = multi_timeframe_summary
        .iter()
        .chain(multi_timeframe_signal.summary.iter())
        .cloned()
        .collect::<Vec<_>>();
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let learning_state = load_learning_state(state_dir, symbol)?;
    stage_trace.event("analyze_command:state_and_models_ready");
    let report = build_analyze_report(BuildAnalyzeReportInput {
        symbol,
        state_dir,
        htf: &htf,
        mtf: &mtf,
        ltf: &ltf,
        params: &params,
        network: &network,
        build_context: AnalyzeBuildContext {
            symbol,
            paired_candles: None,
            auxiliary: None,
            learning_state: &learning_state,
            multi_timeframe_summary: &analyze_multi_timeframe_summary,
            native_frames: AnalyzeNativeFrames {
                d1: if resolve_interval_for_analyze_slot(data_htf, "1d") == "1d" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "1d" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "1d" {
                    Some(&ltf)
                } else {
                    d1_owned.as_deref()
                },
                h4: if resolve_interval_for_analyze_slot(data_htf, "1d") == "4h" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "4h" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "4h" {
                    Some(&ltf)
                } else {
                    h4_owned.as_deref()
                },
                h1: if resolve_interval_for_analyze_slot(data_htf, "1d") == "1h" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "1h" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "1h" {
                    Some(&ltf)
                } else {
                    h1_owned.as_deref()
                },
                m30: if resolve_interval_for_analyze_slot(data_htf, "1d") == "30m" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "30m" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "30m" {
                    Some(&ltf)
                } else {
                    m30_owned.as_deref()
                },
                m15: if resolve_interval_for_analyze_slot(data_htf, "1d") == "15m" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "15m" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "15m" {
                    Some(&ltf)
                } else {
                    m15_owned.as_deref()
                },
                m5: if resolve_interval_for_analyze_slot(data_htf, "1d") == "5m" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "5m" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "5m" {
                    Some(&ltf)
                } else {
                    m5_owned.as_deref()
                },
                m1: if resolve_interval_for_analyze_slot(data_htf, "1d") == "1m" {
                    Some(&htf)
                } else if resolve_interval_for_analyze_slot(data_mtf, "1h") == "1m" {
                    Some(&mtf)
                } else if resolve_interval_for_analyze_slot(data_ltf, "15m") == "1m" {
                    Some(&ltf)
                } else {
                    m1_owned.as_deref()
                },
            },
        },
        regime_bundle_adapter: regime_bundle_adapter.as_ref(),
        apply_regime_bundle_bbn_soft_evidence,
        execution_focus,
    })?;
    stage_trace.event("analyze_command:build_analyze_report_done");
    let mut report = report;
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    stage_trace.event("analyze_command:artifact_trends_loaded");
    augment_action_plan_with_artifact_trends(
        &mut report.supporting.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.supporting.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    if let Some(bundle_path) = regime_consumer_bundle {
        if let Some(adapter) = regime_bundle_adapter.as_ref() {
            let trace_entries = adapter.trace_entries(Some(Path::new(bundle_path)));
            report
                .supporting
                .artifact_action_summary
                .push(format!("regime_bundle_trace:{}", trace_entries.join("|")));
            report
                .supporting
                .artifact_action_summary
                .extend(trace_entries);
            adapter.append_read_only_bbn_diagnostics(
                &mut report.supporting.artifact_action_summary,
                &mut report.supporting.pre_bayes_evidence_filter,
            );
        }
    }
    if let Ok(artifact) = ict_engine::pda_sequence::load_pda_sequence_analysis(state_dir, symbol) {
        let summary = ict_engine::pda_sequence::summarize_pda_sequence_artifact(&artifact);
        report.supporting.artifact_action_summary.push(format!(
            "pda_sequence:{} confidence={:.3} consistency={:.3}",
            summary
                .primary_cluster_label
                .unwrap_or_else(|| "unknown".to_string()),
            summary.primary_cluster_confidence.unwrap_or_default(),
            summary.consistency_ratio,
        ));
    }
    let pending_update_file =
        persist_pending_update_artifact_from_analyze(state_dir, &report, "analyze")?;
    stage_trace.event("analyze_command:pending_update_persisted");
    let _execution_candidate_file =
        persist_execution_candidate_from_analyze(state_dir, &report, "analyze")?;
    stage_trace.event("analyze_command:execution_candidate_persisted");
    report.supporting.artifact_decision_summary =
        artifact_decision_summary_for_symbol(state_dir, symbol)?;
    stage_trace.event("analyze_command:artifact_decision_summary_ready");
    report.supporting.artifact_decision_section = artifact_decision_section_from_parts(
        &report.supporting.artifact_decision_summary,
        &report.supporting.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    apply_command_context_to_analyze_report(
        &mut report,
        &CommandContext {
            symbol: symbol.to_string(),
            state_dir: state_dir.to_string(),
            analyze: Some(AnalyzeCommandSource::Files {
                data_htf: data_htf.to_string(),
                data_mtf: data_mtf.to_string(),
                data_ltf: data_ltf.to_string(),
            }),
            research_data: Some(data_ltf.to_string()),
            paired_data: None,
            update_outcome: None,
            update_entry_signal: None,
            update_feedback_file: Some(pending_update_file),
            user_data_selection_required: false,
        },
    );
    stage_trace.event("analyze_command:command_context_applied");
    report.supporting.workflow_snapshot = persist_analyze_run(
        state_dir,
        &report,
        "analyze",
        Some(data_htf),
        Some(data_mtf),
        Some(data_ltf),
        None,
    )?;
    stage_trace.event("analyze_command:persist_analyze_run_done");
    report.supporting.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.supporting.workflow_snapshot,
        &report.supporting.artifact_action_summary,
    );
    report.supporting.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.supporting.workflow_snapshot);
    append_artifact_decision_prompt(
        &mut report.supporting.agent_prompts,
        symbol,
        &report.supporting.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.supporting.artifact_decision_summary,
        &mut report.supporting.promotion_decision,
        &mut report.supporting.rollback_recommendation,
    );
    stage_trace.event("analyze_command:final_output_emit");

    emit_analyze_output(&report, output_format, inline_ledger)
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, TimeZone, Utc};
    use ict_engine::application::auto_quant::results::STRATEGY_LIBRARY_FILE;
    use ict_engine::state::load_state;
    use ict_engine::state::ExecutionCandidateArtifact;

    fn sample_candles(count: usize) -> Vec<Candle> {
        let start = Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap();
        (0..count)
            .map(|index| {
                let drift = index as f64 * 0.35;
                Candle {
                    timestamp: start + Duration::minutes(index as i64),
                    open: 100.0 + drift,
                    high: 100.6 + drift,
                    low: 99.4 + drift,
                    close: 100.3 + drift,
                    volume: 1_000.0 + index as f64,
                }
            })
            .collect()
    }

    fn write_test_candles(path: &Path, count: usize) {
        std::fs::write(path, serde_json::to_string(&sample_candles(count)).unwrap()).unwrap();
    }

    #[test]
    fn analyze_command_auto_loads_branch_path_from_imported_strategy_library() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");
        let branch_path = "Transition -> MarketStructureEvent -> atr_cisd_direct_limit -> market_structure_event_classifier_atr_cisd_direct_limit_v1";

        write_test_candles(&htf, 220);
        write_test_candles(&mtf, 180);
        write_test_candles(&ltf, 140);

        let symbol_dir = temp.path().join("auto-quant").join("NQ");
        std::fs::create_dir_all(&symbol_dir).unwrap();
        std::fs::write(
            symbol_dir.join(STRATEGY_LIBRARY_FILE),
            serde_json::to_string(&serde_json::json!({
                "manifest_version": "1.0",
                "strategies": [{
                    "name": "MarketStructureEventClassifierAtrCisdDirectLimitV1",
                    "status": "ok",
                    "metadata": {
                        "strategy": "MarketStructureEventClassifierAtrCisdDirectLimitV1",
                        "mutation_id": "market-structure-event-atr-cisd-direct-limit-v1",
                        "base_factor": "market_structure_event_classifier",
                        "hypothesis": "branch survives auto load",
                        "paradigm": "regime_rooted_market_structure_event",
                        "expected_regime": branch_path,
                        "main_regime": "Transition",
                        "sub_regime": "MarketStructureEvent",
                        "sub_sub_regime_or_profit_factor": "atr_cisd_direct_limit",
                        "profit_factor": "market_structure_event_classifier_atr_cisd_direct_limit_v1",
                        "regime_profit_branch_path": branch_path,
                        "promotion_allowed": false,
                        "trade_usable": false
                    },
                    "validation_metrics": {
                        "win_rate_pct": 71.95572,
                        "trade_count": 542
                    }
                }]
            }))
            .unwrap(),
        )
        .unwrap();

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
            OutputFormat::Json,
            false,
            true,
            None,
            false,
            false,
        )
        .unwrap();

        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();
        let candidate: ExecutionCandidateArtifact = load_state(
            temp.path(),
            "NQ",
            ict_engine::state::EXECUTION_CANDIDATE_FILE,
        )
        .unwrap();
        let assignments = &candidate
            .pre_bayes_evidence_filter
            .as_ref()
            .expect("execution candidate should embed pre-Bayes filter")
            .evidence_assignments;
        assert_eq!(
            assignments.get("regime_profit_branch_path"),
            Some(&branch_path.to_string())
        );
        assert_eq!(
            assignments.get("regime_bundle_stable_profit_score"),
            Some(&"0.719557".to_string())
        );

        let learning_state = load_learning_state(temp.path().to_str().unwrap(), "NQ").unwrap();
        let provider_status_agent =
            ict_engine::application::provider_catalog::ProviderCatalogAgentSurface::default();
        let target_summary =
            ict_engine::application::orchestration::export_structural_path_ranking_target(
                temp.path().to_str().unwrap(),
                "NQ",
                &snapshot,
                &provider_status_agent,
                &[],
                &learning_state.structural_prior_state,
            )
            .unwrap();
        let target_csv = std::fs::read_to_string(&target_summary.csv_path).unwrap();
        assert!(target_csv.contains(branch_path));
        assert!(!snapshot.recommended_next_command.contains("ask-user:"));
    }
}
