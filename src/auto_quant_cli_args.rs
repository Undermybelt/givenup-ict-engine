use clap::Args;

#[derive(Args)]
pub(crate) struct AutoQuantStatusArgs {
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant dependency metadata"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "",
        help = "Output format: json (default), compact, agent, or human. `--compact`, `--agent`, and `--human` are aliases; do not combine them with `--output-format`."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format compact")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format agent")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct AutoQuantFuturesCostArgs {
    #[arg(long, help = "Futures root or contract symbol, e.g. ES, NQH6, MESM6")]
    pub(crate) symbol: String,
    #[arg(
        long,
        help = "Representative futures price used to convert points into percent cost"
    )]
    pub(crate) price: f64,
    #[arg(
        long,
        help = "Optional JSON profile override containing a FuturesCostCatalog payload"
    )]
    pub(crate) profile: Option<String>,
    #[arg(
        long,
        default_value = "",
        help = "Output format: json (default), compact, agent, or human. `--compact`, `--agent`, and `--human` are aliases; do not combine them with `--output-format`."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format compact")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format agent")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct AutoQuantBootstrapArgs {
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant dependency metadata"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        env = "ICT_ENGINE_AUTO_QUANT_REPO_URL",
        help = "Override Auto-Quant repository URL; default release-agent source is https://github.com/undermybelt/Auto-Quant"
    )]
    pub(crate) repo_url: Option<String>,
    #[arg(
        long,
        env = "ICT_ENGINE_AUTO_QUANT_BRANCH",
        help = "Override tracked Auto-Quant branch"
    )]
    pub(crate) tracked_branch: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantUpdateArgs {
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant dependency metadata"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        env = "ICT_ENGINE_AUTO_QUANT_REPO_URL",
        help = "Override Auto-Quant repository URL; default release-agent source is https://github.com/undermybelt/Auto-Quant"
    )]
    pub(crate) repo_url: Option<String>,
    #[arg(
        long,
        env = "ICT_ENGINE_AUTO_QUANT_BRANCH",
        help = "Override tracked Auto-Quant branch"
    )]
    pub(crate) tracked_branch: Option<String>,
    #[arg(long, help = "Explicit Auto-Quant target ref to checkout")]
    pub(crate) target_ref: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantPrepareArgs {
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant dependency metadata"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct AutoQuantAdoptionReviewArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant handoff artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional specific handoff artifact id to review")]
    pub(crate) artifact_id: Option<String>,
    #[arg(
        long,
        help = "Optional event/fundamentals sidecar handoff bundle to review alongside the Auto-Quant handoff"
    )]
    pub(crate) sidecar_handoff: Option<String>,
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

#[derive(Args)]
pub(crate) struct AutoQuantAdoptionDecisionArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant handoff artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional specific handoff artifact id to decide on")]
    pub(crate) artifact_id: Option<String>,
    #[arg(long, help = "Decision label, e.g. adopt, discard, defer")]
    pub(crate) decision: String,
    #[arg(long, help = "Why this decision was made")]
    pub(crate) rationale: String,
    #[arg(
        long,
        default_value = "manual",
        help = "Who or what recorded the decision"
    )]
    pub(crate) requested_by: String,
}

#[derive(Args)]
pub(crate) struct AutoQuantSeedEvidenceArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant seed evidence artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Explicit read-only external strategy material root, for example a Tomac py/csv workspace"
    )]
    pub(crate) strategy_material_root: String,
    #[arg(
        long,
        default_value_t = 5,
        help = "Maximum number of top external materials to persist into the seed evidence artifact"
    )]
    pub(crate) limit: usize,
}

#[derive(Args)]
pub(crate) struct AutoQuantPdaUnitBatchArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "expansion_manipulation",
        help = "Research objective label carried into every unit handoff"
    )]
    pub(crate) objective: String,
    #[arg(
        long,
        help = "Comma-separated PDA primitive names, e.g. order_block,fair_value_gap,mss,cisd"
    )]
    pub(crate) factors: String,
    #[arg(
        long,
        default_value_t = 1,
        help = "Ordered primitive-sequence length; 1 for base units, 2+ for later sequence waves"
    )]
    pub(crate) combination_size: usize,
    #[arg(
        long,
        default_value = "long,short",
        help = "Comma-separated unit directions: long, short"
    )]
    pub(crate) directions: String,
    #[arg(
        long,
        help = "Comma-separated requested timeframes, e.g. 15m or 15m,1h"
    )]
    pub(crate) timeframes: String,
    #[arg(
        long = "timeframe-data",
        help = "Repeatable timeframe mapping in the form <timeframe>=<path>, e.g. 15m=/tmp/nq-15m.json"
    )]
    pub(crate) timeframe_data: Vec<String>,
    #[arg(
        long,
        default_value = "",
        help = "Comma-separated consumer evidence surfaces, e.g. indicators,volatility,greeks,open_interest,implied_volatility,cross_market"
    )]
    pub(crate) evidence_surfaces: String,
    #[arg(
        long,
        default_value = "",
        help = "Comma-separated indicator names the consumer explicitly requires, e.g. rsi14,ema20,atr14"
    )]
    pub(crate) indicator_list: String,
    #[arg(
        long = "evidence-note",
        help = "Repeatable freeform consumer evidence requirement note"
    )]
    pub(crate) evidence_notes: Vec<String>,
    #[arg(
        long,
        default_value_t = 4,
        help = "Maximum number of independent unit jobs to dispatch in parallel"
    )]
    pub(crate) max_parallel: usize,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding the batch manifest plus isolated per-unit handoffs"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Optional Auto-Quant repo URL or local path override used when bootstrapping the shared workspace"
    )]
    pub(crate) repo_url: Option<String>,
    #[arg(
        long,
        help = "Optional Auto-Quant branch override used when bootstrapping the shared workspace"
    )]
    pub(crate) tracked_branch: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantPdaUnitDispatchArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding the PDA unit batch manifest and isolated unit state"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Optional explicit auto-quant-pda-unit-batch artifact id; defaults to the latest batch for the symbol"
    )]
    pub(crate) batch_artifact_id: Option<String>,
    #[arg(
        long,
        help = "Optional comma-separated dispatch group indices, e.g. 0,1,3; defaults to every group in the batch"
    )]
    pub(crate) group_indices: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantPromoteCanonicalSetupArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        help = "Versioned setup name to write into the promoted canonical manifest"
    )]
    pub(crate) setup_name: String,
    #[arg(
        long,
        help = "Discovery sequence label, e.g. 'liquidity_sweep -> market_structure_shift'"
    )]
    pub(crate) sequence_label: String,
    #[arg(long, help = "Optional direction filter: bull, bear, or neutral")]
    pub(crate) direction: Option<String>,
    #[arg(
        long,
        help = "Optional explicit PB12 sweep id; defaults to the latest artifact for the symbol"
    )]
    pub(crate) sweep_id: Option<String>,
    #[arg(
        long,
        default_value_t = 30,
        help = "Maximum event span in bars for the promoted sequence matcher"
    )]
    pub(crate) horizon_bars: usize,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory containing PB12 discovery artifacts"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct AutoQuantAgentMaterialBatchArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long = "material",
        help = "Repeatable path to an agent-produced strategy material package (.json)"
    )]
    pub(crate) materials: Vec<String>,
    #[arg(
        long,
        default_value_t = 4,
        help = "Maximum number of independent jobs to dispatch in parallel"
    )]
    pub(crate) max_parallel: usize,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding the generic agent-material batch artifact"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Optional Auto-Quant repo URL or local path override used when bootstrapping the shared workspace"
    )]
    pub(crate) repo_url: Option<String>,
    #[arg(
        long,
        help = "Optional Auto-Quant branch override used when bootstrapping the shared workspace"
    )]
    pub(crate) tracked_branch: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantAgentMaterialDispatchArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding generic agent-material artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Optional comma-separated dispatch group indices, e.g. 0,1,3; defaults to every group"
    )]
    pub(crate) group_indices: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantAgentMaterialRankArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding generic agent-material artifacts"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct AutoQuantResultsImportArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Path to the strategy_library.json produced by Auto-Quant's export_strategy_library.py"
    )]
    pub(crate) library: String,
    #[arg(
        long,
        help = "Optional path to run_ibkr.log for redundant cross-check against the manifest. Drift is reported in the summary but does not fail the import."
    )]
    pub(crate) log: Option<String>,
}

#[derive(Args)]
pub(crate) struct AutoQuantConsumeLiveSignalsArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "redis://localhost:6379",
        help = "Redis connection URL. Must point to the same instance the Auto-Quant publisher writes to."
    )]
    pub(crate) redis_url: String,
    #[arg(
        long,
        help = "Optional cap on XREAD iterations; useful for tests + first-runs. Default: run until shutdown."
    )]
    pub(crate) max_iter: Option<u32>,
    #[arg(
        long,
        default_value_t = 2000,
        help = "XREAD BLOCK timeout in milliseconds per iteration."
    )]
    pub(crate) block_ms: u64,
    #[arg(
        long,
        default_value = "$",
        help = "Initial cursor position when no cursor file exists. '$' = future entries only; '0' = full backlog."
    )]
    pub(crate) start_from: String,
}

#[derive(Args)]
pub(crate) struct AutoQuantIngestRealTradesArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Path to the JSONL realized-trades artifact emitted by auto_quant_export_real_trades.py"
    )]
    pub(crate) trades: String,
    #[arg(
        long,
        default_value = "auto_quant_real_trades",
        help = "Source label recorded on every FeedbackRecord. Surfaces in learning_state audits."
    )]
    pub(crate) source: String,
    #[arg(
        long,
        help = "Parse + summarise but do not mutate the trading network or learning state"
    )]
    pub(crate) dry_run: bool,
    #[arg(
        long,
        help = "Override the same-content-hash guard. Use only after rolling back the BBN snapshot."
    )]
    pub(crate) force: bool,
}

#[derive(Args)]
pub(crate) struct AutoQuantPriorInitArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory holding Auto-Quant artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Path to a strategy_library.json. If omitted, defaults to the canonical state copy persisted by auto-quant-results-import"
    )]
    pub(crate) library: Option<String>,
    #[arg(
        long,
        value_delimiter = ',',
        help = "Comma-separated strategy names; if omitted, every status=ok strategy in the manifest is applied"
    )]
    pub(crate) strategies: Option<Vec<String>>,
    #[arg(
        long,
        help = "Temper factor in [0, 1]. Backtest counts are multiplied by this before being added to the Dirichlet prior. Defaults to 0.5"
    )]
    pub(crate) temper: Option<f64>,
    #[arg(
        long,
        help = "Dirichlet concentration applied to the existing CPT row. Defaults to 4.0"
    )]
    pub(crate) prior_strength: Option<f64>,
    #[arg(
        long,
        value_delimiter = ',',
        help = "Three usize indices [entry_quality, factor_alignment, factor_uncertainty]. Defaults to 0,0,0"
    )]
    pub(crate) parent_config: Option<Vec<usize>>,
    #[arg(
        long,
        help = "Compute the diff and emit the ledger entry but do not persist the mutated trading network"
    )]
    pub(crate) dry_run: bool,
    #[arg(
        long,
        help = "Override the ledger-enforced single-apply guard. Use only after consciously rolling back the BBN snapshot."
    )]
    pub(crate) force: bool,
}
