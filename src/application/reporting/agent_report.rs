use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct AgentGuidanceReport {
    pub direction: Option<String>,
    pub entry_state: Option<String>,
    pub pre_bayes_gate: Option<String>,
    pub next_command: Option<String>,
    pub decision: Option<String>,
    pub evidence: Vec<String>,
    pub risks: Vec<String>,
    pub recommended_next_actions: Vec<String>,
}

fn top_k(items: &[String], limit: usize) -> Vec<String> {
    items.iter().take(limit).cloned().collect()
}

pub fn build_agent_guidance_report(
    direction: Option<String>,
    entry_state: Option<String>,
    pre_bayes_gate: Option<String>,
    next_command: Option<String>,
    decision: Option<String>,
    evidence: &[String],
    risks: &[String],
    recommended_next_actions: &[String],
) -> AgentGuidanceReport {
    AgentGuidanceReport {
        direction,
        entry_state,
        pre_bayes_gate,
        next_command,
        decision,
        evidence: top_k(evidence, 3),
        risks: top_k(risks, 3),
        recommended_next_actions: top_k(recommended_next_actions, 3),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn agent_guidance_has_next_actions() {
        let items = vec![
            "a".to_string(),
            "b".to_string(),
            "c".to_string(),
            "d".to_string(),
        ];
        let report = build_agent_guidance_report(
            Some("Bull".to_string()),
            Some("medium".to_string()),
            Some("observe_only".to_string()),
            Some("next".to_string()),
            Some("tune structure_ict".to_string()),
            &items,
            &items,
            &["n1".to_string()],
        );
        assert_eq!(report.direction.as_deref(), Some("Bull"));
        assert_eq!(report.entry_state.as_deref(), Some("medium"));
        assert_eq!(report.pre_bayes_gate.as_deref(), Some("observe_only"));
        assert_eq!(report.next_command.as_deref(), Some("next"));
        assert_eq!(report.decision.as_deref(), Some("tune structure_ict"));
        assert_eq!(report.evidence.len(), 3);
        assert_eq!(report.recommended_next_actions, vec!["n1".to_string()]);
    }
}
