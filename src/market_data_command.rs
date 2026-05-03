use super::*;

pub(crate) fn clean_futures_shell(
    root: Option<&str>,
    output_dir: &str,
    interval: &str,
    multi_timeframe: bool,
) -> Result<()> {
    ict_engine::application::data_sources::clean_futures_command(
        root,
        output_dir,
        interval,
        multi_timeframe,
        run_clean_futures_multi_timeframe,
        run_clean_futures,
    )
}

pub(crate) fn futures_sop_shell(
    root: Option<&str>,
    output_dir: &str,
    interval: &str,
) -> Result<()> {
    ict_engine::application::data_sources::futures_sop_command(
        root,
        output_dir,
        interval,
        run_futures_sop,
    )
}

pub(crate) fn market_data_harness_shell(
    action: &str,
    input: MarketDataHarnessCommandInput<'_>,
) -> Result<()> {
    match action.trim().to_ascii_lowercase().as_str() {
        "plan" => market_data_harness_plan_command(input),
        "fetch" => market_data_harness_fetch_command(input),
        other => anyhow::bail!("unsupported market-data-harness action '{}'", other),
    }
}
