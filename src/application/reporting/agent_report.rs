use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct AgentGuidanceReport {
    pub summary: String,
    pub evidence: Vec<String>,
    pub risks: Vec<String>,
    pub recommended_next_actions: Vec<String>,
    pub artifact_links: Vec<String>,
}

fn top_k(items: &[String], limit: usize) -> Vec<String> {
    items.iter().take(limit).cloned().collect()
}

pub fn build_agent_guidance_report(
    summary: impl Into<String>,
    evidence: &[String],
    risks: &[String],
    recommended_next_actions: &[String],
    artifact_links: &[String],
) -> AgentGuidanceReport {
    AgentGuidanceReport {
        summary: summary.into(),
        evidence: top_k(evidence, 5),
        risks: top_k(risks, 5),
        recommended_next_actions: top_k(recommended_next_actions, 5),
        artifact_links: top_k(artifact_links, 5),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn agent_guidance_has_next_actions() {
        let report = build_agent_guidance_report(
            "summary",
            &["e1".to_string()],
            &["r1".to_string()],
            &["n1".to_string()],
            &["a1".to_string()],
        );
        assert_eq!(report.recommended_next_actions, vec!["n1".to_string()]);
    }
}
