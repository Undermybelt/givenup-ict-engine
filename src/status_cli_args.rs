use clap::Args;

#[derive(Args)]
pub(crate) struct FactorMutationStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional source command substring filter")]
    pub(crate) source_command: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only the latest mutation attempt"
    )]
    pub(crate) latest_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only accepted mutation attempts"
    )]
    pub(crate) accepted_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Group attempts by source command"
    )]
    pub(crate) bucket_by_source: bool,
    #[arg(long, help = "Limit returned mutation attempts")]
    pub(crate) limit: Option<usize>,
    #[arg(
        long,
        default_value = "",
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
pub(crate) struct FactorAutoresearchStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Explicit autoresearch session id to inspect")]
    pub(crate) session_id: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only the latest session summary"
    )]
    pub(crate) latest_only: bool,
    #[arg(long, help = "Limit returned sessions or attempts")]
    pub(crate) limit: Option<usize>,
    #[arg(
        long,
        default_value = "",
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
pub(crate) struct ResearchVerdictArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "",
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
pub(crate) struct EvidenceQualityBreakdownArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory for model and workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value_t = true,
        help = "Refresh workflow snapshot before reading latest analyze state"
    )]
    pub(crate) refresh: bool,
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
pub(crate) struct WorkflowStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value_t = true,
        help = "Refresh snapshot from current artifacts before printing"
    )]
    pub(crate) refresh: bool,
    #[arg(long, help = "Optional opt-in provider profile id or JSON path")]
    pub(crate) profile: Option<String>,
    #[arg(
        long,
        help = "Print a named workflow phase surface instead of the full snapshot"
    )]
    pub(crate) phase: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Print only actionable artifacts"
    )]
    pub(crate) actionable_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Print only workflow disagreements"
    )]
    pub(crate) conflicts_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Print only the latest promotable artifact"
    )]
    pub(crate) latest_promotable: bool,
    #[arg(long, default_value_t = false, help = "Print only hard-block rows")]
    pub(crate) hard_block_only: bool,
    #[arg(long, help = "Filter hard-block rows by reason substring")]
    pub(crate) hard_block_reason: Option<String>,
    #[arg(long, help = "Limit hard-block rows")]
    pub(crate) limit: Option<usize>,
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
        help = "Strip volatile timestamp-like fields from workflow-status output so repeated calls are stable for caching/diffing"
    )]
    pub(crate) stable: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Disable Execution Triage surfacing in workflow-status output (default: on)"
    )]
    pub(crate) no_execution_focus: bool,
}

#[derive(Args)]
pub(crate) struct PreBayesStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value_t = true,
        help = "Refresh snapshot from current artifacts before printing"
    )]
    pub(crate) refresh: bool,
    #[arg(
        long,
        help = "Optional Pre-Bayes section to print, e.g. policy or bridge"
    )]
    pub(crate) section: Option<String>,
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
pub(crate) struct PolicyTrainingStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing analyze/update histories and policy_training artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long = "entry-model",
        alias = "provider",
        help = "Optional entry-model id filter. Available ids are listed in the command output."
    )]
    pub(crate) entry_model: Option<String>,
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
pub(crate) struct ProviderStatusArgs {
    #[arg(
        long,
        help = "Optional domain filter: market_data, live_runtime, local_runtime, entry_model"
    )]
    pub(crate) domain: Option<String>,
    #[arg(long, help = "Optional provider id filter")]
    pub(crate) provider: Option<String>,
    #[arg(long, help = "Optional opt-in provider profile id or JSON path")]
    pub(crate) profile: Option<String>,
    #[arg(
        long,
        default_value = "",
        help = "Output format: json (default), compact, agent, jsonl, or human. `--compact`, `--agent`, `--human`, and `--jsonl` are aliases; do not combine them with `--output-format`."
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
        help = "Alias for --output-format jsonl"
    )]
    pub(crate) jsonl: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Alias for --output-format compact"
    )]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct PreBayesDiffArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value_t = true,
        help = "Refresh snapshot from current artifacts before printing"
    )]
    pub(crate) refresh: bool,
    #[arg(
        long,
        default_value = "",
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
