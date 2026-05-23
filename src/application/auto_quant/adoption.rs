use anyhow::{anyhow, Result};
use chrono::Utc;
use serde::Serialize;
use serde_json::Value;
use std::path::Path;

use crate::state::{
    append_artifact_ledger_entry, artifact_state_path, load_artifact_ledger, load_state,
    save_state, ArtifactLedgerEntry, RecommendedNextCommandMeta,
};

use super::handoff::{
    auto_quant_active_strategy_count, auto_quant_handoff_data_ready, base_suggested_commands,
    suggested_next_steps_for_handoff, AutoQuantResearchHandoffPayload,
};
use super::readiness::auto_quant_readiness_from_status_and_data;
use super::types::AutoQuantAdoptionDecisionArtifact;
use super::workspace_profile::apply_handoff_workspace_profile;

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
    pub recommended_next_command: String,
    pub recommended_next_command_meta: RecommendedNextCommandMeta,
    pub next_step: Value,
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
    if Path::new(&entry.path).exists() {
        let content = std::fs::read_to_string(&entry.path)?;
        return Ok(serde_json::from_str(&content)?);
    }
    let filename = std::path::Path::new(&entry.path)
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| anyhow!("invalid handoff artifact path '{}'", entry.path))?;
    load_state(state_dir, symbol, filename)
}

fn find_handoff_entry(
    state_dir: &str,
    symbol: &str,
    artifact_id: Option<&str>,
) -> Result<ArtifactLedgerEntry> {
    let symbol_ledger = load_artifact_ledger(state_dir, symbol)?;
    if let Some(artifact_id) = artifact_id {
        if let Some(entry) = symbol_ledger
            .iter()
            .rev()
            .find(|entry| entry.artifact_id == artifact_id)
        {
            return Ok(entry.clone());
        }
    } else if let Some(entry) = symbol_ledger
        .iter()
        .rev()
        .find(|entry| entry.artifact_kind == "auto_quant_handoff_candidate")
    {
        return Ok(entry.clone());
    }

    let mut fallback_entry = None;
    let state_children = match std::fs::read_dir(state_dir) {
        Ok(children) => children,
        Err(err) if err.kind() == std::io::ErrorKind::NotFound => {
            if let Some(artifact_id) = artifact_id {
                return Err(anyhow!(
                    "auto_quant_adoption_handoff_missing: symbol={} artifact_id={} expected=auto_quant_handoff_candidate artifact before adoption decision recovery=run `ict-engine auto-quant-adoption-review --symbol {} --state-dir {}` after creating an Auto-Quant handoff, then rerun adoption-decision with --artifact-id <handoff-artifact-id>",
                    symbol,
                    artifact_id,
                    symbol,
                    state_dir
                ));
            }
            return Err(anyhow!(
                "auto_quant_adoption_handoff_missing: symbol={} expected=auto_quant_handoff_candidate artifact before adoption decision recovery=run `ict-engine auto-quant-adoption-review --symbol {} --state-dir {}` after creating an Auto-Quant handoff, then rerun adoption-decision",
                symbol,
                symbol,
                state_dir
            ));
        }
        Err(err) => return Err(err.into()),
    };
    for state_child in state_children.filter_map(std::result::Result::ok) {
        let symbol_path = state_child.path();
        if !symbol_path.is_dir() {
            continue;
        }
        let Some(child_symbol) = symbol_path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        if child_symbol == symbol {
            continue;
        }
        let Ok(child_ledger) = load_artifact_ledger(state_dir, child_symbol) else {
            continue;
        };
        let child_entry = if let Some(artifact_id) = artifact_id {
            child_ledger
                .iter()
                .rev()
                .find(|entry| entry.artifact_id == artifact_id)
        } else {
            child_ledger
                .iter()
                .rev()
                .find(|entry| entry.artifact_kind == "auto_quant_handoff_candidate")
        };
        let Some(entry) = child_entry else {
            continue;
        };
        if artifact_id.is_some() {
            return Ok(entry.clone());
        }
        if let Ok(payload) = load_handoff_payload(state_dir, child_symbol, entry) {
            if payload.symbol == symbol || payload.symbol.starts_with(symbol) {
                fallback_entry = Some(entry.clone());
            }
        }
    }
    if let Some(entry) = fallback_entry {
        return Ok(entry);
    }

    if let Some(artifact_id) = artifact_id {
        Err(anyhow!(
            "auto_quant_adoption_handoff_missing: symbol={} artifact_id={} expected=auto_quant_handoff_candidate artifact before adoption decision recovery=run `ict-engine auto-quant-adoption-review --symbol {} --state-dir {}` after creating an Auto-Quant handoff, then rerun adoption-decision with --artifact-id <handoff-artifact-id>",
            symbol,
            artifact_id,
            symbol,
            state_dir
        ))
    } else {
        Err(anyhow!(
            "auto_quant_adoption_handoff_missing: symbol={} expected=auto_quant_handoff_candidate artifact before adoption decision recovery=run `ict-engine auto-quant-adoption-review --symbol {} --state-dir {}` after creating an Auto-Quant handoff, then rerun adoption-decision",
            symbol,
            symbol,
            state_dir
        ))
    }
}

pub fn build_auto_quant_adoption_review(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
) -> Result<AutoQuantAdoptionReview> {
    let entry = find_handoff_entry(state_dir, symbol, artifact_id)?;
    let payload = load_handoff_payload(state_dir, symbol, &entry)?;
    let mut workspace = payload.workspace.clone();
    apply_handoff_workspace_profile(&payload, &mut workspace);
    let data_ready = auto_quant_handoff_data_ready(
        &workspace,
        &payload.data_path,
        payload.paired_data_path.as_deref(),
    );
    let active_strategy_count = auto_quant_active_strategy_count(&workspace);
    let readiness = auto_quant_readiness_from_status_and_data(
        &payload.dependency_status,
        &payload.state_dir,
        workspace.clone(),
        data_ready,
    );
    let (review_status, review_summary) = if !readiness.dependency_healthy {
        (
            "blocked_dependency_unhealthy".to_string(),
            "managed Auto-Quant checkout is unhealthy; repair dependency before adoption review"
                .to_string(),
        )
    } else if !readiness.data_ready {
        (
            "prepare_required".to_string(),
            "Auto-Quant workspace is healthy but research data is not ready yet".to_string(),
        )
    } else if active_strategy_count == 0 {
        (
            "seed_required".to_string(),
            "Auto-Quant workspace is healthy and data-ready but has no active strategy files; seed strategies before external execution"
                .to_string(),
        )
    } else {
        (
            "ready_for_external_execution".to_string(),
            "handoff is ready for Auto-Quant execution and candidate export".to_string(),
        )
    };
    let suggested_commands = base_suggested_commands(
        &workspace,
        &payload.state_dir,
        readiness.data_ready,
        active_strategy_count,
        payload.auxiliary_evidence_path.as_deref(),
        payload.strategy_material_root.as_deref(),
        &payload.external_strategy_materials,
    );
    let suggested_next_steps = suggested_next_steps_for_handoff(
        &payload.handoff_kind,
        readiness.data_ready,
        active_strategy_count,
        !payload.external_strategy_materials.is_empty(),
    );
    Ok(AutoQuantAdoptionReview {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        artifact_id: payload.artifact_id,
        handoff_kind: payload.handoff_kind,
        backend: payload.backend,
        data_ready: readiness.data_ready,
        dependency_healthy: readiness.dependency_healthy,
        workspace_repo_root: payload.workspace.repo_root,
        suggested_commands,
        suggested_next_steps,
        recommended_next_command_meta: readiness.recommended_next_command_meta,
        next_step: readiness.next_step,
        recommended_next_command: readiness.recommended_next_command,
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
    use crate::application::auto_quant::handoff::{
        build_factor_research_handoff_payload, BuildFactorResearchHandoffPayloadInput,
    };
    use crate::application::auto_quant::persistence::persist_handoff_payload;
    use crate::application::auto_quant::types::{
        AutoQuantAdoptionDecisionArtifact, AutoQuantDependencyStatus,
    };
    use crate::state::ARTIFACT_LEDGER_FILE;

    #[test]
    fn review_marks_prepare_required_when_data_is_missing() {
        let temp = tempfile::tempdir().unwrap();
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status(),
            });
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();
        let review =
            build_auto_quant_adoption_review("NQ", temp.path().to_str().unwrap(), None).unwrap();
        assert_eq!(review.review_status, "prepare_required");
        assert!(review.review_summary.contains("data is not ready"));
    }

    #[test]
    fn review_uses_current_data_readiness_after_handoff_is_prepared() {
        let temp = tempfile::tempdir().unwrap();
        let managed = temp.path().join("auto-quant");
        let data_path = temp.path().join("demo.json");
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: data_path.to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed.to_str().unwrap()),
            });
        assert!(!payload.data_ready);
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();

        std::fs::write(&data_path, "[]").unwrap();
        std::fs::create_dir_all(&payload.workspace.data_dir).unwrap();
        for index in 0..15 {
            std::fs::write(
                std::path::Path::new(&payload.workspace.data_dir)
                    .join(format!("demo-{index}.feather")),
                "prepared",
            )
            .unwrap();
        }

        std::fs::create_dir_all(&payload.workspace.strategies_dir).unwrap();
        std::fs::write(
            std::path::Path::new(&payload.workspace.strategies_dir).join("SeedAlpha.py"),
            "class SeedAlpha: pass",
        )
        .unwrap();

        let review =
            build_auto_quant_adoption_review("NQ", temp.path().to_str().unwrap(), None).unwrap();
        assert_eq!(review.review_status, "ready_for_external_execution");
        assert!(review.data_ready);
        assert!(!review
            .suggested_commands
            .iter()
            .any(|command| command.contains("prepare.py")));
        assert_eq!(review.next_step["blocked_reason"], serde_json::Value::Null);
    }

    #[test]
    fn review_accepts_legacy_handoff_without_readiness_field() {
        let temp = tempfile::tempdir().unwrap();
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status(),
            });
        let mut value = serde_json::to_value(&payload).unwrap();
        value.as_object_mut().unwrap().remove("readiness");
        let path = persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();
        std::fs::write(&path, serde_json::to_string_pretty(&value).unwrap()).unwrap();

        let review =
            build_auto_quant_adoption_review("NQ", temp.path().to_str().unwrap(), None).unwrap();
        assert_eq!(review.review_status, "prepare_required");
    }

    #[test]
    fn review_finds_explicit_handoff_artifact_under_exact_root_symbol() {
        let temp = tempfile::tempdir().unwrap();
        let exact_root_symbol =
            "IBKR_M2K1M_LIQUIDITY_SWEEP_REJECT_SHORT_RVOL_PDA_GUARD_7D_GATE1_V1";
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: exact_root_symbol,
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status(),
            });
        let artifact_id = payload.artifact_id.clone();
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();

        let review = build_auto_quant_adoption_review(
            "M2K",
            temp.path().to_str().unwrap(),
            Some(&artifact_id),
        )
        .unwrap();

        assert_eq!(review.artifact_id, artifact_id);
        assert_eq!(review.symbol, "M2K");
    }

    #[test]
    fn persist_adoption_decision_writes_decision_artifact_and_ledger_entry() {
        let temp = tempfile::tempdir().unwrap();
        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: "demo.json",
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status(),
            });
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
        let ledger =
            std::fs::read_to_string(temp.path().join("NQ").join(ARTIFACT_LEDGER_FILE)).unwrap();
        assert!(ledger.contains("auto_quant_adoption_decision"));
        assert!(ledger.contains(AUTO_QUANT_ADOPTION_DECISION_REVIEW_RULE_VERSION));
    }

    #[test]
    fn decision_missing_handoff_error_names_prerequisite_and_recovery() {
        let temp = tempfile::tempdir().unwrap();

        let err = persist_auto_quant_adoption_decision(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            "adopt",
            "probe",
            "test",
        )
        .unwrap_err();
        let message = format!("{err:#}");

        assert!(
            message.contains("auto_quant_adoption_handoff_missing"),
            "{message}"
        );
        assert!(message.contains("symbol=NQ"), "{message}");
        assert!(message.contains("auto-quant-adoption-review"), "{message}");
        assert!(message.contains("recovery="), "{message}");
    }

    #[test]
    fn decision_missing_handoff_error_handles_missing_state_root() {
        let temp = tempfile::tempdir().unwrap();
        let missing_state_dir = temp.path().join("missing-state-root");

        let err = persist_auto_quant_adoption_decision(
            "NQ",
            missing_state_dir.to_str().unwrap(),
            None,
            "adopt",
            "probe",
            "test",
        )
        .unwrap_err();
        let message = format!("{err:#}");

        assert!(
            message.contains("auto_quant_adoption_handoff_missing"),
            "{message}"
        );
        assert!(message.contains("symbol=NQ"), "{message}");
        assert!(!message.contains("os error 2"), "{message}");
        assert!(message.contains("recovery="), "{message}");
    }

    #[test]
    fn adoption_review_requires_requested_data_path_even_when_workspace_cache_exists() {
        let temp = tempfile::tempdir().unwrap();
        let managed_dir = temp.path().join("managed-auto-quant");
        let strategies_dir = managed_dir.join("user_data/strategies");
        let data_dir = managed_dir.join("user_data/data");
        std::fs::create_dir_all(&strategies_dir).unwrap();
        std::fs::create_dir_all(&data_dir).unwrap();
        std::fs::write(managed_dir.join("program.md"), "program").unwrap();
        std::fs::write(managed_dir.join("prepare.py"), "print('prepare')").unwrap();
        std::fs::write(managed_dir.join("run.py"), "print('run')").unwrap();
        std::fs::write(
            strategies_dir.join("_template.py.example"),
            "class Template: pass",
        )
        .unwrap();
        std::fs::write(strategies_dir.join("SeedAlpha.py"), "class SeedAlpha: pass").unwrap();
        for index in 0..15 {
            std::fs::write(data_dir.join(format!("prepared-{index}.feather")), "ready").unwrap();
        }

        let payload =
            build_factor_research_handoff_payload(BuildFactorResearchHandoffPayloadInput {
                symbol: "NQ",
                data: temp.path().join("missing-primary.json").to_str().unwrap(),
                objective: "expansion_manipulation",
                provider_profile_selector: None,
                paired_data: None,
                auxiliary_evidence_path: None,
                mutation_spec_path: None,
                strategy_material_root: None,
                state_dir: temp.path().to_str().unwrap(),
                dependency_status: healthy_dependency_status_for(managed_dir.to_str().unwrap()),
            });
        persist_handoff_payload(temp.path().to_str().unwrap(), &payload).unwrap();

        let review =
            build_auto_quant_adoption_review("NQ", temp.path().to_str().unwrap(), None).unwrap();
        assert_eq!(review.review_status, "prepare_required");
        assert!(!review.data_ready);
    }

    fn healthy_dependency_status() -> AutoQuantDependencyStatus {
        healthy_dependency_status_for("dir")
    }

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
}
