use crate::state::{
    AnalyzeRunRecord, BacktestRunRecord, ResearchRunRecord, UpdateRunRecord, WorkflowPhaseSnapshot,
};

pub fn apply_execution_fields_to_workflow_phase(
    phase: &mut WorkflowPhaseSnapshot,
    execution_edge_share: Option<f64>,
    prediction_edge_share: Option<f64>,
    execution_readiness: Option<f64>,
    execution_gate_status: Option<String>,
) {
    phase.execution_edge_share = execution_edge_share;
    phase.prediction_edge_share = prediction_edge_share;
    phase.execution_readiness = execution_readiness;
    phase.execution_gate_status = execution_gate_status;
}

pub fn apply_analyze_run_execution_fields(
    phase: &mut WorkflowPhaseSnapshot,
    run: &AnalyzeRunRecord,
) {
    apply_execution_fields_to_workflow_phase(
        phase,
        run.execution_edge_share,
        run.prediction_edge_share,
        run.execution_readiness,
        run.execution_gate_status.clone(),
    );
}

pub fn apply_research_run_execution_fields(
    phase: &mut WorkflowPhaseSnapshot,
    run: &ResearchRunRecord,
) {
    apply_execution_fields_to_workflow_phase(
        phase,
        run.execution_edge_share,
        run.prediction_edge_share,
        run.execution_readiness,
        run.execution_gate_status.clone(),
    );
}

pub fn apply_backtest_run_execution_fields(
    phase: &mut WorkflowPhaseSnapshot,
    run: &BacktestRunRecord,
) {
    apply_execution_fields_to_workflow_phase(
        phase,
        run.execution_edge_share,
        run.prediction_edge_share,
        run.execution_readiness,
        run.execution_gate_status.clone(),
    );
}

pub fn apply_update_run_execution_fields(phase: &mut WorkflowPhaseSnapshot, run: &UpdateRunRecord) {
    apply_execution_fields_to_workflow_phase(
        phase,
        run.execution_edge_share,
        run.prediction_edge_share,
        run.execution_readiness,
        run.execution_gate_status.clone(),
    );
}

pub fn execution_phase_summary_suffix(phase: &WorkflowPhaseSnapshot) -> String {
    match (
        phase.execution_readiness,
        phase.execution_gate_status.as_deref(),
        phase.execution_edge_share,
    ) {
        (Some(readiness), Some(gate), Some(edge)) => {
            format!(" execution_readiness={readiness:.3} execution_gate={gate} execution_edge={edge:.3}")
        }
        (Some(readiness), Some(gate), None) => {
            format!(" execution_readiness={readiness:.3} execution_gate={gate}")
        }
        _ => String::new(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::WorkflowPhaseSnapshot;

    #[test]
    fn workflow_execution_suffix_is_empty_without_execution_fields() {
        let phase = WorkflowPhaseSnapshot::default();
        assert!(execution_phase_summary_suffix(&phase).is_empty());
    }

    #[test]
    fn workflow_execution_suffix_renders_when_fields_exist() {
        let mut phase = WorkflowPhaseSnapshot::default();
        apply_execution_fields_to_workflow_phase(
            &mut phase,
            Some(0.7),
            Some(0.3),
            Some(0.81),
            Some("execution_ready".to_string()),
        );
        let rendered = execution_phase_summary_suffix(&phase);
        assert!(rendered.contains("execution_readiness=0.810"));
        assert!(rendered.contains("execution_gate=execution_ready"));
        assert!(rendered.contains("execution_edge=0.700"));
    }

    #[test]
    fn research_workflow_fields_are_read_from_record() {
        let mut phase = WorkflowPhaseSnapshot::default();
        let run = ResearchRunRecord {
            execution_edge_share: Some(0.61),
            prediction_edge_share: Some(0.39),
            execution_readiness: Some(0.71),
            execution_gate_status: Some("execution_ready".to_string()),
            ..ResearchRunRecord::default()
        };

        apply_research_run_execution_fields(&mut phase, &run);

        assert_eq!(phase.execution_edge_share, Some(0.61));
        assert_eq!(phase.prediction_edge_share, Some(0.39));
        assert_eq!(phase.execution_readiness, Some(0.71));
        assert_eq!(
            phase.execution_gate_status.as_deref(),
            Some("execution_ready")
        );
    }
}
