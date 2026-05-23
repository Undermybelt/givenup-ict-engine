use super::*;
use ict_engine::application::provider_catalog::ProviderCatalogAgentSurface;
use ict_engine::state::ArtifactDecisionSummary;

#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct OfflineStructuralSupportHintInput {
    pub baseline_support: f64,
    pub aggregate_return: Option<f64>,
    pub execution_readiness: Option<f64>,
    pub comparable_to_previous: bool,
    pub feedback_records_applied: usize,
    pub conformal_coverage_1sigma: Option<f64>,
    pub regime_break_penalty: Option<f64>,
    pub structural_break_detected: Option<bool>,
    pub best_factor_composite_score: Option<f64>,
    pub quality_delta: Option<f64>,
    pub score_before: Option<f64>,
    pub score_after: Option<f64>,
    pub baseline_available: Option<bool>,
    pub accepted: Option<bool>,
    pub artifact_validation_bias: Option<f64>,
}

#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct ResearchStructuralSupportInput {
    pub baseline_composite_score: Option<f64>,
    pub aggregate_return: f64,
    pub execution_readiness: Option<f64>,
    pub comparable_to_previous: bool,
    pub feedback_records_applied: usize,
    pub conformal_coverage_1sigma: Option<f64>,
    pub regime_break_penalty: Option<f64>,
    pub structural_break_detected: Option<bool>,
    pub quality_delta: Option<f64>,
    pub family_avg_score: Option<f64>,
}

#[derive(Debug, Clone, Copy)]
pub(crate) struct MutationStructuralSupportInput<'a> {
    pub baseline_composite_score: Option<f64>,
    pub aggregate_return: f64,
    pub execution_readiness: Option<f64>,
    pub comparable_to_previous: bool,
    pub feedback_records_applied: usize,
    pub conformal_coverage_1sigma: Option<f64>,
    pub regime_break_penalty: Option<f64>,
    pub structural_break_detected: Option<bool>,
    pub evaluation: &'a FactorMutationEvaluation,
}

#[derive(Debug, Clone, Copy, Default)]
pub(crate) struct BacktestStructuralSupportInput {
    pub baseline_composite_score: Option<f64>,
    pub aggregate_return: f64,
    pub execution_readiness: Option<f64>,
    pub comparable_to_previous: bool,
    pub feedback_records_applied: usize,
    pub conformal_coverage_1sigma: Option<f64>,
    pub regime_break_penalty: Option<f64>,
    pub structural_break_detected: Option<bool>,
    pub quality_delta: Option<f64>,
}

pub(crate) fn offline_structural_support_hint(input: OfflineStructuralSupportHintInput) -> f64 {
    let mut support = input.baseline_support.clamp(0.0, 1.0);
    if let Some(readiness) = input.execution_readiness {
        support = (support * 0.55 + readiness.clamp(0.0, 1.0) * 0.45).clamp(0.0, 1.0);
    }
    if let Some(aggregate_return) = input.aggregate_return {
        let return_bias = (aggregate_return * 4.0).clamp(-0.20, 0.20);
        support = (support + return_bias).clamp(0.0, 1.0);
    }
    if input.comparable_to_previous {
        support = (support + 0.05).clamp(0.0, 1.0);
    } else {
        support = (support - 0.03).clamp(0.0, 1.0);
    }
    if input.feedback_records_applied > 0 {
        let feedback_bias = (input.feedback_records_applied as f64 / 20.0).min(1.0) * 0.05;
        support = (support + feedback_bias).clamp(0.0, 1.0);
    }
    if let Some(coverage) = input.conformal_coverage_1sigma {
        let coverage_bias = ((coverage - 0.55) / 0.35).clamp(-0.15, 0.15);
        support = (support + coverage_bias).clamp(0.0, 1.0);
    }
    if let Some(regime_break_penalty) = input.regime_break_penalty {
        support = (support - regime_break_penalty.clamp(0.0, 0.25)).clamp(0.0, 1.0);
    }
    if matches!(input.structural_break_detected, Some(true)) {
        support = (support - 0.08).clamp(0.0, 1.0);
    }
    if let Some(score) = input.best_factor_composite_score {
        let score_bias = (score - 0.50).clamp(-0.10, 0.15);
        support = (support + score_bias).clamp(0.0, 1.0);
    }
    if let Some(score_delta) = input.quality_delta {
        support = (support + score_delta.clamp(-0.10, 0.10)).clamp(0.0, 1.0);
    }
    if let Some(artifact_validation_bias) = input.artifact_validation_bias {
        support = (support + artifact_validation_bias.clamp(-0.12, 0.12)).clamp(0.0, 1.0);
    }
    if let (Some(before), Some(after)) = (input.score_before, input.score_after) {
        support = (support + (after - before).clamp(-0.10, 0.10)).clamp(0.0, 1.0);
    }
    if let Some(baseline_available) = input.baseline_available {
        support = if baseline_available {
            (support + 0.03).clamp(0.0, 1.0)
        } else {
            (support - 0.03).clamp(0.0, 1.0)
        };
    }
    if let Some(accepted) = input.accepted {
        support = if accepted {
            (support + 0.08).clamp(0.0, 1.0)
        } else {
            (support - 0.08).clamp(0.0, 1.0)
        };
    }
    support
}

pub(crate) struct BuildAnalyzeAgentPromptsInput<'a> {
    pub(crate) symbol: &'a str,
    pub(crate) decision: &'a ProbabilisticDecisionSnapshot,
    pub(crate) factor_diagnostics: &'a FactorDiagnostics,
    pub(crate) pre_bayes_evidence_filter: &'a PreBayesEvidenceFilter,
    pub(crate) canonical_structural_regime_posterior:
        Option<&'a ict_engine::state::CanonicalStructuralRegimePosterior>,
    pub(crate) factor_ranking: &'a [PersistedFactorRanking],
    pub(crate) factor_iteration_queue: &'a [FactorIterationPrompt],
    pub(crate) feedback_history_summary: &'a FeedbackHistorySummary,
    pub(crate) trade_plan: &'a TradePlan,
    pub(crate) dataset_comparability: &'a DatasetComparability,
    pub(crate) decision_hint: &'a str,
    pub(crate) multi_timeframe_summary: &'a [String],
}

pub(crate) fn build_analyze_agent_prompts(
    input: BuildAnalyzeAgentPromptsInput<'_>,
) -> AgentPromptPack {
    let BuildAnalyzeAgentPromptsInput {
        symbol,
        decision,
        factor_diagnostics,
        pre_bayes_evidence_filter,
        canonical_structural_regime_posterior,
        factor_ranking,
        factor_iteration_queue,
        feedback_history_summary,
        trade_plan,
        dataset_comparability,
        decision_hint,
        multi_timeframe_summary,
    } = input;
    let canonical_structural_regime_summary =
        compact_canonical_structural_regime_summary(canonical_structural_regime_posterior);
    let mut pack = factor_iteration_prompt_pack(
        symbol,
        factor_ranking,
        factor_iteration_queue,
        feedback_history_summary,
    );
    pack.workflow = format!(
        "Use current market analysis plus stored factor scorecards to decide whether the present trade plan is supported, overfit, or missing evidence for {}.",
        symbol
    );
    pack.prompts.insert(
        0,
        dataset_audit_prompt(symbol, "analyze", None, 0, None, "analyze"),
    );
    pack.prompts.insert(
        1,
        AgentPrompt::new(AgentPromptInput {
            id: "pre_bayes_evidence_review".to_string(),
            stage: "pre_bayes_filter".to_string(),
            priority: "high".to_string(),
            objective: "Review whether raw regime/liquidity/factor evidence should be passed to BBN directly or neutralized first.".to_string(),
            system_prompt: "You are the pre-bayes evidence gate. Compare raw labels with filtered labels, conflicts, and evidence quality before trusting the downstream Bayesian inference.".to_string(),
            user_prompt: format!(
                "Symbol={} raw_market_regime={} raw_liquidity_context={} raw_factor_alignment={} raw_factor_uncertainty={} raw_mtf_direction={} raw_mtf_alignment={:.3} raw_mtf_entry_alignment={:.3} raw_mtf_resonance={} filtered_market_regime={} filtered_liquidity_context={} filtered_factor_alignment={} filtered_factor_uncertainty={} filtered_mtf_direction={} filtered_mtf_alignment={:.3} filtered_mtf_entry_alignment={:.3} filtered_mtf_resonance={} evidence_quality_score={:.3} gating_status={} uses_soft_evidence={} conflict_flags={:?} rationale={:?} soft_market_regime={:?} soft_liquidity_context={:?} soft_factor_alignment={:?} soft_factor_uncertainty={:?} soft_mtf_resonance={:?}",
                symbol,
                pre_bayes_evidence_filter.raw_market_regime_label,
                pre_bayes_evidence_filter.raw_liquidity_context_label,
                pre_bayes_evidence_filter.raw_factor_alignment,
                pre_bayes_evidence_filter.raw_factor_uncertainty,
                pre_bayes_evidence_filter.raw_multi_timeframe_direction_bias,
                pre_bayes_evidence_filter
                    .raw_multi_timeframe_alignment_score
                    .unwrap_or_default(),
                pre_bayes_evidence_filter
                    .raw_multi_timeframe_entry_alignment_score
                    .unwrap_or_default(),
                pre_bayes_evidence_filter.raw_multi_timeframe_resonance_label,
                pre_bayes_evidence_filter.filtered_market_regime_label,
                pre_bayes_evidence_filter.filtered_liquidity_context_label,
                pre_bayes_evidence_filter.filtered_factor_alignment,
                pre_bayes_evidence_filter.filtered_factor_uncertainty,
                pre_bayes_evidence_filter.filtered_multi_timeframe_direction_bias,
                pre_bayes_evidence_filter
                    .filtered_multi_timeframe_alignment_score
                    .unwrap_or_default(),
                pre_bayes_evidence_filter
                    .filtered_multi_timeframe_entry_alignment_score
                    .unwrap_or_default(),
                pre_bayes_evidence_filter.filtered_multi_timeframe_resonance_label,
                pre_bayes_evidence_filter.evidence_quality_score,
                pre_bayes_evidence_filter.gating_status,
                pre_bayes_evidence_filter.uses_soft_evidence,
                pre_bayes_evidence_filter.conflict_flags,
                pre_bayes_evidence_filter.rationale,
                pre_bayes_evidence_filter.soft_market_regime_distribution,
                pre_bayes_evidence_filter.soft_liquidity_context_distribution,
                pre_bayes_evidence_filter.soft_factor_alignment_distribution,
                pre_bayes_evidence_filter.soft_factor_uncertainty_distribution,
                pre_bayes_evidence_filter.soft_multi_timeframe_resonance_distribution
            ),
            success_criteria: vec![
                "State explicitly whether the filtered evidence should be trusted as hard evidence or soft evidence".to_string(),
                "If regime and factor alignment conflict, prefer neutralization over direct Bayesian commitment".to_string(),
            ],
            suggested_files: vec![
                "src/analyze_shared.rs".to_string(),
                "src/bbn/trading/update.rs".to_string(),
                "src/factor_lab/engine.rs".to_string(),
            ],
        }),
    );
    if pre_bayes_evidence_filter.uses_soft_evidence {
        pack.prompts.insert(
            2,
            AgentPrompt::new(AgentPromptInput {
                id: "pre_bayes_soft_evidence_review".to_string(),
                stage: "pre_bayes_soft_evidence".to_string(),
                priority: "high".to_string(),
                objective: "Review whether soft evidence diverges materially from filtered labels before trusting BBN output.".to_string(),
                system_prompt: "You are the pre-bayes soft-evidence reviewer. Compare filtered states with soft evidence distributions and explain whether the Bayesian layer is receiving stable or ambiguous evidence.".to_string(),
                user_prompt: format!(
                    "Symbol={} filtered_assignments={:?} soft_market_regime={:?} soft_liquidity_context={:?} soft_factor_alignment={:?} soft_factor_uncertainty={:?} soft_mtf_resonance={:?}",
                    symbol,
                    pre_bayes_evidence_filter.evidence_assignments,
                    pre_bayes_evidence_filter.soft_market_regime_distribution,
                    pre_bayes_evidence_filter.soft_liquidity_context_distribution,
                    pre_bayes_evidence_filter.soft_factor_alignment_distribution,
                    pre_bayes_evidence_filter.soft_factor_uncertainty_distribution,
                    pre_bayes_evidence_filter.soft_multi_timeframe_resonance_distribution
                ),
                success_criteria: vec![
                    "Call out when the dominant soft-evidence state diverges from the filtered hard label".to_string(),
                    "If entropy is high, prefer observe-only or neutralized review over confident Bayesian commitment".to_string(),
                ],
                suggested_files: vec![
                    "src/analyze_shared.rs".to_string(),
                    "src/bbn/node.rs".to_string(),
                    "src/bbn/trading/update.rs".to_string(),
                ],
            }),
        );
    }
    pack.prompts.insert(
        if pre_bayes_evidence_filter.uses_soft_evidence { 3 } else { 2 },
        AgentPrompt::new(AgentPromptInput {
            id: "analysis_market_review".to_string(),
            stage: "market_analysis".to_string(),
            priority: "high".to_string(),
            objective: "Review the current market conclusion and identify whether factor evidence supports the selected direction.".to_string(),
            system_prompt: "You are the market-review agent. Challenge the current trade direction using price-action evidence, factor diagnostics, and uncertainty. Do not change factor definitions here; decide whether the current conclusion is supported or should be downgraded.".to_string(),
            user_prompt: format!(
                "Symbol={} decision_hint={} dataset_comparability={{comparable:{}, reason:{}}} canonical_structural_regime={} multi_timeframe_summary={:?} selected_direction={:?} selected_score={:.3} selected_win_probability={:.3} trade_direction={:?} posterior={:.3} factor_alignment={} factor_uncertainty={} long_support={:.3} short_support={:.3} uncertainty={:.3} bullish_factors={:?} bearish_factors={:?}",
                symbol,
                decision_hint,
                dataset_comparability.comparable,
                dataset_comparability.reason,
                canonical_structural_regime_summary,
                multi_timeframe_summary,
                decision.selected_direction,
                decision.selected_score,
                decision.selected_win_probability,
                trade_plan.direction,
                trade_plan.posterior,
                factor_diagnostics.alignment_label,
                factor_diagnostics.uncertainty_label,
                factor_diagnostics.long_support,
                factor_diagnostics.short_support,
                factor_diagnostics.uncertainty,
                factor_diagnostics
                    .bullish_factors
                    .iter()
                    .take(3)
                    .map(|factor| format!("{}:{:.3}", factor.factor_name, factor.weighted_score))
                    .collect::<Vec<_>>(),
                factor_diagnostics
                    .bearish_factors
                    .iter()
                    .take(3)
                    .map(|factor| format!("{}:{:.3}", factor.factor_name, factor.weighted_score))
                    .collect::<Vec<_>>()
            ),
            success_criteria: vec![
                "Explicitly name which factors support long, which support short, and which only add uncertainty".to_string(),
                "If uncertainty is high, recommend what evidence the next agent should wait for".to_string(),
            ],
            suggested_files: vec![
                "src/analyze_shared.rs".to_string(),
                "src/factor_lab/engine.rs".to_string(),
                "src/bbn/trading/topology.rs".to_string(),
            ],
        }),
    );
    pack
}

pub(crate) fn analyze_signal_rankings(
    signals: &[ict_engine::factor_lab::FactorSignal],
    regime: Regime,
) -> Vec<PersistedFactorRanking> {
    let mut rankings = signals
        .iter()
        .map(|signal| {
            let confidence_score = signal.confidence.clamp(0.0, 1.0);
            let signal_score = signal.regime_adjusted_score.abs().clamp(0.0, 1.0);
            let reliability_score = signal.posterior_reliability.clamp(0.0, 1.0);
            let composite_score =
                (0.45 * confidence_score + 0.35 * signal_score + 0.20 * reliability_score)
                    .clamp(0.0, 1.0);
            let mut weaknesses = Vec::new();
            if signal.direction == Direction::Neutral {
                weaknesses.push("neutral_signal".to_string());
            }
            if signal.confidence < 0.35 {
                weaknesses.push("low_live_confidence".to_string());
            }
            if signal.posterior_reliability < 0.45 {
                weaknesses.push("low_posterior_reliability".to_string());
            }

            let iteration_action = if signal.direction == Direction::Neutral || signal.confidence < 0.35
            {
                "observe"
            } else if composite_score >= 0.65 {
                "keep"
            } else {
                "tune"
            };

            PersistedFactorRanking {
                factor_name: signal.factor_name.clone(),
                regime: ict_engine::state::regime_key(regime).to_string(),
                ic: 0.0,
                ir: 0.0,
                backtest_return: 0.0,
                sharpe: 0.0,
                stability: reliability_score,
                win_rate: 0.0,
                profit_factor: 1.0,
                trade_count: 0,
                conformal_coverage_1sigma: 0.0,
                conformal_miscoverage_1sigma: 0.0,
                mean_prediction_interval_half_width: 0.0,
                worst_window_miscoverage: 0.0,
                regime_break_penalty: 0.0,
                weight: signal.weight,
                regime_scores: BTreeMap::from([(
                    ict_engine::state::regime_key(regime).to_string(),
                    signal_score,
                )]),
                composite_score,
                score_breakdown: BTreeMap::from([
                    ("current_confidence".to_string(), confidence_score),
                    ("current_signal_strength".to_string(), signal_score),
                    ("posterior_reliability".to_string(), reliability_score),
                ]),
                grade: if composite_score >= 0.85 {
                    "A".to_string()
                } else if composite_score >= 0.70 {
                    "B".to_string()
                } else if composite_score >= 0.55 {
                    "C".to_string()
                } else if composite_score >= 0.40 {
                    "D".to_string()
                } else {
                    "F".to_string()
                },
                iteration_action: iteration_action.to_string(),
                replacement_candidate: false,
                weaknesses,
                agent_prompt: format!(
                    "Analyze-phase snapshot for '{}'. direction={:?} confidence={:.2} weighted_signal={:.2}. Treat as provisional evidence and confirm with factor-research before any promotion or replacement decision.",
                    signal.factor_name,
                    signal.direction,
                    signal.confidence,
                    signal.regime_adjusted_score
                ),
            }
        })
        .collect::<Vec<_>>();
    rankings.sort_by(|a, b| {
        b.composite_score
            .partial_cmp(&a.composite_score)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    rankings
}

pub(crate) fn structural_baseline_support(score: Option<f64>, fallback: f64) -> f64 {
    score.unwrap_or(fallback).clamp(0.0, 1.0)
}

pub(crate) fn artifact_validation_support_bias(summary: &ArtifactDecisionSummary) -> f64 {
    let mut bias: f64 = match summary.consumed_trend_status.as_str() {
        "validated_positive" | "validated_improving" => 0.08,
        "validated_negative" | "validated_regressing" => -0.10,
        "validated_neutral" => -0.02,
        _ => 0.0,
    };
    bias += match summary.promotion_strength.as_str() {
        "high" => 0.03,
        "medium" => 0.01,
        _ => 0.0,
    };
    bias += match summary.rollback_strength.as_str() {
        "high" => -0.03,
        "medium" => -0.01,
        _ => 0.0,
    };
    bias.clamp(-0.12, 0.12)
}

pub(crate) fn structural_support_hint_for_analyze(
    posterior_confidence: f64,
    execution_readiness: Option<f64>,
    comparable_to_previous: bool,
    feedback_records_applied: usize,
) -> f64 {
    offline_structural_support_hint(OfflineStructuralSupportHintInput {
        baseline_support: structural_baseline_support(Some(posterior_confidence), 0.50),
        aggregate_return: None,
        execution_readiness,
        comparable_to_previous,
        feedback_records_applied,
        conformal_coverage_1sigma: None,
        regime_break_penalty: None,
        structural_break_detected: None,
        best_factor_composite_score: None,
        quality_delta: None,
        score_before: None,
        score_after: None,
        baseline_available: None,
        accepted: None,
        artifact_validation_bias: None,
    })
}

pub(crate) fn regime_profit_branch_assignment_entries_from_feedback_history(
    learning_state: &LearningState,
) -> Option<Vec<(String, String)>> {
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for record in &learning_state.feedback_history {
        let Some(refs) = record.structural_feedback.as_ref() else {
            continue;
        };
        let path = refs.path_id.trim();
        if !refs.followed_path || !regime_profit_branch_path_is_exact(path) {
            continue;
        }
        *counts.entry(path.to_string()).or_default() += 1;
    }

    let mut ranked: Vec<(String, usize)> = counts.into_iter().collect();
    ranked.sort_by(|left, right| right.1.cmp(&left.1).then_with(|| left.0.cmp(&right.0)));
    let (branch_path, count) = ranked.first()?;
    if *count < 2 {
        return None;
    }
    if ranked
        .get(1)
        .is_some_and(|(_, next_count)| next_count == count)
    {
        return None;
    }

    let mut entries = regime_profit_branch_assignment_entries_from_path(branch_path);
    entries.push((
        "regime_profit_branch_path_source".to_string(),
        "structural_feedback_history".to_string(),
    ));
    entries.push((
        "regime_profit_branch_path_feedback_count".to_string(),
        count.to_string(),
    ));
    Some(entries)
}

pub(crate) fn regime_profit_branch_path_is_exact(path: &str) -> bool {
    path.split(" -> ")
        .map(str::trim)
        .filter(|segment| !segment.is_empty())
        .count()
        >= 4
}

pub(crate) fn regime_profit_branch_assignment_entries_from_path(
    branch_path: &str,
) -> Vec<(String, String)> {
    let segments: Vec<&str> = branch_path
        .split(" -> ")
        .map(str::trim)
        .filter(|segment| !segment.is_empty())
        .collect();
    let mut entries = vec![(
        "regime_profit_branch_path".to_string(),
        branch_path.to_string(),
    )];
    if let Some(main) = segments.first() {
        entries.push(("parent_regime_root".to_string(), (*main).to_string()));
        entries.push(("main_regime".to_string(), (*main).to_string()));
    }
    if let Some(sub) = segments.get(1) {
        entries.push(("sub_regime".to_string(), (*sub).to_string()));
    }
    if let Some(sub_sub) = segments.get(2) {
        entries.push((
            "sub_sub_regime_or_profit_factor".to_string(),
            (*sub_sub).to_string(),
        ));
    }
    if segments.len() > 3 {
        entries.push(("profit_factor".to_string(), segments[3..].join(" -> ")));
    }
    entries
}

pub(crate) fn pre_bayes_branch_direction_context_from_assignment_entries(
    entries: &[(String, String)],
) -> Option<PreBayesBranchDirectionContext<'_>> {
    let branch_path = entries
        .iter()
        .find(|(key, _)| key == "regime_profit_branch_path")
        .map(|(_, value)| value.trim())
        .filter(|value| !value.is_empty())?;
    let trade_direction = entries
        .iter()
        .find(|(key, _)| key == "trade_direction")
        .map(|(_, value)| value.trim())
        .filter(|value| !value.is_empty())?;
    Some(PreBayesBranchDirectionContext {
        regime_profit_branch_path: branch_path,
        trade_direction,
    })
}

pub(crate) fn structural_support_hint_for_research(input: ResearchStructuralSupportInput) -> f64 {
    offline_structural_support_hint(OfflineStructuralSupportHintInput {
        baseline_support: structural_baseline_support(input.baseline_composite_score, 0.50),
        aggregate_return: Some(input.aggregate_return),
        execution_readiness: input.execution_readiness,
        comparable_to_previous: input.comparable_to_previous,
        feedback_records_applied: input.feedback_records_applied,
        conformal_coverage_1sigma: input.conformal_coverage_1sigma,
        regime_break_penalty: input.regime_break_penalty,
        structural_break_detected: input.structural_break_detected,
        best_factor_composite_score: input.family_avg_score.or(input.baseline_composite_score),
        quality_delta: input.quality_delta,
        score_before: None,
        score_after: None,
        baseline_available: None,
        accepted: None,
        artifact_validation_bias: None,
    })
}

pub(crate) fn structural_support_hint_for_mutation(
    input: MutationStructuralSupportInput<'_>,
) -> f64 {
    offline_structural_support_hint(OfflineStructuralSupportHintInput {
        baseline_support: structural_baseline_support(
            Some(input.evaluation.metrics_after.best_factor_composite_score)
                .or(input.baseline_composite_score),
            0.50,
        ),
        aggregate_return: Some(input.aggregate_return),
        execution_readiness: input.execution_readiness,
        comparable_to_previous: input.comparable_to_previous,
        feedback_records_applied: input.feedback_records_applied,
        conformal_coverage_1sigma: input.conformal_coverage_1sigma,
        regime_break_penalty: input.regime_break_penalty,
        structural_break_detected: input.structural_break_detected,
        best_factor_composite_score: Some(
            input.evaluation.metrics_after.best_factor_composite_score,
        ),
        quality_delta: Some(input.evaluation.score_delta),
        score_before: Some(input.evaluation.score_before),
        score_after: Some(input.evaluation.score_after),
        baseline_available: Some(input.evaluation.baseline_available),
        accepted: Some(input.evaluation.accepted),
        artifact_validation_bias: None,
    })
}

pub(crate) fn structural_support_hint_for_backtest(input: BacktestStructuralSupportInput) -> f64 {
    offline_structural_support_hint(OfflineStructuralSupportHintInput {
        baseline_support: structural_baseline_support(input.baseline_composite_score, 0.50),
        aggregate_return: Some(input.aggregate_return),
        execution_readiness: input.execution_readiness,
        comparable_to_previous: input.comparable_to_previous,
        feedback_records_applied: input.feedback_records_applied,
        conformal_coverage_1sigma: input.conformal_coverage_1sigma,
        regime_break_penalty: input.regime_break_penalty,
        structural_break_detected: input.structural_break_detected,
        best_factor_composite_score: input.baseline_composite_score,
        quality_delta: input.quality_delta,
        score_before: None,
        score_after: None,
        baseline_available: None,
        accepted: None,
        artifact_validation_bias: None,
    })
}

pub(crate) fn structural_prior_seed_from_support_hint(
    source_label: &str,
    support: f64,
) -> ict_engine::state::StructuralPriorSeed {
    let (observations, wins, breakevens, losses) = if support >= 0.75 {
        (3, 2, 1, 0)
    } else if support >= 0.60 {
        (2, 1, 1, 0)
    } else if support >= 0.50 {
        (1, 0, 1, 0)
    } else {
        (1, 0, 0, 1)
    };
    ict_engine::state::StructuralPriorSeed {
        source_label: source_label.to_string(),
        tempering_coefficient: Some(support.clamp(0.0, 1.0)),
        observations,
        followed_count: observations,
        wins,
        losses,
        breakevens,
        invalidated: 0,
        abandoned: 0,
        not_followed: 0,
        avg_pnl: (support - 0.5) * 0.04,
    }
}

pub(crate) fn apply_offline_structural_prior_seed(
    learning_state: &mut LearningState,
    snapshot: &WorkflowSnapshot,
    recommendation_id: &str,
    recommended_at: chrono::DateTime<chrono::Utc>,
    support_hint: f64,
    note: &str,
) {
    // Offline analyze persistence should not block on live provider/runtime probes.
    // Structural prior seeding only needs a stable agent surface shape here.
    let provider_status_agent = ProviderCatalogAgentSurface::default();
    if let Some(bundle) =
        ict_engine::application::orchestration::build_structural_recommended_path_bundle_artifact_with_prior_state(
            snapshot,
            &provider_status_agent,
            learning_state.feedback_history.as_slice(),
            &learning_state.structural_prior_state,
        )
    {
        let branch_id = bundle
            .scenario_id
            .strip_prefix("scenario:")
            .unwrap_or(bundle.scenario_id.as_str())
            .to_string();
        let node_id = branch_id
            .rsplit_once(':')
            .map(|(prefix, _)| prefix.to_string())
            .unwrap_or_else(|| branch_id.clone());
        let refs = ict_engine::state::StructuralFeedbackRefs {
            protocol_version: "structural-prior-seed-v1".to_string(),
            recommendation_id: recommendation_id.to_string(),
            recommended_at: recommended_at.to_rfc3339(),
            node_id,
            branch_id,
            scenario_id: bundle.scenario_id.clone(),
            path_id: bundle.path_id.clone(),
            followed_path: true,
            exit_reason: Some("offline_prior_seed".to_string()),
            notes: Some(note.to_string()),
        };
        let support = ((bundle.current_posterior + bundle.composite_score + support_hint) / 3.0)
            .clamp(0.0, 1.0);
        let seed = structural_prior_seed_from_support_hint(note, support);
        learning_state.apply_structural_prior_seed(&refs, &seed);
    }
}

pub(crate) struct AnalyzeStageTrace {
    path: Option<std::path::PathBuf>,
    started_at: std::time::Instant,
}

impl AnalyzeStageTrace {
    pub(crate) fn maybe_from_env() -> Self {
        static STARTED_AT: std::sync::OnceLock<std::time::Instant> = std::sync::OnceLock::new();
        let path = std::env::var("ICT_ENGINE_ANALYZE_STAGE_TRACE_FILE")
            .ok()
            .map(|value| value.trim().to_string())
            .filter(|value| !value.is_empty())
            .map(std::path::PathBuf::from);
        Self {
            path,
            started_at: *STARTED_AT.get_or_init(std::time::Instant::now),
        }
    }

    pub(crate) fn event<S: AsRef<str>>(&self, stage: S) {
        let Some(path) = &self.path else {
            return;
        };
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }
        let elapsed_ms = self.started_at.elapsed().as_millis();
        let line = format!("{}ms {}\n", elapsed_ms, stage.as_ref());
        let _ = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(path)
            .and_then(|mut file| std::io::Write::write_all(&mut file, line.as_bytes()));
    }
}

pub(crate) fn persist_analyze_run(
    state_dir: &str,
    report: &AnalyzeReport,
    source_command: &str,
    data_htf_path: Option<&str>,
    data_mtf_path: Option<&str>,
    data_ltf_path: Option<&str>,
    live_data_source: Option<LiveDataSourceProvenance>,
) -> Result<WorkflowSnapshot> {
    let previous_policy = load_pre_bayes_policy_history(state_dir, &report.symbol)?
        .last()
        .map(|record| record.policy.clone());
    let order_block_variant = Some(order_block_variant_runtime_evidence(
        &report.analysis.price_action.order_block_variant,
    ));
    let liquidity_pool_texture = Some(liquidity_pool_texture_runtime_evidence(
        &report.analysis.price_action.liquidity_pool_texture,
    ));
    let liquidity_sweep_quality = Some(liquidity_sweep_quality_runtime_evidence(
        &report.analysis.price_action.liquidity_sweep_quality,
    ));
    let volume_imbalance_gap = Some(volume_imbalance_gap_runtime_evidence(
        &report.analysis.price_action.volume_imbalance_gap,
    ));
    let conformal_metrics =
        analyze_conformal_metrics_from_factor_ranking(&report.supporting.factor_ranking);
    let analyze_run_record = AnalyzeRunRecord {
        run_id: format!(
            "{}:{}:{}",
            source_command,
            report.symbol,
            report.timestamp.format("%Y%m%dT%H%M%S%.3fZ")
        ),
        timestamp: report.timestamp,
        symbol: report.symbol.clone(),
        provenance: report.supporting.provenance.clone(),
        decision_thresholds: report.supporting.decision_thresholds.clone(),
        dataset_comparability: report.supporting.dataset_comparability.clone(),
        promotion_decision: report.supporting.promotion_decision.clone(),
        rollback_recommendation: report.supporting.rollback_recommendation.clone(),
        family_history_window: family_history_window(),
        source_command: source_command.to_string(),
        data_htf_path: data_htf_path.map(str::to_string),
        data_mtf_path: data_mtf_path.map(str::to_string),
        data_ltf_path: data_ltf_path.map(str::to_string),
        live_data_source,
        htf_bars: report.meta.bars.htf,
        mtf_bars: report.meta.bars.mtf,
        ltf_bars: report.meta.bars.ltf,
        selected_direction: report.supporting.decision.selected_direction,
        selected_entry_quality: report.supporting.entry_quality.selected_state.clone(),
        decision_hint: report.supporting.decision_hint.clone(),
        regime_probs: Some(report.supporting.model_state.regime_probs),
        market_state_evidence: report.supporting.market_state_evidence.clone(),
        conformal_coverage_1sigma: conformal_metrics.conformal_coverage_1sigma,
        conformal_miscoverage_1sigma: conformal_metrics.conformal_miscoverage_1sigma,
        mean_prediction_interval_half_width: conformal_metrics.mean_prediction_interval_half_width,
        worst_window_miscoverage: conformal_metrics.worst_window_miscoverage,
        canonical_structural_regime_posterior: Some(
            ict_engine::state::CanonicalStructuralRegimePosterior {
                active_regime: report
                    .supporting
                    .canonical_belief_report
                    .regime_posterior
                    .active_regime
                    .clone(),
                confidence: report
                    .supporting
                    .canonical_belief_report
                    .regime_posterior
                    .confidence,
                probabilities: report
                    .supporting
                    .canonical_belief_report
                    .regime_posterior
                    .probabilities
                    .clone(),
                evidence: report
                    .supporting
                    .canonical_belief_report
                    .regime_posterior
                    .evidence
                    .clone(),
            },
        ),
        order_block_variant,
        liquidity_pool_texture,
        liquidity_sweep_quality,
        volume_imbalance_gap,
        reference_liquidity_levels: Some(
            report
                .analysis
                .price_action
                .reference_liquidity_levels
                .clone(),
        ),
        hybrid_regime_label: report.analysis.regime_bayesian.hybrid_regime_label.clone(),
        hybrid_regime_age_bars: report
            .supporting
            .decision_hint
            .split('|')
            .find_map(|part| part.strip_prefix("hybrid_regime_age="))
            .and_then(|value| value.parse::<usize>().ok()),
        hybrid_duration_model: report
            .analysis
            .regime_bayesian
            .hybrid_duration_model
            .clone(),
        hybrid_remaining_expected_bars: report
            .analysis
            .regime_bayesian
            .hybrid_remaining_expected_bars,
        execution_artifact_id: report
            .supporting
            .execution_artifact
            .as_ref()
            .map(|artifact| artifact.artifact_id.clone()),
        execution_edge_share: report
            .supporting
            .execution_artifact
            .as_ref()
            .map(|artifact| artifact.features.execution_edge_share),
        prediction_edge_share: report
            .supporting
            .execution_artifact
            .as_ref()
            .map(|artifact| artifact.features.prediction_edge_share),
        execution_readiness: report
            .supporting
            .execution_artifact
            .as_ref()
            .map(|artifact| artifact.features.execution_readiness),
        execution_gate_status: report
            .supporting
            .execution_artifact
            .as_ref()
            .map(|artifact| artifact.hard_gate_status.clone()),
        entry_model_packets: report.supporting.entry_model_packets.clone(),
        pre_bayes_evidence_filter: report.supporting.pre_bayes_evidence_filter.clone(),
        pre_bayes_entry_quality_bridge: report.supporting.pre_bayes_entry_quality_bridge.clone(),
        factor_family_decisions: report.supporting.factor_family_decisions.clone(),
        factor_family_outcomes: report.supporting.factor_family_outcomes.clone(),
        factor_family_diffs: report.supporting.factor_family_diffs.clone(),
        factor_family_history: report.supporting.factor_family_history.clone(),
        decision_history_summary: report.supporting.decision_history_summary.clone(),
        workflow_state: report.supporting.workflow_state.clone(),
        agent_action_plan: report.supporting.agent_action_plan.clone(),
        recommended_commands: report.supporting.recommended_commands.clone(),
        recommended_next_command: report.supporting.recommended_next_command.clone(),
        recommended_next_command_meta: recommended_next_command_meta(
            &report.supporting.recommended_next_command,
        ),
        agent_context_bundle: report.supporting.agent_context_bundle.clone(),
        agent_context_bundle_minimal: report.supporting.agent_context_bundle_minimal.clone(),
        feedback_history_summary: report.supporting.feedback_history_summary.clone(),
        multi_timeframe_summary: report.supporting.multi_timeframe_summary.clone(),
        artifact_action_summary: report.supporting.artifact_action_summary.clone(),
        artifact_decision_summary: report.supporting.artifact_decision_summary.clone(),
        artifact_decision_section: report.supporting.artifact_decision_section.clone(),
        agent_prompts: report.supporting.agent_prompts.clone(),
        prompt_workflow: report.supporting.agent_prompts.workflow.clone(),
    };
    append_analyze_run(state_dir, &report.symbol, analyze_run_record.clone())?;
    let mut learning_state = load_learning_state(state_dir, &report.symbol).unwrap_or_default();
    let blocking_truth = report.supporting.workflow_snapshot.blocking_truth.clone();
    let hard_blocked = matches!(
        blocking_truth.status.as_str(),
        "blocked"
            | "bridge_needs_confirmation"
            | "validated_regressing"
            | "credibility_gate_blocked"
    );
    let analyze_ensemble_vote = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
        symbol: report.symbol.clone(),
        state_dir: Some(state_dir.to_string()),
        recommended_next_command: report.supporting.recommended_next_command.clone(),
        hard_blocked,
        hard_block_reason: if hard_blocked {
            Some(blocking_truth.reason.clone())
        } else {
            None
        },
        hard_block_command: if hard_blocked {
            Some(blocking_truth.next_command.clone())
        } else {
            None
        },
        provenance: report.supporting.provenance.clone(),
        dataset_comparability: report.supporting.dataset_comparability.clone(),
        pre_bayes_filter: Some(report.supporting.pre_bayes_evidence_filter.clone()),
        belief: report.supporting.canonical_belief_report.clone(),
        ict_structure: None,
    });
    let canonical_scorecards =
        load_ensemble_executor_scorecards(state_dir, &report.symbol).unwrap_or_default();
    let analyze_ensemble_record = build_ensemble_vote_record(
        &report.symbol,
        source_command,
        Some(analyze_run_record.run_id.clone()),
        &report.supporting.provenance,
        &report.supporting.dataset_comparability,
        &analyze_ensemble_vote,
        &canonical_scorecards,
    );
    let structural_snapshot = WorkflowSnapshot {
        symbol: report.symbol.clone(),
        current_focus_phase: "analyze".to_string(),
        current_focus_reason: report.supporting.workflow_state.reason.clone(),
        recommended_next_command: report.supporting.recommended_next_command.clone(),
        recommended_next_command_meta: recommended_next_command_meta(
            &report.supporting.recommended_next_command,
        ),
        blocking_truth: report.supporting.workflow_snapshot.blocking_truth.clone(),
        latest_analyze: Some(workflow_phase_snapshot_from_analyze_run(
            &analyze_run_record,
        )),
        latest_ensemble_vote: Some(analyze_ensemble_record.clone()),
        ..WorkflowSnapshot::default()
    };
    apply_offline_structural_prior_seed(
        &mut learning_state,
        &structural_snapshot,
        &format!("structural-prior-seed:{}", analyze_run_record.run_id),
        analyze_run_record.timestamp,
        structural_support_hint_for_analyze(
            analyze_ensemble_record
                .posterior_confidence
                .unwrap_or(analyze_ensemble_record.confidence),
            analyze_run_record.execution_readiness,
            analyze_run_record.dataset_comparability.comparable,
            analyze_run_record.feedback_history_summary.total_records,
        ),
        "analyze_run_structural_prior_seed",
    );
    save_learning_state(state_dir, &report.symbol, &learning_state)?;
    persist_ensemble_vote_record(state_dir, &analyze_ensemble_record, &canonical_scorecards)?;
    append_pre_bayes_policy_history(
        state_dir,
        &report.symbol,
        PreBayesPolicyRecord {
            timestamp: report.timestamp,
            run_id: format!(
                "{}:{}:{}",
                source_command,
                report.symbol,
                report.timestamp.format("%Y%m%dT%H%M%S%.3fZ")
            ),
            source_command: source_command.to_string(),
            policy: report.supporting.pre_bayes_evidence_filter.policy.clone(),
            diff_from_previous: pre_bayes_policy_diff(
                previous_policy.as_ref(),
                &report.supporting.pre_bayes_evidence_filter.policy,
            ),
        },
    )?;
    refresh_workflow_snapshot(state_dir, &report.symbol)
}

#[derive(Debug, Clone, Copy, Default)]
struct AnalyzeConformalMetrics {
    conformal_coverage_1sigma: Option<f64>,
    conformal_miscoverage_1sigma: Option<f64>,
    mean_prediction_interval_half_width: Option<f64>,
    worst_window_miscoverage: Option<f64>,
}

fn analyze_conformal_metrics_from_factor_ranking(
    factor_ranking: &[ict_engine::state::PersistedFactorRanking],
) -> AnalyzeConformalMetrics {
    let Some(ranking) = factor_ranking.iter().find(|ranking| {
        ranking.conformal_coverage_1sigma > 0.0
            || ranking.conformal_miscoverage_1sigma > 0.0
            || ranking.mean_prediction_interval_half_width > 0.0
            || ranking.worst_window_miscoverage > 0.0
    }) else {
        return AnalyzeConformalMetrics::default();
    };

    AnalyzeConformalMetrics {
        conformal_coverage_1sigma: Some(ranking.conformal_coverage_1sigma),
        conformal_miscoverage_1sigma: Some(ranking.conformal_miscoverage_1sigma),
        mean_prediction_interval_half_width: Some(ranking.mean_prediction_interval_half_width),
        worst_window_miscoverage: Some(ranking.worst_window_miscoverage),
    }
}

fn order_block_variant_runtime_evidence(
    evidence: &ict_engine::analyze_sections::OrderBlockVariantEvidence,
) -> ict_engine::state::OrderBlockVariantRuntimeEvidence {
    ict_engine::state::OrderBlockVariantRuntimeEvidence {
        factor_name: evidence.factor_name.clone(),
        variant: evidence.variant.clone(),
        direction: evidence.direction,
        high: evidence.high,
        low: evidence.low,
        midpoint: evidence.midpoint,
        validation_state: evidence.validation_state.clone(),
        mitigation_count: evidence.mitigation_count,
        mitigation_pct: evidence.mitigation_pct,
        failed_mitigation: evidence.failed_mitigation,
        partial_fill_state: evidence.partial_fill_state.clone(),
        breaker_confirmed: evidence.breaker_confirmed,
        rejection_confirmed: evidence.rejection_confirmed,
        confidence: evidence.confidence,
        fail_closed_reason: evidence.fail_closed_reason.clone(),
    }
}

fn liquidity_pool_texture_runtime_evidence(
    evidence: &ict_engine::analyze_sections::LiquidityPoolTextureEvidence,
) -> ict_engine::state::LiquidityPoolTextureRuntimeEvidence {
    ict_engine::state::LiquidityPoolTextureRuntimeEvidence {
        factor_name: evidence.factor_name.clone(),
        texture: evidence.texture.clone(),
        subtype: evidence.subtype.clone(),
        level: evidence.level,
        high: evidence.high,
        low: evidence.low,
        touch_count: evidence.touch_count,
        spacing_consistency: evidence.spacing_consistency,
        clean_sweep_likelihood: evidence.clean_sweep_likelihood,
        confidence: evidence.confidence,
        fail_closed_reason: evidence.fail_closed_reason.clone(),
    }
}

fn liquidity_sweep_quality_runtime_evidence(
    evidence: &ict_engine::analyze_sections::LiquiditySweepQualityEvidence,
) -> ict_engine::state::LiquiditySweepQualityRuntimeEvidence {
    ict_engine::state::LiquiditySweepQualityRuntimeEvidence {
        factor_name: evidence.factor_name.clone(),
        quality: evidence.quality.clone(),
        sweep_bar: evidence.sweep_bar,
        return_bar: evidence.return_bar,
        pool_price: evidence.pool_price,
        displacement_atr: evidence.displacement_atr,
        return_bars: evidence.return_bars,
        close_reclaim: evidence.close_reclaim,
        confidence: evidence.confidence,
        fail_closed_reason: evidence.fail_closed_reason.clone(),
    }
}

fn volume_imbalance_gap_runtime_evidence(
    evidence: &ict_engine::analyze_sections::VolumeImbalanceGapEvidence,
) -> ict_engine::state::VolumeImbalanceGapRuntimeEvidence {
    ict_engine::state::VolumeImbalanceGapRuntimeEvidence {
        factor_name: evidence.factor_name.clone(),
        direction: evidence.direction,
        top: evidence.top,
        bottom: evidence.bottom,
        midpoint: evidence.midpoint,
        start_bar: evidence.start_bar,
        filled: evidence.filled,
        active: evidence.active,
        mitigation_pct: evidence.mitigation_pct,
        failed_mitigation: evidence.failed_mitigation,
        partial_fill_state: evidence.partial_fill_state.clone(),
        confidence: evidence.confidence,
        fail_closed_reason: evidence.fail_closed_reason.clone(),
    }
}

pub(crate) fn persist_pending_update_artifact_from_analyze(
    state_dir: &str,
    report: &AnalyzeReport,
    source_phase: &str,
) -> Result<String> {
    let rules = artifact_review_rules().pending_update;
    let review_rule_version = pending_update_review_rule_version(&rules);
    let history = load_pending_update_history(state_dir, &report.symbol)?;
    let version = history.len() + 1;
    let top_factor_score = report
        .supporting
        .factor_ranking
        .first()
        .map(|item| item.composite_score)
        .unwrap_or(0.0);
    let avg_family_score = if report.supporting.factor_family_decisions.is_empty() {
        0.0
    } else {
        report
            .supporting
            .factor_family_decisions
            .iter()
            .map(|family| family.avg_score)
            .sum::<f64>()
            / report.supporting.factor_family_decisions.len() as f64
    };
    let template_feedback = FeedbackRecord {
        prompt_version: Some(report.supporting.provenance.prompt_version.clone()),
        factor_version: Some(report.supporting.provenance.factor_version.clone()),
        data_fingerprint: Some(report.supporting.provenance.data_fingerprint.clone()),
        ..build_feedback_record(BuildFeedbackRecordInput {
            symbol: &report.symbol,
            source: source_phase,
            timestamp: report.timestamp,
            factor_diagnostics: &report.supporting.factor_diagnostics,
            decision: &report.supporting.decision,
            pnl: 0.0,
            realized_outcome: "pending".to_string(),
            regime_at_entry: report.supporting.model_state.regime_probs.dominant(),
        })
    };
    let mut artifact = PendingUpdateArtifact {
        artifact_id: format!(
            "pending-update:{}:{}:v{}",
            report.symbol, source_phase, version
        ),
        version,
        generated_at: report.timestamp,
        symbol: report.symbol.clone(),
        source_phase: source_phase.to_string(),
        source_run_id: Some(format!(
            "{}:{}:{}",
            source_phase,
            report.symbol,
            report.timestamp.format("%Y%m%dT%H%M%S%.3fZ")
        )),
        source_command: source_phase.to_string(),
        provenance: report.supporting.provenance.clone(),
        decision_hint: report.supporting.decision_hint.clone(),
        entry_quality: report.supporting.entry_quality.selected_state.clone(),
        factor_alignment: report.supporting.factor_diagnostics.alignment_label.clone(),
        factor_uncertainty: report
            .supporting
            .factor_diagnostics
            .uncertainty_label
            .clone(),
        selected_win_probability: report.supporting.decision.selected_win_probability,
        top_factor_score,
        avg_family_score,
        top_factor_name: report
            .supporting
            .factor_ranking
            .first()
            .map(|item| item.factor_name.clone()),
        top_factor_action: report
            .supporting
            .factor_ranking
            .first()
            .map(|item| item.iteration_action.clone()),
        family_scores: report
            .supporting
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        review_rule_version,
        review_rule_snapshot: rules,
        pre_bayes_evidence_filter: Some(report.supporting.pre_bayes_evidence_filter.clone()),
        pre_bayes_entry_quality_bridge: Some(
            report.supporting.pre_bayes_entry_quality_bridge.clone(),
        ),
        multi_timeframe_summary: report.supporting.multi_timeframe_summary.clone(),
        template_feedback,
        diff_from_previous: PendingUpdateArtifactDiff::default(),
        review_decision: PendingUpdateArtifactDecision::default(),
    };
    if let Some(previous) = history.last() {
        artifact.diff_from_previous = pending_update_artifact_diff(previous, &artifact);
        artifact.review_decision = pending_update_artifact_decision(previous, &artifact);
    } else {
        artifact.review_decision = PendingUpdateArtifactDecision {
            status: "promote_latest".to_string(),
            reason: "first_pending_update_artifact".to_string(),
            supersedes_artifact_id: None,
        };
    }
    append_artifact_ledger_entry(
        state_dir,
        &report.symbol,
        artifact_ledger_entry_from_pending_update(state_dir, &report.symbol, &artifact),
    )?;
    save_pending_update_artifact(state_dir, &report.symbol, &artifact)?;
    append_pending_update_artifact_history(state_dir, &report.symbol, artifact)?;
    Ok(std::path::Path::new(state_dir)
        .join(&report.symbol)
        .join(PENDING_UPDATE_ARTIFACT_FILE)
        .to_string_lossy()
        .to_string())
}

fn pending_update_artifact_decision(
    previous: &PendingUpdateArtifact,
    current: &PendingUpdateArtifact,
) -> PendingUpdateArtifactDecision {
    let rules = artifact_review_rules().pending_update;

    if current.diff_from_previous.exact_duplicate {
        PendingUpdateArtifactDecision {
            status: "discard".to_string(),
            reason: "duplicate_pending_update_context".to_string(),
            supersedes_artifact_id: None,
        }
    } else if (rules.require_same_data && !current.diff_from_previous.comparable_same_data)
        || (rules.require_same_factor_version
            && !current.diff_from_previous.comparable_same_factor_version)
        || (rules.require_same_prompt_version
            && !current.diff_from_previous.comparable_same_prompt_version)
    {
        PendingUpdateArtifactDecision {
            status: "observe".to_string(),
            reason: "artifact_not_comparable_same_data_factor_prompt_required".to_string(),
            supersedes_artifact_id: None,
        }
    } else if current.diff_from_previous.selected_probability_delta
        <= -rules.min_probability_improvement
        || current.diff_from_previous.top_factor_score_delta
            <= -rules.min_top_factor_score_improvement
        || current.diff_from_previous.avg_family_score_delta
            <= -rules.min_avg_family_score_improvement
    {
        PendingUpdateArtifactDecision {
            status: "discard".to_string(),
            reason: "strict_probability_or_score_regression".to_string(),
            supersedes_artifact_id: None,
        }
    } else if current.diff_from_previous.selected_probability_delta
        >= rules.min_probability_improvement
        && (current.diff_from_previous.top_factor_score_delta
            >= rules.min_top_factor_score_improvement
            || current.diff_from_previous.avg_family_score_delta
                >= rules.min_avg_family_score_improvement)
    {
        PendingUpdateArtifactDecision {
            status: "promote_latest".to_string(),
            reason: "strict_probability_and_score_improvement".to_string(),
            supersedes_artifact_id: Some(previous.artifact_id.clone()),
        }
    } else {
        PendingUpdateArtifactDecision {
            status: "observe".to_string(),
            reason: "within_probability_score_threshold_band".to_string(),
            supersedes_artifact_id: None,
        }
    }
}

fn artifact_ledger_entry_from_pending_update(
    state_dir: &str,
    symbol: &str,
    artifact: &PendingUpdateArtifact,
) -> ArtifactLedgerEntry {
    ArtifactLedgerEntry {
        entry_id: format!("ledger:{}", artifact.artifact_id),
        artifact_kind: "pending_update".to_string(),
        artifact_id: artifact.artifact_id.clone(),
        version: artifact.version,
        generated_at: artifact.generated_at,
        symbol: artifact.symbol.clone(),
        source_phase: artifact.source_phase.clone(),
        source_run_id: artifact.source_run_id.clone(),
        path: std::path::Path::new(state_dir)
            .join(symbol)
            .join(PENDING_UPDATE_ARTIFACT_FILE)
            .to_string_lossy()
            .to_string(),
        status: artifact.review_decision.status.clone(),
        promote_candidate: artifact.review_decision.status == "promote_latest",
        actionable: artifact.review_decision.status != "discard",
        decision_hint: artifact.decision_hint.clone(),
        review_reason: artifact.review_decision.reason.clone(),
        review_rule_version: artifact.review_rule_version.clone(),
        top_factor_name: artifact.top_factor_name.clone(),
        top_factor_action: artifact.top_factor_action.clone(),
        family_scores: artifact.family_scores.clone(),
        supersedes_artifact_id: artifact.review_decision.supersedes_artifact_id.clone(),
        quality_score: pending_update_quality_score(artifact),
        consumed_by_update_run_id: None,
        consumed_at: None,
        consumed_outcome: None,
        regraded_at: None,
        consumption_regrade_status: None,
        consumption_regrade_reason: None,
    }
}

fn execution_candidate_artifact_decision(
    previous: &ExecutionCandidateArtifact,
    current: &ExecutionCandidateArtifact,
) -> ExecutionCandidateArtifactDecision {
    let rules = artifact_review_rules().execution_candidate;

    if current.diff_from_previous.exact_duplicate {
        ExecutionCandidateArtifactDecision {
            status: "discard".to_string(),
            reason: "duplicate_execution_candidate_context".to_string(),
            supersedes_artifact_id: None,
        }
    } else if !current.actionable {
        ExecutionCandidateArtifactDecision {
            status: "observe".to_string(),
            reason: "candidate_not_actionable".to_string(),
            supersedes_artifact_id: None,
        }
    } else if (rules.require_same_data
        && previous.provenance.data_fingerprint != current.provenance.data_fingerprint)
        || (rules.require_same_factor_version
            && previous.provenance.factor_version != current.provenance.factor_version)
    {
        ExecutionCandidateArtifactDecision {
            status: "observe".to_string(),
            reason: "candidate_not_comparable_same_data_factor_required".to_string(),
            supersedes_artifact_id: None,
        }
    } else if current.diff_from_previous.posterior_delta <= -rules.min_posterior_improvement
        || current.diff_from_previous.win_probability_delta
            <= -rules.min_win_probability_improvement
    {
        ExecutionCandidateArtifactDecision {
            status: "discard".to_string(),
            reason: "candidate_probability_regression".to_string(),
            supersedes_artifact_id: None,
        }
    } else if current.diff_from_previous.posterior_delta >= rules.min_posterior_improvement
        && current.diff_from_previous.win_probability_delta >= rules.min_win_probability_improvement
    {
        ExecutionCandidateArtifactDecision {
            status: "promote_latest".to_string(),
            reason: "candidate_probability_improvement".to_string(),
            supersedes_artifact_id: Some(previous.artifact_id.clone()),
        }
    } else {
        ExecutionCandidateArtifactDecision {
            status: "observe".to_string(),
            reason: "candidate_within_probability_threshold_band".to_string(),
            supersedes_artifact_id: None,
        }
    }
}

fn report_same_root_branch_paths(report: &AnalyzeReport) -> Vec<String> {
    let assignments = &report
        .supporting
        .pre_bayes_evidence_filter
        .evidence_assignments;
    let mut paths = Vec::new();
    if let Some(path) = assignments
        .get("regime_profit_branch_path")
        .map(|value| value.trim())
        .filter(|value| !value.is_empty())
    {
        paths.push(path.to_string());
    }
    if let Some(raw_paths) = assignments.get("regime_bundle_branch_paths_json") {
        if let Ok(parsed) = serde_json::from_str::<Vec<String>>(raw_paths) {
            paths.extend(
                parsed
                    .into_iter()
                    .map(|value| value.trim().to_string())
                    .filter(|value| !value.is_empty()),
            );
        }
    }
    paths.sort();
    paths.dedup();
    paths
}

fn trace_output_number(output: &serde_json::Value, key: &str) -> Option<f64> {
    output.get(key).and_then(|value| {
        value.as_f64().or_else(|| {
            value
                .as_str()
                .and_then(|text| text.trim().parse::<f64>().ok())
        })
    })
}

fn same_root_execution_tree_admission_status_for_analyze(
    state_dir: &str,
    report: &AnalyzeReport,
    trade_direction: Direction,
) -> Option<String> {
    if matches!(trade_direction, Direction::Neutral) {
        return None;
    }
    let branch_paths = report_same_root_branch_paths(report);
    if branch_paths.is_empty() {
        return None;
    }
    let trace_path = std::path::Path::new(state_dir)
        .join(&report.symbol)
        .join(ict_engine::application::orchestration::EXECUTION_TREE_TRACE_FILE);
    let trace = std::fs::read(trace_path).ok()?;
    let trace: serde_json::Value = serde_json::from_slice(&trace).ok()?;
    let output = trace.get("output")?;
    let admission = trace.get("closed_loop_branch_admission")?;
    let path_id = admission
        .get("path_id")
        .and_then(serde_json::Value::as_str)?;
    if !branch_paths.iter().any(|path| path == path_id) {
        return None;
    }
    let pre_bayes_ready = matches!(
        admission
            .get("pre_bayes_gate_status")
            .and_then(serde_json::Value::as_str)
            .unwrap_or_default(),
        "pass_hard" | "pass_neutralized"
    );
    let admitted = admission.get("status").and_then(serde_json::Value::as_str) == Some("admitted")
        && admission
            .get("ready")
            .and_then(serde_json::Value::as_bool)
            .unwrap_or(false)
        && admission
            .get("actionable")
            .and_then(serde_json::Value::as_bool)
            .unwrap_or(false);
    let execution_tree_ready = output
        .get("gate_status")
        .and_then(serde_json::Value::as_str)
        == Some("ready")
        && output.get("branch").and_then(serde_json::Value::as_str) == Some("fill_viable");
    let ranker_used = output
        .get("path_ranker_score_used_by_execution_tree")
        .and_then(serde_json::Value::as_bool)
        .unwrap_or(false)
        && output
            .get("ranker_validation_ready")
            .and_then(serde_json::Value::as_bool)
            .unwrap_or(false);
    let execution_readiness = trace_output_number(output, "execution_readiness")?;
    let transition_hazard = trace_output_number(output, "hybrid_transition_hazard")?;
    let pda_hybrid_alignment = output
        .get("pda_hybrid_alignment")
        .and_then(serde_json::Value::as_bool)
        .unwrap_or(false);
    if !(pre_bayes_ready
        && admitted
        && execution_tree_ready
        && ranker_used
        && execution_readiness >= 0.65
        && transition_hazard < 0.60
        && pda_hybrid_alignment)
    {
        return None;
    }
    admission
        .get("candidate_status")
        .and_then(serde_json::Value::as_str)
        .or_else(|| {
            admission
                .get("execution_gate_status")
                .and_then(serde_json::Value::as_str)
        })
        .map(|status| status.to_string())
        .or_else(|| Some("execution_ready".to_string()))
}

pub(crate) fn persist_execution_candidate_from_analyze(
    state_dir: &str,
    report: &AnalyzeReport,
    source_phase: &str,
) -> Result<String> {
    let rules = artifact_review_rules().execution_candidate;
    let review_rule_version = execution_candidate_review_rule_version(&rules);
    let history = load_execution_candidate_history(state_dir, &report.symbol)?;
    let version = history.len() + 1;
    let trade_plan = &report.supporting.raw_trade_plan;
    let branch_direction = execution_candidate_branch_trade_direction(report);
    let selected_direction =
        branch_direction.unwrap_or(report.supporting.decision.selected_direction);
    let trade_direction = branch_direction.unwrap_or(trade_plan.direction);
    let same_root_execution_tree_admission =
        same_root_execution_tree_admission_status_for_analyze(state_dir, report, trade_direction);
    let materialized_from_same_root_execution_tree = same_root_execution_tree_admission.is_some();
    let actionability_from_trade_plan =
        trade_direction != Direction::Neutral && trade_plan.position_size > 0.0;
    let actionable = actionability_from_trade_plan || materialized_from_same_root_execution_tree;
    let candidate_status = same_root_execution_tree_admission.unwrap_or_else(|| {
        if actionability_from_trade_plan {
            "ready".to_string()
        } else {
            "no_trade".to_string()
        }
    });
    let artifact = ExecutionCandidateArtifact {
        artifact_id: format!(
            "execution-candidate:{}:{}:v{}",
            report.symbol, source_phase, version
        ),
        version,
        generated_at: report.timestamp,
        symbol: report.symbol.clone(),
        source_phase: source_phase.to_string(),
        source_run_id: Some(format!(
            "{}:{}:{}",
            source_phase,
            report.symbol,
            report.timestamp.format("%Y%m%dT%H%M%S%.3fZ")
        )),
        provenance: report.supporting.provenance.clone(),
        decision_hint: report.supporting.decision_hint.clone(),
        selected_direction,
        trade_direction,
        actionable,
        entry: trade_plan.entry,
        stop_loss: trade_plan.stop_loss,
        take_profits: vec![trade_plan.tp1, trade_plan.tp2, trade_plan.tp3],
        posterior: trade_plan.posterior,
        win_probability: trade_plan.win_probability,
        factor_alignment: report.supporting.factor_diagnostics.alignment_label.clone(),
        factor_uncertainty: report
            .supporting
            .factor_diagnostics
            .uncertainty_label
            .clone(),
        candidate_status,
        top_factor_name: report
            .supporting
            .factor_ranking
            .first()
            .map(|item| item.factor_name.clone()),
        top_factor_action: report
            .supporting
            .factor_ranking
            .first()
            .map(|item| item.iteration_action.clone()),
        family_scores: report
            .supporting
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        review_rule_version,
        review_rule_snapshot: rules,
        pre_bayes_evidence_filter: Some(report.supporting.pre_bayes_evidence_filter.clone()),
        pre_bayes_entry_quality_bridge: Some(
            report.supporting.pre_bayes_entry_quality_bridge.clone(),
        ),
        multi_timeframe_summary: report.supporting.multi_timeframe_summary.clone(),
        executor_scorecards: Vec::new(),
        diff_from_previous: ExecutionCandidateArtifactDiff::default(),
        review_decision: ExecutionCandidateArtifactDecision::default(),
    };
    let mut artifact = artifact;
    if let Some(previous) = history.last() {
        artifact.diff_from_previous = execution_candidate_artifact_diff(previous, &artifact);
        let newly_materialized_same_root_execution_tree = materialized_from_same_root_execution_tree
            && !(previous.actionable && previous.candidate_status == "execution_ready");
        artifact.review_decision = if newly_materialized_same_root_execution_tree {
            ExecutionCandidateArtifactDecision {
                status: "promote_latest".to_string(),
                reason: "same_root_execution_tree_admitted".to_string(),
                supersedes_artifact_id: Some(previous.artifact_id.clone()),
            }
        } else {
            execution_candidate_artifact_decision(previous, &artifact)
        };
    } else {
        artifact.review_decision = ExecutionCandidateArtifactDecision {
            status: if artifact.actionable {
                "promote_latest".to_string()
            } else {
                "observe".to_string()
            },
            reason: if materialized_from_same_root_execution_tree {
                "same_root_execution_tree_admitted".to_string()
            } else {
                "first_execution_candidate_artifact".to_string()
            },
            supersedes_artifact_id: None,
        };
    }
    append_artifact_ledger_entry(
        state_dir,
        &report.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", artifact.artifact_id),
            artifact_kind: "execution_candidate".to_string(),
            artifact_id: artifact.artifact_id.clone(),
            version: artifact.version,
            generated_at: artifact.generated_at,
            symbol: artifact.symbol.clone(),
            source_phase: artifact.source_phase.clone(),
            source_run_id: artifact.source_run_id.clone(),
            path: std::path::Path::new(state_dir)
                .join(&report.symbol)
                .join(EXECUTION_CANDIDATE_FILE)
                .to_string_lossy()
                .to_string(),
            status: artifact.review_decision.status.clone(),
            promote_candidate: artifact.review_decision.status == "promote_latest",
            actionable: artifact.actionable && artifact.review_decision.status != "discard",
            decision_hint: artifact.decision_hint.clone(),
            review_reason: artifact.review_decision.reason.clone(),
            review_rule_version: artifact.review_rule_version.clone(),
            top_factor_name: artifact.top_factor_name.clone(),
            top_factor_action: artifact.top_factor_action.clone(),
            family_scores: artifact.family_scores.clone(),
            supersedes_artifact_id: artifact.review_decision.supersedes_artifact_id.clone(),
            quality_score: ((artifact.posterior + artifact.win_probability) * 100.0) as i32,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    save_execution_candidate_artifact(state_dir, &report.symbol, &artifact)?;
    append_execution_candidate_history(state_dir, &report.symbol, artifact)?;
    Ok(std::path::Path::new(state_dir)
        .join(&report.symbol)
        .join(EXECUTION_CANDIDATE_FILE)
        .to_string_lossy()
        .to_string())
}

fn execution_candidate_branch_trade_direction(report: &AnalyzeReport) -> Option<Direction> {
    let assignments = &report
        .supporting
        .pre_bayes_evidence_filter
        .evidence_assignments;
    let has_rooted_branch = assignments
        .get("regime_profit_branch_path")
        .is_some_and(|value| !value.trim().is_empty())
        || assignments
            .get("regime_bundle_branch_paths_json")
            .is_some_and(|value| !value.trim().is_empty())
        || assignments
            .get("profit_factor")
            .is_some_and(|value| !value.trim().is_empty());
    if !has_rooted_branch {
        return None;
    }
    assignments
        .get("trade_direction")
        .and_then(|value| parse_execution_candidate_direction(value))
}

fn parse_execution_candidate_direction(value: &str) -> Option<Direction> {
    match value.trim().to_ascii_lowercase().as_str() {
        "bear" | "short" | "sell" | "sold" => Some(Direction::Bear),
        "bull" | "long" | "buy" | "bought" => Some(Direction::Bull),
        "neutral" | "none" | "flat" | "no_trade" => Some(Direction::Neutral),
        _ => None,
    }
}

pub(crate) fn apply_command_context_to_analyze_report(
    report: &mut AnalyzeReport,
    command_context: &CommandContext,
) {
    let pda_sequence_summary = ict_engine::pda_sequence::load_pda_sequence_analysis(
        &command_context.state_dir,
        &command_context.symbol,
    )
    .ok()
    .map(|artifact| ict_engine::pda_sequence::summarize_pda_sequence_artifact(&artifact));
    report.supporting.recommended_commands = command_recommendations(command_context);
    concretize_action_plan_commands(
        &mut report.supporting.agent_action_plan,
        &report.supporting.recommended_commands,
    );
    report.supporting.recommended_next_command = recommended_next_command(
        &report.supporting.agent_action_plan,
        &report.supporting.recommended_commands,
    );
    report.supporting.agent_context_bundle =
        build_agent_context_bundle(BuildAgentContextBundleInput {
            symbol: &command_context.symbol,
            state_dir: &command_context.state_dir,
            workflow_state: &report.supporting.workflow_state,
            decision_hint: &report.supporting.decision_hint,
            recommended_next_command: &report.supporting.recommended_next_command,
            recommended_commands: &report.supporting.recommended_commands,
            dataset_comparability: &report.supporting.dataset_comparability,
            factor_iteration_queue: &report.supporting.factor_iteration_queue,
            family_outcomes: &report.supporting.factor_family_outcomes,
            pre_bayes_evidence_filter: Some(&report.supporting.pre_bayes_evidence_filter),
            pre_bayes_entry_quality_bridge: Some(&report.supporting.pre_bayes_entry_quality_bridge),
            pda_sequence_summary: pda_sequence_summary.as_ref(),
            factor_mutation_evaluation: None,
            artifact_decision_summary: Some(&report.supporting.artifact_decision_summary),
        });
    report
        .supporting
        .agent_context_bundle
        .multi_timeframe_summary = report.supporting.multi_timeframe_summary.clone();
    report.supporting.agent_context_bundle_minimal =
        build_agent_context_bundle_minimal(&report.supporting.agent_context_bundle);
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::Utc;
    use std::collections::BTreeMap;

    fn sample_analyze_report_with_factor_ranking(
        factor_ranking: Vec<ict_engine::state::PersistedFactorRanking>,
    ) -> AnalyzeReport {
        AnalyzeReport {
            symbol: "NQ".to_string(),
            timestamp: Utc::now(),
            analysis: AnalyzeSections {
                price_action: PriceActionSection {
                    probability_role: "test".to_string(),
                    structure_bias: Direction::Neutral,
                    latest_break: None,
                    latest_break_level: None,
                    latest_swing_high: None,
                    latest_swing_low: None,
                    recent_break_count: 0,
                    swing_highs: 0,
                    swing_lows: 0,
                    bull_expansion: false,
                    bear_expansion: false,
                    expansion_strength: 0.0,
                    liquidity_sweeps_recent: 0,
                    nearest_liquidity_pool_level: None,
                    liquidity_pool_texture:
                        ict_engine::analyze_sections::LiquidityPoolTextureEvidence::fail_closed(
                            "missing_liquidity_pool_texture",
                        ),
                    latest_liquidity_sweep_level: None,
                    liquidity_sweep_quality:
                        ict_engine::analyze_sections::LiquiditySweepQualityEvidence::fail_closed(
                            "missing_liquidity_sweep_quality",
                        ),
                    reference_liquidity_levels: ict_engine::ict::ReferenceLiquidityLevelsEvidence::default(),
                    volume_imbalance_gap:
                        ict_engine::analyze_sections::VolumeImbalanceGapEvidence::fail_closed(
                            "missing_volume_imbalance_gap",
                        ),
                    open_fvgs: 0,
                    nearest_open_fvg_top: None,
                    nearest_open_fvg_bottom: None,
                    fvg_mitigation_pct: None,
                    fvg_failed_mitigation: false,
                    fvg_partial_fill_state: "none".to_string(),
                    untested_order_blocks: 0,
                    nearest_untested_order_block_high: None,
                    nearest_untested_order_block_low: None,
                    order_block_variant:
                        ict_engine::analyze_sections::OrderBlockVariantEvidence::fail_closed(
                            "missing_order_block_variant",
                        ),
                    bullish_cisd: false,
                    bearish_cisd: false,
                    rejection_block_present: false,
                    narrative: "test".to_string(),
                },
                technical_price: ict_engine::analyze_sections::TechnicalPriceSection {
                    probability_role: "test".to_string(),
                    last_closed_bar_close: 0.0,
                    live_market_price: None,
                    live_spot_price: None,
                    ema20: None,
                    ema50: None,
                    rsi14: None,
                    adx14: None,
                    atr14: None,
                    macd_line: None,
                    macd_signal: None,
                    macd_histogram: None,
                    bollinger_upper: None,
                    bollinger_middle: None,
                    bollinger_lower: None,
                    bollinger_squeeze: false,
                    momentum_5_bar: None,
                    options_hedging:
                        ict_engine::analyze::options_hedging_section::build_options_hedging_section(
                            None,
                        ),
                    narrative: "test".to_string(),
                },
                smt_correlation:
                    ict_engine::analyze::smt_correlation_section::empty_smt_correlation_section(),
                regime_bayesian: RegimeBayesianSection {
                    hmm_state: "test".to_string(),
                    regime_probs: RegimeProbs {
                        accumulation: 0.6,
                        manipulation_expansion: 0.3,
                        distribution: 0.1,
                    },
                    regime_label: "trend".to_string(),
                    liquidity_label: "balanced".to_string(),
                    hybrid_regime_label: None,
                    hybrid_transition_hazard: None,
                    hybrid_duration_model: None,
                    hybrid_remaining_expected_bars: None,
                    pda_cluster_family: None,
                    pda_hybrid_alignment: None,
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    selected_direction: Direction::Bull,
                    evidence_policy: "test".to_string(),
                    ict_role: "test".to_string(),
                },
                multi_timeframe:
                    ict_engine::analyze::multi_timeframe_section::build_analyze_multi_timeframe_section(
                        &[],
                        Some(&ict_engine::state::PreBayesEvidenceFilter::default()),
                    ),
                trade_plan: TradePlanSection {
                    probability_role: "test".to_string(),
                    actionable: false,
                    direction: Direction::Neutral,
                    entry: 0.0,
                    stop_loss: 0.0,
                    take_profits: Vec::new(),
                    risk_reward: 0.0,
                    posterior: 0.0,
                    win_probability: 0.0,
                    kelly_fraction: 0.0,
                    position_size: 0.0,
                    uncertainties: Vec::new(),
                    narrative: "test".to_string(),
                },
            },
            meta: AnalyzeMeta {
                state_dir: String::new(),
                bars: AnalyzeBars {
                    htf: 1,
                    mtf: 1,
                    ltf: 1,
                    observations: 1,
                },
                data_source: None,
            },
            supporting: AnalyzeSupporting {
                model_state: AnalyzeModelState {
                    hmm_state: "test".to_string(),
                    log_likelihood: 0.0,
                    viterbi_log_likelihood: 0.0,
                    regime_probs: RegimeProbs {
                        accumulation: 0.6,
                        manipulation_expansion: 0.3,
                        distribution: 0.1,
                    },
                    evidence_policy: "test".to_string(),
                    canonical_belief_engine: "test".to_string(),
                    canonical_shadow_status: "test".to_string(),
                },
                provenance: ict_engine::state::RunProvenance::default(),
                promotion_decision: ict_engine::state::PromotionDecision::default(),
                rollback_recommendation: ict_engine::state::RollbackRecommendation::default(),
                labels: AnalyzeLabels {
                    regime_label: "trend".to_string(),
                    liquidity_label: "balanced".to_string(),
                },
                ict: AnalyzeIctSummary {
                    total_sweeps: 0,
                    total_fvgs: 0,
                    mtf_open_fvgs: 0,
                    mtf_untested_obs: 0,
                    ict_role: "test".to_string(),
                },
                entry_quality: AnalyzeEntryQualitySummary {
                    base: BTreeMap::new(),
                    long: BTreeMap::new(),
                    short: BTreeMap::new(),
                    selected_state: "neutral".to_string(),
                },
                auxiliary: None,
                decision: ict_engine::planner::ProbabilisticDecisionSnapshot {
                    long_score: 0.6,
                    short_score: 0.4,
                    win_prob_long: 0.6,
                    win_prob_short: 0.4,
                    ict_support_long: 0.5,
                    ict_support_short: 0.5,
                    selected_direction: Direction::Bull,
                    selected_score: 0.6,
                    selected_win_probability: 0.6,
                    ict_role: "test".to_string(),
                },
                entry_model_packets: ict_engine::application::entry_models::EntryModelPacketStore::default(),
                trade_outcome: AnalyzeTradeOutcomeSummary {
                    base: BTreeMap::new(),
                    long: BTreeMap::new(),
                    short: BTreeMap::new(),
                },
                factor_diagnostics: ict_engine::factor_lab::FactorDiagnostics::default(),
                pre_bayes_evidence_filter: ict_engine::state::PreBayesEvidenceFilter {
                    gating_status: "pass_hard".to_string(),
                    policy: ict_engine::state::PreBayesEvidencePolicy {
                        version: "test-policy".to_string(),
                        ..ict_engine::state::PreBayesEvidencePolicy::default()
                    },
                    ..ict_engine::state::PreBayesEvidenceFilter::default()
                },
                market_state_evidence: vec!["test_market_state".to_string()],
                pre_bayes_entry_quality_bridge: ict_engine::state::PreBayesEntryQualityBridge::default(),
                objective_jump_weight: None,
                canonical_belief_report: ict_engine::reporting::belief::BeliefReportPacket::default(),
                decision_thresholds: ict_engine::state::DecisionThresholds::default(),
                factor_ranking,
                factor_iteration_queue: Vec::new(),
                factor_family_decisions: Vec::new(),
                factor_family_outcomes: Vec::new(),
                factor_family_diffs: Vec::new(),
                factor_family_history: Vec::new(),
                decision_history_summary: ict_engine::state::DecisionHistorySummary::default(),
                agent_action_plan: ict_engine::state::AgentActionPlan::default(),
                workflow_state: ict_engine::state::WorkflowState {
                    phase: "observe".to_string(),
                    reason: "test".to_string(),
                },
                agent_context_bundle: ict_engine::state::AgentContextBundle::default(),
                agent_context_bundle_minimal: ict_engine::state::AgentContextBundleMinimal::default(),
                recommended_commands: ict_engine::state::CommandRecommendations::default(),
                recommended_next_command: "analyze".to_string(),
                dataset_comparability: ict_engine::state::DatasetComparability::default(),
                decision_hint: "test".to_string(),
                artifact_action_summary: Vec::new(),
                artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary::default(),
                artifact_decision_section: ict_engine::state::ArtifactDecisionSection::default(),
                agent_prompts: ict_engine::agent::AgentPromptPack::default(),
                feedback_history_summary: ict_engine::state::FeedbackHistorySummary::default(),
                multi_timeframe_summary: Vec::new(),
                raw_trade_plan: TradePlan {
                    symbol: Symbol::NQ,
                    direction: Direction::Neutral,
                    entry: 0.0,
                    stop_loss: 0.0,
                    tp1: 0.0,
                    tp2: 0.0,
                    tp3: 0.0,
                    risk_reward: 0.0,
                    kelly_fraction: 0.0,
                    position_size: 0.0,
                    regime: Regime::Accumulation,
                    posterior: 0.0,
                    win_probability: 0.0,
                    cascade_bull: ict_engine::types::CascadeResult::default(),
                    cascade_bear: ict_engine::types::CascadeResult::default(),
                    uncertainties: Vec::new(),
                },
                workflow_snapshot: ict_engine::state::WorkflowSnapshot::default(),
                staged_orchestration_trace: None,
                execution_artifact: None,
                execution_triage: None,
            },
        }
    }

    #[test]
    fn execution_candidate_uses_branch_trade_direction_over_report_fallback() {
        let temp = tempfile::tempdir().unwrap();
        let mut report = sample_analyze_report_with_factor_ranking(Vec::new());
        report.symbol = "M2K".to_string();
        report.supporting.decision.selected_direction = Direction::Bull;
        report.supporting.raw_trade_plan.direction = Direction::Bull;
        report.supporting.raw_trade_plan.position_size = 0.0;
        report
            .supporting
            .pre_bayes_evidence_filter
            .evidence_assignments
            .insert(
                "regime_profit_branch_path".to_string(),
                "FUTURES -> equity_index -> M2K -> 1m -> RangeReversion -> LiquiditySweepRejectShort -> ibkr_m2k1m_liquidity_sweep_reject_short_7d_gate1_v1 -> ibkr_m2k1m_liquidity_sweep_reject_short_rvol_pda_guard_7d_gate1_v1".to_string(),
            );
        report
            .supporting
            .pre_bayes_evidence_filter
            .evidence_assignments
            .insert("trade_direction".to_string(), "Bear".to_string());

        persist_execution_candidate_from_analyze(temp.path().to_str().unwrap(), &report, "analyze")
            .unwrap();

        let candidate: ict_engine::state::ExecutionCandidateArtifact =
            ict_engine::state::load_state(
                temp.path(),
                "M2K",
                ict_engine::state::EXECUTION_CANDIDATE_FILE,
            )
            .unwrap();

        assert_eq!(candidate.selected_direction, Direction::Bear);
        assert_eq!(candidate.trade_direction, Direction::Bear);
        assert!(!candidate.actionable);
        assert_eq!(candidate.candidate_status, "no_trade");
    }

    #[test]
    fn execution_candidate_materializes_same_root_execution_tree_admission_when_trade_plan_size_is_zero(
    ) {
        let temp = tempfile::tempdir().unwrap();
        let mut report = sample_analyze_report_with_factor_ranking(Vec::new());
        report.symbol = "CRWD".to_string();
        report.supporting.raw_trade_plan.direction = Direction::Bull;
        report.supporting.raw_trade_plan.position_size = 0.0;
        report.supporting.raw_trade_plan.entry = 596.0;
        report.supporting.raw_trade_plan.stop_loss = 591.8;
        report.supporting.raw_trade_plan.tp1 = 598.8;
        report.supporting.raw_trade_plan.tp2 = 601.6;
        report.supporting.raw_trade_plan.tp3 = 604.4;
        report.supporting.raw_trade_plan.posterior = 0.2159;
        report.supporting.raw_trade_plan.win_probability = 0.5037;
        report.supporting.pre_bayes_evidence_filter.gating_status = "pass_neutralized".to_string();
        let branch_path = "RangeReversion -> AiSecuritySoftwareOversoldReclaim -> rsi_vwap_reclaim_dense -> yf_ai_security_software_rsi_vwap_reclaim_crwd_5m_v1 -> session_liquidity_transition_stability_v1 -> pda_mtf_soft_confirmation_v1";
        report
            .supporting
            .pre_bayes_evidence_filter
            .evidence_assignments
            .insert(
                "regime_profit_branch_path".to_string(),
                branch_path.to_string(),
            );
        report
            .supporting
            .pre_bayes_evidence_filter
            .evidence_assignments
            .insert("trade_direction".to_string(), "Bull".to_string());

        let symbol_dir = temp.path().join("CRWD");
        std::fs::create_dir_all(&symbol_dir).unwrap();
        std::fs::write(
            symbol_dir.join(ict_engine::application::orchestration::EXECUTION_TREE_TRACE_FILE),
            serde_json::to_vec_pretty(&serde_json::json!({
                "output": {
                    "execution_readiness": 0.67,
                    "gate_status": "ready",
                    "branch": "fill_viable",
                    "path_ranker_score_visible_to_execution_tree": true,
                    "path_ranker_score_used_by_execution_tree": true,
                    "ranker_validation_ready": true,
                    "hybrid_transition_hazard": 0.595,
                    "pda_hybrid_alignment": true
                },
                "closed_loop_branch_admission": {
                    "status": "admitted",
                    "ready": true,
                    "actionable": true,
                    "candidate_status": "execution_ready",
                    "execution_gate_status": "execution_ready",
                    "execution_tree_gate_status": "ready",
                    "execution_tree_branch": "fill_viable",
                    "path_id": branch_path,
                    "path_label": branch_path,
                    "pre_bayes_gate_status": "pass_neutralized",
                    "review_status": "promote_latest",
                    "source_phase": "structural-recommended-path-bundle"
                }
            }))
            .unwrap(),
        )
        .unwrap();

        persist_execution_candidate_from_analyze(temp.path().to_str().unwrap(), &report, "analyze")
            .unwrap();

        let candidate: ict_engine::state::ExecutionCandidateArtifact =
            ict_engine::state::load_state(
                temp.path(),
                "CRWD",
                ict_engine::state::EXECUTION_CANDIDATE_FILE,
            )
            .unwrap();

        assert_eq!(candidate.trade_direction, Direction::Bull);
        assert!(candidate.actionable);
        assert_eq!(candidate.candidate_status, "execution_ready");
        assert_eq!(candidate.review_decision.status, "promote_latest");
        assert_eq!(
            candidate.review_decision.reason,
            "same_root_execution_tree_admitted"
        );
    }

    #[test]
    fn persist_analyze_run_threads_top_factor_ranking_conformal_metrics_into_latest_analyze_snapshot(
    ) {
        let temp = tempfile::tempdir().unwrap();
        let report = sample_analyze_report_with_factor_ranking(vec![
            ict_engine::state::PersistedFactorRanking {
                factor_name: "dense_kline_upbar_reclaim_tvr_qqq_5m_v1".to_string(),
                composite_score: 0.77,
                conformal_coverage_1sigma: 0.81,
                conformal_miscoverage_1sigma: 0.19,
                mean_prediction_interval_half_width: 0.07,
                worst_window_miscoverage: 0.11,
                ..ict_engine::state::PersistedFactorRanking::default()
            },
        ]);

        let snapshot = persist_analyze_run(
            temp.path().to_str().unwrap(),
            &report,
            "analyze",
            Some("htf.json"),
            Some("mtf.json"),
            Some("ltf.json"),
            None,
        )
        .unwrap();

        let latest = snapshot.latest_analyze.expect("latest analyze snapshot");
        assert_eq!(latest.conformal_coverage_1sigma, Some(0.81));
        assert_eq!(latest.conformal_miscoverage_1sigma, Some(0.19));
        assert_eq!(latest.mean_prediction_interval_half_width, Some(0.07));
        assert_eq!(latest.worst_window_miscoverage, Some(0.11));
    }

    #[test]
    fn persist_analyze_run_threads_liquidity_pool_texture_into_latest_analyze_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let mut report = sample_analyze_report_with_factor_ranking(Vec::new());
        report.analysis.price_action.liquidity_pool_texture =
            ict_engine::analyze_sections::LiquidityPoolTextureEvidence {
                factor_name: "liquidity_pool_texture".to_string(),
                texture: "smooth".to_string(),
                subtype: "equal_low_pool".to_string(),
                level: Some(428.25),
                high: Some(429.0),
                low: Some(427.5),
                touch_count: 5,
                spacing_consistency: Some(0.82),
                clean_sweep_likelihood: Some(0.74),
                confidence: 0.69,
                fail_closed_reason: None,
            };
        report.analysis.price_action.liquidity_sweep_quality =
            ict_engine::analyze_sections::LiquiditySweepQualityEvidence {
                factor_name: "liquidity_sweep_quality".to_string(),
                quality: "clean".to_string(),
                sweep_bar: Some(12),
                return_bar: Some(13),
                pool_price: Some(428.25),
                displacement_atr: Some(0.35),
                return_bars: Some(1),
                close_reclaim: Some(true),
                confidence: 0.71,
                fail_closed_reason: None,
            };

        let snapshot = persist_analyze_run(
            temp.path().to_str().unwrap(),
            &report,
            "analyze",
            None,
            None,
            None,
            None,
        )
        .unwrap();

        let latest = snapshot.latest_analyze.expect("latest analyze snapshot");
        let texture = latest
            .liquidity_pool_texture
            .expect("liquidity pool texture runtime evidence");
        assert_eq!(texture.factor_name, "liquidity_pool_texture");
        assert_eq!(texture.texture, "smooth");
        assert_eq!(texture.subtype, "equal_low_pool");
        assert_eq!(texture.level, Some(428.25));
        assert_eq!(texture.touch_count, 5);
        assert_eq!(texture.spacing_consistency, Some(0.82));
        assert_eq!(texture.clean_sweep_likelihood, Some(0.74));
        assert_eq!(texture.confidence, 0.69);
        assert_eq!(texture.fail_closed_reason, None);
        let sweep_quality = latest
            .liquidity_sweep_quality
            .expect("liquidity sweep quality runtime evidence");
        assert_eq!(sweep_quality.factor_name, "liquidity_sweep_quality");
        assert_eq!(sweep_quality.quality, "clean");
        assert_eq!(sweep_quality.sweep_bar, Some(12));
        assert_eq!(sweep_quality.return_bar, Some(13));
        assert_eq!(sweep_quality.pool_price, Some(428.25));
        assert_eq!(sweep_quality.displacement_atr, Some(0.35));
        assert_eq!(sweep_quality.return_bars, Some(1));
        assert_eq!(sweep_quality.close_reclaim, Some(true));
        assert_eq!(sweep_quality.confidence, 0.71);
        assert_eq!(sweep_quality.fail_closed_reason, None);
    }

    #[test]
    fn persist_analyze_run_threads_volume_imbalance_gap_into_latest_analyze_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let mut report = sample_analyze_report_with_factor_ranking(Vec::new());
        report.analysis.price_action.volume_imbalance_gap =
            ict_engine::analyze_sections::VolumeImbalanceGapEvidence {
                factor_name: "volume_imbalance_gap".to_string(),
                direction: Direction::Bear,
                top: Some(431.5),
                bottom: Some(430.25),
                midpoint: Some(430.875),
                start_bar: Some(27),
                filled: false,
                active: true,
                mitigation_pct: Some(0.25),
                failed_mitigation: false,
                partial_fill_state: "partial".to_string(),
                confidence: 0.63,
                fail_closed_reason: None,
            };

        let snapshot = persist_analyze_run(
            temp.path().to_str().unwrap(),
            &report,
            "analyze",
            None,
            None,
            None,
            None,
        )
        .unwrap();

        let latest = snapshot.latest_analyze.expect("latest analyze snapshot");
        let gap = latest
            .volume_imbalance_gap
            .expect("volume imbalance gap runtime evidence");
        assert_eq!(gap.factor_name, "volume_imbalance_gap");
        assert_eq!(gap.direction, Direction::Bear);
        assert_eq!(gap.top, Some(431.5));
        assert_eq!(gap.bottom, Some(430.25));
        assert_eq!(gap.midpoint, Some(430.875));
        assert_eq!(gap.start_bar, Some(27));
        assert!(!gap.filled);
        assert!(gap.active);
        assert_eq!(gap.confidence, 0.63);
        assert_eq!(gap.fail_closed_reason, None);
    }

    #[test]
    fn test_offline_structural_support_hint_prefers_positive_comparable_high_readiness_runs() {
        let weak = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.50,
            aggregate_return: Some(-0.01),
            execution_readiness: Some(0.42),
            comparable_to_previous: false,
            feedback_records_applied: 0,
            conformal_coverage_1sigma: None,
            regime_break_penalty: None,
            structural_break_detected: None,
            best_factor_composite_score: None,
            quality_delta: Some(-0.04),
            score_before: None,
            score_after: None,
            baseline_available: None,
            accepted: None,
            artifact_validation_bias: None,
        });
        let strong = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.50,
            aggregate_return: Some(0.04),
            execution_readiness: Some(0.83),
            comparable_to_previous: true,
            feedback_records_applied: 8,
            conformal_coverage_1sigma: None,
            regime_break_penalty: None,
            structural_break_detected: None,
            best_factor_composite_score: None,
            quality_delta: Some(0.06),
            score_before: None,
            score_after: None,
            baseline_available: None,
            accepted: None,
            artifact_validation_bias: None,
        });

        assert!(strong > weak);
        assert!(strong > 0.60);
    }

    #[test]
    fn test_offline_structural_support_hint_rewards_accepted_mutation() {
        let rejected = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.55,
            aggregate_return: None,
            execution_readiness: Some(0.60),
            comparable_to_previous: true,
            feedback_records_applied: 0,
            conformal_coverage_1sigma: None,
            regime_break_penalty: None,
            structural_break_detected: None,
            best_factor_composite_score: None,
            quality_delta: Some(-0.02),
            score_before: Some(0.52),
            score_after: Some(0.50),
            baseline_available: Some(true),
            accepted: Some(false),
            artifact_validation_bias: None,
        });
        let accepted = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.55,
            aggregate_return: None,
            execution_readiness: Some(0.60),
            comparable_to_previous: true,
            feedback_records_applied: 0,
            conformal_coverage_1sigma: None,
            regime_break_penalty: None,
            structural_break_detected: None,
            best_factor_composite_score: None,
            quality_delta: Some(0.02),
            score_before: Some(0.52),
            score_after: Some(0.58),
            baseline_available: Some(true),
            accepted: Some(true),
            artifact_validation_bias: None,
        });

        assert!(accepted > rejected);
    }

    #[test]
    fn test_structural_baseline_support_prefers_best_factor_score() {
        assert_eq!(structural_baseline_support(Some(0.78), 0.50), 0.78);
        assert_eq!(structural_baseline_support(None, 0.50), 0.50);
        assert_eq!(structural_baseline_support(Some(1.40), 0.50), 1.0);
        assert_eq!(structural_baseline_support(Some(-0.20), 0.50), 0.0);
    }

    #[test]
    fn test_artifact_validation_support_bias_penalizes_regression() {
        let positive = artifact_validation_support_bias(&ArtifactDecisionSummary {
            consumed_trend_status: "validated_positive".to_string(),
            promotion_strength: "high".to_string(),
            rollback_strength: "low".to_string(),
            ..ArtifactDecisionSummary::default()
        });
        let regressing = artifact_validation_support_bias(&ArtifactDecisionSummary {
            consumed_trend_status: "validated_regressing".to_string(),
            promotion_strength: "low".to_string(),
            rollback_strength: "high".to_string(),
            ..ArtifactDecisionSummary::default()
        });

        assert!(positive > regressing);
        assert!(regressing < 0.0);
    }

    #[test]
    fn test_structural_support_hint_for_research_uses_family_quality() {
        let low = structural_support_hint_for_research(ResearchStructuralSupportInput {
            baseline_composite_score: Some(0.58),
            aggregate_return: 0.01,
            execution_readiness: Some(0.60),
            comparable_to_previous: true,
            feedback_records_applied: 1,
            conformal_coverage_1sigma: Some(0.65),
            regime_break_penalty: Some(0.08),
            structural_break_detected: Some(false),
            quality_delta: Some(0.01),
            family_avg_score: Some(0.42),
        });
        let high = structural_support_hint_for_research(ResearchStructuralSupportInput {
            family_avg_score: Some(0.76),
            ..ResearchStructuralSupportInput {
                baseline_composite_score: Some(0.58),
                aggregate_return: 0.01,
                execution_readiness: Some(0.60),
                comparable_to_previous: true,
                feedback_records_applied: 1,
                conformal_coverage_1sigma: Some(0.65),
                regime_break_penalty: Some(0.08),
                structural_break_detected: Some(false),
                quality_delta: Some(0.01),
                family_avg_score: Some(0.42),
            }
        });

        assert!(high > low);
    }

    #[test]
    fn test_structural_support_hint_for_backtest_penalizes_breaks() {
        let low = structural_support_hint_for_backtest(BacktestStructuralSupportInput {
            baseline_composite_score: Some(0.68),
            aggregate_return: 0.02,
            execution_readiness: Some(0.70),
            comparable_to_previous: true,
            feedback_records_applied: 1,
            conformal_coverage_1sigma: Some(0.48),
            regime_break_penalty: Some(0.22),
            structural_break_detected: Some(true),
            quality_delta: Some(-0.02),
        });
        let high = structural_support_hint_for_backtest(BacktestStructuralSupportInput {
            baseline_composite_score: Some(0.68),
            aggregate_return: 0.02,
            execution_readiness: Some(0.70),
            comparable_to_previous: true,
            feedback_records_applied: 1,
            conformal_coverage_1sigma: Some(0.82),
            regime_break_penalty: Some(0.04),
            structural_break_detected: Some(false),
            quality_delta: Some(0.02),
        });

        assert!(high > low);
    }

    #[test]
    fn test_offline_structural_support_hint_penalizes_breaks_and_rewards_coverage() {
        let poor = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.55,
            aggregate_return: Some(0.01),
            execution_readiness: Some(0.62),
            comparable_to_previous: true,
            feedback_records_applied: 2,
            conformal_coverage_1sigma: Some(0.42),
            regime_break_penalty: Some(0.24),
            structural_break_detected: Some(true),
            best_factor_composite_score: Some(0.48),
            quality_delta: Some(-0.03),
            score_before: None,
            score_after: None,
            baseline_available: None,
            accepted: None,
            artifact_validation_bias: None,
        });
        let good = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.55,
            aggregate_return: Some(0.03),
            execution_readiness: Some(0.76),
            comparable_to_previous: true,
            feedback_records_applied: 6,
            conformal_coverage_1sigma: Some(0.81),
            regime_break_penalty: Some(0.04),
            structural_break_detected: Some(false),
            best_factor_composite_score: Some(0.74),
            quality_delta: Some(0.05),
            score_before: None,
            score_after: None,
            baseline_available: None,
            accepted: None,
            artifact_validation_bias: None,
        });

        assert!(good > poor);
        assert!(good > 0.65);
    }

    #[test]
    fn test_offline_structural_support_hint_rewards_baseline_available_and_score_improvement() {
        let weak = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.58,
            aggregate_return: Some(0.01),
            execution_readiness: Some(0.60),
            comparable_to_previous: true,
            feedback_records_applied: 1,
            conformal_coverage_1sigma: Some(0.66),
            regime_break_penalty: Some(0.08),
            structural_break_detected: Some(false),
            best_factor_composite_score: Some(0.62),
            quality_delta: Some(0.00),
            score_before: Some(0.62),
            score_after: Some(0.62),
            baseline_available: Some(false),
            accepted: None,
            artifact_validation_bias: None,
        });
        let strong = offline_structural_support_hint(OfflineStructuralSupportHintInput {
            baseline_support: 0.58,
            aggregate_return: Some(0.01),
            execution_readiness: Some(0.60),
            comparable_to_previous: true,
            feedback_records_applied: 1,
            conformal_coverage_1sigma: Some(0.66),
            regime_break_penalty: Some(0.08),
            structural_break_detected: Some(false),
            best_factor_composite_score: Some(0.62),
            quality_delta: Some(0.06),
            score_before: Some(0.62),
            score_after: Some(0.71),
            baseline_available: Some(true),
            accepted: None,
            artifact_validation_bias: None,
        });

        assert!(strong > weak);
    }

    #[test]
    fn test_regime_profit_branch_assignments_derive_from_feedback_history() {
        let branch_path = "TrendExpansion -> OpeningDrive -> vwap_reclaim -> mnq_opening_drive_v1";
        let mut learning_state = LearningState::default();
        learning_state.feedback_history.push(FeedbackRecord {
            timestamp: Utc::now(),
            symbol: "MNQ".to_string(),
            source: "structural_feedback_submission".to_string(),
            run_id: Some("analyze:one".to_string()),
            trade_id: None,
            prompt_version: None,
            factor_version: None,
            data_fingerprint: None,
            factors_used: Vec::new(),
            model_probabilities_before_trade: ModelProbabilitySnapshot {
                selected_direction: Direction::Bull,
                selected_probability: 0.62,
                long_score: 0.62,
                short_score: 0.38,
                win_prob_long: 0.62,
                win_prob_short: 0.38,
                uncertainty: 0.18,
            },
            realized_outcome: "win".to_string(),
            pnl: 1.0,
            regime_at_entry: Regime::ManipulationExpansion,
            structural_feedback: Some(ict_engine::state::StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: "structural-feedback:MNQ:one".to_string(),
                recommended_at: Utc::now().to_rfc3339(),
                node_id: "node".to_string(),
                branch_id: "branch".to_string(),
                scenario_id: "scenario".to_string(),
                path_id: branch_path.to_string(),
                followed_path: true,
                exit_reason: None,
                notes: None,
            }),
            reflection_mismatch_tags: Vec::new(),
        });
        learning_state.feedback_history.push(FeedbackRecord {
            timestamp: Utc::now(),
            symbol: "MNQ".to_string(),
            source: "structural_feedback_submission".to_string(),
            run_id: Some("analyze:two".to_string()),
            trade_id: None,
            prompt_version: None,
            factor_version: None,
            data_fingerprint: None,
            factors_used: Vec::new(),
            model_probabilities_before_trade: ModelProbabilitySnapshot {
                selected_direction: Direction::Bull,
                selected_probability: 0.62,
                long_score: 0.62,
                short_score: 0.38,
                win_prob_long: 0.62,
                win_prob_short: 0.38,
                uncertainty: 0.18,
            },
            realized_outcome: "win".to_string(),
            pnl: 1.0,
            regime_at_entry: Regime::ManipulationExpansion,
            structural_feedback: Some(ict_engine::state::StructuralFeedbackRefs {
                protocol_version: "structural-feedback-v1".to_string(),
                recommendation_id: "structural-feedback:MNQ:two".to_string(),
                recommended_at: Utc::now().to_rfc3339(),
                node_id: "node".to_string(),
                branch_id: "branch".to_string(),
                scenario_id: "scenario".to_string(),
                path_id: branch_path.to_string(),
                followed_path: true,
                exit_reason: None,
                notes: None,
            }),
            reflection_mismatch_tags: Vec::new(),
        });

        let entries =
            regime_profit_branch_assignment_entries_from_feedback_history(&learning_state)
                .expect("dominant exact branch path");

        assert!(entries
            .iter()
            .any(|(key, value)| { key == "regime_profit_branch_path" && value == branch_path }));
        assert!(entries.iter().any(|(key, value)| {
            key == "regime_profit_branch_path_source" && value == "structural_feedback_history"
        }));
        assert!(entries.iter().any(|(key, value)| {
            key == "regime_profit_branch_path_feedback_count" && value == "2"
        }));
    }
}
