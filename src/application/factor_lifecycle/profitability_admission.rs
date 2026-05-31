use serde::{Deserialize, Serialize};

pub const DEFAULT_REGIME_CONFIDENCE_FLOOR: f64 = 0.95;
pub const FLYWHEEL_REGIME_CONFIDENCE_FLOOR: f64 = 0.75;
pub const LIVE_EXECUTION_READINESS_FLOOR: f64 = 0.45;
pub const PAPER_VALIDATION_MIN_ROWS: usize = 30;
pub const DEPLOY_READY_READINESS_CONTRACT: &str =
    "deploy_ready_from_backtest_autoquant_provider_or_paper_sim_execution_chain_not_funded_fill";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AdmissionStatus {
    NotEvaluated,
    Admitted,
    Ready,
    Observe,
    Blocked,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProviderEvidenceState {
    Ready,
    RetainedReal,
    LocalResearch,
    Blocked,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct ValidationRows {
    pub raw_scored_mature: usize,
    pub production: usize,
    pub observation: usize,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProfitabilityAdmissionInput {
    pub regime_confidence: Option<f64>,
    pub regime_confidence_floor: f64,
    pub long_run_expectancy_after_declared_friction: Option<f64>,
    pub evidence_count: usize,
    pub leakage_passed: bool,
    pub provider_state: ProviderEvidenceState,
    pub market_data_provenance_verified: bool,
    pub retained_session_scope_verified: bool,
    pub promotion_cost_verified: bool,
    pub accepted_execution_feedback: bool,
    pub execution_readiness: Option<f64>,
    pub transition_hazard: Option<f64>,
    pub pda_hybrid_alignment: Option<bool>,
    pub pre_bayes_gate_status: Option<String>,
    pub execution_gate_status: Option<String>,
    pub execution_tree_gate_status: Option<String>,
    pub execution_tree_branch: Option<String>,
    pub path_ranker_score_used_by_execution_tree: bool,
    pub ranker_validation_ready: bool,
    pub validation_rows: ValidationRows,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AdmissionPlaneDecision {
    pub status: AdmissionStatus,
    pub blockers: Vec<String>,
}

impl AdmissionPlaneDecision {
    pub fn not_evaluated() -> Self {
        Self {
            status: AdmissionStatus::NotEvaluated,
            blockers: Vec::new(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct LiveTradeDecision {
    pub status: AdmissionStatus,
    pub blockers: Vec<String>,
    pub paper_feedback_collection_ready: bool,
    pub paper_feedback_collection_blockers: Vec<String>,
    pub deploy_ready: bool,
    pub funded_live_fill_required: bool,
    pub readiness_contract: String,
    pub promotion_allowed: bool,
    pub trade_usable: bool,
    pub update_goal: bool,
}

impl LiveTradeDecision {
    pub fn promotion_allowed(&self) -> bool {
        self.promotion_allowed
    }

    pub fn trade_usable(&self) -> bool {
        self.trade_usable
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProfitabilityLifecycleDecision {
    pub learning: AdmissionPlaneDecision,
    pub paper: AdmissionPlaneDecision,
    pub live: LiveTradeDecision,
}

pub fn decide_profitability_lifecycle(
    input: &ProfitabilityAdmissionInput,
) -> ProfitabilityLifecycleDecision {
    let learning_regime_confidence_floor = input
        .regime_confidence_floor
        .min(FLYWHEEL_REGIME_CONFIDENCE_FLOOR);
    let mut learning_blockers = Vec::new();
    match input.regime_confidence {
        Some(confidence) if confidence >= learning_regime_confidence_floor => {}
        Some(_) => learning_blockers.push("regime_confidence_below_floor".to_string()),
        None => learning_blockers.push("regime_confidence_missing".to_string()),
    }
    match input.long_run_expectancy_after_declared_friction {
        Some(expectancy) if expectancy > 0.0 => {}
        Some(_) => learning_blockers.push("non_positive_expectancy_after_friction".to_string()),
        None => learning_blockers.push("expectancy_after_friction_missing".to_string()),
    }
    if !input.leakage_passed {
        learning_blockers.push("leakage_check_failed".to_string());
    }
    if input.evidence_count == 0 {
        learning_blockers.push("evidence_count_zero".to_string());
    }
    if input.provider_state == ProviderEvidenceState::Blocked {
        learning_blockers.push("provider_evidence_blocked".to_string());
    }

    let learning_admitted = learning_blockers.is_empty();
    let learning = AdmissionPlaneDecision {
        status: if learning_admitted {
            AdmissionStatus::Admitted
        } else {
            AdmissionStatus::Blocked
        },
        blockers: learning_blockers,
    };

    let mut paper_blockers = Vec::new();
    if !learning_admitted {
        paper_blockers.push("learning_not_admitted".to_string());
    }
    if input.validation_rows.raw_scored_mature < PAPER_VALIDATION_MIN_ROWS {
        paper_blockers.push("raw_scored_mature_below_paper_floor".to_string());
    }
    if input.validation_rows.production < PAPER_VALIDATION_MIN_ROWS {
        paper_blockers.push("production_validation_below_paper_floor".to_string());
    }
    if input.validation_rows.observation < PAPER_VALIDATION_MIN_ROWS {
        paper_blockers.push("observation_validation_below_paper_floor".to_string());
    }
    let paper_ready = learning_admitted && paper_blockers.is_empty();
    let paper = AdmissionPlaneDecision {
        status: if paper_ready {
            AdmissionStatus::Ready
        } else {
            AdmissionStatus::Observe
        },
        blockers: paper_blockers,
    };

    let mut feedback_collection_blockers = Vec::new();
    if !paper_ready {
        feedback_collection_blockers.push("paper_not_ready".to_string());
    }
    if !input.market_data_provenance_verified {
        feedback_collection_blockers.push("market_data_provenance_unverified".to_string());
    }
    match input.execution_readiness {
        Some(readiness) if readiness >= LIVE_EXECUTION_READINESS_FLOOR => {}
        Some(_) => {
            feedback_collection_blockers.push("execution_readiness_below_live_floor".to_string())
        }
        None => feedback_collection_blockers.push("execution_readiness_missing".to_string()),
    }
    match input.execution_gate_status.as_deref().map(str::trim) {
        Some("ready" | "execution_ready" | "pass" | "admissible") => {}
        Some(_) => feedback_collection_blockers.push("execution_gate_status_not_ready".to_string()),
        None => feedback_collection_blockers.push("execution_gate_status_missing".to_string()),
    }
    let live_plane_artifact_missing = input.pre_bayes_gate_status.is_none()
        && input.execution_tree_gate_status.is_none()
        && input.execution_tree_branch.is_none()
        && !input.path_ranker_score_used_by_execution_tree
        && !input.ranker_validation_ready;
    if live_plane_artifact_missing {
        feedback_collection_blockers.push("live_plane_artifact_missing".to_string());
    }
    match input.pre_bayes_gate_status.as_deref().map(str::trim) {
        Some("pass_hard" | "pass_neutralized") => {}
        Some(_) => feedback_collection_blockers.push("pre_bayes_gate_status_not_ready".to_string()),
        None => feedback_collection_blockers.push("pre_bayes_gate_status_missing".to_string()),
    }
    match input.execution_tree_gate_status.as_deref().map(str::trim) {
        Some("ready") => {}
        Some(_) => {
            feedback_collection_blockers.push("execution_tree_gate_status_not_ready".to_string())
        }
        None => feedback_collection_blockers.push("execution_tree_gate_status_missing".to_string()),
    }
    match input.execution_tree_branch.as_deref().map(str::trim) {
        Some("fill_viable") => {}
        Some(_) => {
            feedback_collection_blockers.push("execution_tree_branch_not_live_ready".to_string())
        }
        None => feedback_collection_blockers.push("execution_tree_branch_missing".to_string()),
    }
    if !input.path_ranker_score_used_by_execution_tree {
        feedback_collection_blockers
            .push("path_ranker_score_not_used_by_execution_tree".to_string());
    }
    if !input.ranker_validation_ready {
        feedback_collection_blockers.push("ranker_validation_not_ready".to_string());
    }
    let paper_feedback_collection_ready = paper_ready && feedback_collection_blockers.is_empty();
    let mut live_blockers = feedback_collection_blockers.clone();
    if !input.retained_session_scope_verified {
        live_blockers.push("retained_session_scope_unverified".to_string());
    }
    if !input.promotion_cost_verified {
        live_blockers.push("promotion_cost_unverified".to_string());
    }
    if !input.accepted_execution_feedback {
        live_blockers.push("accepted_execution_feedback_missing".to_string());
    }
    let strict_live_regime_confidence_passed = match input.regime_confidence {
        Some(confidence) if confidence >= input.regime_confidence_floor => true,
        Some(_) => {
            live_blockers.push("regime_confidence_below_live_floor".to_string());
            false
        }
        None => {
            live_blockers.push("regime_confidence_missing_for_live_floor".to_string());
            false
        }
    };
    let live_ready = paper_feedback_collection_ready
        && input.retained_session_scope_verified
        && input.promotion_cost_verified
        && input.accepted_execution_feedback
        && strict_live_regime_confidence_passed;
    let live = LiveTradeDecision {
        status: if live_ready {
            AdmissionStatus::Ready
        } else {
            AdmissionStatus::Blocked
        },
        blockers: live_blockers,
        paper_feedback_collection_ready,
        paper_feedback_collection_blockers: feedback_collection_blockers,
        deploy_ready: live_ready,
        funded_live_fill_required: false,
        readiness_contract: DEPLOY_READY_READINESS_CONTRACT.to_string(),
        promotion_allowed: live_ready,
        trade_usable: live_ready,
        update_goal: live_ready,
    };

    ProfitabilityLifecycleDecision {
        learning,
        paper,
        live,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn learning_admits_regime_conditioned_positive_expectancy_even_when_live_blocked() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.96),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.004),
            evidence_count: 8,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.41),
            transition_hazard: Some(0.72),
            pda_hybrid_alignment: Some(false),
            pre_bayes_gate_status: Some("pass_neutralized".to_string()),
            execution_gate_status: Some("blocked".to_string()),
            execution_tree_gate_status: Some("blocked".to_string()),
            execution_tree_branch: Some("block_crowded".to_string()),
            path_ranker_score_used_by_execution_tree: false,
            ranker_validation_ready: false,
            validation_rows: ValidationRows {
                raw_scored_mature: 8,
                production: 8,
                observation: 8,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Observe);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
    }

    #[test]
    fn learning_blocks_when_regime_confidence_is_missing_or_wrong() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.62),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.02),
            evidence_count: 40,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.80),
            transition_hazard: Some(0.20),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 40,
                production: 40,
                observation: 40,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Blocked);
        assert!(decision
            .learning
            .blockers
            .contains(&"regime_confidence_below_floor".to_string()));
        assert!(!decision.live.trade_usable);
    }

    #[test]
    fn learning_blocks_without_any_evidence_rows() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.97),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.01),
            evidence_count: 0,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::RetainedReal,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.80),
            transition_hazard: Some(0.20),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 40,
                production: 40,
                observation: 40,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Blocked);
        assert!(decision
            .learning
            .blockers
            .contains(&"evidence_count_zero".to_string()));
        assert_eq!(decision.paper.status, AdmissionStatus::Observe);
        assert!(!decision.live.trade_usable);
    }

    #[test]
    fn flywheel_learning_admits_moderate_regime_confidence_without_live_promotion() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.80),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.018),
            evidence_count: 36,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: false,
            execution_readiness: Some(0.83),
            transition_hazard: Some(0.40),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 36,
                production: 36,
                observation: 36,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert!(decision.live.paper_feedback_collection_ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision
            .live
            .blockers
            .contains(&"accepted_execution_feedback_missing".to_string()));
        assert!(decision
            .live
            .blockers
            .contains(&"regime_confidence_below_live_floor".to_string()));
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
    }

    #[test]
    fn accepted_feedback_cannot_promote_below_strict_live_regime_floor() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.80),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.018),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.83),
            transition_hazard: Some(0.40),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision
            .live
            .blockers
            .contains(&"regime_confidence_below_live_floor".to_string()));
        assert!(!decision.live.deploy_ready);
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
    }

    #[test]
    fn lifecycle_decision_serializes_as_snake_case_planes() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.98),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.012),
            evidence_count: 35,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.80),
            transition_hazard: Some(0.99),
            pda_hybrid_alignment: Some(false),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 35,
                production: 35,
                observation: 35,
            },
        };

        let decision = decide_profitability_lifecycle(&input);
        let value = serde_json::to_value(&decision).unwrap();

        assert_eq!(value["learning"]["status"], "admitted");
        assert_eq!(value["paper"]["status"], "ready");
        assert_eq!(value["live"]["status"], "ready");
        assert_eq!(value["live"]["deploy_ready"], true);
        assert_eq!(value["live"]["funded_live_fill_required"], false);
        assert_eq!(
            value["live"]["readiness_contract"],
            DEPLOY_READY_READINESS_CONTRACT
        );
        assert_eq!(value["live"]["promotion_allowed"], true);
        assert_eq!(value["live"]["trade_usable"], true);
        assert!(value["learning"].get("promotion_allowed").is_none());
        assert!(value["paper"].get("trade_usable").is_none());
    }

    #[test]
    fn lifecycle_blocks_live_without_practical_closure_evidence_planes() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.98),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.012),
            evidence_count: 35,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: false,
            retained_session_scope_verified: false,
            promotion_cost_verified: false,
            accepted_execution_feedback: false,
            execution_readiness: Some(0.80),
            transition_hazard: Some(0.99),
            pda_hybrid_alignment: Some(false),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 35,
                production: 35,
                observation: 35,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        for blocker in [
            "market_data_provenance_unverified",
            "retained_session_scope_unverified",
            "promotion_cost_unverified",
            "accepted_execution_feedback_missing",
        ] {
            assert!(decision.live.blockers.contains(&blocker.to_string()));
        }
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
        assert!(!decision.live.paper_feedback_collection_ready);
        assert!(decision
            .live
            .paper_feedback_collection_blockers
            .contains(&"market_data_provenance_unverified".to_string()));
    }

    #[test]
    fn lifecycle_allows_paper_feedback_collection_before_accepted_execution_feedback() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.99),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.03),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: false,
            execution_readiness: Some(0.91),
            transition_hazard: Some(0.10),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision.live.paper_feedback_collection_ready);
        assert!(decision.live.paper_feedback_collection_blockers.is_empty());
        assert!(decision
            .live
            .blockers
            .contains(&"accepted_execution_feedback_missing".to_string()));
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
    }

    #[test]
    fn lifecycle_allows_paper_feedback_collection_with_cost_session_verification_debt() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.99),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.03),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: false,
            promotion_cost_verified: false,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.91),
            transition_hazard: Some(0.10),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert!(decision.live.paper_feedback_collection_ready);
        assert!(decision.live.paper_feedback_collection_blockers.is_empty());
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision
            .live
            .blockers
            .contains(&"retained_session_scope_unverified".to_string()));
        assert!(decision
            .live
            .blockers
            .contains(&"promotion_cost_unverified".to_string()));
        assert!(!decision
            .live
            .blockers
            .contains(&"accepted_execution_feedback_missing".to_string()));
        assert!(!decision.live.deploy_ready);
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
    }

    #[test]
    fn lifecycle_does_not_use_transition_hazard_as_live_blocker() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.98),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.012),
            evidence_count: 35,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.80),
            transition_hazard: None,
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 35,
                production: 35,
                observation: 35,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Ready);
        assert!(decision.live.promotion_allowed);
        assert!(decision.live.trade_usable);
        assert!(!decision
            .live
            .blockers
            .iter()
            .any(|blocker| blocker.contains("transition_hazard")));
    }

    #[test]
    fn lifecycle_uses_not_evaluated_and_blocks_live_without_execution_gate_ready() {
        let not_evaluated = AdmissionPlaneDecision::not_evaluated();
        assert_eq!(not_evaluated.status, AdmissionStatus::NotEvaluated);

        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.99),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.03),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.91),
            transition_hazard: Some(0.10),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("observe".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision
            .live
            .blockers
            .contains(&"execution_gate_status_not_ready".to_string()));
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
    }

    #[test]
    fn lifecycle_blocks_live_when_only_legacy_execution_gate_is_ready() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.99),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.03),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.91),
            transition_hazard: Some(0.10),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: None,
            execution_gate_status: Some("pass".to_string()),
            execution_tree_gate_status: None,
            execution_tree_branch: None,
            path_ranker_score_used_by_execution_tree: false,
            ranker_validation_ready: false,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Blocked);
        assert!(decision
            .live
            .blockers
            .contains(&"live_plane_artifact_missing".to_string()));
        assert!(!decision.live.promotion_allowed);
        assert!(!decision.live.trade_usable);
        assert!(!decision.live.update_goal);
    }

    #[test]
    fn lifecycle_accepts_observe_band_execution_readiness_for_live_plane() {
        let input = ProfitabilityAdmissionInput {
            regime_confidence: Some(0.99),
            regime_confidence_floor: 0.95,
            long_run_expectancy_after_declared_friction: Some(0.03),
            evidence_count: 80,
            leakage_passed: true,
            provider_state: ProviderEvidenceState::Ready,
            market_data_provenance_verified: true,
            retained_session_scope_verified: true,
            promotion_cost_verified: true,
            accepted_execution_feedback: true,
            execution_readiness: Some(0.45),
            transition_hazard: Some(0.10),
            pda_hybrid_alignment: Some(true),
            pre_bayes_gate_status: Some("pass_hard".to_string()),
            execution_gate_status: Some("ready".to_string()),
            execution_tree_gate_status: Some("ready".to_string()),
            execution_tree_branch: Some("fill_viable".to_string()),
            path_ranker_score_used_by_execution_tree: true,
            ranker_validation_ready: true,
            validation_rows: ValidationRows {
                raw_scored_mature: 80,
                production: 80,
                observation: 80,
            },
        };

        let decision = decide_profitability_lifecycle(&input);

        assert_eq!(decision.learning.status, AdmissionStatus::Admitted);
        assert_eq!(decision.paper.status, AdmissionStatus::Ready);
        assert_eq!(decision.live.status, AdmissionStatus::Ready);
        assert!(decision.live.promotion_allowed);
        assert!(decision.live.trade_usable);
        assert!(decision.live.update_goal);
    }
}
