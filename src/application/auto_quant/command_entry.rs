use anyhow::Result;

use super::{auto_quant_bootstrap, auto_quant_status, auto_quant_update};

pub fn auto_quant_status_command(state_dir: &str) -> Result<()> {
    let status = auto_quant_status(state_dir)?;
    println!("{}", serde_json::to_string_pretty(&status)?);
    Ok(())
}

pub fn auto_quant_bootstrap_command(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<()> {
    let status = auto_quant_bootstrap(state_dir, repo_url, tracked_branch)?;
    println!("{}", serde_json::to_string_pretty(&status)?);
    Ok(())
}

pub fn auto_quant_update_command(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
    target_ref: Option<&str>,
) -> Result<()> {
    let report = auto_quant_update(state_dir, repo_url, tracked_branch, target_ref)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}
