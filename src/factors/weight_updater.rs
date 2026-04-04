use crate::types::FactorIC;

/// Factor weight updater
pub struct WeightUpdater;

impl WeightUpdater {
    /// Update weights based on IC/IR
    pub fn update_weights(factors: &mut [FactorIC]) {
        let total_ir: f64 = factors.iter().map(|f| f.ir.abs()).sum();

        if total_ir > 0.0 {
            for factor in factors.iter_mut() {
                factor.weight = factor.ir.abs() / total_ir;
            }
        }
    }
}
