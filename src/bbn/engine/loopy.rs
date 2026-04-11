use anyhow::Result;

use crate::domain::belief::{BeliefNodePosteriorSnapshot, CredibleInterval};
use crate::domain::regime::RegimePosterior;

use super::{
    infer_with_loopy_adapter, loopy_adapter_ready, BeliefInferenceEngine, ExactEngine,
    InferenceRequest,
};

#[derive(Debug, Default, Clone, Copy)]
pub struct LoopyEngine;

impl BeliefInferenceEngine for LoopyEngine {
    fn name(&self) -> &'static str {
        if loopy_adapter_ready() {
            "loopy"
        } else {
            "loopy-stub"
        }
    }

    fn infer_regime(&self, request: &InferenceRequest) -> Result<RegimePosterior> {
        ExactEngine.infer_regime(request)
    }

    fn infer_beliefs(
        &self,
        request: &InferenceRequest,
    ) -> Result<Vec<BeliefNodePosteriorSnapshot>> {
        if loopy_adapter_ready() {
            infer_with_loopy_adapter(&request.packet.evidence_assignments)
        } else {
            ExactEngine.infer_beliefs(request)
        }
    }

    fn credible_intervals(&self, request: &InferenceRequest) -> Result<Vec<CredibleInterval>> {
        let beliefs = self.infer_beliefs(request)?;
        Ok(beliefs
            .into_iter()
            .map(|belief| CredibleInterval {
                node_id: belief.node_id,
                state: belief.top_state,
                lower: (belief.top_probability - 0.18).clamp(0.0, 1.0),
                median: belief.top_probability,
                upper: (belief.top_probability + 0.18).clamp(0.0, 1.0),
                method: "loopy-belief-propagation".to_string(),
            })
            .collect())
    }
}
