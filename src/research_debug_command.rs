use super::*;

pub(crate) fn factor_backtest_shell(
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    ensemble: bool,
    state_dir: &str,
    output_format: &str,
) -> Result<()> {
    ensure_state_dir_ready(state_dir)?;
    ict_engine::application::backtest::factor_backtest_command(
        symbol,
        data,
        paired_data,
        ensemble,
        state_dir,
        output_format,
        run_factor_backtest,
    )
}

pub(crate) fn factor_pipeline_debug_shell(
    input: ict_engine::application::factor_pipeline_debug::FactorPipelineDebugCommandInput<'_>,
) -> Result<()> {
    ict_engine::application::factor_pipeline_debug::factor_pipeline_debug_command(input)
}
