use crate::factor_lab::research::ResearchReport;

use super::{build_reflection_bundle, ReflectionBundle};

pub fn build_research_reflection_bundle(symbol: &str, report: &ResearchReport) -> ReflectionBundle {
    let next_candidates = if report.recommended_next_command.is_empty() {
        vec![format!(
            "research={}",
            report.recommended_commands.research.command
        )]
    } else {
        vec![report.recommended_next_command.clone()]
    };

    build_reflection_bundle(
        symbol,
        report.provenance.data_fingerprint.clone(),
        report.research_objective.clone(),
        report
            .artifact_decision_summary
            .consumed_trend_status
            .clone(),
        report
            .best_factor
            .clone()
            .unwrap_or_else(|| "unknown".to_string()),
        "research_completed",
        &report.multi_timeframe_summary,
        &next_candidates,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn research_adapter_builds_bundle() {
        let report = ResearchReport {
            research_objective: "generic".to_string(),
            best_factor: Some("trend_momentum".to_string()),
            multi_timeframe_summary: vec!["mtf=bullish".to_string()],
            ..ResearchReport::default()
        };
        let bundle = build_research_reflection_bundle("NQ", &report);
        assert_eq!(bundle.prior.symbol, "NQ");
        assert_eq!(bundle.postmortem.realized_outcome, "research_completed");
    }
}
