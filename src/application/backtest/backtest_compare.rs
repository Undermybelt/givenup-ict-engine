use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct BacktestCompareReport {
    pub summary: String,
    pub improvements: Vec<String>,
    pub regressions: Vec<String>,
    pub recommended_actions: Vec<String>,
}

pub fn compare_backtest_results(
    summary: impl Into<String>,
    improvements: &[String],
    regressions: &[String],
    recommended_actions: &[String],
) -> BacktestCompareReport {
    BacktestCompareReport {
        summary: summary.into(),
        improvements: improvements.to_vec(),
        regressions: regressions.to_vec(),
        recommended_actions: recommended_actions.to_vec(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compare_report_keeps_regressions() {
        let report = compare_backtest_results(
            "summary",
            &["up".to_string()],
            &["down".to_string()],
            &["next".to_string()],
        );
        assert_eq!(report.regressions, vec!["down".to_string()]);
    }
}
