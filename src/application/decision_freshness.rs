use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct DecisionFreshnessGate {
    pub status: String,
    pub reason: String,
    pub max_age_seconds: i64,
    pub observed_age_seconds: i64,
}

pub fn build_decision_freshness_gate(
    max_age_seconds: i64,
    observed_age_seconds: i64,
) -> DecisionFreshnessGate {
    let status = if observed_age_seconds <= max_age_seconds {
        "fresh"
    } else if observed_age_seconds <= max_age_seconds * 2 {
        "aging"
    } else {
        "stale"
    };
    let reason = format!(
        "observed_age_seconds={} max_age_seconds={}",
        observed_age_seconds, max_age_seconds
    );
    DecisionFreshnessGate {
        status: status.to_string(),
        reason,
        max_age_seconds,
        observed_age_seconds,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn freshness_gate_marks_stale() {
        let gate = build_decision_freshness_gate(300, 900);
        assert_eq!(gate.status, "stale");
    }
}
