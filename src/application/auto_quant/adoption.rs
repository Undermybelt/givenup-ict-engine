use anyhow::{anyhow, Result};
use chrono::Utc;
use serde::Serialize;

use crate::state::{
    append_artifact_ledger_entry, artifact_state_path, load_artifact_ledger, load_state, save_state,
    ArtifactLedgerEntry,
};

use super::handoff::AutoQuantResearchHandoffPayload;
use super::types::AutoQuantAdoptionDecisionArtifact;

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

pub const AUTO_QUANT_ADOPTION_DECISION_REVIEW_RULE_VERSION: &str =
    "auto-quant-adoption-decision-v1";

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

pub fn persist_auto_quant_adoption_decision(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    decision: &str,
    rationale: &str,
    requested_by: &str,
) -> Result<AutoQuantAdoptionDecisionArtifact> {
    let review = build_auto_quant_adoption_review(symbol, state_dir, artifact_id)?;
    let artifact = AutoQuantAdoptionDecisionArtifact {
        artifact_id: format!(
            "auto-quant-adoption-decision:{}:{}",
            symbol,
            Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
        ),
        generated_at: Utc::now(),
        symbol: symbol.to_string(),
        handoff_artifact_id: review.artifact_id.clone(),
        handoff_kind: review.handoff_kind.clone(),
        decision: decision.to_string(),
        rationale: rationale.to_string(),
        requested_by: requested_by.to_string(),
        state_dir: state_dir.to_string(),
    };
    let filename = format!("auto_quant_adoption_decision.{}.json", review.handoff_kind);
    save_state(state_dir, symbol, &filename, &artifact)?;
    append_artifact_ledger_entry(
        state_dir,
        symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", artifact.artifact_id),
            artifact_kind: "auto_quant_adoption_decision".to_string(),
            artifact_id: artifact.artifact_id.clone(),
            version: 1,
            generated_at: artifact.generated_at,
            symbol: artifact.symbol.clone(),
            source_phase: review.handoff_kind,
            source_run_id: Some(review.artifact_id),
            path: artifact_state_path(state_dir, symbol, &filename),
            status: decision.to_string(),
            promote_candidate: decision == "adopt",
            actionable: true,
            decision_hint: "auto-quant-adoption-review".to_string(),
            review_reason: rationale.to_string(),
            review_rule_version: AUTO_QUANT_ADOPTION_DECISION_REVIEW_RULE_VERSION.to_string(),
            top_factor_name: None,
            top_factor_action: Some(decision.to_string()),
            family_scores: std::collections::BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: if decision == "adopt" { 80 } else { 50 },
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    Ok(artifact)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::auto_quant::persistence::persist_handoff_payload;
    use crate::application::auto_quant::types::{
        AutoQuantAdoptionDecisionArtifact, AutoQuantDependencyStatus,
    };
    use crate::application::auto_quant::AutoQuantResearchHandoffPayload;
    use crate::application::auto_quant::AutoQuantWorkspaceConfig;
    use crate::state::ARTIFACT_LEDGER_FILE;

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

    #[test]
    fn persist_adoption_decision_writes_decision_artifact_and_ledger_entry() {
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
            data_ready: true,
            handoff_artifact_path: String::new(),
            suggested_commands: vec!["cmd".to_string()],
            suggested_next_steps: vec!["step".to_string()],
            agent_prompt: "prompt".to_string(),
            notes: vec!["note".to_string()],
        };
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();
        let artifact: AutoQuantAdoptionDecisionArtifact = persist_auto_quant_adoption_decision(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            "adopt",
            "looks good",
            "agent",
        )
        .unwrap();
        assert_eq!(artifact.decision, "adopt");
        let ledger = std::fs::read_to_string(temp.path().join("NQ").join(ARTIFACT_LEDGER_FILE))
            .unwrap();
        assert!(ledger.contains("auto_quant_adoption_decision"));
        assert!(ledger.contains(AUTO_QUANT_ADOPTION_DECISION_REVIEW_RULE_VERSION));
    }
}
