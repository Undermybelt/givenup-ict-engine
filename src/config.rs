use std::collections::hash_map::DefaultHasher;
use std::collections::BTreeMap;
use std::env;
use std::hash::{Hash, Hasher};

use crate::analyze::multi_timeframe_parse::{
    classify_multi_timeframe_resonance, multi_timeframe_direction_conflicts_with,
    ParsedMultiTimeframeEvidence,
};
use crate::data::candles_to_prices;
use crate::factor_lab::FactorDiagnostics;
use crate::hmm::{build_observations, ObservationInput};
use crate::ict::{detect_fvg, detect_liquidity_pools, detect_liquidity_sweep};
use crate::indicators::{atr_percent, compute_adx, compute_atr, compute_rsi};
use crate::kalman::KalmanFilter;
use crate::state::{
    FactorPipelineLabelSource, PreBayesEvidenceFilter, PreBayesEvidencePolicy,
    PreBayesMarketPolicyOverride,
};
use crate::types::{Candle, Direction};

#[derive(Debug, Clone)]
pub struct FrameFeatures {
    pub observations: Vec<Vec<f64>>,
    pub regime_label: String,
    pub liquidity_label: String,
    pub market: Option<String>,
    pub sweep_count: usize,
    pub fvg_count: usize,
}

pub const INDICATOR_PERIOD: usize = 14;

pub fn build_frame_features(candles: &[Candle]) -> anyhow::Result<FrameFeatures> {
    if candles.len() < INDICATOR_PERIOD * 2 + 1 {
        anyhow::bail!(
            "need at least {} candles to build features, got {}",
            INDICATOR_PERIOD * 2 + 1,
            candles.len()
        );
    }

    let prices = candles_to_prices(candles);
    let initial_price = prices
        .first()
        .copied()
        .ok_or_else(|| anyhow::anyhow!("candle series is empty"))?;

    let atr = left_pad(compute_atr(candles, INDICATOR_PERIOD), candles.len(), 0.0);
    let rsi = left_pad(compute_rsi(candles, INDICATOR_PERIOD), candles.len(), 50.0);
    let adx = left_pad(compute_adx(candles, INDICATOR_PERIOD), candles.len(), 0.0);
    let implied_vol = left_pad(atr_percent(candles, INDICATOR_PERIOD), candles.len(), 0.0);

    let mut kalman = KalmanFilter::new(initial_price, 1e-3, 1e-4, 1e-2);
    let smoothed_prices = kalman.smooth_series(&prices);

    let fvgs = detect_fvg(candles);
    let pools = detect_liquidity_pools(candles, &atr, 0.5, 2);
    let sweeps = detect_liquidity_sweep(candles, &pools, 5);
    let recent_sweeps = sweeps
        .iter()
        .filter(|sweep| sweep.sweep_bar >= candles.len().saturating_sub(10))
        .count();

    let observations = build_observations(ObservationInput {
        candles,
        ltf_candles: candles,
        implied_vol: &implied_vol,
        smoothed_prices: &smoothed_prices,
        atr: &atr,
        rsi: &rsi,
        adx: &adx,
        fvgs: &fvgs,
        sweeps: &sweeps,
    });
    if observations.is_empty() {
        anyhow::bail!(
            "failed to build HMM observations from {} candles",
            candles.len()
        );
    }

    let latest_velocity = smoothed_prices
        .last()
        .map(|(_, velocity, _)| *velocity)
        .unwrap_or(0.0);
    let regime_label = if latest_velocity > 1e-6 {
        "bull"
    } else if latest_velocity < -1e-6 {
        "bear"
    } else {
        "range"
    };
    let liquidity_label = if recent_sweeps >= 2 {
        "hostile"
    } else if recent_sweeps == 1 {
        "neutral"
    } else {
        "favorable"
    };

    Ok(FrameFeatures {
        observations,
        regime_label: regime_label.to_string(),
        liquidity_label: liquidity_label.to_string(),
        market: None,
        sweep_count: sweeps.len(),
        fvg_count: fvgs.len(),
    })
}

pub fn build_frame_features_for_market(
    candles: &[Candle],
    market: Option<&str>,
) -> anyhow::Result<FrameFeatures> {
    let mut frame = build_frame_features(candles)?;
    frame.market = market.map(|value| value.to_ascii_uppercase());

    if let Some(market) = frame.market.as_deref() {
        let base_regime = frame.regime_label.clone();
        let base_liquidity = frame.liquidity_label.clone();
        match market {
            "NQ" => {
                if frame.sweep_count > frame.fvg_count.saturating_mul(2) {
                    frame.regime_label = "range".to_string();
                }
                if base_liquidity == "hostile" && frame.sweep_count > 0 && frame.fvg_count > 0 {
                    frame.liquidity_label = "neutral".to_string();
                }
            }
            "ES" => {
                if base_regime == "range" && frame.fvg_count > frame.sweep_count {
                    frame.regime_label = "bull".to_string();
                }
                if base_liquidity == "hostile"
                    && frame.fvg_count >= frame.sweep_count
                    && frame.fvg_count > 0
                {
                    frame.liquidity_label = "neutral".to_string();
                }
            }
            "YM" => {
                if base_regime == "range" && frame.sweep_count <= frame.fvg_count {
                    frame.regime_label = "bull".to_string();
                }
                if base_liquidity == "hostile" && frame.fvg_count > 0 {
                    frame.liquidity_label = "neutral".to_string();
                }
            }
            "GC" => {
                if base_regime == "range" && frame.fvg_count >= frame.sweep_count.saturating_add(1)
                {
                    frame.regime_label = "bull".to_string();
                }
                if base_liquidity == "favorable" && frame.fvg_count > 0 {
                    frame.liquidity_label = "neutral".to_string();
                }
            }
            "CL" => {
                if base_regime == "bear" && frame.sweep_count > frame.fvg_count {
                    frame.regime_label = "range".to_string();
                }
                if base_liquidity == "favorable" && frame.sweep_count >= 1 {
                    frame.liquidity_label = "neutral".to_string();
                }
            }
            _ => {}
        }
    }

    Ok(frame)
}

pub fn raw_market_regime_trace(
    regime_label: &str,
    frame: &FrameFeatures,
) -> FactorPipelineLabelSource {
    FactorPipelineLabelSource {
        label: regime_label.to_string(),
        derivation: "build_frame_features.regime_label".to_string(),
        evidence: vec![
            format!("frame_regime_label={}", frame.regime_label),
            format!("sweep_count={}", frame.sweep_count),
            format!("fvg_count={}", frame.fvg_count),
        ],
    }
}

pub fn raw_liquidity_context_trace(
    liquidity_label: &str,
    frame: &FrameFeatures,
) -> FactorPipelineLabelSource {
    FactorPipelineLabelSource {
        label: liquidity_label.to_string(),
        derivation: "build_frame_features.liquidity_label".to_string(),
        evidence: vec![
            format!("frame_liquidity_label={}", frame.liquidity_label),
            format!("sweep_count={}", frame.sweep_count),
            format!("fvg_count={}", frame.fvg_count),
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
    let total = bias.iter().copied().sum::<f64>();
    if total > f64::EPSILON {
        for value in &mut bias {
            *value /= total;
        }
    } else {
        let uniform = 1.0 / bias.len() as f64;
        bias.fill(uniform);
    }
    bias
}

pub fn pre_bayes_distribution(
    states: &[&str],
    raw_label: &str,
    filtered_label: &str,
    neutral_label: &str,
    gating_status: &str,
    evidence_quality_score: f64,
) -> BTreeMap<String, f64> {
    let mut distribution = states
        .iter()
        .map(|state| ((*state).to_string(), 0.0))
        .collect::<BTreeMap<_, _>>();
    match gating_status {
        "pass_hard" => {
            distribution.insert(filtered_label.to_string(), 1.0);
        }
        "pass_neutralized" => {
            let dominant = (0.45 + evidence_quality_score * 0.25).clamp(0.45, 0.70);
            let raw_support = if raw_label != filtered_label {
                0.20
            } else {
                0.0
            };
            let neutral_support = 1.0 - dominant - raw_support;
            distribution.insert(filtered_label.to_string(), dominant);
            if raw_support > 0.0 {
                distribution.insert(raw_label.to_string(), raw_support);
            }
            distribution
                .entry(neutral_label.to_string())
                .and_modify(|value| *value += neutral_support);
        }
        _ => {
            distribution.insert(neutral_label.to_string(), 0.60);
            let spill = 0.40 / (states.len().saturating_sub(1).max(1)) as f64;
            for state in states {
                if *state != neutral_label {
                    distribution.insert((*state).to_string(), spill);
                }
            }
        }
    }
    distribution
}

pub fn pre_bayes_market_policy_override(
    market: Option<&str>,
    override_config: &BTreeMap<String, PreBayesMarketPolicyOverride>,
) -> PreBayesMarketPolicyOverride {
    market
        .map(|value| value.to_ascii_uppercase())
        .and_then(|market| override_config.get(&market).cloned())
        .unwrap_or_default()
}

pub fn build_pre_bayes_evidence_filter(
    policy: &PreBayesEvidencePolicy,
    regime_label: &str,
    liquidity_label: &str,
    factor_diagnostics: &FactorDiagnostics,
    multi_timeframe_evidence: &ParsedMultiTimeframeEvidence,
    market: Option<&str>,
) -> PreBayesEvidenceFilter {
    let market_policy = pre_bayes_market_policy_override(market, &policy.market_overrides);
    let hostile_liquidity_penalty = market_policy
        .hostile_liquidity_penalty
        .unwrap_or(policy.hostile_liquidity_penalty);
    let favorable_liquidity_bonus = market_policy
        .favorable_liquidity_bonus
        .unwrap_or(policy.favorable_liquidity_bonus);
    let hostile_liquidity_forces_high_uncertainty = market_policy
        .hostile_liquidity_forces_high_uncertainty
        .unwrap_or(policy.hostile_liquidity_forces_high_uncertainty);
    let raw_factor_alignment = factor_diagnostics.alignment_label.clone();
    let raw_factor_uncertainty = factor_diagnostics.uncertainty_label.clone();
    let raw_multi_timeframe_direction_bias = multi_timeframe_evidence.direction_bias.clone();
    let raw_multi_timeframe_alignment_score = multi_timeframe_evidence.alignment_score;
    let raw_multi_timeframe_entry_alignment_score = multi_timeframe_evidence.entry_alignment_score;
    let mut filtered_market_regime_label = regime_label.to_string();
    let mut filtered_liquidity_context_label = liquidity_label.to_string();
    let mut filtered_factor_alignment = raw_factor_alignment.clone();
    let mut filtered_factor_uncertainty = raw_factor_uncertainty.clone();
    let mut filtered_multi_timeframe_direction_bias = raw_multi_timeframe_direction_bias.clone();
    let filtered_multi_timeframe_alignment_score = raw_multi_timeframe_alignment_score;
    let filtered_multi_timeframe_entry_alignment_score = raw_multi_timeframe_entry_alignment_score;
    let mut conflict_flags = Vec::new();
    let mut rationale = Vec::new();

    if let Some(market) = market {
        rationale.push(format!(
            "market_policy={} hostile_liquidity_penalty={:.3} favorable_liquidity_bonus={:.3} hostile_liquidity_forces_high_uncertainty={}",
            market.to_ascii_uppercase(),
            hostile_liquidity_penalty,
            favorable_liquidity_bonus,
            hostile_liquidity_forces_high_uncertainty
        ));
    }

    let support_gap = (factor_diagnostics.long_support - factor_diagnostics.short_support).abs();
    rationale.push(format!(
        "multi_timeframe_direction_bias={} multi_timeframe_alignment_score={:.3} multi_timeframe_entry_alignment_score={:.3}",
        raw_multi_timeframe_direction_bias,
        raw_multi_timeframe_alignment_score.unwrap_or_default(),
        raw_multi_timeframe_entry_alignment_score.unwrap_or_default()
    ));
    let directional_conflict = matches!(
        (regime_label, raw_factor_alignment.as_str()),
        ("bull", "bearish") | ("bear", "bullish")
    );
    let multi_timeframe_direction_conflict =
        multi_timeframe_direction_conflicts_with(regime_label, &raw_multi_timeframe_direction_bias)
            || multi_timeframe_direction_conflicts_with(
                raw_factor_alignment.as_str(),
                &raw_multi_timeframe_direction_bias,
            );
    let raw_multi_timeframe_resonance_label = classify_multi_timeframe_resonance(
        policy,
        multi_timeframe_direction_conflict,
        multi_timeframe_evidence,
    );
    let mut filtered_multi_timeframe_resonance_label = raw_multi_timeframe_resonance_label.clone();
    if directional_conflict {
        conflict_flags.push("regime_alignment_conflict".to_string());
        filtered_factor_alignment = "mixed".to_string();
        rationale.push(
            "regime and factor alignment disagree, so factor_alignment is neutralized".to_string(),
        );
    }
    if support_gap < policy.min_directional_support_gap {
        conflict_flags.push("low_directional_separation".to_string());
        filtered_factor_alignment = "mixed".to_string();
        rationale.push(format!(
            "long/short support gap {:.3} is too small, so alignment is treated as mixed",
            support_gap
        ));
    }
    if factor_diagnostics.uncertainty >= policy.high_uncertainty_threshold {
        conflict_flags.push("high_factor_uncertainty".to_string());
        filtered_factor_uncertainty = "high".to_string();
        rationale.push(format!(
            "factor uncertainty {:.3} exceeds the hard-evidence comfort band",
            factor_diagnostics.uncertainty
        ));
    }
    if multi_timeframe_direction_conflict {
        conflict_flags.push("multi_timeframe_direction_conflict".to_string());
        filtered_factor_alignment = "mixed".to_string();
        filtered_multi_timeframe_resonance_label = "dislocated".to_string();
        rationale.push(format!(
            "multi-timeframe direction bias '{}' conflicts with regime/alignment, so factor_alignment is neutralized",
            raw_multi_timeframe_direction_bias
        ));
    }
    if raw_multi_timeframe_alignment_score
        .map(|score| score < policy.min_multi_timeframe_alignment_score)
        .unwrap_or(false)
    {
        conflict_flags.push("multi_timeframe_alignment_weak".to_string());
        filtered_factor_alignment = "mixed".to_string();
        if filtered_multi_timeframe_resonance_label != "dislocated" {
            filtered_multi_timeframe_resonance_label = "mixed".to_string();
        }
        rationale.push(format!(
            "multi-timeframe alignment {:.3} is below the policy support floor {:.3}",
            raw_multi_timeframe_alignment_score.unwrap_or_default(),
            policy.min_multi_timeframe_alignment_score
        ));
    }
    if raw_multi_timeframe_entry_alignment_score
        .map(|score| score < policy.min_multi_timeframe_entry_alignment_score)
        .unwrap_or(false)
    {
        conflict_flags.push("multi_timeframe_entry_alignment_weak".to_string());
        filtered_factor_uncertainty = "high".to_string();
        if filtered_multi_timeframe_resonance_label != "dislocated" {
            filtered_multi_timeframe_resonance_label = "mixed".to_string();
        }
        rationale.push(format!(
            "multi-timeframe entry alignment {:.3} is below the policy floor {:.3}, so uncertainty is raised",
            raw_multi_timeframe_entry_alignment_score.unwrap_or_default(),
            policy.min_multi_timeframe_entry_alignment_score
        ));
    }
    if raw_multi_timeframe_direction_bias == "neutral" {
        filtered_multi_timeframe_direction_bias = "neutral".to_string();
    }
    if hostile_liquidity_forces_high_uncertainty
        && liquidity_label == "hostile"
        && filtered_factor_uncertainty == "low"
    {
        conflict_flags.push("hostile_liquidity_requires_high_uncertainty".to_string());
        filtered_factor_uncertainty = "high".to_string();
        rationale.push(
            "hostile liquidity downgrades evidence confidence, so uncertainty is raised"
                .to_string(),
        );
    }

    let mut evidence_quality_score =
        0.55 + support_gap.min(0.5) * 0.50 - factor_diagnostics.uncertainty * 0.35;
    if !directional_conflict {
        evidence_quality_score += 0.15;
    } else {
        evidence_quality_score -= policy.directional_conflict_penalty;
    }
    if filtered_factor_alignment == "mixed" {
        evidence_quality_score -= policy.mixed_alignment_penalty;
    }
    if conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_direction_conflict")
    {
        evidence_quality_score -= policy.multi_timeframe_direction_conflict_penalty;
    }
    if conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_alignment_weak")
    {
        evidence_quality_score -= policy.multi_timeframe_alignment_penalty;
    } else if raw_multi_timeframe_alignment_score
        .map(|score| score >= policy.min_multi_timeframe_alignment_score)
        .unwrap_or(false)
    {
        evidence_quality_score += policy.multi_timeframe_alignment_bonus;
    }
    if conflict_flags
        .iter()
        .any(|flag| flag == "multi_timeframe_entry_alignment_weak")
    {
        evidence_quality_score -= policy.multi_timeframe_entry_penalty;
    }
    if filtered_liquidity_context_label == "hostile" {
        evidence_quality_score -= hostile_liquidity_penalty;
    } else if filtered_liquidity_context_label == "favorable" {
        evidence_quality_score += favorable_liquidity_bonus;
    }
    evidence_quality_score = evidence_quality_score.clamp(0.0, 1.0);

    let gating_status = if evidence_quality_score >= policy.hard_pass_quality_threshold
        && conflict_flags.is_empty()
    {
        "pass_hard".to_string()
    } else if evidence_quality_score >= policy.neutralized_quality_threshold {
        "pass_neutralized".to_string()
    } else {
        filtered_market_regime_label = "range".to_string();
        filtered_liquidity_context_label = "neutral".to_string();
        filtered_factor_alignment = "mixed".to_string();
        filtered_factor_uncertainty = "high".to_string();
        rationale.push(
            "evidence quality is too low, so BBN input is downgraded to neutralized defaults"
                .to_string(),
        );
        filtered_multi_timeframe_direction_bias = "neutral".to_string();
        filtered_multi_timeframe_resonance_label = "mixed".to_string();
        "observe_only".to_string()
    };

    let evidence_assignments = BTreeMap::from([
        (
            "market_regime".to_string(),
            filtered_market_regime_label.clone(),
        ),
        (
            "liquidity_context".to_string(),
            filtered_liquidity_context_label.clone(),
        ),
        (
            "factor_alignment".to_string(),
            filtered_factor_alignment.clone(),
        ),
        (
            "factor_uncertainty".to_string(),
            filtered_factor_uncertainty.clone(),
        ),
        (
            "multi_timeframe_resonance".to_string(),
            filtered_multi_timeframe_resonance_label.clone(),
        ),
    ]);
    rationale.push(format!(
        "pre_bayes_quality_score={:.3} gating_status={}",
        evidence_quality_score, gating_status
    ));
    let uses_soft_evidence = gating_status != "pass_hard";
    let soft_market_regime_distribution = pre_bayes_distribution(
        &["bull", "bear", "range"],
        regime_label,
        &filtered_market_regime_label,
        "range",
        &gating_status,
        evidence_quality_score,
    );
    let soft_liquidity_context_distribution = pre_bayes_distribution(
        &["favorable", "neutral", "hostile"],
        liquidity_label,
        &filtered_liquidity_context_label,
        "neutral",
        &gating_status,
        evidence_quality_score,
    );
    let soft_factor_alignment_distribution = pre_bayes_distribution(
        &["bullish", "mixed", "bearish"],
        &raw_factor_alignment,
        &filtered_factor_alignment,
        "mixed",
        &gating_status,
        evidence_quality_score,
    );
    let soft_factor_uncertainty_distribution = pre_bayes_distribution(
        &["low", "high"],
        &raw_factor_uncertainty,
        &filtered_factor_uncertainty,
        "high",
        &gating_status,
        evidence_quality_score,
    );
    let soft_multi_timeframe_resonance_distribution = pre_bayes_distribution(
        &["aligned", "mixed", "dislocated"],
        &raw_multi_timeframe_resonance_label,
        &filtered_multi_timeframe_resonance_label,
        "mixed",
        &gating_status,
        evidence_quality_score,
    );

    PreBayesEvidenceFilter {
        policy: policy.clone(),
        entry_logic_id: None,
        logic_family: None,
        raw_market_regime_label: regime_label.to_string(),
        raw_liquidity_context_label: liquidity_label.to_string(),
        raw_factor_alignment,
        raw_factor_uncertainty,
        raw_multi_timeframe_direction_bias,
        raw_multi_timeframe_alignment_score,
        raw_multi_timeframe_entry_alignment_score,
        raw_multi_timeframe_resonance_label,
        active_pda_count: 0,
        inversed_pda_count: 0,
        stale_pda_count: 0,
        nearest_active_pda: None,
        nearest_inversed_pda: None,
        filtered_market_regime_label,
        filtered_liquidity_context_label,
        filtered_factor_alignment,
        filtered_factor_uncertainty,
        filtered_multi_timeframe_direction_bias,
        filtered_multi_timeframe_alignment_score,
        filtered_multi_timeframe_entry_alignment_score,
        filtered_multi_timeframe_resonance_label,
        evidence_quality_score,
        gating_status: gating_status.clone(),
        pass_to_bbn: gating_status != "observe_only",
        uses_soft_evidence,
        conflict_flags,
        rationale,
        evidence_assignments,
        soft_market_regime_distribution,
        soft_liquidity_context_distribution,
        soft_factor_alignment_distribution,
        soft_factor_uncertainty_distribution,
        soft_multi_timeframe_resonance_distribution,
    }
}

pub fn env_f64(name: &str, default: f64) -> f64 {
    env::var(name)
        .ok()
        .and_then(|value| value.parse::<f64>().ok())
        .unwrap_or(default)
}

pub fn env_bool(name: &str, default: bool) -> bool {
    env::var(name)
        .ok()
        .and_then(|value| match value.to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => Some(true),
            "0" | "false" | "no" | "off" => Some(false),
            _ => None,
        })
        .unwrap_or(default)
}

pub fn compute_hash(parts: &[impl AsRef<str>]) -> String {
    let mut hasher = DefaultHasher::new();
    for part in parts {
        part.as_ref().hash(&mut hasher);
    }
    format!("{:016x}", hasher.finish())
}

pub fn left_pad(values: Vec<f64>, target_len: usize, fill: f64) -> Vec<f64> {
    if values.len() >= target_len {
        return values[values.len() - target_len..].to_vec();
    }

    let mut padded = vec![fill; target_len - values.len()];
    padded.extend(values);
    padded
}

pub fn env_f64_with_source(name: &str, default: f64) -> (f64, String) {
    match env::var(name)
        .ok()
        .and_then(|value| value.parse::<f64>().ok().map(|parsed| (parsed, value)))
    {
        Some((parsed, raw)) => (parsed, format!("env:{}={}", name, raw)),
        None => (default, "default".to_string()),
    }
}

pub fn env_bool_with_source(name: &str, default: bool) -> (bool, String) {
    match env::var(name).ok() {
        Some(raw) => match raw.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => (true, format!("env:{}={}", name, raw)),
            "0" | "false" | "no" | "off" => (false, format!("env:{}={}", name, raw)),
            _ => (default, "default".to_string()),
        },
        None => (default, "default".to_string()),
    }
}

pub fn family_history_window() -> usize {
    env::var("ICT_ENGINE_FAMILY_HISTORY_WINDOW")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .map(|value| value.clamp(1, 20))
        .unwrap_or(5)
}
