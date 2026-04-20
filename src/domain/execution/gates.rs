pub const EXECUTION_GATE_READY: f64 = 0.65;
pub const EXECUTION_GATE_OBSERVE: f64 = 0.45;

pub fn classify_execution_gate(readiness: f64) -> &'static str {
    if readiness >= EXECUTION_GATE_READY {
        "execution_ready"
    } else if readiness >= EXECUTION_GATE_OBSERVE {
        "execution_observe_only"
    } else {
        "execution_blocked"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn classifies_execution_gates_from_shared_thresholds() {
        assert_eq!(
            classify_execution_gate(EXECUTION_GATE_READY),
            "execution_ready"
        );
        assert_eq!(
            classify_execution_gate(EXECUTION_GATE_OBSERVE),
            "execution_observe_only"
        );
        assert_eq!(
            classify_execution_gate(EXECUTION_GATE_OBSERVE - 0.01),
            "execution_blocked"
        );
    }
}
