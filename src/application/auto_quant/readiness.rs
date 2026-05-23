use anyhow::Result;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::Path;

use crate::application::release_closure::workflow_next_step_view;
use crate::state::{
    load_artifact_ledger, load_state, recommended_next_command_meta, RecommendedNextCommandMeta,
};

use super::handoff::{
    auto_quant_active_strategy_count, auto_quant_data_ready, auto_quant_handoff_data_ready,
    auto_quant_prepare_cli_command, auto_quant_run_command, auto_quant_workspace_config_for_state,
    AutoQuantResearchHandoffPayload, AutoQuantWorkspaceConfig,
};
use super::status::auto_quant_status;
use super::types::AutoQuantDependencyStatus;
use super::workspace_profile::apply_handoff_workspace_profile;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AutoQuantReadinessSurface {
    pub status: String,
    pub healthy: bool,
    pub bootstrap_needed: bool,
    pub dependency_healthy: bool,
    pub data_ready: bool,
    pub update_available: bool,
    pub managed_dir: String,
    pub workspace: AutoQuantWorkspaceConfig,
    pub dependency_status: AutoQuantDependencyStatus,
    pub recommended_next_command: String,
    pub recommended_next_command_meta: RecommendedNextCommandMeta,
    pub next_step: Value,
    pub notes: Vec<String>,
}

pub fn auto_quant_readiness(state_dir: &str) -> Result<AutoQuantReadinessSurface> {
    let dependency_status = auto_quant_status(state_dir)?;
    if dependency_status.bootstrap_needed {
        if let Some(payload) = latest_handoff_payloads(state_dir)
            .into_iter()
            .rev()
            .find(|payload| !payload.dependency_status.bootstrap_needed)
        {
            let mut workspace = payload.workspace.clone();
            apply_handoff_workspace_profile(&payload, &mut workspace);
            let data_ready = auto_quant_handoff_data_ready(
                &workspace,
                &payload.data_path,
                payload.paired_data_path.as_deref(),
            );
            let mut readiness = auto_quant_readiness_from_status_and_data(
                &payload.dependency_status,
                state_dir,
                workspace,
                data_ready,
            );
            readiness.notes.push(format!(
                "auto_quant_dependency_resolved_from_handoff:{}",
                payload.artifact_id
            ));
            return Ok(readiness);
        }
    }
    Ok(auto_quant_readiness_from_status_with_state_dir(
        &dependency_status,
        state_dir,
    ))
}

pub fn auto_quant_readiness_from_status(
    dependency_status: &AutoQuantDependencyStatus,
) -> AutoQuantReadinessSurface {
    let state_dir = Path::new(&dependency_status.managed_dir)
        .parent()
        .and_then(|path| {
            if path
                .file_name()
                .and_then(|value| value.to_str())
                .is_some_and(|value| value == ".deps")
            {
                path.parent()
            } else {
                Some(path)
            }
        })
        .map(|path| path.to_string_lossy().to_string())
        .unwrap_or_else(|| "state".to_string());
    auto_quant_readiness_from_status_with_state_dir(dependency_status, &state_dir)
}

pub fn auto_quant_readiness_from_status_with_state_dir(
    dependency_status: &AutoQuantDependencyStatus,
    state_dir: &str,
) -> AutoQuantReadinessSurface {
    let mut workspace =
        auto_quant_workspace_config_for_state(&dependency_status.managed_dir, state_dir);
    let mut data_ready = auto_quant_data_ready(&workspace);
    if let Some(payload) = latest_auto_quant_handoff_payload(state_dir) {
        workspace = payload.workspace.clone();
        apply_handoff_workspace_profile(&payload, &mut workspace);
        data_ready = auto_quant_handoff_data_ready(
            &workspace,
            &payload.data_path,
            payload.paired_data_path.as_deref(),
        );
    }
    let mut readiness = auto_quant_readiness_from_status_and_data(
        dependency_status,
        state_dir,
        workspace,
        data_ready,
    );
    if let Some(guard) = latest_handoff_exact_data_guard(state_dir) {
        readiness.notes.extend(guard.notes);
    }
    readiness
}

#[derive(Debug, Clone)]
struct LatestHandoffExactDataGuard {
    notes: Vec<String>,
}

fn latest_handoff_exact_data_guard(state_dir: &str) -> Option<LatestHandoffExactDataGuard> {
    let latest_payloads = latest_handoff_payloads(state_dir);
    if latest_payloads.is_empty() {
        return None;
    }
    let mut notes = Vec::new();
    let all_ready = latest_payloads.iter().all(|payload| {
        let mut workspace = payload.workspace.clone();
        apply_handoff_workspace_profile(payload, &mut workspace);
        let ready = auto_quant_handoff_data_ready(
            &workspace,
            &payload.data_path,
            payload.paired_data_path.as_deref(),
        );
        if !ready {
            notes.push(format!(
                "auto_quant_latest_handoff_exact_data_missing:{}:{}",
                payload.symbol, payload.artifact_id
            ));
        }
        ready
    });
    let _ = all_ready;
    Some(LatestHandoffExactDataGuard { notes })
}

pub(crate) fn latest_auto_quant_handoff_payload(
    state_dir: &str,
) -> Option<AutoQuantResearchHandoffPayload> {
    latest_handoff_payloads(state_dir).into_iter().last()
}

fn latest_handoff_payloads(state_dir: &str) -> Vec<AutoQuantResearchHandoffPayload> {
    let state_root = Path::new(state_dir);
    let Ok(entries) = std::fs::read_dir(state_root) else {
        return Vec::new();
    };
    let mut latest_payloads = Vec::new();
    for entry in entries.filter_map(Result::ok) {
        let symbol_path = entry.path();
        if !symbol_path.is_dir() {
            continue;
        }
        let Some(symbol) = symbol_path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        let Ok(ledger) = load_artifact_ledger(state_dir, symbol) else {
            continue;
        };
        let Some(latest_entry) = ledger
            .iter()
            .rev()
            .find(|entry| entry.artifact_kind == "auto_quant_handoff_candidate")
        else {
            continue;
        };
        if Path::new(&latest_entry.path).exists() {
            if let Ok(content) = std::fs::read_to_string(&latest_entry.path) {
                if let Ok(payload) = serde_json::from_str(&content) {
                    latest_payloads.push(payload);
                    continue;
                }
            }
        }
        let Some(filename) = Path::new(&latest_entry.path)
            .file_name()
            .and_then(|value| value.to_str())
        else {
            continue;
        };
        if let Ok(payload) =
            load_state::<AutoQuantResearchHandoffPayload, _>(state_dir, symbol, filename)
        {
            latest_payloads.push(payload);
        }
    }
    latest_payloads
}

pub fn auto_quant_readiness_from_status_and_data(
    dependency_status: &AutoQuantDependencyStatus,
    state_dir: &str,
    workspace: AutoQuantWorkspaceConfig,
    data_ready: bool,
) -> AutoQuantReadinessSurface {
    let active_strategy_count = auto_quant_active_strategy_count(&workspace);
    let run_command = auto_quant_run_command(&workspace);
    let (status, command, blocked_reason) = if dependency_status.bootstrap_needed {
        (
            "missing_dependency",
            format!("ict-engine auto-quant-bootstrap --state-dir {state_dir}"),
            Some("auto_quant_bootstrap_required"),
        )
    } else if !dependency_status.healthy {
        (
            "dependency_unhealthy",
            format!("ict-engine auto-quant-update --state-dir {state_dir}"),
            Some("auto_quant_dependency_unhealthy"),
        )
    } else if dependency_status.update_available {
        (
            "update_available",
            format!("ict-engine auto-quant-update --state-dir {state_dir}"),
            Some("auto_quant_update_available"),
        )
    } else if !data_ready {
        (
            "dependency_ready_data_missing",
            auto_quant_prepare_cli_command(state_dir),
            Some("auto_quant_prepare_required"),
        )
    } else if active_strategy_count == 0 {
        (
            "dependency_ready_seed_required",
            format!(
                "blocked: create 2-3 active non-underscore strategy files under {} before {}",
                workspace.strategies_dir, run_command
            ),
            Some("auto_quant_seed_strategies_required"),
        )
    } else {
        ("dependency_ready_data_ready", run_command.clone(), None)
    };
    let command = command.to_string();
    let mut notes = dependency_status.notes.clone();
    if let Some(profile) = &workspace.profile_name {
        notes.push(format!("auto_quant_profile={profile}"));
    }
    if data_ready && active_strategy_count == 0 {
        notes.push("auto_quant_seed_strategies_required".to_string());
    }
    AutoQuantReadinessSurface {
        status: status.to_string(),
        healthy: dependency_status.healthy && data_ready,
        bootstrap_needed: dependency_status.bootstrap_needed,
        dependency_healthy: dependency_status.healthy,
        data_ready,
        update_available: dependency_status.update_available,
        managed_dir: dependency_status.managed_dir.clone(),
        workspace,
        dependency_status: dependency_status.clone(),
        recommended_next_command_meta: recommended_next_command_meta(&command),
        next_step: workflow_next_step_view(&command, blocked_reason),
        recommended_next_command: command,
        notes,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::handoff::{
        build_factor_research_handoff_payload, BuildFactorResearchHandoffPayloadInput,
    };
    use crate::application::auto_quant::persistence::persist_handoff_payload;
    use crate::application::auto_quant::types::AutoQuantDependencyStatus;

    fn healthy_dependency_status_for(managed_dir: &str) -> AutoQuantDependencyStatus {
        AutoQuantDependencyStatus {
            repo_url: "repo".to_string(),
            managed_dir: managed_dir.to_string(),
            tracked_branch: "master".to_string(),
            pinned_ref: None,
            current_commit: None,
            upstream_commit: None,
            bootstrap_needed: false,
            config_present: true,
            managed_repo_present: true,
            healthy: true,
            update_available: false,
            required_files: Vec::new(),
            notes: Vec::new(),
            adapter_version: "v1".to_string(),
            last_sync: None,
        }
    }

    #[test]
    fn readiness_uses_handoff_adjusted_workspace_for_status_and_run_command() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().join("state");
        let managed_dir = state_dir.join(".deps/auto-quant");
        let default_strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&default_strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('default')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(managed_dir.join("prepare_external.py"), "print('external')").unwrap();
        std::fs::write(managed_dir.join("run_tomac.py"), "print('tomac')").unwrap();
        std::fs::write(
            default_strategies_dir.join("DefaultSeed.py"),
            "class DefaultSeed: pass",
        )
        .unwrap();

        let data_path = temp.path().join("ibkr_m2k_202606_1m_7d.csv");
        std::fs::write(
            &data_path,
            "timestamp,open,high,low,close,volume\n2026-05-19T00:00:00Z,1,2,0.5,1.5,10\n",
        )
        .unwrap();
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "IBKR_M2K1M_TEST",
                data: data_path.to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: state_dir.to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });

        let mut handoff_workspace = payload.workspace.clone();
        apply_handoff_workspace_profile(&payload, &mut handoff_workspace);
        for expected_file in &handoff_workspace.expected_data_files {
            std::fs::write(data_dir.join(expected_file), "ready").unwrap();
        }
        persist_handoff_payload(state_dir.to_str().unwrap(), &payload).unwrap();

        let readiness = auto_quant_readiness_from_status_with_state_dir(
            &healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            state_dir.to_str().unwrap(),
        );

        assert_eq!(
            readiness.workspace.profile_name.as_deref(),
            Some("synthetic_ohlcv")
        );
        assert!(readiness.workspace.run_script.ends_with("run_tomac.py"));
        assert!(readiness
            .workspace
            .strategies_dir
            .ends_with("strategies_external"));
        assert!(readiness.recommended_next_command.contains("run_tomac.py"));
        assert!(!readiness.recommended_next_command.contains(" run.py"));
        assert!(readiness
            .notes
            .iter()
            .any(|note| note == "auto_quant_profile=synthetic_ohlcv"));
    }
}
