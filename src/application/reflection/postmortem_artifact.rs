use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct PostmortemArtifact {
    pub symbol: String,
    pub timestamp: String,
    pub expected_outcome: String,
    pub realized_outcome: String,
    pub deviations: Vec<String>,
    pub evidence_drift: Vec<String>,
    pub what_worked: Vec<String>,
    pub what_failed: Vec<String>,
    pub next_candidates: Vec<String>,
}

pub fn build_postmortem_artifact(
    symbol: impl Into<String>,
    timestamp: impl Into<String>,
    expected_outcome: impl Into<String>,
    realized_outcome: impl Into<String>,
    deviations: &[String],
    evidence_drift: &[String],
    what_worked: &[String],
    what_failed: &[String],
    next_candidates: &[String],
) -> PostmortemArtifact {
    PostmortemArtifact {
        symbol: symbol.into(),
        timestamp: timestamp.into(),
        expected_outcome: expected_outcome.into(),
        realized_outcome: realized_outcome.into(),
        deviations: deviations.to_vec(),
        evidence_drift: evidence_drift.to_vec(),
        what_worked: what_worked.to_vec(),
        what_failed: what_failed.to_vec(),
        next_candidates: next_candidates.to_vec(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn postmortem_builder_keeps_outcomes() {
        let artifact = build_postmortem_artifact(
            "NQ",
            "2026-01-01T00:00:00Z",
            "win",
            "loss",
            &["d1".to_string()],
            &["e1".to_string()],
            &["w1".to_string()],
            &["f1".to_string()],
            &["n1".to_string()],
        );
        assert_eq!(artifact.expected_outcome, "win");
        assert_eq!(artifact.realized_outcome, "loss");
    }
}
