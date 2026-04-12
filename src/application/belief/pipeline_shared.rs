use anyhow::Result;
use serde::Serialize;
use std::cmp::Ordering;
use std::collections::BTreeMap;

use crate::analyze::multi_timeframe_parse::{
    multi_timeframe_direction_conflicts_with, ParsedMultiTimeframeEvidence,
};
use crate::bbn::adapters::belief_evidence_packet_from_pre_bayes_filter;
use crate::bbn::engine::InferenceEngineRegistry;
use crate::reporting::belief::BeliefReportPacket;
use crate::state::{
    FactorPipelineLabelSource, PreBayesEntryQualityBridge, PreBayesEntryQualityBridgeDiff,
    PreBayesEvidenceFilter, PreBayesEvidencePolicy, PreBayesSoftEvidenceNodeDiff,
};
use crate::types::Direction;

use super::pipeline_types::ExpansionFactorPipelineReport;

#[derive(Debug, Clone, Serialize)]
pub struct ExpansionLatestSignal {
    pub timestamp: chrono::DateTime<chrono::Utc>,
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
    pub bullish_factors: Vec<crate::factor_lab::FactorContribution>,
    pub bearish_factors: Vec<crate::factor_lab::FactorContribution>,
    pub uncertainty_factors: Vec<crate::factor_lab::FactorContribution>,
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

pub fn adapt_factor_pipeline_debug_report(
    symbol: &str,
    data: &str,
    objective: &str,
    pipeline: &ExpansionFactorPipelineReport,
    raw_pre_bayes_labels: BTreeMap<String, String>,
    soft_evidence_divergence: Vec<PreBayesSoftEvidenceNodeDiff>,
    bridge_gap_clear_threshold: f64,
    multi_timeframe_summary: &[String],
) -> Result<FactorPipelineDebugReport> {
    build_factor_pipeline_debug_report(
        symbol,
        data,
        objective,
        &pipeline.factor_name,
        ExpansionLatestSignal {
            timestamp: pipeline.latest_signal.timestamp,
            direction: pipeline.latest_signal.direction.clone(),
            value: pipeline.latest_signal.value,
            confidence: pipeline.latest_signal.confidence,
            explanation: pipeline.latest_signal.explanation.clone(),
        },
        ExpansionProbabilitySupport {
            long_support: pipeline.probability_support.long_support,
            short_support: pipeline.probability_support.short_support,
            support_gap: pipeline.probability_support.support_gap,
            alignment_threshold: pipeline.probability_support.alignment_threshold,
            uncertainty: pipeline.probability_support.uncertainty,
            alignment_label: pipeline.probability_support.alignment_label.clone(),
            uncertainty_label: pipeline.probability_support.uncertainty_label.clone(),
            long_entry_bias: pipeline.probability_support.long_entry_bias.clone(),
            short_entry_bias: pipeline.probability_support.short_entry_bias.clone(),
            bullish_factors: pipeline.probability_support.bullish_factors.clone(),
            bearish_factors: pipeline.probability_support.bearish_factors.clone(),
            uncertainty_factors: pipeline.probability_support.uncertainty_factors.clone(),
        },
        ExpansionBbnSupport {
            market_regime_label: pipeline.bbn_support.market_regime_label.clone(),
            liquidity_context_label: pipeline.bbn_support.liquidity_context_label.clone(),
            evidence_policy: pipeline.bbn_support.evidence_policy.clone(),
            pre_bayes_filter: pipeline.bbn_support.pre_bayes_filter.clone(),
            evidence_assignments: pipeline.bbn_support.evidence_assignments.clone(),
            raw_market_regime_trace: pipeline.bbn_support.raw_market_regime_trace.clone(),
            raw_liquidity_context_trace: pipeline.bbn_support.raw_liquidity_context_trace.clone(),
            raw_multi_timeframe_resonance_trace: pipeline
                .bbn_support
                .raw_multi_timeframe_resonance_trace
                .clone(),
            entry_quality_base: pipeline.bbn_support.entry_quality_base.clone(),
            entry_quality_long: pipeline.bbn_support.entry_quality_long.clone(),
            entry_quality_short: pipeline.bbn_support.entry_quality_short.clone(),
            trade_outcome_long: pipeline.bbn_support.trade_outcome_long.clone(),
            trade_outcome_short: pipeline.bbn_support.trade_outcome_short.clone(),
            selected_direction: pipeline.bbn_support.selected_direction.clone(),
            selected_win_probability: pipeline.bbn_support.selected_win_probability,
        },
        pipeline.entry_quality_bridge.clone(),
        pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge),
        multi_timeframe_summary,
        raw_pre_bayes_labels,
        soft_evidence_divergence,
        bridge_gap_clear_threshold,
    )
}

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

fn pre_bayes_entry_quality_bridge_diff(
    bridge: &PreBayesEntryQualityBridge,
) -> PreBayesEntryQualityBridgeDiff {
    let (dominant_long_entry_quality, dominant_long_entry_quality_probability) =
        max_probability_label(&bridge.long_entry_quality);
    let (dominant_short_entry_quality, dominant_short_entry_quality_probability) =
        max_probability_label(&bridge.short_entry_quality);
    let (selected_entry_quality, selected_entry_quality_probability) =
        if bridge.selected_entry_quality.is_empty() {
            let fallback = dominant_long_entry_quality
                .clone()
                .or_else(|| dominant_short_entry_quality.clone());
            let probability = if fallback == dominant_long_entry_quality {
                dominant_long_entry_quality_probability
            } else {
                dominant_short_entry_quality_probability
            };
            (fallback, probability)
        } else {
            max_probability_label(&bridge.selected_entry_quality)
        };

    PreBayesEntryQualityBridgeDiff {
        dominant_long_entry_quality,
        dominant_long_entry_quality_probability,
        dominant_short_entry_quality,
        dominant_short_entry_quality_probability,
        selected_entry_quality,
        selected_entry_quality_probability,
        long_short_signal_probability_gap: (bridge.long_signal_probability
            - bridge.short_signal_probability)
            .abs(),
        multi_timeframe_direction_bias: bridge.multi_timeframe_direction_bias.clone(),
        multi_timeframe_alignment_score: bridge.multi_timeframe_alignment_score,
        multi_timeframe_entry_alignment_score: bridge.multi_timeframe_entry_alignment_score,
        rationale_summary: bridge.rationale.clone(),
    }
}

fn max_probability_label(probabilities: &BTreeMap<String, f64>) -> (Option<String>, f64) {
    probabilities
        .iter()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(Ordering::Equal))
        .map(|(label, value)| (Some(label.clone()), *value))
        .unwrap_or((None, 0.0))
}

pub fn raw_market_regime_trace(
    regime_label: &str,
    regime_evidence_label: &str,
    sweep_count: usize,
    fvg_count: usize,
) -> FactorPipelineLabelSource {
    FactorPipelineLabelSource {
        label: regime_label.to_string(),
        derivation: "build_frame_features.regime_label".to_string(),
        evidence: vec![
            format!("frame_regime_label={}", regime_evidence_label),
            format!("sweep_count={}", sweep_count),
            format!("fvg_count={}", fvg_count),
        ],
    }
}

pub fn raw_liquidity_context_trace(
    liquidity_label: &str,
    liquidity_evidence_label: &str,
    sweep_count: usize,
    fvg_count: usize,
) -> FactorPipelineLabelSource {
    FactorPipelineLabelSource {
        label: liquidity_label.to_string(),
        derivation: "build_frame_features.liquidity_label".to_string(),
        evidence: vec![
            format!("frame_liquidity_label={}", liquidity_evidence_label),
            format!("sweep_count={}", sweep_count),
            format!("fvg_count={}", fvg_count),
        ],
    }
}

pub fn raw_multi_timeframe_resonance_trace(
    policy: &PreBayesEvidencePolicy,
    pre_bayes_filter: &PreBayesEvidenceFilter,
    multi_timeframe_evidence: &ParsedMultiTimeframeEvidence,
    regime_label: &str,
    factor_alignment_label: &str,
) -> FactorPipelineLabelSource {
    let direction_conflict = multi_timeframe_direction_conflicts_with(
        regime_label,
        &multi_timeframe_evidence.direction_bias,
    ) || multi_timeframe_direction_conflicts_with(
        factor_alignment_label,
        &multi_timeframe_evidence.direction_bias,
    );

    FactorPipelineLabelSource {
        label: pre_bayes_filter.raw_multi_timeframe_resonance_label.clone(),
        derivation: "classify_multi_timeframe_resonance(policy, direction_conflict, parsed_multi_timeframe_evidence)".to_string(),
        evidence: vec![
            format!("direction_bias={}", multi_timeframe_evidence.direction_bias),
            format!(
                "alignment_score={:.4}",
                multi_timeframe_evidence.alignment_score.unwrap_or_default()
            ),
            format!(
                "entry_alignment_score={:.4}",
                multi_timeframe_evidence.entry_alignment_score.unwrap_or_default()
            ),
            format!("direction_conflict={}", direction_conflict),
            format!(
                "alignment_floor={:.4}",
                policy.min_multi_timeframe_alignment_score
            ),
            format!(
                "entry_alignment_floor={:.4}",
                policy.min_multi_timeframe_entry_alignment_score
            ),
        ],
    }
}

pub fn multi_timeframe_entry_quality_bias(
    evidence: &ParsedMultiTimeframeEvidence,
    direction: Direction,
) -> Vec<f64> {
    let alignment_score = evidence.alignment_score.unwrap_or(0.5).clamp(0.0, 1.0);
    let entry_alignment_score = evidence
        .entry_alignment_score
        .unwrap_or(0.5)
        .clamp(0.0, 1.0);
    let supportive = matches!(
        (direction, evidence.direction_bias.as_str()),
        (Direction::Bull, "bullish") | (Direction::Bear, "bearish")
    );
    let hostile = matches!(
        (direction, evidence.direction_bias.as_str()),
        (Direction::Bull, "bearish") | (Direction::Bear, "bullish")
    );

    let mut bias = vec![1.0, 1.0, 1.0];
    if supportive {
        bias[0] *= 1.0 + alignment_score * 0.45 + entry_alignment_score * 0.25;
        bias[1] *= 1.0 + alignment_score * 0.10;
        bias[2] *= (1.0 - alignment_score * 0.30 - entry_alignment_score * 0.20).max(0.20);
    } else if hostile {
        bias[0] *= (1.0 - alignment_score * 0.30).max(0.25);
        bias[1] *= 1.0 + (1.0 - entry_alignment_score) * 0.15;
        bias[2] *= 1.0 + alignment_score * 0.40 + (1.0 - entry_alignment_score) * 0.20;
    } else {
        bias[0] *= 1.0 + alignment_score * 0.08;
        bias[1] *= 1.0 + entry_alignment_score * 0.12;
    }
    normalize_distribution(&mut bias);
    bias
}

pub fn probability_map(states: &[String], probabilities: &[f64]) -> BTreeMap<String, f64> {
    states
        .iter()
        .cloned()
        .zip(probabilities.iter().copied())
        .collect()
}

pub fn combine_bias_vectors(left: &[f64], right: &[f64]) -> Vec<f64> {
    let len = left.len().max(right.len());
    let mut combined = vec![1.0; len];
    for index in 0..len {
        let left_value = left.get(index).copied().unwrap_or(1.0 / len as f64);
        let right_value = right.get(index).copied().unwrap_or(1.0 / len as f64);
        combined[index] = (left_value * right_value).max(1e-6);
    }
    normalize_distribution(&mut combined);
    combined
}

pub fn apply_factor_outcome_overlay(
    distribution: &[f64],
    directional_bias: f64,
    uncertainty: f64,
) -> Vec<f64> {
    let mut adjusted = distribution.to_vec();
    if adjusted.len() < 3 {
        return adjusted;
    }

    adjusted[0] *= (1.0 + directional_bias * 0.35 - uncertainty * 0.10).max(0.05);
    adjusted[1] *= (1.0 + uncertainty * 0.20).max(0.05);
    adjusted[2] *= (1.0 - directional_bias * 0.35 + uncertainty * 0.30).max(0.05);
    normalize_distribution(&mut adjusted);
    adjusted
}

pub fn normalize_distribution(values: &mut [f64]) {
    let sum: f64 = values.iter().sum();
    if sum <= f64::EPSILON {
        let uniform = 1.0 / values.len() as f64;
        values.fill(uniform);
        return;
    }
    for value in values {
        *value /= sum;
    }
}
