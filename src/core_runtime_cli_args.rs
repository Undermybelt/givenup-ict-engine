use clap::Args;

#[derive(Args)]
pub(crate) struct ValidateMarketStateArgs {
    #[arg(long, help = "Cleaned candle JSON or CSV path")]
    pub(crate) data: String,
    #[arg(
        long,
        default_value_t = 100,
        help = "Sliding window size used for each market-state classification"
    )]
    pub(crate) window_size: usize,
    #[arg(
        long,
        default_value_t = 1,
        help = "Sliding window step size; increase for faster broad checks"
    )]
    pub(crate) step_size: usize,
    #[arg(long, help = "Print periodic per-window classification samples")]
    pub(crate) verbose: bool,
    #[arg(
        long,
        default_value = "",
        help = "Output format: human (default) or compact. Structured json/agent output is not yet supported."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format compact")]
    pub(crate) compact: bool,
    #[arg(
        long,
        help = "Request agent output; currently rejected with a clear unsupported-format error"
    )]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
    #[arg(
        long,
        help = "Disable enhanced aggregation and use the basic aggregator fallback"
    )]
    pub(crate) no_enhanced: bool,
    #[arg(
        long,
        help = "Optional market-state JSON config path for hot-pluggable tuning"
    )]
    pub(crate) config: Option<String>,
    #[arg(
        long,
        help = "Optional profile name: default, trend_trading, volatility_trading, reversal_trading, risk_control, or high_confidence"
    )]
    pub(crate) profile: Option<String>,
}

#[derive(Args)]
pub(crate) struct TrainArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Cleaned candle JSON path used for HMM training")]
    pub(crate) data: String,
    #[arg(
        short,
        long,
        default_value = "100",
        help = "Number of Baum-Welch training epochs"
    )]
    pub(crate) epochs: usize,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct BacktestArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Primary cleaned candle JSON path")]
    pub(crate) data: String,
    #[arg(long, help = "Optional paired-market candle JSON path")]
    pub(crate) paired_data: Option<String>,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "",
        help = "Output format: json (default), compact, agent, or human. `--compact`, `--agent`, `--human` are aliases; do not combine them with `--output-format`."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format compact")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format agent")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
    #[arg(
        long,
        default_value = "60",
        help = "Warmup bars before trade simulation begins"
    )]
    pub(crate) warmup_bars: usize,
    #[arg(long, default_value = "10", help = "Maximum holding period in bars")]
    pub(crate) hold_bars: usize,
    #[arg(long, default_value = "0", help = "Spread cost in basis points")]
    pub(crate) spread_bps: f64,
    #[arg(long, default_value = "0", help = "Slippage cost in basis points")]
    pub(crate) slippage_bps: f64,
    #[arg(long, default_value = "0", help = "Fee cost in basis points")]
    pub(crate) fee_bps: f64,
    #[arg(
        long,
        default_value = "favor_stop_loss",
        help = "Ambiguous intrabar execution policy"
    )]
    pub(crate) ambiguous_bar_policy: String,
    #[arg(
        long,
        default_value_t = false,
        help = "Update online learning state during backtest"
    )]
    pub(crate) online_learn: bool,
}

#[derive(Args)]
pub(crate) struct UpdateArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Realized trade outcome label")]
    pub(crate) outcome: String,
    #[arg(
        long,
        default_value = "strong_buy",
        help = "Entry signal label applied to the feedback update"
    )]
    pub(crate) entry_signal: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional realized PnL used for outcome normalization")]
    pub(crate) pnl: Option<f64>,
    #[arg(long, help = "Optional regime label override at trade entry")]
    pub(crate) regime: Option<String>,
    #[arg(long, help = "Optional direction label override at trade entry")]
    pub(crate) direction: Option<String>,
    #[arg(long, help = "Optional feedback JSON artifact to consume")]
    pub(crate) feedback_file: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Also update ensemble executor scorecards"
    )]
    pub(crate) ensemble: bool,
}
