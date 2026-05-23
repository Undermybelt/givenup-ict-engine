use clap::Args;

#[derive(Args)]
pub(crate) struct RegisterStructuralPathRankingTrainerArtifactArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing policy_training artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Explicit external trainer artifact URI or path to register; runtime reuse remains disabled until explicitly enabled"
    )]
    pub(crate) artifact_uri: String,
    #[arg(long, help = "External model family label, for example catboost")]
    pub(crate) model_family: String,
    #[arg(
        long,
        default_value = "raw_path_score",
        help = "Score column emitted by the external trainer artifact"
    )]
    pub(crate) score_column: String,
    #[arg(
        long,
        help = "Optional override for the trained row count recorded in the artifact"
    )]
    pub(crate) trained_rows: Option<usize>,
    #[arg(
        long,
        help = "Optional override for the calibration row count recorded in the artifact"
    )]
    pub(crate) calibration_rows: Option<usize>,
}

#[derive(Args)]
pub(crate) struct ClearStructuralPathRankingTrainerArtifactArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing policy_training artifacts"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct EnableStructuralPathRankingRuntimeArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow snapshot, learning state, and policy_training artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "candidate_set_only",
        help = "Reuse mode: candidate_set_only or prefer_history"
    )]
    pub(crate) reuse_mode: String,
}

#[derive(Args)]
pub(crate) struct DisableStructuralPathRankingRuntimeArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow snapshot, learning state, and policy_training artifacts"
    )]
    pub(crate) state_dir: String,
}

#[derive(Args)]
pub(crate) struct ExportStructuralPathRankingTargetArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow snapshot, learning state, and policy_training artifacts"
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
pub(crate) struct ApplyStructuralPathRankingExternalScoresArgs {
    #[arg(long, help = "Instrument identifier supplied by the caller")]
    pub(crate) symbol: String,
    #[arg(
        long,
        default_value = "state",
        help = "State directory containing workflow snapshot, learning state, and policy_training artifacts"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        help = "Path to a CSV or JSONL file with candidate_set_id,path_id,raw_path_score rows"
    )]
    pub(crate) scores_file: String,
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
