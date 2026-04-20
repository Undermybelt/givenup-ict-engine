use anyhow::{anyhow, Result};
use serde::Serialize;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

use crate::config::shell_quote;
use crate::state::{
    load_artifact_ledger, load_factor_autoresearch_attempts, load_factor_autoresearch_sessions,
    load_state_or_default, load_workflow_snapshot, AnalyzeRunRecord, BacktestRunRecord,
    FactorMutationRunRecord, ResearchRunRecord, ANALYZE_RUNS_FILE, BACKTEST_RUNS_FILE,
    FACTOR_MUTATION_RUNS_FILE, RESEARCH_RUNS_FILE,
};

#[derive(Debug, Serialize)]
pub struct ResearchVerdictReport {
    symbol: String,
    state_dir: String,
    best_known_baseline: String,
    proven_bad_regions: Vec<String>,
    current_bottleneck: String,
    recommended_next_experiment: String,
    stop_or_continue: String,
    comparison_contaminated: bool,
    contamination_reasons: Vec<String>,
    evidence: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct EvidenceQualityBreakdownReport {
    symbol: String,
    state_dir: String,
    generated_from_run_id: Option<String>,
    gating_status: String,
    final_evidence_quality_score: f64,
    hard_pass_gap: f64,
    neutralized_gap: f64,
    base_score: f64,
    support_gap_contribution: f64,
    uncertainty_penalty: f64,
    directional_conflict_penalty: f64,
    mixed_alignment_penalty: f64,
    mtf_direction_conflict_penalty: f64,
    mtf_alignment_penalty: f64,
    mtf_alignment_bonus: f64,
    mtf_entry_penalty: f64,
    liquidity_penalty_or_bonus: f64,
    bridge_gap: Option<f64>,
    rationale: Vec<String>,
}

pub fn workflow_next_step_view(command: &str, blocked_reason: Option<&str>) -> Value {
    let trimmed = command.trim();
    if trimmed.is_empty() || trimmed == "recommended_command_unavailable" {
        return serde_json::json!({
            "action_type": "none",
            "user_input_required": false,
            "blocked_reason": blocked_reason,
            "prompt": null,
            "deferred_command": null,
        });
    }
    if let Some(rest) = trimmed.strip_prefix("ask-user: ") {
        let mut parts = rest.split(" | blocked until user_selected_historical_data | then ");
        let prompt = parts.next().unwrap_or("").trim();
        let deferred_command = parts.next().unwrap_or("").trim();
        return serde_json::json!({
            "action_type": "ask_user_choose_historical_data",
            "user_input_required": true,
            "blocked_reason": blocked_reason.unwrap_or("user_selected_historical_data_missing"),
            "prompt": prompt,
            "deferred_command": if deferred_command.is_empty() { Value::Null } else { serde_json::json!(deferred_command) },
        });
    }
    serde_json::json!({
        "action_type": "run_command",
        "user_input_required": false,
        "blocked_reason": blocked_reason,
        "prompt": null,
        "deferred_command": trimmed,
    })
}

pub fn research_verdict_command(symbol: &str, state_dir: &str) -> Result<()> {
    let sessions = load_factor_autoresearch_sessions(state_dir, symbol)?;
    let attempts = load_factor_autoresearch_attempts(state_dir, symbol)?;
    let research_runs: Vec<ResearchRunRecord> =
        load_state_or_default(state_dir, symbol, RESEARCH_RUNS_FILE)?;
    let backtest_runs: Vec<BacktestRunRecord> =
        load_state_or_default(state_dir, symbol, BACKTEST_RUNS_FILE)?;
    let mutation_runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE)?;
    let artifact_ledger = load_artifact_ledger(state_dir, symbol)?;

    let mut contamination_reasons = Vec::new();
    if sessions.len() > 1 {
        let unique_objectives = sessions
            .iter()
            .map(|session| session.objective.clone())
            .collect::<BTreeSet<_>>();
        if unique_objectives.len() > 1 {
            contamination_reasons.push(
                "multiple_autoresearch_sessions_share_one_state_dir_with_different_objectives"
                    .to_string(),
            );
        }
        let unique_base_factors = sessions
            .iter()
            .map(|session| session.base_factor.clone())
            .collect::<BTreeSet<_>>();
        if unique_base_factors.len() > 1 {
            contamination_reasons.push(
                "multiple_autoresearch_sessions_share_one_state_dir_with_different_base_factors"
                    .to_string(),
            );
        }
    }
    if attempts.len() > 1 {
        let deltas = attempts
            .iter()
            .map(|attempt| attempt.decision.score_delta)
            .collect::<Vec<_>>();
        let monotonic_up = deltas.windows(2).all(|w| w[1] >= w[0]);
        let monotonic_down = deltas.windows(2).all(|w| w[1] <= w[0]);
        if monotonic_up || monotonic_down {
            contamination_reasons
                .push("attempt_score_deltas_are_monotonic_within_shared_state".to_string());
        }
    }
    if !research_runs.is_empty() && !backtest_runs.is_empty() {
        let research_objectives = research_runs
            .iter()
            .map(|run| run.research_objective.clone())
            .collect::<BTreeSet<_>>();
        if research_objectives.len() > 1 {
            contamination_reasons
                .push("research_runs_mix_multiple_objectives_in_one_state_dir".to_string());
        }
    }
    if mutation_runs.len() > 3 {
        let unique_sources = mutation_runs
            .iter()
            .map(|run| run.source_command.clone())
            .collect::<BTreeSet<_>>();
        if unique_sources.len() > 1 {
            contamination_reasons
                .push("factor_mutation_runs_mix_multiple_sources_in_one_state_dir".to_string());
        }
    }
    let comparison_contaminated = !contamination_reasons.is_empty();

    let best_research = research_runs.iter().max_by(|a, b| {
        a.aggregate_return
            .partial_cmp(&b.aggregate_return)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    let best_backtest = backtest_runs.iter().max_by(|a, b| {
        a.total_return
            .partial_cmp(&b.total_return)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    let cluster_scoreboard = mutation_runs.iter().fold(
        BTreeMap::<String, (usize, f64, f64)>::new(),
        |mut acc, run| {
            let cluster = run
                .mutation_spec
                .direction_hints
                .get("cluster_jump")
                .cloned()
                .unwrap_or_else(|| "none".to_string());
            let entry = acc.entry(cluster).or_insert((0, 0.0, f64::MIN));
            entry.0 += 1;
            entry.1 += run.evaluation.score_delta;
            entry.2 = entry.2.max(run.evaluation.score_delta);
            acc
        },
    );
    let best_cluster = cluster_scoreboard.iter().max_by(|a, b| {
        a.1 .2
            .partial_cmp(&b.1 .2)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    let best_known_baseline = if let Some(run) = best_research {
        format!(
            "research best_factor={} aggregate_return={:.3}",
            run.best_factor
                .clone()
                .unwrap_or_else(|| "unknown".to_string()),
            run.aggregate_return
        )
    } else if let Some(run) = best_backtest {
        format!(
            "backtest return={:.3} trades={}",
            run.total_return, run.trade_count
        )
    } else {
        "no_persisted_research_baseline".to_string()
    };

    let mut proven_bad_regions = attempts
        .iter()
        .flat_map(|attempt| attempt.evaluation.failure_tags.clone())
        .chain(
            mutation_runs
                .iter()
                .flat_map(|run| run.evaluation.failure_tags.clone()),
        )
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    proven_bad_regions.sort();

    let current_bottleneck = if proven_bad_regions
        .iter()
        .any(|tag| tag.contains("bridge_gap"))
    {
        "bridge_gap".to_string()
    } else if proven_bad_regions
        .iter()
        .any(|tag| tag.contains("pre_bayes"))
    {
        "pre_bayes_gate".to_string()
    } else if proven_bad_regions
        .iter()
        .any(|tag| tag.contains("pair_quality") || tag.contains("cross_market"))
    {
        "paired_data_quality".to_string()
    } else if comparison_contaminated {
        "comparison_contamination".to_string()
    } else if best_cluster.is_some() {
        "cluster_search_follow_up".to_string()
    } else {
        "needs_more_evidence".to_string()
    };

    let recommended_next_experiment = match current_bottleneck.as_str() {
        "bridge_gap" => format!(
            "ict-engine evidence-quality-breakdown --symbol {} --state-dir {}",
            shell_quote(symbol),
            shell_quote(state_dir)
        ),
        "pre_bayes_gate" => format!(
            "ict-engine workflow-status --symbol {} --state-dir {} --phase pre-bayes-policy",
            shell_quote(symbol),
            shell_quote(state_dir)
        ),
        "paired_data_quality" => format!(
            "ict-engine factor-pipeline-debug --symbol {} --data <cleaned-15m.json> --factor cross_market_smt --objective expansion_manipulation",
            shell_quote(symbol)
        ),
        "comparison_contamination" => {
            "rerun experiments in an isolated fresh state_dir before comparing results".to_string()
        }
        "cluster_search_follow_up" => {
            let cluster = best_cluster.map(|item| item.0.as_str()).unwrap_or("none");
            format!(
                "continue cluster search around cluster_jump={} with isolated state_dir",
                cluster
            )
        }
        _ => format!(
            "ict-engine factor-autoresearch-status --symbol {} --state-dir {} --latest-only",
            shell_quote(symbol),
            shell_quote(state_dir)
        ),
    };

    let stop_or_continue = if comparison_contaminated {
        "pivot".to_string()
    } else if best_research
        .map(|run| run.aggregate_return >= 0.0)
        .unwrap_or(false)
        && !proven_bad_regions.is_empty()
    {
        "stop_as_local_optimum".to_string()
    } else if artifact_ledger.iter().any(|item| item.actionable) || best_cluster.is_some() {
        "continue".to_string()
    } else {
        "needs_structural_change".to_string()
    };

    let mut evidence = Vec::new();
    evidence.push(format!("autoresearch_sessions={}", sessions.len()));
    evidence.push(format!("autoresearch_attempts={}", attempts.len()));
    evidence.push(format!("research_runs={}", research_runs.len()));
    evidence.push(format!("backtest_runs={}", backtest_runs.len()));
    evidence.push(format!("factor_mutation_runs={}", mutation_runs.len()));
    evidence.push(format!("artifact_rows={}", artifact_ledger.len()));
    if let Some((cluster, (attempts, avg_delta, best_delta))) = best_cluster {
        evidence.push(format!(
            "best_cluster={} attempts={} avg_score_delta={:.3} best_score_delta={:.3}",
            cluster,
            attempts,
            avg_delta / *attempts as f64,
            best_delta
        ));
    }

    let report = ResearchVerdictReport {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        best_known_baseline,
        proven_bad_regions,
        current_bottleneck,
        recommended_next_experiment,
        stop_or_continue,
        comparison_contaminated,
        contamination_reasons,
        evidence,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

pub fn evidence_quality_breakdown_command(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
) -> Result<()> {
    let snapshot = if refresh {
        load_workflow_snapshot(state_dir, symbol)?
    } else {
        load_workflow_snapshot(state_dir, symbol)?
    };
    snapshot
        .latest_analyze
        .as_ref()
        .ok_or_else(|| anyhow!("no latest analyze phase found for '{}'", symbol))?;
    let latest_analyze_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let analyze_run = latest_analyze_runs
        .last()
        .ok_or_else(|| anyhow!("no latest analyze run found for '{}'", symbol))?;
    let filter = &analyze_run.pre_bayes_evidence_filter;
    let bridge = &analyze_run.pre_bayes_entry_quality_bridge;
    let policy = &filter.policy;
    let support_gap = policy.min_directional_support_gap.clamp(0.0, 0.5);
    let base_score = 0.55;
    let support_gap_contribution = support_gap * 0.50;
    let uncertainty_penalty = if filter.filtered_factor_uncertainty == "high" {
        policy.high_uncertainty_threshold * 0.35
    } else {
        0.0
    };
    let directional_conflict_penalty = if filter
        .conflict_flags
        .iter()
        .any(|flag| flag == "directional_conflict")
    {
        policy.directional_conflict_penalty
    } else {
        0.0
    };
    let mixed_alignment_penalty = if filter.filtered_factor_alignment == "mixed" {
        policy.mixed_alignment_penalty
    } else {
        0.0
    };
    let mtf_direction_conflict_penalty = if filter
        .conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_direction_conflict")
    {
        policy.multi_timeframe_direction_conflict_penalty
    } else {
        0.0
    };
    let mtf_alignment_penalty = if filter
        .conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_alignment_weak")
    {
        policy.multi_timeframe_alignment_penalty
    } else {
        0.0
    };
    let mtf_alignment_bonus = if mtf_alignment_penalty == 0.0
        && filter
            .raw_multi_timeframe_alignment_score
            .map(|score| score >= policy.min_multi_timeframe_alignment_score)
            .unwrap_or(false)
    {
        policy.multi_timeframe_alignment_bonus
    } else {
        0.0
    };
    let mtf_entry_penalty = if filter
        .conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_entry_alignment_weak")
    {
        policy.multi_timeframe_entry_penalty
    } else {
        0.0
    };
    let liquidity_penalty_or_bonus = if filter.filtered_liquidity_context_label == "hostile" {
        -policy.hostile_liquidity_penalty
    } else if filter.filtered_liquidity_context_label == "favorable" {
        policy.favorable_liquidity_bonus
    } else {
        0.0
    };
    let hard_pass_gap = filter.evidence_quality_score - policy.hard_pass_quality_threshold;
    let neutralized_gap = filter.evidence_quality_score - policy.neutralized_quality_threshold;
    let bridge_gap = Some((bridge.long_signal_probability - bridge.short_signal_probability).abs());
    let rationale = vec![
        format!("raw_market_regime_label={}", filter.raw_market_regime_label),
        format!(
            "filtered_market_regime_label={}",
            filter.filtered_market_regime_label
        ),
        format!(
            "raw_liquidity_context_label={}",
            filter.raw_liquidity_context_label
        ),
        format!(
            "filtered_liquidity_context_label={}",
            filter.filtered_liquidity_context_label
        ),
        format!("raw_factor_alignment_label={}", filter.raw_factor_alignment),
        format!(
            "filtered_factor_alignment_label={}",
            filter.filtered_factor_alignment
        ),
        format!("conflict_flags={}", filter.conflict_flags.join(",")),
    ];
    let report = EvidenceQualityBreakdownReport {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        generated_from_run_id: Some(analyze_run.run_id.clone()),
        gating_status: filter.gating_status.clone(),
        final_evidence_quality_score: filter.evidence_quality_score,
        hard_pass_gap,
        neutralized_gap,
        base_score,
        support_gap_contribution,
        uncertainty_penalty,
        directional_conflict_penalty,
        mixed_alignment_penalty,
        mtf_direction_conflict_penalty,
        mtf_alignment_penalty,
        mtf_alignment_bonus,
        mtf_entry_penalty,
        liquidity_penalty_or_bonus,
        bridge_gap,
        rationale,
    };
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}
