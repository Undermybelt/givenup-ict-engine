use anyhow::Result;
use std::collections::BTreeMap;

use crate::domain::belief::{BeliefNodePosteriorSnapshot, CredibleInterval};
use crate::domain::regime::RegimePosterior;

use super::{BeliefInferenceEngine, ExactEngine, InferenceRequest};

#[derive(Debug, Default, Clone, Copy)]
pub struct SamplingEngine;

impl SamplingEngine {
    fn resample_distribution(probabilities: &BTreeMap<String, f64>) -> BTreeMap<String, f64> {
        let len = probabilities.len().max(1) as f64;
        let mut adjusted = BTreeMap::new();
        for (idx, (state, prob)) in probabilities.iter().enumerate() {
            let tilt = (((idx + 1) as f64) * 0.0175).min(0.05);
            let blended = ((*prob * (1.0 - tilt)) + ((1.0 / len) * tilt)).clamp(0.0, 1.0);
            adjusted.insert(state.clone(), blended);
        }
        let total: f64 = adjusted.values().sum();
        if total > 0.0 {
            for value in adjusted.values_mut() {
                *value /= total;
            }
        }
        adjusted
    }
}

impl BeliefInferenceEngine for SamplingEngine {
    fn name(&self) -> &'static str {
        "sampling-stub"
    }

    fn infer_regime(&self, request: &InferenceRequest) -> Result<RegimePosterior> {
        ExactEngine.infer_regime(request)
    }

    fn infer_beliefs(
        &self,
        request: &InferenceRequest,
    ) -> Result<Vec<BeliefNodePosteriorSnapshot>> {
        let mut beliefs = ExactEngine.infer_beliefs(request)?;
        for belief in &mut beliefs {
            belief.probabilities = Self::resample_distribution(&belief.probabilities);
            if let Some((state, prob)) = belief
                .probabilities
                .iter()
                .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            {
                belief.top_state = state.clone();
                belief.top_probability = *prob;
            }
            belief.entropy = belief
                .probabilities
                .values()
                .filter(|p| **p > 0.0)
                .map(|p| -p * p.ln())
                .sum();
        }
        Ok(beliefs)
    }

    fn credible_intervals(&self, request: &InferenceRequest) -> Result<Vec<CredibleInterval>> {
        let beliefs = self.infer_beliefs(request)?;
        Ok(beliefs
            .into_iter()
            .map(|belief| CredibleInterval {
                node_id: belief.node_id,
                state: belief.top_state,
                lower: (belief.top_probability - 0.20).clamp(0.0, 1.0),
                median: belief.top_probability,
                upper: (belief.top_probability + 0.20).clamp(0.0, 1.0),
                method: "sampling-stub-quantile".to_string(),
            })
            .collect())
    }

    fn supports_samples(&self) -> bool {
        true
    }
}
