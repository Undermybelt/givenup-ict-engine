use clap::Args;

#[derive(Args)]
pub(crate) struct FactorCandidatePacksArgs {
    #[arg(
        long,
        default_value = "support/examples/factor_candidate_packs/curated-auto-quant-v1",
        help = "Directory containing repo-local factor candidate packs"
    )]
    pub(crate) candidate_pack_root: String,
    #[arg(
        long,
        help = "Optional symbol bucket used when persisting the inventory into workflow state"
    )]
    pub(crate) symbol: Option<String>,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        help = "Optional state directory; when present, the inventory is written into the artifact ledger"
    )]
    pub(crate) state_dir: Option<String>,
    #[arg(
        long,
        default_value = "human",
        help = "Output format: human or json. `--compact` and `--agent` are aliases for json; `--human` is an alias for human."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct FactorCandidateAdmissionTargetsArgs {
    #[arg(
        long,
        default_value = "support/examples/factor_candidate_packs/curated-auto-quant-v1",
        help = "Directory containing repo-local factor candidate packs"
    )]
    pub(crate) candidate_pack_root: String,
    #[arg(
        long,
        help = "Symbol bucket for the structural admission target export"
    )]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for the exported structural path ranking target"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "human",
        help = "Output format: human or json. `--compact` and `--agent` are aliases for json; `--human` is an alias for human."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct RegimeConfidenceAssetsArgs {
    #[arg(
        long,
        default_value = "config/regime_confidence_assets_v1.csv",
        help = "CSV ledger containing recovered positive and fail-closed regime-confidence assets"
    )]
    pub(crate) asset_ledger: String,
    #[arg(
        long,
        help = "Optional symbol bucket used when persisting the inventory into workflow state"
    )]
    pub(crate) symbol: Option<String>,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        help = "Optional state directory; when present, the inventory is written into the artifact ledger"
    )]
    pub(crate) state_dir: Option<String>,
    #[arg(
        long,
        default_value = "human",
        help = "Output format: human or json. `--compact` and `--agent` are aliases for json; `--human` is an alias for human."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}

#[derive(Args)]
pub(crate) struct FactorAssetClosureIntakeArgs {
    #[arg(
        long,
        default_value = "support/examples/factor_candidate_packs/curated-auto-quant-v1",
        help = "Directory containing repo-local factor candidate packs"
    )]
    pub(crate) candidate_pack_root: String,
    #[arg(
        long,
        default_value = "config/regime_confidence_assets_v1.csv",
        help = "CSV ledger containing recovered positive and fail-closed regime-confidence assets"
    )]
    pub(crate) asset_ledger: String,
    #[arg(long, help = "Symbol bucket for the combined closed-loop intake")]
    pub(crate) symbol: String,
    #[arg(
        long,
        env = "ICT_ENGINE_STATE_DIR",
        default_value = "state",
        help = "State directory for the combined closed-loop intake"
    )]
    pub(crate) state_dir: String,
    #[arg(
        long,
        default_value = "human",
        help = "Output format: human or json. `--compact` and `--agent` are aliases for json; `--human` is an alias for human."
    )]
    pub(crate) output_format: String,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) compact: bool,
    #[arg(long, help = "Alias for --output-format json")]
    pub(crate) agent: bool,
    #[arg(long, help = "Alias for --output-format human")]
    pub(crate) human: bool,
}
