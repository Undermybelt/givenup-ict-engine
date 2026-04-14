use crate::types::Direction;

use super::{AnalysisArtifact, ExecutionPlanArtifact, QualificationArtifact, StagedArtifacts};
use crate::factor_lab::FactorDiagnostics;
use crate::state::PreBayesEvidenceFilter;

pub fn build_staged_artifacts(
    diagnostics: &FactorDiagnostics,
    decision_hint: &str,
    filter: &PreBayesEvidenceFilter,
    selected_entry_quality: &str,
    direction: Direction,
    risk_reward: f64,
    kelly_fraction: f64,
) -> StagedArtifacts {
    StagedArtifacts {
        analysis: AnalysisArtifact {
            stage: "analysis".to_string(),
            factor_alignment: diagnostics.alignment_label.clone(),
            factor_uncertainty: diagnostics.uncertainty_label.clone(),
            decision_hint: decision_hint.to_string(),
            summary: format!(
                "alignment={} uncertainty={} decision_hint={}",
                diagnostics.alignment_label, diagnostics.uncertainty_label, decision_hint
            ),
        },
        qualification: QualificationArtifact {
            stage: "qualification".to_string(),
            gating_status: filter.gating_status.clone(),
            selected_entry_quality: selected_entry_quality.to_string(),
            evidence_quality_score: filter.evidence_quality_score,
            summary: format!(
                "gate={} selected_entry_quality={} evidence_quality={:.4}",
                filter.gating_status, selected_entry_quality, filter.evidence_quality_score
            ),
        },
        execution_plan: ExecutionPlanArtifact {
            stage: "execution_plan".to_string(),
            plan_status: if matches!(direction, Direction::Neutral) {
                "plan_blocked".to_string()
            } else {
                "plan_ready".to_string()
            },
            selected_direction: format!("{:?}", direction),
            summary: format!(
                "direction={:?} rr={:.4} kelly={:.4}",
                direction, risk_reward, kelly_fraction
            ),
        },
    }
}
