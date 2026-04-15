use crate::bbn::temporal::ParticleBeliefSummary;
use crate::domain::regime::{
    JumpModelRegimeSummary, RegimeDisagreementSummary, RegimeFeatures, RegimeGateDecision,
    RegimePosterior,
};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BeliefEvidencePacket {
    pub symbol: String,
    pub market: Option<String>,
    pub timestamp: Option<String>,
    pub entry_logic_id: Option<String>,
    pub logic_family: Option<String>,
    pub regime_features: RegimeFeatures,
    pub market_evidence: Vec<String>,
    pub factor_evidence: Vec<String>,
    pub timed_pda_summary: BTreeMap<String, String>,
    pub multi_timeframe_evidence: BTreeMap<String, String>,
    pub evidence_assignments: BTreeMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct CredibleInterval {
    pub node_id: String,
    pub state: String,
    pub lower: f64,
    pub median: f64,
    pub upper: f64,
    pub method: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BeliefNodePosteriorSnapshot {
    pub node_id: String,
    pub top_state: String,
    pub top_probability: f64,
    pub entropy: f64,
    pub probabilities: BTreeMap<String, f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EngineTrace {
    pub primary_engine: String,
    pub shadow_engine: Option<String>,
    pub sample_count: Option<usize>,
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ShadowComparisonSummary {
    pub top_state_match_rate: BTreeMap<String, f64>,
    pub kl_divergence: BTreeMap<String, f64>,
    pub interval_overlap: BTreeMap<String, f64>,
    pub recommendation_drift: Vec<String>,
    pub status: String,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ObjectiveMarketCredibilityShrink {
    pub objective: Option<String>,
    pub market_family: Option<String>,
    pub credibility_score: f64,
    pub shrink_weight: f64,
    pub shrink_triggered: bool,
    pub hard_blocked: bool,
    pub rationale: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RegimeCompanionPacket {
    pub jump_model: Option<JumpModelRegimeSummary>,
    pub disagreement: Option<RegimeDisagreementSummary>,
    pub objective_market_credibility_shrink: Option<ObjectiveMarketCredibilityShrink>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct BeliefReportPacket {
    pub regime_posterior: RegimePosterior,
    pub regime_companion: RegimeCompanionPacket,
    pub gate_decision: RegimeGateDecision,
    pub belief_posteriors: Vec<BeliefNodePosteriorSnapshot>,
    pub credible_intervals: Vec<CredibleInterval>,
    pub strategy_recommendation: crate::domain::strategy::StrategyRecommendation,
    pub market_family: Option<String>,
    pub market_behavior_profile: Option<String>,
    pub selected_market_subgraph: Option<String>,
    pub engine_trace: EngineTrace,
    pub temporal_summary: Option<ParticleBeliefSummary>,
    pub shadow_comparison: Option<ShadowComparisonSummary>,
}
