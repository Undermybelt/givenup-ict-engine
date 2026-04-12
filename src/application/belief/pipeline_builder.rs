pub use super::pipeline_shared::{
    adapt_factor_pipeline_debug_report, build_canonical_belief_report,
    build_canonical_belief_snapshot, build_factor_pipeline_debug_report, FactorPipelineDebugReport,
};

pub fn infer_market_from_symbol(symbol: &str) -> String {
    symbol
        .split(['.', '_', '-'])
        .next()
        .unwrap_or(symbol)
        .to_ascii_uppercase()
}

pub fn pre_bayes_evidence_policy() -> crate::state::PreBayesEvidencePolicy {
    let min_directional_support_gap =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MIN_SUPPORT_GAP", 0.08);
    let high_uncertainty_threshold =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_HIGH_UNCERTAINTY_THRESHOLD", 0.45);
    let min_multi_timeframe_alignment_score =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MIN_MTF_ALIGNMENT_SCORE", 0.55);
    let min_multi_timeframe_entry_alignment_score =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MIN_MTF_ENTRY_ALIGNMENT_SCORE", 0.50);
    let hard_pass_quality_threshold =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_HARD_PASS_QUALITY_THRESHOLD", 0.75);
    let neutralized_quality_threshold =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_NEUTRALIZED_QUALITY_THRESHOLD", 0.40);
    let directional_conflict_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_DIRECTIONAL_CONFLICT_PENALTY", 0.20);
    let mixed_alignment_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MIXED_ALIGNMENT_PENALTY", 0.10);
    let multi_timeframe_direction_conflict_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MTF_DIRECTION_CONFLICT_PENALTY", 0.18);
    let multi_timeframe_alignment_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MTF_ALIGNMENT_PENALTY", 0.10);
    let multi_timeframe_entry_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MTF_ENTRY_PENALTY", 0.08);
    let multi_timeframe_alignment_bonus =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_MTF_ALIGNMENT_BONUS", 0.05);
    let hostile_liquidity_penalty =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_HOSTILE_LIQUIDITY_PENALTY", 0.10);
    let favorable_liquidity_bonus =
        crate::config::env_f64("ICT_ENGINE_PREBAYES_FAVORABLE_LIQUIDITY_BONUS", 0.05);
    let hostile_liquidity_forces_high_uncertainty = crate::config::env_bool(
        "ICT_ENGINE_PREBAYES_HOSTILE_LIQUIDITY_FORCES_HIGH_UNCERTAINTY",
        true,
    );
    let market_overrides = std::collections::BTreeMap::from([
        (
            "ES".to_string(),
            crate::state::PreBayesMarketPolicyOverride {
                hostile_liquidity_penalty: Some(0.06),
                favorable_liquidity_bonus: Some(0.06),
                hostile_liquidity_forces_high_uncertainty: Some(false),
            },
        ),
        (
            "CL".to_string(),
            crate::state::PreBayesMarketPolicyOverride {
                hostile_liquidity_penalty: Some(0.14),
                favorable_liquidity_bonus: Some(0.03),
                hostile_liquidity_forces_high_uncertainty: Some(true),
            },
        ),
    ]);
    let source = if [
        "ICT_ENGINE_PREBAYES_MIN_SUPPORT_GAP",
        "ICT_ENGINE_PREBAYES_HIGH_UNCERTAINTY_THRESHOLD",
        "ICT_ENGINE_PREBAYES_MIN_MTF_ALIGNMENT_SCORE",
        "ICT_ENGINE_PREBAYES_MIN_MTF_ENTRY_ALIGNMENT_SCORE",
        "ICT_ENGINE_PREBAYES_HARD_PASS_QUALITY_THRESHOLD",
        "ICT_ENGINE_PREBAYES_NEUTRALIZED_QUALITY_THRESHOLD",
        "ICT_ENGINE_PREBAYES_DIRECTIONAL_CONFLICT_PENALTY",
        "ICT_ENGINE_PREBAYES_MIXED_ALIGNMENT_PENALTY",
        "ICT_ENGINE_PREBAYES_MTF_DIRECTION_CONFLICT_PENALTY",
        "ICT_ENGINE_PREBAYES_MTF_ALIGNMENT_PENALTY",
        "ICT_ENGINE_PREBAYES_MTF_ENTRY_PENALTY",
        "ICT_ENGINE_PREBAYES_MTF_ALIGNMENT_BONUS",
        "ICT_ENGINE_PREBAYES_HOSTILE_LIQUIDITY_PENALTY",
        "ICT_ENGINE_PREBAYES_FAVORABLE_LIQUIDITY_BONUS",
        "ICT_ENGINE_PREBAYES_HOSTILE_LIQUIDITY_FORCES_HIGH_UNCERTAINTY",
    ]
    .iter()
    .any(|name| std::env::var(name).is_ok())
    {
        "env_or_default".to_string()
    } else {
        "default".to_string()
    };
    let mut version_inputs = vec![
        format!("{:.6}", min_directional_support_gap),
        format!("{:.6}", high_uncertainty_threshold),
        format!("{:.6}", min_multi_timeframe_alignment_score),
        format!("{:.6}", min_multi_timeframe_entry_alignment_score),
        format!("{:.6}", hard_pass_quality_threshold),
        format!("{:.6}", neutralized_quality_threshold),
        format!("{:.6}", directional_conflict_penalty),
        format!("{:.6}", mixed_alignment_penalty),
        format!("{:.6}", multi_timeframe_direction_conflict_penalty),
        format!("{:.6}", multi_timeframe_alignment_penalty),
        format!("{:.6}", multi_timeframe_entry_penalty),
        format!("{:.6}", multi_timeframe_alignment_bonus),
        format!("{:.6}", hostile_liquidity_penalty),
        format!("{:.6}", favorable_liquidity_bonus),
        hostile_liquidity_forces_high_uncertainty.to_string(),
    ];
    for (market, override_policy) in &market_overrides {
        version_inputs.push(format!("market={market}"));
        version_inputs.push(format!(
            "hostile_liquidity_penalty={}",
            override_policy
                .hostile_liquidity_penalty
                .map(|value| format!("{value:.6}"))
                .unwrap_or_else(|| "none".to_string())
        ));
        version_inputs.push(format!(
            "favorable_liquidity_bonus={}",
            override_policy
                .favorable_liquidity_bonus
                .map(|value| format!("{value:.6}"))
                .unwrap_or_else(|| "none".to_string())
        ));
        version_inputs.push(format!(
            "hostile_liquidity_forces_high_uncertainty={}",
            override_policy
                .hostile_liquidity_forces_high_uncertainty
                .map(|value| value.to_string())
                .unwrap_or_else(|| "none".to_string())
        ));
    }
    let version = crate::config::compute_hash(&version_inputs);
    crate::state::PreBayesEvidencePolicy {
        version,
        source,
        min_directional_support_gap,
        high_uncertainty_threshold,
        min_multi_timeframe_alignment_score,
        min_multi_timeframe_entry_alignment_score,
        hard_pass_quality_threshold,
        neutralized_quality_threshold,
        directional_conflict_penalty,
        mixed_alignment_penalty,
        multi_timeframe_direction_conflict_penalty,
        multi_timeframe_alignment_penalty,
        multi_timeframe_entry_penalty,
        multi_timeframe_alignment_bonus,
        hostile_liquidity_penalty,
        favorable_liquidity_bonus,
        hostile_liquidity_forces_high_uncertainty,
        market_overrides,
    }
}
