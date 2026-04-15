use serde::Serialize;

use super::{build_postmortem_artifact, build_prior_artifact, PostmortemArtifact, PriorArtifact};

#[derive(Debug, Clone, Serialize, Default)]
pub struct ReflectionBundle {
    pub prior: PriorArtifact,
    pub postmortem: PostmortemArtifact,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ensemble_vote_summary: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ensemble_vote_artifact_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ensemble_disagreement_summary: Option<String>,
}

pub fn build_reflection_bundle(
    symbol: impl Into<String>,
    timestamp: impl Into<String>,
    objective: impl Into<String>,
    expected_regime: impl Into<String>,
    expected_direction: impl Into<String>,
    realized_outcome: impl Into<String>,
    evidence: &[String],
    next_candidates: &[String],
) -> ReflectionBundle {
    let symbol = symbol.into();
    let timestamp = timestamp.into();
    let objective = objective.into();
    let expected_regime = expected_regime.into();
    let expected_direction = expected_direction.into();
    let realized_outcome = realized_outcome.into();

    ReflectionBundle {
        prior: build_prior_artifact(
            symbol.clone(),
            timestamp.clone(),
            objective,
            expected_regime,
            expected_direction,
            evidence,
            next_candidates,
            "fresh_required",
            next_candidates,
        ),
        postmortem: build_postmortem_artifact(
            symbol,
            timestamp,
            "unknown_expected_outcome",
            realized_outcome,
            next_candidates,
            evidence,
            evidence,
            next_candidates,
            next_candidates,
        ),
        ensemble_vote_summary: None,
        ensemble_vote_artifact_id: None,
        ensemble_disagreement_summary: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reflection_bundle_contains_prior_and_postmortem() {
        let bundle = build_reflection_bundle(
            "NQ",
            "2026-01-01T00:00:00Z",
            "generic",
            "bull",
            "long",
            "win",
            &["e1".to_string()],
            &["n1".to_string()],
        );
        assert_eq!(bundle.prior.symbol, "NQ");
        assert_eq!(bundle.postmortem.realized_outcome, "win");
    }
}
