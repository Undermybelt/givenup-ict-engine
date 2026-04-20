use anyhow::Result;
use serde::Serialize;

use crate::analyze_report_shell::AnalyzeReport;
use crate::application::belief::{BeliefPolicyLineageSurface, BeliefShadowPolicySurface};
use crate::application::output_foundation::{
    format_executor_summary_lines, print_redacted_json, redact_local_paths,
};
use crate::application::reporting::{
    build_agent_guidance_report, build_compact_analyze_report, build_human_analyze_report,
    humanize_decision_hint, AgentGuidanceReport, CompactAnalyzeReport, HumanAnalyzeReport,
};

use crate::types::Direction;

#[derive(Debug, Serialize)]
pub struct AnalyzeMarketFamilySummary {
    pub market_family: Option<String>,
    pub market_behavior_profile: Option<String>,
    pub selected_market_subgraph: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct AnalyzeOutputEnvelope<R, E>
where
    R: Serialize,
    E: Serialize,
{
    pub report: R,
    pub compact_report: CompactAnalyzeReport,
    pub agent_report: AgentGuidanceReport,
    pub human_report: String,
    pub market_family_summary: AnalyzeMarketFamilySummary,
    pub belief_shadow_policy: BeliefShadowPolicySurface,
    pub belief_policy_lineage: BeliefPolicyLineageSurface,
    pub ensemble_vote: E,
    pub executor_scorecard_summary: Vec<String>,
    pub executor_scorecard_source: String,
}

#[derive(Debug, Serialize)]
pub struct AnalyzeLiveOutputEnvelope<R>
where
    R: Serialize,
{
    pub report: R,
    pub source_snapshot: Option<serde_json::Value>,
    pub freshness_gate: Option<serde_json::Value>,
    pub compact_report: CompactAnalyzeReport,
    pub agent_report: AgentGuidanceReport,
    pub human_report: String,
    pub belief_shadow_policy: BeliefShadowPolicySurface,
}

#[derive(Debug, Clone, Copy)]
pub struct AnalyzeOutputDispatchInput<'a> {
    pub output_format: &'a str,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct AnalyzeLiveOutputDispatchInput;

#[derive(Debug, Clone)]
pub struct AnalyzeHumanInput<'a> {
    pub symbol: &'a str,
    pub selected_direction: Direction,
    pub entry_quality: &'a str,
    pub gate_status: &'a str,
    pub evidence_quality_score: f64,
    pub decision_hint: &'a str,
    pub factor_iteration_queue: &'a [crate::state::FactorIterationPrompt],
    pub recommended_next_command: &'a str,
    pub price_action_narrative: &'a str,
    pub technical_price_narrative: &'a str,
    pub smt_correlation_narrative: &'a str,
    pub regime_label: &'a str,
    pub liquidity_label: &'a str,
    pub regime_selected_direction: Direction,
    pub trade_plan_narrative: &'a str,
    pub market_family: Option<&'a str>,
    pub market_subgraph: &'a str,
    pub objective_jump_weight: Option<f64>,
}

pub fn build_analyze_compact_evidence(
    multi_timeframe_summary: &[String],
    objective_jump_weight: Option<f64>,
) -> Vec<String> {
    let objective_jump_weight =
        objective_jump_weight.map(|weight| format!("objective_jump_weight={weight:.3}"));
    objective_jump_weight
        .iter()
        .chain(multi_timeframe_summary.iter())
        .cloned()
        .collect::<Vec<_>>()
}

pub fn build_analyze_reporting_bundle(
    input: AnalyzeHumanInput<'_>,
    artifact_action_summary: &[String],
    multi_timeframe_summary: &[String],
    decision_hint: &str,
    selected_direction: Direction,
    entry_quality_state: &str,
    gate_status: &str,
    recommended_next_command: &str,
) -> (
    CompactAnalyzeReport,
    AgentGuidanceReport,
    HumanAnalyzeReport,
) {
    let compact_evidence =
        build_analyze_compact_evidence(multi_timeframe_summary, input.objective_jump_weight);
    let compact_report = build_compact_analyze_report(
        decision_hint.to_string(),
        Some(format!("{:?}", selected_direction)),
        Some(entry_quality_state.to_string()),
        Some(gate_status.to_string()),
        Some(recommended_next_command.to_string()),
        &compact_evidence,
        artifact_action_summary,
        std::slice::from_ref(&recommended_next_command.to_string()),
    );
    let agent_report = build_agent_guidance_report(
        Some(format!("{:?}", selected_direction)),
        Some(entry_quality_state.to_string()),
        Some(gate_status.to_string()),
        Some(recommended_next_command.to_string()),
        Some(decision_hint.to_string()),
        multi_timeframe_summary,
        artifact_action_summary,
        std::slice::from_ref(&recommended_next_command.to_string()),
    );
    let human_report = build_human_analyze_surface(input);
    (compact_report, agent_report, human_report)
}

pub fn build_analyze_policy_outputs(
    report: &AnalyzeReport,
) -> Result<(BeliefShadowPolicySurface, BeliefPolicyLineageSurface)> {
    let policy_history =
        crate::state::load_pre_bayes_policy_history(&report.meta.state_dir, &report.symbol)?;
    let policy_record = policy_history.last().cloned();
    let shadow = crate::application::belief::build_belief_shadow_policy_surface(
        &report.supporting.canonical_belief_report,
        policy_record.as_ref(),
    );
    let lineage = crate::application::belief::build_belief_policy_lineage_surface(
        &policy_history,
        report
            .supporting
            .pre_bayes_evidence_filter
            .gating_status
            .as_str(),
    );
    Ok((shadow, lineage))
}

pub fn emit_analyze_output(report: &AnalyzeReport, output_format: &str) -> Result<()> {
    dispatch_analyze_output(report, AnalyzeOutputDispatchInput { output_format })
}

pub fn dispatch_analyze_output(
    report: &AnalyzeReport,
    input: AnalyzeOutputDispatchInput<'_>,
) -> Result<()> {
    let (compact_report, agent_report, human_report) = build_analyze_reporting_bundle(
        AnalyzeHumanInput {
            symbol: &report.symbol,
            selected_direction: report.supporting.decision.selected_direction,
            entry_quality: &report.supporting.entry_quality.selected_state,
            gate_status: &report.supporting.pre_bayes_evidence_filter.gating_status,
            evidence_quality_score: report
                .supporting
                .pre_bayes_evidence_filter
                .evidence_quality_score,
            decision_hint: &report.supporting.decision_hint,
            factor_iteration_queue: &report.supporting.factor_iteration_queue,
            recommended_next_command: &report.supporting.recommended_next_command,
            price_action_narrative: &report.analysis.price_action.narrative,
            technical_price_narrative: &report.analysis.technical_price.narrative,
            smt_correlation_narrative: &report.analysis.smt_correlation.narrative,
            regime_label: &report.analysis.regime_bayesian.regime_label,
            liquidity_label: &report.analysis.regime_bayesian.liquidity_label,
            regime_selected_direction: report.analysis.regime_bayesian.selected_direction,
            trade_plan_narrative: &report.analysis.trade_plan.narrative,
            market_family: report
                .supporting
                .canonical_belief_report
                .market_family
                .as_deref(),
            market_subgraph: report
                .supporting
                .canonical_belief_report
                .selected_market_subgraph
                .as_deref()
                .unwrap_or("unknown"),
            objective_jump_weight: report.supporting.objective_jump_weight,
        },
        &report.supporting.artifact_action_summary,
        &report.supporting.multi_timeframe_summary,
        &report.supporting.decision_hint,
        report.supporting.decision.selected_direction,
        &report.supporting.entry_quality.selected_state,
        &report.supporting.pre_bayes_evidence_filter.gating_status,
        &report.supporting.recommended_next_command,
    );
    let (belief_shadow_policy, belief_policy_lineage) = build_analyze_policy_outputs(report)?;
    let ensemble_vote = crate::application::orchestration::build_stub_ensemble_vote_from_input(
        &crate::application::orchestration::AnalyzeEnsembleVoteInput {
            symbol: report.symbol.clone(),
            state_dir: None,
            recommended_next_command: report.supporting.recommended_next_command.clone(),
            hard_blocked: false,
            hard_block_reason: None,
            hard_block_command: None,
            provenance: report.supporting.provenance.clone(),
            dataset_comparability: report.supporting.dataset_comparability.clone(),
            pre_bayes_filter: Some(report.supporting.pre_bayes_evidence_filter.clone()),
            belief: report.supporting.canonical_belief_report.clone(),
            ict_structure: None,
        },
    );
    let persisted_scorecards =
        crate::state::load_ensemble_executor_scorecards(&report.meta.state_dir, &report.symbol)
            .unwrap_or_default();
    let (_, scorecard_source) =
        crate::application::orchestration::executor_scorecard_surface(&persisted_scorecards, &[]);

    emit_analyze_output_envelope(
        report,
        input.output_format,
        &compact_report,
        &agent_report,
        &human_report,
        AnalyzeMarketFamilySummary {
            market_family: report
                .supporting
                .canonical_belief_report
                .market_family
                .clone(),
            market_behavior_profile: report
                .supporting
                .canonical_belief_report
                .market_behavior_profile
                .clone(),
            selected_market_subgraph: report
                .supporting
                .canonical_belief_report
                .selected_market_subgraph
                .clone(),
        },
        belief_shadow_policy,
        belief_policy_lineage,
        &ensemble_vote,
        scorecard_source,
    )
}

pub fn emit_analyze_live_output(report: &AnalyzeReport) -> Result<()> {
    dispatch_analyze_live_output(report, AnalyzeLiveOutputDispatchInput)
}

pub fn dispatch_analyze_live_output(
    report: &AnalyzeReport,
    _input: AnalyzeLiveOutputDispatchInput,
) -> Result<()> {
    let source_snapshot = report.meta.data_source.as_ref().map(|source| {
        crate::application::data_sources::build_source_snapshot(source, report.timestamp)
    });
    let freshness_gate = report.meta.data_source.as_ref().map(|source| {
        crate::application::decision_freshness::build_decision_freshness_gate(
            300,
            report
                .timestamp
                .signed_duration_since(source.fetched_at)
                .num_seconds(),
        )
    });
    let (compact_report, agent_report, human_report) = build_analyze_reporting_bundle(
        AnalyzeHumanInput {
            symbol: &report.symbol,
            selected_direction: report.supporting.decision.selected_direction,
            entry_quality: &report.supporting.entry_quality.selected_state,
            gate_status: &report.supporting.pre_bayes_evidence_filter.gating_status,
            evidence_quality_score: report
                .supporting
                .pre_bayes_evidence_filter
                .evidence_quality_score,
            decision_hint: &report.supporting.decision_hint,
            factor_iteration_queue: &report.supporting.factor_iteration_queue,
            recommended_next_command: &report.supporting.recommended_next_command,
            price_action_narrative: &report.analysis.price_action.narrative,
            technical_price_narrative: &report.analysis.technical_price.narrative,
            smt_correlation_narrative: &report.analysis.smt_correlation.narrative,
            regime_label: &report.analysis.regime_bayesian.regime_label,
            liquidity_label: &report.analysis.regime_bayesian.liquidity_label,
            regime_selected_direction: report.analysis.regime_bayesian.selected_direction,
            trade_plan_narrative: &report.analysis.trade_plan.narrative,
            market_family: report
                .supporting
                .canonical_belief_report
                .market_family
                .as_deref(),
            market_subgraph: report
                .supporting
                .canonical_belief_report
                .selected_market_subgraph
                .as_deref()
                .unwrap_or("unknown"),
            objective_jump_weight: report.supporting.objective_jump_weight,
        },
        &report.supporting.artifact_action_summary,
        &report.supporting.multi_timeframe_summary,
        &report.supporting.decision_hint,
        report.supporting.decision.selected_direction,
        &report.supporting.entry_quality.selected_state,
        &report.supporting.pre_bayes_evidence_filter.gating_status,
        &report.supporting.recommended_next_command,
    );
    let policy_record =
        crate::state::load_pre_bayes_policy_history(&report.meta.state_dir, &report.symbol)?
            .into_iter()
            .last();
    let belief_shadow_policy = crate::application::belief::build_belief_shadow_policy_surface(
        &report.supporting.canonical_belief_report,
        policy_record.as_ref(),
    );

    emit_analyze_live_output_envelope(
        report,
        source_snapshot,
        freshness_gate,
        compact_report,
        agent_report,
        &human_report,
        belief_shadow_policy,
    )
}

fn human_direction_bias_label(direction: Direction) -> &'static str {
    match direction {
        Direction::Bull => "Bull bias",
        Direction::Bear => "Bear bias",
        Direction::Neutral => "Neutral bias",
    }
}

fn human_action_line(queue: &[crate::state::FactorIterationPrompt]) -> String {
    let action = queue
        .iter()
        .find(|item| item.iteration_action != "keep" || item.replacement_candidate)
        .map(|item| {
            format!(
                "{} {}",
                item.iteration_action.to_uppercase(),
                item.factor_name
            )
        })
        .unwrap_or_else(|| "OBSERVE no_factor_change".to_string());
    format!("Action: {}", action)
}

pub fn build_human_analyze_surface(input: AnalyzeHumanInput<'_>) -> HumanAnalyzeReport {
    let regime_bayes_analysis = match input.market_family {
        Some("metals") => match input.objective_jump_weight {
            Some(weight) => format!(
                "金属品种视角：regime={} liquidity={} direction={:?}。现属防御型流动性环境，先看扫流动性后是否回到顺势确认；subgraph={}；objective_jump_weight={weight:.3}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
            None => format!(
                "金属品种视角：regime={} liquidity={} direction={:?}。现属防御型流动性环境，先看扫流动性后是否回到顺势确认；subgraph={}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
        },
        Some("energy") => match input.objective_jump_weight {
            Some(weight) => format!(
                "能源品种视角：regime={} liquidity={} direction={:?}。当前更该尊重波动冲击与状态切换，先防急拉急杀再谈延续；subgraph={}；objective_jump_weight={weight:.3}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
            None => format!(
                "能源品种视角：regime={} liquidity={} direction={:?}。当前更该尊重波动冲击与状态切换，先防急拉急杀再谈延续；subgraph={}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
        },
        Some("futures_index") => match input.objective_jump_weight {
            Some(weight) => format!(
                "股指品种视角：regime={} liquidity={} direction={:?}。先看 beta 与多周期共振是否同向，再决定是否执行；subgraph={}；objective_jump_weight={weight:.3}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
            None => format!(
                "股指品种视角：regime={} liquidity={} direction={:?}。先看 beta 与多周期共振是否同向，再决定是否执行；subgraph={}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
        },
        _ => match input.objective_jump_weight {
            Some(weight) => format!(
                "regime={} liquidity={} direction={:?} subgraph={} objective_jump_weight={weight:.3}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
            None => format!(
                "regime={} liquidity={} direction={:?} subgraph={}",
                input.regime_label,
                input.liquidity_label,
                input.regime_selected_direction,
                input.market_subgraph
            ),
        },
    };

    let basic_price_structure_analysis = match input.market_family {
        Some("metals") => format!(
            "金属结构偏向：{}。这类盘先看流动性是否被扫完，再等回到顺势一侧；原始标签={}。",
            if input.regime_selected_direction == Direction::Bull {
                "偏多，但不宜追"
            } else if input.regime_selected_direction == Direction::Bear {
                "偏空，但更重确认"
            } else {
                "先观望，等再定向"
            },
            input.price_action_narrative
        ),
        Some("energy") => format!(
            "能源结构偏向：{}。这类盘最怕突发冲击，先防假突破和急反转；原始标签={}。",
            if input.regime_selected_direction == Direction::Bear {
                "空头占优，但随时防剧烈反抽"
            } else if input.regime_selected_direction == Direction::Bull {
                "多头占优，但别忽视突发回吐"
            } else {
                "方向未完全站稳，先等波动收敛"
            },
            input.price_action_narrative
        ),
        _ => input.price_action_narrative.to_string(),
    };

    let technical_price_analysis = match input.market_family {
        Some("metals") => format!(
            "金属技术面：更重均值回归后的二次确认，别把一次拉伸当延续；原始标签={}。",
            input.technical_price_narrative
        ),
        Some("energy") => format!(
            "能源技术面：指标易被波动放大，先看节奏是否稳定，再看趋势是否继续；原始标签={}。",
            input.technical_price_narrative
        ),
        _ => input.technical_price_narrative.to_string(),
    };

    let smt_correlation_analysis = match input.market_family {
        Some("metals") => format!(
            "金属联动面：相关性可参考，但最终仍以本品种流动性反应为主；原始标签={}。",
            input.smt_correlation_narrative
        ),
        Some("energy") => format!(
            "能源联动面：相关市场常会同步放大波动，若联动发散，先减信号强度；原始标签={}。",
            input.smt_correlation_narrative
        ),
        _ => input.smt_correlation_narrative.to_string(),
    };

    build_human_analyze_report(
        Some(format!(
            "{} | {} | Entry: {} | Gate: {} | Quality: {:.3}",
            input.symbol,
            human_direction_bias_label(input.selected_direction),
            input.entry_quality,
            input.gate_status,
            input.evidence_quality_score
        )),
        Some(format!(
            "Decision: {}",
            humanize_decision_hint(input.decision_hint)
        )),
        Some(human_action_line(input.factor_iteration_queue)),
        Some(format!("Next: {}", input.recommended_next_command)),
        basic_price_structure_analysis,
        technical_price_analysis,
        smt_correlation_analysis,
        regime_bayes_analysis,
        input.trade_plan_narrative,
    )
}

pub fn build_analyze_output_envelope<R, E>(
    report: R,
    compact_report: CompactAnalyzeReport,
    agent_report: AgentGuidanceReport,
    human_report: &HumanAnalyzeReport,
    market_family_summary: AnalyzeMarketFamilySummary,
    belief_shadow_policy: BeliefShadowPolicySurface,
    belief_policy_lineage: BeliefPolicyLineageSurface,
    ensemble_vote: E,
    executor_scorecard_source: impl Into<String>,
) -> AnalyzeOutputEnvelope<R, E>
where
    R: Serialize,
    E: Serialize,
{
    let ensemble_value = serde_json::to_value(&ensemble_vote).expect("serialize ensemble vote");
    let executor_summaries = ensemble_value
        .get("executor_summaries")
        .and_then(serde_json::Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(serde_json::Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();

    AnalyzeOutputEnvelope {
        report,
        compact_report,
        agent_report,
        human_report: human_report.render(),
        market_family_summary,
        belief_shadow_policy,
        belief_policy_lineage,
        ensemble_vote,
        executor_scorecard_summary: format_executor_summary_lines(&executor_summaries),
        executor_scorecard_source: executor_scorecard_source.into(),
    }
}

pub fn build_analyze_live_output_envelope<R>(
    report: R,
    source_snapshot: Option<impl Serialize>,
    freshness_gate: Option<impl Serialize>,
    compact_report: CompactAnalyzeReport,
    agent_report: AgentGuidanceReport,
    human_report: &HumanAnalyzeReport,
    belief_shadow_policy: BeliefShadowPolicySurface,
) -> AnalyzeLiveOutputEnvelope<R>
where
    R: Serialize,
{
    AnalyzeLiveOutputEnvelope {
        report,
        source_snapshot: source_snapshot
            .map(|value| serde_json::to_value(value).expect("serialize source snapshot")),
        freshness_gate: freshness_gate
            .map(|value| serde_json::to_value(value).expect("serialize freshness gate")),
        compact_report,
        agent_report,
        human_report: human_report.render(),
        belief_shadow_policy,
    }
}

pub fn emit_analyze_output_envelope<R, E>(
    report: &R,
    output_format: &str,
    compact_report: &CompactAnalyzeReport,
    agent_report: &AgentGuidanceReport,
    human_report: &HumanAnalyzeReport,
    market_family_summary: AnalyzeMarketFamilySummary,
    belief_shadow_policy: BeliefShadowPolicySurface,
    belief_policy_lineage: BeliefPolicyLineageSurface,
    ensemble_vote: &E,
    executor_scorecard_source: impl Into<String>,
) -> Result<()>
where
    R: Serialize,
    E: Serialize,
{
    let full_output = build_analyze_output_envelope(
        report,
        compact_report.clone(),
        agent_report.clone(),
        human_report,
        market_family_summary,
        belief_shadow_policy,
        belief_policy_lineage,
        ensemble_vote,
        executor_scorecard_source,
    );

    match output_format.trim().to_ascii_lowercase().as_str() {
        "json" => print_redacted_json(&full_output)?,
        "compact" => print_redacted_json(compact_report)?,
        "agent" => print_redacted_json(agent_report)?,
        "human" => println!("{}", redact_local_paths(&human_report.render())),
        other => anyhow::bail!("unsupported output format '{}'", other),
    }
    Ok(())
}

pub fn emit_analyze_live_output_envelope<R>(
    report: &R,
    source_snapshot: Option<impl Serialize>,
    freshness_gate: Option<impl Serialize>,
    compact_report: CompactAnalyzeReport,
    agent_report: AgentGuidanceReport,
    human_report: &HumanAnalyzeReport,
    belief_shadow_policy: BeliefShadowPolicySurface,
) -> Result<()>
where
    R: Serialize,
{
    let output = build_analyze_live_output_envelope(
        report,
        source_snapshot,
        freshness_gate,
        compact_report,
        agent_report,
        human_report,
        belief_shadow_policy,
    );
    print_redacted_json(&output)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::reporting::{
        build_agent_guidance_report, build_compact_analyze_report,
    };

    #[derive(Debug, Clone, Serialize)]
    struct StubReport {
        symbol: String,
    }

    #[derive(Debug, Clone, Serialize)]
    struct StubEnsembleVote {
        executor_summaries: Vec<String>,
        final_action: String,
    }

    #[derive(Debug, Clone, Serialize)]
    struct StubSnapshot {
        status: String,
    }

    #[test]
    fn dispatch_analyze_output_input_preserves_output_format() {
        let input = AnalyzeOutputDispatchInput {
            output_format: "agent",
        };
        assert_eq!(input.output_format, "agent");
    }

    #[test]
    fn analyze_live_output_dispatch_input_default_constructs() {
        let _input = AnalyzeLiveOutputDispatchInput;
    }

    #[test]
    fn build_analyze_output_envelope_collects_executor_summary() {
        let report = StubReport {
            symbol: "NQ".to_string(),
        };
        let compact_report = build_compact_analyze_report(
            "observe_only",
            Some("Bull".to_string()),
            Some("medium".to_string()),
            Some("pass_neutralized".to_string()),
            Some("ict-engine analyze".to_string()),
            &[],
            &[],
            &[],
        );
        let agent_report = build_agent_guidance_report(
            Some("Bull".to_string()),
            Some("medium".to_string()),
            Some("pass_neutralized".to_string()),
            Some("ict-engine analyze".to_string()),
            Some("observe_only".to_string()),
            &[],
            &[],
            &[],
        );
        let human_report = build_human_analyze_surface(AnalyzeHumanInput {
            symbol: "NQ",
            selected_direction: Direction::Bull,
            entry_quality: "medium",
            gate_status: "pass_neutralized",
            evidence_quality_score: 0.5,
            decision_hint: "observe_only",
            factor_iteration_queue: &[],
            recommended_next_command: "ict-engine analyze",
            price_action_narrative: "price",
            technical_price_narrative: "tech",
            smt_correlation_narrative: "smt",
            regime_label: "trend",
            liquidity_label: "sweep",
            regime_selected_direction: Direction::Bull,
            trade_plan_narrative: "plan",
            market_family: Some("futures_index"),
            market_subgraph: "index_beta",
            objective_jump_weight: Some(0.25),
        });
        let vote = StubEnsembleVote {
            executor_summaries: vec![
                "executor=catboost_file action=observe confidence=0.55 weight=0.55".to_string(),
            ],
            final_action: "observe".to_string(),
        };

        let output = build_analyze_output_envelope(
            report,
            compact_report,
            agent_report,
            &human_report,
            AnalyzeMarketFamilySummary {
                market_family: Some("futures_index".to_string()),
                market_behavior_profile: Some("index_beta_regime_sensitive".to_string()),
                selected_market_subgraph: Some("index_beta".to_string()),
            },
            BeliefShadowPolicySurface::default(),
            BeliefPolicyLineageSurface::default(),
            vote,
            "persisted",
        );

        assert_eq!(output.executor_scorecard_summary.len(), 1);
        assert_eq!(output.executor_scorecard_source, "persisted");
        assert!(output.human_report.contains("Trade plan"));
    }

    #[test]
    fn build_analyze_live_output_envelope_serializes_optional_surfaces() {
        let report = StubReport {
            symbol: "NQ".to_string(),
        };
        let human_report = build_human_analyze_surface(AnalyzeHumanInput {
            symbol: "NQ",
            selected_direction: Direction::Bull,
            entry_quality: "medium",
            gate_status: "pass_neutralized",
            evidence_quality_score: 0.5,
            decision_hint: "observe_only",
            factor_iteration_queue: &[],
            recommended_next_command: "ict-engine analyze",
            price_action_narrative: "price",
            technical_price_narrative: "tech",
            smt_correlation_narrative: "smt",
            regime_label: "trend",
            liquidity_label: "sweep",
            regime_selected_direction: Direction::Bull,
            trade_plan_narrative: "plan",
            market_family: None,
            market_subgraph: "unknown",
            objective_jump_weight: None,
        });
        let output = build_analyze_live_output_envelope(
            report,
            Some(StubSnapshot {
                status: "fresh".to_string(),
            }),
            Some(StubSnapshot {
                status: "ok".to_string(),
            }),
            build_compact_analyze_report("observe_only", None, None, None, None, &[], &[], &[]),
            build_agent_guidance_report(None, None, None, None, None, &[], &[], &[]),
            &human_report,
            BeliefShadowPolicySurface::default(),
        );

        assert_eq!(output.source_snapshot.unwrap()["status"], "fresh");
        assert_eq!(output.freshness_gate.unwrap()["status"], "ok");
        assert!(output.human_report.contains("Trade plan"));
    }
}
