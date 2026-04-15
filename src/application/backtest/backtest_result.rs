use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct BacktestResultArtifact {
    pub summary: String,
    pub scorecards: Vec<String>,
    pub shrink_comparison_summary: Vec<String>,
    pub oos_quality_delta_surface: Vec<String>,
    pub market_breakdown: Vec<String>,
    pub regime_breakdown: Vec<String>,
    pub window_breakdown: Vec<String>,
    pub comparable: bool,
    pub artifacts: Vec<String>,
}

pub fn build_backtest_result_artifact(
    summary: impl Into<String>,
    scorecards: &[String],
    shrink_comparison_summary: &[String],
    oos_quality_delta_surface: &[String],
    market_breakdown: &[String],
    regime_breakdown: &[String],
    window_breakdown: &[String],
    comparable: bool,
    artifacts: &[String],
) -> BacktestResultArtifact {
    BacktestResultArtifact {
        summary: summary.into(),
        scorecards: scorecards.to_vec(),
        shrink_comparison_summary: shrink_comparison_summary.to_vec(),
        oos_quality_delta_surface: oos_quality_delta_surface.to_vec(),
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
        let result = build_backtest_result_artifact(
            "summary",
            &[],
            &["shrink_preference=neutral".to_string()],
            &["oos_quality_direction=flat".to_string()],
            &[],
            &[],
            &[],
            true,
            &[],
        );
        assert!(result.comparable);
        assert_eq!(
            result.shrink_comparison_summary,
            vec!["shrink_preference=neutral".to_string()]
        );
        assert_eq!(
            result.oos_quality_delta_surface,
            vec!["oos_quality_direction=flat".to_string()]
        );
    }
}
