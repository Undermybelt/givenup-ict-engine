use anyhow::Result;

use crate::bbn::adapters::belief_evidence_packet_from_pre_bayes_filter;
use crate::bbn::engine::InferenceEngineRegistry;
use crate::reporting::belief::BeliefReportPacket;
use crate::state::{FactorPipelineLabelSource, PreBayesEvidenceFilter};

pub fn build_canonical_belief_report(
    symbol: &str,
    market: Option<&str>,
    filter: &PreBayesEvidenceFilter,
    raw_market_regime_trace: Option<&FactorPipelineLabelSource>,
    raw_liquidity_context_trace: Option<&FactorPipelineLabelSource>,
    raw_multi_timeframe_resonance_trace: Option<&FactorPipelineLabelSource>,
) -> Result<BeliefReportPacket> {
    InferenceEngineRegistry::default().build_report(belief_evidence_packet_from_pre_bayes_filter(
        symbol,
        market,
        filter,
        raw_market_regime_trace,
        raw_liquidity_context_trace,
        raw_multi_timeframe_resonance_trace,
    ))
}

pub fn build_canonical_belief_snapshot(
    symbol: &str,
    market: Option<&str>,
    filter: &PreBayesEvidenceFilter,
) -> Result<BeliefReportPacket> {
    build_canonical_belief_report(symbol, market, filter, None, None, None)
}
