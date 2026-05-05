use super::*;

pub(crate) fn auto_quant_status_shell(state_dir: &str) -> Result<()> {
    auto_quant_status_command(state_dir)
}

pub(crate) fn auto_quant_bootstrap_shell(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    auto_quant_bootstrap_command(state_dir, repo_url, tracked_branch)
}

pub(crate) fn auto_quant_update_shell(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
    target_ref: Option<&str>,
) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    auto_quant_update_command(state_dir, repo_url, tracked_branch, target_ref)
}

pub(crate) fn auto_quant_prepare_shell(state_dir: &str) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    auto_quant_prepare_workspace_command(state_dir)
}

pub(crate) fn auto_quant_adoption_review_shell(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
) -> Result<()> {
    auto_quant_adoption_review_command(symbol, state_dir, artifact_id)
}

pub(crate) fn auto_quant_adoption_decision_shell(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    decision: &str,
    rationale: &str,
    requested_by: &str,
) -> Result<()> {
    auto_quant_adoption_decision_command(
        symbol,
        state_dir,
        artifact_id,
        decision,
        rationale,
        requested_by,
    )
}

pub(crate) fn auto_quant_seed_evidence_shell(
    symbol: &str,
    state_dir: &str,
    strategy_material_root: &str,
    limit: usize,
) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    auto_quant_seed_evidence_command(symbol, state_dir, strategy_material_root, limit)
}

pub(crate) fn auto_quant_pda_unit_batch_shell(
    input: AutoQuantPdaUnitBatchCommandInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_pda_unit_batch_command(input)
}

pub(crate) fn auto_quant_pda_unit_dispatch_shell(
    input: AutoQuantPdaUnitDispatchCommandInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_pda_unit_dispatch_command(input)
}

pub(crate) fn auto_quant_agent_material_batch_shell(
    input: AutoQuantAgentMaterialBatchCommandInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_agent_material_batch_command(input)
}

pub(crate) fn auto_quant_agent_material_dispatch_shell(
    input: AutoQuantAgentMaterialDispatchCommandInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_agent_material_dispatch_command(input)
}

pub(crate) fn auto_quant_agent_material_rank_shell(
    input: AutoQuantAgentMaterialRankCommandInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_agent_material_rank_command(input)
}

pub(crate) fn auto_quant_results_import_shell(
    symbol: &str,
    state_dir: &str,
    library: &str,
    log: Option<&str>,
) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    auto_quant_results_import_command(symbol, state_dir, library, log)
}

pub(crate) fn auto_quant_prior_init_shell(input: AutoQuantPriorInitCommandInput<'_>) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_prior_init_command(input)
}

pub(crate) fn auto_quant_consume_live_signals_shell(
    input: AutoQuantConsumeLiveSignalsInput<'_>,
) -> Result<()> {
    ensure_state_dir_ready(input.state_dir)?;
    auto_quant_consume_live_signals_command(input)
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
    ensure_state_dir_ready(input.state_dir)?;
    let report =
        ict_engine::application::backtest::auto_quant_promote_canonical_setup_command(input)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}
