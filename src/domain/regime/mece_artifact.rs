use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::state::RunProvenance;

/// Hard-gate threshold used by `classify_mece_recovery_gate` and the artifact
/// ledger. Sprint 3 acceptance condition: an MECE recovery report is only
/// allowed to promote downstream artifacts when accuracy >= this value.
pub const MECE_RECOVERY_ACCURACY_GATE: f64 = 0.95;

/// Persistent record of an MECE recovery run. Carries the accuracy / macro_f1
/// pair, the selected factor subset, and stable hashes of the underlying HMM
/// Viterbi path + label sequence so reruns can be diffed bit-for-bit. The
/// `execution_validity_summary` line preserves the dual constraint
/// (regime recovery only counts when execution coverage is non-degenerate)
/// directly inside the ledger row.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MeceRecoveryArtifact {
    pub artifact_id: String,
    pub generated_at: DateTime<Utc>,
    pub symbol: String,
    pub accuracy: f64,
    pub macro_f1: f64,
    pub selected_factors: Vec<String>,
    pub hmm_viterbi_hash: String,
    pub label_hash: String,
    pub execution_validity_summary: String,
    pub provenance: RunProvenance,
}

pub fn classify_mece_recovery_gate(accuracy: f64) -> &'static str {
    if accuracy >= MECE_RECOVERY_ACCURACY_GATE {
        "promote"
    } else {
        "blocked"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn promotes_at_or_above_threshold() {
        assert_eq!(
            classify_mece_recovery_gate(MECE_RECOVERY_ACCURACY_GATE),
            "promote"
        );
        assert_eq!(classify_mece_recovery_gate(0.99), "promote");
    }

    #[test]
    fn blocks_below_threshold() {
        assert_eq!(
            classify_mece_recovery_gate(MECE_RECOVERY_ACCURACY_GATE - 0.0001),
            "blocked"
        );
        assert_eq!(classify_mece_recovery_gate(0.0), "blocked");
    }
}
