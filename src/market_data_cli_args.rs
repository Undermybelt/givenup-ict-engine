use clap::Args;

#[derive(Args)]
pub(crate) struct CleanFuturesArgs {
    #[arg(long, help = "Root directory containing TOMAC-style futures CSV files")]
    pub(crate) root: Option<String>,
    #[arg(long, help = "Output directory for cleaned candle JSON")]
    pub(crate) output_dir: String,
    #[arg(long, default_value = "15m", help = "Target output interval")]
    pub(crate) interval: String,
    #[arg(
        long,
        default_value_t = false,
        help = "Also emit sibling multi-timeframe intervals"
    )]
    pub(crate) multi_timeframe: bool,
}

#[derive(Args)]
pub(crate) struct FuturesSopArgs {
    #[arg(long, help = "Root directory containing TOMAC-style futures CSV files")]
    pub(crate) root: Option<String>,
    #[arg(long, help = "Output directory for cleaned candle JSON and reports")]
    pub(crate) output_dir: String,
    #[arg(long, default_value = "15m", help = "Primary research interval")]
    pub(crate) interval: String,
}

#[derive(Args)]
pub(crate) struct ExpansionSopArgs {
    #[arg(long, help = "Root directory containing TOMAC-style futures CSV files")]
    pub(crate) root: Option<String>,
    #[arg(long, help = "Output directory for cleaned candle JSON and reports")]
    pub(crate) output_dir: String,
    #[arg(long, default_value = "15m", help = "Primary research interval")]
    pub(crate) interval: String,
    #[arg(long, default_value_t = 20, help = "Expansion lookback window in bars")]
    pub(crate) lookback: usize,
    #[arg(
        long,
        default_value_t = 1.5,
        help = "ATR multiplier used for expansion thresholding"
    )]
    pub(crate) atr_multiplier: f64,
    #[arg(
        long,
        default_value = "expansion_manipulation",
        help = "Research objective label"
    )]
    pub(crate) objective: String,
    #[arg(long, help = "Optional mutation spec JSON path")]
    pub(crate) mutation_spec: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Emit mutation evaluation details in output"
    )]
    pub(crate) emit_mutation_evaluation: bool,
}

#[derive(Args)]
pub(crate) struct MarketDataHarnessArgs {
    #[arg(long, default_value = "plan", help = "Harness action: plan or fetch")]
    pub(crate) action: String,
    #[arg(
        long,
        help = "Optional opaque request label when not using --request-json or --request-stdin"
    )]
    pub(crate) market: Option<String>,
    #[arg(
        long,
        help = "Optional primary candle JSON path to infer interval/range"
    )]
    pub(crate) primary_data: Option<String>,
    #[arg(long, help = "Optional explicit interval override, e.g. 15m, 1h, 1d")]
    pub(crate) interval: Option<String>,
    #[arg(
        long,
        help = "Related role to resolve from explicit caller configuration; repeatable"
    )]
    pub(crate) role: Vec<String>,
    #[arg(
        long,
        help = "Explicit per-role provider mapping, role=provider; repeatable"
    )]
    pub(crate) provider: Vec<String>,
    #[arg(
        long,
        help = "Explicit role=symbol shorthand for simple providers; repeatable"
    )]
    pub(crate) symbol_spec: Vec<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Read the full harness request JSON from stdin"
    )]
    pub(crate) request_stdin: bool,
    #[arg(
        long,
        help = "Optional explicit volatility proxy symbol for options.summary fallback"
    )]
    pub(crate) options_volatility_proxy_symbol: Option<String>,
    #[arg(long, help = "Full request JSON path; preferred over individual flags")]
    pub(crate) request_json: Option<String>,
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
