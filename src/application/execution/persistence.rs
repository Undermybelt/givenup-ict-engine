use std::path::Path;

use anyhow::Result;

use crate::domain::execution::{
    classify_execution_gate, ExecutionArtifact, EXECUTION_GATE_OBSERVE, EXECUTION_GATE_READY,
};
use crate::state::{append_artifact_ledger_entry, save_state, ArtifactLedgerEntry};

pub const EXECUTION_ARTIFACT_FILE: &str = "execution_artifact.json";

pub fn persist_execution_artifact<P: AsRef<Path>>(
    dir: P,
    artifact: &ExecutionArtifact,
    source_phase: &str,
    source_run_id: Option<String>,
    decision_hint: &str,
) -> Result<()> {
    save_state(&dir, &artifact.symbol, EXECUTION_ARTIFACT_FILE, artifact)?;
    append_artifact_ledger_entry(
        dir,
        &artifact.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", artifact.artifact_id),
            artifact_kind: "execution_artifact".to_string(),
            artifact_id: artifact.artifact_id.clone(),
            version: 1,
            generated_at: artifact.generated_at,
            symbol: artifact.symbol.clone(),
            source_phase: source_phase.to_string(),
            source_run_id,
            path: std::path::Path::new("state")
                .join(&artifact.symbol)
                .join(EXECUTION_ARTIFACT_FILE)
                .to_string_lossy()
                .to_string(),
            status: classify_execution_gate(artifact.features.execution_readiness).to_string(),
            promote_candidate: artifact.features.execution_readiness >= EXECUTION_GATE_READY,
            actionable: artifact.features.execution_readiness >= EXECUTION_GATE_OBSERVE,
            decision_hint: decision_hint.to_string(),
            review_reason: format!(
                "execution_edge_share={:.3};prediction_edge_share={:.3}",
                artifact.features.execution_edge_share, artifact.features.prediction_edge_share
            ),
            review_rule_version: "execution-artifact-v1".to_string(),
            top_factor_name: None,
            top_factor_action: None,
            family_scores: std::collections::BTreeMap::from([(
                "execution".to_string(),
                artifact.features.execution_score,
            )]),
            supersedes_artifact_id: None,
            quality_score: (artifact.features.execution_readiness * 100.0).round() as i32,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    Ok(())
}
