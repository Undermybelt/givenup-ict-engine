use clap::Args;

#[derive(Args)]
pub(crate) struct ArtifactLineageArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing artifact ledger"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional artifact id to focus lineage output")]
    pub(crate) artifact_id: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only the latest lineage rows"
    )]
    pub(crate) latest_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only improving lineage rows"
    )]
    pub(crate) improving_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only regressing lineage rows"
    )]
    pub(crate) regressing_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only lineage rows with rule breaks"
    )]
    pub(crate) rule_break_only: bool,
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
pub(crate) struct ArtifactStatusArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing artifact ledger"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Optional artifact id to inspect")]
    pub(crate) artifact_id: Option<String>,
    #[arg(long, help = "Optional artifact kind filter")]
    pub(crate) kind: Option<String>,
    #[arg(
        long,
        default_value_t = false,
        help = "Keep only the latest artifact per kind (one row per artifact_kind, most recent by generated_at)"
    )]
    pub(crate) latest_only: bool,
    #[arg(long, default_value_t = false, help = "Show only actionable artifacts")]
    pub(crate) actionable_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Show only artifacts with review rule breaks"
    )]
    pub(crate) rule_break_only: bool,
    #[arg(long, default_value = "generated", help = "Sort key for artifact rows")]
    pub(crate) sort_by: String,
    #[arg(
        long,
        default_value_t = true,
        help = "Sort descending instead of ascending"
    )]
    pub(crate) descending: bool,
    #[arg(long, help = "Maximum artifact rows to print")]
    pub(crate) limit: Option<usize>,
    #[arg(long, help = "Print only the most recent N artifact rows")]
    pub(crate) recent_n: Option<usize>,
    #[arg(long, default_value_t = false, help = "Show only consumed artifacts")]
    pub(crate) consumed_only: bool,
    #[arg(
        long,
        default_value_t = false,
        help = "Aggregate artifact rows by kind"
    )]
    pub(crate) bucket_by_kind: bool,
    #[arg(
        long,
        default_value = "kind",
        help = "Sort key for bucketed artifact output"
    )]
    pub(crate) bucket_order_by: String,
    #[arg(long, help = "Maximum bucket rows to print")]
    pub(crate) bucket_limit: Option<usize>,
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
pub(crate) struct ArtifactDiffArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing artifact ledger"
    )]
    pub(crate) state_dir: String,
    #[arg(long, help = "Left artifact id for diff comparison")]
    pub(crate) left_artifact_id: String,
    #[arg(long, help = "Right artifact id for diff comparison")]
    pub(crate) right_artifact_id: String,
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
