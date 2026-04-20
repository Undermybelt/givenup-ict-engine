use std::collections::BTreeMap;
use std::path::Path;

use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::application::execution::ExecutionPhysicsOverlay;
use crate::domain::execution::{
    classify_execution_gate, ExecutionFeatures, EXECUTION_GATE_OBSERVE, EXECUTION_GATE_READY,
};
use crate::state::{
    append_artifact_ledger_entry, save_state, ArtifactLedgerEntry, RunProvenance,
};
use crate::types::RegimeProbs;

pub const EXECUTION_TREE_TRACE_FILE: &str = "execution_tree_trace.json";

const PREDICTION_STRONG_THRESHOLD: f64 = 0.65;
const PREDICTION_WEAK_THRESHOLD: f64 = 0.35;
const ISING_HERD_BLOCK_THRESHOLD: f64 = 0.70;
const PYTHAGOREAN_OVERSTRETCH_WAIT_THRESHOLD: f64 = 0.70;

pub struct ExecutionTreeInput<'a> {
    pub execution_features: &'a ExecutionFeatures,
    pub physics_overlay: &'a ExecutionPhysicsOverlay,
    pub hmm_posterior: &'a RegimeProbs,
    pub mece_recovery_confidence: Option<f64>,
    pub prediction_vote_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExecutionTreeOutput {
    pub execution_score: f64,
    pub branch: String,
    pub execution_bias: String,
    pub gate_status: String,
    pub branch_probability: f64,
    pub posterior_uncertainty: f64,
    pub split_reason_lineage: Vec<String>,
    pub decision_hint: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExecutionTreeArtifact {
    pub artifact_id: String,
    pub generated_at: DateTime<Utc>,
    pub symbol: String,
    pub output: ExecutionTreeOutput,
    pub provenance: RunProvenance,
}

pub trait ExecutionTreeScorer {
    fn score(&self, input: &ExecutionTreeInput<'_>) -> Result<ExecutionTreeOutput>;
}

pub struct DefaultExecutionTreeScorer;

impl ExecutionTreeScorer for DefaultExecutionTreeScorer {
    fn score(&self, input: &ExecutionTreeInput<'_>) -> Result<ExecutionTreeOutput> {
        let mut lineage: Vec<String> = Vec::new();
        let readiness = input.execution_features.execution_readiness;
        let gate_status = short_gate_status(classify_execution_gate(readiness));
        lineage.push(format!(
            "execution_readiness={:.4} → gate_status={}",
            readiness, gate_status
        ));

        let ising_risk = input
            .physics_overlay
            .ising
            .as_ref()
            .map(|state| state.phase_transition_risk)
            .unwrap_or(0.0);
        let overstretch = input
            .physics_overlay
            .pythagorean
            .as_ref()
            .map(|metrics| metrics.normalized_overstretch)
            .unwrap_or(0.0);

        let (branch, branch_probability) = if gate_status == "blocked" {
            lineage.push(format!(
                "branch=block_crowded (gate_status=blocked, readiness {:.4} < {:.2})",
                readiness, EXECUTION_GATE_OBSERVE
            ));
            (
                "block_crowded".to_string(),
                gate_distance(readiness, EXECUTION_GATE_OBSERVE),
            )
        } else if ising_risk >= ISING_HERD_BLOCK_THRESHOLD {
            lineage.push(format!(
                "branch=block_crowded (ising_phase_transition_risk={:.4} ≥ {:.2})",
                ising_risk, ISING_HERD_BLOCK_THRESHOLD
            ));
            (
                "block_crowded".to_string(),
                proximity_confidence(ising_risk, ISING_HERD_BLOCK_THRESHOLD),
            )
        } else if overstretch >= PYTHAGOREAN_OVERSTRETCH_WAIT_THRESHOLD {
            lineage.push(format!(
                "branch=wait_for_reversion (pythagorean_overstretch={:.4} ≥ {:.2})",
                overstretch, PYTHAGOREAN_OVERSTRETCH_WAIT_THRESHOLD
            ));
            (
                "wait_for_reversion".to_string(),
                proximity_confidence(overstretch, PYTHAGOREAN_OVERSTRETCH_WAIT_THRESHOLD),
            )
        } else {
            lineage.push(format!(
                "branch=fill_viable (gate_status={}, ising_risk={:.4}<{:.2}, overstretch={:.4}<{:.2})",
                gate_status, ising_risk, ISING_HERD_BLOCK_THRESHOLD, overstretch, PYTHAGOREAN_OVERSTRETCH_WAIT_THRESHOLD
            ));
            (
                "fill_viable".to_string(),
                gate_distance(readiness, EXECUTION_GATE_READY),
            )
        };

        let prediction_strength = classify_prediction_strength(input.prediction_vote_score);
        let execution_strength = classify_execution_strength(readiness);
        let (execution_bias, decision_hint) =
            execution_first_decision(prediction_strength, execution_strength);
        lineage.push(format!(
            "prediction_vote_score={:.4} ({}) × execution_readiness={:.4} ({}) → bias={}, hint={}",
            input.prediction_vote_score,
            prediction_strength,
            readiness,
            execution_strength,
            execution_bias,
            decision_hint
        ));

        if let Some(confidence) = input.mece_recovery_confidence {
            lineage.push(format!("mece_recovery_confidence={:.4}", confidence));
        }
        lineage.push(format!(
            "hmm_posterior=(acc={:.3}, manip={:.3}, dist={:.3})",
            input.hmm_posterior.accumulation,
            input.hmm_posterior.manipulation_expansion,
            input.hmm_posterior.distribution
        ));

        Ok(ExecutionTreeOutput {
            execution_score: input.execution_features.execution_score,
            branch,
            execution_bias: execution_bias.to_string(),
            gate_status: gate_status.to_string(),
            branch_probability,
            posterior_uncertainty: (1.0 - branch_probability).clamp(0.0, 1.0),
            split_reason_lineage: lineage,
            decision_hint: decision_hint.to_string(),
        })
    }
}

fn short_gate_status(raw: &str) -> &'static str {
    match raw {
        "execution_ready" => "ready",
        "execution_observe_only" => "observe",
        _ => "blocked",
    }
}

fn gate_distance(value: f64, threshold: f64) -> f64 {
    let span = (1.0 - threshold).max(f64::EPSILON);
    ((value - threshold) / span).clamp(0.0, 1.0)
}

fn proximity_confidence(value: f64, threshold: f64) -> f64 {
    let span = (1.0 - threshold).max(f64::EPSILON);
    ((value - threshold) / span).clamp(0.0, 1.0)
}

fn classify_prediction_strength(score: f64) -> &'static str {
    if score >= PREDICTION_STRONG_THRESHOLD {
        "strong"
    } else if score >= PREDICTION_WEAK_THRESHOLD {
        "medium"
    } else {
        "weak"
    }
}

fn classify_execution_strength(readiness: f64) -> &'static str {
    if readiness >= EXECUTION_GATE_READY {
        "strong"
    } else if readiness >= EXECUTION_GATE_OBSERVE {
        "medium"
    } else {
        "weak"
    }
}

/// Execution-first hard gate: regardless of prediction strength, weak
/// execution always blocks; medium/strong execution can stay actionable even
/// with weak prediction. Returns `(bias, decision_hint)`.
pub fn execution_first_decision(
    prediction_strength: &str,
    execution_strength: &str,
) -> (&'static str, &'static str) {
    match (prediction_strength, execution_strength) {
        (_, "weak") => ("skip", "execution_blocked_regardless_of_prediction"),
        ("strong", "strong") => ("aggressive", "execution_first_fill"),
        ("strong", "medium") => ("passive", "execution_observe_with_strong_prediction"),
        ("medium", "strong") => ("aggressive", "execution_first_fill_with_medium_prediction"),
        ("medium", "medium") => ("passive", "execution_observe_with_medium_prediction"),
        ("weak", "strong") => ("aggressive", "execution_first_fill_despite_weak_prediction"),
        ("weak", "medium") => ("passive", "execution_observe_despite_weak_prediction"),
        _ => ("skip", "unhandled_combination"),
    }
}

pub fn build_execution_tree_artifact(
    symbol: &str,
    output: ExecutionTreeOutput,
    provenance: RunProvenance,
) -> ExecutionTreeArtifact {
    let generated_at = Utc::now();
    ExecutionTreeArtifact {
        artifact_id: format!(
            "execution-tree-{}-{}",
            symbol,
            generated_at.timestamp_millis()
        ),
        generated_at,
        symbol: symbol.to_string(),
        output,
        provenance,
    }
}

pub fn persist_execution_tree_artifact<P: AsRef<Path>>(
    dir: P,
    artifact: &ExecutionTreeArtifact,
    source_phase: &str,
    source_run_id: Option<String>,
) -> Result<()> {
    save_state(
        &dir,
        &artifact.symbol,
        EXECUTION_TREE_TRACE_FILE,
        artifact,
    )?;
    let promote = artifact.output.branch == "fill_viable"
        && artifact.output.gate_status == "ready";
    let actionable = artifact.output.gate_status != "blocked"
        && artifact.output.branch != "block_crowded";
    let quality_score = (artifact.output.branch_probability * 100.0).round() as i32;
    append_artifact_ledger_entry(
        dir,
        &artifact.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", artifact.artifact_id),
            artifact_kind: "execution_tree_artifact".to_string(),
            artifact_id: artifact.artifact_id.clone(),
            version: 1,
            generated_at: artifact.generated_at,
            symbol: artifact.symbol.clone(),
            source_phase: source_phase.to_string(),
            source_run_id,
            path: Path::new("state")
                .join(&artifact.symbol)
                .join(EXECUTION_TREE_TRACE_FILE)
                .to_string_lossy()
                .to_string(),
            status: artifact.output.gate_status.clone(),
            promote_candidate: promote,
            actionable,
            decision_hint: artifact.output.decision_hint.clone(),
            review_reason: format!(
                "branch={};bias={};branch_prob={:.4};uncertainty={:.4}",
                artifact.output.branch,
                artifact.output.execution_bias,
                artifact.output.branch_probability,
                artifact.output.posterior_uncertainty
            ),
            review_rule_version: "execution-tree-artifact-v1".to_string(),
            top_factor_name: None,
            top_factor_action: None,
            family_scores: BTreeMap::from([
                (
                    "execution_score".to_string(),
                    artifact.output.execution_score,
                ),
                (
                    "branch_probability".to_string(),
                    artifact.output.branch_probability,
                ),
            ]),
            supersedes_artifact_id: None,
            quality_score,
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::execution::ExecutionPhysicsOverlay;
    use crate::domain::execution::ExecutionFeatures;
    use crate::domain::regime::IsingState;
    use crate::ict::PythagoreanExtensionMetrics;
    use crate::types::RegimeProbs;
    use std::fs;
    use tempfile::TempDir;

    fn baseline_features(readiness: f64) -> ExecutionFeatures {
        ExecutionFeatures {
            execution_readiness: readiness,
            execution_score: readiness,
            evidence_quality: 0.6,
            ..Default::default()
        }
    }

    fn flat_overlay() -> ExecutionPhysicsOverlay {
        ExecutionPhysicsOverlay {
            ou: None,
            ising: Some(IsingState {
                magnetization: 0.0,
                coupling_strength: 0.2,
                phase_transition_risk: 0.2,
                herding_bias: 0.1,
            }),
            pythagorean: Some(PythagoreanExtensionMetrics {
                trendline_distance: 0.0,
                orthogonal_extension: 0.0,
                normalized_overstretch: 0.1,
            }),
        }
    }

    fn neutral_posterior() -> RegimeProbs {
        RegimeProbs {
            accumulation: 0.34,
            manipulation_expansion: 0.33,
            distribution: 0.33,
        }
    }

    #[test]
    fn ready_low_overlay_yields_fill_viable() {
        let features = baseline_features(0.85);
        let overlay = flat_overlay();
        let posterior = neutral_posterior();
        let input = ExecutionTreeInput {
            execution_features: &features,
            physics_overlay: &overlay,
            hmm_posterior: &posterior,
            mece_recovery_confidence: Some(0.97),
            prediction_vote_score: 0.7,
        };
        let output = DefaultExecutionTreeScorer.score(&input).unwrap();
        assert_eq!(output.branch, "fill_viable");
        assert_eq!(output.gate_status, "ready");
        assert!(output.branch_probability > 0.0);
        assert!(!output.split_reason_lineage.is_empty());
    }

    #[test]
    fn high_ising_risk_blocks_even_when_ready() {
        let features = baseline_features(0.85);
        let mut overlay = flat_overlay();
        if let Some(ising) = overlay.ising.as_mut() {
            ising.phase_transition_risk = 0.9;
        }
        let posterior = neutral_posterior();
        let input = ExecutionTreeInput {
            execution_features: &features,
            physics_overlay: &overlay,
            hmm_posterior: &posterior,
            mece_recovery_confidence: None,
            prediction_vote_score: 0.7,
        };
        let output = DefaultExecutionTreeScorer.score(&input).unwrap();
        assert_eq!(output.branch, "block_crowded");
    }

    #[test]
    fn high_overstretch_routes_to_wait_for_reversion() {
        let features = baseline_features(0.85);
        let mut overlay = flat_overlay();
        if let Some(p) = overlay.pythagorean.as_mut() {
            p.normalized_overstretch = 0.85;
        }
        let posterior = neutral_posterior();
        let input = ExecutionTreeInput {
            execution_features: &features,
            physics_overlay: &overlay,
            hmm_posterior: &posterior,
            mece_recovery_confidence: None,
            prediction_vote_score: 0.7,
        };
        let output = DefaultExecutionTreeScorer.score(&input).unwrap();
        assert_eq!(output.branch, "wait_for_reversion");
    }

    #[test]
    fn weak_execution_blocks_even_with_strong_prediction() {
        let features = baseline_features(0.30);
        let overlay = flat_overlay();
        let posterior = neutral_posterior();
        let input = ExecutionTreeInput {
            execution_features: &features,
            physics_overlay: &overlay,
            hmm_posterior: &posterior,
            mece_recovery_confidence: Some(0.97),
            prediction_vote_score: 0.95,
        };
        let output = DefaultExecutionTreeScorer.score(&input).unwrap();
        assert_eq!(output.gate_status, "blocked");
        assert_eq!(output.execution_bias, "skip");
        assert_eq!(output.decision_hint, "execution_blocked_regardless_of_prediction");
    }

    #[test]
    fn persists_artifact_and_ledger_entry() {
        let features = baseline_features(0.80);
        let overlay = flat_overlay();
        let posterior = neutral_posterior();
        let output = DefaultExecutionTreeScorer
            .score(&ExecutionTreeInput {
                execution_features: &features,
                physics_overlay: &overlay,
                hmm_posterior: &posterior,
                mece_recovery_confidence: Some(0.97),
                prediction_vote_score: 0.7,
            })
            .unwrap();
        let artifact = build_execution_tree_artifact("NQ", output, RunProvenance::default());
        let dir = TempDir::new().unwrap();
        persist_execution_tree_artifact(dir.path(), &artifact, "analyze", None).unwrap();

        let trace_path = dir.path().join("NQ").join(EXECUTION_TREE_TRACE_FILE);
        assert!(trace_path.exists());
        let raw = fs::read_to_string(&trace_path).unwrap();
        assert!(raw.contains("\"branch\""));
        assert!(raw.contains("\"split_reason_lineage\""));

        let ledger_path = dir
            .path()
            .join("NQ")
            .join(crate::state::ARTIFACT_LEDGER_FILE);
        let ledger = fs::read_to_string(&ledger_path).unwrap();
        assert!(ledger.contains("\"execution_tree_artifact\""));
        assert!(ledger.contains("\"execution-tree-artifact-v1\""));
    }
}
