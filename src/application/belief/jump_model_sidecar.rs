use std::collections::BTreeMap;

use crate::domain::regime::{
    JumpModelRegimeSummary, RegimeDisagreementSummary, RegimeFeatures,
};
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
    let market_family = factor_evidence.iter().find_map(|line| {
        line.strip_prefix("market_category=")
            .map(|value| value.to_string())
    });
    let trend_weight = match market_family.as_deref() {
        Some("futures_index") => 1.10,
        Some("metals") => 0.92,
        Some("energy") => 0.84,
        _ => 1.0,
    };
    let balance_weight = match market_family.as_deref() {
        Some("metals") => 1.08,
        Some("energy") => 0.88,
        Some("futures_index") => 0.95,
        _ => 1.0,
    };
    let transition_weight = match market_family.as_deref() {
        Some("energy") => 1.18,
        Some("futures_index") => 1.02,
        Some("metals") => 0.96,
        _ => 1.0,
    };
    let trend_score = match features.market_regime_label.as_deref() {
        Some("bull") | Some("bear") | Some("trend") => 0.62 * trend_weight,
        Some("range") => 0.18 * trend_weight,
        _ => 0.34 * trend_weight,
    };
    let balance_score = match features.market_regime_label.as_deref() {
        Some("range") => 0.58 * balance_weight,
        Some("bull") | Some("bear") | Some("trend") => 0.20 * balance_weight,
        _ => 0.30 * balance_weight,
    };
    let transition_hint = multi_timeframe_evidence
        .get("filtered_resonance_label")
        .map(|value| value.as_str())
        .unwrap_or("mixed");
    let volatility = features.stress_score.unwrap_or(0.5).clamp(0.0, 1.0);
    let transition_score = (match transition_hint {
        "dislocated" => 0.66,
        "mixed" => 0.42,
        "aligned" => 0.18,
        _ => 0.34,
    } + volatility * 0.18
        + features.transition_score.unwrap_or(0.0).clamp(0.0, 1.0) * 0.24)
        * transition_weight;

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
        format!(
            "jump_model.market_family_weighting={}:trend={:.2}:balance={:.2}:transition={:.2}",
            market_family.clone().unwrap_or_else(|| "unknown".to_string()),
            trend_weight,
            balance_weight,
            transition_weight
        ),
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

pub fn build_regime_disagreement_summary(
    hmm_active_regime: Option<&str>,
    jump_model: Option<&JumpModelRegimeSummary>,
) -> RegimeDisagreementSummary {
    let jump_active_state = jump_model.map(|item| item.active_state.clone());
    let aligned = match (hmm_active_regime, jump_active_state.as_deref()) {
        (Some("trend"), Some("trend_persistent")) => true,
        (Some("range"), Some("balance_mean_revert")) => true,
        (Some("transition"), Some("jump_transition")) => true,
        (Some(_), Some(_)) => false,
        _ => true,
    };
    let disagreement_score = if let Some(jump_model) = jump_model {
        if aligned {
            (1.0 - jump_model.confidence).clamp(0.0, 1.0) * 0.35
        } else {
            jump_model.confidence.clamp(0.0, 1.0)
        }
    } else {
        0.0
    };
    let gate_bias = if jump_model.is_none() {
        "hmm_only".to_string()
    } else if aligned {
        "relax_if_other_gates_clear".to_string()
    } else {
        "shrink_and_observe".to_string()
    };
    let mut evidence = Vec::new();
    if let Some(hmm) = hmm_active_regime {
        evidence.push(format!("hmm_active_regime={hmm}"));
    }
    if let Some(jump) = &jump_active_state {
        evidence.push(format!("jump_active_state={jump}"));
    }
    evidence.push(format!("aligned={aligned}"));
    evidence.push(format!("disagreement_score={disagreement_score:.3}"));
    evidence.push(format!("gate_bias={gate_bias}"));

    RegimeDisagreementSummary {
        hmm_active_regime: hmm_active_regime.map(|value| value.to_string()),
        jump_active_state,
        aligned,
        disagreement_score,
        gate_bias,
        evidence,
    }
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
            &[
                "market_category=energy".to_string(),
                "mtf_divergence".to_string(),
            ],
        );

        assert_eq!(summary.active_state, "jump_transition");
        assert!(summary.transition_risk > 0.4);
        assert_eq!(summary.state_probabilities.len(), 3);
    }
}
