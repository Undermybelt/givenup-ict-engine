use serde::{Deserialize, Serialize};

use crate::application::belief::{IsingOverlayState, OuOverlayState};
use crate::application::execution::ExecutionPhysicsOverlay;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PipelineState {
    pub symbol: String,
    pub market: Option<String>,
    pub feature_flag: String,
    pub completed_stages: Vec<String>,
    pub ou_overlay: Option<OuOverlayState>,
    pub ising_overlay: Option<IsingOverlayState>,
    pub physics_overlay: Option<ExecutionPhysicsOverlay>,
}

impl PipelineState {
    pub fn new(
        symbol: impl Into<String>,
        market: Option<&str>,
        feature_flag: impl Into<String>,
    ) -> Self {
        Self {
            symbol: symbol.into(),
            market: market.map(str::to_string),
            feature_flag: feature_flag.into(),
            completed_stages: Vec::new(),
            ou_overlay: None,
            ising_overlay: None,
            physics_overlay: None,
        }
    }

    pub fn mark_stage_completed(&mut self, stage: impl Into<String>) {
        self.completed_stages.push(stage.into());
    }
}
