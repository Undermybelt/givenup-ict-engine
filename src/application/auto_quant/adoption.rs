use anyhow::{anyhow, Result};
use serde::Serialize;

use crate::state::{load_artifact_ledger, load_state, ArtifactLedgerEntry};

use super::handoff::AutoQuantResearchHandoffPayload;

#[derive(Debug, Clone, Serialize)]
pub struct AutoQuantAdoptionReview {
    pub symbol: String,
    pub state_dir: String,
    pub artifact_id: String,
    pub handoff_kind: String,
    pub backend: String,
    pub data_ready: bool,
    pub dependency_healthy: bool,
    pub workspace_repo_root: String,
    pub suggested_commands: Vec<String>,
    pub suggested_next_steps: Vec<String>,
    pub review_status: String,
    pub review_summary: String,
    pub notes: Vec<String>,
}

fn load_handoff_payload(
    state_dir: &str,
    symbol: &str,
    entry: &ArtifactLedgerEntry,
) -> Result<AutoQuantResearchHandoffPayload> {
    let filename = std::path::Path::new(&entry.path)
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| anyhow!("invalid handoff artifact path '{}'", entry.path))?;
    load_state(state_dir, symbol, filename)
}

pub fn build_auto_quant_adoption_review(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
) -> Result<AutoQuantAdoptionReview> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    let entry = if let Some(artifact_id) = artifact_id {
        ledger
            .iter()
            .rev()
            .find(|entry| entry.artifact_id == artifact_id)
            .ok_or_else(|| anyhow!("no auto-quant handoff artifact '{}' for '{}'", artifact_id, symbol))?
    } else {
        ledger
            .iter()
            .rev()
            .find(|entry| entry.artifact_kind == "auto_quant_handoff_candidate")
            .ok_or_else(|| anyhow!("no auto-quant handoff artifact found for '{}'", symbol))?
    };
    let payload = load_handoff_payload(state_dir, symbol, entry)?;
    let (review_status, review_summary) = if !payload.dependency_status.healthy {
        (
            "blocked_dependency_unhealthy".to_string(),
            "managed Auto-Quant checkout is unhealthy; repair dependency before adoption review"
                .to_string(),
        )
    } else if !payload.data_ready {
        (
            "prepare_required".to_string(),
            "Auto-Quant workspace is healthy but research data is not ready yet".to_string(),
        )
    } else {
        (
            "ready_for_external_execution".to_string(),
            "handoff is ready for Auto-Quant execution and candidate export".to_string(),
        )
    };
    Ok(AutoQuantAdoptionReview {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        artifact_id: payload.artifact_id,
        handoff_kind: payload.handoff_kind,
        backend: payload.backend,
        data_ready: payload.data_ready,
        dependency_healthy: payload.dependency_status.healthy,
        workspace_repo_root: payload.workspace.repo_root,
        suggested_commands: payload.suggested_commands,
        suggested_next_steps: payload.suggested_next_steps,
        review_status,
        review_summary,
        notes: payload.notes,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::persistence::persist_handoff_payload;
    use crate::application::auto_quant::types::AutoQuantDependencyStatus;
    use crate::application::auto_quant::AutoQuantResearchHandoffPayload;
    use crate::application::auto_quant::AutoQuantWorkspaceConfig;

    #[test]
    fn review_marks_prepare_required_when_data_is_missing() {
        let temp = tempfile::tempdir().unwrap();
        let payload = AutoQuantResearchHandoffPayload {
            artifact_id: "auto-quant-handoff:test".to_string(),
            handoff_kind: "factor_research".to_string(),
            symbol: "NQ".to_string(),
            state_dir: temp.path().to_string_lossy().to_string(),
            objective: "expansion_manipulation".to_string(),
            backend: "auto-quant".to_string(),
            data_path: "demo.json".to_string(),
            paired_data_path: None,
            mutation_spec_path: None,
            iterations: None,
            session_id: None,
            dependency_status: AutoQuantDependencyStatus {
                repo_url: "repo".to_string(),
                managed_dir: "dir".to_string(),
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
            },
            workspace: AutoQuantWorkspaceConfig {
                repo_root: "repo".to_string(),
                program_md: "program".to_string(),
                prepare_script: "prepare".to_string(),
                run_script: "run".to_string(),
                config_json: "config".to_string(),
                strategies_dir: "strategies".to_string(),
                data_dir: "data".to_string(),
            },
            data_ready: false,
            handoff_artifact_path: String::new(),
            suggested_commands: vec!["prepare".to_string()],
            suggested_next_steps: vec!["step".to_string()],
            agent_prompt: "prompt".to_string(),
            notes: vec!["note".to_string()],
        };
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();
        let review =
            build_auto_quant_adoption_review("NQ", temp.path().to_str().unwrap(), None).unwrap();
        assert_eq!(review.review_status, "prepare_required");
        assert!(review.review_summary.contains("data is not ready"));
    }
}
