use anyhow::{anyhow, bail, Context, Result};
use chrono::{SecondsFormat, Utc};
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};

use super::{
    structural_path_ranking_ips_weight, structural_path_ranking_reward_label,
    structural_path_ranking_training_weight, StructuralPathRankingTargetArtifact,
    StructuralPathRankingTargetExportSummary, StructuralPathRankingTargetRow,
};
use crate::state::{
    append_artifact_ledger_entry, artifact_state_path, save_state, save_text_state,
    ArtifactLedgerEntry,
};

#[derive(Debug, Clone, Eq, PartialEq)]
pub struct FactorCandidateBranchFields {
    pub main_regime: String,
    pub sub_regime: String,
    pub sub_sub_regime_or_profit_factor: String,
    pub profit_factor: String,
    pub regime_profit_branch_path: String,
}

pub fn resolve_factor_candidate_branch_fields(
    expression: &Value,
    fallback_main_regime: &str,
    fallback_sub_regime: String,
    fallback_sub_sub_regime_or_profit_factor: String,
    fallback_profit_factor: String,
) -> FactorCandidateBranchFields {
    let contract = expression
        .get("branch_path_contract")
        .and_then(Value::as_object);
    let contract_path = contract
        .and_then(|value| value.get("regime_profit_branch_path"))
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty());
    let parsed_segments = contract_path.and_then(|path| {
        let parts = path
            .split("->")
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .collect::<Vec<_>>();
        (parts.len() >= 4).then(|| {
            (
                parts[0].to_string(),
                parts[1].to_string(),
                parts[2].to_string(),
                parts[3..].join(" -> "),
            )
        })
    });
    let contract_str = |key: &str| -> Option<String> {
        contract
            .and_then(|value| value.get(key))
            .and_then(Value::as_str)
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .map(ToString::to_string)
    };
    let main_regime = contract_str("main_regime")
        .or_else(|| parsed_segments.as_ref().map(|segments| segments.0.clone()))
        .unwrap_or_else(|| fallback_main_regime.to_string());
    let sub_regime = contract_str("sub_regime")
        .or_else(|| parsed_segments.as_ref().map(|segments| segments.1.clone()))
        .unwrap_or(fallback_sub_regime);
    let sub_sub_regime_or_profit_factor = contract_str("sub_sub_regime_or_profit_factor")
        .or_else(|| parsed_segments.as_ref().map(|segments| segments.2.clone()))
        .unwrap_or(fallback_sub_sub_regime_or_profit_factor);
    let profit_factor = contract_str("profit_factor")
        .or_else(|| parsed_segments.as_ref().map(|segments| segments.3.clone()))
        .unwrap_or(fallback_profit_factor);
    let regime_profit_branch_path = contract_path.map(ToString::to_string).unwrap_or_else(|| {
        format!(
            "{main_regime} -> {sub_regime} -> {sub_sub_regime_or_profit_factor} -> {profit_factor}"
        )
    });

    FactorCandidateBranchFields {
        main_regime,
        sub_regime,
        sub_sub_regime_or_profit_factor,
        profit_factor,
        regime_profit_branch_path,
    }
}

pub fn candidate_pack_root_slug(candidate_pack_root: &str) -> String {
    let root = std::path::Path::new(candidate_pack_root);
    let raw = root
        .file_name()
        .and_then(|name| name.to_str())
        .filter(|value| !value.trim().is_empty())
        .unwrap_or(candidate_pack_root);
    let mut slug = String::with_capacity(raw.len());
    let mut previous_was_sep = false;
    for ch in raw.chars() {
        if ch.is_ascii_alphanumeric() {
            slug.push(ch.to_ascii_lowercase());
            previous_was_sep = false;
        } else if matches!(ch, '-' | '_') {
            slug.push(ch);
            previous_was_sep = false;
        } else if !previous_was_sep {
            slug.push('-');
            previous_was_sep = true;
        }
    }
    let slug = slug.trim_matches('-').trim_matches('_');
    if slug.is_empty() {
        "candidate-pack-root".to_string()
    } else {
        slug.to_string()
    }
}

pub fn build_factor_candidate_admission_target_artifact(
    candidate_pack_root: &str,
    symbol: &str,
) -> Result<StructuralPathRankingTargetArtifact> {
    let root = std::path::Path::new(candidate_pack_root);
    if !root.exists() {
        bail!(
            "candidate pack root does not exist: '{}'",
            candidate_pack_root
        );
    }
    let mut pack_dirs = std::fs::read_dir(root)
        .with_context(|| {
            format!(
                "failed to read candidate pack root '{}'",
                candidate_pack_root
            )
        })?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.is_dir())
        .collect::<Vec<_>>();
    pack_dirs.sort();

    let candidate_set_root = candidate_pack_root_slug(candidate_pack_root);
    let candidate_set_id = format!("factor-candidate-admission:{symbol}:{candidate_set_root}");
    let generated_at = Utc::now().to_rfc3339_opts(SecondsFormat::Secs, true);
    let mut rows = Vec::new();
    for pack_dir in pack_dirs.iter() {
        let expression = read_candidate_pack_json(pack_dir, "factor_expression.json")?;
        let eval_summary = read_candidate_pack_json(pack_dir, "factor_eval_grid_summary.json")?;
        let transfer = read_candidate_pack_json(pack_dir, "transfer_score.json")?;
        let candidate_id = expression
            .get("candidate_id")
            .and_then(Value::as_str)
            .or_else(|| pack_dir.file_name().and_then(|name| name.to_str()))
            .unwrap_or("unknown");
        let family = value_str(&expression, "family").unwrap_or("candidate_family");
        let paradigm = value_str(&expression, "paradigm").unwrap_or("candidate_pack");
        let timeframe = value_str(&expression, "base_timeframe").unwrap_or("unknown_timeframe");
        let main_regime = value_str(&expression, "expected_regime")
            .filter(|value| !value.trim().is_empty())
            .unwrap_or("candidate_pack");
        let family_key = family.replace(' ', "_").to_lowercase();
        let base_profit_factor = candidate_id.to_string();
        let breadth_matrix = eval_summary
            .get("breadth_matrix")
            .and_then(Value::as_object);
        let market_evidence = transfer.get("market_evidence").and_then(Value::as_object);
        let mut markets = BTreeSet::new();
        if let Some(matrix) = breadth_matrix {
            markets.extend(matrix.keys().cloned());
        }
        if let Some(evidence) = market_evidence {
            markets.extend(evidence.keys().cloned());
        }
        if markets.is_empty() {
            markets.insert("candidate_market".to_string());
        }
        markets.insert("AGGREGATE".to_string());
        let transfer_candidate =
            transfer.get("status").and_then(Value::as_str) == Some("cross_market_candidate");
        for market in markets {
            let market_eval = breadth_matrix.and_then(|matrix| matrix.get(&market));
            let market_transfer = market_evidence.and_then(|evidence| evidence.get(&market));
            let metric = |key: &str| -> Option<f64> {
                market_eval
                    .and_then(|value| value.get(key))
                    .and_then(Value::as_f64)
                    .or_else(|| {
                        market_transfer
                            .and_then(|value| value.get(key))
                            .and_then(Value::as_f64)
                    })
                    .or_else(|| {
                        eval_summary
                            .pointer(&format!("/aggregate_metrics/{key}"))
                            .and_then(Value::as_f64)
                    })
            };
            let trade_count = metric("trade_count").unwrap_or(0.0);
            let aggregate_profit_factor = metric("profit_factor");
            let total_profit_pct = metric("total_profit_pct");
            let sharpe = metric("sharpe");
            let lifecycle = eval_summary.get("factor_profitability_lifecycle");
            let learning_admission_status = lifecycle
                .and_then(|value| value.pointer("/learning_admission/status"))
                .and_then(Value::as_str);
            let learning_expectancy = lifecycle
                .and_then(|value| {
                    value.pointer("/learning_admission/long_run_expectancy_after_declared_friction")
                })
                .and_then(Value::as_f64);
            let live_trade_status = lifecycle
                .and_then(|value| value.pointer("/live_trade/status"))
                .and_then(Value::as_str);
            let learning_only_positive = learning_admission_status == Some("admitted")
                && learning_expectancy.unwrap_or(0.0) > 0.0;
            let density_label = market_eval
                .and_then(|value| value.get("trade_density_label"))
                .and_then(Value::as_str)
                .or_else(|| {
                    eval_summary
                        .pointer("/trade_density_summary/aggregate_label")
                        .and_then(Value::as_str)
                })
                .unwrap_or("unknown");
            let preferred_density = density_label == "preferred_density";
            let full_profit_observation = trade_count >= 30.0
                && aggregate_profit_factor.is_some()
                && total_profit_pct.is_some();
            let external_score_observation = !full_profit_observation && sharpe.is_some();
            let pending_reward_state = if learning_only_positive && !full_profit_observation {
                "regime_conditioned_learning_success"
            } else if full_profit_observation
                && aggregate_profit_factor.is_some_and(|value| value > 1.0)
                && total_profit_pct.is_some_and(|value| value > 0.0)
            {
                "matured_success"
            } else if full_profit_observation {
                "matured_failure"
            } else if external_score_observation && sharpe.is_some_and(|value| value > 0.0) {
                "matured_success"
            } else if external_score_observation {
                "matured_failure"
            } else {
                "candidate_pack_admission_pending"
            };
            let learning_only = pending_reward_state == "regime_conditioned_learning_success";
            let calibrated_label = if learning_only {
                None
            } else {
                structural_path_ranking_reward_label(pending_reward_state)
            };
            let maturity_mask = calibrated_label.is_some();
            let maturity_weight = if learning_only {
                0.0
            } else if full_profit_observation {
                1.0
            } else if external_score_observation {
                0.5
            } else {
                0.0
            };
            let behavior_policy_probability = if preferred_density && transfer_candidate {
                0.50
            } else if preferred_density {
                0.35
            } else {
                0.20
            };
            let propensity_estimate = maturity_mask.then_some(behavior_policy_probability);
            let ips_weight = structural_path_ranking_ips_weight(propensity_estimate);
            let training_weight = structural_path_ranking_training_weight(
                calibrated_label,
                maturity_weight,
                ips_weight,
            );
            let raw_path_score = transfer
                .get("overall_transfer_score")
                .and_then(Value::as_f64)
                .or_else(|| sharpe.map(|value| (value + 1.0) / 2.0))
                .map(|value| value.clamp(0.0, 1.0));
            let calibrated_path_prob = maturity_mask.then_some(raw_path_score.unwrap_or(0.5));
            let baseline = raw_path_score.unwrap_or(0.0);
            let normalized_expectancy_prior = learning_only.then(|| {
                let expectancy = learning_expectancy.unwrap_or(0.0);
                (0.5 + expectancy.tanh() / 2.0).clamp(0.0, 1.0)
            });
            let learning_live_blocked = learning_only && live_trade_status != Some("ready");
            let learning_execution_gate_status =
                learning_live_blocked.then_some("learning_admitted_live_blocked".to_string());
            let learning_execution_gate_reason = learning_live_blocked
                .then_some("learning admission is not live trade usability".to_string());
            let target_policy_reward_lower_bound =
                normalized_expectancy_prior.map(|value| (value - 0.10).max(0.0));
            let current_posterior = normalized_expectancy_prior.unwrap_or(baseline);
            let market_key = market.replace(['/', ' '], "_").to_lowercase();
            let fallback_sub_regime = market_key;
            let fallback_sub_sub_regime_or_profit_factor =
                format!("{}:{}:{}", family_key, paradigm, timeframe);
            let fallback_profit_factor = format!("{base_profit_factor}@{market}");
            let branch_fields = resolve_factor_candidate_branch_fields(
                &expression,
                main_regime,
                fallback_sub_regime,
                fallback_sub_sub_regime_or_profit_factor,
                fallback_profit_factor,
            );
            rows.push(StructuralPathRankingTargetRow {
                rank: rows.len() + 1,
                candidate_set_id: candidate_set_id.clone(),
                candidate_set_size: 0,
                path_id: branch_fields.regime_profit_branch_path.clone(),
                scenario_id: format!("factor_candidate:{candidate_id}:{market}"),
                path_label: format!(
                    "{} [{}]",
                    value_str(&expression, "display_name").unwrap_or(candidate_id),
                    market
                ),
                regime_profit_branch_path: Some(branch_fields.regime_profit_branch_path),
                parent_regime_root: Some(branch_fields.main_regime.clone()),
                main_regime: Some(branch_fields.main_regime),
                sub_regime: Some(branch_fields.sub_regime),
                sub_sub_regime_or_profit_factor: Some(
                    branch_fields.sub_sub_regime_or_profit_factor,
                ),
                profit_factor: Some(branch_fields.profit_factor),
                direction: "Observe".to_string(),
                raw_path_score,
                calibrated_path_prob,
                path_prob_lower_bound: None,
                execution_gate_status: learning_execution_gate_status,
                execution_gate_min_path_prob: None,
                execution_gate_reason: learning_execution_gate_reason,
                pending_reward_state: pending_reward_state.to_string(),
                maturity_mask,
                maturity_weight,
                calibrated_label,
                propensity_estimate,
                ips_weight,
                training_weight,
                regime_calibration_bucket: format!("{symbol}:factor_candidate_admission"),
                behavior_policy_probability,
                execution_propensity: None,
                target_policy_probability_confidence: None,
                target_policy_probability_lower_bound: None,
                target_policy_reward_prior: normalized_expectancy_prior,
                target_policy_reward_lower_bound,
                experience_prior: (trade_count / 2500.0).clamp(0.0, 1.0),
                current_posterior,
                structural_baseline_score: baseline,
                regime_aux_qqq_hv_level: None,
                regime_aux_nq_vs_200d_pct: None,
                regime_aux_vix3m_level: None,
                regime_aux_qqq_hv_pct_rank_252: None,
                regime_aux_vvix_over_vix: None,
                ref_previous_day_high: None,
                ref_previous_day_low: None,
                ref_previous_day_close: None,
                ref_current_day_open: None,
                ref_previous_week_high: None,
                ref_previous_week_low: None,
                ref_previous_week_close: None,
                ref_current_week_open: None,
                ref_previous_month_high: None,
                ref_previous_month_low: None,
                ref_current_day_gap_upper: None,
                ref_current_day_gap_lower: None,
                ref_current_week_gap_upper: None,
                ref_current_week_gap_lower: None,
                ref_recent_week_gap_levels: None,
                ob_variant: None,
                ob_direction: None,
                ob_validation_state: None,
                ob_high: None,
                ob_low: None,
                ob_midpoint: None,
                ob_mitigation_count: None,
                ob_breaker_confirmed: None,
                ob_rejection_confirmed: None,
                ob_confidence: None,
                ob_fail_closed_reason: None,
                score_model_family: Some("candidate_pack_transfer_score_v1".to_string()),
                score_source_kind: Some("factor_candidate_pack_admission_seed".to_string()),
                score_model_artifact_uri: Some(pack_dir.to_string_lossy().to_string()),
                score_generator: Some("factor-candidate-admission-targets".to_string()),
            });
        }
    }
    let candidate_set_size = rows.len();
    for row in &mut rows {
        row.candidate_set_size = candidate_set_size;
    }
    Ok(StructuralPathRankingTargetArtifact {
        protocol_version: "structural-path-ranking-target-v1".to_string(),
        symbol: symbol.to_string(),
        candidate_set_id,
        candidate_set_size,
        generated_at,
        rows,
    })
}

pub fn build_factor_candidate_pack_inventory(candidate_pack_root: &str) -> Result<Value> {
    let root = std::path::Path::new(candidate_pack_root);
    if !root.exists() {
        bail!(
            "candidate pack root does not exist: '{}'",
            candidate_pack_root
        );
    }
    if !root.is_dir() {
        bail!(
            "candidate pack root is not a directory: '{}'",
            candidate_pack_root
        );
    }
    let mut pack_dirs = std::fs::read_dir(root)
        .with_context(|| {
            format!(
                "failed to read candidate pack root '{}'",
                candidate_pack_root
            )
        })?
        .filter_map(|entry| entry.ok().map(|entry| entry.path()))
        .filter(|path| path.is_dir())
        .collect::<Vec<_>>();
    pack_dirs.sort();

    let mut candidates = Vec::new();
    for pack_dir in pack_dirs {
        let expression = read_candidate_pack_json(&pack_dir, "factor_expression.json")?;
        let eval_summary = read_candidate_pack_json(&pack_dir, "factor_eval_grid_summary.json")?;
        let transfer = read_candidate_pack_json(&pack_dir, "transfer_score.json")?;
        let trade_density = eval_summary
            .get("trade_density_summary")
            .and_then(Value::as_object)
            .ok_or_else(|| {
                anyhow!(
                    "candidate pack '{}' missing trade_density_summary",
                    pack_dir.display()
                )
            })?;
        let candidate_id = expression
            .get("candidate_id")
            .and_then(Value::as_str)
            .or_else(|| pack_dir.file_name().and_then(|name| name.to_str()))
            .unwrap_or("unknown");
        candidates.push(serde_json::json!({
            "candidate_id": candidate_id,
            "display_name": expression.get("display_name").cloned().unwrap_or(Value::Null),
            "family": expression.get("family").cloned().unwrap_or(Value::Null),
            "strategy_name": expression.get("strategy_name").cloned().unwrap_or(Value::Null),
            "promotion_state": expression.get("promotion_state").cloned().unwrap_or(Value::Null),
            "base_timeframe": expression.get("base_timeframe").cloned().unwrap_or(Value::Null),
            "branch_path_contract": expression
                .get("branch_path_contract")
                .cloned()
                .unwrap_or(Value::Null),
            "expression_text": expression.get("expression_text").cloned().unwrap_or(Value::Null),
            "timeframe_ladder_evidence": eval_summary
                .get("timeframe_ladder_evidence")
                .cloned()
                .unwrap_or(Value::Null),
            "timeframe_ladder_transfer": transfer
                .get("timeframe_ladder_transfer")
                .cloned()
                .unwrap_or(Value::Null),
            "pack_dir": pack_dir.to_string_lossy(),
            "aggregate_trade_count": trade_density
                .get("aggregate_trade_count")
                .cloned()
                .unwrap_or(Value::Null),
            "aggregate_label": trade_density
                .get("aggregate_label")
                .cloned()
                .unwrap_or(Value::Null),
            "transfer_status": transfer.get("status").cloned().unwrap_or(Value::Null),
        }));
    }

    Ok(serde_json::json!({
        "schema_version": "factor-candidate-pack-inventory/v1",
        "summary": {
            "candidate_pack_root": candidate_pack_root,
            "candidate_pack_count": candidates.len(),
        },
        "candidates": candidates,
    }))
}

pub fn persist_factor_candidate_pack_inventory(
    state_dir: &str,
    symbol: &str,
    payload: &Value,
) -> Result<String> {
    let filename = "factor_candidate_pack_inventory.json";
    save_state(state_dir, symbol, filename, payload)?;
    let path = artifact_state_path(state_dir, symbol, filename);
    let generated_at = Utc::now();
    let candidate_count = payload
        .pointer("/summary/candidate_pack_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    append_artifact_ledger_entry(
        state_dir,
        symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:factor-candidate-pack-inventory:{symbol}"),
            artifact_kind: "factor_candidate_pack_inventory".to_string(),
            artifact_id: format!(
                "factor-candidate-pack-inventory:{symbol}:{}",
                generated_at.format("%Y%m%dT%H%M%SZ")
            ),
            version: 1,
            generated_at,
            symbol: symbol.to_string(),
            source_phase: "factor-candidate-packs".to_string(),
            source_run_id: None,
            path: path.clone(),
            status: "ready".to_string(),
            promote_candidate: false,
            actionable: false,
            decision_hint: "inspect_candidate_packs_before_admission".to_string(),
            review_reason: format!("candidate_pack_count={candidate_count}"),
            review_rule_version: "factor-candidate-pack-inventory/v1".to_string(),
            top_factor_name: None,
            top_factor_action: Some("inspect".to_string()),
            family_scores: BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: candidate_count.min(i32::MAX as u64) as i32,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    Ok(path)
}

pub fn build_factor_candidate_ranker_direct_model_artifact() -> Value {
    serde_json::json!({
        "protocol_version": "structural-path-ranker-direct-model-v1",
        "model_family": "weighted_feature_sum_v1",
        "feature_schema_version": "structural-path-ranking-target-v1",
        "output_transform": "identity_clamped",
        "intercept": 0.0,
        "numerical_feature_weights": {
            "raw_path_score": 0.70,
            "training_weight": 0.05,
            "experience_prior": 0.15,
            "current_posterior": 0.10
        },
        "lower_bound_margin": 0.0,
        "notes": [
            "generated_by=factor-candidate-admission-targets",
            "runtime_not_enabled_by_default",
            "scores rank offline candidate-pack observations only; execution gates remain disabled"
        ]
    })
}

pub fn build_factor_candidate_trainer_artifact(
    summary: &StructuralPathRankingTargetExportSummary,
    created_at: &str,
) -> Value {
    serde_json::json!({
        "protocol_version": "structural-path-ranking-trainer-artifact-v1",
        "dataset_role": summary.trainer_manifest.dataset_role.clone(),
        "model_family": "weighted_feature_sum_v1",
        "artifact_uri": "factor_candidate_ranker_direct_model.json",
        "model_artifact_uri": "factor_candidate_ranker_direct_model.json",
        "score_column": "raw_path_score",
        "trained_rows": summary.rows_with_training_weight,
        "history_rows": summary.history_rows,
        "calibration_rows": summary.history_rows_with_calibrated_path_prob,
        "selected_features": summary.trainer_manifest.feature_columns.clone(),
        "validation_metrics": {
            "raw_scored_mature_rows": summary.history_rows_with_raw_path_score,
            "raw_scored_mature_min_rows": 30,
            "production_validation_rows": 0,
            "production_validation_min_rows": 30
        },
        "calibration_metrics": {
            "eligible_rows": 0
        },
        "created_at": created_at,
        "notes": [
            "generated_by=factor-candidate-admission-targets",
            "trainer_ready_for_observation_only",
            "runtime_not_enabled_by_default",
            "production_validation_still_required"
        ]
    })
}

pub fn write_factor_candidate_trainer_artifacts(
    state_dir: &str,
    symbol: &str,
    summary: &StructuralPathRankingTargetExportSummary,
) -> Result<()> {
    std::fs::create_dir_all(
        std::path::Path::new(state_dir)
            .join(symbol)
            .join("policy_training"),
    )?;
    let model_name = "factor_candidate_ranker_direct_model.json";
    let model = build_factor_candidate_ranker_direct_model_artifact();
    save_text_state(
        state_dir,
        symbol,
        &format!("policy_training/{model_name}"),
        &serde_json::to_string_pretty(&model)?,
    )?;
    let created_at = Utc::now().to_rfc3339();
    let trainer = build_factor_candidate_trainer_artifact(summary, &created_at);
    save_text_state(
        state_dir,
        symbol,
        "policy_training/structural_path_ranking_trainer_artifact.json",
        &serde_json::to_string_pretty(&trainer)?,
    )?;
    append_artifact_ledger_entry(
        state_dir,
        symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:factor-candidate-trainer-artifact:{symbol}"),
            artifact_kind: "structural_path_ranking_trainer_artifact".to_string(),
            artifact_id: format!("factor-candidate-trainer:{symbol}"),
            version: 1,
            generated_at: Utc::now(),
            symbol: symbol.to_string(),
            source_phase: "factor-candidate-admission-targets".to_string(),
            source_run_id: None,
            path: artifact_state_path(
                state_dir,
                symbol,
                "policy_training/structural_path_ranking_trainer_artifact.json",
            ),
            status: "ready_observation_only".to_string(),
            promote_candidate: false,
            actionable: false,
            decision_hint: "trainer_ready_but_runtime_not_enabled".to_string(),
            review_reason: format!(
                "trained_rows={} production_validation_rows=0 runtime_selection=disabled",
                summary.rows_with_training_weight
            ),
            review_rule_version: "factor-candidate-trainer-artifact/v1".to_string(),
            top_factor_name: None,
            top_factor_action: Some("observe".to_string()),
            family_scores: BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: summary.rows_with_training_weight.min(i32::MAX as usize) as i32,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    Ok(())
}

pub fn read_candidate_pack_json(pack_dir: &std::path::Path, file_name: &str) -> Result<Value> {
    let path = pack_dir.join(file_name);
    let raw = std::fs::read_to_string(&path)
        .with_context(|| format!("failed to read candidate pack file '{}'", path.display()))?;
    serde_json::from_str(&raw)
        .with_context(|| format!("failed to parse candidate pack file '{}'", path.display()))
}

fn value_str<'a>(value: &'a Value, key: &str) -> Option<&'a str> {
    value.get(key).and_then(Value::as_str)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use tempfile::TempDir;

    fn write_json(path: &std::path::Path, value: &Value) {
        std::fs::write(path, serde_json::to_string_pretty(value).unwrap()).unwrap();
    }

    #[test]
    fn factor_candidate_sparse_regime_conditioned_positive_admits_learning() {
        let root = TempDir::new().unwrap();
        let pack_dir = root.path().join("sparse-positive");
        std::fs::create_dir(&pack_dir).unwrap();
        write_json(
            &pack_dir.join("factor_expression.json"),
            &json!({
                "candidate_id": "sparse_positive_v1",
                "display_name": "Sparse Positive",
                "family": "Regime Momentum",
                "paradigm": "regime_conditioned",
                "base_timeframe": "1m",
                "expected_regime": "TrendExpansion",
                "branch_path_contract": {
                    "main_regime": "TrendExpansion",
                    "sub_regime": "IntradayMomentum",
                    "sub_sub_regime_or_profit_factor": "declared_friction_edge",
                    "profit_factor": "sparse_positive_v1",
                    "regime_profit_branch_path": "TrendExpansion -> IntradayMomentum -> declared_friction_edge -> sparse_positive_v1"
                }
            }),
        );
        write_json(
            &pack_dir.join("factor_eval_grid_summary.json"),
            &json!({
                "aggregate_metrics": {
                    "trade_count": 8,
                    "profit_factor": 1.45,
                    "long_run_expectancy_after_declared_friction": 0.012
                },
                "trade_density_summary": {
                    "aggregate_label": "probe_only"
                },
                "factor_profitability_lifecycle": {
                    "schema_version": "factor-profitability-lifecycle/v1",
                    "learning_admission": {
                        "status": "admitted",
                        "long_run_expectancy_after_declared_friction": 0.012,
                        "evidence_count": 8
                    },
                    "paper_admission": {"status": "observe"},
                    "live_trade": {
                        "status": "blocked",
                        "promotion_allowed": false,
                        "trade_usable": false,
                        "update_goal": false,
                        "blockers": ["execution_readiness_below_live_floor"]
                    }
                }
            }),
        );
        write_json(
            &pack_dir.join("transfer_score.json"),
            &json!({
                "status": "single_market_only",
                "overall_transfer_score": 0.62,
                "market_evidence": {
                    "AGGREGATE": {
                        "trade_count": 8,
                        "profit_factor": 1.45
                    }
                }
            }),
        );

        let artifact =
            build_factor_candidate_admission_target_artifact(root.path().to_str().unwrap(), "NQ")
                .unwrap();
        let row = artifact
            .rows
            .iter()
            .find(|row| row.scenario_id == "factor_candidate:sparse_positive_v1:AGGREGATE")
            .unwrap();

        assert_eq!(
            row.pending_reward_state,
            "regime_conditioned_learning_success"
        );
        assert!(!row.maturity_mask);
        assert_eq!(row.calibrated_label, None);
        assert_eq!(row.training_weight, None);
        assert_eq!(row.direction, "Observe");
        assert_eq!(
            row.execution_gate_status.as_deref(),
            Some("learning_admitted_live_blocked")
        );
        assert_eq!(
            row.execution_gate_reason.as_deref(),
            Some("learning admission is not live trade usability")
        );
        let expected_prior = 0.5_f64 + 0.012_f64.tanh() / 2.0;
        assert!(
            (row.target_policy_reward_prior.unwrap() - expected_prior).abs() < 1e-12,
            "target_policy_reward_prior={:?} expected={expected_prior}",
            row.target_policy_reward_prior
        );
        assert!(
            (row.target_policy_reward_lower_bound.unwrap() - (expected_prior - 0.10)).abs() < 1e-12,
            "target_policy_reward_lower_bound={:?} expected={}",
            row.target_policy_reward_lower_bound,
            expected_prior - 0.10
        );
        assert!(
            (row.current_posterior - expected_prior).abs() < 1e-12,
            "current_posterior={} expected={expected_prior}",
            row.current_posterior
        );
    }

    #[test]
    fn factor_candidate_lifecycle_does_not_demote_full_profit_observation() {
        let root = TempDir::new().unwrap();
        let pack_dir = root.path().join("mature-positive");
        std::fs::create_dir(&pack_dir).unwrap();
        write_json(
            &pack_dir.join("factor_expression.json"),
            &json!({
                "candidate_id": "mature_positive_v1",
                "display_name": "Mature Positive",
                "family": "Regime Momentum",
                "paradigm": "regime_conditioned",
                "base_timeframe": "1m",
                "expected_regime": "TrendExpansion",
                "branch_path_contract": {
                    "main_regime": "TrendExpansion",
                    "sub_regime": "IntradayMomentum",
                    "sub_sub_regime_or_profit_factor": "declared_friction_edge",
                    "profit_factor": "mature_positive_v1",
                    "regime_profit_branch_path": "TrendExpansion -> IntradayMomentum -> declared_friction_edge -> mature_positive_v1"
                }
            }),
        );
        write_json(
            &pack_dir.join("factor_eval_grid_summary.json"),
            &json!({
                "aggregate_metrics": {
                    "trade_count": 30,
                    "profit_factor": 1.30,
                    "total_profit_pct": 2.25,
                    "long_run_expectancy_after_declared_friction": 0.018
                },
                "trade_density_summary": {
                    "aggregate_label": "preferred_density"
                },
                "factor_profitability_lifecycle": {
                    "schema_version": "factor-profitability-lifecycle/v1",
                    "learning_admission": {
                        "status": "admitted",
                        "long_run_expectancy_after_declared_friction": 0.018,
                        "evidence_count": 30
                    },
                    "paper_admission": {"status": "observe"},
                    "live_trade": {
                        "status": "blocked",
                        "promotion_allowed": false,
                        "trade_usable": false,
                        "update_goal": false
                    }
                }
            }),
        );
        write_json(
            &pack_dir.join("transfer_score.json"),
            &json!({
                "status": "single_market_only",
                "overall_transfer_score": 0.64,
                "market_evidence": {
                    "AGGREGATE": {
                        "trade_count": 30,
                        "profit_factor": 1.30,
                        "total_profit_pct": 2.25
                    }
                }
            }),
        );

        let artifact =
            build_factor_candidate_admission_target_artifact(root.path().to_str().unwrap(), "NQ")
                .unwrap();
        let row = artifact
            .rows
            .iter()
            .find(|row| row.scenario_id == "factor_candidate:mature_positive_v1:AGGREGATE")
            .unwrap();

        assert_eq!(row.pending_reward_state, "matured_success");
        assert!(row.maturity_mask);
        assert_eq!(row.calibrated_label, Some(1.0));
        assert!(row.training_weight.is_some());
        assert_eq!(row.execution_gate_status, None);
        assert_eq!(row.execution_gate_reason, None);
        assert_eq!(row.target_policy_reward_prior, None);
    }

    #[test]
    fn factor_candidate_preserves_arbitrary_depth_branch_contract_metadata() {
        let expression = json!({
            "branch_path_contract": {
                "regime_profit_branch_path": "TrendExpansion -> IntradayMomentum -> PullbackContinuation -> LiquiditySweep -> pda_transition_guard"
            }
        });

        let fields = resolve_factor_candidate_branch_fields(
            &expression,
            "fallback_main",
            "fallback_sub".to_string(),
            "fallback_middle".to_string(),
            "fallback_profit".to_string(),
        );

        assert_eq!(fields.main_regime, "TrendExpansion");
        assert_eq!(fields.sub_regime, "IntradayMomentum");
        assert_eq!(
            fields.sub_sub_regime_or_profit_factor,
            "PullbackContinuation"
        );
        assert_eq!(
            fields.profit_factor,
            "LiquiditySweep -> pda_transition_guard"
        );
        assert_eq!(
            fields.regime_profit_branch_path,
            "TrendExpansion -> IntradayMomentum -> PullbackContinuation -> LiquiditySweep -> pda_transition_guard"
        );
    }
}
