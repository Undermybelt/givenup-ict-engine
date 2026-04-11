use chrono::Utc;
use serde::Serialize;
use std::collections::BTreeMap;

use crate::factor_lab::FactorContribution;
use crate::state::{FactorPipelineLabelSource, PreBayesEntryQualityBridge, PreBayesEvidenceFilter};

#[derive(Debug, Serialize, Clone)]
pub struct ExpansionFactorPipelineReport {
    pub factor_name: String,
    pub parameters: BTreeMap<String, f64>,
    pub latest_signal: ExpansionLatestSignal,
    pub probability_support: ExpansionProbabilitySupport,
    pub entry_quality_bridge: PreBayesEntryQualityBridge,
    pub bbn_support: ExpansionBbnSupport,
    pub pipeline_summary: String,
    pub recommended_actions: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ExpansionLatestSignal {
    pub timestamp: chrono::DateTime<Utc>,
    pub direction: String,
    pub value: f64,
    pub confidence: f64,
    pub explanation: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct ExpansionProbabilitySupport {
    pub long_support: f64,
    pub short_support: f64,
    pub support_gap: f64,
    pub alignment_threshold: f64,
    pub uncertainty: f64,
    pub alignment_label: String,
    pub uncertainty_label: String,
    pub long_entry_bias: Vec<f64>,
    pub short_entry_bias: Vec<f64>,
    pub bullish_factors: Vec<FactorContribution>,
    pub bearish_factors: Vec<FactorContribution>,
    pub uncertainty_factors: Vec<FactorContribution>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ExpansionBbnSupport {
    pub market_regime_label: String,
    pub liquidity_context_label: String,
    pub evidence_policy: String,
    pub pre_bayes_filter: PreBayesEvidenceFilter,
    pub evidence_assignments: BTreeMap<String, String>,
    pub raw_market_regime_trace: FactorPipelineLabelSource,
    pub raw_liquidity_context_trace: FactorPipelineLabelSource,
    pub raw_multi_timeframe_resonance_trace: FactorPipelineLabelSource,
    pub entry_quality_base: BTreeMap<String, f64>,
    pub entry_quality_long: BTreeMap<String, f64>,
    pub entry_quality_short: BTreeMap<String, f64>,
    pub trade_outcome_long: BTreeMap<String, f64>,
    pub trade_outcome_short: BTreeMap<String, f64>,
    pub selected_direction: String,
    pub selected_win_probability: f64,
}
