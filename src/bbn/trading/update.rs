use anyhow::{anyhow, bail, Result};

use crate::bbn::{
    dag::BayesianNetwork,
    evidence::{Evidence, EvidenceType},
    inference::VariableEliminationEngine,
};
use crate::state::PreBayesEvidenceFilter;

pub fn trade_evidence_from_labels(
    network: &BayesianNetwork,
    assignments: &[(&str, &str)],
) -> Result<Evidence> {
    let mut evidence = Evidence::new();

    for (node_id, state_label) in assignments {
        let node = network
            .nodes
            .get(*node_id)
            .ok_or_else(|| anyhow!("unknown node '{}'", node_id))?;
        let state_index = node
            .state_index(state_label)
            .ok_or_else(|| anyhow!("unknown state '{}' for node '{}'", state_label, node_id))?;
        evidence.insert((*node_id).to_string(), EvidenceType::Hard(state_index));
    }

    Ok(evidence)
}

pub fn trade_evidence_from_pre_bayes_filter(
    network: &BayesianNetwork,
    filter: &PreBayesEvidenceFilter,
) -> Result<Evidence> {
    let mut evidence = Evidence::new();
    let nodes = [
        (
            "market_regime",
            &filter.filtered_market_regime_label,
            &filter.soft_market_regime_distribution,
        ),
        (
            "liquidity_context",
            &filter.filtered_liquidity_context_label,
            &filter.soft_liquidity_context_distribution,
        ),
        (
            "factor_alignment",
            &filter.filtered_factor_alignment,
            &filter.soft_factor_alignment_distribution,
        ),
        (
            "factor_uncertainty",
            &filter.filtered_factor_uncertainty,
            &filter.soft_factor_uncertainty_distribution,
        ),
        (
            "multi_timeframe_resonance",
            &filter.filtered_multi_timeframe_resonance_label,
            &filter.soft_multi_timeframe_resonance_distribution,
        ),
    ];

    for (node_id, filtered_label, soft_distribution) in nodes {
        let node = network
            .nodes
            .get(node_id)
            .ok_or_else(|| anyhow!("unknown node '{}'", node_id))?;
        if filter.uses_soft_evidence && !soft_distribution.is_empty() {
            evidence.insert(
                node_id.to_string(),
                EvidenceType::Soft(distribution_from_named_map(node, soft_distribution)?),
            );
        } else {
            let state_index = node.state_index(filtered_label).ok_or_else(|| {
                anyhow!("unknown state '{}' for node '{}'", filtered_label, node_id)
            })?;
            evidence.insert(node_id.to_string(), EvidenceType::Hard(state_index));
        }
    }

    Ok(evidence)
}

pub fn infer_trade_outcome(network: &BayesianNetwork, evidence: &Evidence) -> Result<Vec<f64>> {
    let entry_quality = infer_entry_quality(network, evidence)?;
    infer_trade_outcome_from_entry_quality_distribution(network, evidence, &entry_quality)
}

pub fn infer_entry_quality(network: &BayesianNetwork, evidence: &Evidence) -> Result<Vec<f64>> {
    VariableEliminationEngine::query(network, "entry_quality", evidence)
}

pub fn infer_entry_quality_with_bias(
    network: &BayesianNetwork,
    evidence: &Evidence,
    entry_quality_bias: &[f64],
) -> Result<Vec<f64>> {
    let mut entry_quality = infer_entry_quality(network, evidence)?;

    if entry_quality.len() != entry_quality_bias.len() {
        bail!(
            "entry quality bias length {} does not match network state count {}",
            entry_quality_bias.len(),
            entry_quality.len()
        );
    }

    for (probability, bias) in entry_quality.iter_mut().zip(entry_quality_bias.iter()) {
        if !bias.is_finite() || *bias < 0.0 {
            bail!("entry quality bias must be finite and non-negative");
        }
        *probability *= *bias;
    }

    normalize(&mut entry_quality);
    Ok(entry_quality)
}

pub fn infer_trade_outcome_with_entry_quality_bias(
    network: &BayesianNetwork,
    evidence: &Evidence,
    entry_quality_bias: &[f64],
) -> Result<Vec<f64>> {
    let entry_quality = infer_entry_quality_with_bias(network, evidence, entry_quality_bias)?;

    infer_trade_outcome_from_entry_quality_distribution(network, evidence, &entry_quality)
}

fn infer_trade_outcome_from_entry_quality_distribution(
    network: &BayesianNetwork,
    evidence: &Evidence,
    entry_quality: &[f64],
) -> Result<Vec<f64>> {
    if entry_quality.is_empty() {
        bail!("entry quality distribution cannot be empty");
    }

    let trade_outcome = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("unknown node 'trade_outcome'"))?;
    let mut distribution = vec![0.0; trade_outcome.states.len()];

    for (entry_state, entry_probability) in entry_quality.iter().copied().enumerate() {
        let mut parent_config = Vec::with_capacity(trade_outcome.parents.len());
        for parent in &trade_outcome.parents {
            if parent == "entry_quality" {
                parent_config.push(entry_state);
            } else {
                let state = match evidence.get(parent) {
                    Some(EvidenceType::Hard(index)) => *index,
                    Some(EvidenceType::Soft(distribution)) => distribution
                        .iter()
                        .enumerate()
                        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                        .map(|(idx, _)| idx)
                        .ok_or_else(|| anyhow!("soft evidence for '{}' is empty", parent))?,
                    None => bail!("missing evidence for trade_outcome parent '{}'", parent),
                };
                parent_config.push(state);
            }
        }
        let outcome_probs = trade_outcome.cpt.get(&parent_config).ok_or_else(|| {
            anyhow!(
                "missing CPT for 'trade_outcome' and config {:?}",
                parent_config
            )
        })?;

        for (outcome_probability, conditional_probability) in
            distribution.iter_mut().zip(outcome_probs.iter())
        {
            *outcome_probability += entry_probability * conditional_probability;
        }
    }

    Ok(distribution)
}

pub fn entry_quality_bias_from_signal(signal_probability: f64) -> Vec<f64> {
    let signal_probability = signal_probability.clamp(0.001, 0.999);
    let high = signal_probability;
    let low = 1.0 - signal_probability;
    let medium = 1.0 - ((signal_probability - 0.5).abs() * 2.0);
    let mut bias = vec![high, medium.max(0.0), low];
    normalize(&mut bias);
    bias
}

fn normalize(values: &mut [f64]) {
    let sum: f64 = values.iter().sum();
    if sum <= f64::EPSILON {
        let uniform = 1.0 / values.len() as f64;
        values.fill(uniform);
        return;
    }

    for value in values {
        *value /= sum;
    }
}

fn distribution_from_named_map(
    node: &crate::bbn::node::Node,
    distribution: &std::collections::BTreeMap<String, f64>,
) -> Result<Vec<f64>> {
    let mut values = vec![0.0; node.states.len()];
    for (state, probability) in distribution {
        let index = node
            .state_index(state)
            .ok_or_else(|| anyhow!("unknown state '{}' for node '{}'", state, node.id))?;
        values[index] = *probability;
    }
    normalize(&mut values);
    Ok(values)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bbn::trading::topology::build_trading_network;
    use crate::state::PreBayesEvidenceFilter;

    #[test]
    fn test_entry_quality_bias_monotonicity() {
        let low = entry_quality_bias_from_signal(0.2);
        let high = entry_quality_bias_from_signal(0.8);

        assert!(high[0] > low[0]);
        assert!(high[2] < low[2]);
        assert!((low.iter().sum::<f64>() - 1.0).abs() < 1e-9);
        assert!((high.iter().sum::<f64>() - 1.0).abs() < 1e-9);
    }

    #[test]
    fn test_infer_trade_outcome_with_entry_quality_bias() {
        let network = build_trading_network().unwrap();
        let evidence = trade_evidence_from_labels(
            &network,
            &[
                ("market_regime", "bull"),
                ("liquidity_context", "favorable"),
                ("factor_alignment", "bullish"),
                ("factor_uncertainty", "low"),
                ("multi_timeframe_resonance", "aligned"),
            ],
        )
        .unwrap();

        let bullish = infer_trade_outcome_with_entry_quality_bias(
            &network,
            &evidence,
            &entry_quality_bias_from_signal(0.8),
        )
        .unwrap();
        let weak = infer_trade_outcome_with_entry_quality_bias(
            &network,
            &evidence,
            &entry_quality_bias_from_signal(0.2),
        )
        .unwrap();

        assert!(bullish[0] > weak[0]);
        assert!(bullish[2] < weak[2]);
    }

    #[test]
    fn test_trade_evidence_from_pre_bayes_filter_uses_soft_evidence() {
        let network = build_trading_network().unwrap();
        let evidence = trade_evidence_from_pre_bayes_filter(
            &network,
            &PreBayesEvidenceFilter {
                filtered_market_regime_label: "bull".to_string(),
                filtered_liquidity_context_label: "neutral".to_string(),
                filtered_factor_alignment: "mixed".to_string(),
                filtered_factor_uncertainty: "high".to_string(),
                filtered_multi_timeframe_resonance_label: "mixed".to_string(),
                uses_soft_evidence: true,
                soft_market_regime_distribution: std::collections::BTreeMap::from([
                    ("bull".to_string(), 0.6),
                    ("bear".to_string(), 0.2),
                    ("range".to_string(), 0.2),
                ]),
                soft_liquidity_context_distribution: std::collections::BTreeMap::from([
                    ("favorable".to_string(), 0.2),
                    ("neutral".to_string(), 0.6),
                    ("hostile".to_string(), 0.2),
                ]),
                soft_factor_alignment_distribution: std::collections::BTreeMap::from([
                    ("bullish".to_string(), 0.2),
                    ("mixed".to_string(), 0.6),
                    ("bearish".to_string(), 0.2),
                ]),
                soft_factor_uncertainty_distribution: std::collections::BTreeMap::from([
                    ("low".to_string(), 0.3),
                    ("high".to_string(), 0.7),
                ]),
                soft_multi_timeframe_resonance_distribution: std::collections::BTreeMap::from([
                    ("aligned".to_string(), 0.2),
                    ("mixed".to_string(), 0.6),
                    ("dislocated".to_string(), 0.2),
                ]),
                ..PreBayesEvidenceFilter::default()
            },
        )
        .unwrap();

        assert!(matches!(
            evidence.get("factor_alignment"),
            Some(EvidenceType::Soft(_))
        ));
        assert!(matches!(
            evidence.get("factor_uncertainty"),
            Some(EvidenceType::Soft(_))
        ));
        assert!(matches!(
            evidence.get("multi_timeframe_resonance"),
            Some(EvidenceType::Soft(_))
        ));
    }
}
