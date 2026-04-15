use serde::Serialize;

use crate::reporting::belief::BeliefReportPacket;
use crate::state::PreBayesPolicyRecord;

#[derive(Debug, Clone, Serialize, Default)]
pub struct BeliefShadowPolicySurface {
    pub policy_version: String,
    pub shadow_summary_line: String,
    pub shadow_available: bool,
    pub pre_bayes_uses_soft_evidence: bool,
    pub evidence_quality_score: f64,
    pub jump_model_active_state: String,
    pub jump_model_transition_risk: f64,
    pub jump_model_disagreement_score: f64,
    pub jump_model_gate_bias: String,
}

pub fn build_belief_shadow_policy_surface(
    packet: &BeliefReportPacket,
    policy_record: Option<&PreBayesPolicyRecord>,
) -> BeliefShadowPolicySurface {
    BeliefShadowPolicySurface {
        policy_version: policy_record
            .map(|record| record.policy.version.clone())
            .unwrap_or_else(|| "policy_version_unavailable".to_string()),
        shadow_summary_line: packet
            .shadow_comparison
            .as_ref()
            .map(|item| item.summary_line.clone())
            .unwrap_or_else(|| "shadow=unavailable".to_string()),
        shadow_available: packet.shadow_comparison.is_some(),
        pre_bayes_uses_soft_evidence: policy_record
            .map(|record| !record.diff_from_previous.changed_fields.is_empty())
            .unwrap_or(false),
        evidence_quality_score: policy_record
            .map(|record| record.diff_from_previous.changed_fields.len() as f64)
            .unwrap_or_default(),
        jump_model_active_state: packet
            .regime_companion
            .jump_model
            .as_ref()
            .map(|item| item.active_state.clone())
            .unwrap_or_else(|| "jump_model_unavailable".to_string()),
        jump_model_transition_risk: packet
            .regime_companion
            .jump_model
            .as_ref()
            .map(|item| item.transition_risk)
            .unwrap_or_default(),
        jump_model_disagreement_score: packet
            .regime_companion
            .disagreement
            .as_ref()
            .map(|item| item.disagreement_score)
            .unwrap_or_default(),
        jump_model_gate_bias: packet
            .regime_companion
            .disagreement
            .as_ref()
            .map(|item| item.gate_bias.clone())
            .unwrap_or_else(|| "jump_gate_unavailable".to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shadow_surface_defaults_without_policy_record() {
        let packet = BeliefReportPacket::default();
        let surface = build_belief_shadow_policy_surface(&packet, None);
        assert_eq!(surface.policy_version, "policy_version_unavailable");
        assert_eq!(surface.shadow_summary_line, "shadow=unavailable");
        assert!(!surface.shadow_available);
        assert_eq!(surface.jump_model_active_state, "jump_model_unavailable");
    }

    #[test]
    fn shadow_surface_exposes_jump_model_sidecar() {
        let mut packet = BeliefReportPacket::default();
        packet.regime_companion.jump_model = Some(crate::domain::regime::JumpModelRegimeSummary {
            active_state: "jump_transition".to_string(),
            confidence: 0.61,
            transition_risk: 0.61,
            state_probabilities: std::collections::BTreeMap::new(),
            evidence: vec![],
        });

        packet.regime_companion.disagreement = Some(
            crate::application::belief::build_regime_disagreement_summary(
                Some("trend"),
                packet.regime_companion.jump_model.as_ref(),
            ),
        );

        let surface = build_belief_shadow_policy_surface(&packet, None);
        assert_eq!(surface.jump_model_active_state, "jump_transition");
        assert!(surface.jump_model_transition_risk > 0.6);
        assert!(surface.jump_model_disagreement_score > 0.6);
        assert_eq!(surface.jump_model_gate_bias, "shrink_and_observe");
    }
}
