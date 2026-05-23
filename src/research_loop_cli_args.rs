use clap::Args;

#[derive(Args)]
pub(crate) struct FactorResearchArgs {
    #[arg(
        long,
        default_value = "RESEARCH",
        help = "Instrument identifier supplied by the caller"
    )]
    pub(crate) symbol: String,
    #[arg(long, help = "Primary cleaned candle JSON path")]
    pub(crate) data: String,
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
    #[arg(long, help = "Optional paired-market candle JSON path")]
    pub(crate) paired_data: Option<String>,
    #[arg(long, help = "Optional opt-in provider profile id or JSON path")]
    pub(crate) profile: Option<String>,
    #[arg(
        long,
        help = "Optional managed Auto-Quant workspace profile. `synthetic_ohlcv` deploys the additive external runner against the provided primary candle JSON; `managed` clears any saved profile for this state dir."
    )]
    pub(crate) auto_quant_profile: Option<String>,
    #[arg(
        long,
        help = "Optional path to AuxiliaryMarketEvidence JSON, or a full analyze-report JSON containing supporting.auxiliary"
    )]
    pub(crate) auxiliary_evidence: Option<String>,
    #[arg(long, help = "Optional mutation spec JSON path")]
    pub(crate) mutation_spec: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Attach the canonical PB(12) control-matrix plan to native output without changing the executed research run"
    )]
    pub(crate) control_matrix_pb12: bool,
    #[arg(
        long,
        help = "Optional read-only external strategy material root (for example a Tomac py/csv workspace) used only to enrich auto-quant handoff seed guidance"
    )]
    pub(crate) strategy_material_root: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Emit mutation evaluation details in output"
    )]
    pub(crate) emit_mutation_evaluation: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Also emit ensemble vote artifacts"
    )]
    pub(crate) ensemble: bool,
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
        default_value = "auto-quant",
        help = "Research backend: public factor iteration is locked to auto-quant; keep the default or pass --backend auto-quant explicitly."
    )]
    pub(crate) backend: String,
}

#[derive(Args)]
pub(crate) struct FactorAutoresearchArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Primary cleaned candle JSON path")]
    pub(crate) data: String,
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
        default_value_t = 1,
        help = "Number of autoresearch iterations to run"
    )]
    pub(crate) iterations: usize,
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
    #[arg(long, help = "Optional paired-market candle JSON path")]
    pub(crate) paired_data: Option<String>,
    #[arg(long, help = "Optional opt-in provider profile id or JSON path")]
    pub(crate) profile: Option<String>,
    #[arg(
        long,
        help = "Optional managed Auto-Quant workspace profile. `synthetic_ohlcv` deploys the additive external runner against the provided primary candle JSON; `managed` clears any saved profile for this state dir."
    )]
    pub(crate) auto_quant_profile: Option<String>,
    #[arg(
        long,
        help = "Optional path to AuxiliaryMarketEvidence JSON, or a full analyze-report JSON containing supporting.auxiliary"
    )]
    pub(crate) auxiliary_evidence: Option<String>,
    #[arg(
        long,
        help = "Optional read-only external strategy material root (for example a Tomac py/csv workspace) used only to enrich auto-quant handoff seed guidance"
    )]
    pub(crate) strategy_material_root: Option<String>,
    #[arg(long, help = "Explicit autoresearch session id to resume or inspect")]
    pub(crate) session_id: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Resume the latest known autoresearch session"
    )]
    pub(crate) resume_latest: bool,
    #[arg(
        long,
        default_value_t = 2,
        help = "Maximum consecutive clustered failures before jumping templates"
    )]
    pub(crate) max_cluster_fail_streak: usize,
    #[arg(
        long,
        default_value_t = false,
        help = "Also emit ensemble vote artifacts"
    )]
    pub(crate) ensemble: bool,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "auto-quant",
        help = "Autoresearch backend: public factor iteration is locked to auto-quant; keep the default or pass --backend auto-quant explicitly."
    )]
    pub(crate) backend: String,
}

#[derive(Args)]
pub(crate) struct FactorBacktestArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(long, help = "Primary cleaned candle JSON path")]
    pub(crate) data: String,
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
    #[arg(long, help = "Optional paired-market candle JSON path")]
    pub(crate) paired_data: Option<String>,
    #[arg(
        long,
        help = "Optional path to AuxiliaryMarketEvidence JSON, or a full analyze-report JSON containing supporting.auxiliary"
    )]
    pub(crate) auxiliary_evidence: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Also emit ensemble vote artifacts"
    )]
    pub(crate) ensemble: bool,
    #[arg(
        long,
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
}
