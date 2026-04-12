use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct PriorArtifact {
    pub symbol: String,
    pub timestamp: String,
    pub objective: String,
    pub expected_regime: String,
    pub expected_direction: String,
    pub expected_key_evidence: Vec<String>,
    pub invalidation_conditions: Vec<String>,
    pub freshness_expectation: String,
    pub notes: Vec<String>,
}

pub fn build_prior_artifact(
    symbol: impl Into<String>,
    timestamp: impl Into<String>,
    objective: impl Into<String>,
    expected_regime: impl Into<String>,
    expected_direction: impl Into<String>,
    expected_key_evidence: &[String],
    invalidation_conditions: &[String],
    freshness_expectation: impl Into<String>,
    notes: &[String],
) -> PriorArtifact {
    PriorArtifact {
        symbol: symbol.into(),
        timestamp: timestamp.into(),
        objective: objective.into(),
        expected_regime: expected_regime.into(),
        expected_direction: expected_direction.into(),
        expected_key_evidence: expected_key_evidence.to_vec(),
        invalidation_conditions: invalidation_conditions.to_vec(),
        freshness_expectation: freshness_expectation.into(),
        notes: notes.to_vec(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn prior_builder_keeps_symbol_and_objective() {
        let artifact = build_prior_artifact(
            "NQ",
            "2026-01-01T00:00:00Z",
            "expansion_manipulation",
            "bull",
            "long",
            &["e1".to_string()],
            &["i1".to_string()],
            "fresh",
            &["n1".to_string()],
        );
        assert_eq!(artifact.symbol, "NQ");
        assert_eq!(artifact.objective, "expansion_manipulation");
    }
}
