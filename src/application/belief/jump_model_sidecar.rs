use std::collections::BTreeMap;

use crate::domain::regime::{JumpModelRegimeSummary, RegimeFeatures};
use crate::state::WorkflowSnapshot;

fn normalized_distribution(entries: [(String, f64); 3]) -> BTreeMap<String, f64> {
    let total = entries.iter().map(|(_, value)| value.max(0.0)).sum::<f64>();
    entries
        .into_iter()
        .map(|(label, value)| {
            let normalized = if total > 0.0 {
                value.max(0.0) / total
            } else {
                1.0 / 3.0
            };
            (label, normalized)
        })
        .collect()
}

pub fn build_jump_model_regime_sidecar(
    features: &RegimeFeatures,
    multi_timeframe_evidence: &BTreeMap<String, String>,
    factor_evidence: &[String],
) -> JumpModelRegimeSummary {
    let trend_score = match features.market_regime_label.as_deref() {
        Some("bull") | Some("bear") | Some("trend") => 0.62,
        Some("range") => 0.18,
        _ => 0.34,
    };
    let balance_score = match features.market_regime_label.as_deref() {
        Some("range") => 0.58,
        Some("bull") | Some("bear") | Some("trend") => 0.20,
        _ => 0.30,
    };
    let transition_hint = multi_timeframe_evidence
        .get("filtered_resonance_label")
        .map(|value| value.as_str())
        .unwrap_or("mixed");
    let volatility = features.stress_score.unwrap_or(0.5).clamp(0.0, 1.0);
    let transition_score = match transition_hint {
        "dislocated" => 0.66,
        "mixed" => 0.42,
        "aligned" => 0.18,
        _ => 0.34,
    } + volatility * 0.18
        + features.transition_score.unwrap_or(0.0).clamp(0.0, 1.0) * 0.24;

    let state_probabilities = normalized_distribution([
        ("trend_persistent".to_string(), trend_score),
        ("balance_mean_revert".to_string(), balance_score),
        ("jump_transition".to_string(), transition_score),
    ]);

    let (active_state, confidence) = state_probabilities
        .iter()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(state, probability)| (state.clone(), *probability))
        .unwrap_or_else(|| ("balance_mean_revert".to_string(), 1.0 / 3.0));

    let transition_risk = state_probabilities
        .get("jump_transition")
        .copied()
        .unwrap_or_default();
    let mut evidence = vec![
        format!("jump_model.active_state={active_state}"),
        format!("jump_model.transition_hint={transition_hint}"),
        format!("jump_model.volatility={volatility:.3}"),
    ];
    if let Some(liquidity) = features.liquidity_regime_label.as_deref() {
        evidence.push(format!("jump_model.liquidity={liquidity}"));
    }
    evidence.extend(
        factor_evidence
            .iter()
            .take(2)
            .map(|item| format!("jump_model.factor={item}")),
    );

    JumpModelRegimeSummary {
        active_state,
        confidence,
        transition_risk,
        state_probabilities,
        evidence,
    }
}

pub fn jump_model_workflow_summary(snapshot: &WorkflowSnapshot) -> Option<String> {
    let vote = snapshot.latest_ensemble_vote.as_ref()?;
    vote.executor_summaries
        .iter()
        .find(|line| line.contains("jump_model"))
        .cloned()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn jump_model_sidecar_prefers_transition_state_when_dislocated_and_stressed() {
        let summary = build_jump_model_regime_sidecar(
            &RegimeFeatures {
                market_regime_label: Some("range".to_string()),
                liquidity_regime_label: Some("hostile".to_string()),
                stress_score: Some(0.9),
                transition_score: Some(0.8),
                ..RegimeFeatures::default()
            },
            &BTreeMap::from([(
                "filtered_resonance_label".to_string(),
                "dislocated".to_string(),
            )]),
            &["mtf_divergence".to_string()],
        );

        assert_eq!(summary.active_state, "jump_transition");
        assert!(summary.transition_risk > 0.4);
        assert_eq!(summary.state_probabilities.len(), 3);
    }
}
