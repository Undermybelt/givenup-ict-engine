use anyhow::Result;
use chrono::Utc;
use serde::Serialize;
use std::collections::BTreeMap;

use crate::application::belief::build_canonical_belief_report;
use crate::factor_lab::FactorContribution;
use crate::reporting::belief::BeliefReportPacket;
use crate::state::{
    FactorPipelineLabelSource, PreBayesEntryQualityBridge, PreBayesEntryQualityBridgeDiff,
    PreBayesSoftEvidenceNodeDiff,
};

#[derive(Debug, Serialize, Clone)]
pub struct FactorPipelineDebugReport {
    pub symbol: String,
    pub data: String,
    pub factor_name: String,
    pub objective: String,
    pub latest_signal: ExpansionLatestSignal,
    pub factor_diagnostics: ExpansionProbabilitySupport,
    pub raw_label_trace: FactorPipelineRawLabelTrace,
    pub raw_pre_bayes_labels: BTreeMap<String, String>,
    pub filtered_pre_bayes_labels: BTreeMap<String, String>,
    pub evidence_quality_score: f64,
    pub gating_status: String,
    pub soft_evidence_divergence: Vec<PreBayesSoftEvidenceNodeDiff>,
    pub bridge_gap: f64,
    pub selected_entry_quality: String,
    pub six_timeframe_resonance: Vec<String>,
    pub pipeline_verdict: String,
    pub pipeline_summary: String,
    pub recommended_actions: Vec<String>,
    pub entry_quality_bridge: PreBayesEntryQualityBridge,
    pub bbn_support: ExpansionBbnSupport,
    pub shadow_belief_report: BeliefReportPacket,
    pub shadow_summary_line: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct FactorPipelineRawLabelTrace {
    pub market_regime: FactorPipelineLabelSource,
    pub liquidity_context: FactorPipelineLabelSource,
    pub multi_timeframe_resonance: FactorPipelineLabelSource,
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
    pub pre_bayes_filter: crate::state::PreBayesEvidenceFilter,
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

pub fn build_factor_pipeline_debug_report(
    symbol: &str,
    data: &str,
    objective: &str,
    factor_name: &str,
    latest_signal: ExpansionLatestSignal,
    factor_diagnostics: ExpansionProbabilitySupport,
    bbn_support: ExpansionBbnSupport,
    entry_quality_bridge: PreBayesEntryQualityBridge,
    bridge_diff: PreBayesEntryQualityBridgeDiff,
    multi_timeframe_summary: &[String],
    raw_pre_bayes_labels: BTreeMap<String, String>,
    soft_evidence_divergence: Vec<PreBayesSoftEvidenceNodeDiff>,
    bridge_gap_clear_threshold: f64,
) -> Result<FactorPipelineDebugReport> {
    let filtered_pre_bayes_labels = bbn_support.evidence_assignments.clone();
    let gating_status = bbn_support.pre_bayes_filter.gating_status.clone();
    let selected_entry_quality = bridge_diff
        .selected_entry_quality
        .clone()
        .unwrap_or_else(|| "unknown".to_string());
    let bridge_gap = bridge_diff.long_short_signal_probability_gap;
    let pipeline_verdict =
        if is_hard_pass(&gating_status) && bridge_gap >= bridge_gap_clear_threshold {
            "clear_through_pre_bayes_and_bridge".to_string()
        } else if gating_status == "pass_neutralized" {
            "pre_bayes_pass_but_bridge_needs_confirmation".to_string()
        } else if gating_status == "observe_only" {
            "blocked_at_pre_bayes_gate".to_string()
        } else if is_hard_pass(&gating_status) {
            "pre_bayes_pass_hard_but_bridge_gap_insufficient".to_string()
        } else {
            "pipeline_unclear".to_string()
        };

    let shadow_belief_report = build_canonical_belief_report(
        symbol,
        Some(data),
        &bbn_support.pre_bayes_filter,
        Some(&bbn_support.raw_market_regime_trace),
        Some(&bbn_support.raw_liquidity_context_trace),
        Some(&bbn_support.raw_multi_timeframe_resonance_trace),
    )?;
    let shadow_summary_line = shadow_belief_report
        .shadow_comparison
        .as_ref()
        .map(|summary| summary.summary_line.clone())
        .unwrap_or_else(|| "shadow=unavailable".to_string());

    Ok(FactorPipelineDebugReport {
        symbol: symbol.to_string(),
        data: data.to_string(),
        factor_name: factor_name.to_string(),
        objective: objective.to_string(),
        latest_signal,
        factor_diagnostics,
        raw_label_trace: FactorPipelineRawLabelTrace {
            market_regime: bbn_support.raw_market_regime_trace.clone(),
            liquidity_context: bbn_support.raw_liquidity_context_trace.clone(),
            multi_timeframe_resonance: bbn_support.raw_multi_timeframe_resonance_trace.clone(),
        },
        raw_pre_bayes_labels,
        filtered_pre_bayes_labels,
        evidence_quality_score: bbn_support.pre_bayes_filter.evidence_quality_score,
        gating_status,
        soft_evidence_divergence,
        bridge_gap,
        selected_entry_quality,
        six_timeframe_resonance: multi_timeframe_summary.to_vec(),
        pipeline_verdict,
        pipeline_summary: bbn_support.evidence_policy.clone(),
        recommended_actions: vec![format!("inspect_factor={factor_name}")],
        entry_quality_bridge,
        bbn_support,
        shadow_belief_report,
        shadow_summary_line,
    })
}

fn is_hard_pass(status: &str) -> bool {
    status == "pass_hard"
}
