use clap::Args;

#[derive(Args)]
pub(crate) struct FactorPipelineDebugArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Primary cleaned candle JSON path")]
    pub(crate) data: String,
    #[arg(long, help = "Factor name to inspect")]
    pub(crate) factor: String,
    #[arg(
        long,
        default_value = "expansion_manipulation",
        help = "Research objective label"
    )]
    pub(crate) objective: String,
    #[arg(long, help = "Optional 1m candle JSON path")]
    pub(crate) data_1m: Option<String>,
    #[arg(long, help = "Optional 5m candle JSON path")]
    pub(crate) data_5m: Option<String>,
    #[arg(long, help = "Optional 15m candle JSON path")]
    pub(crate) data_15m: Option<String>,
    #[arg(long, help = "Optional 30m candle JSON path")]
    pub(crate) data_30m: Option<String>,
    #[arg(long, help = "Optional 1h candle JSON path")]
    pub(crate) data_1h: Option<String>,
    #[arg(long, help = "Optional 4h candle JSON path")]
    pub(crate) data_4h: Option<String>,
    #[arg(long, help = "Optional 1d candle JSON path")]
    pub(crate) data_1d: Option<String>,
    #[arg(
        long,
        default_value = "json",
        help = "Output format: json (default), compact, agent, or human. `--compact`, `--agent`, and `--human` are aliases; do not combine them with `--output-format`."
    )]
    pub(crate) output_format: String,
    #[arg(
        long,
        default_value_t = false,
        help = "Alias for --output-format compact"
    )]
    pub(crate) compact: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Alias for --output-format agent"
    )]
    pub(crate) agent: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Alias for --output-format human"
    )]
    pub(crate) human: bool,
}
