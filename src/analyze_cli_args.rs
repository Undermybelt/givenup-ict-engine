use clap::Args;

#[derive(Args)]
pub(crate) struct AnalyzeArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Higher-timeframe cleaned candle JSON path")]
    pub(crate) data_htf: Option<String>,
    #[arg(long, help = "Middle-timeframe cleaned candle JSON path")]
    pub(crate) data_mtf: Option<String>,
    #[arg(long, help = "Lower-timeframe cleaned candle JSON path")]
    pub(crate) data_ltf: Option<String>,
    #[arg(
        long,
        help = "Root directory for auto-resolving cleaned multi-timeframe data"
    )]
    pub(crate) data_root: Option<String>,
    #[arg(
        long,
        help = "Use bundled demo candles from support/examples/demo/demo-15m.json for first-run analyze checks; too short for backtest"
    )]
    pub(crate) demo: bool,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for model and workflow artifacts; pass /tmp/... for no-pollution first runs"
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
        default_value_t = false,
        help = "Inline full workflow snapshot ledger arrays in JSON output instead of trimming them to a token-friendly tail"
    )]
    pub(crate) inline_ledger: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Disable the leading Execution Triage section / envelope field (default: on)"
    )]
    pub(crate) no_execution_focus: bool,
    #[arg(
        long,
        help = "Optional regime_consumer_bundle.json path for read-only trace/report context"
    )]
    pub(crate) regime_consumer_bundle: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Fail analyze if --regime-consumer-bundle is missing or invalid"
    )]
    pub(crate) regime_consumer_bundle_strict: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Opt in to applying strong/moderate regime bundle BBN soft evidence to the pre-Bayes filter"
    )]
    pub(crate) apply_regime_bundle_bbn_soft_evidence: bool,
    #[arg(
        long,
        help = "Optional structure-events JSON hotplug; confirms direction only from CISD/MSS-style multi-timeframe events"
    )]
    pub(crate) structure_events: Option<String>,
}

#[derive(Args)]
pub(crate) struct AnalyzeLiveArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Explicit futures symbol for the live data provider")]
    pub(crate) futures_symbol: Option<String>,
    #[arg(long, help = "Explicit spot symbol for auxiliary evidence")]
    pub(crate) spot_symbol: Option<String>,
    #[arg(long, help = "Explicit options symbol for auxiliary evidence")]
    pub(crate) options_symbol: Option<String>,
    #[arg(
        long,
        help = "Optional explicit volatility proxy symbol used only when options-chain fetch fails"
    )]
    pub(crate) options_volatility_proxy_symbol: Option<String>,
    #[arg(long, help = "Spot instrument kind override, e.g. spot, etf, index")]
    pub(crate) spot_kind: Option<String>,
    #[arg(
        long,
        default_value = "yfinance",
        help = "Backend for live futures candles"
    )]
    pub(crate) futures_backend: String,
    #[arg(
        long,
        default_value = "yfinance",
        help = "Backend for auxiliary spot/options evidence"
    )]
    pub(crate) aux_backend: String,
    #[arg(
        long,
        default_value = "http://127.0.0.1:6901/api/v1",
        help = "Base URL for the external HTTP live runtime when that backend is selected"
    )]
    pub(crate) external_http_base_url: String,
    #[arg(
        long,
        default_value = "http://127.0.0.1:8080",
        help = "Base URL for the optional crypto-public runtime when that backend is selected"
    )]
    pub(crate) crypto_public_base_url: String,
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
        help = "Optional regime_consumer_bundle.json path for read-only trace/report context"
    )]
    pub(crate) regime_consumer_bundle: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Fail analyze-live if --regime-consumer-bundle is missing or invalid"
    )]
    pub(crate) regime_consumer_bundle_strict: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Opt in to applying strong/moderate regime bundle BBN soft evidence to the pre-Bayes filter"
    )]
    pub(crate) apply_regime_bundle_bbn_soft_evidence: bool,
}
