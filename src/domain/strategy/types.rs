use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StrategyRecommendation {
    pub direction: String,
    pub aggression_level: String,
    pub sizing_multiplier: f64,
    pub invalidate_if: Vec<String>,
    pub rationale: Vec<String>,
}
