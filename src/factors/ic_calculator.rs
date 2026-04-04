/// IC (Information Coefficient) calculator
pub struct ICCalculator;

impl ICCalculator {
    /// Calculate IC between factor values and returns
    pub fn calculate(factor_values: &[f64], returns: &[f64]) -> f64 {
        if factor_values.len() != returns.len() || factor_values.len() < 2 {
            return 0.0;
        }

        // Spearman rank correlation
        let n = factor_values.len();
        let mut factor_ranks = vec![0.0; n];
        let mut return_ranks = vec![0.0; n];

        // Simple ranking
        for i in 0..n {
            factor_ranks[i] = factor_values
                .iter()
                .filter(|&&f| f < factor_values[i])
                .count() as f64;
            return_ranks[i] = returns.iter().filter(|&&r| r < returns[i]).count() as f64;
        }

        // Pearson correlation on ranks
        let fr_mean = factor_ranks.iter().sum::<f64>() / n as f64;
        let rr_mean = return_ranks.iter().sum::<f64>() / n as f64;

        let mut xy = 0.0;
        let mut xx = 0.0;
        let mut yy = 0.0;

        for i in 0..n {
            let dx = factor_ranks[i] - fr_mean;
            let dy = return_ranks[i] - rr_mean;
            xy += dx * dy;
            xx += dx * dx;
            yy += dy * dy;
        }

        let denom = (xx * yy).sqrt();
        if denom > 0.0 {
            xy / denom
        } else {
            0.0
        }
    }
}
