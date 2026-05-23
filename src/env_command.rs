use anyhow::Result;
use clap::Args;
use serde_json::Value;
use std::env;

use crate::auto_quant_command::AUTO_QUANT_OUTPUT_DIR_ENV_VAR;
use crate::state_dir::{DEFAULT_STATE_DIR, STATE_DIR_ENV_VAR};
use ict_engine::application::auto_quant::{
    AUTO_QUANT_BRANCH_ENV_VAR, AUTO_QUANT_DIR_ENV_VAR, AUTO_QUANT_REPO_URL_ENV_VAR,
};
use ict_engine::application::output_foundation::print_redacted_json;

#[derive(Args)]
pub(crate) struct EnvArgs {
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

pub(crate) fn build_env_report() -> Value {
    let variables = [
        (
            STATE_DIR_ENV_VAR,
            "default state directory for CLI commands",
        ),
        (
            "ICT_ENGINE_STAGED_ORCHESTRATION",
            "enable staged orchestration flow",
        ),
        (
            "ICT_ENGINE_BELIEF_PRIMARY",
            "select the primary belief engine",
        ),
        (
            "ICT_ENGINE_FAMILY_HISTORY_WINDOW",
            "override family history window length",
        ),
        (
            "ICT_ENGINE_TOMAC_ROOT",
            "set the TOMAC root for futures cleaning commands",
        ),
        (
            AUTO_QUANT_OUTPUT_DIR_ENV_VAR,
            "override auto-quant output dir (default: <state-dir>/auto-quant/)",
        ),
        (
            AUTO_QUANT_REPO_URL_ENV_VAR,
            "override the Auto-Quant upstream repository URL",
        ),
        (
            AUTO_QUANT_BRANCH_ENV_VAR,
            "override the tracked Auto-Quant branch",
        ),
        (
            AUTO_QUANT_DIR_ENV_VAR,
            "override the managed Auto-Quant checkout directory",
        ),
        (
            "ICT_EXECUTION_FOCUS",
            "enable execution-focus reporting surfaces",
        ),
        ("HOME", "OS-provided home directory used for path discovery"),
    ]
    .into_iter()
    .map(|(key, description)| {
        let value = env::var(key).ok();
        serde_json::json!({
            "name": key,
            "description": description,
            "set": value.is_some(),
            "value": value,
        })
    })
    .collect::<Vec<_>>();
    serde_json::json!({
        "state_dir_env_var": STATE_DIR_ENV_VAR,
        "default_state_dir": DEFAULT_STATE_DIR,
        "variables": variables,
    })
}

pub(crate) fn env_command(output_format: &str) -> Result<()> {
    let report = build_env_report();
    match output_format.trim().to_ascii_lowercase().as_str() {
        "json" | "compact" | "agent" => print_redacted_json(&report),
        "human" => {
            let variables = report
                .get("variables")
                .and_then(serde_json::Value::as_array)
                .cloned()
                .unwrap_or_default();
            let set_count = variables
                .iter()
                .filter(|variable| {
                    variable
                        .get("set")
                        .and_then(serde_json::Value::as_bool)
                        .unwrap_or(false)
                })
                .count();
            println!(
                "Environment | variables={} | set={} | unset={} | state_dir_env_var={} | default_state_dir={}",
                variables.len(),
                set_count,
                variables.len().saturating_sub(set_count),
                report
                    .get("state_dir_env_var")
                    .and_then(serde_json::Value::as_str)
                    .unwrap_or("unavailable"),
                report
                    .get("default_state_dir")
                    .and_then(serde_json::Value::as_str)
                    .unwrap_or("unavailable")
            );
            Ok(())
        }
        other => anyhow::bail!("unsupported env output format '{}'", other),
    }
}
