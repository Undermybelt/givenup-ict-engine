use anyhow::Result;

use crate::bbn::temporal::bootstrap_particle_summary;
use crate::domain::belief::{
    BeliefEvidencePacket, BeliefReportPacket, EngineTrace, ShadowComparisonSummary,
};

use super::{BeliefInferenceEngine, ExactEngine, InferenceRequest, LoopyEngine, SamplingEngine};
use crate::bbn::adapters::{
    gate_decision_from_regime_posterior, strategy_recommendation_from_pre_bayes_filter,
};
use crate::state::PreBayesEvidenceFilter;

pub struct InferenceEngineRegistry {
    primary: Box<dyn BeliefInferenceEngine + Send + Sync>,
    shadow: Vec<Box<dyn BeliefInferenceEngine + Send + Sync>>,
}

impl Default for InferenceEngineRegistry {
    fn default() -> Self {
        let primary_name = std::env::var("ICT_ENGINE_BELIEF_PRIMARY")
            .unwrap_or_else(|_| "exact".to_string())
            .to_ascii_lowercase();
        let primary: Box<dyn BeliefInferenceEngine + Send + Sync> = match primary_name.as_str() {
            "loopy" => Box::new(LoopyEngine),
            "sampling" => Box::new(SamplingEngine),
            _ => Box::new(ExactEngine),
        };
        Self {
            primary,
            shadow: vec![Box::new(LoopyEngine), Box::new(SamplingEngine)],
        }
    }
}

impl InferenceEngineRegistry {
    pub fn build_report(&self, packet: BeliefEvidencePacket) -> Result<BeliefReportPacket> {
        let request = InferenceRequest { packet };
        let regime_posterior = self.primary.infer_regime(&request)?;
        let gate_decision = gate_decision_from_regime_posterior(&regime_posterior);
        let belief_posteriors = self.primary.infer_beliefs(&request)?;
        let credible_intervals = self.primary.credible_intervals(&request)?;

        let selected_direction = if regime_posterior.active_regime.as_deref() == Some("trend") {
            "bull"
        } else {
            "neutral"
        };
        let pseudo_filter = PreBayesEvidenceFilter {
            filtered_market_regime_label: request
                .packet
                .regime_features
                .market_regime_label
                .clone()
                .unwrap_or_else(|| "range".to_string()),
            filtered_liquidity_context_label: request
                .packet
                .regime_features
                .liquidity_regime_label
                .clone()
                .unwrap_or_else(|| "neutral".to_string()),
            filtered_multi_timeframe_resonance_label: request
                .packet
                .multi_timeframe_evidence
                .get("filtered_resonance_label")
                .cloned()
                .unwrap_or_else(|| "mixed".to_string()),
            evidence_quality_score: 1.0
                - request
                    .packet
                    .regime_features
                    .stress_score
                    .unwrap_or(0.5)
                    .clamp(0.0, 1.0),
            rationale: request.packet.factor_evidence.clone(),
            gating_status: if gate_decision.selected_regime == "stress" {
                "observe_only".to_string()
            } else {
                "pass_neutralized".to_string()
            },
            ..PreBayesEvidenceFilter::default()
        };
        let strategy_recommendation =
            strategy_recommendation_from_pre_bayes_filter(&pseudo_filter, selected_direction, 0.55);

        let mut match_rate = std::collections::BTreeMap::new();
        let mut kl_divergence = std::collections::BTreeMap::new();
        let mut interval_overlap = std::collections::BTreeMap::new();
        let mut recommendation_drift = Vec::new();
        let mut shadow_names = Vec::new();
        for engine in &self.shadow {
            shadow_names.push(engine.name().to_string());
            let shadow_beliefs = engine.infer_beliefs(&request)?;
            let shadow_intervals = engine.credible_intervals(&request)?;
            for primary in &belief_posteriors {
                if let Some(shadow) = shadow_beliefs
                    .iter()
                    .find(|item| item.node_id == primary.node_id)
                {
                    match_rate.insert(
                        format!("{}:{}", engine.name(), primary.node_id),
                        if primary.top_state == shadow.top_state {
                            1.0
                        } else {
                            0.0
                        },
                    );
                    kl_divergence.insert(
                        format!("{}:{}", engine.name(), primary.node_id),
                        (primary.top_probability - shadow.top_probability).abs(),
                    );
                }
            }
            for primary in &credible_intervals {
                if let Some(shadow) = shadow_intervals
                    .iter()
                    .find(|item| item.node_id == primary.node_id)
                {
                    let overlap_low = primary.lower.max(shadow.lower);
                    let overlap_high = primary.upper.min(shadow.upper);
                    let overlap = if overlap_high > overlap_low {
                        overlap_high - overlap_low
                    } else {
                        0.0
                    };
                    interval_overlap
                        .insert(format!("{}:{}", engine.name(), primary.node_id), overlap);
                }
            }
            recommendation_drift.push(format!(
                "{}:direction={}",
                engine.name(),
                strategy_recommendation.direction
            ));
        }

        let node_count = belief_posteriors.len();
        let shadow_engine_names = shadow_names.join(",");
        let shadow_status = if kl_divergence.values().any(|value| *value > 0.35) {
            "red".to_string()
        } else if kl_divergence.values().any(|value| *value > 0.15) {
            "yellow".to_string()
        } else {
            "green".to_string()
        };
        let temporal_summary = bootstrap_particle_summary(
            regime_posterior.active_regime.as_deref().unwrap_or("range"),
        );

        Ok(BeliefReportPacket {
            regime_posterior,
            gate_decision,
            belief_posteriors,
            credible_intervals,
            strategy_recommendation,
            engine_trace: EngineTrace {
                primary_engine: self.primary.name().to_string(),
                shadow_engine: Some(shadow_engine_names.clone()),
                sample_count: Some(self.shadow.len()),
                notes: vec![
                    "registry_build_report_v3".to_string(),
                    format!(
                        "particle_count={} ess={:.2} dominant_regime={}",
                        temporal_summary.particle_count,
                        temporal_summary.effective_sample_size,
                        temporal_summary.dominant_regime
                    ),
                ],
            },
            temporal_summary: Some(temporal_summary.clone()),
            shadow_comparison: Some(ShadowComparisonSummary {
                status: shadow_status.clone(),
                summary_line: format!(
                    "primary={} shadow={} nodes={} status={} particle_count={} ess={:.2}",
                    self.primary.name(),
                    shadow_engine_names,
                    node_count,
                    shadow_status,
                    temporal_summary.particle_count,
                    temporal_summary.effective_sample_size
                ),
                top_state_match_rate: match_rate,
                kl_divergence,
                interval_overlap,
                recommendation_drift,
            }),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    #[test]
    fn registry_builds_belief_report_packet() {
        let registry = InferenceEngineRegistry::default();
        let report = registry
            .build_report(BeliefEvidencePacket {
                symbol: "NQ".to_string(),
                market: Some("futures".to_string()),
                timestamp: None,
                regime_features: crate::domain::regime::RegimeFeatures {
                    market_regime_label: Some("bull".to_string()),
                    volatility_regime_label: Some("low".to_string()),
                    liquidity_regime_label: Some("favorable".to_string()),
                    stress_score: Some(0.2),
                    transition_score: Some(0.1),
                    evidence: vec![],
                },
                market_evidence: vec![],
                factor_evidence: vec!["aligned".to_string()],
                timed_pda_summary: BTreeMap::new(),
                multi_timeframe_evidence: BTreeMap::from([(
                    "filtered_resonance_label".to_string(),
                    "aligned".to_string(),
                )]),
                evidence_assignments: BTreeMap::from([
                    ("market_regime".to_string(), "bull".to_string()),
                    ("liquidity_context".to_string(), "favorable".to_string()),
                    ("entry_quality".to_string(), "high".to_string()),
                ]),
            })
            .unwrap();
        assert!(!report.engine_trace.primary_engine.is_empty());
        assert!(!report.belief_posteriors.is_empty());
        assert_eq!(report.gate_decision.selected_subgraph, "trend_subgraph");
        assert!(report.shadow_comparison.is_some());
        assert!(report
            .shadow_comparison
            .as_ref()
            .unwrap()
            .summary_line
            .contains("particle_count="));
    }
}
