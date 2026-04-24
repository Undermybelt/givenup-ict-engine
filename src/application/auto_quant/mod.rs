mod adoption;
pub mod command_entry;
mod config;
pub mod handoff;
mod health;
mod persistence;
pub mod readiness;
mod repo_manager;
mod status;
mod types;
mod update;

pub use handoff::{AutoQuantFactorAutoresearchCommandInput, AutoQuantFactorResearchCommandInput};
pub use handoff::{AutoQuantResearchHandoffPayload, AutoQuantWorkspaceConfig};
pub use readiness::{auto_quant_readiness, AutoQuantReadinessSurface};
pub use status::auto_quant_status;
pub use types::{
    AutoQuantDependencyConfig, AutoQuantDependencyStatus, AutoQuantUpdateReport,
    AUTO_QUANT_ADAPTER_VERSION, AUTO_QUANT_BRANCH_ENV_VAR, AUTO_QUANT_CONFIG_FILE,
    AUTO_QUANT_DIR_ENV_VAR, AUTO_QUANT_REPO_URL_ENV_VAR, DEFAULT_AUTO_QUANT_BRANCH,
    DEFAULT_AUTO_QUANT_REPO_URL,
};
pub use update::{auto_quant_bootstrap, auto_quant_update};

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::config::config_path;
    use super::repo_manager::git_output;
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
    fn readiness_reports_missing_dependency_with_bootstrap_next_step() {
        let temp = tempfile::tempdir().unwrap();
        let readiness =
            super::readiness::auto_quant_readiness(temp.path().to_str().unwrap()).unwrap();

        assert_eq!(readiness.status, "missing_dependency");
        assert!(readiness.bootstrap_needed);
        assert!(!readiness.dependency_healthy);
        assert!(!readiness.data_ready);
        assert_eq!(
            readiness.recommended_next_command,
            format!(
                "ict-engine auto-quant-bootstrap --state-dir {}",
                temp.path().to_string_lossy()
            )
        );
        assert_eq!(
            readiness.next_step["blocked_reason"],
            "auto_quant_bootstrap_required"
        );
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
    fn readiness_reports_data_missing_after_healthy_bootstrap() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        let readiness = super::readiness::auto_quant_readiness_from_status(&status);

        assert_eq!(readiness.status, "dependency_ready_data_missing");
        assert!(!readiness.bootstrap_needed);
        assert!(readiness.dependency_healthy);
        assert!(!readiness.data_ready);
        assert_eq!(
            readiness.recommended_next_command,
            format!("uv run {}/prepare.py", status.managed_dir)
        );
        assert_eq!(
            readiness.next_step["blocked_reason"],
            "auto_quant_prepare_required"
        );
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
