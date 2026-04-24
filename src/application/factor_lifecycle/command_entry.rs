use anyhow::Result;
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};

use crate::application::factor_lifecycle::{
    build_hint_effectiveness_summary, compare_hint_effectiveness,
    factor_mutation_direction_hint_summary, factor_mutation_recommended_focus,
    factor_mutation_step_size_hint_summary, FactorMutationPerFactorHintSummary,
};
use crate::config::shell_quote;
use crate::state::{load_state_or_default, FactorMutationRunRecord, FACTOR_MUTATION_RUNS_FILE};

#[derive(Debug, Serialize)]
pub struct FactorMutationFailureCluster {
    tag: String,
    count: usize,
    latest_mutation_id: Option<String>,
    average_score_delta: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct FactorMutationSourceSummary {
    source_command: String,
    total_runs: usize,
    accepted_runs: usize,
    latest_mutation_id: Option<String>,
    average_score_delta: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct FactorMutationReasonSummary {
    reason: String,
    count: usize,
    markets: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct FactorMutationMarketSummary {
    market: String,
    count: usize,
    reasons: Vec<String>,
}

fn factor_mutation_research_command(symbol: &str, data: &str, state_dir: &str) -> String {
    format!(
        "ict-engine factor-research --symbol {} --data {} --state-dir {}",
        shell_quote(symbol),
        shell_quote(data),
        shell_quote(state_dir)
    )
}

pub fn factor_mutation_status_command(
    symbol: &str,
    state_dir: &str,
    source_command: Option<&str>,
    latest_only: bool,
    accepted_only: bool,
    bucket_by_source: bool,
    limit: Option<usize>,
) -> Result<()> {
    let mut runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE)?;
    if let Some(source_command) = source_command {
        runs.retain(|run| run.source_command == source_command);
    }
    runs.sort_by_key(|run| run.timestamp);
    runs.reverse();
    if latest_only {
        runs.truncate(1);
    }
    if accepted_only {
        runs.retain(|run| run.evaluation.accepted);
    }
    if let Some(limit) = limit {
        runs.truncate(limit);
    }
    let all_runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE)?;
    let all_runs = all_runs
        .into_iter()
        .filter(|run| {
            source_command
                .map(|expected| run.source_command == expected)
                .unwrap_or(true)
        })
        .collect::<Vec<_>>();
    let mut failure_tag_counts = BTreeMap::<String, usize>::new();
    let mut regression_reason_counts = BTreeMap::<String, usize>::new();
    let mut regression_reason_markets = BTreeMap::<String, BTreeSet<String>>::new();
    let mut market_reason_counts = BTreeMap::<String, usize>::new();
    let mut market_reasons = BTreeMap::<String, BTreeSet<String>>::new();
    let mut direction_hint_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut direction_hint_accepts = BTreeMap::<String, usize>::new();
    let mut step_hint_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut step_hint_accepts = BTreeMap::<String, usize>::new();
    let mut per_factor_direction_hint_deltas =
        BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut per_factor_direction_hint_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    let mut per_factor_step_hint_deltas = BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut per_factor_step_hint_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    let mut cluster_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut cluster_latest = BTreeMap::<String, String>::new();
    for run in &all_runs {
        for tag in &run.evaluation.failure_tags {
            *failure_tag_counts.entry(tag.clone()).or_default() += 1;
            cluster_deltas
                .entry(tag.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            cluster_latest.insert(tag.clone(), run.evaluation.mutation_id.clone());
        }
        for (market, reasons) in &run.evaluation.metrics_after.regression_reasons_by_market {
            *market_reason_counts.entry(market.clone()).or_default() += 1;
            for reason in reasons {
                *regression_reason_counts.entry(reason.clone()).or_default() += 1;
                regression_reason_markets
                    .entry(reason.clone())
                    .or_default()
                    .insert(market.clone());
                market_reasons
                    .entry(market.clone())
                    .or_default()
                    .insert(reason.clone());
            }
        }
        for (parameter, hint) in &run.mutation_spec.direction_hints {
            let label = format!("{}:{}", parameter, hint);
            direction_hint_deltas
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            per_factor_direction_hint_deltas
                .entry(run.mutation_spec.base_factor.clone())
                .or_default()
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *direction_hint_accepts.entry(label.clone()).or_default() += 1;
                *per_factor_direction_hint_accepts
                    .entry(run.mutation_spec.base_factor.clone())
                    .or_default()
                    .entry(label)
                    .or_default() += 1;
            }
        }
        for (parameter, step) in &run.mutation_spec.step_size_hints {
            let label = format!("{}:{:.4}", parameter, step);
            step_hint_deltas
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            per_factor_step_hint_deltas
                .entry(run.mutation_spec.base_factor.clone())
                .or_default()
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *step_hint_accepts.entry(label.clone()).or_default() += 1;
                *per_factor_step_hint_accepts
                    .entry(run.mutation_spec.base_factor.clone())
                    .or_default()
                    .entry(label)
                    .or_default() += 1;
            }
        }
    }
    let mut failure_clusters = failure_tag_counts
        .iter()
        .map(|(tag, count)| FactorMutationFailureCluster {
            tag: tag.clone(),
            count: *count,
            latest_mutation_id: cluster_latest.get(tag).cloned(),
            average_score_delta: cluster_deltas
                .get(tag)
                .map(|values| values.iter().sum::<f64>() / values.len() as f64)
                .unwrap_or_default(),
        })
        .collect::<Vec<_>>();
    failure_clusters.sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.tag.cmp(&b.tag)));
    let mut runs_by_source = BTreeMap::<String, Vec<&FactorMutationRunRecord>>::new();
    for run in &all_runs {
        runs_by_source
            .entry(run.source_command.clone())
            .or_default()
            .push(run);
    }
    let mut source_summaries = runs_by_source
        .into_iter()
        .map(
            |(source_command, grouped_runs)| FactorMutationSourceSummary {
                source_command,
                total_runs: grouped_runs.len(),
                accepted_runs: grouped_runs
                    .iter()
                    .filter(|run| run.evaluation.accepted)
                    .count(),
                latest_mutation_id: grouped_runs
                    .iter()
                    .max_by_key(|run| run.timestamp)
                    .map(|run| run.evaluation.mutation_id.clone()),
                average_score_delta: if grouped_runs.is_empty() {
                    0.0
                } else {
                    grouped_runs
                        .iter()
                        .map(|run| run.evaluation.score_delta)
                        .sum::<f64>()
                        / grouped_runs.len() as f64
                },
            },
        )
        .collect::<Vec<_>>();
    source_summaries.sort_by(|a, b| {
        b.total_runs
            .cmp(&a.total_runs)
            .then_with(|| a.source_command.cmp(&b.source_command))
    });
    let mut regression_reason_summaries = regression_reason_counts
        .into_iter()
        .map(|(reason, count)| FactorMutationReasonSummary {
            markets: regression_reason_markets
                .remove(&reason)
                .map(|items| items.into_iter().collect::<Vec<_>>())
                .unwrap_or_default(),
            reason,
            count,
        })
        .collect::<Vec<_>>();
    regression_reason_summaries
        .sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.reason.cmp(&b.reason)));
    let mut market_regression_summaries = market_reason_counts
        .into_iter()
        .map(|(market, count)| FactorMutationMarketSummary {
            reasons: market_reasons
                .remove(&market)
                .map(|items| items.into_iter().collect::<Vec<_>>())
                .unwrap_or_default(),
            market,
            count,
        })
        .collect::<Vec<_>>();
    market_regression_summaries
        .sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.market.cmp(&b.market)));
    let mut direction_hint_effectiveness = direction_hint_deltas
        .into_iter()
        .map(|(hint, deltas)| {
            build_hint_effectiveness_summary(
                &hint,
                &deltas,
                direction_hint_accepts
                    .get(&hint)
                    .copied()
                    .unwrap_or_default(),
            )
        })
        .collect::<Vec<_>>();
    direction_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
    let mut step_size_hint_effectiveness = step_hint_deltas
        .into_iter()
        .map(|(hint, deltas)| {
            build_hint_effectiveness_summary(
                &hint,
                &deltas,
                step_hint_accepts.get(&hint).copied().unwrap_or_default(),
            )
        })
        .collect::<Vec<_>>();
    step_size_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
    let mut per_factor_hint_effectiveness = per_factor_direction_hint_deltas
        .into_iter()
        .map(|(base_factor, direction_entries)| {
            let mut direction_hint_effectiveness = direction_entries
                .into_iter()
                .map(|(hint, deltas)| {
                    let accepted_runs = per_factor_direction_hint_accepts
                        .get(&base_factor)
                        .and_then(|entries| entries.get(&hint))
                        .copied()
                        .unwrap_or_default();
                    build_hint_effectiveness_summary(&hint, &deltas, accepted_runs)
                })
                .collect::<Vec<_>>();
            direction_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
            let mut step_size_hint_effectiveness = per_factor_step_hint_deltas
                .get(&base_factor)
                .cloned()
                .unwrap_or_default()
                .into_iter()
                .map(|(hint, deltas)| {
                    let accepted_runs = per_factor_step_hint_accepts
                        .get(&base_factor)
                        .and_then(|entries| entries.get(&hint))
                        .copied()
                        .unwrap_or_default();
                    build_hint_effectiveness_summary(&hint, &deltas, accepted_runs)
                })
                .collect::<Vec<_>>();
            step_size_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
            FactorMutationPerFactorHintSummary {
                base_factor,
                direction_hint_effectiveness,
                step_size_hint_effectiveness,
            }
        })
        .collect::<Vec<_>>();
    per_factor_hint_effectiveness.sort_by(|a, b| a.base_factor.cmp(&b.base_factor));
    let priority_markets = market_regression_summaries
        .iter()
        .take(3)
        .map(|summary| summary.market.clone())
        .collect::<Vec<_>>();
    let priority_regression_reasons = regression_reason_summaries
        .iter()
        .take(3)
        .map(|summary| summary.reason.clone())
        .collect::<Vec<_>>();
    let recommended_next_mutation_focus =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_recommended_focus(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    let latest_direction_hints =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_direction_hint_summary(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    let latest_step_size_hints =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_step_size_hint_summary(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "symbol": symbol,
            "source_command_filter": source_command,
            "bucket_by_source": bucket_by_source,
            "total_runs": all_runs.len(),
            "accepted_runs": all_runs.iter().filter(|run| run.evaluation.accepted).count(),
            "latest_run": all_runs.iter().max_by_key(|run| run.timestamp).cloned(),
            "priority_markets": priority_markets,
            "priority_regression_reasons": priority_regression_reasons,
            "recommended_next_mutation_focus": recommended_next_mutation_focus,
            "latest_direction_hints": latest_direction_hints,
            "latest_step_size_hints": latest_step_size_hints,
            "direction_hint_effectiveness": direction_hint_effectiveness,
            "step_size_hint_effectiveness": step_size_hint_effectiveness,
            "per_factor_hint_effectiveness": per_factor_hint_effectiveness,
            "failure_tag_counts": failure_tag_counts,
            "failure_clusters": failure_clusters,
            "regression_reason_summaries": regression_reason_summaries,
            "market_regression_summaries": market_regression_summaries,
            "source_summaries": if bucket_by_source { source_summaries.clone() } else { Vec::<FactorMutationSourceSummary>::new() },
            "runs": runs,
            "recommended_commands": [
                format!(
                    "ict-engine factor-mutation-status --symbol {} --state-dir {} --limit 10{}{}",
                    shell_quote(symbol),
                    shell_quote(state_dir),
                    source_command.map(|value| format!(" --source-command {}", shell_quote(value))).unwrap_or_default(),
                    if bucket_by_source { " --bucket-by-source" } else { "" }
                ),
                format!(
                    "{} --mutation-spec <spec.json> --emit-mutation-evaluation",
                    factor_mutation_research_command(symbol, "<data.json>", state_dir)
                ),
                format!(
                    "ict-engine expansion-sop --root {} --output-dir <output> --interval 15m --lookback 20 --atr-multiplier 1.50 --mutation-spec <spec.json> --emit-mutation-evaluation",
                    shell_quote(
                        &crate::application::multi_timeframe_inputs::detected_tomac_root_or_placeholder()
                    )
                ),
            ]
        }))?
    );
    Ok(())
}
