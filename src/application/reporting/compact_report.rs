use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct CompactAnalyzeReport {
    pub verdict: String,
    pub direction: Option<String>,
    pub entry_state: Option<String>,
    pub pre_bayes_gate: Option<String>,
    pub next_command: Option<String>,
    pub evidence: Vec<String>,
    pub risks: Vec<String>,
    pub next_actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct CompactBacktestReport {
    pub summary: String,
    pub highlights: Vec<String>,
    pub risks: Vec<String>,
    pub next_actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct CompactReflectionReport {
    pub summary: String,
    pub findings: Vec<String>,
    pub risks: Vec<String>,
    pub next_actions: Vec<String>,
}

fn top_k(items: &[String], limit: usize) -> Vec<String> {
    items.iter().take(limit).cloned().collect()
}

pub fn build_compact_analyze_report(
    verdict: impl Into<String>,
    direction: Option<String>,
    entry_state: Option<String>,
    pre_bayes_gate: Option<String>,
    next_command: Option<String>,
    evidence: &[String],
    risks: &[String],
    next_actions: &[String],
) -> CompactAnalyzeReport {
    CompactAnalyzeReport {
        verdict: verdict.into(),
        direction,
        entry_state,
        pre_bayes_gate,
        next_command,
        evidence: top_k(evidence, 5),
        risks: top_k(risks, 5),
        next_actions: top_k(next_actions, 5),
    }
}

pub fn build_compact_backtest_report(
    summary: impl Into<String>,
    highlights: &[String],
    risks: &[String],
    next_actions: &[String],
) -> CompactBacktestReport {
    CompactBacktestReport {
        summary: summary.into(),
        highlights: top_k(highlights, 5),
        risks: top_k(risks, 5),
        next_actions: top_k(next_actions, 5),
    }
}

pub fn build_compact_reflection_report(
    summary: impl Into<String>,
    findings: &[String],
    risks: &[String],
    next_actions: &[String],
) -> CompactReflectionReport {
    CompactReflectionReport {
        summary: summary.into(),
        findings: top_k(findings, 5),
        risks: top_k(risks, 5),
        next_actions: top_k(next_actions, 5),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compact_analyze_report_limits_lists() {
        let items = vec![
            "a".to_string(),
            "b".to_string(),
            "c".to_string(),
            "d".to_string(),
            "e".to_string(),
            "f".to_string(),
        ];
        let report = build_compact_analyze_report(
            "ok",
            Some("bull".to_string()),
            Some("medium".to_string()),
            Some("observe_only".to_string()),
            Some("next".to_string()),
            &items,
            &items,
            &items,
        );
        assert_eq!(report.direction.as_deref(), Some("bull"));
        assert_eq!(report.entry_state.as_deref(), Some("medium"));
        assert_eq!(report.pre_bayes_gate.as_deref(), Some("observe_only"));
        assert_eq!(report.next_command.as_deref(), Some("next"));
        assert_eq!(report.evidence.len(), 5);
        assert_eq!(report.risks.len(), 5);
        assert_eq!(report.next_actions.len(), 5);
    }

    #[test]
    fn compact_backtest_report_limits_lists() {
        let items = vec![
            "a".to_string(),
            "b".to_string(),
            "c".to_string(),
            "d".to_string(),
            "e".to_string(),
            "f".to_string(),
        ];
        let report = build_compact_backtest_report("ok", &items, &items, &items);
        assert_eq!(report.highlights.len(), 5);
        assert_eq!(report.risks.len(), 5);
        assert_eq!(report.next_actions.len(), 5);
    }
}
