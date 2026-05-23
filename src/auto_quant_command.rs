use super::*;
use ict_engine::application::auto_quant::FuturesCostCatalog;
use std::path::Path;

pub(crate) const AUTO_QUANT_OUTPUT_DIR_ENV_VAR: &str = "ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR";
pub(crate) const DEFAULT_AUTO_QUANT_SUBDIR: &str = "auto-quant";

/// Resolve the Auto-Quant output directory from the given state_dir.
/// Auto-Quant artifacts are always isolated from the repo root:
/// - If ICT_ENGINE_AUTO_QUANT_OUTPUT_DIR is set, use that path.
/// - Otherwise, use <state_dir>/auto-quant/ subdirectory.
fn aq_state_dir(state_dir: &str) -> String {
    let custom = std::env::var(AUTO_QUANT_OUTPUT_DIR_ENV_VAR).ok();
    aq_state_dir_with_custom(state_dir, custom.as_deref())
}

fn aq_state_dir_with_custom(state_dir: &str, custom_output_dir: Option<&str>) -> String {
    if let Some(custom) = custom_output_dir
        .map(str::trim)
        .filter(|value| !value.is_empty())
    {
        return custom.to_string();
    }
    if state_dir_has_auto_quant_workspace(Path::new(state_dir)) {
        return state_dir.to_string();
    }
    resolve_auto_quant_output_dir(state_dir)
}

pub(crate) fn resolve_auto_quant_output_dir(state_dir: &str) -> String {
    if let Ok(custom) = std::env::var(AUTO_QUANT_OUTPUT_DIR_ENV_VAR) {
        if !custom.trim().is_empty() {
            return custom;
        }
    }
    format!("{}/{}", state_dir, DEFAULT_AUTO_QUANT_SUBDIR)
}

fn state_dir_has_auto_quant_workspace(state_dir: &Path) -> bool {
    state_dir.join("auto_quant_config.json").exists()
        || state_dir.join("auto_quant_workspace_profile.json").exists()
        || state_dir.join(".deps").join("auto-quant").exists()
        || state_dir_has_auto_quant_handoff(state_dir)
}

fn state_dir_has_auto_quant_handoff(state_dir: &Path) -> bool {
    let Ok(entries) = std::fs::read_dir(state_dir) else {
        return false;
    };
    entries.filter_map(Result::ok).any(|entry| {
        let ledger_path = entry.path().join("artifact_ledger.json");
        if !ledger_path.exists() {
            return false;
        }
        std::fs::read_to_string(&ledger_path)
            .map(|content| content.contains("auto_quant_handoff_candidate"))
            .unwrap_or(false)
    })
}

pub(crate) fn auto_quant_status_shell(state_dir: &str, output_format: &str) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    auto_quant_status_command(&aq_dir, output_format)
}

pub(crate) fn auto_quant_futures_cost_shell(
    symbol: &str,
    price: f64,
    profile_path: Option<&str>,
    output_format: &str,
) -> Result<()> {
    let mut catalog = FuturesCostCatalog::default();
    if let Some(path) = profile_path
        .map(str::trim)
        .filter(|value| !value.is_empty())
    {
        let json = std::fs::read_to_string(path)
            .with_context(|| format!("reading futures cost profile override '{}'", path))?;
        catalog = catalog.with_json_overrides(&json)?;
    }
    let profile = catalog.profile_for(symbol).ok_or_else(|| {
        anyhow!(
            "unknown futures cost profile: {}",
            futures_root_for_error(symbol)
        )
    })?;
    let round_trip_cost_pct = profile.round_trip_cost_percent(price)?;
    let report = serde_json::json!({
        "command": "auto-quant-futures-cost",
        "symbol": profile.root_symbol,
        "input_symbol": symbol,
        "profile_id": profile.profile_id,
        "exchange": profile.exchange,
        "representative_price": price,
        "tick_size": profile.tick_size,
        "tick_value": profile.tick_value,
        "point_value": profile.point_value(),
        "round_trip_cost_points": profile.round_trip_cost_points(),
        "round_trip_cost_pct": round_trip_cost_pct,
        "commission_per_contract_side": profile.commission_per_contract_side,
        "exchange_fees_per_contract_side": profile.exchange_fees_per_contract_side,
        "regulatory_fees_per_contract_side": profile.regulatory_fees_per_contract_side,
        "assumed_spread_ticks": profile.assumed_spread_ticks,
        "assumed_slippage_ticks_per_side": profile.assumed_slippage_ticks_per_side,
        "source": profile.source,
        "notes": profile.notes,
        "gate_note": "fixed_bps_is_diagnostic_only; futures_gate_uses_instrument_cost_profile",
        "override": profile_path.is_some(),
    });
    match output_format {
        "json" => println!("{}", serde_json::to_string_pretty(&report)?),
        "compact" => println!(
            "symbol={} profile={} price={} round_trip_cost_pct={:.6} round_trip_cost_points={:.6} spread_ticks={} slippage_ticks_side={} source={} fixed_bps_is_diagnostic_only",
            profile.root_symbol,
            profile.profile_id,
            price,
            round_trip_cost_pct,
            profile.round_trip_cost_points(),
            profile.assumed_spread_ticks,
            profile.assumed_slippage_ticks_per_side,
            profile.source,
        ),
        "human" => {
            println!(
                "Futures cost | {} | {}",
                profile.root_symbol, profile.profile_id
            );
            println!("Exchange: {}", profile.exchange);
            println!(
                "Tick: size={} value={} point_value={}",
                profile.tick_size,
                profile.tick_value,
                profile.point_value()
            );
            println!(
                "Round trip: {:.6}% ({:.6} points)",
                round_trip_cost_pct,
                profile.round_trip_cost_points()
            );
            println!(
                "Assumptions: commission_side={} exchange_fees_side={} regulatory_side={} spread_ticks={} slippage_ticks_side={}",
                profile.commission_per_contract_side,
                profile.exchange_fees_per_contract_side,
                profile.regulatory_fees_per_contract_side,
                profile.assumed_spread_ticks,
                profile.assumed_slippage_ticks_per_side
            );
            println!(
                "Gate: fixed_bps_is_diagnostic_only; use instrument profile or hotplug override for futures."
            );
        }
        other => bail!("unsupported auto-quant-futures-cost output format '{}'", other),
    }
    Ok(())
}

fn futures_root_for_error(symbol: &str) -> String {
    symbol
        .trim()
        .chars()
        .take_while(|ch| ch.is_ascii_alphabetic())
        .collect::<String>()
        .to_ascii_uppercase()
}

pub(crate) fn auto_quant_bootstrap_shell(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    auto_quant_bootstrap_command(&aq_dir, repo_url, tracked_branch)
}

pub(crate) fn auto_quant_update_shell(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
    target_ref: Option<&str>,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    auto_quant_update_command(&aq_dir, repo_url, tracked_branch, target_ref)
}

pub(crate) fn auto_quant_prepare_shell(state_dir: &str) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    auto_quant_prepare_workspace_command(&aq_dir)
}

pub(crate) fn auto_quant_adoption_review_shell(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    output_format: &str,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    match auto_quant_adoption_review_command(symbol, &aq_dir, artifact_id, output_format) {
        Ok(()) => Ok(()),
        Err(error)
            if aq_dir != state_dir
                && error.to_string().contains("no auto-quant handoff artifact") =>
        {
            auto_quant_adoption_review_command(symbol, state_dir, artifact_id, output_format)
        }
        Err(error) => Err(error),
    }
}

pub(crate) fn auto_quant_adoption_decision_shell(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    decision: &str,
    rationale: &str,
    requested_by: &str,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    match auto_quant_adoption_decision_command(
        symbol,
        &aq_dir,
        artifact_id,
        decision,
        rationale,
        requested_by,
    ) {
        Ok(()) => Ok(()),
        Err(error)
            if aq_dir != state_dir
                && (error.to_string().contains("no auto-quant handoff artifact")
                    || error
                        .to_string()
                        .contains("auto_quant_adoption_handoff_missing")) =>
        {
            auto_quant_adoption_decision_command(
                symbol,
                state_dir,
                artifact_id,
                decision,
                rationale,
                requested_by,
            )
        }
        Err(error) => Err(error),
    }
}

pub(crate) fn auto_quant_seed_evidence_shell(
    symbol: &str,
    state_dir: &str,
    strategy_material_root: &str,
    limit: usize,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    auto_quant_seed_evidence_command(symbol, &aq_dir, strategy_material_root, limit)
}

pub(crate) fn auto_quant_pda_unit_batch_shell(
    input: AutoQuantPdaUnitBatchCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantPdaUnitBatchCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_pda_unit_batch_command(resolved)
}

pub(crate) fn auto_quant_pda_unit_dispatch_shell(
    input: AutoQuantPdaUnitDispatchCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantPdaUnitDispatchCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_pda_unit_dispatch_command(resolved)
}

pub(crate) fn auto_quant_agent_material_batch_shell(
    input: AutoQuantAgentMaterialBatchCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantAgentMaterialBatchCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_agent_material_batch_command(resolved)
}

pub(crate) fn auto_quant_agent_material_dispatch_shell(
    input: AutoQuantAgentMaterialDispatchCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantAgentMaterialDispatchCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_agent_material_dispatch_command(resolved)
}

pub(crate) fn auto_quant_agent_material_rank_shell(
    input: AutoQuantAgentMaterialRankCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantAgentMaterialRankCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_agent_material_rank_command(resolved)
}

pub(crate) fn auto_quant_results_import_shell(
    symbol: &str,
    state_dir: &str,
    library: &str,
    log: Option<&str>,
) -> Result<()> {
    let aq_dir = aq_state_dir(state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    auto_quant_results_import_command(symbol, &aq_dir, library, log)
}

pub(crate) fn auto_quant_prior_init_shell(input: AutoQuantPriorInitCommandInput<'_>) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantPriorInitCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_prior_init_command(resolved)
}

pub(crate) fn auto_quant_consume_live_signals_shell(
    input: AutoQuantConsumeLiveSignalsInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = AutoQuantConsumeLiveSignalsInput {
        state_dir: &aq_dir,
        ..input
    };
    auto_quant_consume_live_signals_command(resolved)
}

pub(crate) fn auto_quant_ingest_real_trades_shell(
    input: AutoQuantIngestRealTradesInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_ingest_real_trades_command(input)
}

pub(crate) fn auto_quant_promote_canonical_setup_shell(
    input: ict_engine::application::backtest::PromoteCanonicalSetupCommandInput<'_>,
) -> Result<()> {
    let aq_dir = aq_state_dir(input.state_dir);
    ensure_state_dir_ready(&aq_dir)?;
    let resolved = ict_engine::application::backtest::PromoteCanonicalSetupCommandInput {
        state_dir: &aq_dir,
        ..input
    };
    let report =
        ict_engine::application::backtest::auto_quant_promote_canonical_setup_command(resolved)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn aq_state_dir_uses_existing_handoff_state_without_extra_subdir() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::create_dir_all(temp.path().join(".deps/auto-quant")).unwrap();

        assert_eq!(
            aq_state_dir_with_custom(temp.path().to_str().unwrap(), None),
            temp.path().to_string_lossy()
        );
    }

    #[test]
    fn aq_state_dir_uses_profile_state_without_extra_subdir() {
        let temp = tempfile::tempdir().unwrap();
        std::fs::write(temp.path().join("auto_quant_workspace_profile.json"), "{}").unwrap();

        assert_eq!(
            aq_state_dir_with_custom(temp.path().to_str().unwrap(), None),
            temp.path().to_string_lossy()
        );
    }

    #[test]
    fn aq_state_dir_uses_symbol_handoff_state_without_extra_subdir() {
        let temp = tempfile::tempdir().unwrap();
        let symbol_dir = temp.path().join("M2K");
        std::fs::create_dir_all(&symbol_dir).unwrap();
        std::fs::write(
            symbol_dir.join("artifact_ledger.json"),
            r#"[{"artifact_kind":"auto_quant_handoff_candidate"}]"#,
        )
        .unwrap();

        assert_eq!(
            aq_state_dir_with_custom(temp.path().to_str().unwrap(), None),
            temp.path().to_string_lossy()
        );
    }

    #[test]
    fn aq_state_dir_keeps_isolated_subdir_for_fresh_state() {
        let temp = tempfile::tempdir().unwrap();

        assert_eq!(
            aq_state_dir_with_custom(temp.path().to_str().unwrap(), None),
            format!(
                "{}/{}",
                temp.path().to_string_lossy(),
                DEFAULT_AUTO_QUANT_SUBDIR
            )
        );
    }

    #[test]
    fn aq_state_dir_respects_explicit_output_dir_override() {
        let temp = tempfile::tempdir().unwrap();

        assert_eq!(
            aq_state_dir_with_custom(temp.path().to_str().unwrap(), Some("/tmp/custom-aq")),
            "/tmp/custom-aq"
        );
    }

    #[test]
    fn auto_quant_ingest_real_trades_shell_feeds_requested_downstream_state_dir() {
        let temp = tempfile::tempdir().unwrap();
        let trades_path = temp.path().join("real_trades.jsonl");
        let branch_path =
            "Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1";
        let record = serde_json::json!({
            "schema_version": "1.0",
            "symbol": "NQ",
            "trade_id": "trade-1",
            "strategy_name": "ProviderCryptoPullbackRevertV1",
            "strategy_mutation_id": "provider-pullback-v1",
            "auto_quant_run_id": "aq-run-1",
            "open_ts_ms": 1717707600000_i64,
            "close_ts_ms": 1717740000000_i64,
            "direction": "Bull",
            "pnl": 21.69,
            "realized_outcome": "win",
            "regime_at_entry": "Range",
            "entry_signal": "provider_crypto_pullback_revert",
            "regime_profit_branch_path": branch_path,
            "main_regime": "Range",
            "sub_regime": "ProviderCryptoPullback",
            "sub_sub_regime_or_profit_factor": "MeanRevertBounce",
            "profit_factor": "ProviderCryptoPullbackRevertV1",
            "factors_used": []
        });
        std::fs::write(&trades_path, format!("{record}\n")).unwrap();

        auto_quant_ingest_real_trades_shell(AutoQuantIngestRealTradesInput {
            symbol: "NQ",
            state_dir: temp.path().to_str().unwrap(),
            trades_path: trades_path.to_str().unwrap(),
            source: "auto_quant_real_trades",
            dry_run: false,
            force: false,
        })
        .unwrap();

        let target_jsonl = temp
            .path()
            .join("NQ")
            .join("policy_training")
            .join("structural_path_ranking_target.jsonl");
        let target_rows = std::fs::read_to_string(target_jsonl).unwrap();
        assert!(
            target_rows.contains(branch_path),
            "real-trade branch feedback must be visible to downstream structural target export"
        );

        let policy = ict_engine::application::entry_models::policy_training_status(
            temp.path().to_str().unwrap(),
            "NQ",
            None,
        )
        .unwrap();
        let real_trade_entry = policy
            .providers
            .iter()
            .find(|provider| provider.provider_id == "auto_quant_real_trade_entry_v1")
            .expect("real-trade feedback entry-model provider");
        assert_eq!(real_trade_entry.matched_rows, 1);
        assert!(
            policy.structural_path_ranking_target.mature_rows >= 1,
            "real-trade structural feedback must become mature path-ranker rows"
        );
        assert!(
            policy
                .structural_path_ranking_target
                .rows_with_training_weight
                >= 1,
            "real-trade structural feedback must carry supervised training weight"
        );
    }
}
