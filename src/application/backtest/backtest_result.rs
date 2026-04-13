use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct BacktestResultArtifact {
    pub summary: String,
    pub scorecards: Vec<String>,
    pub market_breakdown: Vec<String>,
    pub regime_breakdown: Vec<String>,
    pub window_breakdown: Vec<String>,
    pub comparable: bool,
    pub artifacts: Vec<String>,
}

pub fn build_backtest_result_artifact(
    summary: impl Into<String>,
    scorecards: &[String],
    market_breakdown: &[String],
    regime_breakdown: &[String],
    window_breakdown: &[String],
    comparable: bool,
    artifacts: &[String],
) -> BacktestResultArtifact {
    BacktestResultArtifact {
        summary: summary.into(),
        scorecards: scorecards.to_vec(),
        market_breakdown: market_breakdown.to_vec(),
        regime_breakdown: regime_breakdown.to_vec(),
        window_breakdown: window_breakdown.to_vec(),
        comparable,
        artifacts: artifacts.to_vec(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn backtest_result_builder_keeps_comparable_flag() {
        let result = build_backtest_result_artifact("summary", &[], &[], &[], &[], true, &[]);
        assert!(result.comparable);
    }
}
