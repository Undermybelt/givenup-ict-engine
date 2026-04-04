use crate::types::Regime;

/// Regime-conditional factor evaluation
pub struct RegimeConditional;

impl RegimeConditional {
    /// Evaluate factor under specific regime
    pub fn evaluate(factor_value: f64, regime: Regime) -> f64 {
        match regime {
            Regime::Accumulation => factor_value * 0.8,
            Regime::ManipulationExpansion => factor_value * 1.2,
            Regime::Distribution => factor_value * 0.9,
        }
    }
}
