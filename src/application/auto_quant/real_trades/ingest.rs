//! JSONL → FeedbackRecord ingest path with content-hash idempotency.
//!
//! The ledger artifact_kind is `auto_quant_real_trades_ingested`.
//! Every ingest run pins `source_run_id = content_hash`, which is
//! the SipHash of the source JSONL bytes. A second run against the
//! same file is rejected unless `--force` is set, so accidental
//! double-ingestion (which would silently double the effective
//! evidence weight on the trade_outcome CPT) cannot happen.

use anyhow::{anyhow, bail, Context, Result};
use chrono::Utc;
use std::collections::BTreeMap;

use crate::application::backtest::apply_feedback_to_trade_outcome_network;
use crate::application::entry_models::export_policy_training_tables;
use crate::application::orchestration::export_structural_path_ranking_target;
use crate::application::provider_catalog::provider_status_agent_surface;
use crate::bbn::trading::persistence::load_or_init_trading_network;
use crate::config::compute_hash;
use crate::state::{
    append_artifact_ledger_entry, append_learning_feedback_batch, load_state_or_default,
    load_workflow_snapshot, save_state, ArtifactLedgerEntry, FeedbackRecord, LearningState,
    PreBayesEvidenceFilter, UpdateRunRecord, ARTIFACT_LEDGER_FILE, BBN_STATE_FILE,
};

use super::wire::RealTradeRecord;

/// Ledger artifact_kind for this ingest path.
pub const ARTIFACT_KIND_REAL_TRADES: &str = "auto_quant_real_trades_ingested";

/// Rule version recorded on every real-trades ledger entry. Bump on
/// any change to the wire schema, idempotency key, or evidence
/// computation.
pub const REAL_TRADES_RULE_VERSION: &str = "auto-quant-real-trades-v1";

/// Operator-facing input for `ingest_real_trades`.
#[derive(Debug, Clone)]
pub struct IngestRealTradesInput<'a> {
    pub symbol: &'a str,
    pub state_dir: &'a str,
    pub trades_path: &'a str,
    pub source: &'a str,
    pub dry_run: bool,
    pub force: bool,
}

/// Outcome of an ingest run, suitable for serialising to stdout
/// alongside the ledger artifact id.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IngestRealTradesOutcome {
    pub artifact_id: String,
    pub status: &'static str,
    pub trades_total: u32,
    pub trades_applied: u32,
    pub trades_invalid: u32,
    pub feedback_records_inserted: u32,
    pub content_hash: String,
    pub previous_artifact_id: Option<String>,
}

/// Read + validate the JSONL trades file, apply the implied
/// `FeedbackRecord`s through the trading-network update path, and
/// emit a ledger entry summarising the run.
pub fn ingest_real_trades(input: IngestRealTradesInput<'_>) -> Result<IngestRealTradesOutcome> {
    let raw = std::fs::read_to_string(input.trades_path).with_context(|| {
        format!(
            "reading real-trades JSONL artifact at '{}'",
            input.trades_path
        )
    })?;

    let content_hash = compute_hash(&[raw.as_str()]);

    let previous = find_existing_for_hash(input.state_dir, input.symbol, &content_hash)?;
    if !input.force {
        if let Some(prev_id) = &previous {
            bail!(
                "refusing to re-ingest the same JSONL: a prior \
                 auto_quant_real_trades_ingested entry with content_hash \
                 '{}' exists ({}); pass --force after rolling back the BBN \
                 to override",
                content_hash,
                prev_id
            );
        }
    }

    let timestamp = Utc::now();
    let artifact_id = format!(
        "auto_quant_real_trades_{}_{}",
        input.symbol,
        timestamp.format("%Y%m%dT%H%M%S%.9fZ")
    );

    let (records, invalid_count) = parse_jsonl(&raw, input.trades_path)?;
    let total: u32 = (records.len() + invalid_count) as u32;

    if records.is_empty() {
        // Same status whether or not invalid_count > 0: no records
        // mean no CPT mutation, by definition. The invalid count is
        // surfaced separately in `review_reason` for audit.
        let status = "no_op";
        write_ledger(
            input,
            &artifact_id,
            timestamp,
            status,
            total,
            0,
            invalid_count as u32,
            0,
            &content_hash,
        )?;
        return Ok(IngestRealTradesOutcome {
            artifact_id,
            status,
            trades_total: total,
            trades_applied: 0,
            trades_invalid: invalid_count as u32,
            feedback_records_inserted: 0,
            content_hash,
            previous_artifact_id: previous,
        });
    }

    if input.dry_run {
        let status = "dry_run_preview";
        write_ledger(
            input,
            &artifact_id,
            timestamp,
            status,
            total,
            records.len() as u32,
            invalid_count as u32,
            0,
            &content_hash,
        )?;
        return Ok(IngestRealTradesOutcome {
            artifact_id,
            status,
            trades_total: total,
            trades_applied: records.len() as u32,
            trades_invalid: invalid_count as u32,
            feedback_records_inserted: 0,
            content_hash,
            previous_artifact_id: previous,
        });
    }

    // Build feedback records, anchoring run_id on the ingest
    // artifact when the source did not carry one.
    let feedback_records = records
        .into_iter()
        .map(|r| {
            let mut fr = r.into_feedback_record(input.source);
            if fr.run_id.is_none() {
                fr.run_id = Some(artifact_id.clone());
            }
            fr
        })
        .collect::<Vec<_>>();
    let trades_applied = feedback_records.len() as u32;

    // Apply the CPT update first so the BBN snapshot is consistent
    // with what we report below. Fail-loudly: no partial mutation.
    let mut network = load_or_init_trading_network(input.symbol, input.state_dir)?;
    let updates_applied = apply_feedback_to_trade_outcome_network(&mut network, &feedback_records)?;

    save_state(input.state_dir, input.symbol, BBN_STATE_FILE, &network)?;

    let mut feedback_records_inserted: u32 = 0;
    if !feedback_records.is_empty() {
        let learning_state = append_learning_feedback_batch(
            std::path::Path::new(input.state_dir),
            input.symbol,
            &feedback_records,
        )?;
        append_update_runs_for_real_trade_feedback(
            input.state_dir,
            input.symbol,
            &artifact_id,
            &feedback_records,
        )?;
        refresh_policy_targets_after_real_trade_ingest(
            input.state_dir,
            input.symbol,
            &learning_state,
        )
        .with_context(|| {
            format!(
                "refreshing policy targets after real-trade ingest for '{}'",
                input.symbol
            )
        })?;
        // We surface the CPT-evidence count rather than
        // `learning_state.feedback_history.len()`. The latter is the
        // running total across all symbols' history (deduped on
        // (symbol, timestamp, source, trade_id)), which is useful
        // for audit elsewhere but not the right granularity here.
        feedback_records_inserted = updates_applied.min(u32::MAX as usize) as u32;
    }

    let status = if trades_applied > 0 {
        "applied"
    } else {
        "no_op"
    };

    write_ledger(
        input,
        &artifact_id,
        timestamp,
        status,
        total,
        trades_applied,
        invalid_count as u32,
        feedback_records_inserted,
        &content_hash,
    )?;

    Ok(IngestRealTradesOutcome {
        artifact_id,
        status,
        trades_total: total,
        trades_applied,
        trades_invalid: invalid_count as u32,
        feedback_records_inserted,
        content_hash,
        previous_artifact_id: previous,
    })
}

fn parse_jsonl(raw: &str, path_label: &str) -> Result<(Vec<RealTradeRecord>, usize)> {
    let mut records = Vec::new();
    let mut invalid = 0usize;
    for (idx, line) in raw.lines().enumerate() {
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        match serde_json::from_str::<RealTradeRecord>(trimmed) {
            Ok(record) => match record.validate() {
                Ok(_) => records.push(record),
                Err(e) => {
                    log::warn!(
                        "real-trades JSONL '{}' line {}: validation failed: {}",
                        path_label,
                        idx + 1,
                        e
                    );
                    invalid += 1;
                }
            },
            Err(e) => {
                log::warn!(
                    "real-trades JSONL '{}' line {}: parse failed: {}",
                    path_label,
                    idx + 1,
                    e
                );
                invalid += 1;
            }
        }
    }
    Ok((records, invalid))
}

fn append_update_runs_for_real_trade_feedback(
    state_dir: &str,
    symbol: &str,
    artifact_id: &str,
    feedback_records: &[FeedbackRecord],
) -> Result<()> {
    for (index, feedback) in feedback_records.iter().enumerate() {
        let trade_id = feedback
            .trade_id
            .as_deref()
            .filter(|value| !value.trim().is_empty())
            .map(str::to_string)
            .unwrap_or_else(|| format!("row-{index}"));
        crate::state::append_update_run(
            state_dir,
            symbol,
            UpdateRunRecord {
                run_id: format!("update:{symbol}:{artifact_id}:{trade_id}"),
                timestamp: feedback.timestamp,
                symbol: symbol.to_string(),
                source_command: "auto-quant-ingest-real-trades".to_string(),
                normalized_entry_quality: "auto_quant_real_trade".to_string(),
                factor_alignment: "structural_feedback".to_string(),
                factor_uncertainty: "realized_trade".to_string(),
                realized_outcome: feedback.realized_outcome.clone(),
                structural_feedback: feedback.structural_feedback.clone(),
                consumed_pre_bayes_evidence_filter:
                    consumed_pre_bayes_filter_from_real_trade_feedback(feedback),
                feedback_records_applied: 1,
                consumed_artifact_path: Some(artifact_id.to_string()),
                ..UpdateRunRecord::default()
            },
        )?;
    }
    Ok(())
}

fn consumed_pre_bayes_filter_from_real_trade_feedback(
    feedback: &FeedbackRecord,
) -> Option<PreBayesEvidenceFilter> {
    let refs = feedback.structural_feedback.as_ref()?;
    let mut evidence_assignments = BTreeMap::new();
    evidence_assignments.insert("parent_regime_root".to_string(), refs.node_id.clone());
    evidence_assignments.insert(
        "regime_profit_branch_path".to_string(),
        refs.path_id.clone(),
    );
    evidence_assignments.insert(
        "pre_bayes_branch_path_gate".to_string(),
        "observe_only".to_string(),
    );
    evidence_assignments.insert(
        "structural_feedback_recommendation_id".to_string(),
        refs.recommendation_id.clone(),
    );
    evidence_assignments.insert(
        "structural_feedback_branch_id".to_string(),
        refs.branch_id.clone(),
    );
    evidence_assignments.insert(
        "structural_feedback_scenario_id".to_string(),
        refs.scenario_id.clone(),
    );

    let factor_alignment = match feedback.model_probabilities_before_trade.selected_direction {
        crate::types::Direction::Bull => "bull",
        crate::types::Direction::Bear => "bear",
        crate::types::Direction::Neutral => "structural_feedback",
    }
    .to_string();
    let evidence_quality_score = feedback
        .model_probabilities_before_trade
        .selected_probability
        .clamp(0.0, 1.0);

    Some(PreBayesEvidenceFilter {
        raw_market_regime_label: refs.node_id.clone(),
        raw_liquidity_context_label: "structural_feedback".to_string(),
        raw_factor_alignment: factor_alignment.clone(),
        raw_factor_uncertainty: "realized_trade".to_string(),
        filtered_market_regime_label: refs.node_id.clone(),
        filtered_liquidity_context_label: "structural_feedback".to_string(),
        filtered_factor_alignment: factor_alignment,
        filtered_factor_uncertainty: "realized_trade".to_string(),
        evidence_quality_score,
        gating_status: "observe_only".to_string(),
        pass_to_bbn: false,
        rationale: vec![
            "auto_quant_real_trade_structural_feedback_consumed_as_observe_only".to_string(),
        ],
        evidence_assignments,
        ..PreBayesEvidenceFilter::default()
    })
}

fn refresh_policy_targets_after_real_trade_ingest(
    state_dir: &str,
    symbol: &str,
    learning_state: &LearningState,
) -> Result<()> {
    if let Err(err) = export_policy_training_tables(state_dir, symbol) {
        log::warn!(
            "policy training table export after real-trade ingest failed for '{}': {}",
            symbol,
            err
        );
    }
    let snapshot = load_workflow_snapshot(state_dir, symbol).unwrap_or_default();
    let provider_status_agent = provider_status_agent_surface(None, None, None).unwrap_or_default();
    export_structural_path_ranking_target(
        state_dir,
        symbol,
        &snapshot,
        &provider_status_agent,
        &learning_state.feedback_history,
        &learning_state.structural_prior_state,
    )?;
    Ok(())
}

fn find_existing_for_hash(
    state_dir: &str,
    symbol: &str,
    content_hash: &str,
) -> Result<Option<String>> {
    let ledger: Vec<ArtifactLedgerEntry> =
        load_state_or_default(state_dir, symbol, ARTIFACT_LEDGER_FILE)?;
    Ok(ledger
        .into_iter()
        .rev()
        .find(|e| {
            e.artifact_kind == ARTIFACT_KIND_REAL_TRADES
                && e.status == "applied"
                && e.source_run_id.as_deref() == Some(content_hash)
        })
        .map(|e| e.artifact_id))
}

#[allow(clippy::too_many_arguments)]
fn write_ledger(
    input: IngestRealTradesInput<'_>,
    artifact_id: &str,
    timestamp: chrono::DateTime<Utc>,
    status: &'static str,
    trades_total: u32,
    trades_applied: u32,
    trades_invalid: u32,
    feedback_records_inserted: u32,
    content_hash: &str,
) -> Result<()> {
    let path = std::path::Path::new(input.trades_path)
        .canonicalize()
        .map(|p| p.to_string_lossy().into_owned())
        .unwrap_or_else(|_| input.trades_path.to_string());

    let review_reason = format!(
        "ingested {trades_applied}/{trades_total} (invalid {trades_invalid}) \
         feedback_inserted={feedback_records_inserted} content_hash={content_hash} \
         dry_run={dry_run} force={force}",
        dry_run = input.dry_run,
        force = input.force,
    );

    append_artifact_ledger_entry(
        input.state_dir,
        input.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", artifact_id),
            artifact_kind: ARTIFACT_KIND_REAL_TRADES.to_string(),
            artifact_id: artifact_id.to_string(),
            version: 1,
            generated_at: timestamp,
            symbol: input.symbol.to_string(),
            source_phase: "auto_quant_real_trades".to_string(),
            source_run_id: Some(content_hash.to_string()),
            path,
            status: status.to_string(),
            promote_candidate: false,
            actionable: false,
            decision_hint: format!("ingested {trades_applied} trade(s)"),
            review_reason,
            review_rule_version: REAL_TRADES_RULE_VERSION.to_string(),
            quality_score: trades_applied.min(i32::MAX as u32) as i32,
            ..Default::default()
        },
    )
    .map_err(|e| anyhow!("failed to append real-trades ledger entry: {e}"))?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::real_trades::wire::SCHEMA_VERSION;

    fn good_jsonl_line() -> String {
        let s = format!(
            r#"{{"schema_version":"{}","symbol":"NQ","trade_id":"t-1","strategy_name":"S","strategy_mutation_id":"m-1","auto_quant_run_id":"run-1","open_ts_ms":1745423100000,"close_ts_ms":1745427900000,"direction":"Bull","pnl":0.0123,"realized_outcome":"win","regime_at_entry":"expansion","entry_signal":"strong_buy","factors_used":[]}}"#,
            SCHEMA_VERSION
        );
        s
    }

    fn structural_branch_jsonl_line() -> String {
        let branch_path =
            "TrendExpansion -> SessionLiquidity -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1";
        serde_json::json!({
            "schema_version": SCHEMA_VERSION,
            "symbol": "NQ",
            "trade_id": "t-structural-1",
            "strategy_name": "SweepReclaim",
            "strategy_mutation_id": "sweep-v1",
            "auto_quant_run_id": "run-structural-1",
            "open_ts_ms": 1745423100000_i64,
            "close_ts_ms": 1745427900000_i64,
            "direction": "Bull",
            "pnl": 0.0123,
            "realized_outcome": "win",
            "regime_at_entry": "expansion",
            "entry_signal": "strong_buy",
            "regime_profit_branch_path": branch_path,
            "main_regime": "TrendExpansion",
            "sub_regime": "SessionLiquidity",
            "sub_sub_regime_or_profit_factor": "sweep_reclaim_small_cycle",
            "profit_factor": "liquidity_sweep_reclaim_15m_wide_v1",
            "factors_used": []
        })
        .to_string()
    }

    fn branch_jsonl_line() -> String {
        serde_json::json!({
            "schema_version": SCHEMA_VERSION,
            "symbol": "NQ",
            "trade_id": "t-branch-1",
            "strategy_name": "S",
            "strategy_mutation_id": "m-branch-1",
            "auto_quant_run_id": "run-branch-1",
            "open_ts_ms": 1745423100000_i64,
            "close_ts_ms": 1745427900000_i64,
            "direction": "Bull",
            "pnl": 0.0123,
            "realized_outcome": "win",
            "regime_at_entry": "expansion",
            "entry_signal": "strong_buy",
            "regime_profit_branch_path": "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1",
            "main_regime": "Transition",
            "sub_regime": "LiquiditySweep",
            "sub_sub_regime_or_profit_factor": "sweep_reclaim_small_cycle",
            "profit_factor": "liquidity_sweep_reclaim_15m_wide_v1",
            "model_probabilities_before_trade": {
                "selected_direction": "Bull",
                "selected_probability": 0.62,
                "long_score": 0.62,
                "short_score": 0.38,
                "win_prob_long": 0.62,
                "win_prob_short": 0.38,
                "uncertainty": 0.12
            },
            "factors_used": []
        })
        .to_string()
    }

    fn write_jsonl(path: &std::path::Path, lines: &[String]) {
        std::fs::write(path, lines.join("\n")).unwrap();
    }

    #[test]
    fn no_op_when_file_is_empty() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        std::fs::write(&trades, "").unwrap();

        let outcome = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        assert_eq!(outcome.status, "no_op");
        assert_eq!(outcome.trades_applied, 0);
        assert_eq!(outcome.trades_invalid, 0);
    }

    #[test]
    fn applied_status_when_one_valid_trade() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[good_jsonl_line()]);

        let outcome = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        assert_eq!(outcome.status, "applied");
        assert_eq!(outcome.trades_applied, 1);
        assert_eq!(outcome.feedback_records_inserted, 1);
        assert!(outcome.previous_artifact_id.is_none());

        // Ledger entry pins content_hash as source_run_id.
        let ledger: Vec<ArtifactLedgerEntry> =
            load_state_or_default(state_dir, "NQ", ARTIFACT_LEDGER_FILE).unwrap();
        let entry = ledger
            .iter()
            .find(|e| e.artifact_kind == ARTIFACT_KIND_REAL_TRADES)
            .expect("real-trades ledger entry");
        assert_eq!(
            entry.source_run_id.as_deref(),
            Some(outcome.content_hash.as_str())
        );
        assert_eq!(entry.status, "applied");
    }

    #[test]
    fn structural_real_trade_ingest_refreshes_policy_target_consumption_surfaces() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[structural_branch_jsonl_line()]);

        ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        let status =
            crate::application::entry_models::policy_training_status(state_dir, "NQ", None)
                .unwrap();

        assert_eq!(status.update_runs, 1);
        assert_eq!(
            status
                .structural_path_ranking_target
                .update_runs_with_structural_feedback,
            1
        );
        assert_eq!(
            status
                .structural_path_ranking_target
                .feedback_rows_with_structural_feedback,
            1
        );
        assert_eq!(
            status.structural_path_ranking_target.feedback_rows_matured,
            1
        );
        assert!(status.structural_path_ranking_target.mature_rows >= 1);
        assert!(
            status
                .structural_path_ranking_target
                .rows_with_training_weight
                >= 1
        );
    }

    #[test]
    fn structural_real_trade_ingest_records_consumed_pre_bayes_filter() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[structural_branch_jsonl_line()]);

        ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        let update_runs: Vec<UpdateRunRecord> =
            load_state_or_default(state_dir, "NQ", crate::state::UPDATE_RUNS_FILE).unwrap();
        let run = update_runs.first().expect("real-trade update run");
        let filter = run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .expect("structural real-trade update run should consume a Pre-Bayes filter");

        assert_eq!(filter.gating_status, "observe_only");
        assert!(!filter.pass_to_bbn);
        assert_eq!(
            filter
                .evidence_assignments
                .get("parent_regime_root")
                .map(String::as_str),
            Some("TrendExpansion")
        );
        assert_eq!(
            filter
                .evidence_assignments
                .get("regime_profit_branch_path")
                .map(String::as_str),
            Some(
                "TrendExpansion -> SessionLiquidity -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
            )
        );
        assert_eq!(
            filter
                .evidence_assignments
                .get("pre_bayes_branch_path_gate")
                .map(String::as_str),
            Some("observe_only")
        );
    }

    #[test]
    fn second_run_with_same_content_refused_without_force() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[good_jsonl_line()]);

        ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        let err = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap_err();
        assert!(
            err.to_string().contains("refusing to re-ingest"),
            "got {err}"
        );
    }

    #[test]
    fn force_allows_second_run_and_records_lineage() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[good_jsonl_line()]);

        let first = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        let second = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: true,
        })
        .unwrap();

        assert_eq!(first.content_hash, second.content_hash);
        assert_eq!(
            second.previous_artifact_id.as_deref(),
            Some(first.artifact_id.as_str())
        );
    }

    #[test]
    fn dry_run_does_not_persist_bbn() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[good_jsonl_line()]);

        let outcome = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: true,
            force: false,
        })
        .unwrap();

        assert_eq!(outcome.status, "dry_run_preview");
        assert_eq!(outcome.feedback_records_inserted, 0);
        // No BBN snapshot was written.
        assert!(
            !crate::state::state_exists(state_dir, "NQ", BBN_STATE_FILE),
            "dry-run must not write a BBN snapshot"
        );
    }

    #[test]
    fn dry_run_preview_does_not_block_first_real_ingest() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[good_jsonl_line()]);

        let preview = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: true,
            force: false,
        })
        .unwrap();
        assert_eq!(preview.status, "dry_run_preview");

        let applied = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        assert_eq!(applied.status, "applied");
        assert_eq!(applied.trades_applied, 1);
        assert_eq!(applied.previous_artifact_id, None);
    }

    #[test]
    fn invalid_lines_are_counted_and_skipped() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(
            &trades,
            &[
                good_jsonl_line(),
                "this is not valid json".to_string(),
                r#"{"schema_version":"9.9","symbol":"NQ","trade_id":"t","strategy_name":"S","open_ts_ms":0,"close_ts_ms":0,"direction":"Bull","pnl":0.0}"#.to_string(),
            ],
        );

        let outcome = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        assert_eq!(outcome.trades_total, 3);
        assert_eq!(outcome.trades_applied, 1);
        assert_eq!(outcome.trades_invalid, 2);
    }

    #[test]
    fn real_trades_ingest_refreshes_policy_target_training_rows() {
        let dir = tempfile::tempdir().unwrap();
        let state_dir = dir.path().to_str().unwrap();
        let trades = dir.path().join("trades.jsonl");
        write_jsonl(&trades, &[branch_jsonl_line()]);

        let outcome = ingest_real_trades(IngestRealTradesInput {
            symbol: "NQ",
            state_dir,
            trades_path: trades.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();
        assert_eq!(outcome.status, "applied");

        let status =
            crate::application::entry_models::policy_training_status(state_dir, "NQ", None)
                .unwrap();

        assert_eq!(
            status
                .structural_path_ranking_target
                .feedback_rows_with_structural_feedback,
            1
        );
        assert!(
            status
                .structural_path_ranking_target
                .rows_with_training_weight
                >= 1,
            "real AQ structural feedback should be exported as policy target training rows: {:?}",
            status.structural_path_ranking_target
        );
        assert!(
            status.structural_path_ranking_target.mature_rows >= 1,
            "real AQ structural feedback should be mature policy target evidence"
        );
    }
}
