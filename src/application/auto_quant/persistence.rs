use anyhow::Result;
use chrono::Utc;

use crate::state::{
    append_artifact_ledger_entry, artifact_state_path, save_state, ArtifactLedgerEntry,
};

use super::handoff::AutoQuantResearchHandoffPayload;

pub const AUTO_QUANT_HANDOFF_REVIEW_RULE_VERSION: &str = "auto-quant-handoff-v1";

pub fn persist_handoff_payload(
    state_dir: &str,
    payload: &AutoQuantResearchHandoffPayload,
) -> Result<String> {
    let filename = format!("auto_quant_handoff.{}.json", payload.handoff_kind);
    save_state(state_dir, &payload.symbol, &filename, payload)?;
    let path = artifact_state_path(state_dir, &payload.symbol, &filename);
    append_artifact_ledger_entry(
        state_dir,
        &payload.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", payload.artifact_id),
            artifact_kind: "auto_quant_handoff_candidate".to_string(),
            artifact_id: payload.artifact_id.clone(),
            version: 1,
            generated_at: Utc::now(),
            symbol: payload.symbol.clone(),
            source_phase: payload.handoff_kind.clone(),
            source_run_id: payload.session_id.clone(),
            path: path.clone(),
            status: if payload.data_ready {
                "ready_for_external_run".to_string()
            } else {
                "prepare_required".to_string()
            },
            promote_candidate: false,
            actionable: true,
            decision_hint: payload.backend.clone(),
            review_reason: payload.suggested_next_steps.join(" | "),
            review_rule_version: AUTO_QUANT_HANDOFF_REVIEW_RULE_VERSION.to_string(),
            top_factor_name: None,
            top_factor_action: Some("review".to_string()),
            family_scores: std::collections::BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: if payload.data_ready { 70 } else { 30 },
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    Ok(path)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::types::AutoQuantDependencyStatus;
    use crate::state::ARTIFACT_LEDGER_FILE;
    use std::path::Path;

    #[test]
    fn persist_handoff_writes_artifact_and_ledger_entry() {
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
            workspace: crate::application::auto_quant::handoff::AutoQuantWorkspaceConfig {
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
            suggested_commands: vec!["cmd".to_string()],
            suggested_next_steps: vec!["step".to_string()],
            agent_prompt: "prompt".to_string(),
            notes: vec!["note".to_string()],
        };

        let path = persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();
        assert!(Path::new(&path).exists());
        let ledger = std::fs::read_to_string(temp.path().join("NQ").join(ARTIFACT_LEDGER_FILE))
            .unwrap();
        assert!(ledger.contains("auto_quant_handoff_candidate"));
        assert!(ledger.contains(AUTO_QUANT_HANDOFF_REVIEW_RULE_VERSION));
    }
}
