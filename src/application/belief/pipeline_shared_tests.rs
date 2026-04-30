use super::*;
use crate::state::{
    FactorPipelineLabelSource, PreBayesEntryQualityBridge, PreBayesEntryQualityBridgeDiff,
    PreBayesEvidenceFilter, StructuralNodeDurationPrior, StructuralPriorLearningState,
};
use std::collections::BTreeMap;

#[test]
fn build_factor_pipeline_debug_report_marks_missing_selected_entry_quality_unavailable() {
    let latest_signal = ExpansionLatestSignal {
        timestamp: chrono::Utc::now(),
        direction: "bull".to_string(),
        value: 1.0,
        confidence: 0.6,
        explanation: "test".to_string(),
    };
    let factor_diagnostics = ExpansionProbabilitySupport {
        long_support: 0.6,
        short_support: 0.4,
        support_gap: 0.2,
        alignment_threshold: 0.1,
        uncertainty: 0.2,
        alignment_label: "bullish".to_string(),
        uncertainty_label: "low".to_string(),
        long_entry_bias: vec![0.7, 0.2, 0.1],
        short_entry_bias: vec![0.2, 0.3, 0.5],
        bullish_factors: vec![],
        bearish_factors: vec![],
        uncertainty_factors: vec![],
    };
    let trace = FactorPipelineLabelSource {
        label: "bull".to_string(),
        derivation: "test".to_string(),
        evidence: vec!["e1".to_string()],
    };
    let bbn_support = ExpansionBbnSupport {
        market_regime_label: "bull".to_string(),
        liquidity_context_label: "neutral".to_string(),
        evidence_policy: "test_policy".to_string(),
        pre_bayes_filter: PreBayesEvidenceFilter {
            gating_status: "observe_only".to_string(),
            ..PreBayesEvidenceFilter::default()
        },
        evidence_assignments: BTreeMap::new(),
        raw_market_regime_trace: trace.clone(),
        raw_liquidity_context_trace: trace.clone(),
        raw_multi_timeframe_resonance_trace: trace,
        entry_quality_base: BTreeMap::new(),
        entry_quality_long: BTreeMap::new(),
        entry_quality_short: BTreeMap::new(),
        trade_outcome_long: BTreeMap::new(),
        trade_outcome_short: BTreeMap::new(),
        selected_direction: "bull".to_string(),
        selected_win_probability: 0.55,
    };
    let report = build_factor_pipeline_debug_report(FactorPipelineDebugReportInput {
        symbol: "NQ".to_string(),
        data: "NQ".to_string(),
        objective: "test".to_string(),
        factor_name: "factor_x".to_string(),
        latest_signal,
        factor_diagnostics,
        bbn_support,
        entry_quality_bridge: PreBayesEntryQualityBridge::default(),
        bridge_diff: PreBayesEntryQualityBridgeDiff {
            selected_entry_quality: None,
            ..PreBayesEntryQualityBridgeDiff::default()
        },
        multi_timeframe_summary: vec![],
        raw_pre_bayes_labels: BTreeMap::new(),
        soft_evidence_divergence: vec![],
        bridge_gap_clear_threshold: 0.12,
        paired_market_quality_report: None,
    })
    .unwrap();
    assert_eq!(report.selected_entry_quality, "entry_quality_unavailable");
}

#[test]
fn adapt_factor_pipeline_debug_report_prefers_explicit_paired_market_quality_report() {
    let trace = FactorPipelineLabelSource {
        label: "bull".to_string(),
        derivation: "test".to_string(),
        evidence: vec!["e1".to_string()],
    };
    let pipeline = ExpansionFactorPipelineReport {
        factor_name: "cross_market_smt".to_string(),
        parameters: BTreeMap::new(),
        latest_signal: ExpansionLatestSignal {
            timestamp: chrono::Utc::now(),
            direction: "bull".to_string(),
            value: 1.0,
            confidence: 0.5,
            explanation: "status=invalid_due_to_pair_quality;quality_tier=low;reason=from_explanation;aligned_length=2;primary_length=3;paired_length=4;overlap_ratio=0.5;safe_lookback=1".to_string(),
        },
        probability_support: ExpansionProbabilitySupport {
            long_support: 0.6,
            short_support: 0.4,
            support_gap: 0.2,
            alignment_threshold: 0.1,
            uncertainty: 0.2,
            alignment_label: "bullish".to_string(),
            uncertainty_label: "low".to_string(),
            long_entry_bias: vec![0.7, 0.2, 0.1],
            short_entry_bias: vec![0.2, 0.3, 0.5],
            bullish_factors: vec![],
            bearish_factors: vec![],
            uncertainty_factors: vec![],
        },
        paired_market_quality_report: Some(crate::factor_lab::PairedMarketQualityReport {
            paired_market_quality: "poor".to_string(),
            aligned_length: 2,
            primary_length: 3,
            paired_length: 4,
            overlap_ratio: 0.5,
            safe_lookback: 1,
            status: "invalid_due_to_pair_quality".to_string(),
            reason: "from_pipeline".to_string(),
        }),
        entry_quality_bridge: PreBayesEntryQualityBridge::default(),
        bbn_support: ExpansionBbnSupport {
            market_regime_label: "bull".to_string(),
            liquidity_context_label: "neutral".to_string(),
            evidence_policy: "test_policy".to_string(),
            pre_bayes_filter: PreBayesEvidenceFilter {
                gating_status: "observe_only".to_string(),
                ..PreBayesEvidenceFilter::default()
            },
            evidence_assignments: BTreeMap::new(),
            raw_market_regime_trace: trace.clone(),
            raw_liquidity_context_trace: trace.clone(),
            raw_multi_timeframe_resonance_trace: trace,
            entry_quality_base: BTreeMap::new(),
            entry_quality_long: BTreeMap::new(),
            entry_quality_short: BTreeMap::new(),
            trade_outcome_long: BTreeMap::new(),
            trade_outcome_short: BTreeMap::new(),
            selected_direction: "bull".to_string(),
            selected_win_probability: 0.55,
        },
        pipeline_summary: "summary".to_string(),
        recommended_actions: vec![],
        frame_physics_trace: vec![],
    };
    let explicit = crate::factor_lab::PairedMarketQualityReport {
        paired_market_quality: "medium".to_string(),
        aligned_length: 80,
        primary_length: 100,
        paired_length: 82,
        overlap_ratio: 0.80,
        safe_lookback: 24,
        status: "valid".to_string(),
        reason: "limited_pair_overlap".to_string(),
    };
    let report = adapt_factor_pipeline_debug_report(AdaptFactorPipelineDebugReportInput {
        symbol: "NQ",
        data: "test-data",
        objective: "test",
        pipeline: &pipeline,
        multi_timeframe_summary: &[],
        raw_pre_bayes_labels: BTreeMap::new(),
        soft_evidence_divergence: vec![],
        bridge_gap_clear_threshold: 0.12,
        paired_market_quality_report: Some(explicit.clone()),
    })
    .unwrap();
    assert_eq!(report.paired_market_quality_report, Some(explicit));
}

#[test]
fn canonical_belief_snapshot_with_structural_prior_state_uses_duration_prior_for_regime_confidence()
{
    let filter = PreBayesEvidenceFilter {
        filtered_market_regime_label: "bull".to_string(),
        soft_market_regime_distribution: BTreeMap::from([
            ("bull".to_string(), 0.72),
            ("range".to_string(), 0.18),
            ("transition".to_string(), 0.10),
        ]),
        uses_soft_evidence: true,
        ..PreBayesEvidenceFilter::default()
    };
    let mut structural_prior_state = StructuralPriorLearningState::default();
    structural_prior_state.node_duration_priors.insert(
        "NQ:belief_regime_node:trend".to_string(),
        StructuralNodeDurationPrior {
            observations: 6,
            streak_count: 3,
            total_streak_length: 6,
            avg_streak_length: 2.0,
            max_streak_length: 3,
            last_streak_length: 3,
            persistence_prior: 0.90,
            last_recommended_at: Some("2026-04-30T03:00:00Z".to_string()),
        },
    );

    let report = build_canonical_belief_snapshot_with_pda_and_structural_prior_state(
        "NQ",
        Some("NQ"),
        &filter,
        None,
        None,
        None,
        Some(&structural_prior_state),
    )
    .unwrap();

    assert_eq!(report.regime_posterior.active_regime.as_deref(), Some("trend"));
    assert!(report.regime_posterior.confidence.unwrap_or_default() > 0.72);
    assert!(report
        .regime_posterior
        .evidence
        .iter()
        .any(|line| line.contains("duration_persistence_prior")));
}

#[test]
fn adapt_factor_pipeline_debug_report_uses_pipeline_structured_report_before_explanation() {
    let trace = FactorPipelineLabelSource {
        label: "bull".to_string(),
        derivation: "test".to_string(),
        evidence: vec!["e1".to_string()],
    };
    let pipeline_report = crate::factor_lab::PairedMarketQualityReport {
        paired_market_quality: "medium".to_string(),
        aligned_length: 80,
        primary_length: 100,
        paired_length: 82,
        overlap_ratio: 0.80,
        safe_lookback: 24,
        status: "valid".to_string(),
        reason: "from_pipeline".to_string(),
    };
    let pipeline = ExpansionFactorPipelineReport {
        factor_name: "cross_market_smt".to_string(),
        parameters: BTreeMap::new(),
        latest_signal: ExpansionLatestSignal {
            timestamp: chrono::Utc::now(),
            direction: "bull".to_string(),
            value: 1.0,
            confidence: 0.5,
            explanation: "status=invalid_due_to_pair_quality;quality_tier=low;reason=from_explanation;aligned_length=2;primary_length=3;paired_length=4;overlap_ratio=0.5;safe_lookback=1".to_string(),
        },
        probability_support: ExpansionProbabilitySupport {
            long_support: 0.6,
            short_support: 0.4,
            support_gap: 0.2,
            alignment_threshold: 0.1,
            uncertainty: 0.2,
            alignment_label: "bullish".to_string(),
            uncertainty_label: "low".to_string(),
            long_entry_bias: vec![0.7, 0.2, 0.1],
            short_entry_bias: vec![0.2, 0.3, 0.5],
            bullish_factors: vec![],
            bearish_factors: vec![],
            uncertainty_factors: vec![],
        },
        paired_market_quality_report: Some(pipeline_report.clone()),
        entry_quality_bridge: PreBayesEntryQualityBridge::default(),
        bbn_support: ExpansionBbnSupport {
            market_regime_label: "bull".to_string(),
            liquidity_context_label: "neutral".to_string(),
            evidence_policy: "test_policy".to_string(),
            pre_bayes_filter: PreBayesEvidenceFilter {
                gating_status: "observe_only".to_string(),
                ..PreBayesEvidenceFilter::default()
            },
            evidence_assignments: BTreeMap::new(),
            raw_market_regime_trace: trace.clone(),
            raw_liquidity_context_trace: trace.clone(),
            raw_multi_timeframe_resonance_trace: trace,
            entry_quality_base: BTreeMap::new(),
            entry_quality_long: BTreeMap::new(),
            entry_quality_short: BTreeMap::new(),
            trade_outcome_long: BTreeMap::new(),
            trade_outcome_short: BTreeMap::new(),
            selected_direction: "bull".to_string(),
            selected_win_probability: 0.55,
        },
        pipeline_summary: "summary".to_string(),
        recommended_actions: vec![],
        frame_physics_trace: vec![],
    };
    let report = adapt_factor_pipeline_debug_report(AdaptFactorPipelineDebugReportInput {
        symbol: "NQ",
        data: "test-data",
        objective: "test",
        pipeline: &pipeline,
        multi_timeframe_summary: &[],
        raw_pre_bayes_labels: BTreeMap::new(),
        soft_evidence_divergence: vec![],
        bridge_gap_clear_threshold: 0.12,
        paired_market_quality_report: None,
    })
    .unwrap();
    assert_eq!(report.paired_market_quality_report, Some(pipeline_report));
}
