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
}

pub fn build_belief_shadow_policy_surface(
    packet: &BeliefReportPacket,
    policy_record: Option<&PreBayesPolicyRecord>,
) -> BeliefShadowPolicySurface {
    BeliefShadowPolicySurface {
        policy_version: policy_record
            .map(|record| record.policy.version.clone())
            .unwrap_or_default(),
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
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shadow_surface_defaults_without_policy_record() {
        let packet = BeliefReportPacket::default();
        let surface = build_belief_shadow_policy_surface(&packet, None);
        assert_eq!(surface.shadow_summary_line, "shadow=unavailable");
        assert!(!surface.shadow_available);
    }
}
