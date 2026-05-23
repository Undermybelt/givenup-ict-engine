use anyhow::{Context, Result};
use std::env;

pub(crate) const DEFAULT_STATE_DIR: &str = "state";
pub(crate) const STATE_DIR_ENV_VAR: &str = "ICT_ENGINE_STATE_DIR";

fn should_warn_about_default_state_dir(state_dir: &str) -> bool {
    if state_dir != DEFAULT_STATE_DIR || env::var_os(STATE_DIR_ENV_VAR).is_some() {
        return false;
    }
    let path = std::path::Path::new(state_dir);
    if path.exists() {
        return false;
    }
    let Ok(cwd) = env::current_dir() else {
        return false;
    };
    !cwd.join("Cargo.toml").exists() && !cwd.join(".ict-engine").exists()
}

pub(crate) fn ensure_state_dir_ready(state_dir: &str) -> Result<()> {
    if should_warn_about_default_state_dir(state_dir) {
        eprintln!(
            "auto-creating state dir at ./state; set --state-dir or {} to customize",
            STATE_DIR_ENV_VAR
        );
    }
    std::fs::create_dir_all(state_dir)
        .with_context(|| format!("creating state directory '{}'", state_dir))?;
    Ok(())
}
