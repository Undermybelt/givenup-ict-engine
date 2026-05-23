use crate::application::orchestration::ExecutionTreeOutput;
use crate::domain::regime::RegimeSegmentationPacket;
use crate::types::TradePlan;

fn transition_hazard_block_threshold() -> f64 {
    std::env::var("ICT_ENGINE_TRANSITION_HAZARD_BLOCK_THRESHOLD")
        .ok()
        .and_then(|raw| raw.parse::<f64>().ok())
        .filter(|value| value.is_finite())
        .unwrap_or(0.60)
}

fn transition_hazard_context_relaxed_threshold() -> f64 {
    std::env::var("ICT_ENGINE_TRANSITION_HAZARD_CONTEXT_RELAXED_THRESHOLD")
        .ok()
        .and_then(|raw| raw.parse::<f64>().ok())
        .filter(|value| value.is_finite())
        .unwrap_or(0.75)
}

pub fn apply_duration_sizing_adjustment(
    mut trade_plan: TradePlan,
    market: &str,
    hybrid_regime: &RegimeSegmentationPacket,
) -> TradePlan {
    let Some(remaining) = hybrid_regime.duration_remaining_expected_bars else {
        return trade_plan;
    };
    let family = hybrid_regime
        .active_regime_cluster
        .as_deref()
        .map(|label| {
            if label.contains("trend") {
                "trend"
            } else if label.contains("range") {
                "range"
            } else {
                "transition"
            }
        })
        .unwrap_or("transition");
    let scale = duration_sizing_scale(market, family, remaining);
    if scale < 1.0 {
        trade_plan.kelly_fraction *= scale;
        trade_plan.position_size *= scale;
        trade_plan.uncertainties.push(format!(
            "duration_sizing_scale={scale:.2} remaining_expected_bars={remaining:.3} market={} family={}",
            market,
            family
        ));
        if scale == 0.0 {
            trade_plan
                .uncertainties
                .push("duration_window_too_short_for_execution_size_zeroed".to_string());
        }
    }
    trade_plan
}

pub fn duration_sizing_scale(market: &str, family: &str, remaining_expected_bars: f64) -> f64 {
    let _ = market;
    match family {
        "trend" => {
            if remaining_expected_bars <= 1.5 {
                0.0
            } else if remaining_expected_bars <= 2.5 {
                0.25
            } else if remaining_expected_bars <= 4.0 {
                0.50
            } else {
                1.0
            }
        }
        "range" => {
            if remaining_expected_bars <= 1.0 {
                0.0
            } else if remaining_expected_bars <= 2.0 {
                0.35
            } else if remaining_expected_bars <= 3.5 {
                0.60
            } else {
                1.0
            }
        }
        _ => {
            if remaining_expected_bars <= 1.5 {
                0.0
            } else if remaining_expected_bars <= 3.0 {
                0.40
            } else if remaining_expected_bars <= 5.0 {
                0.70
            } else {
                1.0
            }
        }
    }
}

pub fn apply_regime_execution_guardrail(
    mut output: ExecutionTreeOutput,
    hybrid_regime: &RegimeSegmentationPacket,
) -> ExecutionTreeOutput {
    let base_transition_hazard_threshold = transition_hazard_block_threshold();
    let pda_disagreement = hybrid_regime
        .evidence
        .iter()
        .any(|line| line == "pda_hybrid_alignment=false");
    let pda_disagreement_execution_accepted = hybrid_regime.evidence.iter().any(|line| {
        matches!(
            line.as_str(),
            "pda_hybrid_alignment_context=orthogonal_root_session_rhythm"
                | "pda_hybrid_alignment_context=trend_pullback_structure_supplement"
        )
    });
    let effective_pda_disagreement = pda_disagreement && !pda_disagreement_execution_accepted;
    let transition_hazard_threshold = if pda_disagreement_execution_accepted {
        transition_hazard_context_relaxed_threshold().max(base_transition_hazard_threshold)
    } else {
        base_transition_hazard_threshold
    };
    let high_transition_hazard =
        hybrid_regime.transition_hazard.unwrap_or_default() >= transition_hazard_threshold;
    output.hybrid_transition_hazard = hybrid_regime.transition_hazard;
    output.pda_hybrid_alignment = Some(!effective_pda_disagreement);
    let low_remaining_duration = hybrid_regime
        .duration_remaining_expected_bars
        .unwrap_or(f64::INFINITY)
        <= 1.5;
    let short_remaining_duration = hybrid_regime
        .duration_remaining_expected_bars
        .unwrap_or(f64::INFINITY)
        <= 2.5;
    if high_transition_hazard || effective_pda_disagreement || low_remaining_duration {
        output.gate_status = "observe".to_string();
        output.branch = "transition_guardrail".to_string();
        output.execution_bias = "guarded".to_string();
        output.branch_probability = output.branch_probability.min(0.50);
        output.posterior_uncertainty = output.posterior_uncertainty.max(0.60);
        output.decision_hint = if low_remaining_duration {
            "execution_guarded_due_to_low_remaining_regime_duration".to_string()
        } else if effective_pda_disagreement {
            "execution_guarded_due_to_pda_hybrid_disagreement".to_string()
        } else {
            "execution_guarded_due_to_high_transition_hazard".to_string()
        };
        output.split_reason_lineage.push(format!(
            "hybrid_transition_hazard={:.3} threshold={:.3}",
            hybrid_regime.transition_hazard.unwrap_or_default(),
            transition_hazard_threshold
        ));
        if effective_pda_disagreement {
            output
                .split_reason_lineage
                .push("pda_hybrid_alignment=false".to_string());
            for prefix in [
                "pda_sequence_h1_second_expansion_support=",
                "pda_sequence_h0_no_second_expansion_support=",
            ] {
                if let Some(line) = hybrid_regime
                    .evidence
                    .iter()
                    .find(|line| line.starts_with(prefix))
                {
                    output.split_reason_lineage.push(line.clone());
                }
            }
        }
        if low_remaining_duration || short_remaining_duration {
            output.split_reason_lineage.push(format!(
                "duration_remaining_expected_bars={:.3}",
                hybrid_regime
                    .duration_remaining_expected_bars
                    .unwrap_or_default()
            ));
        }
    } else if short_remaining_duration {
        output.execution_bias = "passive".to_string();
        output.split_reason_lineage.push(format!(
            "duration_remaining_expected_bars={:.3} → execution_bias=passive",
            hybrid_regime
                .duration_remaining_expected_bars
                .unwrap_or_default()
        ));
    }
    if pda_disagreement_execution_accepted {
        output
            .split_reason_lineage
            .push("pda_hybrid_alignment=false_context_accepted=true".to_string());
        output.split_reason_lineage.push(format!(
            "transition_hazard_context_threshold={:.3} base_threshold={:.3}",
            transition_hazard_threshold, base_transition_hazard_threshold
        ));
    }
    output
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;

    fn ready_execution_output() -> ExecutionTreeOutput {
        ExecutionTreeOutput {
            gate_status: "ready".to_string(),
            branch: "fill_viable".to_string(),
            execution_bias: "aggressive".to_string(),
            branch_probability: 0.72,
            posterior_uncertainty: 0.30,
            decision_hint: "execution_first_fill".to_string(),
            ..ExecutionTreeOutput::default()
        }
    }

    fn regime_packet(evidence: Vec<String>) -> RegimeSegmentationPacket {
        RegimeSegmentationPacket {
            method: "hybrid_regime_first_pass_v1".to_string(),
            segmentation_version: "v2".to_string(),
            active_regime_cluster: Some("trend_impulse".to_string()),
            transition_hazard: Some(0.22),
            duration_elapsed_bars: Some(2),
            duration_model: Some("negative_binomial".to_string()),
            duration_remaining_expected_bars: Some(4.0),
            regime_membership: BTreeMap::new(),
            feature_attribution: BTreeMap::new(),
            evidence,
            wasserstein_label: Some("trend_impulse".to_string()),
            wasserstein_distance: Some(0.12),
            governor_confidence: Some(0.70),
            governor_entropy: Some(0.90),
            governor_min_hold_active: Some(false),
            timeframe_alignment: Some(true),
            timeframe_alignment_score: Some(1.0),
        }
    }

    #[test]
    fn guardrail_keeps_pda_disagreement_observe_but_preserves_h1_h0_lineage() {
        let output = apply_regime_execution_guardrail(
            ready_execution_output(),
            &regime_packet(vec![
                "pda_hybrid_alignment=false".to_string(),
                "pda_sequence_h1_second_expansion_support=0.7715".to_string(),
                "pda_sequence_h0_no_second_expansion_support=0.2285".to_string(),
            ]),
        );

        assert_eq!(output.gate_status, "observe");
        assert_eq!(output.branch, "transition_guardrail");
        assert_eq!(
            output.decision_hint,
            "execution_guarded_due_to_pda_hybrid_disagreement"
        );
        assert!(output
            .split_reason_lineage
            .contains(&"pda_sequence_h1_second_expansion_support=0.7715".to_string()));
        assert!(output
            .split_reason_lineage
            .contains(&"pda_sequence_h0_no_second_expansion_support=0.2285".to_string()));
    }

    #[test]
    fn guardrail_accepts_session_rhythm_orthogonal_pda_context_without_lowering_hazard_gate() {
        let output = apply_regime_execution_guardrail(
            ready_execution_output(),
            &regime_packet(vec![
                "pda_hybrid_alignment=false".to_string(),
                "pda_hybrid_alignment_context=orthogonal_root_session_rhythm".to_string(),
            ]),
        );

        assert_eq!(output.gate_status, "ready");
        assert_eq!(output.branch, "fill_viable");
        assert_eq!(output.pda_hybrid_alignment, Some(true));
        assert!(output
            .split_reason_lineage
            .contains(&"pda_hybrid_alignment=false_context_accepted=true".to_string()));
        assert!(output.split_reason_lineage.contains(
            &"transition_hazard_context_threshold=0.750 base_threshold=0.600".to_string()
        ));

        let mut moderately_high_hazard = regime_packet(vec![
            "pda_hybrid_alignment=false".to_string(),
            "pda_hybrid_alignment_context=orthogonal_root_session_rhythm".to_string(),
        ]);
        moderately_high_hazard.transition_hazard = Some(0.70);
        let relaxed =
            apply_regime_execution_guardrail(ready_execution_output(), &moderately_high_hazard);
        assert_eq!(relaxed.gate_status, "ready");
        assert_eq!(relaxed.branch, "fill_viable");

        let mut high_hazard = regime_packet(vec![
            "pda_hybrid_alignment=false".to_string(),
            "pda_hybrid_alignment_context=orthogonal_root_session_rhythm".to_string(),
        ]);
        high_hazard.transition_hazard = Some(0.78);
        let blocked = apply_regime_execution_guardrail(ready_execution_output(), &high_hazard);
        assert_eq!(blocked.gate_status, "observe");
        assert_eq!(blocked.branch, "transition_guardrail");
        assert_eq!(
            blocked.decision_hint,
            "execution_guarded_due_to_high_transition_hazard"
        );
    }
}
