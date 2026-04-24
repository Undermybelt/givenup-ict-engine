pub mod command_entry;

use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

use anyhow::{anyhow, bail, Context, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

pub const AUTO_QUANT_CONFIG_FILE: &str = "auto_quant_dependency.json";
pub const AUTO_QUANT_ADAPTER_VERSION: &str = "v1";
pub const AUTO_QUANT_REPO_URL_ENV_VAR: &str = "ICT_ENGINE_AUTO_QUANT_REPO_URL";
pub const AUTO_QUANT_BRANCH_ENV_VAR: &str = "ICT_ENGINE_AUTO_QUANT_BRANCH";
pub const AUTO_QUANT_DIR_ENV_VAR: &str = "ICT_ENGINE_AUTO_QUANT_DIR";
pub const DEFAULT_AUTO_QUANT_REPO_URL: &str = "https://github.com/TraderAlice/Auto-Quant.git";
pub const DEFAULT_AUTO_QUANT_BRANCH: &str = "master";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantDependencyConfig {
    pub repo_url: String,
    pub managed_dir: String,
    pub tracked_branch: String,
    pub pinned_ref: Option<String>,
    pub adapter_version: String,
    pub last_sync: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantDependencyStatus {
    pub repo_url: String,
    pub managed_dir: String,
    pub tracked_branch: String,
    pub pinned_ref: Option<String>,
    pub current_commit: Option<String>,
    pub upstream_commit: Option<String>,
    pub bootstrap_needed: bool,
    pub config_present: bool,
    pub managed_repo_present: bool,
    pub healthy: bool,
    pub update_available: bool,
    pub required_files: Vec<String>,
    pub notes: Vec<String>,
    pub adapter_version: String,
    pub last_sync: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantUpdateReport {
    pub repo_url: String,
    pub managed_dir: String,
    pub tracked_branch: String,
    pub previous_commit: Option<String>,
    pub target_ref: String,
    pub current_commit: String,
    pub applied: bool,
    pub rolled_back: bool,
    pub healthy: bool,
    pub notes: Vec<String>,
    pub adapter_version: String,
    pub last_sync: DateTime<Utc>,
}

fn required_files() -> Vec<String> {
    vec![
        "README.md".to_string(),
        "program.md".to_string(),
        "prepare.py".to_string(),
        "run.py".to_string(),
        "versions/README.md".to_string(),
    ]
}

fn config_path(state_dir: &str) -> PathBuf {
    Path::new(state_dir).join(AUTO_QUANT_CONFIG_FILE)
}

fn default_managed_dir(state_dir: &str) -> PathBuf {
    Path::new(state_dir).join(".deps").join("auto-quant")
}

fn resolve_repo_url() -> String {
    env::var(AUTO_QUANT_REPO_URL_ENV_VAR)
        .unwrap_or_else(|_| DEFAULT_AUTO_QUANT_REPO_URL.to_string())
}

fn resolve_tracked_branch() -> String {
    env::var(AUTO_QUANT_BRANCH_ENV_VAR).unwrap_or_else(|_| DEFAULT_AUTO_QUANT_BRANCH.to_string())
}

fn resolve_managed_dir(state_dir: &str) -> PathBuf {
    env::var(AUTO_QUANT_DIR_ENV_VAR)
        .map(|value| PathBuf::from(value).expand_home())
        .unwrap_or_else(|_| default_managed_dir(state_dir))
}

trait ExpandHome {
    fn expand_home(self) -> PathBuf;
}

impl ExpandHome for PathBuf {
    fn expand_home(self) -> PathBuf {
        let text = self.to_string_lossy();
        if let Some(stripped) = text.strip_prefix("~/") {
            if let Ok(home) = env::var("HOME") {
                return Path::new(&home).join(stripped);
            }
        }
        self
    }
}

fn default_config(state_dir: &str) -> AutoQuantDependencyConfig {
    AutoQuantDependencyConfig {
        repo_url: resolve_repo_url(),
        managed_dir: resolve_managed_dir(state_dir).to_string_lossy().to_string(),
        tracked_branch: resolve_tracked_branch(),
        pinned_ref: None,
        adapter_version: AUTO_QUANT_ADAPTER_VERSION.to_string(),
        last_sync: None,
    }
}

fn load_config(state_dir: &str) -> Result<Option<AutoQuantDependencyConfig>> {
    let path = config_path(state_dir);
    if !path.exists() {
        return Ok(None);
    }
    let content = std::fs::read_to_string(&path)
        .with_context(|| format!("reading auto-quant config '{}'", path.display()))?;
    let config = serde_json::from_str(&content)
        .with_context(|| format!("parsing auto-quant config '{}'", path.display()))?;
    Ok(Some(config))
}

fn save_config(state_dir: &str, config: &AutoQuantDependencyConfig) -> Result<()> {
    let path = config_path(state_dir);
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent)
            .with_context(|| format!("creating auto-quant config parent '{}'", parent.display()))?;
    }
    std::fs::write(&path, serde_json::to_string_pretty(config)?)
        .with_context(|| format!("writing auto-quant config '{}'", path.display()))?;
    Ok(())
}

fn git_output(cwd: Option<&Path>, args: &[&str]) -> Result<String> {
    let mut command = Command::new("git");
    command.args(args);
    if let Some(cwd) = cwd {
        command.current_dir(cwd);
    }
    let output = command
        .output()
        .with_context(|| format!("running git {}", args.join(" ")))?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        bail!("git {} failed: {}", args.join(" "), stderr.trim());
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

fn is_git_repo(dir: &Path) -> bool {
    git_output(Some(dir), &["rev-parse", "--git-dir"]).is_ok()
}

fn current_commit(dir: &Path) -> Result<String> {
    git_output(Some(dir), &["rev-parse", "HEAD"])
}

fn upstream_commit(dir: &Path, tracked_branch: &str) -> Result<String> {
    let reference = format!("refs/heads/{tracked_branch}");
    let line = git_output(Some(dir), &["ls-remote", "origin", &reference])?;
    let commit = line
        .split_whitespace()
        .next()
        .ok_or_else(|| anyhow!("no upstream commit found for '{}'", tracked_branch))?;
    Ok(commit.to_string())
}

fn verify_checkout(dir: &Path) -> (bool, Vec<String>) {
    let mut notes = Vec::new();
    let mut healthy = true;
    if !is_git_repo(dir) {
        healthy = false;
        notes.push("managed_dir_is_not_a_git_repo".to_string());
    }
    for relative in required_files() {
        if !dir.join(&relative).exists() {
            healthy = false;
            notes.push(format!("missing_required_file={relative}"));
        }
    }
    (healthy, notes)
}

fn ensure_bootstrapped_config(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> AutoQuantDependencyConfig {
    let mut config = load_config(state_dir)
        .ok()
        .flatten()
        .unwrap_or_else(|| default_config(state_dir));
    if let Some(repo_url) = repo_url {
        config.repo_url = repo_url.to_string();
    }
    if let Some(tracked_branch) = tracked_branch {
        config.tracked_branch = tracked_branch.to_string();
    }
    if config.managed_dir.trim().is_empty() {
        config.managed_dir = resolve_managed_dir(state_dir).to_string_lossy().to_string();
    }
    config.adapter_version = AUTO_QUANT_ADAPTER_VERSION.to_string();
    config
}

pub fn auto_quant_status(state_dir: &str) -> Result<AutoQuantDependencyStatus> {
    let config = load_config(state_dir)?;
    let config_present = config.is_some();
    let config = config.unwrap_or_else(|| default_config(state_dir));
    let managed_dir = PathBuf::from(&config.managed_dir);
    let managed_repo_present = managed_dir.exists() && is_git_repo(&managed_dir);
    let bootstrap_needed = !managed_repo_present;
    let mut notes = Vec::new();
    let (healthy, verify_notes) = if managed_repo_present {
        verify_checkout(&managed_dir)
    } else {
        (false, vec!["auto_quant_not_bootstrapped".to_string()])
    };
    notes.extend(verify_notes);
    let current_commit = if managed_repo_present {
        current_commit(&managed_dir).ok()
    } else {
        None
    };
    let upstream_commit = if managed_repo_present {
        match upstream_commit(&managed_dir, &config.tracked_branch) {
            Ok(commit) => Some(commit),
            Err(err) => {
                notes.push(format!("upstream_check_failed={err}"));
                None
            }
        }
    } else {
        None
    };
    let pinned_ref = config.pinned_ref.clone().or_else(|| current_commit.clone());
    Ok(AutoQuantDependencyStatus {
        repo_url: config.repo_url,
        managed_dir: managed_dir.to_string_lossy().to_string(),
        tracked_branch: config.tracked_branch,
        pinned_ref,
        current_commit: current_commit.clone(),
        upstream_commit: upstream_commit.clone(),
        bootstrap_needed,
        config_present,
        managed_repo_present,
        healthy,
        update_available: matches!((&current_commit, &upstream_commit), (Some(current), Some(upstream)) if current != upstream),
        required_files: required_files(),
        notes,
        adapter_version: config.adapter_version,
        last_sync: config.last_sync,
    })
}

pub fn auto_quant_bootstrap(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
) -> Result<AutoQuantDependencyStatus> {
    let mut config = ensure_bootstrapped_config(state_dir, repo_url, tracked_branch);
    let managed_dir = PathBuf::from(&config.managed_dir);
    if managed_dir.exists() {
        if !is_git_repo(&managed_dir) {
            bail!(
                "managed auto-quant directory exists but is not a git repo: '{}'",
                managed_dir.display()
            );
        }
    } else {
        if let Some(parent) = managed_dir.parent() {
            std::fs::create_dir_all(parent).with_context(|| {
                format!("creating auto-quant managed parent '{}'", parent.display())
            })?;
        }
        git_output(
            None,
            &[
                "clone",
                "--branch",
                &config.tracked_branch,
                &config.repo_url,
                &config.managed_dir,
            ],
        )?;
    }
    let pinned_ref = current_commit(&managed_dir)?;
    config.pinned_ref = Some(pinned_ref);
    config.last_sync = Some(Utc::now());
    save_config(state_dir, &config)?;
    auto_quant_status(state_dir)
}

pub fn auto_quant_update(
    state_dir: &str,
    repo_url: Option<&str>,
    tracked_branch: Option<&str>,
    target_ref: Option<&str>,
) -> Result<AutoQuantUpdateReport> {
    let mut config = ensure_bootstrapped_config(state_dir, repo_url, tracked_branch);
    let managed_dir = PathBuf::from(&config.managed_dir);
    if !managed_dir.exists() || !is_git_repo(&managed_dir) {
        auto_quant_bootstrap(state_dir, repo_url, tracked_branch)?;
    }
    let managed_dir = PathBuf::from(&config.managed_dir);
    let previous_commit = current_commit(&managed_dir).ok();
    let target_ref = target_ref
        .map(str::to_string)
        .unwrap_or_else(|| config.tracked_branch.clone());
    let mut notes = Vec::new();
    if target_ref == config.tracked_branch {
        git_output(
            Some(&managed_dir),
            &[
                "fetch",
                "origin",
                &config.tracked_branch,
                "--tags",
                "--prune",
            ],
        )?;
    } else {
        git_output(
            Some(&managed_dir),
            &["fetch", "origin", "--tags", "--prune"],
        )?;
    }
    let update_result = if target_ref == config.tracked_branch {
        git_output(Some(&managed_dir), &["checkout", "--detach", "FETCH_HEAD"])
    } else {
        git_output(Some(&managed_dir), &["checkout", "--detach", &target_ref])
    };
    if let Err(err) = update_result {
        notes.push(format!("update_failed={err}"));
        return Err(err);
    }
    let current_commit = current_commit(&managed_dir)?;
    let (healthy, verify_notes) = verify_checkout(&managed_dir);
    notes.extend(verify_notes);
    let mut rolled_back = false;
    if !healthy {
        if let Some(previous_commit) = &previous_commit {
            git_output(
                Some(&managed_dir),
                &["checkout", "--detach", previous_commit],
            )?;
            rolled_back = true;
            notes.push("rolled_back_to_previous_commit".to_string());
        } else {
            bail!(
                "auto-quant update produced an unhealthy checkout and no rollback target existed"
            );
        }
    } else {
        config.pinned_ref = Some(current_commit.clone());
        config.last_sync = Some(Utc::now());
        save_config(state_dir, &config)?;
    }
    Ok(AutoQuantUpdateReport {
        repo_url: config.repo_url,
        managed_dir: config.managed_dir,
        tracked_branch: config.tracked_branch,
        previous_commit,
        target_ref,
        current_commit,
        applied: !rolled_back,
        rolled_back,
        healthy,
        notes,
        adapter_version: config.adapter_version,
        last_sync: config.last_sync.unwrap_or_else(Utc::now),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn init_repo(path: &Path) {
        std::fs::create_dir_all(path.join("versions")).unwrap();
        std::fs::write(path.join("README.md"), "readme").unwrap();
        std::fs::write(path.join("program.md"), "program").unwrap();
        std::fs::write(path.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(path.join("run.py"), "print('run')").unwrap();
        std::fs::write(path.join("versions/README.md"), "versions").unwrap();
        git_output(Some(path), &["init", "-b", "master"]).unwrap();
        git_output(Some(path), &["config", "user.name", "Test User"]).unwrap();
        git_output(Some(path), &["config", "user.email", "test@example.com"]).unwrap();
        git_output(Some(path), &["add", "."]).unwrap();
        git_output(Some(path), &["commit", "-m", "init"]).unwrap();
    }

    #[test]
    fn status_reports_bootstrap_needed_when_missing() {
        let temp = tempfile::tempdir().unwrap();
        let status = auto_quant_status(temp.path().to_str().unwrap()).unwrap();
        assert!(status.bootstrap_needed);
        assert!(!status.managed_repo_present);
    }

    #[test]
    fn bootstrap_clones_repo_and_persists_config() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        assert!(status.managed_repo_present);
        assert!(status.healthy);
        assert!(config_path(state.path().to_str().unwrap()).exists());
    }

    #[test]
    fn update_advances_to_new_upstream_commit() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let first = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        std::fs::write(upstream.path().join("README.md"), "changed").unwrap();
        git_output(Some(upstream.path()), &["add", "README.md"]).unwrap();
        git_output(Some(upstream.path()), &["commit", "-m", "change"]).unwrap();
        let report = auto_quant_update(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
            None,
        )
        .unwrap();
        assert_ne!(
            report.previous_commit.as_deref(),
            Some(report.current_commit.as_str())
        );
        assert_eq!(report.previous_commit, first.current_commit);
        assert!(report.applied);
        assert!(report.healthy);
    }
}
