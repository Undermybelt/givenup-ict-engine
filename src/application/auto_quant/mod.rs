mod adoption;
pub mod agent_material;
pub mod command_entry;
mod config;
mod futures_cost;
pub mod handoff;
mod health;
pub mod live;
pub mod pda_unit_batch;
pub mod pda_unit_dispatch;
mod persistence;
pub mod readiness;
pub mod real_trades;
mod repo_manager;
pub mod results;
mod seed_evidence;
mod status;
mod strategy_materials;
mod types;
mod update;
mod workspace_profile;

pub use agent_material::{
    AgentMaterialAggregateMetrics, AgentMaterialBatchArtifact, AgentMaterialBatchJob,
    AgentMaterialDispatchArtifact, AgentMaterialDispatchGroup, AgentMaterialDispatchGroupResult,
    AgentMaterialDispatchJobResult, AgentMaterialDispatchTotals, AgentMaterialPackage,
    AgentMaterialRankArtifact, AgentMaterialRankRow, AUTO_QUANT_AGENT_MATERIAL_BATCH_RULE_VERSION,
    AUTO_QUANT_AGENT_MATERIAL_DISPATCH_RULE_VERSION, AUTO_QUANT_AGENT_MATERIAL_RANK_RULE_VERSION,
};
pub use futures_cost::{FuturesCostCatalog, FuturesCostProfile};
pub use handoff::{
    AutoQuantFactorAutoresearchCommandInput, AutoQuantFactorResearchCommandInput,
    BuildFactorAutoresearchHandoffPayloadInput, BuildFactorResearchHandoffPayloadInput,
};
pub use handoff::{AutoQuantResearchHandoffPayload, AutoQuantWorkspaceConfig};
pub use pda_unit_batch::{
    AutoQuantPdaPrimitiveKind, AutoQuantPdaUnitBatchArtifact, AutoQuantPdaUnitBrief,
    AutoQuantPdaUnitDispatchGroup, AutoQuantPdaUnitJob, AutoQuantPdaUnitScope,
    AutoQuantUnitDirection, AUTO_QUANT_PDA_UNIT_BATCH_RULE_VERSION,
};
pub use pda_unit_dispatch::{
    AutoQuantPdaDispatchGroupResult, AutoQuantPdaDispatchTotals, AutoQuantPdaUnitAggregateMetrics,
    AutoQuantPdaUnitDispatchArtifact, AutoQuantPdaUnitResult,
    AUTO_QUANT_PDA_UNIT_DISPATCH_RULE_VERSION,
};
pub use readiness::{auto_quant_readiness, AutoQuantReadinessSurface};
pub use seed_evidence::AutoQuantSeedMaterialEvidenceArtifact;
pub use status::auto_quant_status;
pub use strategy_materials::AutoQuantStrategyMaterialSummary;
pub use types::{
    AutoQuantDependencyConfig, AutoQuantDependencyStatus, AutoQuantUpdateReport,
    AUTO_QUANT_ADAPTER_VERSION, AUTO_QUANT_BRANCH_ENV_VAR, AUTO_QUANT_CONFIG_FILE,
    AUTO_QUANT_DIR_ENV_VAR, AUTO_QUANT_REPO_URL_ENV_VAR, DEFAULT_AUTO_QUANT_BRANCH,
    DEFAULT_AUTO_QUANT_REPO_URL,
};
pub use update::{auto_quant_bootstrap, auto_quant_update};
pub use workspace_profile::{
    apply_workspace_profile, load_workspace_profile, materialize_workspace_profile,
    persist_workspace_profile_selection, AutoQuantWorkspaceProfileConfig,
    AUTO_QUANT_PROFILE_MANAGED, AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV,
};

#[cfg(test)]
mod tests {
    use std::path::Path;

    use super::config::config_path;
    use super::repo_manager::git_output;
    use super::*;

    fn init_repo(path: &Path) {
        std::fs::create_dir_all(path.join("versions")).unwrap();
        std::fs::create_dir_all(path.join("user_data/strategies")).unwrap();
        std::fs::write(path.join("README.md"), "readme").unwrap();
        std::fs::write(path.join("program.md"), "program").unwrap();
        std::fs::write(path.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(path.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            path.join("user_data/strategies/_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(path.join("versions/README.md"), "versions").unwrap();
        git_output(Some(path), &["init", "-b", "master"]).unwrap();
        git_output(Some(path), &["config", "user.name", "Test User"]).unwrap();
        git_output(Some(path), &["config", "user.email", "test@example.com"]).unwrap();
        git_output(Some(path), &["add", "."]).unwrap();
        git_output(Some(path), &["commit", "-m", "init"]).unwrap();
    }

    fn seed_data(path: &Path) {
        seed_data_for_stem(path, "seed");
    }

    fn seed_data_for_stem(path: &Path, stem: &str) {
        let data_dir = path.join("user_data/data");
        std::fs::create_dir_all(&data_dir).unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("{stem}-{index}.feather")), "").unwrap();
        }
    }

    fn seed_strategy(path: &Path, name: &str) {
        std::fs::write(
            path.join("user_data/strategies").join(format!("{name}.py")),
            "class SeedStrategy: pass",
        )
        .unwrap();
    }

    #[test]
    fn status_reports_bootstrap_needed_when_missing() {
        let temp = tempfile::tempdir().unwrap();
        let status = auto_quant_status(temp.path().to_str().unwrap()).unwrap();
        assert!(status.bootstrap_needed);
        assert!(!status.managed_repo_present);
    }

    #[test]
    fn status_rebases_copied_state_config_to_state_local_workspace() {
        let source_state = tempfile::tempdir().unwrap();
        let copied_state = tempfile::tempdir().unwrap();
        let source_workspace = source_state.path().join(".deps/auto-quant");
        let copied_workspace = copied_state.path().join(".deps/auto-quant");
        init_repo(&source_workspace);
        init_repo(&copied_workspace);

        let config = AutoQuantDependencyConfig {
            repo_url: "repo".to_string(),
            managed_dir: source_workspace.to_string_lossy().to_string(),
            tracked_branch: "master".to_string(),
            pinned_ref: None,
            adapter_version: AUTO_QUANT_ADAPTER_VERSION.to_string(),
            last_sync: None,
        };
        std::fs::write(
            config_path(copied_state.path().to_str().unwrap()),
            serde_json::to_string_pretty(&config).unwrap(),
        )
        .unwrap();

        let status = auto_quant_status(copied_state.path().to_str().unwrap()).unwrap();

        assert_eq!(
            status.managed_dir,
            copied_workspace.to_string_lossy().to_string()
        );
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
    fn bootstrap_missing_local_repo_error_names_input_and_recovery() {
        let temp = tempfile::tempdir().unwrap();
        let missing_repo = temp.path().join("missing-auto-quant-repo");
        let state = temp.path().join("state");

        let result = auto_quant_bootstrap(
            state.to_str().unwrap(),
            Some(missing_repo.to_str().unwrap()),
            Some("master"),
        );

        let err = result.expect_err("missing local repo must fail clearly");
        let message = format!("{err:#}");
        assert!(
            message.contains("auto_quant_bootstrap_repo_missing"),
            "unexpected error: {message}"
        );
        assert!(message.contains("repo-url"), "unexpected error: {message}");
        assert!(message.contains("recovery="), "unexpected error: {message}");
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
            format!(
                "ict-engine auto-quant-prepare --state-dir {}",
                state.path().to_string_lossy()
            )
        );
        assert_eq!(
            readiness.next_step["blocked_reason"],
            "auto_quant_prepare_required"
        );
    }

    #[test]
    fn readiness_reports_seed_required_when_data_is_ready_but_no_active_strategies_exist() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        seed_data(Path::new(&status.managed_dir));
        let readiness = super::readiness::auto_quant_readiness_from_status(&status);

        assert_eq!(readiness.status, "dependency_ready_seed_required");
        assert!(readiness.data_ready);
        assert_eq!(
            readiness.next_step["blocked_reason"],
            "auto_quant_seed_strategies_required"
        );
        assert!(readiness.recommended_next_command.starts_with("blocked:"));
    }

    #[test]
    fn readiness_reports_run_ready_after_data_and_active_strategy_exist() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        seed_data(Path::new(&status.managed_dir));
        seed_strategy(Path::new(&status.managed_dir), "SeedAlpha");
        let readiness = super::readiness::auto_quant_readiness_from_status(&status);

        assert_eq!(readiness.status, "dependency_ready_data_ready");
        assert_eq!(
            readiness.recommended_next_command,
            format!(
                "cd {} && ./.venv/bin/python run.py",
                crate::config::shell_quote(&status.managed_dir)
            )
        );
    }

    #[test]
    fn readiness_does_not_recommend_run_py_when_latest_handoff_exact_data_is_missing() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        seed_data(Path::new(&status.managed_dir));
        seed_strategy(Path::new(&status.managed_dir), "SeedAlpha");

        let requested_data = state.path().join("yf_crwd_5m.csv");
        std::fs::write(&requested_data, "timestamp,open,high,low,close,volume\n").unwrap();
        let payload = super::handoff::build_factor_research_handoff_payload(
            super::handoff::BuildFactorResearchHandoffPayloadInput {
                symbol: "YF_AI_SECURITY_CRWD5M_PDA_MTF_SOFT_CONFIRMATION_DOWNSTREAM",
                data: requested_data.to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: state.path().to_str().unwrap(),
                dependency_status: status.clone(),
            },
        );
        assert!(!payload.data_ready);
        super::persistence::persist_handoff_payload(state.path().to_str().unwrap(), &payload)
            .unwrap();

        let readiness =
            super::readiness::auto_quant_readiness(state.path().to_str().unwrap()).unwrap();

        assert_eq!(readiness.status, "dependency_ready_data_missing");
        assert!(!readiness.data_ready);
        assert!(readiness
            .recommended_next_command
            .contains("auto-quant-prepare"));
        assert!(readiness.notes.iter().any(|note| note.contains(
            "auto_quant_latest_handoff_exact_data_missing:YF_AI_SECURITY_CRWD5M_PDA_MTF_SOFT_CONFIRMATION_DOWNSTREAM"
        )));
    }

    #[test]
    fn readiness_uses_repo_local_venv_contract_for_synthetic_profile_run_tomac() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        super::workspace_profile::persist_workspace_profile_selection(
            state.path().to_str().unwrap(),
            Some(super::workspace_profile::AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV),
            "XLK",
            "/tmp/xlk.json",
        )
        .unwrap();
        let workspace = super::handoff::auto_quant_workspace_config_for_state(
            &status.managed_dir,
            state.path().to_str().unwrap(),
        );
        std::fs::create_dir_all(&workspace.data_dir).unwrap();
        for filename in &workspace.expected_data_files {
            std::fs::write(Path::new(&workspace.data_dir).join(filename), "").unwrap();
        }
        seed_strategy(Path::new(&status.managed_dir), "SeedAlpha");

        let readiness = super::readiness::auto_quant_readiness_from_status_with_state_dir(
            &status,
            state.path().to_str().unwrap(),
        );

        assert_eq!(readiness.status, "dependency_ready_data_ready");
        assert_eq!(workspace.profile_name.as_deref(), Some("synthetic_ohlcv"));
        assert_eq!(
            readiness.recommended_next_command,
            format!(
                "cd {} && ./.venv/bin/python run_tomac.py",
                crate::config::shell_quote(&status.managed_dir)
            )
        );
    }

    #[test]
    fn factor_research_handoff_prompt_demands_strategy_seeding_when_workspace_is_empty() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        let requested_data = state.path().join("nq.json");
        std::fs::write(&requested_data, "[]").unwrap();
        seed_data_for_stem(Path::new(&status.managed_dir), "nq");
        let payload = super::handoff::build_factor_research_handoff_payload(
            super::handoff::BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: requested_data.to_str().unwrap(),
                objective: "generic",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: state.path().to_str().unwrap(),
                dependency_status: status,
            },
        );

        assert!(payload
            .agent_prompt
            .contains("Never treat 'no strategies found' as completion"));
        assert!(payload
            .suggested_next_steps
            .iter()
            .any(|step| { step.contains("create 2-3 active non-underscore strategy files") }));
        assert!(payload
            .notes
            .iter()
            .any(|note| note == "auto_quant_seed_strategies_required"));
    }

    #[test]
    fn exact_runtime_synthetic_profile_ignores_generic_upstream_seed_strategy() {
        let upstream = tempfile::tempdir().unwrap();
        init_repo(upstream.path());
        let state = tempfile::tempdir().unwrap();
        let status = auto_quant_bootstrap(
            state.path().to_str().unwrap(),
            Some(upstream.path().to_str().unwrap()),
            Some("master"),
        )
        .unwrap();
        let requested_data = state.path().join("m2k_202606_5m.candles.json");
        std::fs::write(&requested_data, "[]").unwrap();
        super::workspace_profile::persist_workspace_profile_selection(
            state.path().to_str().unwrap(),
            Some(super::workspace_profile::AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV),
            "IBKR_M2K1M_RVOL_PDA_CONSISTENCY_FLOOR_AUTORESEARCH_REPAIR_V1",
            requested_data.to_str().unwrap(),
        )
        .unwrap();
        let workspace = super::handoff::auto_quant_workspace_config_for_state(
            &status.managed_dir,
            state.path().to_str().unwrap(),
        );
        std::fs::create_dir_all(&workspace.data_dir).unwrap();
        for filename in &workspace.expected_data_files {
            std::fs::write(Path::new(&workspace.data_dir).join(filename), "").unwrap();
        }
        seed_strategy(Path::new(&status.managed_dir), "TomacNQ_KillzoneBreakout");

        let payload = super::handoff::build_factor_autoresearch_handoff_payload(
            super::handoff::BuildFactorAutoresearchHandoffPayloadInput {
                symbol: "IBKR_M2K1M_RVOL_PDA_CONSISTENCY_FLOOR_AUTORESEARCH_REPAIR_V1",
                data: requested_data.to_str().unwrap(),
                objective: "m2k_rvol_pda_same_root_transition_pda_repair",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                iterations: 1,
                session_id: None,
                state_dir: state.path().to_str().unwrap(),
                dependency_status: status,
            },
        );

        assert!(payload.data_ready);
        assert!(payload
            .notes
            .iter()
            .any(|note| note == "auto_quant_seed_strategies_required"));
        assert!(payload
            .notes
            .iter()
            .any(|note| note == "auto_quant_active_strategy_count=0"));
        assert!(payload
            .suggested_next_steps
            .iter()
            .any(|step| step.contains("create 2-3 active non-underscore strategy files")));
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
