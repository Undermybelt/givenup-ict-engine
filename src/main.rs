use anyhow::{anyhow, bail, Context, Result};
use chrono::{Duration, Utc};
use clap::{Parser, Subcommand};
use ict_engine::agent::{
    dataset_audit_prompt, factor_iteration_prompt_pack, promotion_gate_prompt,
    research_diff_prompt, rollback_review_prompt, update_diff_prompt, AgentPrompt, AgentPromptPack,
    PROMPT_PACK_VERSION,
};
use ict_engine::analyze::multi_timeframe_parse::parse_multi_timeframe_evidence;
use ict_engine::analyze::multi_timeframe_section::{
    build_analyze_multi_timeframe_section, AnalyzeMultiTimeframeSection,
};
use ict_engine::analyze::options_hedging_section::OptionsHedgingSection;
use ict_engine::analyze::smt_correlation_section::{
    build_smt_correlation_section, empty_smt_correlation_section, SmtCorrelationSection,
};
use ict_engine::analyze::technical_price_section::{
    build_technical_price_section, TechnicalPriceSection,
};
use ict_engine::application::{
    backtest::build_backtest_result_artifact,
    belief::{
        apply_factor_outcome_overlay, build_belief_policy_lineage_surface,
        build_belief_shadow_policy_surface, build_canonical_belief_snapshot,
        build_expansion_factor_pipeline_report as build_expansion_factor_pipeline_report_v2,
        build_expansion_factor_pipeline_report_with_registry as build_expansion_factor_pipeline_report_with_registry_v2,
        build_factor_pipeline_debug_report as build_factor_pipeline_debug_report_v2,
        build_pre_bayes_entry_quality_bridge, combine_bias_vectors,
        debug_report::{
            ExpansionBbnSupport as DebugExpansionBbnSupport,
            ExpansionLatestSignal as DebugExpansionLatestSignal,
            ExpansionProbabilitySupport as DebugExpansionProbabilitySupport,
        },
        infer_market_from_symbol, multi_timeframe_entry_quality_bias,
        pipeline_types::ExpansionFactorPipelineReport,
        pre_bayes_evidence_policy, probability_map, FactorPipelineDebugReport,
    },
    data_sources::build_source_snapshot,
    decision_freshness::build_decision_freshness_gate,
    decision_utils::{
        derive_family_outcomes, derive_promotion_decision, derive_rollback_recommendation,
        normalize_entry_quality_label, normalize_trade_outcome_label, parse_research_objective,
        research_objective_label, score_grade, ArtifactConsumedDecisionGate, ResearchObjectiveMode,
    },
    factor_lifecycle::build_factor_lifecycle_view,
    multi_timeframe_inputs::{
        detected_multi_timeframe_clean_root, infer_interval_for_analyze_frame,
        resolve_analyze_cli_inputs, resolve_analyze_multi_timeframe_inputs,
        resolve_multi_timeframe_inputs, resolved_multi_timeframe_inputs_for_market,
        MultiTimeframeCleanReportView, ResolvedMultiTimeframeInputs, MULTI_TIMEFRAME_INTERVALS,
    },
    orchestration::{
        build_stub_ensemble_vote_from_input, build_stub_ensemble_vote_from_research,
        run_stage_plan, staged_orchestration_enabled, AnalyzeEnsembleVoteInput,
        CatBoostCompatiblePolicyEngine, FinalOutputAdapter, FinalSurfaceAdapter, PipelineState,
        StagePlan,
    },
    reflection::{build_reflection_bundle, build_research_reflection_bundle},
    reporting::{
        build_agent_guidance_report, build_compact_analyze_report, build_human_analyze_report,
    },
};
use ict_engine::backtest::engine::{AmbiguousBarPolicy, ExecutionRealismConfig};
use ict_engine::backtest::{BacktestEngine, Metrics, RegimeSplit};
use ict_engine::bayesian::{cascade_bear, cascade_bull, CascadeConfig};
use ict_engine::bbn::learning::cpt_updater::{CPTUpdater, TradeOutcome};
use ict_engine::bbn::trading::{
    topology::{build_trading_network, upgrade_trading_network},
    update::{
        entry_quality_bias_from_signal, infer_entry_quality, infer_entry_quality_with_bias,
        infer_trade_outcome, infer_trade_outcome_with_entry_quality_bias,
        trade_evidence_from_labels, trade_evidence_from_pre_bayes_filter,
    },
};
use ict_engine::config::{
    build_frame_features, build_pre_bayes_evidence_filter, left_pad, FrameFeatures,
    INDICATOR_PERIOD,
};
use ict_engine::data::{
    aggregate_candles_by_minutes, load_candles, load_tomac_continuous_candles,
    realtime::{
        build_live_data_source,
        openalice::{AuxiliaryMarketEvidence, SpotInstrumentKind},
        LiveDataBackend,
    },
    CleanedContinuousFuturesSummary,
};
use ict_engine::factor_lab::{
    BacktestConfig as FactorBacktestConfig, FactorContext, FactorDiagnostics, FactorEngine,
    FactorLab,
};
use ict_engine::factors::{FactorRegistry, WeightUpdater};
use ict_engine::hmm::{init_hmm_params, state_name, BaumWelch, ForwardBackward, Viterbi};
use ict_engine::ict::{
    check_bear_expansion_exists, check_bull_expansion_exists, count_recent_breaks,
    count_recent_sweeps, detect_cisd, detect_liquidity_pools, detect_liquidity_sweep,
    detect_order_blocks, detect_structure_breaks, expansion_strength, find_swing_highs,
    find_swing_lows, find_unfilled_fvgs, find_untested_obs, has_recent_pinbar,
};
use ict_engine::indicators::compute_atr;
use ict_engine::planner::{
    generate_probabilistic_trade_plan, probabilistic_decision_snapshot,
    ProbabilisticDecisionSnapshot, ProbabilisticPlanConfig,
};
use serde_json::Value;

use ict_engine::state::{
    append_analyze_run, append_artifact_ledger_entry, append_backtest_run,
    append_ensemble_vote_history, append_execution_candidate_history, append_factor_mutation_run,
    append_pending_update_artifact_history, append_pre_bayes_policy_history, append_research_run,
    append_trade_history, append_train_run, append_update_run, load_artifact_ledger,
    load_ensemble_executor_scorecards, load_ensemble_vote_history,
    load_execution_candidate_history, load_learning_state, load_pending_update_artifact,
    load_pending_update_history, load_pre_bayes_policy_history, load_state, load_state_or_default,
    load_workflow_snapshot, mark_artifact_consumed, migrate_ensemble_executor_scorecards,
    save_ensemble_executor_scorecards, save_ensemble_vote_artifact,
    save_execution_candidate_artifact, save_learning_state, save_pending_update_artifact,
    save_state, save_workflow_snapshot, state_exists, AgentActionItem, AgentActionPlan,
    AgentContextBundle, AgentContextBundleMinimal, AnalyzeRunRecord, ArtifactLedgerEntry,
    BacktestRunRecord, CommandRecommendations, DatasetComparability, DecisionHistorySummary,
    DecisionThresholds, EnsembleExecutorScorecard, EnsembleVoteRecord, ExecutionCandidateArtifact,
    ExecutionCandidateArtifactDecision, ExecutionCandidateArtifactDiff,
    ExecutionCandidateArtifactSummary, ExpectedStateChange, FactorFamilyDecision, FactorFamilyDiff,
    FactorFamilyHistory, FactorFamilyOutcome, FactorIterationPrompt, FactorMutationEvaluation,
    FactorMutationMetricSet, FactorMutationRunRecord, FactorMutationSpec, FeedbackFactorUsage,
    FeedbackHistorySummary, FeedbackRecord, LearningState, LiveDataSourceProvenance,
    ModelProbabilitySnapshot, PendingUpdateArtifact, PendingUpdateArtifactDecision,
    PendingUpdateArtifactDiff, PendingUpdateArtifactSummary, PersistedFactorRanking,
    PreBayesEvidenceFilter, PreBayesPolicyRecord, ProbabilityDiff, PromotionDecision,
    RankingDiffItem, RecommendedCommand, ResearchRunRecord, RollbackRecommendation, RunProvenance,
    StageAgentContext, StageAgentContextMinimal, TrainRunRecord, UpdateRunRecord,
    WorkflowBlockingTruth, WorkflowConflictSource, WorkflowDisagreement, WorkflowFieldDiff,
    WorkflowPhaseSnapshot, WorkflowSnapshot, WorkflowState, ANALYZE_RUNS_FILE, BACKTEST_RUNS_FILE,
    ENSEMBLE_VOTE_FILE, EXECUTION_CANDIDATE_FILE, FACTOR_MUTATION_RUNS_FILE,
    PENDING_UPDATE_ARTIFACT_FILE, RESEARCH_RUNS_FILE, TRAIN_RUNS_FILE, UPDATE_RUNS_FILE,
};
use ict_engine::types::{
    Candle, CascadeLayer, Direction, HMMParams, Regime, RegimeProbs, Symbol, TradePlan,
    TradeRecord, OBS_DIM,
};
use serde::Serialize;
use std::collections::hash_map::DefaultHasher;
use std::collections::{BTreeMap, BTreeSet, HashMap};
use std::env;
use std::hash::{Hash, Hasher};

const HMM_STATE_FILE: &str = "hmm_params.json";
const BBN_STATE_FILE: &str = "bbn_network.json";
#[derive(Debug, Serialize)]
struct AnalyzeReport {
    symbol: String,
    timestamp: chrono::DateTime<Utc>,
    #[serde(flatten)]
    analysis: AnalyzeSections,
    meta: AnalyzeMeta,
    supporting: AnalyzeSupporting,
}

#[derive(Debug, Serialize)]
struct AnalyzeMeta {
    state_dir: String,
    bars: AnalyzeBars,
    #[serde(skip_serializing_if = "Option::is_none")]
    data_source: Option<LiveDataSourceProvenance>,
}

#[derive(Debug, Serialize)]
struct AnalyzeSupporting {
    model_state: AnalyzeModelState,
    provenance: RunProvenance,
    promotion_decision: PromotionDecision,
    rollback_recommendation: RollbackRecommendation,
    labels: AnalyzeLabels,
    ict: AnalyzeIctSummary,
    entry_quality: AnalyzeEntryQualitySummary,
    #[serde(skip_serializing_if = "Option::is_none")]
    auxiliary: Option<AuxiliaryMarketEvidence>,
    decision: ProbabilisticDecisionSnapshot,
    trade_outcome: AnalyzeTradeOutcomeSummary,
    factor_diagnostics: FactorDiagnostics,
    pre_bayes_evidence_filter: PreBayesEvidenceFilter,
    pre_bayes_entry_quality_bridge: ict_engine::state::PreBayesEntryQualityBridge,
    canonical_belief_report: ict_engine::reporting::belief::BeliefReportPacket,
    decision_thresholds: DecisionThresholds,
    factor_ranking: Vec<PersistedFactorRanking>,
    factor_iteration_queue: Vec<FactorIterationPrompt>,
    factor_family_decisions: Vec<FactorFamilyDecision>,
    factor_family_outcomes: Vec<FactorFamilyOutcome>,
    factor_family_diffs: Vec<FactorFamilyDiff>,
    factor_family_history: Vec<FactorFamilyHistory>,
    decision_history_summary: DecisionHistorySummary,
    agent_action_plan: AgentActionPlan,
    workflow_state: WorkflowState,
    agent_context_bundle: AgentContextBundle,
    agent_context_bundle_minimal: AgentContextBundleMinimal,
    recommended_commands: CommandRecommendations,
    recommended_next_command: String,
    dataset_comparability: DatasetComparability,
    decision_hint: String,
    artifact_action_summary: Vec<String>,
    artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary,
    artifact_decision_section: ict_engine::state::ArtifactDecisionSection,
    agent_prompts: AgentPromptPack,
    feedback_history_summary: FeedbackHistorySummary,
    multi_timeframe_summary: Vec<String>,
    raw_trade_plan: TradePlan,
    workflow_snapshot: ict_engine::state::WorkflowSnapshot,
    #[serde(skip_serializing_if = "Option::is_none")]
    staged_orchestration_trace: Option<serde_json::Value>,
}

#[derive(Debug, Serialize)]
struct AnalyzeBars {
    htf: usize,
    mtf: usize,
    ltf: usize,
    observations: usize,
}

#[derive(Debug, Serialize)]
struct AnalyzeSections {
    price_action: PriceActionSection,
    technical_price: TechnicalPriceSection,
    smt_correlation: SmtCorrelationSection,
    regime_bayesian: RegimeBayesianSection,
    multi_timeframe: AnalyzeMultiTimeframeSection,
    trade_plan: TradePlanSection,
}

#[derive(Debug, Serialize)]
struct PriceActionSection {
    probability_role: String,
    structure_bias: Direction,
    latest_break: Option<String>,
    recent_break_count: usize,
    swing_highs: usize,
    swing_lows: usize,
    bull_expansion: bool,
    bear_expansion: bool,
    expansion_strength: f64,
    liquidity_sweeps_recent: usize,
    open_fvgs: usize,
    untested_order_blocks: usize,
    bullish_cisd: bool,
    bearish_cisd: bool,
    rejection_block_present: bool,
    narrative: String,
}

#[derive(Debug, Serialize)]
struct RegimeBayesianSection {
    hmm_state: String,
    regime_probs: RegimeProbs,
    regime_label: String,
    liquidity_label: String,
    long_score: f64,
    short_score: f64,
    win_prob_long: f64,
    win_prob_short: f64,
    selected_direction: Direction,
    evidence_policy: String,
    ict_role: String,
}

#[derive(Debug, Serialize)]
struct TradePlanSection {
    probability_role: String,
    actionable: bool,
    direction: Direction,
    entry: f64,
    stop_loss: f64,
    take_profits: Vec<f64>,
    risk_reward: f64,
    posterior: f64,
    win_probability: f64,
    kelly_fraction: f64,
    position_size: f64,
    uncertainties: Vec<String>,
    narrative: String,
}

#[derive(Debug, Serialize)]
struct AnalyzeModelState {
    hmm_state: String,
    log_likelihood: f64,
    viterbi_log_likelihood: f64,
    regime_probs: RegimeProbs,
    evidence_policy: String,
    canonical_belief_engine: String,
    canonical_shadow_status: String,
}

#[derive(Debug, Serialize)]
struct AnalyzeLabels {
    regime_label: String,
    liquidity_label: String,
}

#[derive(Debug, Serialize)]
struct AnalyzeIctSummary {
    total_sweeps: usize,
    total_fvgs: usize,
    mtf_open_fvgs: usize,
    mtf_untested_obs: usize,
    ict_role: String,
}

#[derive(Debug, Serialize)]
struct AnalyzeTradeOutcomeSummary {
    base: BTreeMap<String, f64>,
    long: BTreeMap<String, f64>,
    short: BTreeMap<String, f64>,
}

#[derive(Debug, Serialize)]
struct AnalyzeEntryQualitySummary {
    base: BTreeMap<String, f64>,
    long: BTreeMap<String, f64>,
    short: BTreeMap<String, f64>,
    selected_state: String,
}

#[derive(Debug, Serialize)]
struct BacktestReport {
    symbol: String,
    state_dir: String,
    provenance: RunProvenance,
    decision_thresholds: DecisionThresholds,
    dataset_comparability: DatasetComparability,
    promotion_decision: PromotionDecision,
    rollback_recommendation: RollbackRecommendation,
    bars: usize,
    warmup_bars: usize,
    hold_bars: usize,
    spread_bps: f64,
    slippage_bps: f64,
    fee_bps: f64,
    ambiguous_bar_policy: String,
    window_mode: String,
    evidence_policy: String,
    ict_role: String,
    online_learning: bool,
    learning_updates: usize,
    signals: usize,
    trades: usize,
    metrics: BacktestMetricsSummary,
    equity_curve: Vec<f64>,
    regime_metrics: Vec<BacktestRegimeSummary>,
    factor_ranking: Vec<PersistedFactorRanking>,
    factor_score_deltas: Vec<RankingDiffItem>,
    trade_outcome_deltas: Vec<ProbabilityDiff>,
    factor_iteration_queue: Vec<FactorIterationPrompt>,
    factor_family_decisions: Vec<FactorFamilyDecision>,
    factor_family_outcomes: Vec<FactorFamilyOutcome>,
    factor_family_diffs: Vec<FactorFamilyDiff>,
    factor_family_history: Vec<FactorFamilyHistory>,
    decision_history_summary: DecisionHistorySummary,
    agent_action_plan: AgentActionPlan,
    workflow_state: WorkflowState,
    agent_context_bundle: AgentContextBundle,
    agent_context_bundle_minimal: AgentContextBundleMinimal,
    recommended_commands: CommandRecommendations,
    recommended_next_command: String,
    artifact_action_summary: Vec<String>,
    artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary,
    artifact_decision_section: ict_engine::state::ArtifactDecisionSection,
    agent_prompts: AgentPromptPack,
    feedback_history_summary: FeedbackHistorySummary,
    multi_timeframe_summary: Vec<String>,
    last_decision: Option<ProbabilisticDecisionSnapshot>,
    final_trade_outcome_cpt: BTreeMap<String, BTreeMap<String, f64>>,
    recent_trades: Vec<BacktestTradeSample>,
    workflow_snapshot: ict_engine::state::WorkflowSnapshot,
}

#[derive(Debug, Serialize)]
struct BacktestMetricsSummary {
    total_return: f64,
    sharpe: f64,
    max_drawdown: f64,
    win_rate: f64,
    profit_factor: f64,
    conformal_coverage_1sigma: f64,
    conformal_miscoverage_1sigma: f64,
    mean_prediction_interval_half_width: f64,
    worst_window_miscoverage: f64,
    regime_break_penalty: f64,
    structural_break_score: f64,
    structural_break_index: Option<usize>,
    structural_break_detected: bool,
    signal_structural_break_score: f64,
    signal_structural_break_index: Option<usize>,
    signal_structural_break_detected: bool,
    residual_structural_break_score: f64,
    residual_structural_break_index: Option<usize>,
    residual_structural_break_detected: bool,
    rolling_ic_structural_break_score: f64,
    rolling_ic_structural_break_index: Option<usize>,
    rolling_ic_structural_break_detected: bool,
}

#[derive(Debug, Serialize)]
struct BacktestRegimeSummary {
    regime: Regime,
    win_rate: f64,
    avg_pnl: f64,
}

#[derive(Debug, Serialize)]
struct BacktestTradeSample {
    timestamp: chrono::DateTime<Utc>,
    direction: Direction,
    entry_price: f64,
    exit_price: f64,
    pnl: f64,
    long_score: f64,
    short_score: f64,
    win_prob_long: f64,
    win_prob_short: f64,
    ict_role: String,
}

#[derive(Debug, Serialize)]
struct UpdateReport {
    symbol: String,
    timestamp: chrono::DateTime<Utc>,
    state_dir: String,
    provenance: RunProvenance,
    decision_thresholds: DecisionThresholds,
    dataset_comparability: DatasetComparability,
    promotion_decision: PromotionDecision,
    rollback_recommendation: RollbackRecommendation,
    trade_outcome_deltas: Vec<ProbabilityDiff>,
    factor_score_deltas: Vec<RankingDiffItem>,
    normalized_entry_quality: String,
    factor_alignment: String,
    factor_uncertainty: String,
    realized_outcome: String,
    feedback_records_applied: usize,
    duplicate_feedback_skipped: bool,
    consumed_pending_update_artifact_id: Option<String>,
    consumed_execution_candidate_artifact_id: Option<String>,
    consumed_artifact_path: Option<String>,
    consumed_analyze_run_id: Option<String>,
    consumed_pre_bayes_evidence_filter: Option<PreBayesEvidenceFilter>,
    consumed_pre_bayes_entry_quality_bridge: Option<ict_engine::state::PreBayesEntryQualityBridge>,
    consumed_multi_timeframe_summary: Vec<String>,
    updated_trade_outcome: BTreeMap<String, f64>,
    factor_ranking: Vec<PersistedFactorRanking>,
    factor_iteration_queue: Vec<FactorIterationPrompt>,
    factor_family_decisions: Vec<FactorFamilyDecision>,
    factor_family_outcomes: Vec<FactorFamilyOutcome>,
    factor_family_diffs: Vec<FactorFamilyDiff>,
    factor_family_history: Vec<FactorFamilyHistory>,
    decision_history_summary: DecisionHistorySummary,
    agent_action_plan: AgentActionPlan,
    workflow_state: WorkflowState,
    agent_context_bundle: AgentContextBundle,
    agent_context_bundle_minimal: AgentContextBundleMinimal,
    recommended_commands: CommandRecommendations,
    recommended_next_command: String,
    artifact_action_summary: Vec<String>,
    artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary,
    artifact_decision_section: ict_engine::state::ArtifactDecisionSection,
    agent_prompts: AgentPromptPack,
    feedback_history_summary: FeedbackHistorySummary,
    workflow_snapshot: ict_engine::state::WorkflowSnapshot,
}

#[derive(Clone, Copy)]
struct AnalyzeBuildContext<'a> {
    symbol: &'a str,
    paired_candles: Option<&'a [Candle]>,
    auxiliary: Option<&'a AuxiliaryMarketEvidence>,
    learning_state: &'a LearningState,
    multi_timeframe_summary: &'a [String],
    native_frames: AnalyzeNativeFrames<'a>,
}

#[derive(Debug, Clone, Default)]
struct ConsumedAnalyzeContext {
    analyze_run_id: Option<String>,
    pre_bayes_evidence_filter: Option<PreBayesEvidenceFilter>,
    pre_bayes_entry_quality_bridge: Option<ict_engine::state::PreBayesEntryQualityBridge>,
    multi_timeframe_summary: Vec<String>,
}

#[derive(Clone, Copy, Default)]
struct AnalyzeNativeFrames<'a> {
    d1: Option<&'a [Candle]>,
    h4: Option<&'a [Candle]>,
    h1: Option<&'a [Candle]>,
    m15: Option<&'a [Candle]>,
    m5: Option<&'a [Candle]>,
    m1: Option<&'a [Candle]>,
}

#[derive(Clone)]
struct NativeFrameComputation {
    weight: f64,
    features: FrameFeatures,
    regime_probs: RegimeProbs,
    log_likelihood: f64,
    viterbi_log_likelihood: f64,
}

#[derive(Parser)]
#[command(name = "ict-engine")]
#[command(about = "ICT Expansion Trading Engine", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Analyze market data
    Analyze {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        data_htf: Option<String>,
        #[arg(long)]
        data_mtf: Option<String>,
        #[arg(long)]
        data_ltf: Option<String>,
        #[arg(long)]
        data_root: Option<String>,
        #[arg(long)]
        market: Option<String>,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Analyze live futures with integrated backends and spot/options auxiliary evidence
    AnalyzeLive {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        futures_symbol: Option<String>,
        #[arg(long)]
        spot_symbol: Option<String>,
        #[arg(long)]
        options_symbol: Option<String>,
        #[arg(long)]
        spot_kind: Option<String>,
        #[arg(long, default_value = "openbb")]
        futures_backend: String,
        #[arg(long, default_value = "openbb")]
        aux_backend: String,
        #[arg(long, default_value = "http://127.0.0.1:6901/api/v1")]
        openalice_base_url: String,
        #[arg(long, default_value = "http://127.0.0.1:8080")]
        nofx_base_url: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Train HMM model
    Train {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        data: String,
        #[arg(short, long, default_value = "100")]
        epochs: usize,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Run backtest
    Backtest {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        data: String,
        #[arg(long)]
        paired_data: Option<String>,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long, default_value = "60")]
        warmup_bars: usize,
        #[arg(long, default_value = "10")]
        hold_bars: usize,
        #[arg(long, default_value = "0")]
        spread_bps: f64,
        #[arg(long, default_value = "0")]
        slippage_bps: f64,
        #[arg(long, default_value = "0")]
        fee_bps: f64,
        #[arg(long, default_value = "favor_stop_loss")]
        ambiguous_bar_policy: String,
        #[arg(long, default_value_t = false)]
        online_learn: bool,
    },
    /// Update BBN from realized trade outcome
    Update {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        outcome: String,
        #[arg(long, default_value = "strong_buy")]
        entry_signal: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long)]
        pnl: Option<f64>,
        #[arg(long)]
        regime: Option<String>,
        #[arg(long)]
        direction: Option<String>,
        #[arg(long)]
        feedback_file: Option<String>,
        #[arg(long, default_value_t = false)]
        ensemble: bool,
    },
    /// Run factor research sandbox
    FactorResearch {
        #[arg(long, default_value = "RESEARCH")]
        symbol: String,
        #[arg(long)]
        data: String,
        #[arg(long, default_value = "expansion_manipulation")]
        objective: String,
        #[arg(long)]
        data_1m: Option<String>,
        #[arg(long)]
        data_5m: Option<String>,
        #[arg(long)]
        data_15m: Option<String>,
        #[arg(long)]
        data_1h: Option<String>,
        #[arg(long)]
        data_4h: Option<String>,
        #[arg(long)]
        data_1d: Option<String>,
        #[arg(long)]
        paired_data: Option<String>,
        #[arg(long)]
        mutation_spec: Option<String>,
        #[arg(long, default_value_t = false)]
        emit_mutation_evaluation: bool,
        #[arg(long, default_value_t = false)]
        ensemble: bool,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Show factor mutation history and clustered failure tags
    FactorMutationStatus {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long)]
        source_command: Option<String>,
        #[arg(long, default_value_t = false)]
        latest_only: bool,
        #[arg(long, default_value_t = false)]
        accepted_only: bool,
        #[arg(long, default_value_t = false)]
        bucket_by_source: bool,
        #[arg(long)]
        limit: Option<usize>,
    },
    /// Run factor walk-forward backtest and learning updates
    FactorBacktest {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        data: String,
        #[arg(long)]
        data_1m: Option<String>,
        #[arg(long)]
        data_5m: Option<String>,
        #[arg(long)]
        data_15m: Option<String>,
        #[arg(long)]
        data_1h: Option<String>,
        #[arg(long)]
        data_4h: Option<String>,
        #[arg(long)]
        data_1d: Option<String>,
        #[arg(long)]
        paired_data: Option<String>,
        #[arg(long, default_value_t = false)]
        ensemble: bool,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Clean TOMAC-style futures minute CSVs into continuous candles
    CleanFutures {
        #[arg(long)]
        root: Option<String>,
        #[arg(long)]
        output_dir: String,
        #[arg(long, default_value = "15m")]
        interval: String,
        #[arg(long, default_value_t = false)]
        multi_timeframe: bool,
    },
    /// Standard futures research SOP: clean, research, summarize best factors
    FuturesSop {
        #[arg(long)]
        root: Option<String>,
        #[arg(long)]
        output_dir: String,
        #[arg(long, default_value = "15m")]
        interval: String,
    },
    /// Expansion-focused futures SOP: rank factors by bull/bear expansion discrimination
    ExpansionSop {
        #[arg(long)]
        root: Option<String>,
        #[arg(long)]
        output_dir: String,
        #[arg(long, default_value = "15m")]
        interval: String,
        #[arg(long, default_value_t = 20)]
        lookback: usize,
        #[arg(long, default_value_t = 1.5)]
        atr_multiplier: f64,
        #[arg(long, default_value = "expansion_manipulation")]
        objective: String,
        #[arg(long)]
        mutation_spec: Option<String>,
        #[arg(long, default_value_t = false)]
        emit_mutation_evaluation: bool,
    },
    /// Structured latest-sample trace from factor signal through Pre-Bayes, bridge, and resonance
    FactorPipelineDebug {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        data: String,
        #[arg(long)]
        factor: String,
        #[arg(long, default_value = "expansion_manipulation")]
        objective: String,
        #[arg(long)]
        data_1m: Option<String>,
        #[arg(long)]
        data_5m: Option<String>,
        #[arg(long)]
        data_15m: Option<String>,
        #[arg(long)]
        data_1h: Option<String>,
        #[arg(long)]
        data_4h: Option<String>,
        #[arg(long)]
        data_1d: Option<String>,
    },
    /// Show the latest cross-phase workflow snapshot
    WorkflowStatus {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long, default_value_t = true)]
        refresh: bool,
        #[arg(long)]
        phase: Option<String>,
        #[arg(long, default_value_t = false)]
        actionable_only: bool,
        #[arg(long, default_value_t = false)]
        conflicts_only: bool,
        #[arg(long, default_value_t = false)]
        latest_promotable: bool,
    },
    /// Show the latest Pre-Bayes status directly
    PreBayesStatus {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long, default_value_t = true)]
        refresh: bool,
        #[arg(long)]
        section: Option<String>,
    },
    /// Show the latest Pre-Bayes diff package directly
    PreBayesDiff {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long, default_value_t = true)]
        refresh: bool,
    },
    /// Show artifact lineage edges and related nodes
    ArtifactLineage {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long)]
        artifact_id: Option<String>,
        #[arg(long, default_value_t = false)]
        latest_only: bool,
        #[arg(long, default_value_t = false)]
        improving_only: bool,
        #[arg(long, default_value_t = false)]
        regressing_only: bool,
        #[arg(long, default_value_t = false)]
        rule_break_only: bool,
    },
    /// Show artifact ledger status
    ArtifactStatus {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long)]
        artifact_id: Option<String>,
        #[arg(long)]
        kind: Option<String>,
        #[arg(long, default_value_t = false)]
        latest_only: bool,
        #[arg(long, default_value_t = false)]
        actionable_only: bool,
        #[arg(long, default_value_t = false)]
        rule_break_only: bool,
        #[arg(long, default_value = "generated")]
        sort_by: String,
        #[arg(long, default_value_t = true)]
        descending: bool,
        #[arg(long)]
        limit: Option<usize>,
        #[arg(long)]
        recent_n: Option<usize>,
        #[arg(long, default_value_t = false)]
        consumed_only: bool,
        #[arg(long, default_value_t = false)]
        bucket_by_kind: bool,
        #[arg(long, default_value = "kind")]
        bucket_order_by: String,
        #[arg(long)]
        bucket_limit: Option<usize>,
    },
    /// Diff two artifacts by id
    ArtifactDiff {
        #[arg(long)]
        symbol: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long)]
        left_artifact_id: String,
        #[arg(long)]
        right_artifact_id: String,
    },
}

fn main() -> Result<()> {
    env_logger::init();
    let cli = Cli::parse();

    match cli.command {
        Commands::Analyze {
            symbol,
            data_htf,
            data_mtf,
            data_ltf,
            data_root,
            market,
            state_dir,
        } => {
            let (data_htf, data_mtf, data_ltf) = resolve_analyze_cli_inputs(
                &symbol,
                data_htf.as_deref(),
                data_mtf.as_deref(),
                data_ltf.as_deref(),
                data_root.as_deref(),
                market.as_deref(),
            )?;
            analyze_command(&symbol, &data_htf, &data_mtf, &data_ltf, &state_dir)?
        }
        Commands::AnalyzeLive {
            symbol,
            futures_symbol,
            spot_symbol,
            options_symbol,
            spot_kind,
            futures_backend,
            aux_backend,
            openalice_base_url,
            nofx_base_url,
            state_dir,
        } => analyze_live_command(
            &symbol,
            futures_symbol.as_deref(),
            spot_symbol.as_deref(),
            options_symbol.as_deref(),
            spot_kind.as_deref(),
            &futures_backend,
            &aux_backend,
            &resolve_live_backend_base_url(&futures_backend, &openalice_base_url, &nofx_base_url),
            &resolve_live_backend_base_url(&aux_backend, &openalice_base_url, &nofx_base_url),
            &state_dir,
        )?,
        Commands::Train {
            symbol,
            data,
            epochs,
            state_dir,
        } => train_command(&symbol, &data, epochs, &state_dir)?,
        Commands::Backtest {
            symbol,
            data,
            paired_data,
            state_dir,
            warmup_bars,
            hold_bars,
            spread_bps,
            slippage_bps,
            fee_bps,
            ambiguous_bar_policy,
            online_learn,
        } => backtest_command(
            &symbol,
            &data,
            paired_data.as_deref(),
            &state_dir,
            warmup_bars,
            hold_bars,
            spread_bps,
            slippage_bps,
            fee_bps,
            &ambiguous_bar_policy,
            online_learn,
        )?,
        Commands::Update {
            symbol,
            outcome,
            entry_signal,
            state_dir,
            pnl,
            regime,
            direction,
            feedback_file,
            ensemble,
        } => update_command(
            &symbol,
            &outcome,
            Some(&entry_signal),
            feedback_file.as_deref(),
            &state_dir,
            pnl,
            regime.as_deref(),
            direction.as_deref(),
            ensemble,
        )?,
        Commands::FactorResearch {
            symbol,
            data,
            objective,
            data_1m,
            data_5m,
            data_15m,
            data_1h,
            data_4h,
            data_1d,
            paired_data,
            mutation_spec,
            emit_mutation_evaluation,
            ensemble,
            state_dir,
        } => factor_research_command(
            &symbol,
            &data,
            &objective,
            data_1m.as_deref(),
            data_5m.as_deref(),
            data_15m.as_deref(),
            data_1h.as_deref(),
            data_4h.as_deref(),
            data_1d.as_deref(),
            paired_data.as_deref(),
            mutation_spec.as_deref(),
            emit_mutation_evaluation,
            ensemble,
            &state_dir,
        )?,
        Commands::FactorMutationStatus {
            symbol,
            state_dir,
            source_command,
            latest_only,
            accepted_only,
            bucket_by_source,
            limit,
        } => factor_mutation_status_command(
            &symbol,
            &state_dir,
            source_command.as_deref(),
            latest_only,
            accepted_only,
            bucket_by_source,
            limit,
        )?,
        Commands::FactorBacktest {
            symbol,
            data,
            paired_data,
            ensemble,
            state_dir,
            ..
        } => factor_backtest_command(&symbol, &data, paired_data.as_deref(), ensemble, &state_dir)?,
        Commands::CleanFutures {
            root,
            output_dir,
            interval,
            multi_timeframe,
        } => clean_futures_command(root.as_deref(), &output_dir, &interval, multi_timeframe)?,
        Commands::FuturesSop {
            root,
            output_dir,
            interval,
        } => futures_sop_command(root.as_deref(), &output_dir, &interval)?,
        Commands::ExpansionSop {
            root,
            output_dir,
            interval,
            lookback,
            atr_multiplier,
            objective,
            mutation_spec,
            emit_mutation_evaluation,
        } => expansion_sop_command(
            root.as_deref(),
            &output_dir,
            &interval,
            lookback,
            atr_multiplier,
            &objective,
            mutation_spec.as_deref(),
            emit_mutation_evaluation,
        )?,
        Commands::FactorPipelineDebug {
            symbol,
            data,
            factor,
            objective,
            data_1m,
            data_5m,
            data_15m,
            data_1h,
            data_4h,
            data_1d,
        } => factor_pipeline_debug_command(
            &symbol,
            &data,
            &factor,
            &objective,
            data_1m.as_deref(),
            data_5m.as_deref(),
            data_15m.as_deref(),
            data_1h.as_deref(),
            data_4h.as_deref(),
            data_1d.as_deref(),
        )?,
        Commands::WorkflowStatus {
            symbol,
            state_dir,
            refresh,
            phase,
            actionable_only,
            conflicts_only,
            latest_promotable,
        } => workflow_status_command(
            &symbol,
            &state_dir,
            refresh,
            phase.as_deref(),
            actionable_only,
            conflicts_only,
            latest_promotable,
        )?,
        Commands::PreBayesStatus {
            symbol,
            state_dir,
            refresh,
            section,
        } => pre_bayes_status_command(&symbol, &state_dir, refresh, section.as_deref())?,
        Commands::PreBayesDiff {
            symbol,
            state_dir,
            refresh,
        } => pre_bayes_diff_command(&symbol, &state_dir, refresh)?,
        Commands::ArtifactStatus {
            symbol,
            state_dir,
            artifact_id,
            kind,
            latest_only,
            actionable_only,
            rule_break_only,
            sort_by,
            descending,
            limit,
            recent_n,
            consumed_only,
            bucket_by_kind,
            bucket_order_by,
            bucket_limit,
        } => artifact_status_command(
            &symbol,
            &state_dir,
            artifact_id.as_deref(),
            kind.as_deref(),
            latest_only,
            actionable_only,
            rule_break_only,
            &sort_by,
            descending,
            limit,
            recent_n,
            consumed_only,
            bucket_by_kind,
            &bucket_order_by,
            bucket_limit,
        )?,
        Commands::ArtifactDiff {
            symbol,
            state_dir,
            left_artifact_id,
            right_artifact_id,
        } => artifact_diff_command(&symbol, &state_dir, &left_artifact_id, &right_artifact_id)?,
        Commands::ArtifactLineage {
            symbol,
            state_dir,
            artifact_id,
            latest_only,
            improving_only,
            regressing_only,
            rule_break_only,
        } => artifact_lineage_command(
            &symbol,
            &state_dir,
            artifact_id.as_deref(),
            latest_only,
            improving_only,
            regressing_only,
            rule_break_only,
        )?,
    }

    Ok(())
}

fn analyze_command(
    symbol: &str,
    data_htf: &str,
    data_mtf: &str,
    data_ltf: &str,
    state_dir: &str,
) -> Result<()> {
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;
    let htf = load_candles(data_htf)?;
    let mtf = load_candles(data_mtf)?;
    let ltf = load_candles(data_ltf)?;
    let resolved_multi_timeframe_inputs =
        resolve_analyze_multi_timeframe_inputs(data_htf, data_mtf, data_ltf);
    let d1_owned = resolved_multi_timeframe_inputs
        .get("1d")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let h4_owned = resolved_multi_timeframe_inputs
        .get("4h")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let h1_owned = resolved_multi_timeframe_inputs
        .get("1h")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m15_owned = resolved_multi_timeframe_inputs
        .get("15m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m5_owned = resolved_multi_timeframe_inputs
        .get("5m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let m1_owned = resolved_multi_timeframe_inputs
        .get("1m")
        .filter(|path| *path != data_htf && *path != data_mtf && *path != data_ltf)
        .map(load_candles)
        .transpose()?;
    let multi_timeframe_summary =
        build_multi_timeframe_summary(data_ltf, &resolved_multi_timeframe_inputs)?;
    let multi_timeframe_signal =
        build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?;
    let analyze_multi_timeframe_summary = multi_timeframe_summary
        .iter()
        .cloned()
        .chain(multi_timeframe_signal.summary.iter().cloned())
        .collect::<Vec<_>>();
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let learning_state = load_learning_state(state_dir, symbol)?;
    let report = build_analyze_report(
        symbol,
        state_dir,
        &htf,
        &mtf,
        &ltf,
        &params,
        &network,
        AnalyzeBuildContext {
            symbol,
            paired_candles: None,
            auxiliary: None,
            learning_state: &learning_state,
            multi_timeframe_summary: &analyze_multi_timeframe_summary,
            native_frames: AnalyzeNativeFrames {
                d1: if infer_interval_for_analyze_frame(data_htf, "1d") == "1d" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "1d" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "1d" {
                    Some(&ltf)
                } else {
                    d1_owned.as_deref()
                },
                h4: if infer_interval_for_analyze_frame(data_htf, "1d") == "4h" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "4h" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "4h" {
                    Some(&ltf)
                } else {
                    h4_owned.as_deref()
                },
                h1: if infer_interval_for_analyze_frame(data_htf, "1d") == "1h" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "1h" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "1h" {
                    Some(&ltf)
                } else {
                    h1_owned.as_deref()
                },
                m15: if infer_interval_for_analyze_frame(data_htf, "1d") == "15m" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "15m" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "15m" {
                    Some(&ltf)
                } else {
                    m15_owned.as_deref()
                },
                m5: if infer_interval_for_analyze_frame(data_htf, "1d") == "5m" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "5m" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "5m" {
                    Some(&ltf)
                } else {
                    m5_owned.as_deref()
                },
                m1: if infer_interval_for_analyze_frame(data_htf, "1d") == "1m" {
                    Some(&htf)
                } else if infer_interval_for_analyze_frame(data_mtf, "1h") == "1m" {
                    Some(&mtf)
                } else if infer_interval_for_analyze_frame(data_ltf, "15m") == "1m" {
                    Some(&ltf)
                } else {
                    m1_owned.as_deref()
                },
            },
        },
    )?;
    let mut report = report;
    let pending_update_file =
        persist_pending_update_artifact_from_analyze(state_dir, &report, "analyze")?;
    let _execution_candidate_file =
        persist_execution_candidate_from_analyze(state_dir, &report, "analyze")?;
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    augment_action_plan_with_artifact_trends(
        &mut report.supporting.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.supporting.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.supporting.artifact_decision_summary =
        artifact_decision_summary_for_symbol(state_dir, symbol)?;
    report.supporting.artifact_decision_section = artifact_decision_section_from_parts(
        &report.supporting.artifact_decision_summary,
        &report.supporting.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    apply_command_context_to_analyze_report(
        &mut report,
        &CommandContext {
            symbol: symbol.to_string(),
            state_dir: state_dir.to_string(),
            analyze: Some(AnalyzeCommandSource::Files {
                data_htf: data_htf.to_string(),
                data_mtf: data_mtf.to_string(),
                data_ltf: data_ltf.to_string(),
            }),
            research_data: Some(data_ltf.to_string()),
            paired_data: None,
            update_outcome: None,
            update_entry_signal: None,
            update_feedback_file: Some(pending_update_file),
            user_data_selection_required: true,
        },
    );
    report.supporting.workflow_snapshot = persist_analyze_run(
        state_dir,
        &report,
        "analyze",
        Some(data_htf),
        Some(data_mtf),
        Some(data_ltf),
        None,
    )?;
    report.supporting.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.supporting.workflow_snapshot,
        &report.supporting.artifact_action_summary,
    );
    report.supporting.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.supporting.workflow_snapshot);
    append_artifact_decision_prompt(
        &mut report.supporting.agent_prompts,
        symbol,
        &report.supporting.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.supporting.artifact_decision_summary,
        &mut report.supporting.promotion_decision,
        &mut report.supporting.rollback_recommendation,
    );

    emit_analyze_output(&report)
}

fn build_analyze_policy_outputs(
    report: &AnalyzeReport,
) -> Result<(
    ict_engine::application::belief::BeliefShadowPolicySurface,
    ict_engine::application::belief::BeliefPolicyLineageSurface,
)> {
    let policy_history = load_pre_bayes_policy_history(&report.meta.state_dir, &report.symbol)?;
    let policy_record = policy_history.last().cloned();
    let shadow = build_belief_shadow_policy_surface(
        &report.supporting.canonical_belief_report,
        policy_record.as_ref(),
    );
    let lineage = build_belief_policy_lineage_surface(
        &policy_history,
        report
            .supporting
            .pre_bayes_evidence_filter
            .gating_status
            .as_str(),
    );
    Ok((shadow, lineage))
}

fn format_executor_summary_lines(executor_summaries: &[String]) -> Vec<String> {
    executor_summaries
        .iter()
        .map(|summary| summary.to_string())
        .collect()
}

fn resolved_vote_scorecards<'a>(
    persisted_scorecards: &'a [EnsembleExecutorScorecard],
    vote: &'a EnsembleVoteRecord,
) -> (&'a [EnsembleExecutorScorecard], &'a str) {
    if persisted_scorecards.is_empty() {
        (
            &vote.executor_scorecards,
            vote.executor_scorecards_source
                .as_deref()
                .unwrap_or("fallback"),
        )
    } else {
        (persisted_scorecards, "persisted")
    }
}

fn executor_scorecard_surface<'a>(
    persisted_scorecards: &'a [EnsembleExecutorScorecard],
    fallback_scorecards: &'a [EnsembleExecutorScorecard],
) -> (&'a [EnsembleExecutorScorecard], &'static str) {
    if persisted_scorecards.is_empty() {
        (fallback_scorecards, "fallback")
    } else {
        (persisted_scorecards, "persisted")
    }
}

fn emit_analyze_output(report: &AnalyzeReport) -> Result<()> {
    let compact_report = build_compact_analyze_report(
        report.supporting.decision_hint.clone(),
        &report.supporting.multi_timeframe_summary,
        &report.supporting.artifact_action_summary,
        &[report.supporting.recommended_next_command.clone()],
    );
    let agent_report = build_agent_guidance_report(
        report.supporting.workflow_state.reason.clone(),
        &report.supporting.multi_timeframe_summary,
        &report.supporting.artifact_action_summary,
        &[report.supporting.recommended_next_command.clone()],
        &[],
    );
    let human_market_family = report
        .supporting
        .canonical_belief_report
        .market_family
        .as_deref();
    let human_market_subgraph = report
        .supporting
        .canonical_belief_report
        .selected_market_subgraph
        .as_deref()
        .unwrap_or("unknown");
    let human_report = build_human_analyze_report(
        match human_market_family {
            Some("metals") => format!(
                "金属结构偏向：{}。这类盘先看流动性是否被扫完，再等回到顺势一侧；原始标签={}。",
                if report.analysis.regime_bayesian.selected_direction == Direction::Bull {
                    "偏多，但不宜追"
                } else if report.analysis.regime_bayesian.selected_direction == Direction::Bear {
                    "偏空，但更重确认"
                } else {
                    "先观望，等再定向"
                },
                report.analysis.price_action.narrative
            ),
            Some("energy") => format!(
                "能源结构偏向：{}。这类盘最怕突发冲击，先防假突破和急反转；原始标签={}。",
                if report.analysis.regime_bayesian.selected_direction == Direction::Bear {
                    "空头占优，但随时防剧烈反抽"
                } else if report.analysis.regime_bayesian.selected_direction == Direction::Bull {
                    "多头占优，但别忽视突发回吐"
                } else {
                    "方向未完全站稳，先等波动收敛"
                },
                report.analysis.price_action.narrative
            ),
            _ => report.analysis.price_action.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属技术面：更重均值回归后的二次确认，别把一次拉伸当延续；原始标签={}。",
                report.analysis.technical_price.narrative
            ),
            Some("energy") => format!(
                "能源技术面：指标易被波动放大，先看节奏是否稳定，再看趋势是否继续；原始标签={}。",
                report.analysis.technical_price.narrative
            ),
            _ => report.analysis.technical_price.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属联动面：相关性可参考，但最终仍以本品种流动性反应为主；原始标签={}。",
                report.analysis.smt_correlation.narrative
            ),
            Some("energy") => format!(
                "能源联动面：相关市场常会同步放大波动，若联动发散，先减信号强度；原始标签={}。",
                report.analysis.smt_correlation.narrative
            ),
            _ => report.analysis.smt_correlation.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属品种视角：regime={} liquidity={} direction={:?}。现属防御型流动性环境，先看扫流动性后是否回到顺势确认；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            Some("energy") => format!(
                "能源品种视角：regime={} liquidity={} direction={:?}。当前更该尊重波动冲击与状态切换，先防急拉急杀再谈延续；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            Some("futures_index") => format!(
                "股指品种视角：regime={} liquidity={} direction={:?}。先看 beta 与多周期共振是否同向，再决定是否执行；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            _ => format!(
                "regime={} liquidity={} direction={:?} subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
        },
        report.analysis.trade_plan.narrative.clone(),
    );
    let (belief_shadow_policy, belief_policy_lineage) = build_analyze_policy_outputs(report)?;
    let ensemble_vote = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
        symbol: report.symbol.clone(),
        state_dir: None,
        recommended_next_command: report.supporting.recommended_next_command.clone(),
        provenance: report.supporting.provenance.clone(),
        dataset_comparability: report.supporting.dataset_comparability.clone(),
        belief: report.supporting.canonical_belief_report.clone(),
    });
    let scorecard_summary = format_executor_summary_lines(&ensemble_vote.executor_summaries);
    let persisted_scorecards =
        load_ensemble_executor_scorecards(&report.meta.state_dir, &report.symbol)
            .unwrap_or_default();
    let (_, scorecard_source) = executor_scorecard_surface(&persisted_scorecards, &[]);
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "compact_report": compact_report,
            "agent_report": agent_report,
            "human_report": human_report.render(),
            "market_family_summary": {
                "market_family": report.supporting.canonical_belief_report.market_family,
                "market_behavior_profile": report.supporting.canonical_belief_report.market_behavior_profile,
                "selected_market_subgraph": report.supporting.canonical_belief_report.selected_market_subgraph,
            },
            "belief_shadow_policy": belief_shadow_policy,
            "belief_policy_lineage": belief_policy_lineage,
            "ensemble_vote": ensemble_vote,
            "executor_scorecard_summary": scorecard_summary,
            "executor_scorecard_source": scorecard_source,
        }))?
    );
    Ok(())
}

fn humanize_workflow_command(command: &str) -> String {
    let trimmed = command.trim();
    if trimmed.is_empty() {
        return "No actionable command available.".to_string();
    }
    if let Some(rest) = trimmed.strip_prefix("ask-user: ") {
        let mut parts = rest.split(" | blocked until user_selected_historical_data | then ");
        let ask = parts.next().unwrap_or("").trim();
        let then = parts.next().unwrap_or("").trim();
        if then.is_empty() || then == "choose historical dataset with user before running command" {
            return format!("Ask the user to choose the historical dataset. {}", ask);
        }
        return format!(
            "Ask the user to choose the historical dataset. {} Then run: {}",
            ask, then
        );
    }
    if trimmed.starts_with("blocked:") {
        return format!("Blocked: {}", trimmed.trim_start_matches("blocked:").trim());
    }
    format!("Next step: {}", trimmed)
}

fn workflow_status_human_view(
    snapshot: &ict_engine::state::WorkflowSnapshot,
    persisted_scorecards: &[EnsembleExecutorScorecard],
) -> Value {
    let latest_phase = snapshot
        .latest_update
        .as_ref()
        .or(snapshot.latest_research.as_ref())
        .or(snapshot.latest_analyze.as_ref())
        .or(snapshot.latest_backtest.as_ref())
        .or(snapshot.latest_train.as_ref());
    let latest_phase_label = latest_phase
        .map(|phase| phase.phase.clone())
        .unwrap_or_else(|| "workflow_phase_unavailable".to_string());
    let latest_phase_summary = latest_phase
        .map(|phase| phase.phase_summary.clone())
        .unwrap_or_else(|| "尚无可用阶段摘要。".to_string());
    let selected_data_candidates = if let Some(update) = &snapshot.latest_update {
        let mut candidates = update
            .multi_timeframe_summary
            .iter()
            .filter_map(|line| line.split("path=").nth(1))
            .map(str::trim)
            .filter(|value| !value.is_empty())
            .map(str::to_string)
            .collect::<Vec<_>>();
        candidates.sort();
        candidates.dedup();
        candidates
    } else {
        Vec::new()
    };
    let human_next_action = humanize_workflow_command(&snapshot.recommended_next_command);
    let credibility_risks = snapshot
        .risk_flags
        .iter()
        .filter(|flag| {
            flag.contains("conformal_coverage_low")
                || flag.contains("regime_break_penalty_high")
                || flag.contains("structural_break_detected")
                || flag.contains("conformal_credibility")
        })
        .cloned()
        .collect::<Vec<_>>();
    let ensemble_summary = snapshot.latest_ensemble_vote.as_ref().map(|vote| {
        let (scorecards, scorecard_source) = resolved_vote_scorecards(persisted_scorecards, vote);
        serde_json::json!({
            "final_action": vote.final_action,
            "confidence": vote.confidence,
            "consensus_strength": vote.consensus_strength,
            "human_next_triage": vote.human_next_triage,
            "recommended_command": vote.recommended_command,
            "disagreement_flags": vote.disagreement_flags,
            "executor_scorecards": scorecards,
            "executor_scorecard_source": scorecard_source,
        })
    });
    serde_json::json!({
        "symbol": snapshot.symbol,
        "current_status": {
            "focus_phase": snapshot.current_focus_phase,
            "focus_reason": snapshot.current_focus_reason,
            "blocking_stage": snapshot.blocking_truth.stage,
            "blocking_status": snapshot.blocking_truth.status,
            "blocking_reason": snapshot.blocking_truth.reason,
        },
        "what_you_should_do_now": human_next_action,
        "latest_stage": {
            "phase": latest_phase_label,
            "summary": latest_phase_summary,
        },
        "ensemble_consensus": ensemble_summary,
        "credibility_risks": credibility_risks,
        "pending_actions": snapshot.pending_actions,
        "risk_flags": snapshot.risk_flags,
        "historical_data_candidates": selected_data_candidates,
        "jump_model": snapshot
            .latest_ensemble_vote
            .as_ref()
            .and_then(|vote| {
                vote.executor_summaries
                    .iter()
                    .find(|line| line.contains("jump_model"))
                    .cloned()
            }),
        "jump_disagreement": snapshot
            .latest_ensemble_vote
            .as_ref()
            .and_then(|vote| {
                vote.executor_summaries
                    .iter()
                    .find(|line| line.contains("jump_disagreement"))
                    .cloned()
            }),
    })
}

#[cfg(test)]
fn sample_human_workflow_snapshot() -> ict_engine::state::WorkflowSnapshot {
    let mut snapshot = ict_engine::state::WorkflowSnapshot::default();
    snapshot.symbol = "NQ".to_string();
    snapshot.current_focus_phase = "update".to_string();
    snapshot.current_focus_reason = "waiting_for_user_data_choice".to_string();
    snapshot.blocking_truth = ict_engine::state::WorkflowBlockingTruth {
        stage: "research".to_string(),
        status: "blocked".to_string(),
        reason: "user_selected_historical_data_missing".to_string(),
        evidence: vec!["need user choice".to_string()],
        next_command: "ask-user".to_string(),
    };
    snapshot.recommended_next_command = "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state".to_string();
    snapshot.pending_actions = vec!["research:choose data".to_string()];
    snapshot.risk_flags = vec!["human_gate_active".to_string()];
    snapshot.latest_ensemble_vote = Some(EnsembleVoteRecord {
        artifact_id: "ensemble-vote:update:test".to_string(),
        generated_at: Utc::now(),
        symbol: "NQ".to_string(),
        source_phase: "update".to_string(),
        source_run_id: Some("update:NQ:test".to_string()),
        provenance: RunProvenance::default(),
        dataset_comparability: DatasetComparability::default(),
        ensemble_version: "ensemble-audit-v1".to_string(),
        final_action: "observe".to_string(),
        recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next".to_string(),
        human_next_triage: "ensemble_action=observe consensus=0.500 regime=research command=ict-engine workflow-status --symbol NQ --phase human-next".to_string(),
        confidence: 0.5,
        consensus_strength: 0.5,
        disagreement_flags: Vec::new(),
        executor_summaries: vec![
            "executor=catboost_stub action=observe confidence=0.500".to_string(),
            "jump_model active_state=jump_transition confidence=0.500 transition_risk=0.500"
                .to_string(),
        ],
        split_explanations: vec!["active_regime=research".to_string()],
        executor_scorecards: vec![EnsembleExecutorScorecard {
            executor: "catboost_stub".to_string(),
            latest_weight_hint: Some(0.55),
            ..EnsembleExecutorScorecard::default()
        }],
        executor_scorecards_source: Some("fallback".to_string()),
        posterior_fingerprint: "fp-test".to_string(),
        posterior_normalization_status: "normalized".to_string(),
        posterior_active_regime: "research".to_string(),
        posterior_confidence: Some(0.5),
        posterior_probabilities: BTreeMap::new(),
        posterior_evidence: vec!["mtf=test".to_string()],
    });
    snapshot.latest_update = Some(ict_engine::state::WorkflowPhaseSnapshot {
        phase: "update".to_string(),
        source_command: "update".to_string(),
        run_id: "update:NQ:test".to_string(),
        timestamp: Utc::now(),
        workflow_phase: "research_iteration".to_string(),
        workflow_reason: "waiting_for_data_choice".to_string(),
        promotion_status: "hold".to_string(),
        rollback_scope: "none".to_string(),
        comparable_to_previous: true,
        comparison_class: "same_data_different_config".to_string(),
        recommended_next_command: snapshot.recommended_next_command.clone(),
        phase_summary: "latest update complete".to_string(),
        top_actions: vec!["update:review".to_string()],
        risk_flags: vec!["human_gate_active".to_string()],
        selected_direction: None,
        selected_entry_quality: Some("medium".to_string()),
        pre_bayes_gate_status: "pass_neutralized".to_string(),
        pre_bayes_uses_soft_evidence: true,
        pre_bayes_policy_version: "v1".to_string(),
        pre_bayes_evidence_quality_score: 0.5,
        pre_bayes_conflict_flags: vec![],
        pre_bayes_filtered_assignments: std::collections::BTreeMap::new(),
        pre_bayes_soft_evidence: std::collections::BTreeMap::new(),
        pre_bayes_long_signal_probability: None,
        pre_bayes_short_signal_probability: None,
        pre_bayes_selected_entry_quality_probability: None,
        pre_bayes_bridge_selected_entry_quality: Some("medium".to_string()),
        pre_bayes_bridge_probability_gap: Some(0.01),
        pre_bayes_bridge_rationale_summary: vec![],
        pre_bayes_multi_timeframe_direction_bias: "bullish".to_string(),
        pre_bayes_multi_timeframe_alignment_score: Some(0.8),
        pre_bayes_multi_timeframe_entry_alignment_score: Some(0.8),
        realized_outcome: Some("win".to_string()),
        family_states: vec![],
        factor_actions: vec![],
        multi_timeframe_summary: vec![
            "15m:80 bars path=/tmp/a.json".to_string(),
            "1h:80 bars path=/tmp/b.json".to_string(),
        ],
        family_score_map: std::collections::BTreeMap::new(),
        factor_score_map: std::collections::BTreeMap::new(),
    });
    snapshot
}

fn workflow_status_command(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
    phase: Option<&str>,
    actionable_only: bool,
    conflicts_only: bool,
    latest_promotable: bool,
) -> Result<()> {
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;
    let filter_count = actionable_only as u8 + conflicts_only as u8 + latest_promotable as u8;
    if phase.is_some() && filter_count > 0 {
        bail!("workflow-status phase and filter flags are mutually exclusive");
    }
    if filter_count > 1 {
        bail!("workflow-status accepts at most one filter flag");
    }
    let snapshot = if refresh {
        refresh_workflow_snapshot(state_dir, symbol)?
    } else {
        load_workflow_snapshot(state_dir, symbol)?
    };
    let persisted_scorecards =
        load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    if actionable_only {
        println!(
            "{}",
            serde_json::to_string_pretty(&snapshot.actionable_artifacts)?
        );
        return Ok(());
    }
    if conflicts_only {
        println!("{}", serde_json::to_string_pretty(&snapshot.disagreements)?);
        return Ok(());
    }
    if latest_promotable {
        println!(
            "{}",
            serde_json::to_string_pretty(&snapshot.latest_promotable_artifact)?
        );
        return Ok(());
    }
    if let Some(phase) = phase {
        let value = match phase.trim().to_ascii_lowercase().as_str() {
            "agent-bootstrap" | "bootstrap" => {
                serde_json::to_value(build_agent_bootstrap_view(symbol, state_dir, &snapshot))?
            }
            "human" | "human-next" | "human-next-action" => {
                workflow_status_human_view(&snapshot, &persisted_scorecards)
            }
            "train" => serde_json::to_value(&snapshot.latest_train)?,
            "analyze" => serde_json::to_value(&snapshot.latest_analyze)?,
            "research" => serde_json::to_value(&snapshot.latest_research)?,
            "backtest" => serde_json::to_value(&snapshot.latest_backtest)?,
            "update" => serde_json::to_value(&snapshot.latest_update)?,
            "pre-bayes-policy" => serde_json::to_value(&snapshot.latest_pre_bayes_policy)?,
            "pre-bayes-policy-history" => {
                serde_json::to_value(&snapshot.recent_pre_bayes_policies)?
            }
            "pre-bayes-policy-diff" => {
                serde_json::to_value(&snapshot.latest_pre_bayes_policy_diff)?
            }
            "pre-bayes-policy-lineage" => {
                serde_json::to_value(&snapshot.latest_pre_bayes_policy_lineage)?
            }
            "pre-bayes-entry-quality-bridge" => {
                serde_json::to_value(&snapshot.latest_pre_bayes_entry_quality_bridge)?
            }
            "pre-bayes-entry-quality-bridge-diff" => {
                serde_json::to_value(&snapshot.latest_pre_bayes_entry_quality_bridge_diff)?
            }
            "pre-bayes-soft-evidence" => serde_json::to_value(
                &snapshot
                    .latest_analyze
                    .as_ref()
                    .map(|phase| phase.pre_bayes_soft_evidence.clone()),
            )?,
            "pre-bayes-soft-evidence-diff" => {
                serde_json::to_value(&snapshot.latest_pre_bayes_soft_evidence_diff)?
            }
            "pending-update" => serde_json::to_value(&snapshot.latest_pending_update)?,
            "pending-update-history" => serde_json::to_value(&snapshot.recent_pending_updates)?,
            "execution-candidate" => serde_json::to_value(&snapshot.latest_execution_candidate)?,
            "execution-candidate-history" => {
                serde_json::to_value(&snapshot.recent_execution_candidates)?
            }
            "ensemble-vote" => {
                serde_json::to_value(&snapshot.latest_ensemble_vote.as_ref().map(|vote| {
                    let (scorecards, scorecard_source) =
                        resolved_vote_scorecards(&persisted_scorecards, vote);
                    serde_json::json!({
                        "artifact_id": vote.artifact_id,
                        "generated_at": vote.generated_at,
                        "symbol": vote.symbol,
                        "source_phase": vote.source_phase,
                        "source_run_id": vote.source_run_id,
                        "provenance": vote.provenance,
                        "dataset_comparability": vote.dataset_comparability,
                        "ensemble_version": vote.ensemble_version,
                        "final_action": vote.final_action,
                        "recommended_command": vote.recommended_command,
                        "human_next_triage": vote.human_next_triage,
                        "confidence": vote.confidence,
                        "consensus_strength": vote.consensus_strength,
                        "disagreement_flags": vote.disagreement_flags,
                        "executor_summaries": vote.executor_summaries,
                        "split_explanations": vote.split_explanations,
                        "executor_scorecards": scorecards,
                        "executor_scorecard_source": scorecard_source,
                        "posterior_fingerprint": vote.posterior_fingerprint,
                        "posterior_normalization_status": vote.posterior_normalization_status,
                        "posterior_active_regime": vote.posterior_active_regime,
                        "posterior_confidence": vote.posterior_confidence,
                        "posterior_probabilities": vote.posterior_probabilities,
                        "posterior_evidence": vote.posterior_evidence,
                    })
                }))?
            }
            "ensemble-vote-history" => serde_json::to_value(
                &snapshot
                    .recent_ensemble_votes
                    .iter()
                    .map(|vote| {
                        let (scorecards, scorecard_source) =
                            resolved_vote_scorecards(&persisted_scorecards, vote);
                        serde_json::json!({
                            "artifact_id": vote.artifact_id,
                            "generated_at": vote.generated_at,
                            "symbol": vote.symbol,
                            "source_phase": vote.source_phase,
                            "source_run_id": vote.source_run_id,
                            "provenance": vote.provenance,
                            "dataset_comparability": vote.dataset_comparability,
                            "ensemble_version": vote.ensemble_version,
                            "final_action": vote.final_action,
                            "recommended_command": vote.recommended_command,
                            "human_next_triage": vote.human_next_triage,
                            "confidence": vote.confidence,
                            "consensus_strength": vote.consensus_strength,
                            "disagreement_flags": vote.disagreement_flags,
                            "executor_summaries": vote.executor_summaries,
                            "split_explanations": vote.split_explanations,
                            "executor_scorecards": scorecards,
                            "executor_scorecard_source": scorecard_source,
                            "posterior_fingerprint": vote.posterior_fingerprint,
                            "posterior_normalization_status": vote.posterior_normalization_status,
                            "posterior_active_regime": vote.posterior_active_regime,
                            "posterior_confidence": vote.posterior_confidence,
                            "posterior_probabilities": vote.posterior_probabilities,
                            "posterior_evidence": vote.posterior_evidence,
                        })
                    })
                    .collect::<Vec<_>>(),
            )?,
            "ensemble-scorecards" | "ensemble-executor-scorecards" => {
                serde_json::to_value(&persisted_scorecards)?
            }
            "artifact-history-summary" => serde_json::to_value(&snapshot.artifact_history_summary)?,
            "artifact-factor-trends" => serde_json::to_value(&snapshot.artifact_factor_trends)?,
            "artifact-family-trends" => serde_json::to_value(&snapshot.artifact_family_trends)?,
            "artifact-consumed-gate" => serde_json::to_value(&serde_json::json!({
                "status": snapshot.artifact_decision_summary.consumed_trend_status,
                "reason": snapshot.artifact_decision_summary.consumed_trend_reason,
                "target_kinds": snapshot.artifact_decision_summary.consumed_target_kinds,
                "promotion_strength": snapshot.artifact_decision_summary.promotion_strength,
                "rollback_strength": snapshot.artifact_decision_summary.rollback_strength,
            }))?,
            "artifact-factor-consumed-validation" | "artifact-factor-consumed-leaderboard" => {
                serde_json::to_value(&sorted_artifact_factor_consumed_validation(&snapshot))?
            }
            "artifact-family-consumed-validation" | "artifact-family-consumed-leaderboard" => {
                serde_json::to_value(&sorted_artifact_family_consumed_validation(&snapshot))?
            }
            "artifact-lineage-summaries" => {
                serde_json::to_value(&snapshot.artifact_lineage_summaries)?
            }
            "artifact-decision-summary" => {
                serde_json::to_value(&snapshot.artifact_decision_summary)?
            }
            "artifact-rule-breaks" => serde_json::to_value(
                &snapshot
                    .artifact_lineage_summaries
                    .iter()
                    .filter(|summary| summary.review_rule_break_count > 0)
                    .cloned()
                    .collect::<Vec<_>>(),
            )?,
            "artifact-rule-break-effects" => {
                serde_json::to_value(&snapshot.artifact_rule_break_effects)?
            }
            "artifact-factor-rule-break-impacts" => {
                serde_json::to_value(&snapshot.artifact_factor_rule_break_impacts)?
            }
            "artifact-family-rule-break-impacts" => {
                serde_json::to_value(&snapshot.artifact_family_rule_break_impacts)?
            }
            "artifact-impact-leaderboard" => serde_json::to_value(&serde_json::json!({
                "factor": snapshot.artifact_factor_rule_break_impacts,
                "family": snapshot.artifact_family_rule_break_impacts,
            }))?,
            "artifact-impact-consumed" => serde_json::to_value(&serde_json::json!({
                "factor": snapshot
                    .artifact_factor_rule_break_impacts
                    .iter()
                    .filter(|impact| impact.consumed_breaks > 0)
                    .cloned()
                    .collect::<Vec<_>>(),
                "family": snapshot
                    .artifact_family_rule_break_impacts
                    .iter()
                    .filter(|impact| impact.consumed_breaks > 0)
                    .cloned()
                    .collect::<Vec<_>>(),
            }))?,
            "artifact-impact-consumed-trend" => {
                serde_json::to_value(&snapshot.artifact_consumed_impact_summary)?
            }
            "artifact-review-rules" => serde_json::to_value(&snapshot.artifact_review_rules)?,
            "artifact-review-rule-sources" => {
                serde_json::to_value(&snapshot.artifact_review_rule_sources)?
            }
            "disagreements" => serde_json::to_value(&snapshot.disagreements)?,
            "diffs" => serde_json::to_value(&snapshot.field_diffs)?,
            other => bail!("unsupported workflow-status phase '{}'", other),
        };
        println!("{}", serde_json::to_string_pretty(&value)?);
    } else {
        println!("{}", serde_json::to_string_pretty(&snapshot)?);
    }
    Ok(())
}

fn build_agent_bootstrap_view(
    symbol: &str,
    state_dir: &str,
    snapshot: &WorkflowSnapshot,
) -> AgentBootstrapView {
    let tomac_history_root = detected_tomac_root();
    let multi_timeframe_clean_root =
        detected_multi_timeframe_clean_root(tomac_history_root.as_deref());
    let agent_brief = vec![
        "mission: formalize factor-pipeline debug from latest signal through pre-bayes / bridge / resonance".to_string(),
        "priority: promote expansion_manipulation to SOP-tier objective, not research-only".to_string(),
        "guardrail: do not blind-tune structure_ict before evidence pinpoints the blocking surface".to_string(),
        "success: either find a real structure_ict mutation win or prove near-local-optimum then shift to label refinement / market fork".to_string(),
    ];
    let analyze_command = if let Some(clean_root) = &multi_timeframe_clean_root {
        format!(
            "ict-engine analyze --symbol {} --data-root {} --market {} --state-dir {}",
            shell_quote(symbol),
            shell_quote(clean_root),
            shell_quote(&symbol.to_ascii_lowercase()),
            shell_quote(state_dir)
        )
    } else {
        "ict-engine analyze --symbol <symbol> --data-root <clean-root> --market <market> --state-dir <state-dir>".to_string()
    };
    let train_command = if let Some(clean_root) = &multi_timeframe_clean_root {
        format!(
            "ict-engine train --symbol {} --data {}/cleaned-15m/{}.continuous-15m.json --epochs 200 --state-dir {}",
            shell_quote(symbol),
            shell_quote(clean_root),
            symbol.to_ascii_lowercase(),
            shell_quote(state_dir)
        )
    } else {
        "ict-engine train --symbol <symbol> --data <clean-root>/cleaned-15m/<market>.continuous-15m.json --epochs 200 --state-dir <state-dir>".to_string()
    };
    let clean_command = if let Some(root) = &tomac_history_root {
        format!(
            "ict-engine clean-futures --root {} --output-dir {} --multi-timeframe",
            shell_quote(root),
            shell_quote(
                &multi_timeframe_clean_root
                    .clone()
                    .unwrap_or_else(|| format!("{}/ict-engine-mtf", root))
            )
        )
    } else {
        "ict-engine clean-futures --root <tomac-root> --output-dir <output-dir> --multi-timeframe"
            .to_string()
    };
    let inferable_live_defaults = BTreeMap::from([
        (
            "NQ".to_string(),
            BTreeMap::from([
                ("futures_symbol".to_string(), "NQ=F".to_string()),
                ("spot_symbol".to_string(), "QQQ".to_string()),
                ("options_symbol".to_string(), "QQQ".to_string()),
                ("spot_kind".to_string(), "equity".to_string()),
            ]),
        ),
        (
            "ES".to_string(),
            BTreeMap::from([
                ("futures_symbol".to_string(), "ES=F".to_string()),
                ("spot_symbol".to_string(), "SPY".to_string()),
                ("options_symbol".to_string(), "SPY".to_string()),
                ("spot_kind".to_string(), "equity".to_string()),
            ]),
        ),
        (
            "YM".to_string(),
            BTreeMap::from([
                ("futures_symbol".to_string(), "YM=F".to_string()),
                ("spot_symbol".to_string(), "DIA".to_string()),
                ("options_symbol".to_string(), "DIA".to_string()),
                ("spot_kind".to_string(), "equity".to_string()),
            ]),
        ),
        (
            "GC".to_string(),
            BTreeMap::from([
                ("futures_symbol".to_string(), "GC=F".to_string()),
                ("spot_symbol".to_string(), "GLD".to_string()),
                ("options_symbol".to_string(), "GLD".to_string()),
                ("spot_kind".to_string(), "etf".to_string()),
            ]),
        ),
        (
            "CL".to_string(),
            BTreeMap::from([
                ("futures_symbol".to_string(), "CL=F".to_string()),
                ("spot_symbol".to_string(), "USO".to_string()),
                ("options_symbol".to_string(), "USO".to_string()),
                ("spot_kind".to_string(), "etf".to_string()),
            ]),
        ),
    ]);
    AgentBootstrapView {
        symbol: symbol.to_string(),
        project_role: "closed_loop_multi_timeframe_pre_bayes_bbn_engine".to_string(),
        closed_loop_chain: vec![
            "tomac_history -> clean-futures".to_string(),
            "clean-futures -> train/research/backtest/analyze".to_string(),
            "analyze -> pre-bayes-filter -> bridge -> bbn".to_string(),
            "analyze -> pending/execution artifacts".to_string(),
            "artifacts -> update -> learning feedback".to_string(),
        ],
        agent_brief,
        guardrails: vec![
            "do_not_bypass_pre_bayes_evidence_filter".to_string(),
            "do_not_feed_raw_factor_labels_directly_into_bbn".to_string(),
            "treat_factors_as_evidence_not_triggers".to_string(),
            "keep_six_timeframe_resonance_in_train_analyze_bridge_artifact_update".to_string(),
        ],
        detected_paths: AgentBootstrapPaths {
            tomac_history_root,
            multi_timeframe_clean_root: multi_timeframe_clean_root.clone(),
            state_dir: state_dir.to_string(),
        },
        input_acquisition: AgentBootstrapInputs {
            backtest: AgentBootstrapBacktestInput {
                local_discovery_order: vec![
                    "multi_timeframe_clean_root".to_string(),
                    "tomac_history_root".to_string(),
                    "direct_backtest_file".to_string(),
                ],
                preferred_user_inputs: vec![
                    "multi_timeframe_clean_root".to_string(),
                    "tomac_history_root".to_string(),
                ],
                fallback_user_inputs: vec![
                    "single_backtest_file_path".to_string(),
                    "download_link_to_backtest_file_or_directory".to_string(),
                ],
                should_ask_download_link_if_local_missing: true,
            },
            live: AgentBootstrapLiveInput {
                minimum_required_user_inputs: vec![],
                inferable_defaults: inferable_live_defaults,
                additional_user_inputs_if_not_inferable: vec![
                    "spot_symbol".to_string(),
                    "options_symbol".to_string(),
                    "spot_kind".to_string(),
                    "futures_backend".to_string(),
                    "aux_backend".to_string(),
                    "backend_base_urls_if_non_default".to_string(),
                ],
            },
        },
        commands: AgentBootstrapCommands {
            clean_multi_timeframe: clean_command,
            train: train_command,
            analyze: analyze_command,
            futures_sop: format!(
                "ict-engine futures-sop --root {} --output-dir {} --interval 15m",
                shell_quote(&detected_tomac_root_or_placeholder()),
                shell_quote(
                    &multi_timeframe_clean_root
                        .clone()
                        .unwrap_or_else(|| "<output-dir>".to_string())
                )
            ),
            expansion_sop: format!(
                "ict-engine expansion-sop --root {} --output-dir {} --interval 15m --lookback 20 --atr-multiplier 1.50",
                shell_quote(&detected_tomac_root_or_placeholder()),
                shell_quote(
                    &multi_timeframe_clean_root
                        .clone()
                        .unwrap_or_else(|| "<output-dir>".to_string())
                )
            ),
            workflow_status: format!(
                "ict-engine workflow-status --symbol {} --state-dir {}",
                shell_quote(symbol),
                shell_quote(state_dir)
            ),
            recommended_next_command: snapshot.recommended_next_command.clone(),
        },
        latest_snapshot: AgentBootstrapSnapshot {
            current_focus_phase: snapshot.current_focus_phase.clone(),
            current_focus_reason: snapshot.current_focus_reason.clone(),
            blocking_truth: snapshot.blocking_truth.clone(),
            latest_train_phase: snapshot.latest_train.as_ref().map(|phase| phase.phase.clone()),
            latest_analyze_phase: snapshot
                .latest_analyze
                .as_ref()
                .map(|phase| phase.phase.clone()),
            latest_pre_bayes_gate_status: snapshot
                .latest_analyze
                .as_ref()
                .map(|phase| phase.pre_bayes_gate_status.clone()),
        },
    }
}

fn pre_bayes_status_command(
    symbol: &str,
    state_dir: &str,
    refresh: bool,
    section: Option<&str>,
) -> Result<()> {
    let snapshot = if refresh {
        refresh_workflow_snapshot(state_dir, symbol)?
    } else {
        load_workflow_snapshot(state_dir, symbol)?
    };
    let value = match section.map(|value| value.trim().to_ascii_lowercase()) {
        None => serde_json::to_value(&serde_json::json!({
            "latest_policy": snapshot.latest_pre_bayes_policy,
            "latest_bridge": snapshot.latest_pre_bayes_entry_quality_bridge,
            "latest_bridge_diff": snapshot.latest_pre_bayes_entry_quality_bridge_diff,
            "latest_policy_diff": snapshot.latest_pre_bayes_policy_diff,
            "latest_policy_lineage": snapshot.latest_pre_bayes_policy_lineage,
            "latest_gate_status": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_gate_status.clone()),
            "latest_policy_version": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_policy_version.clone()),
            "latest_uses_soft_evidence": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_uses_soft_evidence),
            "latest_soft_evidence_diff": snapshot.latest_pre_bayes_soft_evidence_diff,
            "latest_soft_evidence": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_soft_evidence.clone()),
        }))?,
        Some(section) if section == "policy" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_policy)?
        }
        Some(section) if section == "bridge" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_entry_quality_bridge)?
        }
        Some(section) if section == "bridge-diff" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_entry_quality_bridge_diff)?
        }
        Some(section) if section == "history" => {
            serde_json::to_value(&snapshot.recent_pre_bayes_policies)?
        }
        Some(section) if section == "diff" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_policy_diff)?
        }
        Some(section) if section == "lineage" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_policy_lineage)?
        }
        Some(section) if section == "gate" => serde_json::to_value(&serde_json::json!({
            "status": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_gate_status.clone()),
            "policy_version": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_policy_version.clone()),
            "uses_soft_evidence": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_uses_soft_evidence),
        }))?,
        Some(section) if section == "soft" || section == "soft-evidence" => serde_json::to_value(
            &snapshot
                .latest_analyze
                .as_ref()
                .map(|phase| phase.pre_bayes_soft_evidence.clone()),
        )?,
        Some(section) if section == "soft-diff" => {
            serde_json::to_value(&snapshot.latest_pre_bayes_soft_evidence_diff)?
        }
        Some(other) => bail!("unsupported pre-bayes-status section '{}'", other),
    };
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

fn pre_bayes_diff_command(symbol: &str, state_dir: &str, refresh: bool) -> Result<()> {
    let snapshot = if refresh {
        refresh_workflow_snapshot(state_dir, symbol)?
    } else {
        load_workflow_snapshot(state_dir, symbol)?
    };
    let value = serde_json::json!({
        "latest_policy_diff": snapshot.latest_pre_bayes_policy_diff,
        "latest_policy_lineage": snapshot.latest_pre_bayes_policy_lineage,
        "latest_gate_status": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_gate_status.clone()),
        "latest_policy_version": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_policy_version.clone()),
        "latest_uses_soft_evidence": snapshot.latest_analyze.as_ref().map(|phase| phase.pre_bayes_uses_soft_evidence),
        "latest_soft_evidence_diff": snapshot.latest_pre_bayes_soft_evidence_diff,
        "latest_bridge": snapshot.latest_pre_bayes_entry_quality_bridge,
        "latest_bridge_diff": snapshot.latest_pre_bayes_entry_quality_bridge_diff,
    });
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

fn multi_timeframe_phase_hint(summary: &[String]) -> String {
    let direction = summary
        .iter()
        .find_map(|item| item.strip_prefix("higher_timeframe_direction_bias="));
    let alignment = summary
        .iter()
        .find_map(|item| item.strip_prefix("higher_timeframe_alignment_score="));
    let entry = summary
        .iter()
        .find_map(|item| item.strip_prefix("lower_timeframe_entry_alignment_score="));
    let covered = summary
        .iter()
        .find_map(|item| item.strip_prefix("multi_timeframe_source="))
        .unwrap_or("primary_only");
    let mut parts = vec![format!("mtf_source={covered}")];
    if let Some(direction) = direction {
        parts.push(format!("mtf_direction={direction}"));
    }
    if let Some(alignment) = alignment {
        parts.push(format!("mtf_alignment={alignment}"));
    }
    if let Some(entry) = entry {
        parts.push(format!("mtf_entry_alignment={entry}"));
    }
    parts.join(" ")
}

#[derive(Debug, Serialize)]
struct ArtifactStatusView {
    symbol: String,
    total_entries: usize,
    entries: Vec<ArtifactLedgerEntry>,
}

#[derive(Debug, Serialize)]
struct ArtifactStatusBucketView {
    symbol: String,
    total_entries: usize,
    buckets: BTreeMap<String, Vec<ArtifactLedgerEntry>>,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapView {
    symbol: String,
    project_role: String,
    closed_loop_chain: Vec<String>,
    agent_brief: Vec<String>,
    guardrails: Vec<String>,
    detected_paths: AgentBootstrapPaths,
    input_acquisition: AgentBootstrapInputs,
    commands: AgentBootstrapCommands,
    latest_snapshot: AgentBootstrapSnapshot,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapPaths {
    tomac_history_root: Option<String>,
    multi_timeframe_clean_root: Option<String>,
    state_dir: String,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapCommands {
    clean_multi_timeframe: String,
    train: String,
    analyze: String,
    futures_sop: String,
    expansion_sop: String,
    workflow_status: String,
    recommended_next_command: String,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapSnapshot {
    current_focus_phase: String,
    current_focus_reason: String,
    blocking_truth: WorkflowBlockingTruth,
    latest_train_phase: Option<String>,
    latest_analyze_phase: Option<String>,
    latest_pre_bayes_gate_status: Option<String>,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapInputs {
    backtest: AgentBootstrapBacktestInput,
    live: AgentBootstrapLiveInput,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapBacktestInput {
    local_discovery_order: Vec<String>,
    preferred_user_inputs: Vec<String>,
    fallback_user_inputs: Vec<String>,
    should_ask_download_link_if_local_missing: bool,
}

#[derive(Debug, Serialize)]
struct AgentBootstrapLiveInput {
    minimum_required_user_inputs: Vec<String>,
    inferable_defaults: BTreeMap<String, BTreeMap<String, String>>,
    additional_user_inputs_if_not_inferable: Vec<String>,
}

#[derive(Debug, Serialize)]
struct FactorMutationFailureCluster {
    tag: String,
    count: usize,
    latest_mutation_id: Option<String>,
    average_score_delta: f64,
}

#[derive(Debug, Clone, Serialize)]
struct FactorMutationSourceSummary {
    source_command: String,
    total_runs: usize,
    accepted_runs: usize,
    latest_mutation_id: Option<String>,
    average_score_delta: f64,
}

#[derive(Debug, Clone, Serialize)]
struct FactorMutationReasonSummary {
    reason: String,
    count: usize,
    markets: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
struct FactorMutationMarketSummary {
    market: String,
    count: usize,
    reasons: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
struct FactorMutationHintEffectivenessSummary {
    hint: String,
    count: usize,
    accepted_runs: usize,
    acceptance_rate: f64,
    average_score_delta: f64,
}

#[derive(Debug, Clone, Serialize)]
struct FactorMutationPerFactorHintSummary {
    base_factor: String,
    direction_hint_effectiveness: Vec<FactorMutationHintEffectivenessSummary>,
    step_size_hint_effectiveness: Vec<FactorMutationHintEffectivenessSummary>,
}

#[derive(Debug, Clone, Default)]
struct MultiTimeframeResearchSignal {
    summary: Vec<String>,
}

fn build_hint_effectiveness_summary(
    hint: &str,
    deltas: &[f64],
    accepted_runs: usize,
) -> FactorMutationHintEffectivenessSummary {
    FactorMutationHintEffectivenessSummary {
        hint: hint.to_string(),
        count: deltas.len(),
        accepted_runs,
        acceptance_rate: if deltas.is_empty() {
            0.0
        } else {
            accepted_runs as f64 / deltas.len() as f64
        },
        average_score_delta: if deltas.is_empty() {
            0.0
        } else {
            deltas.iter().sum::<f64>() / deltas.len() as f64
        },
    }
}

fn compare_hint_effectiveness(
    left: &FactorMutationHintEffectivenessSummary,
    right: &FactorMutationHintEffectivenessSummary,
) -> std::cmp::Ordering {
    left.acceptance_rate
        .partial_cmp(&right.acceptance_rate)
        .unwrap_or(std::cmp::Ordering::Equal)
        .then_with(|| {
            left.average_score_delta
                .partial_cmp(&right.average_score_delta)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .then_with(|| left.count.cmp(&right.count))
}

#[derive(Debug, Serialize)]
struct ArtifactDiffView {
    kind: String,
    left_artifact_id: String,
    right_artifact_id: String,
    changed_fields: Vec<String>,
    numeric_evidence: Vec<String>,
    embedded_pre_bayes_evidence: Vec<String>,
    summary: String,
    cross_rule_version_summary: Option<String>,
    lineage_artifact_ids: Vec<String>,
    lineage_numeric_evidence: Vec<String>,
}

#[derive(Debug, Serialize)]
struct ArtifactLineageEdge {
    from: String,
    to: String,
    relation: String,
}

#[derive(Debug, Serialize)]
struct ArtifactLineageView {
    symbol: String,
    focus_artifact_id: Option<String>,
    nodes: Vec<ArtifactLedgerEntry>,
    edges: Vec<ArtifactLineageEdge>,
}

fn artifact_status_command(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    kind: Option<&str>,
    latest_only: bool,
    actionable_only: bool,
    rule_break_only: bool,
    sort_by: &str,
    descending: bool,
    limit: Option<usize>,
    recent_n: Option<usize>,
    consumed_only: bool,
    bucket_by_kind: bool,
    bucket_order_by: &str,
    bucket_limit: Option<usize>,
) -> Result<()> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    let mut entries = ledger.clone();
    if let Some(artifact_id) = artifact_id {
        entries.retain(|entry| entry.artifact_id == artifact_id);
    }
    if let Some(kind) = kind {
        entries.retain(|entry| entry.artifact_kind == kind);
    }
    if actionable_only {
        entries.retain(|entry| entry.actionable);
    }
    if consumed_only {
        entries.retain(|entry| entry.consumed_by_update_run_id.is_some());
    }
    if rule_break_only {
        entries.retain(|entry| artifact_entry_is_rule_break(&ledger, entry));
    }
    if let Some(recent_n) = recent_n {
        entries.sort_by_key(artifact_generated_recency_key);
        entries.reverse();
        entries.truncate(recent_n);
    }
    if latest_only {
        entries = latest_artifact_entries_by_kind(&entries);
    }
    sort_artifact_entries(&mut entries, sort_by, descending)?;
    if let Some(limit) = limit {
        entries.truncate(limit);
    }
    if bucket_by_kind {
        let mut buckets = BTreeMap::<String, Vec<ArtifactLedgerEntry>>::new();
        for entry in entries {
            buckets
                .entry(entry.artifact_kind.clone())
                .or_default()
                .push(entry);
        }
        let mut bucket_items = buckets.into_iter().collect::<Vec<_>>();
        sort_artifact_buckets(&mut bucket_items, bucket_order_by, descending)?;
        let buckets = bucket_items
            .into_iter()
            .map(|(kind, mut values)| {
                if let Some(limit) = bucket_limit {
                    values.truncate(limit);
                }
                (kind, values)
            })
            .collect::<BTreeMap<_, _>>();
        println!(
            "{}",
            serde_json::to_string_pretty(&ArtifactStatusBucketView {
                symbol: symbol.to_string(),
                total_entries: buckets.values().map(Vec::len).sum(),
                buckets,
            })?
        );
        return Ok(());
    }
    println!(
        "{}",
        serde_json::to_string_pretty(&ArtifactStatusView {
            symbol: symbol.to_string(),
            total_entries: entries.len(),
            entries,
        })?
    );
    Ok(())
}

fn artifact_generated_recency_key(entry: &ArtifactLedgerEntry) -> (i64, usize, String) {
    (
        entry.generated_at.timestamp_millis(),
        entry.version,
        entry.artifact_id.clone(),
    )
}

fn artifact_consumed_recency_key(entry: &ArtifactLedgerEntry) -> (i64, i64, usize, String) {
    (
        entry
            .consumed_at
            .unwrap_or(entry.generated_at)
            .timestamp_millis(),
        entry.generated_at.timestamp_millis(),
        entry.version,
        entry.artifact_id.clone(),
    )
}

fn latest_artifact_entries_by_kind(entries: &[ArtifactLedgerEntry]) -> Vec<ArtifactLedgerEntry> {
    let mut latest = BTreeMap::<String, ArtifactLedgerEntry>::new();
    for entry in entries {
        let should_replace = latest
            .get(&entry.artifact_kind)
            .map(|current| {
                artifact_generated_recency_key(entry) > artifact_generated_recency_key(current)
            })
            .unwrap_or(true);
        if should_replace {
            latest.insert(entry.artifact_kind.clone(), entry.clone());
        }
    }
    latest.into_values().collect()
}

fn artifact_entry_is_rule_break(
    artifact_ledger: &[ArtifactLedgerEntry],
    entry: &ArtifactLedgerEntry,
) -> bool {
    entry
        .supersedes_artifact_id
        .as_deref()
        .and_then(|parent_id| {
            artifact_ledger
                .iter()
                .find(|candidate| candidate.artifact_id == parent_id)
        })
        .map(|parent| parent.review_rule_version != entry.review_rule_version)
        .unwrap_or(false)
}

fn sort_artifact_entries(
    entries: &mut [ArtifactLedgerEntry],
    sort_by: &str,
    descending: bool,
) -> Result<()> {
    match sort_by.trim().to_ascii_lowercase().as_str() {
        "generated" => entries.sort_by_key(|entry| entry.generated_at),
        "quality" => entries.sort_by_key(|entry| entry.quality_score),
        "improvement" => entries.sort_by_key(artifact_improvement_score),
        "regression" => entries.sort_by_key(artifact_regression_score),
        "kind" => entries.sort_by(|a, b| a.artifact_kind.cmp(&b.artifact_kind)),
        "status" => entries.sort_by(|a, b| a.status.cmp(&b.status)),
        "version" => entries.sort_by_key(|entry| entry.version),
        other => bail!("unsupported artifact-status sort '{}'", other),
    }
    if descending {
        entries.reverse();
    }
    Ok(())
}

fn sort_artifact_buckets(
    buckets: &mut [(String, Vec<ArtifactLedgerEntry>)],
    bucket_order_by: &str,
    descending: bool,
) -> Result<()> {
    match bucket_order_by.trim().to_ascii_lowercase().as_str() {
        "kind" => buckets.sort_by(|a, b| a.0.cmp(&b.0)),
        "count" => buckets.sort_by_key(|(_, values)| values.len()),
        "quality" => buckets.sort_by_key(|(_, values)| {
            values
                .iter()
                .map(|entry| entry.quality_score)
                .max()
                .unwrap_or_default()
        }),
        other => bail!("unsupported artifact-status bucket-order-by '{}'", other),
    }
    if descending {
        buckets.reverse();
    }
    Ok(())
}

fn artifact_improvement_score(entry: &ArtifactLedgerEntry) -> i32 {
    entry.quality_score
        + if entry.promote_candidate { 50 } else { 0 }
        + if matches!(
            entry.consumption_regrade_status.as_deref(),
            Some("validated_positive")
        ) {
            25
        } else {
            0
        }
}

fn artifact_regression_score(entry: &ArtifactLedgerEntry) -> i32 {
    let mut score = 0;
    if entry.status == "discard" {
        score += 50;
    }
    if matches!(
        entry.consumption_regrade_status.as_deref(),
        Some("validated_negative")
    ) {
        score += 25;
    }
    score - entry.quality_score
}

fn artifact_diff_command(
    symbol: &str,
    state_dir: &str,
    left_artifact_id: &str,
    right_artifact_id: &str,
) -> Result<()> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    let left_entry = ledger
        .iter()
        .find(|entry| entry.artifact_id == left_artifact_id)
        .ok_or_else(|| anyhow!("unknown artifact id '{}'", left_artifact_id))?;
    let right_entry = ledger
        .iter()
        .find(|entry| entry.artifact_id == right_artifact_id)
        .ok_or_else(|| anyhow!("unknown artifact id '{}'", right_artifact_id))?;
    if left_entry.artifact_kind != right_entry.artifact_kind {
        bail!(
            "artifact kinds differ: '{}' vs '{}'",
            left_entry.artifact_kind,
            right_entry.artifact_kind
        );
    }

    let view = match left_entry.artifact_kind.as_str() {
        "pending_update" => artifact_diff_view_for_pending_update(
            &ledger,
            state_dir,
            symbol,
            left_artifact_id,
            right_artifact_id,
        )?,
        "execution_candidate" => artifact_diff_view_for_execution_candidate(
            &ledger,
            state_dir,
            symbol,
            left_artifact_id,
            right_artifact_id,
        )?,
        other => bail!("artifact-diff not supported for artifact kind '{}'", other),
    };
    println!("{}", serde_json::to_string_pretty(&view)?);
    Ok(())
}

fn artifact_lineage_command(
    symbol: &str,
    state_dir: &str,
    artifact_id: Option<&str>,
    latest_only: bool,
    improving_only: bool,
    regressing_only: bool,
    rule_break_only: bool,
) -> Result<()> {
    let filter_count = improving_only as u8 + regressing_only as u8 + rule_break_only as u8;
    if filter_count > 1 {
        bail!(
            "artifact-lineage accepts at most one of --improving-only/--regressing-only/--rule-break-only"
        );
    }
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    let snapshot = refresh_workflow_snapshot(state_dir, symbol)?;
    let focus_artifact_id = if let Some(artifact_id) = artifact_id {
        Some(artifact_id.to_string())
    } else if latest_only {
        ledger
            .iter()
            .max_by_key(|entry| artifact_generated_recency_key(entry))
            .map(|entry| entry.artifact_id.clone())
    } else {
        None
    };

    if focus_artifact_id.is_none() {
        let summaries = snapshot
            .artifact_lineage_summaries
            .into_iter()
            .filter(|summary| {
                (!improving_only || summary.conclusion == "improving")
                    && (!regressing_only || summary.conclusion == "deteriorating")
                    && (!rule_break_only || summary.review_rule_break_count > 0)
            })
            .collect::<Vec<_>>();
        println!("{}", serde_json::to_string_pretty(&summaries)?);
        return Ok(());
    }

    let nodes = if let Some(focus) = focus_artifact_id.as_deref() {
        let mut related = BTreeMap::<String, ArtifactLedgerEntry>::new();
        for entry in &ledger {
            if entry.artifact_id == focus
                || entry.supersedes_artifact_id.as_deref() == Some(focus)
                || entry.artifact_id
                    == ledger
                        .iter()
                        .find(|candidate| candidate.artifact_id == focus)
                        .and_then(|candidate| candidate.supersedes_artifact_id.clone())
                        .unwrap_or_default()
            {
                related.insert(entry.artifact_id.clone(), entry.clone());
            }
        }
        related.into_values().collect()
    } else {
        ledger.clone()
    };

    let edges = nodes
        .iter()
        .flat_map(|entry| {
            let mut edges = Vec::new();
            if let Some(previous) = &entry.supersedes_artifact_id {
                edges.push(ArtifactLineageEdge {
                    from: previous.clone(),
                    to: entry.artifact_id.clone(),
                    relation: "supersedes".to_string(),
                });
            }
            if let Some(update_run_id) = &entry.consumed_by_update_run_id {
                edges.push(ArtifactLineageEdge {
                    from: entry.artifact_id.clone(),
                    to: update_run_id.clone(),
                    relation: "consumed_by_update".to_string(),
                });
            }
            edges
        })
        .collect::<Vec<_>>();

    println!(
        "{}",
        serde_json::to_string_pretty(&ArtifactLineageView {
            symbol: symbol.to_string(),
            focus_artifact_id,
            nodes,
            edges,
        })?
    );
    Ok(())
}

#[derive(Debug, Serialize)]
struct PersistedCandlesFile {
    candles: Vec<Candle>,
}

#[derive(Debug, Serialize)]
struct CleanedCandleOutput {
    symbol: String,
    candles: Vec<Candle>,
}

#[derive(Debug, Clone, Serialize)]
struct CleanFuturesReport {
    root: String,
    output_dir: String,
    interval: String,
    datasets: Vec<CleanFuturesDatasetReport>,
}

#[derive(Debug, Clone, Serialize)]
struct MultiTimeframeCleanFuturesReport {
    root: String,
    output_dir: String,
    intervals: Vec<String>,
    reports: Vec<CleanFuturesReport>,
}

#[derive(Debug, Clone, Serialize)]
struct CleanFuturesDatasetReport {
    market: String,
    source_path: String,
    symbology_path: String,
    output_path: String,
    summary: CleanedContinuousFuturesSummary,
}

impl MultiTimeframeCleanReportView for MultiTimeframeCleanFuturesReport {
    fn interval_dataset_output_pairs<'a>(
        &'a self,
        market: &'a str,
    ) -> Box<dyn Iterator<Item = (&'a str, &'a str)> + 'a> {
        Box::new(self.reports.iter().filter_map(move |report| {
            report
                .datasets
                .iter()
                .find(|dataset| dataset.market == market)
                .map(|dataset| (report.interval.as_str(), dataset.output_path.as_str()))
        }))
    }
}

#[derive(Debug, Serialize)]
struct FuturesSopReport {
    sop_version: String,
    generated_at: chrono::DateTime<Utc>,
    root: String,
    output_dir: String,
    cleaned_dir: String,
    state_dir: String,
    interval: String,
    selection_policy: String,
    clean_report: CleanFuturesReport,
    market_reports: Vec<FuturesSopMarketReport>,
    global_factor_leaderboard: Vec<FuturesSopFactorLeaderboardEntry>,
    recommended_global_factor: Option<String>,
    recommended_global_pre_bayes_policy: Option<ict_engine::state::PreBayesEvidencePolicy>,
    recommended_global_pre_bayes_entry_quality_bridge:
        Option<ict_engine::state::PreBayesEntryQualityBridge>,
    recommended_global_pre_bayes_summary: Vec<String>,
    recommended_global_pre_bayes_policy_lineage:
        Option<ict_engine::state::PreBayesPolicyLineageSummary>,
    recommended_global_pre_bayes_soft_evidence_diff:
        Vec<ict_engine::state::PreBayesSoftEvidenceNodeDiff>,
    #[serde(skip_serializing_if = "Option::is_none")]
    recommended_global_pipeline_debug: Option<FactorPipelineDebugReport>,
    recommended_market_factors: BTreeMap<String, String>,
    warnings: Vec<String>,
    recommended_commands: Vec<String>,
}

#[derive(Debug, Serialize)]
struct FuturesSopMarketReport {
    market: String,
    cleaned_path: String,
    candle_count: usize,
    multi_timeframe_summary: Vec<String>,
    best_factor: Option<String>,
    promotion_status: String,
    rollback_scope: String,
    workflow_phase: String,
    artifact_gate_status: String,
    recommended_next_command: String,
    aggregate_return: f64,
    aggregate_return_warning: Option<String>,
    top_scorecards: Vec<FuturesSopScorecard>,
    pipeline: Option<ExpansionFactorPipelineReport>,
}

#[derive(Debug, Clone, Serialize)]
struct FuturesSopScorecard {
    factor_name: String,
    composite_score: f64,
    grade: String,
    iteration_action: String,
}

#[derive(Debug, Serialize)]
struct FuturesSopFactorLeaderboardEntry {
    factor_name: String,
    markets_seen: usize,
    first_place_markets: usize,
    average_composite_score: f64,
    best_composite_score: f64,
}

#[derive(Debug, Serialize)]
struct ExpansionSopReport {
    sop_version: String,
    generated_at: chrono::DateTime<Utc>,
    root: String,
    output_dir: String,
    cleaned_dir: String,
    interval: String,
    expansion_lookback: usize,
    expansion_atr_multiplier: f64,
    clean_report: CleanFuturesReport,
    market_reports: Vec<ExpansionMarketReport>,
    global_factor_leaderboard: Vec<ExpansionFactorLeaderboardEntry>,
    recommended_global_factor: Option<String>,
    recommended_global_pre_bayes_policy: Option<ict_engine::state::PreBayesEvidencePolicy>,
    recommended_global_pre_bayes_entry_quality_bridge:
        Option<ict_engine::state::PreBayesEntryQualityBridge>,
    recommended_global_pre_bayes_summary: Vec<String>,
    recommended_global_pre_bayes_policy_lineage:
        Option<ict_engine::state::PreBayesPolicyLineageSummary>,
    recommended_global_pre_bayes_soft_evidence_diff:
        Vec<ict_engine::state::PreBayesSoftEvidenceNodeDiff>,
    #[serde(skip_serializing_if = "Option::is_none")]
    recommended_global_pipeline_debug: Option<FactorPipelineDebugReport>,
    recommended_market_factors: BTreeMap<String, String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    mutation_spec: Option<FactorMutationSpec>,
    #[serde(skip_serializing_if = "Option::is_none")]
    factor_mutation_evaluation: Option<FactorMutationEvaluation>,
    warnings: Vec<String>,
    recommended_commands: Vec<String>,
}

#[derive(Debug, Serialize)]
struct ExpansionMarketReport {
    market: String,
    cleaned_path: String,
    total_candles: usize,
    expansion_samples: usize,
    bull_expansion_samples: usize,
    bear_expansion_samples: usize,
    best_factor: Option<String>,
    top_factors: Vec<ExpansionFactorScore>,
    multi_timeframe_summary: Vec<String>,
    pipeline: Option<ExpansionFactorPipelineReport>,
}

#[derive(Debug, Clone, Serialize)]
struct ExpansionFactorScore {
    factor_name: String,
    expansion_samples: usize,
    bull_expansion_samples: usize,
    bear_expansion_samples: usize,
    bull_hit_rate: f64,
    bear_hit_rate: f64,
    balanced_accuracy: f64,
    directional_accuracy: f64,
    confidence_weighted_accuracy: f64,
    mean_confidence: f64,
    neutral_predictions: usize,
    wrong_direction_predictions: usize,
    fit_score: f64,
}

#[derive(Debug, Serialize)]
struct ExpansionFactorLeaderboardEntry {
    factor_name: String,
    markets_seen: usize,
    first_place_markets: usize,
    average_fit_score: f64,
    average_balanced_accuracy: f64,
    average_directional_accuracy: f64,
}

fn factor_pipeline_debug_command(
    symbol: &str,
    data: &str,
    factor: &str,
    objective: &str,
    data_1m: Option<&str>,
    data_5m: Option<&str>,
    data_15m: Option<&str>,
    data_1h: Option<&str>,
    data_4h: Option<&str>,
    data_1d: Option<&str>,
) -> Result<()> {
    let objective_mode = parse_research_objective(objective)?;
    let resolved_multi_timeframe_inputs =
        resolve_multi_timeframe_inputs(data, data_1m, data_5m, data_15m, data_1h, data_4h, data_1d);
    let multi_timeframe_summary =
        build_multi_timeframe_summary(data, &resolved_multi_timeframe_inputs)?
            .into_iter()
            .chain(
                build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?
                    .summary
                    .into_iter(),
            )
            .collect::<Vec<_>>();
    let candles = load_candles(data)?;
    let registry = FactorRegistry::default();
    let pipeline = build_expansion_factor_pipeline_report_with_registry_v2(
        symbol,
        factor,
        &candles,
        &multi_timeframe_summary,
        &registry,
    )?;
    let report = build_factor_pipeline_debug_report_v2(
        symbol,
        data,
        research_objective_label(objective_mode),
        &pipeline.factor_name,
        DebugExpansionLatestSignal {
            timestamp: pipeline.latest_signal.timestamp,
            direction: pipeline.latest_signal.direction.clone(),
            value: pipeline.latest_signal.value,
            confidence: pipeline.latest_signal.confidence,
            explanation: pipeline.latest_signal.explanation.clone(),
        },
        DebugExpansionProbabilitySupport {
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
        DebugExpansionBbnSupport {
            market_regime_label: pipeline.bbn_support.market_regime_label.clone(),
            liquidity_context_label: pipeline.bbn_support.liquidity_context_label.clone(),
            evidence_policy: pipeline.bbn_support.evidence_policy.clone(),
            pre_bayes_filter: pipeline.bbn_support.pre_bayes_filter.clone(),
            evidence_assignments: pipeline.bbn_support.evidence_assignments.clone(),
            raw_market_regime_trace: ict_engine::state::FactorPipelineLabelSource {
                label: pipeline.bbn_support.raw_market_regime_trace.label.clone(),
                derivation: pipeline
                    .bbn_support
                    .raw_market_regime_trace
                    .derivation
                    .clone(),
                evidence: pipeline
                    .bbn_support
                    .raw_market_regime_trace
                    .evidence
                    .clone(),
            },
            raw_liquidity_context_trace: ict_engine::state::FactorPipelineLabelSource {
                label: pipeline
                    .bbn_support
                    .raw_liquidity_context_trace
                    .label
                    .clone(),
                derivation: pipeline
                    .bbn_support
                    .raw_liquidity_context_trace
                    .derivation
                    .clone(),
                evidence: pipeline
                    .bbn_support
                    .raw_liquidity_context_trace
                    .evidence
                    .clone(),
            },
            raw_multi_timeframe_resonance_trace: ict_engine::state::FactorPipelineLabelSource {
                label: pipeline
                    .bbn_support
                    .raw_multi_timeframe_resonance_trace
                    .label
                    .clone(),
                derivation: pipeline
                    .bbn_support
                    .raw_multi_timeframe_resonance_trace
                    .derivation
                    .clone(),
                evidence: pipeline
                    .bbn_support
                    .raw_multi_timeframe_resonance_trace
                    .evidence
                    .clone(),
            },
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
        &multi_timeframe_summary,
        BTreeMap::from([
            (
                "market_regime".to_string(),
                pipeline.bbn_support.market_regime_label.clone(),
            ),
            (
                "liquidity_context".to_string(),
                pipeline.bbn_support.liquidity_context_label.clone(),
            ),
            (
                "factor_alignment".to_string(),
                pipeline.probability_support.alignment_label.clone(),
            ),
            (
                "factor_uncertainty".to_string(),
                pipeline.probability_support.uncertainty_label.clone(),
            ),
            (
                "multi_timeframe_resonance".to_string(),
                pipeline
                    .bbn_support
                    .pre_bayes_filter
                    .raw_multi_timeframe_resonance_label
                    .clone(),
            ),
        ]),
        pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter),
        env_f64("ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD", 0.12),
    )?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn persist_candle_snapshot(
    state_dir: &str,
    symbol: &str,
    filename: &str,
    candles: &[Candle],
) -> Result<String> {
    let path = std::path::Path::new(state_dir)
        .join(symbol)
        .join(filename)
        .to_string_lossy()
        .to_string();
    save_state(
        state_dir,
        symbol,
        filename,
        &PersistedCandlesFile {
            candles: candles.to_vec(),
        },
    )?;
    Ok(path)
}

fn clean_futures_command(
    root: Option<&str>,
    output_dir: &str,
    interval: &str,
    multi_timeframe: bool,
) -> Result<()> {
    let root = resolve_tomac_root(root)?;
    if multi_timeframe {
        let report = run_clean_futures_multi_timeframe(&root, output_dir)?;
        println!("{}", serde_json::to_string_pretty(&report)?);
    } else {
        let report = run_clean_futures(&root, output_dir, interval)?;
        println!("{}", serde_json::to_string_pretty(&report)?);
    }
    Ok(())
}

fn run_clean_futures_multi_timeframe(
    root: &str,
    output_dir: &str,
) -> Result<MultiTimeframeCleanFuturesReport> {
    let intervals = MULTI_TIMEFRAME_INTERVALS
        .iter()
        .map(|interval| (*interval).to_string())
        .collect::<Vec<_>>();
    std::fs::create_dir_all(output_dir)?;
    let mut reports = Vec::new();
    for interval in &intervals {
        let interval_output_dir = std::path::Path::new(output_dir)
            .join(format!("cleaned-{}", interval))
            .to_string_lossy()
            .to_string();
        reports.push(run_clean_futures(root, &interval_output_dir, interval)?);
    }
    let manifest_path = std::path::Path::new(output_dir)
        .join("cleaned-multi-timeframe-manifest.json")
        .to_string_lossy()
        .to_string();
    let report = MultiTimeframeCleanFuturesReport {
        root: root.to_string(),
        output_dir: output_dir.to_string(),
        intervals,
        reports,
    };
    std::fs::write(&manifest_path, serde_json::to_string_pretty(&report)?)?;
    Ok(report)
}

fn run_clean_futures(root: &str, output_dir: &str, interval: &str) -> Result<CleanFuturesReport> {
    let interval_minutes = parse_interval_minutes(interval)?;
    std::fs::create_dir_all(output_dir)?;
    let datasets = discover_tomac_futures_datasets(root)?;
    if datasets.is_empty() {
        bail!("no TOMAC futures datasets found under '{}'", root);
    }

    let mut reports = Vec::new();
    for (ohlcv_path, symbology_path) in datasets {
        let market = infer_market_code_from_path(&ohlcv_path);
        let (continuous, mut summary) =
            load_tomac_continuous_candles(&ohlcv_path, &symbology_path)?;
        let cleaned = aggregate_candles_by_minutes(&continuous, interval_minutes)?;
        summary.matched_front_rows = continuous.len();
        summary.continuous_candles = continuous.len();
        summary.aggregated_candles = cleaned.len();

        let output_path = std::path::Path::new(output_dir)
            .join(format!(
                "{}.continuous-{}.json",
                market.to_ascii_lowercase(),
                interval
            ))
            .to_string_lossy()
            .to_string();
        std::fs::write(
            &output_path,
            serde_json::to_string_pretty(&CleanedCandleOutput {
                symbol: market.clone(),
                candles: cleaned,
            })?,
        )?;
        reports.push(CleanFuturesDatasetReport {
            market,
            source_path: ohlcv_path,
            symbology_path,
            output_path,
            summary,
        });
    }

    reports.sort_by(|a, b| a.market.cmp(&b.market));
    Ok(CleanFuturesReport {
        root: root.to_string(),
        output_dir: output_dir.to_string(),
        interval: interval.to_string(),
        datasets: reports,
    })
}

fn discover_tomac_futures_datasets(root: &str) -> Result<Vec<(String, String)>> {
    let mut stack = vec![std::path::PathBuf::from(root)];
    let mut datasets = Vec::new();

    while let Some(path) = stack.pop() {
        if path.is_dir() {
            for entry in std::fs::read_dir(&path)
                .with_context(|| format!("failed to read directory '{}'", path.display()))?
            {
                let entry = entry?;
                stack.push(entry.path());
            }
            continue;
        }
        let Some(name) = path.file_name().and_then(|value| value.to_str()) else {
            continue;
        };
        if !name.ends_with(".ohlcv-1m.csv") {
            continue;
        }
        let Some(parent) = path.parent() else {
            continue;
        };
        let symbology = parent.join("symbology.csv");
        if symbology.exists() {
            datasets.push((
                path.to_string_lossy().to_string(),
                symbology.to_string_lossy().to_string(),
            ));
        }
    }

    datasets.sort();
    Ok(datasets)
}

fn infer_market_code_from_path(path: &str) -> String {
    let parent = std::path::Path::new(path)
        .parent()
        .and_then(|value| value.file_name())
        .and_then(|value| value.to_str())
        .unwrap_or("market");
    parent
        .split_whitespace()
        .next()
        .unwrap_or(parent)
        .to_ascii_uppercase()
}

fn parse_interval_minutes(interval: &str) -> Result<i64> {
    let normalized = interval.trim().to_ascii_lowercase();
    match normalized.as_str() {
        "1m" => Ok(1),
        "5m" => Ok(5),
        "15m" => Ok(15),
        "30m" => Ok(30),
        "1h" => Ok(60),
        "4h" => Ok(240),
        "1d" => Ok(1440),
        _ => bail!("unsupported interval '{}'", interval),
    }
}

fn futures_sop_command(root: Option<&str>, output_dir: &str, interval: &str) -> Result<()> {
    let root = resolve_tomac_root(root)?;
    let report = run_futures_sop(&root, output_dir, interval)?;
    let report_path = std::path::Path::new(output_dir)
        .join(format!("futures_sop_report.{}.json", interval))
        .to_string_lossy()
        .to_string();
    std::fs::write(&report_path, serde_json::to_string_pretty(&report)?)?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn run_futures_sop(root: &str, output_dir: &str, interval: &str) -> Result<FuturesSopReport> {
    let objective_mode = ResearchObjectiveMode::Generic;
    let cleaned_dir = std::path::Path::new(output_dir)
        .join(format!("cleaned-{}", interval))
        .to_string_lossy()
        .to_string();
    let state_dir = std::path::Path::new(output_dir)
        .join("state")
        .to_string_lossy()
        .to_string();
    std::fs::create_dir_all(&state_dir)?;

    let multi_timeframe_clean_report = run_clean_futures_multi_timeframe(root, output_dir)?;
    let clean_report = multi_timeframe_clean_report
        .reports
        .iter()
        .find(|report| report.interval == interval)
        .cloned()
        .ok_or_else(|| anyhow!("missing cleaned report for interval '{}'", interval))?;
    let mut market_reports = Vec::new();
    let mut factor_scores = BTreeMap::<String, Vec<f64>>::new();
    let mut factor_first_places = BTreeMap::<String, usize>::new();
    let mut warnings = Vec::new();
    let mut recommended_market_factors = BTreeMap::<String, String>::new();

    for dataset in &clean_report.datasets {
        let multi_timeframe_inputs = resolved_multi_timeframe_inputs_for_market(
            &multi_timeframe_clean_report,
            &dataset.market,
        );
        let report = run_factor_research(
            &dataset.market,
            &dataset.output_path,
            objective_mode,
            multi_timeframe_inputs.get("1m"),
            multi_timeframe_inputs.get("5m"),
            multi_timeframe_inputs.get("15m"),
            multi_timeframe_inputs.get("1h"),
            multi_timeframe_inputs.get("4h"),
            multi_timeframe_inputs.get("1d"),
            None,
            None,
            &state_dir,
        )?;
        let top_scorecards = report
            .backtest
            .scorecards
            .iter()
            .map(|item| FuturesSopScorecard {
                factor_name: item.factor_name.clone(),
                composite_score: item.composite_score,
                grade: item.grade.clone(),
                iteration_action: item.iteration_action.clone(),
            })
            .take(5)
            .collect::<Vec<_>>();
        for scorecard in &report.backtest.scorecards {
            factor_scores
                .entry(scorecard.factor_name.clone())
                .or_default()
                .push(scorecard.composite_score);
        }
        if let Some(best_factor) = &report.best_factor {
            *factor_first_places.entry(best_factor.clone()).or_default() += 1;
            recommended_market_factors.insert(dataset.market.clone(), best_factor.clone());
        }
        let aggregate_return_warning =
            suspicious_aggregate_return(report.aggregate_return).then(|| {
                format!(
                "aggregate_return={} looks unstable; prefer composite_score for factor selection",
                report.aggregate_return
            )
            });
        if let Some(warning) = &aggregate_return_warning {
            warnings.push(format!("{}:{}", dataset.market, warning));
        }
        let candles = load_candles(&dataset.output_path)?;
        let pipeline = report
            .best_factor
            .as_deref()
            .map(|factor| {
                build_expansion_factor_pipeline_report_v2(
                    &dataset.market,
                    factor,
                    &candles,
                    &report.multi_timeframe_summary,
                )
            })
            .transpose()?;
        market_reports.push(FuturesSopMarketReport {
            market: dataset.market.clone(),
            cleaned_path: dataset.output_path.clone(),
            candle_count: dataset.summary.aggregated_candles,
            multi_timeframe_summary: report.multi_timeframe_summary.clone(),
            best_factor: report.best_factor.clone(),
            promotion_status: report.promotion_decision.status.clone(),
            rollback_scope: report.rollback_recommendation.scope.clone(),
            workflow_phase: report.workflow_state.phase.clone(),
            artifact_gate_status: report
                .artifact_decision_summary
                .consumed_trend_status
                .clone(),
            recommended_next_command: report.recommended_next_command.clone(),
            aggregate_return: report.aggregate_return,
            aggregate_return_warning,
            top_scorecards,
            pipeline,
        });
    }

    market_reports.sort_by(|a, b| a.market.cmp(&b.market));
    let mut global_factor_leaderboard = factor_scores
        .into_iter()
        .map(|(factor_name, scores)| FuturesSopFactorLeaderboardEntry {
            first_place_markets: factor_first_places.get(&factor_name).copied().unwrap_or(0),
            markets_seen: scores.len(),
            average_composite_score: scores.iter().sum::<f64>() / scores.len() as f64,
            best_composite_score: scores.iter().copied().fold(f64::MIN, f64::max),
            factor_name,
        })
        .collect::<Vec<_>>();
    global_factor_leaderboard.sort_by(|a, b| {
        b.first_place_markets
            .cmp(&a.first_place_markets)
            .then_with(|| {
                b.average_composite_score
                    .partial_cmp(&a.average_composite_score)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    let recommended_global_factor = global_factor_leaderboard
        .first()
        .map(|entry| entry.factor_name.clone());
    let recommended_global_pre_bayes_policy = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.policy.clone())
        });
    let recommended_global_pre_bayes_entry_quality_bridge = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.entry_quality_bridge.clone())
        });
    let recommended_global_pre_bayes_summary = {
        pre_bayes_report_summary(
            recommended_global_pre_bayes_policy.as_ref(),
            recommended_global_pre_bayes_entry_quality_bridge.as_ref(),
        )
    };
    let recommended_global_pre_bayes_policy_lineage = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            let history = load_pre_bayes_policy_history(&state_dir, &market.market).ok()?;
            let gate_status = market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.as_str())
                .unwrap_or("");
            Some(pre_bayes_policy_lineage_summary(&history, gate_status))
        });
    let recommended_global_pre_bayes_soft_evidence_diff = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| market.pipeline.as_ref())
        .map(|pipeline| pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter))
        .unwrap_or_default();
    let recommended_global_pipeline_debug = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market.pipeline.as_ref().and_then(|pipeline| {
                build_factor_pipeline_debug_report_v2(
                    &market.market,
                    &market.cleaned_path,
                    research_objective_label(objective_mode),
                    &pipeline.factor_name,
                    DebugExpansionLatestSignal {
                        timestamp: pipeline.latest_signal.timestamp,
                        direction: pipeline.latest_signal.direction.clone(),
                        value: pipeline.latest_signal.value,
                        confidence: pipeline.latest_signal.confidence,
                        explanation: pipeline.latest_signal.explanation.clone(),
                    },
                    DebugExpansionProbabilitySupport {
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
                        uncertainty_factors: pipeline
                            .probability_support
                            .uncertainty_factors
                            .clone(),
                    },
                    DebugExpansionBbnSupport {
                        market_regime_label: pipeline.bbn_support.market_regime_label.clone(),
                        liquidity_context_label: pipeline
                            .bbn_support
                            .liquidity_context_label
                            .clone(),
                        evidence_policy: pipeline.bbn_support.evidence_policy.clone(),
                        pre_bayes_filter: pipeline.bbn_support.pre_bayes_filter.clone(),
                        evidence_assignments: pipeline.bbn_support.evidence_assignments.clone(),
                        raw_market_regime_trace: ict_engine::state::FactorPipelineLabelSource {
                            label: pipeline.bbn_support.raw_market_regime_trace.label.clone(),
                            derivation: pipeline
                                .bbn_support
                                .raw_market_regime_trace
                                .derivation
                                .clone(),
                            evidence: pipeline
                                .bbn_support
                                .raw_market_regime_trace
                                .evidence
                                .clone(),
                        },
                        raw_liquidity_context_trace: ict_engine::state::FactorPipelineLabelSource {
                            label: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .label
                                .clone(),
                            derivation: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .derivation
                                .clone(),
                            evidence: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .evidence
                                .clone(),
                        },
                        raw_multi_timeframe_resonance_trace:
                            ict_engine::state::FactorPipelineLabelSource {
                                label: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .label
                                    .clone(),
                                derivation: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .derivation
                                    .clone(),
                                evidence: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .evidence
                                    .clone(),
                            },
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
                    &market.multi_timeframe_summary,
                    BTreeMap::from([
                        (
                            "market_regime".to_string(),
                            pipeline.bbn_support.market_regime_label.clone(),
                        ),
                        (
                            "liquidity_context".to_string(),
                            pipeline.bbn_support.liquidity_context_label.clone(),
                        ),
                        (
                            "factor_alignment".to_string(),
                            pipeline.probability_support.alignment_label.clone(),
                        ),
                        (
                            "factor_uncertainty".to_string(),
                            pipeline.probability_support.uncertainty_label.clone(),
                        ),
                        (
                            "multi_timeframe_resonance".to_string(),
                            pipeline
                                .bbn_support
                                .pre_bayes_filter
                                .raw_multi_timeframe_resonance_label
                                .clone(),
                        ),
                    ]),
                    pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter),
                    env_f64("ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD", 0.12),
                )
                .ok()
            })
        });

    Ok(FuturesSopReport {
        sop_version: "futures-sop-v1".to_string(),
        generated_at: Utc::now(),
        root: root.to_string(),
        output_dir: output_dir.to_string(),
        cleaned_dir,
        state_dir: state_dir.clone(),
        interval: interval.to_string(),
        selection_policy:
            "continuous_front_contract_multi_timeframe_cleaning_then_factor_research_with_1m_5m_15m_1h_4h_1d_context_then_global_leaderboard_by_first_place_and_average_composite_score"
                .to_string(),
        clean_report,
        market_reports,
        global_factor_leaderboard,
        recommended_global_factor,
        recommended_global_pre_bayes_policy,
        recommended_global_pre_bayes_entry_quality_bridge,
        recommended_global_pre_bayes_summary,
        recommended_global_pre_bayes_policy_lineage,
        recommended_global_pre_bayes_soft_evidence_diff,
        recommended_global_pipeline_debug,
        recommended_market_factors,
        warnings,
        recommended_commands: vec![
            format!(
                "ict-engine futures-sop --root {} --output-dir {} --interval {}",
                shell_quote(root),
                shell_quote(output_dir),
                shell_quote(interval)
            ),
            format!(
                "ict-engine factor-research --symbol NQ --data {} --state-dir {}",
                shell_quote(
                    &std::path::Path::new(output_dir)
                        .join(format!("cleaned-{}/nq.continuous-{}.json", interval, interval))
                        .to_string_lossy()
                ),
                shell_quote(&state_dir)
            ),
            format!(
                "ict-engine clean-futures --root {} --output-dir {} --multi-timeframe",
                shell_quote(root),
                shell_quote(output_dir)
            ),
        ],
    })
}

fn suspicious_aggregate_return(value: f64) -> bool {
    !value.is_finite() || value.abs() > 1_000_000.0
}

fn expansion_sop_command(
    root: Option<&str>,
    output_dir: &str,
    interval: &str,
    lookback: usize,
    atr_multiplier: f64,
    objective: &str,
    mutation_spec_path: Option<&str>,
    emit_mutation_evaluation: bool,
) -> Result<()> {
    let objective_mode = parse_research_objective(objective)?;
    let root = resolve_tomac_root(root)?;
    let mutation_spec = mutation_spec_path
        .map(load_factor_mutation_spec)
        .transpose()?;
    let report = run_expansion_sop(
        &root,
        output_dir,
        interval,
        lookback,
        atr_multiplier,
        objective_mode,
        mutation_spec.as_ref(),
    )?;
    let report_path = std::path::Path::new(output_dir)
        .join(format!("expansion_sop_report.{}.json", interval))
        .to_string_lossy()
        .to_string();
    std::fs::write(&report_path, serde_json::to_string_pretty(&report)?)?;
    if emit_mutation_evaluation {
        let next_mutation_spec_template =
            report
                .factor_mutation_evaluation
                .as_ref()
                .map(|evaluation| {
                    next_mutation_spec_template(mutation_spec.as_ref(), evaluation, true)
                });
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({
                "mutation_spec": mutation_spec,
                "factor_mutation_evaluation": report.factor_mutation_evaluation,
                "next_mutation_spec_template": next_mutation_spec_template,
                "recommended_global_factor": report.recommended_global_factor,
                "recommended_global_pre_bayes_summary": report.recommended_global_pre_bayes_summary,
                "recommended_commands": report.recommended_commands,
            }))?
        );
    } else {
        let compact_report = build_backtest_result_artifact(
            format!("expansion_sop:{}", interval),
            &report
                .recommended_market_factors
                .iter()
                .map(|(market, factor)| format!("{}:{}", market, factor))
                .collect::<Vec<_>>(),
            &[format!(
                "recommended_global_factor={:?}",
                report.recommended_global_factor
            )],
            &[],
            &[],
            true,
            &report.recommended_commands,
        );
        let factor_lifecycle = build_factor_lifecycle_view(
            report.mutation_spec.as_ref(),
            report.factor_mutation_evaluation.as_ref(),
            &PromotionDecision {
                approved: report.recommended_global_factor.is_some(),
                status: if report.recommended_global_factor.is_some() {
                    "promote".to_string()
                } else {
                    "hold".to_string()
                },
                reason: "expansion_sop_global_selection".to_string(),
                target_factors: report.recommended_global_factor.iter().cloned().collect(),
                target_families: vec![],
            },
            &RollbackRecommendation {
                should_rollback: false,
                scope: "none".to_string(),
                reason: "no_global_rollback".to_string(),
                target_factors: vec![],
                target_families: vec![],
            },
        );
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({
                "report": report,
                "compact_backtest_report": compact_report,
                "factor_lifecycle": factor_lifecycle,
            }))?
        );
    }
    Ok(())
}

fn run_expansion_sop(
    root: &str,
    output_dir: &str,
    interval: &str,
    lookback: usize,
    atr_multiplier: f64,
    objective_mode: ResearchObjectiveMode,
    mutation_spec: Option<&FactorMutationSpec>,
) -> Result<ExpansionSopReport> {
    let cleaned_dir = std::path::Path::new(output_dir)
        .join(format!("cleaned-{}", interval))
        .to_string_lossy()
        .to_string();
    let state_dir = std::path::Path::new(output_dir)
        .join("state")
        .to_string_lossy()
        .to_string();
    std::fs::create_dir_all(&state_dir)?;
    let multi_timeframe_clean_report = run_clean_futures_multi_timeframe(root, output_dir)?;
    let clean_report = multi_timeframe_clean_report
        .reports
        .iter()
        .find(|report| report.interval == interval)
        .cloned()
        .ok_or_else(|| anyhow!("missing cleaned report for interval '{}'", interval))?;

    let mut market_reports = Vec::new();
    let mut warnings = Vec::new();
    let mut recommended_market_factors = BTreeMap::<String, String>::new();
    let mut global_scores = BTreeMap::<String, Vec<ExpansionFactorScore>>::new();
    let baseline_registry = FactorRegistry::default();
    let mut registry = FactorRegistry::default();
    if let Some(spec) = mutation_spec {
        apply_factor_mutation_spec(&mut registry, spec)?;
    }
    let baseline_metrics = mutation_spec
        .map(|_| {
            build_expansion_sop_mutation_metrics(
                &baseline_registry,
                &clean_report,
                lookback,
                atr_multiplier,
                objective_mode,
            )
        })
        .transpose()?;

    for dataset in &clean_report.datasets {
        let candles = load_candles(&dataset.output_path)?;
        let resolved_multi_timeframe_inputs = resolved_multi_timeframe_inputs_for_market(
            &multi_timeframe_clean_report,
            &dataset.market,
        );
        let multi_timeframe_summary =
            build_multi_timeframe_summary(&dataset.output_path, &resolved_multi_timeframe_inputs)?
                .into_iter()
                .chain(
                    build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?
                        .summary
                        .into_iter(),
                )
                .collect::<Vec<_>>();
        let scores =
            expansion_factor_scores_for_market(&registry, &candles, lookback, atr_multiplier)?;
        let expansion_samples = scores
            .first()
            .map(|score| score.expansion_samples)
            .unwrap_or(0);
        let bull_expansion_samples = scores
            .first()
            .map(|score| score.bull_expansion_samples)
            .unwrap_or(0);
        let bear_expansion_samples = scores
            .first()
            .map(|score| score.bear_expansion_samples)
            .unwrap_or(0);
        if expansion_samples == 0 {
            warnings.push(format!(
                "{}:no_expansion_samples_for_lookback_{}_atr_{:.2}",
                dataset.market, lookback, atr_multiplier
            ));
        }
        if bull_expansion_samples == 0 || bear_expansion_samples == 0 {
            warnings.push(format!(
                "{}:unbalanced_expansion_labels bull={} bear={}",
                dataset.market, bull_expansion_samples, bear_expansion_samples
            ));
        }
        for score in &scores {
            global_scores
                .entry(score.factor_name.clone())
                .or_default()
                .push(score.clone());
        }
        let best_factor = scores.first().map(|score| score.factor_name.clone());
        if let Some(best_factor) = &best_factor {
            recommended_market_factors.insert(dataset.market.clone(), best_factor.clone());
        }
        let pipeline = best_factor
            .as_deref()
            .map(|factor| {
                build_expansion_factor_pipeline_report_with_registry_v2(
                    &dataset.market,
                    factor,
                    &candles,
                    &multi_timeframe_summary,
                    &registry,
                )
            })
            .transpose()?;
        market_reports.push(ExpansionMarketReport {
            market: dataset.market.clone(),
            cleaned_path: dataset.output_path.clone(),
            total_candles: dataset.summary.aggregated_candles,
            expansion_samples,
            bull_expansion_samples,
            bear_expansion_samples,
            best_factor,
            top_factors: scores.into_iter().take(5).collect(),
            multi_timeframe_summary,
            pipeline,
        });
    }

    market_reports.sort_by(|a, b| a.market.cmp(&b.market));
    let mut global_factor_leaderboard = global_scores
        .into_iter()
        .map(|(factor_name, scores)| ExpansionFactorLeaderboardEntry {
            first_place_markets: market_reports
                .iter()
                .filter(|market| market.best_factor.as_deref() == Some(factor_name.as_str()))
                .count(),
            markets_seen: scores.len(),
            average_fit_score: scores.iter().map(|score| score.fit_score).sum::<f64>()
                / scores.len() as f64,
            average_balanced_accuracy: scores
                .iter()
                .map(|score| score.balanced_accuracy)
                .sum::<f64>()
                / scores.len() as f64,
            average_directional_accuracy: scores
                .iter()
                .map(|score| score.directional_accuracy)
                .sum::<f64>()
                / scores.len() as f64,
            factor_name,
        })
        .collect::<Vec<_>>();
    global_factor_leaderboard.sort_by(|a, b| {
        b.first_place_markets
            .cmp(&a.first_place_markets)
            .then_with(|| {
                b.average_fit_score
                    .partial_cmp(&a.average_fit_score)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    let recommended_global_factor = global_factor_leaderboard
        .first()
        .map(|entry| entry.factor_name.clone());
    let recommended_global_pre_bayes_policy = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.policy.clone())
        });
    let recommended_global_pre_bayes_entry_quality_bridge = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.entry_quality_bridge.clone())
        });
    let recommended_global_pre_bayes_summary = {
        pre_bayes_report_summary(
            recommended_global_pre_bayes_policy.as_ref(),
            recommended_global_pre_bayes_entry_quality_bridge.as_ref(),
        )
    };
    let recommended_global_pre_bayes_policy_lineage = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            let history = load_pre_bayes_policy_history(&state_dir, &market.market).ok()?;
            let gate_status = market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.as_str())
                .unwrap_or("");
            Some(pre_bayes_policy_lineage_summary(&history, gate_status))
        });
    let recommended_global_pre_bayes_soft_evidence_diff = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| market.pipeline.as_ref())
        .map(|pipeline| pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter))
        .unwrap_or_default();
    let factor_mutation_evaluation = mutation_spec.map(|spec| {
        let mut metrics_after = build_expansion_sop_metrics_from_market_reports(&market_reports);
        metrics_after.regression_reasons_by_market = expansion_regression_reasons_by_market(
            &baseline_registry,
            &registry,
            &clean_report,
            lookback,
            atr_multiplier,
            objective_mode,
        )
        .unwrap_or_default();
        metrics_after.regressed_markets = metrics_after
            .regression_reasons_by_market
            .keys()
            .cloned()
            .collect();
        evaluate_expansion_sop_mutation(
            spec,
            root,
            interval,
            lookback,
            atr_multiplier,
            baseline_metrics.as_ref(),
            metrics_after,
        )
    });
    if let (Some(spec), Some(evaluation)) = (mutation_spec, factor_mutation_evaluation.clone()) {
        append_factor_mutation_run(
            &state_dir,
            "EXPANSION_SOP",
            FactorMutationRunRecord {
                run_id: format!(
                    "factor-mutation:expansion-sop:{}",
                    Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
                ),
                timestamp: Utc::now(),
                symbol: "EXPANSION_SOP".to_string(),
                source_command: "expansion-sop".to_string(),
                data_path: root.to_string(),
                paired_data_path: Some(interval.to_string()),
                mutation_spec: spec.clone(),
                evaluation,
            },
        )?;
    }
    let recommended_policy_history_symbol = market_reports
        .iter()
        .find(|market| market.best_factor.as_deref() == recommended_global_factor.as_deref())
        .map(|market| market.market.clone())
        .unwrap_or_else(|| "NQ".to_string());
    let recommended_global_pipeline_debug = market_reports
        .iter()
        .find(|market| {
            market.best_factor.as_deref() == recommended_global_factor.as_deref()
                && market.pipeline.is_some()
        })
        .and_then(|market| {
            market.pipeline.as_ref().and_then(|pipeline| {
                build_factor_pipeline_debug_report_v2(
                    &market.market,
                    &market.cleaned_path,
                    research_objective_label(objective_mode),
                    &pipeline.factor_name,
                    DebugExpansionLatestSignal {
                        timestamp: pipeline.latest_signal.timestamp,
                        direction: pipeline.latest_signal.direction.clone(),
                        value: pipeline.latest_signal.value,
                        confidence: pipeline.latest_signal.confidence,
                        explanation: pipeline.latest_signal.explanation.clone(),
                    },
                    DebugExpansionProbabilitySupport {
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
                        uncertainty_factors: pipeline
                            .probability_support
                            .uncertainty_factors
                            .clone(),
                    },
                    DebugExpansionBbnSupport {
                        market_regime_label: pipeline.bbn_support.market_regime_label.clone(),
                        liquidity_context_label: pipeline
                            .bbn_support
                            .liquidity_context_label
                            .clone(),
                        evidence_policy: pipeline.bbn_support.evidence_policy.clone(),
                        pre_bayes_filter: pipeline.bbn_support.pre_bayes_filter.clone(),
                        evidence_assignments: pipeline.bbn_support.evidence_assignments.clone(),
                        raw_market_regime_trace: ict_engine::state::FactorPipelineLabelSource {
                            label: pipeline.bbn_support.raw_market_regime_trace.label.clone(),
                            derivation: pipeline
                                .bbn_support
                                .raw_market_regime_trace
                                .derivation
                                .clone(),
                            evidence: pipeline
                                .bbn_support
                                .raw_market_regime_trace
                                .evidence
                                .clone(),
                        },
                        raw_liquidity_context_trace: ict_engine::state::FactorPipelineLabelSource {
                            label: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .label
                                .clone(),
                            derivation: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .derivation
                                .clone(),
                            evidence: pipeline
                                .bbn_support
                                .raw_liquidity_context_trace
                                .evidence
                                .clone(),
                        },
                        raw_multi_timeframe_resonance_trace:
                            ict_engine::state::FactorPipelineLabelSource {
                                label: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .label
                                    .clone(),
                                derivation: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .derivation
                                    .clone(),
                                evidence: pipeline
                                    .bbn_support
                                    .raw_multi_timeframe_resonance_trace
                                    .evidence
                                    .clone(),
                            },
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
                    &market.multi_timeframe_summary,
                    BTreeMap::from([
                        (
                            "market_regime".to_string(),
                            pipeline.bbn_support.market_regime_label.clone(),
                        ),
                        (
                            "liquidity_context".to_string(),
                            pipeline.bbn_support.liquidity_context_label.clone(),
                        ),
                        (
                            "factor_alignment".to_string(),
                            pipeline.probability_support.alignment_label.clone(),
                        ),
                        (
                            "factor_uncertainty".to_string(),
                            pipeline.probability_support.uncertainty_label.clone(),
                        ),
                        (
                            "multi_timeframe_resonance".to_string(),
                            pipeline
                                .bbn_support
                                .pre_bayes_filter
                                .raw_multi_timeframe_resonance_label
                                .clone(),
                        ),
                    ]),
                    pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter),
                    env_f64("ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD", 0.12),
                )
                .ok()
            })
        });

    Ok(ExpansionSopReport {
        sop_version: "expansion-sop-v1".to_string(),
        generated_at: Utc::now(),
        root: root.to_string(),
        output_dir: output_dir.to_string(),
        cleaned_dir,
        interval: interval.to_string(),
        expansion_lookback: lookback,
        expansion_atr_multiplier: atr_multiplier,
        clean_report,
        market_reports,
        global_factor_leaderboard,
        recommended_global_factor: recommended_global_factor.clone(),
        recommended_global_pre_bayes_policy,
        recommended_global_pre_bayes_entry_quality_bridge,
        recommended_global_pre_bayes_summary,
        recommended_global_pre_bayes_policy_lineage,
        recommended_global_pre_bayes_soft_evidence_diff,
        recommended_global_pipeline_debug,
        recommended_market_factors,
        mutation_spec: mutation_spec.cloned(),
        factor_mutation_evaluation,
        warnings,
        recommended_commands: vec![
            format!(
                "ict-engine expansion-sop --root {} --output-dir {} --interval {} --lookback {} --atr-multiplier {:.2} --objective {}",
                shell_quote(root),
                shell_quote(output_dir),
                shell_quote(interval),
                lookback,
                atr_multiplier,
                shell_quote(research_objective_label(objective_mode))
            ),
            format!(
                "ict-engine expansion-sop --root {} --output-dir {} --interval {} --lookback {} --atr-multiplier {:.2} --objective {} --mutation-spec <spec.json> --emit-mutation-evaluation",
                shell_quote(root),
                shell_quote(output_dir),
                shell_quote(interval),
                lookback,
                atr_multiplier,
                shell_quote(research_objective_label(objective_mode))
            ),
            format!(
                "ict-engine factor-pipeline-debug --symbol {} --data {} --factor {} --objective {}",
                shell_quote(&recommended_policy_history_symbol),
                shell_quote(
                    &std::path::Path::new(output_dir)
                        .join(format!("cleaned-{}/{}.continuous-{}.json", interval, recommended_policy_history_symbol.to_ascii_lowercase(), interval))
                        .to_string_lossy()
                ),
                shell_quote(
                    recommended_global_factor
                        .clone()
                        .unwrap_or_else(|| "structure_ict".to_string())
                        .as_str()
                ),
                shell_quote(research_objective_label(objective_mode))
            ),
            format!(
                "ict-engine workflow-status --symbol {} --state-dir {} --phase pre-bayes-policy-history",
                shell_quote(&recommended_policy_history_symbol),
                shell_quote(&state_dir)
            ),
            format!(
                "ict-engine clean-futures --root {} --output-dir {} --multi-timeframe",
                shell_quote(root),
                shell_quote(output_dir)
            ),
        ],
    })
}

fn build_expansion_sop_mutation_metrics(
    registry: &FactorRegistry,
    clean_report: &CleanFuturesReport,
    lookback: usize,
    atr_multiplier: f64,
    _objective_mode: ResearchObjectiveMode,
) -> Result<FactorMutationMetricSet> {
    let mut market_reports = Vec::new();
    for dataset in &clean_report.datasets {
        let candles = load_candles(&dataset.output_path)?;
        let resolved_multi_timeframe_inputs = resolve_multi_timeframe_inputs(
            &dataset.output_path,
            None,
            None,
            None,
            None,
            None,
            None,
        );
        let multi_timeframe_summary =
            build_multi_timeframe_summary(&dataset.output_path, &resolved_multi_timeframe_inputs)?
                .into_iter()
                .chain(
                    build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?
                        .summary
                        .into_iter(),
                )
                .collect::<Vec<_>>();
        let scores =
            expansion_factor_scores_for_market(registry, &candles, lookback, atr_multiplier)?;
        let best_factor = scores.first().map(|score| score.factor_name.clone());
        let pipeline = best_factor
            .as_deref()
            .map(|factor| {
                build_expansion_factor_pipeline_report_with_registry_v2(
                    &dataset.market,
                    factor,
                    &candles,
                    &multi_timeframe_summary,
                    registry,
                )
            })
            .transpose()?;
        market_reports.push(ExpansionMarketReport {
            market: dataset.market.clone(),
            cleaned_path: dataset.output_path.clone(),
            total_candles: dataset.summary.aggregated_candles,
            expansion_samples: scores
                .first()
                .map(|score| score.expansion_samples)
                .unwrap_or(0),
            bull_expansion_samples: scores
                .first()
                .map(|score| score.bull_expansion_samples)
                .unwrap_or(0),
            bear_expansion_samples: scores
                .first()
                .map(|score| score.bear_expansion_samples)
                .unwrap_or(0),
            best_factor,
            top_factors: scores.into_iter().take(5).collect(),
            multi_timeframe_summary,
            pipeline,
        });
    }
    Ok(build_expansion_sop_metrics_from_market_reports(
        &market_reports,
    ))
}

fn build_expansion_sop_metrics_from_market_reports(
    market_reports: &[ExpansionMarketReport],
) -> FactorMutationMetricSet {
    let mut metrics = FactorMutationMetricSet {
        top_factor_names: market_reports
            .iter()
            .filter_map(|market| market.best_factor.clone())
            .take(3)
            .collect(),
        ..FactorMutationMetricSet::default()
    };
    if market_reports.is_empty() {
        return metrics;
    }
    metrics.best_factor_composite_score = market_reports
        .iter()
        .filter_map(|market| market.top_factors.first().map(|score| score.fit_score))
        .sum::<f64>()
        / market_reports.len() as f64;
    metrics.expansion_balanced_accuracy = Some(
        market_reports
            .iter()
            .filter_map(|market| {
                market
                    .top_factors
                    .first()
                    .map(|score| score.balanced_accuracy)
            })
            .sum::<f64>()
            / market_reports.len() as f64,
    );
    metrics.expansion_directional_accuracy = Some(
        market_reports
            .iter()
            .filter_map(|market| {
                market
                    .top_factors
                    .first()
                    .map(|score| score.directional_accuracy)
            })
            .sum::<f64>()
            / market_reports.len() as f64,
    );
    let selected_probabilities = market_reports
        .iter()
        .filter_map(|market| {
            market
                .pipeline
                .as_ref()
                .map(|pipeline| pipeline.bbn_support.selected_win_probability)
        })
        .collect::<Vec<_>>();
    if !selected_probabilities.is_empty() {
        metrics.expansion_selected_win_probability =
            Some(selected_probabilities.iter().sum::<f64>() / selected_probabilities.len() as f64);
    }
    metrics.pre_bayes_soft_evidence_divergence_count = market_reports
        .iter()
        .filter_map(|market| market.pipeline.as_ref())
        .map(|pipeline| {
            pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter)
                .into_iter()
                .filter(|item| item.diverges_from_filtered_state)
                .count()
        })
        .sum::<usize>();
    metrics.pre_bayes_gate_status = market_reports
        .iter()
        .filter_map(|market| market.pipeline.as_ref())
        .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.clone())
        .find(|status| status == "observe_only")
        .or_else(|| {
            market_reports
                .iter()
                .filter_map(|market| market.pipeline.as_ref())
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.clone())
                .find(|status| status == "pass_neutralized")
        })
        .or_else(|| {
            market_reports
                .iter()
                .filter_map(|market| market.pipeline.as_ref())
                .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.clone())
                .next()
        });
    let bridge_gaps = market_reports
        .iter()
        .filter_map(|market| market.pipeline.as_ref())
        .map(|pipeline| {
            pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
                .long_short_signal_probability_gap
        })
        .collect::<Vec<_>>();
    if !bridge_gaps.is_empty() {
        metrics.pre_bayes_bridge_probability_gap =
            Some(bridge_gaps.iter().sum::<f64>() / bridge_gaps.len() as f64);
    }
    metrics.pre_bayes_bridge_selected_entry_quality = market_reports
        .iter()
        .filter_map(|market| market.pipeline.as_ref())
        .find_map(|pipeline| {
            pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
                .selected_entry_quality
        });
    metrics.expansion_selected_direction = market_reports
        .iter()
        .filter_map(|market| market.pipeline.as_ref())
        .map(|pipeline| pipeline.bbn_support.selected_direction.clone())
        .next();
    metrics.worst_market_balanced_accuracy = market_reports
        .iter()
        .filter_map(|market| {
            market
                .top_factors
                .first()
                .map(|score| score.balanced_accuracy)
        })
        .min_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    metrics.worst_market_bridge_probability_gap = market_reports
        .iter()
        .filter_map(|market| {
            market.pipeline.as_ref().map(|pipeline| {
                pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
                    .long_short_signal_probability_gap
            })
        })
        .min_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
    metrics
}

fn pre_bayes_gate_rank(status: &str) -> u8 {
    match status {
        "pass_hard" => 2,
        "pass_neutralized" => 1,
        "observe_only" => 0,
        _ => 0,
    }
}

fn pre_bayes_gate_is_hard_pass(status: &str) -> bool {
    status == "pass_hard"
}

fn pre_bayes_gate_regressed(previous: &str, current: &str) -> bool {
    pre_bayes_gate_rank(current) < pre_bayes_gate_rank(previous)
}

fn expansion_regression_reasons_by_market(
    baseline_registry: &FactorRegistry,
    mutated_registry: &FactorRegistry,
    clean_report: &CleanFuturesReport,
    lookback: usize,
    atr_multiplier: f64,
    _objective_mode: ResearchObjectiveMode,
) -> Result<BTreeMap<String, Vec<String>>> {
    let mut reasons_by_market = BTreeMap::<String, Vec<String>>::new();
    for dataset in &clean_report.datasets {
        let candles = load_candles(&dataset.output_path)?;
        let resolved_multi_timeframe_inputs = resolve_multi_timeframe_inputs(
            &dataset.output_path,
            None,
            None,
            None,
            None,
            None,
            None,
        );
        let multi_timeframe_summary =
            build_multi_timeframe_summary(&dataset.output_path, &resolved_multi_timeframe_inputs)?
                .into_iter()
                .chain(
                    build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?
                        .summary
                        .into_iter(),
                )
                .collect::<Vec<_>>();
        let baseline_scores = expansion_factor_scores_for_market(
            baseline_registry,
            &candles,
            lookback,
            atr_multiplier,
        )?;
        let mutated_scores = expansion_factor_scores_for_market(
            mutated_registry,
            &candles,
            lookback,
            atr_multiplier,
        )?;
        let baseline_balanced = baseline_scores
            .first()
            .map(|score| score.balanced_accuracy)
            .unwrap_or_default();
        let mutated_balanced = mutated_scores
            .first()
            .map(|score| score.balanced_accuracy)
            .unwrap_or_default();
        let baseline_factor = baseline_scores
            .first()
            .map(|score| score.factor_name.as_str());
        let mutated_factor = mutated_scores
            .first()
            .map(|score| score.factor_name.as_str());
        let baseline_pipeline = baseline_factor
            .map(|factor| {
                build_expansion_factor_pipeline_report_with_registry_v2(
                    &dataset.market,
                    factor,
                    &candles,
                    &multi_timeframe_summary,
                    baseline_registry,
                )
            })
            .transpose()?;
        let mutated_pipeline = mutated_factor
            .map(|factor| {
                build_expansion_factor_pipeline_report_with_registry_v2(
                    &dataset.market,
                    factor,
                    &candles,
                    &multi_timeframe_summary,
                    mutated_registry,
                )
            })
            .transpose()?;
        let baseline_bridge_gap = baseline_pipeline
            .as_ref()
            .map(|pipeline| {
                pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
                    .long_short_signal_probability_gap
            })
            .unwrap_or_default();
        let mutated_bridge_gap = mutated_pipeline
            .as_ref()
            .map(|pipeline| {
                pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
                    .long_short_signal_probability_gap
            })
            .unwrap_or_default();
        let baseline_gate = baseline_pipeline
            .as_ref()
            .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.as_str())
            .unwrap_or("");
        let mutated_gate = mutated_pipeline
            .as_ref()
            .map(|pipeline| pipeline.bbn_support.pre_bayes_filter.gating_status.as_str())
            .unwrap_or("");
        let mut reasons = Vec::new();
        if mutated_balanced + 1e-9 < baseline_balanced {
            reasons.push("balanced_accuracy_regressed".to_string());
        }
        if mutated_bridge_gap + 1e-9 < baseline_bridge_gap {
            reasons.push("bridge_gap_regressed".to_string());
        }
        if pre_bayes_gate_regressed(baseline_gate, mutated_gate) {
            reasons.push("pre_bayes_gate_regressed".to_string());
        }
        if !reasons.is_empty() {
            reasons_by_market.insert(dataset.market.clone(), reasons);
        }
    }
    Ok(reasons_by_market)
}

fn recommended_mutation_directions_from_failure_tags(
    failure_tags: &[String],
    regressed_markets: &[String],
    regression_reasons_by_market: &BTreeMap<String, Vec<String>>,
) -> Vec<String> {
    let mut directions = Vec::new();
    if failure_tags
        .iter()
        .any(|tag| tag == "bull_bear_separation_weak")
        || failure_tags
            .iter()
            .any(|tag| tag == "bull_bear_separation_regressed")
    {
        directions.push(
            "Prioritize base factor parameter tuning that improves bull/bear expansion separation before enabling additional factors"
                .to_string(),
        );
    }
    if failure_tags.iter().any(|tag| tag == "bridge_gap_too_small")
        || failure_tags.iter().any(|tag| tag == "bridge_gap_regressed")
    {
        directions.push(
            "Tighten directionality-sensitive parameters to widen PreBayes bridge probability gap instead of broad family enablement"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "soft_evidence_divergence_elevated")
    {
        directions.push(
            "Reduce mutations that create label conflict; prefer edits that keep soft evidence aligned with filtered assignments"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "pre_bayes_gate_observe_only" || tag == "pre_bayes_gate_neutralized")
    {
        directions.push(
            "Avoid mutations that neutralize the PreBayes gate; prefer stronger alignment/uncertainty separation on the selected factor"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "pre_bayes_gate_regressed")
    {
        directions.push(
            "Revert the gate-regressing parameter move and prefer slower, confirmation-heavy edits that preserve PreBayes pass_neutralized or better"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "best_factor_composite_regressed")
    {
        directions.push(
            "Keep the base factor first in the objective ranking before chasing bridge improvements; do not sacrifice composite separation quality for a single latest-sample boost"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "market_specific_regressions_detected")
    {
        directions.push(
            "Stop global blind tuning and pivot to market-specific label refinement or per-market factor forks for the regressed families"
                .to_string(),
        );
    }
    if failure_tags
        .iter()
        .any(|tag| tag == "no_superior_mutation_found")
    {
        directions.push(
            "Treat the current default as near-local-optimum until new evidence appears; shift the next cycle to label refinement or market-specific fork validation"
                .to_string(),
        );
    }
    if !regressed_markets.is_empty() {
        directions.push(format!(
            "Inspect regressed markets first: {}",
            regressed_markets.join(",")
        ));
    }
    let markets_with_bridge_regressions = regression_reasons_by_market
        .iter()
        .filter(|(_, reasons)| {
            reasons
                .iter()
                .any(|reason| reason == "bridge_gap_regressed")
        })
        .map(|(market, _)| market.clone())
        .collect::<Vec<_>>();
    if !markets_with_bridge_regressions.is_empty() {
        directions.push(format!(
            "Target bridge-sensitive parameter edits for markets with bridge regressions: {}",
            markets_with_bridge_regressions.join(",")
        ));
    }
    let markets_with_gate_regressions = regression_reasons_by_market
        .iter()
        .filter(|(_, reasons)| {
            reasons
                .iter()
                .any(|reason| reason == "pre_bayes_gate_regressed")
        })
        .map(|(market, _)| market.clone())
        .collect::<Vec<_>>();
    if !markets_with_gate_regressions.is_empty() {
        directions.push(format!(
            "Prioritize mutations that restore PreBayes pass gating for markets: {}",
            markets_with_gate_regressions.join(",")
        ));
    }
    let markets_with_separation_regressions = regression_reasons_by_market
        .iter()
        .filter(|(_, reasons)| {
            reasons
                .iter()
                .any(|reason| reason == "balanced_accuracy_regressed")
        })
        .map(|(market, _)| market.clone())
        .collect::<Vec<_>>();
    if !markets_with_separation_regressions.is_empty() {
        directions.push(format!(
            "Re-tune expansion separation parameters for markets: {}",
            markets_with_separation_regressions.join(",")
        ));
    }
    directions.dedup();
    directions
}

fn no_superior_mutation_found(
    score_delta: f64,
    failure_tags: &[String],
    objective: ResearchObjectiveMode,
) -> bool {
    objective == ResearchObjectiveMode::ExpansionManipulation
        && score_delta <= 0.0
        && !failure_tags
            .iter()
            .any(|tag| tag == "pre_bayes_gate_regressed")
}

fn factor_mutation_priority_markets(evaluation: &FactorMutationEvaluation) -> Vec<String> {
    let mut items = evaluation.metrics_after.regressed_markets.clone();
    if items.is_empty() {
        items.extend(
            evaluation
                .metrics_after
                .regression_reasons_by_market
                .keys()
                .cloned(),
        );
    }
    items.truncate(3);
    items
}

fn factor_mutation_priority_reasons(evaluation: &FactorMutationEvaluation) -> Vec<String> {
    let mut counts = BTreeMap::<String, usize>::new();
    for reasons in evaluation
        .metrics_after
        .regression_reasons_by_market
        .values()
    {
        for reason in reasons {
            *counts.entry(reason.clone()).or_default() += 1;
        }
    }
    let mut ordered = counts.into_iter().collect::<Vec<_>>();
    ordered.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    let mut items = ordered
        .into_iter()
        .map(|(reason, _)| reason)
        .collect::<Vec<_>>();
    if items.is_empty() {
        items = evaluation.failure_tags.clone();
    }
    items.truncate(3);
    items
}

fn factor_mutation_recommended_focus(evaluation: &FactorMutationEvaluation) -> Vec<String> {
    let mut focus = evaluation.recommended_mutation_directions.clone();
    focus.truncate(3);
    focus
}

fn factor_mutation_direction_hint_summary(evaluation: &FactorMutationEvaluation) -> Vec<String> {
    let template = next_mutation_spec_template(None, evaluation, false);
    if template.direction_hints.is_empty() {
        return Vec::new();
    }
    template
        .direction_hints
        .into_iter()
        .map(|(parameter, hint)| format!("{}:{}", parameter, hint))
        .collect()
}

fn factor_mutation_step_size_hint_summary(evaluation: &FactorMutationEvaluation) -> Vec<String> {
    let template = next_mutation_spec_template(None, evaluation, false);
    if template.step_size_hints.is_empty() {
        return Vec::new();
    }
    template
        .step_size_hints
        .into_iter()
        .map(|(parameter, step)| format!("{}:{:.4}", parameter, step))
        .collect()
}

fn factor_specific_hint_preferences(
    state_dir: &str,
    symbol: &str,
    base_factor: &str,
) -> (BTreeMap<String, String>, BTreeMap<String, f64>) {
    let runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE).unwrap_or_default();
    let relevant_runs = runs
        .into_iter()
        .filter(|run| run.mutation_spec.base_factor == base_factor)
        .collect::<Vec<_>>();
    let mut direction_candidates =
        BTreeMap::<String, FactorMutationHintEffectivenessSummary>::new();
    let mut direction_buckets = BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut direction_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    let mut step_candidates = BTreeMap::<String, FactorMutationHintEffectivenessSummary>::new();
    let mut step_buckets = BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut step_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    for run in &relevant_runs {
        for (parameter, hint) in &run.mutation_spec.direction_hints {
            direction_buckets
                .entry(parameter.clone())
                .or_default()
                .entry(hint.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *direction_accepts
                    .entry(parameter.clone())
                    .or_default()
                    .entry(hint.clone())
                    .or_default() += 1;
            }
        }
        for (parameter, step) in &run.mutation_spec.step_size_hints {
            let label = format!("{:.4}", step);
            step_buckets
                .entry(parameter.clone())
                .or_default()
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *step_accepts
                    .entry(parameter.clone())
                    .or_default()
                    .entry(label.clone())
                    .or_default() += 1;
            }
        }
    }
    for (parameter, entries) in direction_buckets {
        for (hint, deltas) in entries {
            let accepted = direction_accepts
                .get(&parameter)
                .and_then(|items| items.get(&hint))
                .copied()
                .unwrap_or_default();
            let summary = build_hint_effectiveness_summary(&hint, &deltas, accepted);
            let replace = direction_candidates
                .get(&parameter)
                .map(|existing| compare_hint_effectiveness(&summary, existing).is_gt())
                .unwrap_or(true);
            if replace {
                direction_candidates.insert(parameter.clone(), summary);
            }
        }
    }
    for (parameter, entries) in step_buckets {
        for (hint, deltas) in entries {
            let accepted = step_accepts
                .get(&parameter)
                .and_then(|items| items.get(&hint))
                .copied()
                .unwrap_or_default();
            let summary = build_hint_effectiveness_summary(&hint, &deltas, accepted);
            let replace = step_candidates
                .get(&parameter)
                .map(|existing| compare_hint_effectiveness(&summary, existing).is_gt())
                .unwrap_or(true);
            if replace {
                step_candidates.insert(parameter.clone(), summary);
            }
        }
    }
    (
        direction_candidates
            .into_iter()
            .map(|(parameter, summary)| (parameter, summary.hint))
            .collect(),
        step_candidates
            .into_iter()
            .filter_map(|(parameter, summary)| {
                summary
                    .hint
                    .parse::<f64>()
                    .ok()
                    .map(|value| (parameter, value))
            })
            .collect(),
    )
}

fn next_mutation_spec_template(
    current_spec: Option<&FactorMutationSpec>,
    evaluation: &FactorMutationEvaluation,
    evaluate_expansion_preview: bool,
) -> FactorMutationSpec {
    next_mutation_spec_template_with_preferences(
        current_spec,
        evaluation,
        evaluate_expansion_preview,
        None,
        None,
    )
}

fn next_mutation_spec_template_with_preferences(
    current_spec: Option<&FactorMutationSpec>,
    evaluation: &FactorMutationEvaluation,
    evaluate_expansion_preview: bool,
    preferred_direction_hints: Option<&BTreeMap<String, String>>,
    preferred_step_size_hints: Option<&BTreeMap<String, f64>>,
) -> FactorMutationSpec {
    let priority_reasons = factor_mutation_priority_reasons(evaluation);
    let base_factor = current_spec
        .map(|spec| spec.base_factor.clone())
        .filter(|value| !value.is_empty())
        .or_else(|| evaluation.metrics_after.top_factor_names.first().cloned())
        .unwrap_or_default();
    let base_parameter_overrides = current_spec
        .map(|spec| spec.parameter_overrides.clone())
        .unwrap_or_default();
    let base_enabled_overrides = current_spec
        .map(|spec| spec.enabled_overrides.clone())
        .unwrap_or_default();
    let mut direction_hints = reason_aware_direction_hints(&base_factor, &priority_reasons);
    let mut step_size_hints = reason_aware_step_size_hints(&base_factor, &priority_reasons);
    if let Some(preferred_direction_hints) = preferred_direction_hints {
        for (parameter, hint) in preferred_direction_hints {
            if direction_hints.contains_key(parameter) {
                direction_hints.insert(parameter.clone(), hint.clone());
            }
        }
    }
    if let Some(preferred_step_size_hints) = preferred_step_size_hints {
        for (parameter, step) in preferred_step_size_hints {
            if step_size_hints.contains_key(parameter) {
                step_size_hints.insert(parameter.clone(), *step);
            }
        }
    }
    let reason_aware_parameter_overrides = reason_aware_parameter_overrides(
        &base_factor,
        &priority_reasons,
        &base_parameter_overrides,
        &direction_hints,
        &step_size_hints,
    );
    let reason_aware_enabled_overrides =
        reason_aware_enabled_overrides(&priority_reasons, &base_enabled_overrides);
    FactorMutationSpec {
        mutation_id: format!("{}:next", evaluation.mutation_id),
        base_factor,
        hypothesis: if priority_reasons.is_empty() {
            "Run one atomic mutation that improves PreBayes/bridge quality without widening soft-evidence conflicts"
                .to_string()
        } else {
            format!(
                "Run one atomic mutation targeting: {} with direction_hints={}",
                priority_reasons.join(","),
                format_direction_hints(&direction_hints)
            )
        },
        parameter_overrides: reason_aware_parameter_overrides,
        direction_hints,
        step_size_hints,
        enabled_overrides: reason_aware_enabled_overrides,
        evaluate_expansion_preview,
    }
}

fn reason_aware_parameter_overrides(
    base_factor: &str,
    priority_reasons: &[String],
    parameter_overrides: &BTreeMap<String, f64>,
    direction_hints: &BTreeMap<String, String>,
    step_size_hints: &BTreeMap<String, f64>,
) -> BTreeMap<String, f64> {
    let registry = FactorRegistry::default();
    let factor_definition = registry.get(base_factor);
    let mut selected = BTreeMap::new();
    for reason in priority_reasons {
        let grouped_keys = factor_definition
            .map(|definition| definition.mutation_parameter_group(reason))
            .unwrap_or_default();
        let keywords: &[&str] = match reason.as_str() {
            "balanced_accuracy_regressed"
            | "bull_bear_separation_regressed"
            | "bull_bear_separation_weak"
            | "worst_market_separation_weak" => {
                &["window", "lookback", "threshold", "fast", "slow", "period"]
            }
            "bridge_gap_regressed"
            | "bridge_gap_too_small"
            | "worst_market_bridge_gap_too_small" => {
                &["threshold", "sensitivity", "weight", "bias", "level"]
            }
            "pre_bayes_gate_regressed"
            | "pre_bayes_gate_observe_only"
            | "pre_bayes_gate_neutralized" => {
                &["threshold", "uncertainty", "confidence", "bias", "weight"]
            }
            _ => &[],
        };
        for (key, value) in parameter_overrides {
            if grouped_keys.iter().any(|grouped| grouped == key)
                || keywords.iter().any(|keyword| key.contains(keyword))
            {
                selected.insert(key.clone(), *value);
            }
        }
        if parameter_overrides.is_empty() {
            for key in grouped_keys {
                if let Some(default_value) = factor_definition
                    .and_then(|definition| definition.parameters.get(&key).copied())
                {
                    let adjusted = apply_direction_hint(
                        default_value,
                        direction_hints.get(&key).map(String::as_str),
                        step_size_hints.get(&key).copied(),
                    );
                    selected.insert(key, adjusted);
                }
            }
        }
    }
    if selected.is_empty() {
        if parameter_overrides.is_empty() {
            return BTreeMap::new();
        }
        parameter_overrides
            .iter()
            .take(2)
            .map(|(key, value)| (key.clone(), *value))
            .collect()
    } else {
        selected
    }
}

fn reason_aware_direction_hints(
    base_factor: &str,
    priority_reasons: &[String],
) -> BTreeMap<String, String> {
    let registry = FactorRegistry::default();
    let Some(definition) = registry.get(base_factor) else {
        return BTreeMap::new();
    };
    let mut hints = BTreeMap::new();
    for reason in priority_reasons {
        for (parameter, hint) in definition.mutation_direction_hint(reason) {
            hints.entry(parameter).or_insert(hint);
        }
    }
    hints
}

fn reason_aware_step_size_hints(
    base_factor: &str,
    priority_reasons: &[String],
) -> BTreeMap<String, f64> {
    let registry = FactorRegistry::default();
    let Some(definition) = registry.get(base_factor) else {
        return BTreeMap::new();
    };
    let mut hints = BTreeMap::new();
    for reason in priority_reasons {
        for (parameter, step) in definition.mutation_step_size_hint(reason) {
            hints.entry(parameter).or_insert(step);
        }
    }
    hints
}

fn apply_direction_hint(value: f64, hint: Option<&str>, step_size: Option<f64>) -> f64 {
    let step = step_size.unwrap_or(0.10);
    match hint.unwrap_or("") {
        "increase" | "widen" => value * (1.0 + step),
        "decrease" | "tighten" => value * (1.0 - step),
        _ => value,
    }
}

fn format_direction_hints(hints: &BTreeMap<String, String>) -> String {
    if hints.is_empty() {
        "none".to_string()
    } else {
        hints
            .iter()
            .map(|(parameter, hint)| format!("{}:{}", parameter, hint))
            .collect::<Vec<_>>()
            .join("|")
    }
}

fn reason_aware_enabled_overrides(
    priority_reasons: &[String],
    enabled_overrides: &BTreeMap<String, bool>,
) -> BTreeMap<String, bool> {
    if enabled_overrides.is_empty() {
        return BTreeMap::new();
    }
    let should_preserve = priority_reasons.iter().any(|reason| {
        matches!(
            reason.as_str(),
            "balanced_accuracy_regressed"
                | "bull_bear_separation_regressed"
                | "bull_bear_separation_weak"
        )
    });
    if should_preserve {
        enabled_overrides
            .iter()
            .take(1)
            .map(|(key, value)| (key.clone(), *value))
            .collect()
    } else {
        BTreeMap::new()
    }
}

fn factor_mutation_focus_prompt(
    current_spec: Option<&FactorMutationSpec>,
    evaluation: &FactorMutationEvaluation,
    evaluate_expansion_preview: bool,
) -> AgentPrompt {
    let priority_markets = factor_mutation_priority_markets(evaluation);
    let priority_reasons = factor_mutation_priority_reasons(evaluation);
    let recommended_focus = factor_mutation_recommended_focus(evaluation);
    let next_spec_template =
        next_mutation_spec_template(current_spec, evaluation, evaluate_expansion_preview);
    AgentPrompt::new(
        "factor-mutation-focus",
        "iteration",
        "high",
        "Prepare the next atomic factor mutation using the current priority markets, regression reasons, and recommended focus.",
        "Choose exactly one small mutation that targets the highest-priority regression pattern. Do not broaden scope across multiple factors or bypass the PreBayes gate.",
        format!(
            "mutation_id={} accepted={} priority_markets={} priority_reasons={} recommended_focus={} direction_hints={} step_size_hints={} next_mutation_spec_template={}",
            evaluation.mutation_id,
            evaluation.accepted,
            if priority_markets.is_empty() {
                "none".to_string()
            } else {
                priority_markets.join(",")
            },
            if priority_reasons.is_empty() {
                "none".to_string()
            } else {
                priority_reasons.join(",")
            },
            if recommended_focus.is_empty() {
                "none".to_string()
            } else {
                recommended_focus.join(" | ")
            },
            if next_spec_template.direction_hints.is_empty() {
                "none".to_string()
            } else {
                next_spec_template
                    .direction_hints
                    .iter()
                    .map(|(parameter, hint)| format!("{}:{}", parameter, hint))
                    .collect::<Vec<_>>()
                    .join("|")
            },
            if next_spec_template.step_size_hints.is_empty() {
                "none".to_string()
            } else {
                next_spec_template
                    .step_size_hints
                    .iter()
                    .map(|(parameter, step)| format!("{}:{:.4}", parameter, step))
                    .collect::<Vec<_>>()
                    .join("|")
            },
            serde_json::to_string(&next_spec_template).unwrap_or_else(|_| "{}".to_string())
        ),
        vec![
            "Pick one mutation that addresses the top regression reason in the top priority market".to_string(),
            "Prefer parameter tuning over enabling extra factors unless the current reason clearly points to missing directional separation".to_string(),
            "Do not accept any next mutation that regresses PreBayes gate quality or widens soft evidence conflicts".to_string(),
        ],
        vec!["src/main.rs".to_string(), "src/factors/registry.rs".to_string()],
    )
}

fn expansion_factor_scores_for_market(
    registry: &FactorRegistry,
    candles: &[Candle],
    lookback: usize,
    atr_multiplier: f64,
) -> Result<Vec<ExpansionFactorScore>> {
    let context = FactorContext::default();
    let labels = expansion_direction_labels(candles, lookback, atr_multiplier);
    let bull_expansion_samples = labels
        .iter()
        .filter(|label| matches!(label, Some(Direction::Bull)))
        .count();
    let bear_expansion_samples = labels
        .iter()
        .filter(|label| matches!(label, Some(Direction::Bear)))
        .count();
    let expansion_samples = bull_expansion_samples + bear_expansion_samples;

    let mut scores = registry
        .enabled_factors()
        .into_iter()
        .map(|definition| {
            let series = definition.evaluate(candles, &context)?;
            let mut bull_hits = 0usize;
            let mut bear_hits = 0usize;
            let mut correct = 0usize;
            let mut neutral_predictions = 0usize;
            let mut wrong_direction_predictions = 0usize;
            let mut confidence_total = 0.0;
            let mut confidence_correct = 0.0;

            for (signal, label) in series.signals.iter().zip(labels.iter()) {
                let Some(label) = label else {
                    continue;
                };
                confidence_total += signal.confidence;
                match (signal.direction, label) {
                    (Direction::Bull, Direction::Bull) => {
                        bull_hits += 1;
                        correct += 1;
                        confidence_correct += signal.confidence;
                    }
                    (Direction::Bear, Direction::Bear) => {
                        bear_hits += 1;
                        correct += 1;
                        confidence_correct += signal.confidence;
                    }
                    (Direction::Neutral, _) => neutral_predictions += 1,
                    _ => wrong_direction_predictions += 1,
                }
            }

            let bull_hit_rate = if bull_expansion_samples == 0 {
                0.0
            } else {
                bull_hits as f64 / bull_expansion_samples as f64
            };
            let bear_hit_rate = if bear_expansion_samples == 0 {
                0.0
            } else {
                bear_hits as f64 / bear_expansion_samples as f64
            };
            let directional_accuracy = if expansion_samples == 0 {
                0.0
            } else {
                correct as f64 / expansion_samples as f64
            };
            let balanced_accuracy = if bull_expansion_samples > 0 && bear_expansion_samples > 0 {
                (bull_hit_rate + bear_hit_rate) / 2.0
            } else {
                directional_accuracy
            };
            let confidence_weighted_accuracy = if confidence_total <= f64::EPSILON {
                0.0
            } else {
                confidence_correct / confidence_total
            };
            let mean_confidence = if expansion_samples == 0 {
                0.0
            } else {
                confidence_total / expansion_samples as f64
            };
            let fit_score = balanced_accuracy * 0.70
                + directional_accuracy * 0.20
                + confidence_weighted_accuracy * 0.10;

            Ok(ExpansionFactorScore {
                factor_name: definition.name.clone(),
                expansion_samples,
                bull_expansion_samples,
                bear_expansion_samples,
                bull_hit_rate,
                bear_hit_rate,
                balanced_accuracy,
                directional_accuracy,
                confidence_weighted_accuracy,
                mean_confidence,
                neutral_predictions,
                wrong_direction_predictions,
                fit_score,
            })
        })
        .collect::<Result<Vec<_>>>()?;

    scores.sort_by(|a, b| {
        b.fit_score
            .partial_cmp(&a.fit_score)
            .unwrap_or(std::cmp::Ordering::Equal)
            .then_with(|| {
                b.balanced_accuracy
                    .partial_cmp(&a.balanced_accuracy)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
            .then_with(|| {
                b.directional_accuracy
                    .partial_cmp(&a.directional_accuracy)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    Ok(scores)
}

fn apply_expansion_manipulation_objective(
    report: &mut ict_engine::factor_lab::ResearchReport,
    registry: &FactorRegistry,
    symbol: &str,
    candles: &[Candle],
    multi_timeframe_summary: &[String],
) -> Result<()> {
    let expansion_scores = expansion_factor_scores_for_market(registry, candles, 20, 1.5)?
        .into_iter()
        .map(|score| (score.factor_name.clone(), score))
        .collect::<BTreeMap<_, _>>();

    let mut objective_scorecards = report.backtest.scorecards.clone();
    for scorecard in &mut objective_scorecards {
        let Some(expansion_score) = expansion_scores.get(&scorecard.factor_name) else {
            continue;
        };
        let pipeline = build_expansion_factor_pipeline_report_with_registry_v2(
            symbol,
            &scorecard.factor_name,
            candles,
            multi_timeframe_summary,
            registry,
        )?;
        let gate_status = pipeline.bbn_support.pre_bayes_filter.gating_status.as_str();
        let bridge_gap = pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge)
            .long_short_signal_probability_gap;
        let bridge_gap_score = (bridge_gap / 0.25).clamp(0.0, 1.0);
        let gate_adjustment = match gate_status {
            "pass_hard" => 0.10,
            "pass_neutralized" => 0.03,
            "observe_only" => -0.12,
            _ => 0.0,
        };
        let objective_score = (expansion_score.balanced_accuracy * 0.45
            + expansion_score.directional_accuracy * 0.20
            + expansion_score.fit_score * 0.15
            + bridge_gap_score * 0.10
            + pipeline.bbn_support.selected_win_probability * 0.10
            + gate_adjustment)
            .clamp(0.0, 1.0);

        scorecard.composite_score = objective_score;
        scorecard.score_breakdown = BTreeMap::from([
            (
                "expansion_balanced_accuracy".to_string(),
                expansion_score.balanced_accuracy,
            ),
            (
                "expansion_directional_accuracy".to_string(),
                expansion_score.directional_accuracy,
            ),
            ("expansion_fit_score".to_string(), expansion_score.fit_score),
            ("pre_bayes_bridge_gap_score".to_string(), bridge_gap_score),
            (
                "selected_win_probability".to_string(),
                pipeline.bbn_support.selected_win_probability,
            ),
        ]);
        let mut weaknesses = Vec::new();
        if expansion_score.balanced_accuracy < 0.60 {
            weaknesses.push("expansion_separation_weak".to_string());
        }
        if gate_status == "observe_only" {
            weaknesses.push("pre_bayes_gate_observe_only".to_string());
        }
        if bridge_gap < 0.05 {
            weaknesses.push("bridge_gap_too_small".to_string());
        }
        if pipeline
            .bbn_support
            .pre_bayes_filter
            .filtered_multi_timeframe_resonance_label
            != "aligned"
        {
            weaknesses.push("multi_timeframe_resonance_not_aligned".to_string());
        }
        scorecard.weaknesses = weaknesses;
        scorecard.grade = score_grade(objective_score);
        scorecard.iteration_action = if objective_score >= 0.82 && gate_status == "pass_hard" {
            "keep".to_string()
        } else if objective_score >= 0.60 {
            "tune".to_string()
        } else if objective_score >= 0.45 {
            "observe".to_string()
        } else {
            "replace".to_string()
        };
        scorecard.replacement_candidate = scorecard.iteration_action == "replace";
        scorecard.agent_prompt = format!(
            "Expansion/manipulation objective for '{}'. balanced_accuracy={:.3} directional_accuracy={:.3} gate_status={} bridge_gap={:.3}. Keep bull/bear expansion separation and liquidity-sweep manipulation discrimination while improving pre-bayes gate acceptance.",
            scorecard.factor_name,
            expansion_score.balanced_accuracy,
            expansion_score.directional_accuracy,
            gate_status,
            bridge_gap
        );
    }
    objective_scorecards.sort_by(|a, b| {
        b.composite_score
            .partial_cmp(&a.composite_score)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    report.backtest.scorecards = objective_scorecards.clone();
    report.backtest.iteration_queue = objective_scorecards
        .iter()
        .map(FactorIterationPrompt::from)
        .filter(|item| item.iteration_action != "keep" || item.replacement_candidate)
        .collect();
    report.best_factor = objective_scorecards
        .first()
        .map(|scorecard| scorecard.factor_name.clone());
    report.backtest.best_factor = report.best_factor.clone();
    report.factor_count = objective_scorecards.len();
    Ok(())
}

fn evaluate_expansion_sop_mutation(
    spec: &FactorMutationSpec,
    root: &str,
    interval: &str,
    _lookback: usize,
    _atr_multiplier: f64,
    baseline_metrics: Option<&FactorMutationMetricSet>,
    metrics_after: FactorMutationMetricSet,
) -> FactorMutationEvaluation {
    let metrics_before = baseline_metrics.cloned();
    let score_before = metrics_before
        .as_ref()
        .map(|metrics| {
            mechanical_mutation_score(metrics, ResearchObjectiveMode::ExpansionManipulation)
        })
        .unwrap_or_default();
    let score_after =
        mechanical_mutation_score(&metrics_after, ResearchObjectiveMode::ExpansionManipulation);
    let score_delta = score_after - score_before;
    let balanced_accuracy_before = metrics_before
        .as_ref()
        .and_then(|metrics| metrics.expansion_balanced_accuracy)
        .unwrap_or_default();
    let balanced_accuracy_after = metrics_after
        .expansion_balanced_accuracy
        .unwrap_or_default();
    let bridge_gap_before = metrics_before
        .as_ref()
        .and_then(|metrics| metrics.pre_bayes_bridge_probability_gap)
        .unwrap_or_default();
    let bridge_gap_after = metrics_after
        .pre_bayes_bridge_probability_gap
        .unwrap_or_default();
    let worst_market_balanced_accuracy_after = metrics_after
        .worst_market_balanced_accuracy
        .unwrap_or_default();
    let worst_market_bridge_gap_after = metrics_after
        .worst_market_bridge_probability_gap
        .unwrap_or_default();
    let mut failure_tags = Vec::new();
    if balanced_accuracy_after < 0.60 {
        failure_tags.push("bull_bear_separation_weak".to_string());
    }
    if balanced_accuracy_after + 1e-9 < balanced_accuracy_before {
        failure_tags.push("bull_bear_separation_regressed".to_string());
    }
    if metrics_before
        .as_ref()
        .map(|before| {
            metrics_after.pre_bayes_soft_evidence_divergence_count
                > before.pre_bayes_soft_evidence_divergence_count
        })
        .unwrap_or(metrics_after.pre_bayes_soft_evidence_divergence_count > 0)
    {
        failure_tags.push("soft_evidence_divergence_elevated".to_string());
    }
    if bridge_gap_after < 0.08 {
        failure_tags.push("bridge_gap_too_small".to_string());
    }
    if worst_market_balanced_accuracy_after < 0.55 {
        failure_tags.push("worst_market_separation_weak".to_string());
    }
    if worst_market_bridge_gap_after < 0.06 {
        failure_tags.push("worst_market_bridge_gap_too_small".to_string());
    }
    if bridge_gap_after + 1e-9 < bridge_gap_before {
        failure_tags.push("bridge_gap_regressed".to_string());
    }
    if metrics_after.pre_bayes_gate_status.as_deref() == Some("observe_only") {
        failure_tags.push("pre_bayes_gate_observe_only".to_string());
    }
    if metrics_after.pre_bayes_gate_status.as_deref() == Some("pass_neutralized") {
        failure_tags.push("pre_bayes_gate_neutralized".to_string());
    }
    if !metrics_after.regressed_markets.is_empty() {
        failure_tags.push("market_specific_regressions_detected".to_string());
    }
    let recommended_mutation_directions = recommended_mutation_directions_from_failure_tags(
        &failure_tags,
        &metrics_after.regressed_markets,
        &metrics_after.regression_reasons_by_market,
    );

    FactorMutationEvaluation {
        mutation_id: if spec.mutation_id.is_empty() {
            format!("expansion-sop:{}:{}", interval, root)
        } else {
            spec.mutation_id.clone()
        },
        accepted: score_delta > 0.0
            && balanced_accuracy_after >= balanced_accuracy_before
            && bridge_gap_after >= bridge_gap_before
            && metrics_after
                .pre_bayes_gate_status
                .as_deref()
                .map(pre_bayes_gate_is_hard_pass)
                .unwrap_or(false)
            && failure_tags.is_empty(),
        score_before,
        score_after,
        score_delta,
        baseline_available: metrics_before.is_some(),
        reason: if score_delta > 0.0 && failure_tags.is_empty() {
            "expansion_preview_mechanical_score_improved".to_string()
        } else if failure_tags.is_empty() {
            "expansion_preview_mechanical_score_not_improved".to_string()
        } else {
            format!("expansion_preview_flagged:{}", failure_tags.join(","))
        },
        failure_tags,
        recommended_mutation_directions,
        metrics_before,
        metrics_after,
    }
}

fn expansion_direction_labels(
    candles: &[Candle],
    lookback: usize,
    atr_multiplier: f64,
) -> Vec<Option<Direction>> {
    candles
        .iter()
        .enumerate()
        .map(|(index, _)| expansion_direction_at(candles, index, lookback, atr_multiplier))
        .collect()
}

fn expansion_direction_at(
    candles: &[Candle],
    index: usize,
    lookback: usize,
    atr_multiplier: f64,
) -> Option<Direction> {
    let window_size = lookback.max(14) * 2;
    let start = index.saturating_sub(window_size);
    let window = &candles[start..=index];
    let effective_lookback = lookback.min(window.len());
    let bull = check_bull_expansion_exists(window, effective_lookback, atr_multiplier);
    let bear = check_bear_expansion_exists(window, effective_lookback, atr_multiplier);
    match (bull, bear) {
        (true, false) => Some(Direction::Bull),
        (false, true) => Some(Direction::Bear),
        _ => None,
    }
}

fn pending_update_artifact_path(state_dir: &str, symbol: &str) -> Option<String> {
    let path = std::path::Path::new(state_dir)
        .join(symbol)
        .join(PENDING_UPDATE_ARTIFACT_FILE);
    path.exists().then(|| path.to_string_lossy().to_string())
}

fn source_analyze_run_id_from_artifacts(
    pending: Option<&PendingUpdateArtifact>,
    execution: Option<&ExecutionCandidateArtifact>,
) -> Option<String> {
    pending
        .and_then(|artifact| artifact.source_run_id.clone())
        .or_else(|| execution.and_then(|artifact| artifact.source_run_id.clone()))
}

fn consumed_analyze_context_for_update(
    state_dir: &str,
    symbol: &str,
    pending: Option<&PendingUpdateArtifact>,
    execution: Option<&ExecutionCandidateArtifact>,
) -> Result<ConsumedAnalyzeContext> {
    if let Some(pending) = pending {
        if pending.pre_bayes_evidence_filter.is_some()
            || pending.pre_bayes_entry_quality_bridge.is_some()
            || !pending.multi_timeframe_summary.is_empty()
        {
            return Ok(ConsumedAnalyzeContext {
                analyze_run_id: pending.source_run_id.clone(),
                pre_bayes_evidence_filter: pending.pre_bayes_evidence_filter.clone(),
                pre_bayes_entry_quality_bridge: pending.pre_bayes_entry_quality_bridge.clone(),
                multi_timeframe_summary: pending.multi_timeframe_summary.clone(),
            });
        }
    }
    if let Some(execution) = execution {
        if execution.pre_bayes_evidence_filter.is_some()
            || execution.pre_bayes_entry_quality_bridge.is_some()
            || !execution.multi_timeframe_summary.is_empty()
        {
            return Ok(ConsumedAnalyzeContext {
                analyze_run_id: execution.source_run_id.clone(),
                pre_bayes_evidence_filter: execution.pre_bayes_evidence_filter.clone(),
                pre_bayes_entry_quality_bridge: execution.pre_bayes_entry_quality_bridge.clone(),
                multi_timeframe_summary: execution.multi_timeframe_summary.clone(),
            });
        }
    }
    let Some(run_id) = source_analyze_run_id_from_artifacts(pending, execution) else {
        return Ok(ConsumedAnalyzeContext::default());
    };
    let analyze_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let Some(run) = analyze_runs.iter().rev().find(|run| run.run_id == run_id) else {
        return Ok(ConsumedAnalyzeContext {
            analyze_run_id: Some(run_id),
            ..ConsumedAnalyzeContext::default()
        });
    };
    Ok(ConsumedAnalyzeContext {
        analyze_run_id: Some(run.run_id.clone()),
        pre_bayes_evidence_filter: Some(run.pre_bayes_evidence_filter.clone()),
        pre_bayes_entry_quality_bridge: Some(run.pre_bayes_entry_quality_bridge.clone()),
        multi_timeframe_summary: run.multi_timeframe_summary.clone(),
    })
}

fn persist_live_data_source(
    state_dir: &str,
    symbol: &str,
    timestamp: chrono::DateTime<Utc>,
    futures_backend: &str,
    aux_backend: &str,
    futures_base_url: &str,
    aux_base_url: &str,
    futures_symbol: &str,
    spot_symbol: &str,
    options_symbol: &str,
    spot_kind: &str,
    htf: &[Candle],
    h4: &[Candle],
    mtf: &[Candle],
    m5: &[Candle],
    ltf: &[Candle],
    m1: &[Candle],
    spot_candles: &[Candle],
) -> Result<LiveDataSourceProvenance> {
    let stamp = timestamp.format("%Y%m%dT%H%M%S").to_string();
    Ok(LiveDataSourceProvenance {
        futures_backend: futures_backend.to_string(),
        aux_backend: aux_backend.to_string(),
        futures_base_url: futures_base_url.to_string(),
        aux_base_url: aux_base_url.to_string(),
        futures_symbol: futures_symbol.to_string(),
        spot_symbol: spot_symbol.to_string(),
        options_symbol: options_symbol.to_string(),
        spot_kind: spot_kind.to_string(),
        fetched_at: timestamp,
        persisted_htf_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_htf.json", stamp),
            htf,
        )?),
        persisted_h4_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_h4.json", stamp),
            h4,
        )?),
        persisted_mtf_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_mtf.json", stamp),
            mtf,
        )?),
        persisted_m5_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_m5.json", stamp),
            m5,
        )?),
        persisted_ltf_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_ltf.json", stamp),
            ltf,
        )?),
        persisted_m1_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_m1.json", stamp),
            m1,
        )?),
        persisted_spot_path: Some(persist_candle_snapshot(
            state_dir,
            symbol,
            &format!("analyze_live_{}_spot.json", stamp),
            spot_candles,
        )?),
    })
}

fn analyze_live_command(
    symbol: &str,
    futures_symbol: Option<&str>,
    spot_symbol: Option<&str>,
    options_symbol: Option<&str>,
    spot_kind: Option<&str>,
    futures_backend: &str,
    aux_backend: &str,
    futures_base_url: &str,
    aux_base_url: &str,
    state_dir: &str,
) -> Result<()> {
    let inferred = match symbol.to_ascii_uppercase().as_str() {
        "NQ" => Some(("NQ=F", "QQQ", "QQQ", "equity")),
        "ES" => Some(("ES=F", "SPY", "SPY", "equity")),
        "YM" => Some(("YM=F", "DIA", "DIA", "equity")),
        "GC" => Some(("GC=F", "GLD", "GLD", "etf")),
        "CL" => Some(("CL=F", "USO", "USO", "etf")),
        _ => None,
    };
    let futures_symbol = futures_symbol
        .or_else(|| inferred.map(|item| item.0))
        .ok_or_else(|| anyhow!("missing live futures_symbol for symbol '{}'", symbol))?;
    let spot_symbol = spot_symbol
        .or_else(|| inferred.map(|item| item.1))
        .ok_or_else(|| anyhow!("missing live spot_symbol for symbol '{}'", symbol))?;
    let options_symbol = options_symbol
        .or_else(|| inferred.map(|item| item.2))
        .unwrap_or(spot_symbol);
    let spot_kind_raw = spot_kind
        .or_else(|| inferred.map(|item| item.3))
        .unwrap_or("equity");
    let spot_kind_label = spot_kind_raw.to_string();
    let spot_kind = SpotInstrumentKind::parse(spot_kind_raw)?;
    let futures_backend = LiveDataBackend::parse(futures_backend)?;
    let aux_backend = LiveDataBackend::parse(aux_backend)?;
    let futures_provider = build_live_data_source(futures_backend, futures_base_url);
    let aux_provider = build_live_data_source(aux_backend, aux_base_url);
    let now = Utc::now();

    let htf = futures_provider.fetch_futures_candles(
        futures_symbol,
        "1d",
        now - Duration::days(420),
        now,
    )?;
    let mtf = futures_provider.fetch_futures_candles(
        futures_symbol,
        "1h",
        now - Duration::days(120),
        now,
    )?;
    let ltf = futures_provider.fetch_futures_candles(
        futures_symbol,
        "15m",
        now - Duration::days(45),
        now,
    )?;
    let htf_4h = futures_provider.fetch_futures_candles(
        futures_symbol,
        "4h",
        now - Duration::days(420),
        now,
    )?;
    let ltf_5m = futures_provider.fetch_futures_candles(
        futures_symbol,
        "5m",
        now - Duration::days(21),
        now,
    )?;
    let ltf_1m = futures_provider.fetch_futures_candles(
        futures_symbol,
        "1m",
        now - Duration::days(7),
        now,
    )?;
    let live_multi_timeframe_summary = build_live_multi_timeframe_summary(
        "live_futures_multi_timeframe",
        &[
            ("1m", &ltf_1m),
            ("5m", &ltf_5m),
            ("15m", &ltf),
            ("1h", &mtf),
            ("4h", &htf_4h),
            ("1d", &htf),
        ],
    );
    let live_multi_timeframe_signal = build_live_multi_timeframe_signal(&[
        ("1m", &ltf_1m),
        ("5m", &ltf_5m),
        ("15m", &ltf),
        ("1h", &mtf),
        ("4h", &htf_4h),
        ("1d", &htf),
    ]);
    let analyze_multi_timeframe_summary = live_multi_timeframe_summary
        .iter()
        .cloned()
        .chain(live_multi_timeframe_signal.summary.iter().cloned())
        .collect::<Vec<_>>();

    let (spot_interval, spot_lookback_days) = match spot_kind {
        SpotInstrumentKind::Commodity => ("1d", 420),
        SpotInstrumentKind::Equity | SpotInstrumentKind::Index => ("15m", 45),
    };
    let futures_live_price = futures_provider
        .fetch_futures_last_price(futures_symbol)
        .ok();
    let spot_candles = aux_provider.fetch_spot_candles(
        spot_kind,
        spot_symbol,
        Some(spot_interval),
        now - Duration::days(spot_lookback_days),
        now,
    )?;
    let spot_live_price = aux_provider
        .fetch_spot_last_price(spot_kind, spot_symbol)
        .ok();
    let options_summary = aux_provider
        .fetch_options_chain_summary(options_symbol)
        .unwrap_or_else(|_| neutral_options_summary(options_symbol));

    let auxiliary = aux_provider.build_auxiliary_evidence(
        spot_kind,
        spot_symbol,
        options_symbol,
        &ltf,
        &spot_candles,
        &options_summary,
    );
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let learning_state = load_learning_state(state_dir, symbol)?;
    let mut report = build_analyze_report(
        symbol,
        state_dir,
        &htf,
        &mtf,
        &ltf,
        &params,
        &network,
        AnalyzeBuildContext {
            symbol,
            paired_candles: Some(&spot_candles),
            auxiliary: Some(&auxiliary),
            learning_state: &learning_state,
            multi_timeframe_summary: &analyze_multi_timeframe_summary,
            native_frames: AnalyzeNativeFrames {
                d1: Some(&htf),
                h4: Some(&htf_4h),
                h1: Some(&mtf),
                m15: Some(&ltf),
                m5: Some(&ltf_5m),
                m1: Some(&ltf_1m),
            },
        },
    )?;

    let trade_outcome_states = &network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?
        .states;
    let long_adjusted = aux_provider.apply_auxiliary_evidence_to_outcome(
        &distribution_from_map(trade_outcome_states, &report.supporting.trade_outcome.long),
        auxiliary.long_bias - auxiliary.short_bias * 0.5,
        auxiliary.uncertainty_penalty,
    );
    let short_adjusted = aux_provider.apply_auxiliary_evidence_to_outcome(
        &distribution_from_map(trade_outcome_states, &report.supporting.trade_outcome.short),
        auxiliary.short_bias - auxiliary.long_bias * 0.5,
        auxiliary.uncertainty_penalty,
    );

    let fvgs = find_unfilled_fvgs(&mtf);
    let obs = find_untested_obs(&mtf);
    let live_decision = probabilistic_decision_snapshot(
        &report.supporting.model_state.regime_probs,
        &report.supporting.raw_trade_plan.cascade_bull,
        &report.supporting.raw_trade_plan.cascade_bear,
        &long_adjusted,
        &short_adjusted,
    );
    let mut live_trade_plan = generate_probabilistic_trade_plan(
        &mtf,
        &ltf,
        &fvgs,
        &obs,
        symbol,
        report.supporting.model_state.regime_probs,
        &report.supporting.raw_trade_plan.cascade_bull,
        &report.supporting.raw_trade_plan.cascade_bear,
        &long_adjusted,
        &short_adjusted,
        &ProbabilisticPlanConfig::default(),
    );
    live_trade_plan
        .uncertainties
        .extend(auxiliary.notes.iter().cloned());

    let live_data_source = persist_live_data_source(
        state_dir,
        symbol,
        report.timestamp,
        futures_backend.as_str(),
        aux_backend.as_str(),
        futures_base_url,
        aux_base_url,
        futures_symbol,
        spot_symbol,
        options_symbol,
        &spot_kind_label,
        &htf,
        &htf_4h,
        &mtf,
        &ltf_5m,
        &ltf,
        &ltf_1m,
        &spot_candles,
    )?;
    report.supporting.multi_timeframe_summary.extend(
        [
            live_data_source
                .persisted_h4_path
                .as_ref()
                .map(|path| format!("persisted_4h_path={}", path)),
            live_data_source
                .persisted_m5_path
                .as_ref()
                .map(|path| format!("persisted_5m_path={}", path)),
            live_data_source
                .persisted_m1_path
                .as_ref()
                .map(|path| format!("persisted_1m_path={}", path)),
        ]
        .into_iter()
        .flatten(),
    );
    report.meta.data_source = Some(live_data_source.clone());
    report.supporting.auxiliary = Some(auxiliary);
    report.supporting.model_state.evidence_policy =
        "hmm_prior_times_pre_bayes_evidence_filter_times_bbn_trade_probability_plus_spot_options_auxiliary"
            .to_string();
    report.supporting.decision = live_decision;
    report.supporting.trade_outcome.long = probability_map(trade_outcome_states, &long_adjusted);
    report.supporting.trade_outcome.short = probability_map(trade_outcome_states, &short_adjusted);
    report.supporting.raw_trade_plan = live_trade_plan;
    report.analysis.technical_price = build_technical_price_section(
        &ltf,
        futures_live_price,
        spot_live_price,
        report.supporting.auxiliary.as_ref(),
    );
    report.analysis.smt_correlation = build_smt_correlation_section(
        futures_symbol,
        spot_symbol,
        &ltf,
        &spot_candles,
        report.supporting.auxiliary.as_ref().unwrap(),
    );
    report.analysis.regime_bayesian = build_regime_bayesian_section(
        &report.supporting.model_state.hmm_state,
        &report.supporting.model_state.regime_probs,
        &report.supporting.labels.regime_label,
        &report.supporting.labels.liquidity_label,
        &report.supporting.decision,
        &report.supporting.model_state.evidence_policy,
        Some(&report.analysis.technical_price.options_hedging),
    );
    report.analysis.multi_timeframe = build_analyze_multi_timeframe_section(
        &report.supporting.multi_timeframe_summary,
        Some(&report.supporting.pre_bayes_evidence_filter),
    );
    report.analysis.trade_plan = build_trade_plan_section(
        &report.supporting.raw_trade_plan,
        Some(&report.analysis.technical_price.options_hedging),
    );
    let pending_update_file =
        persist_pending_update_artifact_from_analyze(state_dir, &report, "analyze-live")?;
    let _execution_candidate_file =
        persist_execution_candidate_from_analyze(state_dir, &report, "analyze-live")?;
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    augment_action_plan_with_artifact_trends(
        &mut report.supporting.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.supporting.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.supporting.artifact_decision_summary =
        artifact_decision_summary_for_symbol(state_dir, symbol)?;
    report.supporting.artifact_decision_section = artifact_decision_section_from_parts(
        &report.supporting.artifact_decision_summary,
        &report.supporting.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    apply_command_context_to_analyze_report(
        &mut report,
        &CommandContext {
            symbol: symbol.to_string(),
            state_dir: state_dir.to_string(),
            analyze: Some(AnalyzeCommandSource::Live {
                source: live_data_source.clone(),
            }),
            research_data: live_data_source.persisted_ltf_path.clone(),
            paired_data: live_data_source.persisted_spot_path.clone(),
            update_outcome: None,
            update_entry_signal: None,
            update_feedback_file: Some(pending_update_file),
            user_data_selection_required: true,
        },
    );
    report.supporting.workflow_snapshot = persist_analyze_run(
        state_dir,
        &report,
        "analyze-live",
        None,
        None,
        None,
        Some(live_data_source),
    )?;
    report.supporting.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.supporting.workflow_snapshot,
        &report.supporting.artifact_action_summary,
    );
    report.supporting.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.supporting.workflow_snapshot);
    append_artifact_decision_prompt(
        &mut report.supporting.agent_prompts,
        symbol,
        &report.supporting.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.supporting.artifact_decision_summary,
        &mut report.supporting.promotion_decision,
        &mut report.supporting.rollback_recommendation,
    );

    emit_analyze_live_output(&report)
}

fn emit_analyze_live_output(report: &AnalyzeReport) -> Result<()> {
    let source_snapshot = report
        .meta
        .data_source
        .as_ref()
        .map(|source| build_source_snapshot(source, report.timestamp));
    let freshness_gate = report.meta.data_source.as_ref().map(|source| {
        build_decision_freshness_gate(
            300,
            report
                .timestamp
                .signed_duration_since(source.fetched_at)
                .num_seconds(),
        )
    });
    let compact_report = build_compact_analyze_report(
        report.supporting.decision_hint.clone(),
        &report.supporting.multi_timeframe_summary,
        &report.supporting.artifact_action_summary,
        &[report.supporting.recommended_next_command.clone()],
    );
    let agent_report = build_agent_guidance_report(
        report.supporting.workflow_state.reason.clone(),
        &report.supporting.multi_timeframe_summary,
        &report.supporting.artifact_action_summary,
        &[report.supporting.recommended_next_command.clone()],
        &[],
    );
    let human_market_family = report
        .supporting
        .canonical_belief_report
        .market_family
        .as_deref();
    let human_market_subgraph = report
        .supporting
        .canonical_belief_report
        .selected_market_subgraph
        .as_deref()
        .unwrap_or("unknown");
    let human_report = build_human_analyze_report(
        match human_market_family {
            Some("metals") => format!(
                "金属结构偏向：{}。这类盘先看流动性是否被扫完，再等回到顺势一侧；原始标签={}。",
                if report.analysis.regime_bayesian.selected_direction == Direction::Bull {
                    "偏多，但不宜追"
                } else if report.analysis.regime_bayesian.selected_direction == Direction::Bear {
                    "偏空，但更重确认"
                } else {
                    "先观望，等再定向"
                },
                report.analysis.price_action.narrative
            ),
            Some("energy") => format!(
                "能源结构偏向：{}。这类盘最怕突发冲击，先防假突破和急反转；原始标签={}。",
                if report.analysis.regime_bayesian.selected_direction == Direction::Bear {
                    "空头占优，但随时防剧烈反抽"
                } else if report.analysis.regime_bayesian.selected_direction == Direction::Bull {
                    "多头占优，但别忽视突发回吐"
                } else {
                    "方向未完全站稳，先等波动收敛"
                },
                report.analysis.price_action.narrative
            ),
            _ => report.analysis.price_action.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属技术面：更重均值回归后的二次确认，别把一次拉伸当延续；原始标签={}。",
                report.analysis.technical_price.narrative
            ),
            Some("energy") => format!(
                "能源技术面：指标易被波动放大，先看节奏是否稳定，再看趋势是否继续；原始标签={}。",
                report.analysis.technical_price.narrative
            ),
            _ => report.analysis.technical_price.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属联动面：相关性可参考，但最终仍以本品种流动性反应为主；原始标签={}。",
                report.analysis.smt_correlation.narrative
            ),
            Some("energy") => format!(
                "能源联动面：相关市场常会同步放大波动，若联动发散，先减信号强度；原始标签={}。",
                report.analysis.smt_correlation.narrative
            ),
            _ => report.analysis.smt_correlation.narrative.clone(),
        },
        match human_market_family {
            Some("metals") => format!(
                "金属品种视角：regime={} liquidity={} direction={:?}。现属防御型流动性环境，先看扫流动性后是否回到顺势确认；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            Some("energy") => format!(
                "能源品种视角：regime={} liquidity={} direction={:?}。当前更该尊重波动冲击与状态切换，先防急拉急杀再谈延续；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            Some("futures_index") => format!(
                "股指品种视角：regime={} liquidity={} direction={:?}。先看 beta 与多周期共振是否同向，再决定是否执行；subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
            _ => format!(
                "regime={} liquidity={} direction={:?} subgraph={}",
                report.analysis.regime_bayesian.regime_label,
                report.analysis.regime_bayesian.liquidity_label,
                report.analysis.regime_bayesian.selected_direction,
                human_market_subgraph
            ),
        },
        report.analysis.trade_plan.narrative.clone(),
    );
    let policy_record = load_pre_bayes_policy_history(&report.meta.state_dir, &report.symbol)?
        .into_iter()
        .last();
    let belief_shadow_policy = build_belief_shadow_policy_surface(
        &report.supporting.canonical_belief_report,
        policy_record.as_ref(),
    );
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "source_snapshot": source_snapshot,
            "freshness_gate": freshness_gate,
            "compact_report": compact_report,
            "agent_report": agent_report,
            "human_report": human_report.render(),
            "belief_shadow_policy": belief_shadow_policy,
        }))?
    );
    Ok(())
}

fn persist_analyze_run(
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
    let analyze_ensemble_vote = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
        symbol: report.symbol.clone(),
        state_dir: Some(state_dir.to_string()),
        recommended_next_command: report.supporting.recommended_next_command.clone(),
        provenance: report.supporting.provenance.clone(),
        dataset_comparability: report.supporting.dataset_comparability.clone(),
        belief: report.supporting.canonical_belief_report.clone(),
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

fn persist_pending_update_artifact_from_analyze(
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
        ..build_feedback_record(
            &report.symbol,
            source_phase,
            report.timestamp,
            &report.supporting.factor_diagnostics,
            &report.supporting.decision,
            0.0,
            "pending".to_string(),
            report.supporting.model_state.regime_probs.dominant(),
        )
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

fn pending_update_artifact_diff(
    previous: &PendingUpdateArtifact,
    current: &PendingUpdateArtifact,
) -> PendingUpdateArtifactDiff {
    let mut changed_fields = Vec::new();
    if previous.entry_quality != current.entry_quality {
        changed_fields.push("entry_quality".to_string());
    }
    if previous.factor_alignment != current.factor_alignment {
        changed_fields.push("factor_alignment".to_string());
    }
    if previous.factor_uncertainty != current.factor_uncertainty {
        changed_fields.push("factor_uncertainty".to_string());
    }
    if previous
        .template_feedback
        .model_probabilities_before_trade
        .selected_direction
        != current
            .template_feedback
            .model_probabilities_before_trade
            .selected_direction
    {
        changed_fields.push("selected_direction".to_string());
    }
    if previous.provenance.data_fingerprint != current.provenance.data_fingerprint {
        changed_fields.push("data_fingerprint".to_string());
    }
    if previous.provenance.factor_version != current.provenance.factor_version {
        changed_fields.push("factor_version".to_string());
    }
    let comparable_same_data =
        previous.provenance.data_fingerprint == current.provenance.data_fingerprint;
    let comparable_same_factor_version =
        previous.provenance.factor_version == current.provenance.factor_version;
    let comparable_same_prompt_version =
        previous.provenance.prompt_version == current.provenance.prompt_version;
    let selected_probability_delta =
        current.selected_win_probability - previous.selected_win_probability;
    let top_factor_score_delta = current.top_factor_score - previous.top_factor_score;
    let avg_family_score_delta = current.avg_family_score - previous.avg_family_score;
    let quality_delta =
        pending_update_quality_score(current) - pending_update_quality_score(previous);
    PendingUpdateArtifactDiff {
        previous_artifact_id: Some(previous.artifact_id.clone()),
        exact_duplicate: changed_fields.is_empty(),
        changed_fields,
        quality_delta,
        comparable_same_data,
        comparable_same_factor_version,
        comparable_same_prompt_version,
        selected_probability_delta,
        top_factor_score_delta,
        avg_family_score_delta,
    }
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
    } else if !((!rules.require_same_data || current.diff_from_previous.comparable_same_data)
        && (!rules.require_same_factor_version
            || current.diff_from_previous.comparable_same_factor_version)
        && (!rules.require_same_prompt_version
            || current.diff_from_previous.comparable_same_prompt_version))
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

fn pending_update_quality_score(artifact: &PendingUpdateArtifact) -> i32 {
    let entry_quality = match artifact.entry_quality.as_str() {
        "high" => 3,
        "medium" => 2,
        "low" => 1,
        _ => 0,
    };
    let alignment = match artifact.factor_alignment.as_str() {
        "bullish" | "bearish" => 2,
        "mixed" => 1,
        _ => 0,
    };
    let uncertainty = match artifact.factor_uncertainty.as_str() {
        "low" => 2,
        "high" => 0,
        _ => 1,
    };
    let probability = (artifact
        .template_feedback
        .model_probabilities_before_trade
        .selected_probability
        * 100.0)
        .round() as i32;
    entry_quality * 100 + alignment * 10 + uncertainty * 5 + probability
}

fn feedback_record_from_artifact(
    artifact: PendingUpdateArtifact,
    outcome_label: &str,
    pnl: Option<f64>,
    regime: Option<&str>,
    direction: Option<&str>,
) -> FeedbackRecord {
    let mut feedback = artifact.template_feedback;
    feedback.realized_outcome = outcome_label.to_string();
    feedback.pnl = pnl.unwrap_or_else(|| match outcome_label {
        "win" => 0.01,
        "loss" => -0.01,
        _ => 0.0,
    });
    if let Some(regime) = regime {
        feedback.regime_at_entry = normalize_regime_label(regime);
    }
    if let Some(direction) = direction {
        feedback.model_probabilities_before_trade.selected_direction =
            normalize_direction_label(direction);
    }
    feedback
}

fn execution_candidate_artifact_diff(
    previous: &ExecutionCandidateArtifact,
    current: &ExecutionCandidateArtifact,
) -> ExecutionCandidateArtifactDiff {
    let mut changed_fields = Vec::new();
    if previous.selected_direction != current.selected_direction {
        changed_fields.push("selected_direction".to_string());
    }
    if previous.trade_direction != current.trade_direction {
        changed_fields.push("trade_direction".to_string());
    }
    if previous.actionable != current.actionable {
        changed_fields.push("actionable".to_string());
    }
    if previous.factor_alignment != current.factor_alignment {
        changed_fields.push("factor_alignment".to_string());
    }
    if previous.factor_uncertainty != current.factor_uncertainty {
        changed_fields.push("factor_uncertainty".to_string());
    }
    if previous.provenance.data_fingerprint != current.provenance.data_fingerprint {
        changed_fields.push("data_fingerprint".to_string());
    }
    if previous.provenance.factor_version != current.provenance.factor_version {
        changed_fields.push("factor_version".to_string());
    }
    ExecutionCandidateArtifactDiff {
        previous_artifact_id: Some(previous.artifact_id.clone()),
        posterior_delta: current.posterior - previous.posterior,
        win_probability_delta: current.win_probability - previous.win_probability,
        entry_delta: current.entry - previous.entry,
        exact_duplicate: changed_fields.is_empty(),
        changed_fields,
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

fn persist_execution_candidate_from_analyze(
    state_dir: &str,
    report: &AnalyzeReport,
    source_phase: &str,
) -> Result<String> {
    let rules = artifact_review_rules().execution_candidate;
    let review_rule_version = execution_candidate_review_rule_version(&rules);
    let history = load_execution_candidate_history(state_dir, &report.symbol)?;
    let version = history.len() + 1;
    let trade_plan = &report.supporting.raw_trade_plan;
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
        selected_direction: report.supporting.decision.selected_direction,
        trade_direction: trade_plan.direction,
        actionable: trade_plan.direction != Direction::Neutral && trade_plan.position_size > 0.0,
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
        candidate_status: if trade_plan.direction != Direction::Neutral
            && trade_plan.position_size > 0.0
        {
            "ready".to_string()
        } else {
            "no_trade".to_string()
        },
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
        artifact.review_decision = execution_candidate_artifact_decision(previous, &artifact);
    } else {
        artifact.review_decision = ExecutionCandidateArtifactDecision {
            status: if artifact.actionable {
                "promote_latest".to_string()
            } else {
                "observe".to_string()
            },
            reason: "first_execution_candidate_artifact".to_string(),
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
fn build_ensemble_vote_record(
    symbol: &str,
    source_phase: &str,
    source_run_id: Option<String>,
    provenance: &RunProvenance,
    dataset_comparability: &DatasetComparability,
    ensemble_vote: &ict_engine::application::orchestration::EnsembleVoteArtifact,
    compatibility_scorecards: &[EnsembleExecutorScorecard],
) -> EnsembleVoteRecord {
    EnsembleVoteRecord {
        artifact_id: format!(
            "ensemble-vote:{}:{}",
            source_phase,
            Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
        ),
        generated_at: Utc::now(),
        symbol: symbol.to_string(),
        source_phase: source_phase.to_string(),
        source_run_id,
        provenance: provenance.clone(),
        dataset_comparability: dataset_comparability.clone(),
        ensemble_version: ensemble_vote.ensemble_version.clone(),
        final_action: ensemble_vote.final_action.clone(),
        recommended_command: ensemble_vote.recommended_command.clone(),
        human_next_triage: ensemble_vote.human_next_triage.clone(),
        confidence: ensemble_vote.confidence,
        consensus_strength: ensemble_vote.consensus_strength,
        disagreement_flags: ensemble_vote.disagreement_flags.clone(),
        executor_summaries: ensemble_vote.executor_summaries.clone(),
        split_explanations: ensemble_vote.split_explanations.clone(),
        executor_scorecards: compatibility_scorecards.to_vec(),
        executor_scorecards_source: Some("persisted".to_string()),
        posterior_fingerprint: ensemble_vote.posterior.fingerprint.clone(),
        posterior_normalization_status: ensemble_vote.posterior.normalization_status.clone(),
        posterior_active_regime: ensemble_vote.posterior.active_regime.clone(),
        posterior_confidence: ensemble_vote.posterior.confidence,
        posterior_probabilities: ensemble_vote.posterior.probabilities.clone(),
        posterior_evidence: ensemble_vote.posterior.evidence.clone(),
    }
}

fn persist_ensemble_vote_record(
    state_dir: &str,
    record: &EnsembleVoteRecord,
    canonical_scorecards: &[EnsembleExecutorScorecard],
) -> Result<()> {
    append_artifact_ledger_entry(
        state_dir,
        &record.symbol,
        ArtifactLedgerEntry {
            entry_id: format!("ledger:{}", record.artifact_id),
            artifact_kind: "ensemble_vote".to_string(),
            artifact_id: record.artifact_id.clone(),
            version: 1,
            generated_at: record.generated_at,
            symbol: record.symbol.clone(),
            source_phase: record.source_phase.clone(),
            source_run_id: record.source_run_id.clone(),
            path: std::path::Path::new(state_dir)
                .join(&record.symbol)
                .join(ENSEMBLE_VOTE_FILE)
                .to_string_lossy()
                .to_string(),
            status: if record.disagreement_flags.is_empty() {
                "consensus".to_string()
            } else {
                "mixed".to_string()
            },
            promote_candidate: record.confidence >= 0.60 && record.disagreement_flags.is_empty(),
            actionable: true,
            decision_hint: record.final_action.clone(),
            review_reason: record.human_next_triage.clone(),
            review_rule_version: record.ensemble_version.clone(),
            top_factor_name: None,
            top_factor_action: Some(record.final_action.clone()),
            family_scores: BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: ((record.confidence + record.consensus_strength) * 50.0) as i32,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        },
    )?;
    save_ensemble_vote_artifact(state_dir, &record.symbol, record)?;
    save_ensemble_executor_scorecards(state_dir, &record.symbol, canonical_scorecards)?;
    append_ensemble_vote_history(state_dir, &record.symbol, record.clone())?;
    Ok(())
}

fn latest_execution_candidate_for_source_run(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Option<ExecutionCandidateArtifact>> {
    let Some(source_run_id) = source_run_id else {
        return Ok(None);
    };
    Ok(load_execution_candidate_history(state_dir, symbol)?
        .into_iter()
        .rev()
        .find(|artifact| artifact.source_run_id.as_deref() == Some(source_run_id)))
}

fn latest_ensemble_vote_for_source_run(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Option<EnsembleVoteRecord>> {
    let Some(source_run_id) = source_run_id else {
        return Ok(None);
    };
    Ok(load_ensemble_vote_history(state_dir, symbol)?
        .into_iter()
        .rev()
        .find(|artifact| artifact.source_run_id.as_deref() == Some(source_run_id)))
}

fn derive_executor_scorecards_from_summaries(
    executor_summaries: &[String],
) -> Vec<EnsembleExecutorScorecard> {
    executor_summaries
        .iter()
        .map(|summary| EnsembleExecutorScorecard {
            executor: summary
                .split_whitespace()
                .find_map(|part| part.strip_prefix("executor="))
                .unwrap_or("executor_unavailable")
                .to_string(),
            latest_weight_hint: summary
                .split_whitespace()
                .find_map(|part| part.strip_prefix("weight="))
                .and_then(|value| value.parse::<f64>().ok()),
            ..EnsembleExecutorScorecard::default()
        })
        .collect()
}

fn load_canonical_executor_scorecards(
    state_dir: &str,
    symbol: &str,
    source_run_id: Option<&str>,
) -> Result<Vec<EnsembleExecutorScorecard>> {
    let persisted = load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    if !persisted.is_empty() {
        return Ok(persisted);
    }
    Ok(
        latest_ensemble_vote_for_source_run(state_dir, symbol, source_run_id)?
            .map(|artifact| {
                if artifact.executor_scorecards.is_empty() {
                    derive_executor_scorecards_from_summaries(&artifact.executor_summaries)
                } else {
                    artifact.executor_scorecards
                }
            })
            .unwrap_or_default(),
    )
}

fn apply_update_outcome_to_executor_scorecards(
    scorecards: &mut [EnsembleExecutorScorecard],
    realized_outcome: &str,
    quality_adjustment: i64,
) {
    for scorecard in scorecards {
        match realized_outcome {
            "win" => scorecard.wins += 1,
            "loss" => scorecard.losses += 1,
            _ => scorecard.breakevens += 1,
        }
        match realized_outcome {
            "win" => scorecard.validated_positive += 1,
            "loss" => scorecard.validated_negative += 1,
            _ => {}
        }
        scorecard.cumulative_quality_score += quality_adjustment;
        scorecard.last_outcome = Some(realized_outcome.to_string());
        scorecard.last_updated_at = Some(Utc::now());
    }
}

fn pending_update_artifact_by_id(
    state_dir: &str,
    symbol: &str,
    artifact_id: &str,
) -> Result<PendingUpdateArtifact> {
    load_pending_update_history(state_dir, symbol)?
        .into_iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .ok_or_else(|| anyhow!("unknown pending_update artifact '{}'", artifact_id))
}

fn execution_candidate_artifact_by_id(
    state_dir: &str,
    symbol: &str,
    artifact_id: &str,
) -> Result<ExecutionCandidateArtifact> {
    load_execution_candidate_history(state_dir, symbol)?
        .into_iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .ok_or_else(|| anyhow!("unknown execution_candidate artifact '{}'", artifact_id))
}

fn artifact_diff_view_for_pending_update(
    ledger: &[ArtifactLedgerEntry],
    state_dir: &str,
    symbol: &str,
    left_artifact_id: &str,
    right_artifact_id: &str,
) -> Result<ArtifactDiffView> {
    let left = pending_update_artifact_by_id(state_dir, symbol, left_artifact_id)?;
    let right = pending_update_artifact_by_id(state_dir, symbol, right_artifact_id)?;
    let diff = pending_update_artifact_diff(&left, &right);
    let lineage_artifact_ids = artifact_lineage_path(ledger, left_artifact_id, right_artifact_id);
    Ok(ArtifactDiffView {
        kind: "pending_update".to_string(),
        left_artifact_id: left.artifact_id,
        right_artifact_id: right.artifact_id,
        changed_fields: diff.changed_fields,
        numeric_evidence: vec![
            format!(
                "selected_probability_delta={:.4}",
                diff.selected_probability_delta
            ),
            format!("top_factor_score_delta={:.4}", diff.top_factor_score_delta),
            format!("avg_family_score_delta={:.4}", diff.avg_family_score_delta),
            format!("quality_delta={}", diff.quality_delta),
        ],
        embedded_pre_bayes_evidence: artifact_embedded_pre_bayes_evidence(
            left.pre_bayes_evidence_filter.as_ref(),
            right.pre_bayes_evidence_filter.as_ref(),
            left.pre_bayes_entry_quality_bridge.as_ref(),
            right.pre_bayes_entry_quality_bridge.as_ref(),
            &left.multi_timeframe_summary,
            &right.multi_timeframe_summary,
        ),
        summary: format!(
            "same_data={} same_factor_version={} same_prompt_version={}",
            diff.comparable_same_data,
            diff.comparable_same_factor_version,
            diff.comparable_same_prompt_version
        ),
        cross_rule_version_summary: (left.review_rule_version != right.review_rule_version).then(
            || {
                format!(
                    "rule_version_changed:{}->{} quality_delta={} probability_delta={:.4}",
                    left.review_rule_version,
                    right.review_rule_version,
                    diff.quality_delta,
                    diff.selected_probability_delta
                )
            },
        ),
        lineage_artifact_ids: lineage_artifact_ids.clone(),
        lineage_numeric_evidence: artifact_lineage_numeric_evidence(ledger, &lineage_artifact_ids),
    })
}

fn artifact_diff_view_for_execution_candidate(
    ledger: &[ArtifactLedgerEntry],
    state_dir: &str,
    symbol: &str,
    left_artifact_id: &str,
    right_artifact_id: &str,
) -> Result<ArtifactDiffView> {
    let left = execution_candidate_artifact_by_id(state_dir, symbol, left_artifact_id)?;
    let right = execution_candidate_artifact_by_id(state_dir, symbol, right_artifact_id)?;
    let diff = execution_candidate_artifact_diff(&left, &right);
    let lineage_artifact_ids = artifact_lineage_path(ledger, left_artifact_id, right_artifact_id);
    Ok(ArtifactDiffView {
        kind: "execution_candidate".to_string(),
        left_artifact_id: left.artifact_id,
        right_artifact_id: right.artifact_id,
        changed_fields: diff.changed_fields,
        numeric_evidence: vec![
            format!("posterior_delta={:.4}", diff.posterior_delta),
            format!("win_probability_delta={:.4}", diff.win_probability_delta),
            format!("entry_delta={:.4}", diff.entry_delta),
        ],
        embedded_pre_bayes_evidence: artifact_embedded_pre_bayes_evidence(
            left.pre_bayes_evidence_filter.as_ref(),
            right.pre_bayes_evidence_filter.as_ref(),
            left.pre_bayes_entry_quality_bridge.as_ref(),
            right.pre_bayes_entry_quality_bridge.as_ref(),
            &left.multi_timeframe_summary,
            &right.multi_timeframe_summary,
        ),
        summary: format!("exact_duplicate={}", diff.exact_duplicate),
        cross_rule_version_summary: (left.review_rule_version != right.review_rule_version).then(
            || {
                format!(
                    "rule_version_changed:{}->{} posterior_delta={:.4} win_probability_delta={:.4}",
                    left.review_rule_version,
                    right.review_rule_version,
                    diff.posterior_delta,
                    diff.win_probability_delta
                )
            },
        ),
        lineage_artifact_ids: lineage_artifact_ids.clone(),
        lineage_numeric_evidence: artifact_lineage_numeric_evidence(ledger, &lineage_artifact_ids),
    })
}

fn artifact_lineage_path(
    ledger: &[ArtifactLedgerEntry],
    left_artifact_id: &str,
    right_artifact_id: &str,
) -> Vec<String> {
    let mut chain = Vec::new();
    let mut current = Some(right_artifact_id.to_string());
    while let Some(artifact_id) = current {
        chain.push(artifact_id.clone());
        if artifact_id == left_artifact_id {
            chain.reverse();
            return chain;
        }
        current = ledger
            .iter()
            .find(|entry| entry.artifact_id == artifact_id)
            .and_then(|entry| entry.supersedes_artifact_id.clone());
    }
    Vec::new()
}

fn artifact_lineage_numeric_evidence(
    ledger: &[ArtifactLedgerEntry],
    lineage_artifact_ids: &[String],
) -> Vec<String> {
    if lineage_artifact_ids.len() < 2 {
        return Vec::new();
    }
    let entries = lineage_artifact_ids
        .iter()
        .filter_map(|artifact_id| {
            ledger
                .iter()
                .find(|entry| &entry.artifact_id == artifact_id)
        })
        .collect::<Vec<_>>();
    let Some(first) = entries.first() else {
        return Vec::new();
    };
    let Some(last) = entries.last() else {
        return Vec::new();
    };
    vec![
        format!("lineage_steps={}", entries.len()),
        format!(
            "lineage_quality_delta={}",
            last.quality_score - first.quality_score
        ),
        format!(
            "lineage_consumed_entries={}",
            entries
                .iter()
                .filter(|entry| entry.consumed_by_update_run_id.is_some())
                .count()
        ),
    ]
}

fn artifact_embedded_pre_bayes_evidence(
    left_filter: Option<&PreBayesEvidenceFilter>,
    right_filter: Option<&PreBayesEvidenceFilter>,
    left_bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
    right_bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
    left_multi_timeframe_summary: &[String],
    right_multi_timeframe_summary: &[String],
) -> Vec<String> {
    let mut evidence = Vec::new();
    match (left_filter, right_filter) {
        (Some(left), Some(right)) => {
            if left.policy.version != right.policy.version {
                evidence.push(format!(
                    "pre_bayes_policy_version:{}->{}",
                    left.policy.version, right.policy.version
                ));
            }
            if left.gating_status != right.gating_status {
                evidence.push(format!(
                    "pre_bayes_gate_status:{}->{}",
                    left.gating_status, right.gating_status
                ));
            }
            if (left.evidence_quality_score - right.evidence_quality_score).abs() > f64::EPSILON {
                evidence.push(format!(
                    "pre_bayes_quality_delta={:.4}",
                    right.evidence_quality_score - left.evidence_quality_score
                ));
            }
            if left.filtered_multi_timeframe_resonance_label
                != right.filtered_multi_timeframe_resonance_label
            {
                evidence.push(format!(
                    "pre_bayes_resonance:{}->{}",
                    left.filtered_multi_timeframe_resonance_label,
                    right.filtered_multi_timeframe_resonance_label
                ));
            }
        }
        (Some(left), None) => evidence.push(format!(
            "pre_bayes_embedded_left_only gate_status={} policy_version={}",
            left.gating_status, left.policy.version
        )),
        (None, Some(right)) => evidence.push(format!(
            "pre_bayes_embedded_right_only gate_status={} policy_version={}",
            right.gating_status, right.policy.version
        )),
        (None, None) => {}
    }
    match (left_bridge, right_bridge) {
        (Some(left), Some(right)) => {
            let left_diff = pre_bayes_entry_quality_bridge_diff(left);
            let right_diff = pre_bayes_entry_quality_bridge_diff(right);
            if left_diff.selected_entry_quality != right_diff.selected_entry_quality {
                evidence.push(format!(
                    "pre_bayes_bridge_selected_entry_quality:{:?}->{:?}",
                    left_diff.selected_entry_quality, right_diff.selected_entry_quality
                ));
            }
            if (left_diff.long_short_signal_probability_gap
                - right_diff.long_short_signal_probability_gap)
                .abs()
                > f64::EPSILON
            {
                evidence.push(format!(
                    "pre_bayes_bridge_probability_gap_delta={:.4}",
                    right_diff.long_short_signal_probability_gap
                        - left_diff.long_short_signal_probability_gap
                ));
            }
        }
        (Some(_), None) => evidence.push("pre_bayes_bridge_left_only".to_string()),
        (None, Some(_)) => evidence.push("pre_bayes_bridge_right_only".to_string()),
        (None, None) => {}
    }
    if left_multi_timeframe_summary != right_multi_timeframe_summary {
        evidence.push(format!(
            "embedded_multi_timeframe_summary_changed left={:?} right={:?}",
            left_multi_timeframe_summary, right_multi_timeframe_summary
        ));
    }
    evidence
}

fn pending_update_embedded_filter<'a>(
    artifact_id: &str,
    artifacts: &'a [PendingUpdateArtifact],
) -> Option<&'a PreBayesEvidenceFilter> {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .and_then(|artifact| artifact.pre_bayes_evidence_filter.as_ref())
}

fn pending_update_embedded_bridge<'a>(
    artifact_id: &str,
    artifacts: &'a [PendingUpdateArtifact],
) -> Option<&'a ict_engine::state::PreBayesEntryQualityBridge> {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .and_then(|artifact| artifact.pre_bayes_entry_quality_bridge.as_ref())
}

fn pending_update_embedded_mtf<'a>(
    artifact_id: &str,
    artifacts: &'a [PendingUpdateArtifact],
) -> &'a [String] {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .map(|artifact| artifact.multi_timeframe_summary.as_slice())
        .unwrap_or(&[])
}

fn execution_candidate_embedded_filter<'a>(
    artifact_id: &str,
    artifacts: &'a [ExecutionCandidateArtifact],
) -> Option<&'a PreBayesEvidenceFilter> {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .and_then(|artifact| artifact.pre_bayes_evidence_filter.as_ref())
}

fn execution_candidate_embedded_bridge<'a>(
    artifact_id: &str,
    artifacts: &'a [ExecutionCandidateArtifact],
) -> Option<&'a ict_engine::state::PreBayesEntryQualityBridge> {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .and_then(|artifact| artifact.pre_bayes_entry_quality_bridge.as_ref())
}

fn execution_candidate_embedded_mtf<'a>(
    artifact_id: &str,
    artifacts: &'a [ExecutionCandidateArtifact],
) -> &'a [String] {
    artifacts
        .iter()
        .find(|artifact| artifact.artifact_id == artifact_id)
        .map(|artifact| artifact.multi_timeframe_summary.as_slice())
        .unwrap_or(&[])
}

fn embedded_pre_bayes_evidence_for_entry<'a>(
    entry: &'a ArtifactLedgerEntry,
    pending_updates: &'a [PendingUpdateArtifact],
    execution_candidates: &'a [ExecutionCandidateArtifact],
) -> (
    Option<&'a PreBayesEvidenceFilter>,
    Option<&'a ict_engine::state::PreBayesEntryQualityBridge>,
    &'a [String],
) {
    match entry.artifact_kind.as_str() {
        "pending_update" => (
            pending_update_embedded_filter(&entry.artifact_id, pending_updates),
            pending_update_embedded_bridge(&entry.artifact_id, pending_updates),
            pending_update_embedded_mtf(&entry.artifact_id, pending_updates),
        ),
        "execution_candidate" => (
            execution_candidate_embedded_filter(&entry.artifact_id, execution_candidates),
            execution_candidate_embedded_bridge(&entry.artifact_id, execution_candidates),
            execution_candidate_embedded_mtf(&entry.artifact_id, execution_candidates),
        ),
        _ => (None, None, &[]),
    }
}

fn apply_command_context_to_analyze_report(
    report: &mut AnalyzeReport,
    command_context: &CommandContext,
) {
    report.supporting.recommended_commands = command_recommendations(command_context);
    concretize_action_plan_commands(
        &mut report.supporting.agent_action_plan,
        &report.supporting.recommended_commands,
    );
    report.supporting.recommended_next_command = recommended_next_command(
        &report.supporting.agent_action_plan,
        &report.supporting.recommended_commands,
    );
    report.supporting.agent_context_bundle = build_agent_context_bundle(
        &command_context.symbol,
        &command_context.state_dir,
        &report.supporting.workflow_state,
        &report.supporting.decision_hint,
        &report.supporting.recommended_next_command,
        &report.supporting.recommended_commands,
        &report.supporting.dataset_comparability,
        &report.supporting.factor_iteration_queue,
        &report.supporting.factor_family_outcomes,
        Some(&report.supporting.pre_bayes_evidence_filter),
        Some(&report.supporting.pre_bayes_entry_quality_bridge),
        None,
        Some(&report.supporting.artifact_decision_summary),
    );
    report
        .supporting
        .agent_context_bundle
        .multi_timeframe_summary = report.supporting.multi_timeframe_summary.clone();
    report.supporting.agent_context_bundle_minimal =
        build_agent_context_bundle_minimal(&report.supporting.agent_context_bundle);
}

fn refresh_workflow_snapshot(state_dir: &str, symbol: &str) -> Result<WorkflowSnapshot> {
    let analyze_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let train_runs: Vec<TrainRunRecord> =
        load_state_or_default(state_dir, symbol, TRAIN_RUNS_FILE)?;
    let research_runs: Vec<ResearchRunRecord> =
        load_state_or_default(state_dir, symbol, RESEARCH_RUNS_FILE)?;
    let backtest_runs: Vec<BacktestRunRecord> =
        load_state_or_default(state_dir, symbol, BACKTEST_RUNS_FILE)?;
    let update_runs: Vec<UpdateRunRecord> =
        load_state_or_default(state_dir, symbol, UPDATE_RUNS_FILE)?;
    let pre_bayes_policy_history = load_pre_bayes_policy_history(state_dir, symbol)?;
    let pending_update_history = load_pending_update_history(state_dir, symbol)?;
    let execution_candidate_history = load_execution_candidate_history(state_dir, symbol)?;
    let artifact_ledger = load_artifact_ledger(state_dir, symbol)?;

    let snapshot = build_workflow_snapshot(
        state_dir,
        symbol,
        train_runs.last(),
        analyze_runs.last(),
        research_runs.last(),
        backtest_runs.last(),
        update_runs.last(),
        &pre_bayes_policy_history,
        &pending_update_history,
        &execution_candidate_history,
        &artifact_ledger,
    );
    save_workflow_snapshot(state_dir, symbol, &snapshot)?;
    Ok(snapshot)
}

fn build_workflow_snapshot(
    state_dir: &str,
    symbol: &str,
    latest_train: Option<&TrainRunRecord>,
    latest_analyze: Option<&AnalyzeRunRecord>,
    latest_research: Option<&ResearchRunRecord>,
    latest_backtest: Option<&BacktestRunRecord>,
    latest_update: Option<&UpdateRunRecord>,
    pre_bayes_policy_history: &[PreBayesPolicyRecord],
    pending_update_history: &[PendingUpdateArtifact],
    execution_candidate_history: &[ExecutionCandidateArtifact],
    artifact_ledger: &[ArtifactLedgerEntry],
) -> WorkflowSnapshot {
    let train = latest_train.map(workflow_phase_snapshot_from_train_run);
    let analyze = latest_analyze.map(workflow_phase_snapshot_from_analyze_run);
    let research = latest_research.map(workflow_phase_snapshot_from_research_run);
    let backtest = latest_backtest.map(workflow_phase_snapshot_from_backtest_run);
    let update = latest_update.map(workflow_phase_snapshot_from_update_run);
    let field_diffs = workflow_field_diffs(&analyze, &research, &backtest, &update);
    let disagreements = workflow_disagreements(&analyze, &research, &backtest, &update);
    let recent_pending_updates = pending_update_history
        .iter()
        .rev()
        .take(5)
        .map(|artifact| pending_update_summary(state_dir, symbol, artifact))
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>();
    let recent_execution_candidates = execution_candidate_history
        .iter()
        .rev()
        .take(5)
        .map(|artifact| execution_candidate_summary(state_dir, symbol, artifact))
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>();
    let recent_ensemble_votes = load_ensemble_vote_history(state_dir, symbol)
        .unwrap_or_default()
        .into_iter()
        .rev()
        .take(5)
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>();
    let recent_artifacts = artifact_ledger
        .iter()
        .rev()
        .take(10)
        .cloned()
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>();
    let actionable_artifacts = artifact_ledger
        .iter()
        .filter(|entry| entry.actionable && entry.consumed_by_update_run_id.is_none())
        .cloned()
        .collect::<Vec<_>>();
    let latest_promotable_artifact = artifact_ledger
        .iter()
        .filter(|entry| entry.promote_candidate && entry.consumed_by_update_run_id.is_none())
        .max_by_key(|entry| artifact_generated_recency_key(entry))
        .cloned();
    let artifact_history_summary = build_artifact_history_summary(artifact_ledger);
    let artifact_factor_trends =
        build_artifact_factor_trends(artifact_ledger, &research, &backtest, &update);
    let artifact_family_trends =
        build_artifact_family_trends(artifact_ledger, &research, &backtest, &update);
    let review_rules = artifact_review_rules();
    let review_rule_sources = artifact_review_rule_sources();
    let artifact_lineage_summaries = build_artifact_lineage_summaries_with_embedded_snapshots(
        artifact_ledger,
        pending_update_history,
        execution_candidate_history,
    );
    let artifact_consumed_impact_summary = build_artifact_consumed_impact_summary(artifact_ledger);
    let artifact_decision_summary = artifact_decision_summary_from_trends(
        &actionable_artifacts,
        latest_promotable_artifact.as_ref(),
        &artifact_lineage_summaries,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    let latest_pre_bayes_policy =
        latest_analyze.map(|run| run.pre_bayes_evidence_filter.policy.clone());
    let latest_pre_bayes_entry_quality_bridge =
        latest_analyze.map(|run| run.pre_bayes_entry_quality_bridge.clone());
    let latest_pre_bayes_entry_quality_bridge_diff = latest_analyze
        .map(|run| pre_bayes_entry_quality_bridge_diff(&run.pre_bayes_entry_quality_bridge));
    let recent_pre_bayes_policies = pre_bayes_policy_history
        .iter()
        .rev()
        .take(5)
        .cloned()
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect::<Vec<_>>();
    let latest_pre_bayes_policy_diff = recent_pre_bayes_policies
        .last()
        .map(|record| record.diff_from_previous.clone());
    let latest_pre_bayes_policy_lineage = Some(pre_bayes_policy_lineage_summary(
        &recent_pre_bayes_policies,
        latest_analyze
            .map(|run| run.pre_bayes_evidence_filter.gating_status.as_str())
            .unwrap_or(""),
    ));
    let latest_pre_bayes_soft_evidence_diff = latest_analyze
        .map(|run| pre_bayes_soft_evidence_diff(&run.pre_bayes_evidence_filter))
        .unwrap_or_default();
    let artifact_rule_break_effects = build_artifact_rule_break_effects(artifact_ledger);
    let artifact_factor_rule_break_impacts =
        build_artifact_factor_rule_break_impacts(artifact_ledger, &artifact_rule_break_effects);
    let artifact_family_rule_break_impacts =
        build_artifact_family_rule_break_impacts(artifact_ledger, &artifact_rule_break_effects);
    let mut phases = [
        train.clone(),
        analyze.clone(),
        research.clone(),
        backtest.clone(),
        update.clone(),
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>();
    phases.sort_by(|a, b| a.timestamp.cmp(&b.timestamp));
    let current = phases.last().cloned();
    let blocking_truth = workflow_blocking_truth(
        symbol,
        state_dir,
        current.as_ref(),
        latest_analyze,
        &artifact_decision_summary,
    );

    let mut risk_flags = std::collections::BTreeSet::new();
    for phase in [
        train.as_ref(),
        analyze.as_ref(),
        research.as_ref(),
        backtest.as_ref(),
        update.as_ref(),
    ]
    .into_iter()
    .flatten()
    {
        for flag in &phase.risk_flags {
            risk_flags.insert(format!("{}:{}", phase.phase, flag));
        }
    }

    WorkflowSnapshot {
        symbol: symbol.to_string(),
        generated_at: Utc::now(),
        current_focus_phase: current
            .as_ref()
            .map(|phase| phase.phase.clone())
            .unwrap_or_default(),
        current_focus_reason: current
            .as_ref()
            .map(|phase| phase.workflow_reason.clone())
            .unwrap_or_default(),
        blocking_truth,
        recommended_next_command: current
            .as_ref()
            .map(|phase| phase.recommended_next_command.clone())
            .unwrap_or_default(),
        pending_actions: current.map(|phase| phase.top_actions).unwrap_or_default(),
        risk_flags: risk_flags
            .into_iter()
            .chain(
                disagreements
                    .iter()
                    .map(|item| format!("{}:{}", item.severity, item.id)),
            )
            .collect(),
        latest_train: train,
        latest_analyze: analyze,
        latest_research: research,
        latest_backtest: backtest,
        latest_update: update,
        latest_pre_bayes_policy,
        latest_pre_bayes_entry_quality_bridge,
        latest_pre_bayes_entry_quality_bridge_diff,
        latest_pre_bayes_policy_diff,
        latest_pre_bayes_policy_lineage,
        latest_pre_bayes_soft_evidence_diff,
        recent_pre_bayes_policies,
        latest_pending_update: recent_pending_updates.last().cloned(),
        recent_pending_updates,
        latest_execution_candidate: recent_execution_candidates.last().cloned(),
        recent_execution_candidates,
        latest_ensemble_vote: recent_ensemble_votes.last().cloned(),
        recent_ensemble_votes,
        recent_artifacts,
        actionable_artifacts,
        latest_promotable_artifact,
        artifact_history_summary,
        artifact_factor_trends,
        artifact_family_trends,
        artifact_decision_summary,
        artifact_review_rules: review_rules,
        artifact_review_rule_sources: review_rule_sources,
        artifact_lineage_summaries,
        artifact_rule_break_effects,
        artifact_factor_rule_break_impacts,
        artifact_family_rule_break_impacts,
        artifact_consumed_impact_summary,
        field_diffs,
        disagreements,
    }
}

fn artifact_decision_summary_from_trends(
    actionable_artifacts: &[ArtifactLedgerEntry],
    latest_promotable_artifact: Option<&ArtifactLedgerEntry>,
    lineage_summaries: &[ict_engine::state::ArtifactLineageSummary],
    factor_trends: &[ict_engine::state::ArtifactFactorTrendSummary],
    family_trends: &[ict_engine::state::ArtifactFamilyTrendSummary],
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> ict_engine::state::ArtifactDecisionSummary {
    let highlighted_actions =
        artifact_action_summary(factor_trends, family_trends, consumed_impact_summary);
    let highlighted_factor_targets = factor_trends
        .iter()
        .filter(|trend| trend.decision_status != "observe")
        .map(|trend| trend.factor_name.clone())
        .collect::<Vec<_>>();
    let highlighted_family_targets = family_trends
        .iter()
        .filter(|trend| trend.decision_status != "observe")
        .map(|trend| trend.family.clone())
        .collect::<Vec<_>>();
    let (consumed_trend_status, consumed_trend_reason, consumed_target_kinds) =
        artifact_consumed_trend_signal(consumed_impact_summary);
    let mut promotion_strength =
        if latest_promotable_artifact.is_some() && actionable_artifacts.len() >= 2 {
            "high".to_string()
        } else if latest_promotable_artifact.is_some() {
            "medium".to_string()
        } else {
            "low".to_string()
        };
    let mut rollback_strength = if factor_trends
        .iter()
        .any(|trend| trend.rollback_link_status == "rollback_watch")
        || family_trends
            .iter()
            .any(|trend| trend.rollback_link_status == "rollback_watch")
    {
        "high".to_string()
    } else {
        "low".to_string()
    };
    match consumed_trend_status.as_str() {
        "validated_improving" if latest_promotable_artifact.is_some() => {
            promotion_strength = "high".to_string();
        }
        "validated_regressing" => {
            promotion_strength = "low".to_string();
            rollback_strength = "high".to_string();
        }
        _ => {}
    }
    ict_engine::state::ArtifactDecisionSummary {
        actionable_artifact_count: actionable_artifacts.len(),
        latest_promotable_artifact_id: latest_promotable_artifact
            .map(|entry| entry.artifact_id.clone()),
        artifact_rule_break_count: lineage_summaries
            .iter()
            .map(|summary| summary.review_rule_break_count)
            .sum(),
        summary: format!(
            "actionable_artifacts={} latest_promotable={:?} rule_breaks={} consumed_trend={} consumed_targets={:?}",
            actionable_artifacts.len(),
            latest_promotable_artifact.map(|entry| entry.artifact_id.clone()),
            lineage_summaries
                .iter()
                .map(|summary| summary.review_rule_break_count)
                .sum::<usize>(),
            consumed_trend_status.clone(),
            consumed_target_kinds.clone()
        ),
        highlighted_actions,
        highlighted_factor_targets,
        highlighted_family_targets,
        promotion_strength,
        rollback_strength,
        consumed_trend_status,
        consumed_trend_reason,
        consumed_target_kinds,
    }
}

fn build_artifact_history_summary(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> ict_engine::state::ArtifactHistorySummary {
    let total_entries = artifact_ledger.len();
    let pending_update_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.artifact_kind == "pending_update")
        .count();
    let execution_candidate_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.artifact_kind == "execution_candidate")
        .count();
    let ensemble_vote_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.artifact_kind == "ensemble_vote")
        .count();
    let promotable_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.promote_candidate)
        .count();
    let actionable_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.actionable)
        .count();
    let consumed_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.consumed_by_update_run_id.is_some())
        .count();
    let average_quality_score = if total_entries == 0 {
        0.0
    } else {
        artifact_ledger
            .iter()
            .map(|entry| entry.quality_score as f64)
            .sum::<f64>()
            / total_entries as f64
    };
    let latest_consumed_artifact_id = artifact_ledger
        .iter()
        .rev()
        .find(|entry| entry.consumed_by_update_run_id.is_some())
        .map(|entry| entry.artifact_id.clone());
    let mut statuses_by_kind = BTreeMap::<String, BTreeMap<String, usize>>::new();
    for entry in artifact_ledger {
        let kind = statuses_by_kind
            .entry(entry.artifact_kind.clone())
            .or_default();
        *kind.entry(entry.status.clone()).or_default() += 1;
    }

    ict_engine::state::ArtifactHistorySummary {
        total_entries,
        pending_update_entries,
        execution_candidate_entries,
        ensemble_vote_entries,
        promotable_entries,
        actionable_entries,
        consumed_entries,
        average_quality_score,
        latest_consumed_artifact_id,
        statuses_by_kind,
    }
}

fn build_artifact_factor_trends(
    artifact_ledger: &[ArtifactLedgerEntry],
    research: &Option<WorkflowPhaseSnapshot>,
    backtest: &Option<WorkflowPhaseSnapshot>,
    update: &Option<WorkflowPhaseSnapshot>,
) -> Vec<ict_engine::state::ArtifactFactorTrendSummary> {
    let mut grouped = BTreeMap::<String, Vec<&ArtifactLedgerEntry>>::new();
    for entry in artifact_ledger {
        if let Some(factor_name) = &entry.top_factor_name {
            grouped.entry(factor_name.clone()).or_default().push(entry);
        }
    }
    let mut trends = grouped
        .into_iter()
        .map(|(factor_name, entries)| {
            let factor_name_for_reason = factor_name.clone();
            let entries_len = entries.len();
            let mut consumed_entries_sorted = entries
                .iter()
                .copied()
                .filter(|entry| entry.consumed_by_update_run_id.is_some())
                .collect::<Vec<_>>();
            consumed_entries_sorted.sort_by_key(|entry| artifact_consumed_recency_key(entry));
            let consumed_comparisons = [3usize, 5usize]
                .into_iter()
                .filter_map(|window| {
                    consumed_impact_trend_comparison(window, &consumed_entries_sorted)
                })
                .collect::<Vec<_>>();
            let (consumed_validation_status, consumed_validation_reason) =
                consumed_validation_status_from_comparisons(&consumed_comparisons);
            let consumed_validation_rank =
                i32::from(consumed_validation_rank(&consumed_validation_status));
            let consumed_validation_score = consumed_validation_score(
                &consumed_validation_status,
                &consumed_validation_reason,
            );
            let promotable_entries = entries
                .iter()
                .filter(|entry| entry.promote_candidate)
                .count();
            let consumed_entries = entries
                .iter()
                .filter(|entry| entry.consumed_by_update_run_id.is_some())
                .count();
            let average_quality_score = if entries_len == 0 {
                0.0
            } else {
                entries
                    .iter()
                    .map(|entry| entry.quality_score as f64)
                    .sum::<f64>()
                    / entries_len as f64
            };
            let latest_action = entries
                .last()
                .and_then(|entry| entry.top_factor_action.clone());
            let promotion_link_status = if entries.iter().any(|entry| entry.promote_candidate) {
                "promotion_supporting".to_string()
            } else {
                "none".to_string()
            };
            let rollback_link_status = if entries.iter().any(|entry| {
                matches!(
                    entry.consumption_regrade_status.as_deref(),
                    Some("validated_negative")
                )
            }) || consumed_validation_status == "validated_regressing" {
                "rollback_watch".to_string()
            } else {
                "none".to_string()
            };
            let decision_status = if rollback_link_status != "none" {
                "rollback_watch".to_string()
            } else if promotion_link_status != "none"
                || consumed_validation_status == "validated_improving"
            {
                "promotion_supporting".to_string()
            } else {
                "observe".to_string()
            };
            ict_engine::state::ArtifactFactorTrendSummary {
                factor_name,
                entries: entries_len,
                promotable_entries,
                consumed_entries,
                average_quality_score,
                latest_status: entries.last().map(|entry| entry.status.clone()),
                latest_action: latest_action.clone(),
                decision_status,
                decision_reason: format!(
                    "latest_action={:?} research_action={:?} backtest_action={:?} update_action={:?} consumed_validation_status={} consumed_validation_reason={}",
                    latest_action,
                    latest_factor_action(research, &factor_name_for_reason),
                    latest_factor_action(backtest, &factor_name_for_reason),
                    latest_factor_action(update, &factor_name_for_reason),
                    consumed_validation_status,
                    consumed_validation_reason
                ),
                promotion_link_status,
                rollback_link_status,
                consumed_validation_status,
                consumed_validation_reason,
                consumed_validation_rank,
                consumed_validation_score,
            }
        })
        .collect::<Vec<_>>();
    trends.sort_by(|a, b| {
        b.entries
            .cmp(&a.entries)
            .then_with(|| a.factor_name.cmp(&b.factor_name))
    });
    trends
}

fn build_artifact_family_trends(
    artifact_ledger: &[ArtifactLedgerEntry],
    research: &Option<WorkflowPhaseSnapshot>,
    backtest: &Option<WorkflowPhaseSnapshot>,
    update: &Option<WorkflowPhaseSnapshot>,
) -> Vec<ict_engine::state::ArtifactFamilyTrendSummary> {
    let mut grouped = BTreeMap::<String, Vec<(f64, &ArtifactLedgerEntry)>>::new();
    for entry in artifact_ledger {
        for (family, score) in &entry.family_scores {
            grouped
                .entry(family.clone())
                .or_default()
                .push((*score, entry));
        }
    }
    let mut trends = grouped
        .into_iter()
        .map(|(family, entries)| {
            let family_for_reason = family.clone();
            let entries_len = entries.len();
            let mut consumed_entries_sorted = entries
                .iter()
                .map(|(_, entry)| *entry)
                .filter(|entry| entry.consumed_by_update_run_id.is_some())
                .collect::<Vec<_>>();
            consumed_entries_sorted.sort_by_key(|entry| artifact_consumed_recency_key(entry));
            let consumed_comparisons = [3usize, 5usize]
                .into_iter()
                .filter_map(|window| {
                    consumed_impact_trend_comparison(window, &consumed_entries_sorted)
                })
                .collect::<Vec<_>>();
            let (consumed_validation_status, consumed_validation_reason) =
                consumed_validation_status_from_comparisons(&consumed_comparisons);
            let consumed_validation_rank =
                i32::from(consumed_validation_rank(&consumed_validation_status));
            let consumed_validation_score = consumed_validation_score(
                &consumed_validation_status,
                &consumed_validation_reason,
            );
            let promotable_entries = entries
                .iter()
                .filter(|(_, entry)| entry.promote_candidate)
                .count();
            let consumed_entries = entries
                .iter()
                .filter(|(_, entry)| entry.consumed_by_update_run_id.is_some())
                .count();
            let average_quality_score = if entries_len == 0 {
                0.0
            } else {
                entries
                    .iter()
                    .map(|(_, entry)| entry.quality_score as f64)
                    .sum::<f64>()
                    / entries_len as f64
            };
            let latest = entries.last().copied();
            let promotion_link_status = if entries.iter().any(|(_, entry)| entry.promote_candidate)
            {
                "promotion_supporting".to_string()
            } else {
                "none".to_string()
            };
            let rollback_link_status = if entries.iter().any(|(_, entry)| {
                matches!(
                    entry.consumption_regrade_status.as_deref(),
                    Some("validated_negative")
                )
            }) || consumed_validation_status == "validated_regressing" {
                "rollback_watch".to_string()
            } else {
                "none".to_string()
            };
            let decision_status = if rollback_link_status != "none" {
                "rollback_watch".to_string()
            } else if promotion_link_status != "none"
                || consumed_validation_status == "validated_improving"
            {
                "promotion_supporting".to_string()
            } else {
                "observe".to_string()
            };
            ict_engine::state::ArtifactFamilyTrendSummary {
                family,
                entries: entries_len,
                promotable_entries,
                consumed_entries,
                average_quality_score,
                latest_status: latest.map(|(_, entry)| entry.status.clone()),
                latest_score: latest.map(|(score, _)| score),
                decision_status,
                decision_reason: format!(
                    "research_state={:?} backtest_state={:?} update_state={:?} consumed_validation_status={} consumed_validation_reason={}",
                    latest_family_state(research, &family_for_reason),
                    latest_family_state(backtest, &family_for_reason),
                    latest_family_state(update, &family_for_reason),
                    consumed_validation_status,
                    consumed_validation_reason
                ),
                promotion_link_status,
                rollback_link_status,
                consumed_validation_status,
                consumed_validation_reason,
                consumed_validation_rank,
                consumed_validation_score,
            }
        })
        .collect::<Vec<_>>();
    trends.sort_by(|a, b| {
        b.entries
            .cmp(&a.entries)
            .then_with(|| a.family.cmp(&b.family))
    });
    trends
}

fn build_artifact_lineage_summaries_with_embedded_snapshots(
    artifact_ledger: &[ArtifactLedgerEntry],
    pending_updates: &[PendingUpdateArtifact],
    execution_candidates: &[ExecutionCandidateArtifact],
) -> Vec<ict_engine::state::ArtifactLineageSummary> {
    let mut children = BTreeMap::<String, Vec<&ArtifactLedgerEntry>>::new();
    for entry in artifact_ledger {
        if let Some(parent) = &entry.supersedes_artifact_id {
            children.entry(parent.clone()).or_default().push(entry);
        }
    }
    artifact_ledger
        .iter()
        .filter(|entry| entry.supersedes_artifact_id.is_none())
        .map(|root| {
            let mut chain = vec![root];
            let mut current = root;
            while let Some(next) = children
                .get(&current.artifact_id)
                .and_then(|items| items.iter().max_by_key(|item| item.version).copied())
            {
                chain.push(next);
                current = next;
            }
            let first = chain.first().copied().unwrap_or(root);
            let last = chain.last().copied().unwrap_or(root);
            let distinct_review_rule_versions = chain
                .iter()
                .filter_map(|entry| {
                    if entry.review_rule_version.is_empty() {
                        None
                    } else {
                        Some(entry.review_rule_version.clone())
                    }
                })
                .collect::<std::collections::BTreeSet<_>>()
                .into_iter()
                .collect::<Vec<_>>();
            let review_rule_break_count = chain
                .windows(2)
                .filter(|window| window[0].review_rule_version != window[1].review_rule_version)
                .count();
            let embedded_pre_bayes_change_count = chain
                .windows(2)
                .filter(|window| {
                    let (left_filter, left_bridge, left_mtf) =
                        embedded_pre_bayes_evidence_for_entry(
                            window[0],
                            pending_updates,
                            execution_candidates,
                        );
                    let (right_filter, right_bridge, right_mtf) =
                        embedded_pre_bayes_evidence_for_entry(
                            window[1],
                            pending_updates,
                            execution_candidates,
                        );
                    !artifact_embedded_pre_bayes_evidence(
                        left_filter,
                        right_filter,
                        left_bridge,
                        right_bridge,
                        left_mtf,
                        right_mtf,
                    )
                    .is_empty()
                })
                .count();
            let (latest_filter, latest_bridge, _) =
                embedded_pre_bayes_evidence_for_entry(last, pending_updates, execution_candidates);
            ict_engine::state::ArtifactLineageSummary {
                artifact_kind: root.artifact_kind.clone(),
                root_artifact_id: first.artifact_id.clone(),
                latest_artifact_id: last.artifact_id.clone(),
                artifact_count: chain.len(),
                quality_delta: last.quality_score - first.quality_score,
                consumed_count: chain
                    .iter()
                    .filter(|entry| entry.consumed_by_update_run_id.is_some())
                    .count(),
                conclusion: if last.quality_score - first.quality_score > 10 {
                    "improving".to_string()
                } else if first.quality_score - last.quality_score > 10 {
                    "deteriorating".to_string()
                } else {
                    "stable".to_string()
                },
                distinct_review_rule_versions,
                review_rule_break_count,
                embedded_pre_bayes_change_count,
                latest_pre_bayes_gate_status: latest_filter
                    .map(|filter| filter.gating_status.clone())
                    .unwrap_or_default(),
                latest_pre_bayes_bridge_selected_entry_quality: latest_bridge
                    .and_then(|bridge| {
                        pre_bayes_entry_quality_bridge_diff(bridge).selected_entry_quality
                    })
                    .unwrap_or_default(),
                latest_pre_bayes_multi_timeframe_direction_bias: latest_filter
                    .map(|filter| filter.filtered_multi_timeframe_direction_bias.clone())
                    .unwrap_or_default(),
            }
        })
        .collect()
}

fn build_artifact_lineage_summaries(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> Vec<ict_engine::state::ArtifactLineageSummary> {
    build_artifact_lineage_summaries_with_embedded_snapshots(artifact_ledger, &[], &[])
}

fn build_artifact_factor_rule_break_impacts(
    artifact_ledger: &[ArtifactLedgerEntry],
    effects: &[ict_engine::state::ArtifactRuleBreakEffect],
) -> Vec<ict_engine::state::ArtifactRuleBreakFactorImpact> {
    let mut grouped = BTreeMap::<String, Vec<&ict_engine::state::ArtifactRuleBreakEffect>>::new();
    for effect in effects {
        if let Some(name) = artifact_ledger
            .iter()
            .find(|entry| entry.artifact_id == effect.to_artifact_id)
            .and_then(|entry| entry.top_factor_name.clone())
        {
            grouped.entry(name).or_default().push(effect);
        }
    }
    let mut impacts = grouped
        .into_iter()
        .map(
            |(factor_name, effects)| ict_engine::state::ArtifactRuleBreakFactorImpact {
                factor_name,
                break_count: effects.len(),
                cumulative_quality_delta: effects.iter().map(|effect| effect.quality_delta).sum(),
                improving_breaks: effects
                    .iter()
                    .filter(|effect| effect.conclusion == "improving")
                    .count(),
                deteriorating_breaks: effects
                    .iter()
                    .filter(|effect| effect.conclusion == "deteriorating")
                    .count(),
                consumed_breaks: effects
                    .iter()
                    .filter(|effect| effect.consumed_delta > 0)
                    .count(),
            },
        )
        .collect::<Vec<_>>();
    impacts.sort_by(|a, b| {
        b.break_count
            .cmp(&a.break_count)
            .then_with(|| b.cumulative_quality_delta.cmp(&a.cumulative_quality_delta))
    });
    impacts
}

fn build_artifact_family_rule_break_impacts(
    artifact_ledger: &[ArtifactLedgerEntry],
    effects: &[ict_engine::state::ArtifactRuleBreakEffect],
) -> Vec<ict_engine::state::ArtifactRuleBreakFamilyImpact> {
    let mut grouped = BTreeMap::<String, Vec<&ict_engine::state::ArtifactRuleBreakEffect>>::new();
    for effect in effects {
        if let Some(scores) = artifact_ledger
            .iter()
            .find(|entry| entry.artifact_id == effect.to_artifact_id)
            .map(|entry| entry.family_scores.clone())
        {
            for family in scores.keys() {
                grouped.entry(family.clone()).or_default().push(effect);
            }
        }
    }
    let mut impacts = grouped
        .into_iter()
        .map(
            |(family, effects)| ict_engine::state::ArtifactRuleBreakFamilyImpact {
                family,
                break_count: effects.len(),
                cumulative_quality_delta: effects.iter().map(|effect| effect.quality_delta).sum(),
                improving_breaks: effects
                    .iter()
                    .filter(|effect| effect.conclusion == "improving")
                    .count(),
                deteriorating_breaks: effects
                    .iter()
                    .filter(|effect| effect.conclusion == "deteriorating")
                    .count(),
                consumed_breaks: effects
                    .iter()
                    .filter(|effect| effect.consumed_delta > 0)
                    .count(),
            },
        )
        .collect::<Vec<_>>();
    impacts.sort_by(|a, b| {
        b.break_count
            .cmp(&a.break_count)
            .then_with(|| b.cumulative_quality_delta.cmp(&a.cumulative_quality_delta))
    });
    impacts
}

fn build_artifact_consumed_impact_summary(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> ict_engine::state::ArtifactConsumedImpactSummary {
    let mut consumed_entries = artifact_ledger
        .iter()
        .filter(|entry| entry.consumed_by_update_run_id.is_some())
        .collect::<Vec<_>>();
    consumed_entries.sort_by_key(|entry| artifact_consumed_recency_key(entry));
    let mut previous_quality = None;
    let points = consumed_entries
        .iter()
        .map(|entry| {
            let delta = previous_quality
                .map(|value| entry.quality_score - value)
                .unwrap_or(0);
            previous_quality = Some(entry.quality_score);
            ict_engine::state::ArtifactConsumedImpactPoint {
                artifact_id: entry.artifact_id.clone(),
                artifact_kind: entry.artifact_kind.clone(),
                consumed_at: entry.consumed_at,
                consumed_outcome: entry.consumed_outcome.clone(),
                quality_score: entry.quality_score,
                regrade_status: entry.consumption_regrade_status.clone(),
                quality_delta_from_previous_consumed: delta,
            }
        })
        .collect::<Vec<_>>();
    let by_kind = consumed_entries
        .iter()
        .fold(
            BTreeMap::<String, Vec<&ArtifactLedgerEntry>>::new(),
            |mut acc, entry| {
                acc.entry(entry.artifact_kind.clone())
                    .or_default()
                    .push(*entry);
                acc
            },
        )
        .into_iter()
        .map(|(kind, entries)| (kind, consumed_impact_window("all", &entries)))
        .collect::<BTreeMap<_, _>>();
    let recent_windows = [3usize, 5usize]
        .into_iter()
        .filter_map(|window| {
            (consumed_entries.len() >= window).then(|| {
                consumed_impact_window(
                    &format!("recent_{}", window),
                    &consumed_entries[consumed_entries.len() - window..],
                )
            })
        })
        .collect::<Vec<_>>();
    let trend_comparisons = [3usize, 5usize]
        .into_iter()
        .filter_map(|window| consumed_impact_trend_comparison(window, &consumed_entries))
        .collect::<Vec<_>>();
    let by_kind_trend_comparisons = consumed_entries
        .iter()
        .fold(
            BTreeMap::<String, Vec<&ArtifactLedgerEntry>>::new(),
            |mut acc, entry| {
                acc.entry(entry.artifact_kind.clone())
                    .or_default()
                    .push(*entry);
                acc
            },
        )
        .into_iter()
        .map(|(kind, entries)| {
            let comparisons = [3usize, 5usize]
                .into_iter()
                .filter_map(|window| consumed_impact_trend_comparison(window, &entries))
                .collect::<Vec<_>>();
            (kind, comparisons)
        })
        .collect::<BTreeMap<_, _>>();
    ict_engine::state::ArtifactConsumedImpactSummary {
        total_consumed: consumed_entries.len(),
        positive_consumed: consumed_entries
            .iter()
            .filter(|entry| {
                matches!(
                    entry.consumption_regrade_status.as_deref(),
                    Some("validated_positive")
                )
            })
            .count(),
        negative_consumed: consumed_entries
            .iter()
            .filter(|entry| {
                matches!(
                    entry.consumption_regrade_status.as_deref(),
                    Some("validated_negative")
                )
            })
            .count(),
        neutral_consumed: consumed_entries
            .iter()
            .filter(|entry| {
                matches!(
                    entry.consumption_regrade_status.as_deref(),
                    Some("validated_neutral")
                )
            })
            .count(),
        cumulative_quality_score: consumed_entries
            .iter()
            .map(|entry| entry.quality_score)
            .sum(),
        points,
        by_kind,
        recent_windows,
        trend_comparisons,
        by_kind_trend_comparisons,
    }
}

fn consumed_impact_window(
    label: &str,
    entries: &[&ArtifactLedgerEntry],
) -> ict_engine::state::ArtifactConsumedImpactWindow {
    let count = entries.len();
    let positive = entries
        .iter()
        .filter(|entry| {
            matches!(
                entry.consumption_regrade_status.as_deref(),
                Some("validated_positive")
            )
        })
        .count();
    let negative = entries
        .iter()
        .filter(|entry| {
            matches!(
                entry.consumption_regrade_status.as_deref(),
                Some("validated_negative")
            )
        })
        .count();
    let neutral = entries
        .iter()
        .filter(|entry| {
            matches!(
                entry.consumption_regrade_status.as_deref(),
                Some("validated_neutral")
            )
        })
        .count();
    let cumulative_quality_delta = entries
        .windows(2)
        .map(|window| window[1].quality_score - window[0].quality_score)
        .sum();
    ict_engine::state::ArtifactConsumedImpactWindow {
        label: label.to_string(),
        count,
        positive,
        negative,
        neutral,
        average_quality_score: if count == 0 {
            0.0
        } else {
            entries
                .iter()
                .map(|entry| entry.quality_score as f64)
                .sum::<f64>()
                / count as f64
        },
        cumulative_quality_delta,
    }
}

fn consumed_impact_trend_comparison(
    window: usize,
    consumed_entries: &[&ArtifactLedgerEntry],
) -> Option<ict_engine::state::ArtifactConsumedImpactTrendComparison> {
    if consumed_entries.len() < window + 1 {
        return None;
    }
    let recent_slice = &consumed_entries[consumed_entries.len() - window..];
    let baseline_end = consumed_entries.len().saturating_sub(window);
    let baseline_start = baseline_end.saturating_sub(window);
    let baseline_slice = &consumed_entries[baseline_start..baseline_end];
    if baseline_slice.is_empty() {
        return None;
    }
    let recent = consumed_impact_window(&format!("recent_{}", window), recent_slice);
    let baseline = consumed_impact_window(
        &format!("previous_{}", baseline_slice.len()),
        baseline_slice,
    );
    let recent_positive_rate = recent.positive as f64 / recent.count.max(1) as f64;
    let baseline_positive_rate = baseline.positive as f64 / baseline.count.max(1) as f64;
    let average_quality_score_delta = recent.average_quality_score - baseline.average_quality_score;
    let cumulative_quality_delta_delta =
        recent.cumulative_quality_delta - baseline.cumulative_quality_delta;
    let positive_rate_delta = recent_positive_rate - baseline_positive_rate;
    let conclusion = if average_quality_score_delta > 5.0 || positive_rate_delta > 0.25 {
        "improving".to_string()
    } else if average_quality_score_delta < -5.0 || positive_rate_delta < -0.25 {
        "regressing".to_string()
    } else {
        "stable".to_string()
    };
    Some(ict_engine::state::ArtifactConsumedImpactTrendComparison {
        label: format!("recent_{}_vs_previous_{}", window, baseline_slice.len()),
        recent,
        baseline,
        average_quality_score_delta,
        cumulative_quality_delta_delta,
        positive_rate_delta,
        conclusion,
    })
}

fn build_artifact_rule_break_effects(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> Vec<ict_engine::state::ArtifactRuleBreakEffect> {
    let mut effects = Vec::new();
    let mut grouped = BTreeMap::<String, Vec<&ArtifactLedgerEntry>>::new();
    for entry in artifact_ledger {
        let root = artifact_lineage_root_id(artifact_ledger, &entry.artifact_id);
        grouped.entry(root).or_default().push(entry);
    }
    for (root_id, mut entries) in grouped {
        entries.sort_by_key(|entry| entry.version);
        for window in entries.windows(2) {
            let left = window[0];
            let right = window[1];
            if left.review_rule_version != right.review_rule_version {
                effects.push(ict_engine::state::ArtifactRuleBreakEffect {
                    artifact_kind: right.artifact_kind.clone(),
                    lineage_root_artifact_id: root_id.clone(),
                    from_artifact_id: left.artifact_id.clone(),
                    to_artifact_id: right.artifact_id.clone(),
                    from_rule_version: left.review_rule_version.clone(),
                    to_rule_version: right.review_rule_version.clone(),
                    quality_delta: right.quality_score - left.quality_score,
                    consumed_delta: i32::from(right.consumed_by_update_run_id.is_some())
                        - i32::from(left.consumed_by_update_run_id.is_some()),
                    conclusion: if right.quality_score - left.quality_score > 10 {
                        "improving".to_string()
                    } else if left.quality_score - right.quality_score > 10 {
                        "deteriorating".to_string()
                    } else {
                        "stable".to_string()
                    },
                });
            }
        }
    }
    effects
}

fn artifact_lineage_root_id(artifact_ledger: &[ArtifactLedgerEntry], artifact_id: &str) -> String {
    let mut current = artifact_id.to_string();
    while let Some(parent) = artifact_ledger
        .iter()
        .find(|entry| entry.artifact_id == current)
        .and_then(|entry| entry.supersedes_artifact_id.clone())
    {
        current = parent;
    }
    current
}

fn latest_factor_action(
    snapshot: &Option<WorkflowPhaseSnapshot>,
    factor_name: &str,
) -> Option<String> {
    snapshot.as_ref().and_then(|snapshot| {
        snapshot.factor_actions.iter().find_map(|item| {
            let mut parts = item.splitn(3, ':');
            let name = parts.next()?;
            let action = parts.next()?;
            (name == factor_name).then(|| action.to_string())
        })
    })
}

fn latest_family_state(snapshot: &Option<WorkflowPhaseSnapshot>, family: &str) -> Option<String> {
    snapshot.as_ref().and_then(|snapshot| {
        snapshot.family_states.iter().find_map(|item| {
            let mut parts = item.splitn(3, ':');
            let name = parts.next()?;
            let promotion = parts.next()?;
            let rollback = parts.next()?;
            (name == family).then(|| format!("{}:{}", promotion, rollback))
        })
    })
}

fn pending_update_summary(
    state_dir: &str,
    symbol: &str,
    artifact: &PendingUpdateArtifact,
) -> PendingUpdateArtifactSummary {
    PendingUpdateArtifactSummary {
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
        decision_hint: artifact.decision_hint.clone(),
        entry_quality: artifact.entry_quality.clone(),
        factor_alignment: artifact.factor_alignment.clone(),
        factor_uncertainty: artifact.factor_uncertainty.clone(),
        top_factor_name: artifact.top_factor_name.clone(),
        top_factor_action: artifact.top_factor_action.clone(),
        review_rule_version: artifact.review_rule_version.clone(),
        review_status: artifact.review_decision.status.clone(),
        review_reason: artifact.review_decision.reason.clone(),
        pre_bayes_gate_status: artifact
            .pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.gating_status.clone())
            .unwrap_or_default(),
        pre_bayes_bridge_selected_entry_quality: artifact
            .pre_bayes_entry_quality_bridge
            .as_ref()
            .and_then(|bridge| pre_bayes_entry_quality_bridge_diff(bridge).selected_entry_quality)
            .unwrap_or_default(),
        multi_timeframe_summary: artifact.multi_timeframe_summary.clone(),
        quality_delta: artifact.diff_from_previous.quality_delta,
        selected_probability_delta: artifact.diff_from_previous.selected_probability_delta,
        top_factor_score_delta: artifact.diff_from_previous.top_factor_score_delta,
        avg_family_score_delta: artifact.diff_from_previous.avg_family_score_delta,
    }
}

fn execution_candidate_summary(
    state_dir: &str,
    symbol: &str,
    artifact: &ExecutionCandidateArtifact,
) -> ExecutionCandidateArtifactSummary {
    ExecutionCandidateArtifactSummary {
        artifact_id: artifact.artifact_id.clone(),
        version: artifact.version,
        generated_at: artifact.generated_at,
        symbol: artifact.symbol.clone(),
        source_phase: artifact.source_phase.clone(),
        source_run_id: artifact.source_run_id.clone(),
        path: std::path::Path::new(state_dir)
            .join(symbol)
            .join(EXECUTION_CANDIDATE_FILE)
            .to_string_lossy()
            .to_string(),
        trade_direction: format!("{:?}", artifact.trade_direction),
        actionable: artifact.actionable,
        candidate_status: artifact.candidate_status.clone(),
        decision_hint: artifact.decision_hint.clone(),
        top_factor_name: artifact.top_factor_name.clone(),
        top_factor_action: artifact.top_factor_action.clone(),
        review_rule_version: artifact.review_rule_version.clone(),
        review_status: artifact.review_decision.status.clone(),
        review_reason: artifact.review_decision.reason.clone(),
        pre_bayes_gate_status: artifact
            .pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.gating_status.clone())
            .unwrap_or_default(),
        pre_bayes_bridge_selected_entry_quality: artifact
            .pre_bayes_entry_quality_bridge
            .as_ref()
            .and_then(|bridge| pre_bayes_entry_quality_bridge_diff(bridge).selected_entry_quality)
            .unwrap_or_default(),
        multi_timeframe_summary: artifact.multi_timeframe_summary.clone(),
        posterior_delta: artifact.diff_from_previous.posterior_delta,
        win_probability_delta: artifact.diff_from_previous.win_probability_delta,
    }
}

fn workflow_phase_snapshot_from_analyze_run(run: &AnalyzeRunRecord) -> WorkflowPhaseSnapshot {
    let bridge_diff = pre_bayes_entry_quality_bridge_diff(&run.pre_bayes_entry_quality_bridge);
    WorkflowPhaseSnapshot {
        phase: "analyze".to_string(),
        source_command: run.source_command.clone(),
        run_id: run.run_id.clone(),
        timestamp: run.timestamp,
        workflow_phase: run.workflow_state.phase.clone(),
        workflow_reason: run.workflow_state.reason.clone(),
        promotion_status: run.promotion_decision.status.clone(),
        rollback_scope: run.rollback_recommendation.scope.clone(),
        comparable_to_previous: run.dataset_comparability.comparable,
        comparison_class: run.dataset_comparability.comparison_class.clone(),
        recommended_next_command: run.recommended_next_command.clone(),
        phase_summary: format!(
            "selected_direction={:?} selected_entry_quality={} pre_bayes_status={} pre_bayes_quality={:.3} decision_hint={} {}",
            run.selected_direction,
            run.selected_entry_quality,
            run.pre_bayes_evidence_filter.gating_status,
            run.pre_bayes_evidence_filter.evidence_quality_score,
            run.decision_hint,
            multi_timeframe_phase_hint(&run.multi_timeframe_summary)
        ),
        top_actions: workflow_top_actions(&run.agent_action_plan),
        risk_flags: workflow_phase_risk_flags(
            &run.dataset_comparability,
            &run.promotion_decision,
            &run.rollback_recommendation,
        )
        .into_iter()
        .chain(
            run.pre_bayes_evidence_filter
                .conflict_flags
                .iter()
                .map(|flag| format!("pre_bayes:{}", flag)),
        )
        .collect(),
        selected_direction: Some(format!("{:?}", run.selected_direction)),
        selected_entry_quality: Some(run.selected_entry_quality.clone()),
        pre_bayes_gate_status: run.pre_bayes_evidence_filter.gating_status.clone(),
        pre_bayes_uses_soft_evidence: run.pre_bayes_evidence_filter.uses_soft_evidence,
        pre_bayes_policy_version: run.pre_bayes_evidence_filter.policy.version.clone(),
        pre_bayes_evidence_quality_score: run.pre_bayes_evidence_filter.evidence_quality_score,
        pre_bayes_conflict_flags: run.pre_bayes_evidence_filter.conflict_flags.clone(),
        pre_bayes_filtered_assignments: {
            let mut assignments = run.pre_bayes_evidence_filter.evidence_assignments.clone();
            assignments.insert(
                "__policy_version".to_string(),
                run.pre_bayes_evidence_filter.policy.version.clone(),
            );
            assignments
        },
        pre_bayes_soft_evidence: BTreeMap::from([
            (
                "market_regime".to_string(),
                run.pre_bayes_evidence_filter
                    .soft_market_regime_distribution
                    .clone(),
            ),
            (
                "liquidity_context".to_string(),
                run.pre_bayes_evidence_filter
                    .soft_liquidity_context_distribution
                    .clone(),
            ),
            (
                "factor_alignment".to_string(),
                run.pre_bayes_evidence_filter
                    .soft_factor_alignment_distribution
                    .clone(),
            ),
            (
                "factor_uncertainty".to_string(),
                run.pre_bayes_evidence_filter
                    .soft_factor_uncertainty_distribution
                    .clone(),
            ),
            (
                "multi_timeframe_resonance".to_string(),
                run.pre_bayes_evidence_filter
                    .soft_multi_timeframe_resonance_distribution
                    .clone(),
            ),
        ]),
        pre_bayes_long_signal_probability: Some(
            run.pre_bayes_entry_quality_bridge.long_signal_probability,
        ),
        pre_bayes_short_signal_probability: Some(
            run.pre_bayes_entry_quality_bridge.short_signal_probability,
        ),
        pre_bayes_selected_entry_quality_probability: run
            .pre_bayes_entry_quality_bridge
            .selected_entry_quality
            .values()
            .copied()
            .fold(None, |acc, value| {
                Some(acc.map(|current| current.max(value)).unwrap_or(value))
            }),
        pre_bayes_bridge_selected_entry_quality: bridge_diff.selected_entry_quality.clone(),
        pre_bayes_bridge_probability_gap: Some(bridge_diff.long_short_signal_probability_gap),
        pre_bayes_bridge_rationale_summary: bridge_diff.rationale_summary,
        pre_bayes_multi_timeframe_direction_bias: run
            .pre_bayes_evidence_filter
            .filtered_multi_timeframe_direction_bias
            .clone(),
        pre_bayes_multi_timeframe_alignment_score: run
            .pre_bayes_evidence_filter
            .filtered_multi_timeframe_alignment_score,
        pre_bayes_multi_timeframe_entry_alignment_score: run
            .pre_bayes_evidence_filter
            .filtered_multi_timeframe_entry_alignment_score,
        realized_outcome: None,
        family_states: run
            .factor_family_outcomes
            .iter()
            .map(|item| {
                format!(
                    "{}:{}:{}",
                    item.family, item.promotion_decision.status, item.rollback_recommendation.scope
                )
            })
            .collect(),
        factor_actions: run.agent_context_bundle.top_factor_actions.clone(),
        multi_timeframe_summary: run.multi_timeframe_summary.clone(),
        family_score_map: run
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        factor_score_map: BTreeMap::new(),
    }
}

fn workflow_phase_snapshot_from_train_run(run: &TrainRunRecord) -> WorkflowPhaseSnapshot {
    WorkflowPhaseSnapshot {
        phase: "train".to_string(),
        source_command: run.source_command.clone(),
        run_id: run.run_id.clone(),
        timestamp: run.timestamp,
        workflow_phase: run.workflow_state.phase.clone(),
        workflow_reason: run.workflow_state.reason.clone(),
        promotion_status: "promotion_status_unavailable".to_string(),
        rollback_scope: "rollback_scope_unavailable".to_string(),
        comparable_to_previous: run.dataset_comparability.comparable,
        comparison_class: run.dataset_comparability.comparison_class.clone(),
        recommended_next_command: run.recommended_next_command.clone(),
        phase_summary: format!(
            "final_state={} observations={} epochs={} log_likelihood={:.4} {}",
            run.final_state,
            run.observations,
            run.epochs,
            run.log_likelihood,
            multi_timeframe_phase_hint(&run.multi_timeframe_summary)
        ),
        top_actions: workflow_top_actions(&run.agent_action_plan),
        risk_flags: if run.dataset_comparability.comparable {
            Vec::new()
        } else {
            vec![format!(
                "not_comparable:{}",
                run.dataset_comparability.comparison_class
            )]
        },
        selected_direction: None,
        selected_entry_quality: None,
        pre_bayes_gate_status: "pre_bayes_gate_unavailable".to_string(),
        pre_bayes_uses_soft_evidence: false,
        pre_bayes_policy_version: "policy_version_unavailable".to_string(),
        pre_bayes_evidence_quality_score: 0.0,
        pre_bayes_conflict_flags: Vec::new(),
        pre_bayes_filtered_assignments: BTreeMap::new(),
        pre_bayes_soft_evidence: BTreeMap::new(),
        pre_bayes_long_signal_probability: None,
        pre_bayes_short_signal_probability: None,
        pre_bayes_selected_entry_quality_probability: None,
        pre_bayes_bridge_selected_entry_quality: None,
        pre_bayes_bridge_probability_gap: None,
        pre_bayes_bridge_rationale_summary: Vec::new(),
        pre_bayes_multi_timeframe_direction_bias: "direction_bias_unavailable".to_string(),
        pre_bayes_multi_timeframe_alignment_score: None,
        pre_bayes_multi_timeframe_entry_alignment_score: None,
        realized_outcome: None,
        family_states: Vec::new(),
        factor_actions: Vec::new(),
        multi_timeframe_summary: run.multi_timeframe_summary.clone(),
        family_score_map: BTreeMap::new(),
        factor_score_map: BTreeMap::new(),
    }
}

fn workflow_phase_snapshot_from_research_run(run: &ResearchRunRecord) -> WorkflowPhaseSnapshot {
    WorkflowPhaseSnapshot {
        phase: "research".to_string(),
        source_command: run.source_command.clone(),
        run_id: run.run_id.clone(),
        timestamp: run.timestamp,
        workflow_phase: run.workflow_state.phase.clone(),
        workflow_reason: run.workflow_state.reason.clone(),
        promotion_status: run.promotion_decision.status.clone(),
        rollback_scope: run.rollback_recommendation.scope.clone(),
        comparable_to_previous: run.dataset_comparability.comparable,
        comparison_class: run.dataset_comparability.comparison_class.clone(),
        recommended_next_command: run.recommended_next_command.clone(),
        phase_summary: format!(
            "objective={} best_factor={:?} aggregate_return={:.4} feedback_applied={} credibility={} {}",
            if run.research_objective.is_empty() {
                "generic"
            } else {
                run.research_objective.as_str()
            },
            run.best_factor,
            run.aggregate_return,
            run.feedback_records_applied,
            run.artifact_action_summary
                .iter()
                .find(|item| item.starts_with("conformal_credibility:"))
                .cloned()
                .unwrap_or_else(|| "conformal_credibility:unavailable".to_string()),
            multi_timeframe_phase_hint(&run.multi_timeframe_summary)
        ),
        top_actions: workflow_top_actions(&run.agent_action_plan),
        risk_flags: workflow_phase_risk_flags(
            &run.dataset_comparability,
            &run.promotion_decision,
            &run.rollback_recommendation,
        ),
        selected_direction: None,
        selected_entry_quality: None,
        pre_bayes_gate_status: "pre_bayes_gate_unavailable".to_string(),
        pre_bayes_uses_soft_evidence: false,
        pre_bayes_policy_version: "policy_version_unavailable".to_string(),
        pre_bayes_evidence_quality_score: 0.0,
        pre_bayes_conflict_flags: Vec::new(),
        pre_bayes_filtered_assignments: BTreeMap::new(),
        pre_bayes_soft_evidence: BTreeMap::new(),
        pre_bayes_long_signal_probability: None,
        pre_bayes_short_signal_probability: None,
        pre_bayes_selected_entry_quality_probability: None,
        pre_bayes_bridge_selected_entry_quality: None,
        pre_bayes_bridge_probability_gap: None,
        pre_bayes_bridge_rationale_summary: Vec::new(),
        pre_bayes_multi_timeframe_direction_bias: "direction_bias_unavailable".to_string(),
        pre_bayes_multi_timeframe_alignment_score: None,
        pre_bayes_multi_timeframe_entry_alignment_score: None,
        realized_outcome: None,
        family_states: run
            .factor_family_outcomes
            .iter()
            .map(|item| {
                format!(
                    "{}:{}:{}",
                    item.family, item.promotion_decision.status, item.rollback_recommendation.scope
                )
            })
            .collect(),
        factor_actions: run.agent_context_bundle.top_factor_actions.clone(),
        multi_timeframe_summary: run.multi_timeframe_summary.clone(),
        family_score_map: run
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        factor_score_map: run
            .factor_score_deltas
            .iter()
            .map(|item| (item.factor_name.clone(), item.new_score))
            .collect(),
    }
}

fn workflow_phase_snapshot_from_backtest_run(run: &BacktestRunRecord) -> WorkflowPhaseSnapshot {
    WorkflowPhaseSnapshot {
        phase: "backtest".to_string(),
        source_command: run.source_command.clone(),
        run_id: run.run_id.clone(),
        timestamp: run.timestamp,
        workflow_phase: run.workflow_state.phase.clone(),
        workflow_reason: run.workflow_state.reason.clone(),
        promotion_status: run.promotion_decision.status.clone(),
        rollback_scope: run.rollback_recommendation.scope.clone(),
        comparable_to_previous: run.dataset_comparability.comparable,
        comparison_class: run.dataset_comparability.comparison_class.clone(),
        recommended_next_command: run.recommended_next_command.clone(),
        phase_summary: format!(
            "total_return={:.4} trade_count={} source={} coverage_1sigma={:.3} break_penalty={:.3} structural_break_detected={} structural_break_score={:.3} structural_break_index={:?} {}",
            run.total_return,
            run.trade_count,
            run.source_command,
            run.conformal_coverage_1sigma,
            run.regime_break_penalty,
            run.structural_break_detected,
            run.structural_break_score,
            run.structural_break_index,
            multi_timeframe_phase_hint(&run.multi_timeframe_summary)
        ),
        top_actions: workflow_top_actions(&run.agent_action_plan),
        risk_flags: workflow_phase_risk_flags(
            &run.dataset_comparability,
            &run.promotion_decision,
            &run.rollback_recommendation,
        ),
        selected_direction: None,
        selected_entry_quality: None,
        pre_bayes_gate_status: "pre_bayes_gate_unavailable".to_string(),
        pre_bayes_uses_soft_evidence: false,
        pre_bayes_policy_version: "policy_version_unavailable".to_string(),
        pre_bayes_evidence_quality_score: 0.0,
        pre_bayes_conflict_flags: Vec::new(),
        pre_bayes_filtered_assignments: BTreeMap::new(),
        pre_bayes_soft_evidence: BTreeMap::new(),
        pre_bayes_long_signal_probability: None,
        pre_bayes_short_signal_probability: None,
        pre_bayes_selected_entry_quality_probability: None,
        pre_bayes_bridge_selected_entry_quality: None,
        pre_bayes_bridge_probability_gap: None,
        pre_bayes_bridge_rationale_summary: Vec::new(),
        pre_bayes_multi_timeframe_direction_bias: "direction_bias_unavailable".to_string(),
        pre_bayes_multi_timeframe_alignment_score: None,
        pre_bayes_multi_timeframe_entry_alignment_score: None,
        realized_outcome: None,
        family_states: run
            .factor_family_outcomes
            .iter()
            .map(|item| {
                format!(
                    "{}:{}:{}",
                    item.family, item.promotion_decision.status, item.rollback_recommendation.scope
                )
            })
            .collect(),
        factor_actions: run.agent_context_bundle.top_factor_actions.clone(),
        multi_timeframe_summary: run.multi_timeframe_summary.clone(),
        family_score_map: run
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        factor_score_map: run
            .factor_score_deltas
            .iter()
            .map(|item| (item.factor_name.clone(), item.new_score))
            .collect(),
    }
}

fn workflow_phase_snapshot_from_update_run(run: &UpdateRunRecord) -> WorkflowPhaseSnapshot {
    let consumed_bridge_diff = run
        .consumed_pre_bayes_entry_quality_bridge
        .as_ref()
        .map(pre_bayes_entry_quality_bridge_diff);
    WorkflowPhaseSnapshot {
        phase: "update".to_string(),
        source_command: run.source_command.clone(),
        run_id: run.run_id.clone(),
        timestamp: run.timestamp,
        workflow_phase: run.workflow_state.phase.clone(),
        workflow_reason: run.workflow_state.reason.clone(),
        promotion_status: run.promotion_decision.status.clone(),
        rollback_scope: run.rollback_recommendation.scope.clone(),
        comparable_to_previous: run.dataset_comparability.comparable,
        comparison_class: run.dataset_comparability.comparison_class.clone(),
        recommended_next_command: run.recommended_next_command.clone(),
        phase_summary: format!(
            "realized_outcome={} feedback_applied={} duplicate_feedback_skipped={} consumed_pre_bayes_gate_status={} {}",
            run.realized_outcome,
            run.feedback_records_applied,
            run.duplicate_feedback_skipped,
            run.consumed_pre_bayes_evidence_filter
                .as_ref()
                .map(|filter| filter.gating_status.clone())
                .unwrap_or_default(),
            multi_timeframe_phase_hint(&run.consumed_multi_timeframe_summary)
        ),
        top_actions: workflow_top_actions(&run.agent_action_plan),
        risk_flags: workflow_phase_risk_flags(
            &run.dataset_comparability,
            &run.promotion_decision,
            &run.rollback_recommendation,
        ),
        selected_direction: None,
        selected_entry_quality: Some(run.normalized_entry_quality.clone()),
        pre_bayes_gate_status: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.gating_status.clone())
            .unwrap_or_default(),
        pre_bayes_uses_soft_evidence: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.uses_soft_evidence)
            .unwrap_or(false),
        pre_bayes_policy_version: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.policy.version.clone())
            .unwrap_or_default(),
        pre_bayes_evidence_quality_score: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.evidence_quality_score)
            .unwrap_or_default(),
        pre_bayes_conflict_flags: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.conflict_flags.clone())
            .unwrap_or_default(),
        pre_bayes_filtered_assignments: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.evidence_assignments.clone())
            .unwrap_or_default(),
        pre_bayes_soft_evidence: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| {
                BTreeMap::from([
                    (
                        "market_regime".to_string(),
                        filter.soft_market_regime_distribution.clone(),
                    ),
                    (
                        "liquidity_context".to_string(),
                        filter.soft_liquidity_context_distribution.clone(),
                    ),
                    (
                        "factor_alignment".to_string(),
                        filter.soft_factor_alignment_distribution.clone(),
                    ),
                    (
                        "factor_uncertainty".to_string(),
                        filter.soft_factor_uncertainty_distribution.clone(),
                    ),
                    (
                        "multi_timeframe_resonance".to_string(),
                        filter.soft_multi_timeframe_resonance_distribution.clone(),
                    ),
                ])
            })
            .unwrap_or_default(),
        pre_bayes_long_signal_probability: None,
        pre_bayes_short_signal_probability: None,
        pre_bayes_selected_entry_quality_probability: None,
        pre_bayes_bridge_selected_entry_quality: consumed_bridge_diff
            .as_ref()
            .and_then(|diff| diff.selected_entry_quality.clone()),
        pre_bayes_bridge_probability_gap: consumed_bridge_diff
            .as_ref()
            .map(|diff| diff.long_short_signal_probability_gap),
        pre_bayes_bridge_rationale_summary: consumed_bridge_diff
            .as_ref()
            .map(|diff| diff.rationale_summary.clone())
            .unwrap_or_default(),
        pre_bayes_multi_timeframe_direction_bias: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .map(|filter| filter.filtered_multi_timeframe_direction_bias.clone())
            .unwrap_or_default(),
        pre_bayes_multi_timeframe_alignment_score: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .and_then(|filter| filter.filtered_multi_timeframe_alignment_score),
        pre_bayes_multi_timeframe_entry_alignment_score: run
            .consumed_pre_bayes_evidence_filter
            .as_ref()
            .and_then(|filter| filter.filtered_multi_timeframe_entry_alignment_score),
        realized_outcome: Some(run.realized_outcome.clone()),
        family_states: run
            .factor_family_outcomes
            .iter()
            .map(|item| {
                format!(
                    "{}:{}:{}",
                    item.family, item.promotion_decision.status, item.rollback_recommendation.scope
                )
            })
            .collect(),
        factor_actions: run.agent_context_bundle.top_factor_actions.clone(),
        multi_timeframe_summary: run.consumed_multi_timeframe_summary.clone(),
        family_score_map: run
            .factor_family_decisions
            .iter()
            .map(|family| (family.family.clone(), family.avg_score))
            .collect(),
        factor_score_map: run
            .factor_score_deltas
            .iter()
            .map(|item| (item.factor_name.clone(), item.new_score))
            .collect(),
    }
}

fn workflow_top_actions(plan: &AgentActionPlan) -> Vec<String> {
    plan.items
        .iter()
        .take(3)
        .map(|item| format!("{}:{}", item.stage, item.title))
        .collect()
}

fn workflow_blocking_truth(
    symbol: &str,
    state_dir: &str,
    current_phase: Option<&WorkflowPhaseSnapshot>,
    pre_bayes_filter: Option<&AnalyzeRunRecord>,
    artifact_decision_summary: &ict_engine::state::ArtifactDecisionSummary,
) -> WorkflowBlockingTruth {
    let current_recommended_command = current_phase
        .map(|phase| phase.recommended_next_command.clone())
        .unwrap_or_default();
    if let Some(analyze) = pre_bayes_filter {
        let gate_status = analyze.pre_bayes_evidence_filter.gating_status.clone();
        let bridge_diff =
            pre_bayes_entry_quality_bridge_diff(&analyze.pre_bayes_entry_quality_bridge);
        let bridge_gap = bridge_diff.long_short_signal_probability_gap;
        let hard_pass = pre_bayes_gate_is_hard_pass(&gate_status);
        let bridge_gap_clear_threshold = env_f64("ICT_ENGINE_BRIDGE_GAP_CLEAR_THRESHOLD", 0.12);
        if !hard_pass || bridge_gap < bridge_gap_clear_threshold {
            let mut evidence = vec![
                format!("pre_bayes_gate_status={gate_status}"),
                format!("bridge_probability_gap={bridge_gap:.3}"),
                format!(
                    "selected_entry_quality={}",
                    bridge_diff
                        .selected_entry_quality
                        .unwrap_or_else(|| "entry_quality_unavailable".to_string())
                ),
            ];
            evidence.extend(
                analyze
                    .pre_bayes_evidence_filter
                    .rationale
                    .iter()
                    .take(3)
                    .cloned(),
            );
            return WorkflowBlockingTruth {
                stage: "analyze".to_string(),
                status: if hard_pass {
                    "bridge_needs_confirmation".to_string()
                } else {
                    gate_status.clone()
                },
                reason: if hard_pass {
                    format!(
                        "pre_bayes passed but bridge gap {:.3} is below confirmation threshold",
                        bridge_gap
                    )
                } else {
                    analyze
                        .pre_bayes_evidence_filter
                        .rationale
                        .first()
                        .cloned()
                        .unwrap_or_else(|| {
                            "pre-bayes gate still blocks downstream chain".to_string()
                        })
                },
                evidence,
                next_command: if current_recommended_command.is_empty() {
                    format!(
                        "ict-engine pre-bayes-status --symbol {} --state-dir {}",
                        shell_quote(symbol),
                        shell_quote(state_dir)
                    )
                } else {
                    current_recommended_command
                },
            };
        }
    }
    if artifact_decision_summary.consumed_trend_status == "validated_regressing" {
        return WorkflowBlockingTruth {
            stage: "artifact_consumption".to_string(),
            status: artifact_decision_summary.consumed_trend_status.clone(),
            reason: artifact_decision_summary.consumed_trend_reason.clone(),
            evidence: artifact_decision_summary.consumed_target_kinds.clone(),
            next_command: format!(
                "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-consumed-gate",
                shell_quote(symbol),
                shell_quote(state_dir)
            ),
        };
    }
    if let Some(phase) = current_phase {
        if let Some(credibility_block) = phase.risk_flags.iter().find(|flag| {
            flag.contains("conformal_coverage_low")
                || flag.contains("regime_break_penalty_high")
                || flag.contains("structural_break_detected")
        }) {
            return WorkflowBlockingTruth {
                stage: phase.phase.clone(),
                status: "credibility_gate_blocked".to_string(),
                reason: format!(
                    "workflow credibility gate blocked next step because {}",
                    credibility_block
                ),
                evidence: phase.risk_flags.clone(),
                next_command: format!(
                    "ict-engine workflow-status --symbol {} --state-dir {} --phase human-next",
                    shell_quote(symbol),
                    shell_quote(state_dir)
                ),
            };
        }
    }
    if let Some(phase) = current_phase {
        return WorkflowBlockingTruth {
            stage: phase.phase.clone(),
            status: "follow_current_focus".to_string(),
            reason: phase.workflow_reason.clone(),
            evidence: phase.top_actions.clone(),
            next_command: phase.recommended_next_command.clone(),
        };
    }
    WorkflowBlockingTruth {
        stage: "stage_unavailable".to_string(),
        status: "insufficient_state".to_string(),
        reason: "no workflow phase snapshots available".to_string(),
        evidence: Vec::new(),
        next_command: "next_command_unavailable".to_string(),
    }
}

fn workflow_phase_risk_flags(
    comparability: &DatasetComparability,
    promotion: &PromotionDecision,
    rollback: &RollbackRecommendation,
) -> Vec<String> {
    let mut flags = Vec::new();
    if !comparability.comparable {
        flags.push(format!("not_comparable:{}", comparability.comparison_class));
    }
    if rollback.should_rollback {
        flags.push(format!("rollback:{}", rollback.reason));
    }
    if !promotion.approved && !promotion.status.is_empty() && promotion.status != "observe" {
        flags.push(format!("promotion_blocked:{}", promotion.reason));
    }
    flags
}

fn workflow_field_diffs(
    analyze: &Option<WorkflowPhaseSnapshot>,
    research: &Option<WorkflowPhaseSnapshot>,
    backtest: &Option<WorkflowPhaseSnapshot>,
    update: &Option<WorkflowPhaseSnapshot>,
) -> Vec<WorkflowFieldDiff> {
    let mut diffs = Vec::new();
    for (left, right) in [
        (research.as_ref(), backtest.as_ref()),
        (analyze.as_ref(), update.as_ref()),
        (research.as_ref(), update.as_ref()),
    ] {
        if let (Some(left), Some(right)) = (left, right) {
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "promotion_status",
                &left.promotion_status,
                &right.promotion_status,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "rollback_scope",
                &left.rollback_scope,
                &right.rollback_scope,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "workflow_phase",
                &left.workflow_phase,
                &right.workflow_phase,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "comparison_class",
                &left.comparison_class,
                &right.comparison_class,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_gate_status",
                &left.pre_bayes_gate_status,
                &right.pre_bayes_gate_status,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_policy_version",
                &left.pre_bayes_policy_version,
                &right.pre_bayes_policy_version,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_uses_soft_evidence",
                if left.pre_bayes_uses_soft_evidence {
                    "true"
                } else {
                    "false"
                },
                if right.pre_bayes_uses_soft_evidence {
                    "true"
                } else {
                    "false"
                },
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_soft_market_regime",
                &format!("{:?}", left.pre_bayes_soft_evidence.get("market_regime")),
                &format!("{:?}", right.pre_bayes_soft_evidence.get("market_regime")),
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_bridge_selected_entry_quality",
                &left
                    .pre_bayes_bridge_selected_entry_quality
                    .clone()
                    .unwrap_or_default(),
                &right
                    .pre_bayes_bridge_selected_entry_quality
                    .clone()
                    .unwrap_or_default(),
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_bridge_probability_gap",
                &left
                    .pre_bayes_bridge_probability_gap
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
                &right
                    .pre_bayes_bridge_probability_gap
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_multi_timeframe_direction_bias",
                &left.pre_bayes_multi_timeframe_direction_bias,
                &right.pre_bayes_multi_timeframe_direction_bias,
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_multi_timeframe_alignment_score",
                &left
                    .pre_bayes_multi_timeframe_alignment_score
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
                &right
                    .pre_bayes_multi_timeframe_alignment_score
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
            );
            push_workflow_field_diff(
                &mut diffs,
                left,
                right,
                "pre_bayes_multi_timeframe_entry_alignment_score",
                &left
                    .pre_bayes_multi_timeframe_entry_alignment_score
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
                &right
                    .pre_bayes_multi_timeframe_entry_alignment_score
                    .map(|value| format!("{value:.4}"))
                    .unwrap_or_default(),
            );
        }
    }
    diffs
}

fn push_workflow_field_diff(
    diffs: &mut Vec<WorkflowFieldDiff>,
    left: &WorkflowPhaseSnapshot,
    right: &WorkflowPhaseSnapshot,
    field: &str,
    left_value: &str,
    right_value: &str,
) {
    if left_value != right_value {
        diffs.push(WorkflowFieldDiff {
            left_phase: left.phase.clone(),
            right_phase: right.phase.clone(),
            field: field.to_string(),
            left_value: left_value.to_string(),
            right_value: right_value.to_string(),
            severity: if field == "promotion_status" || field == "rollback_scope" {
                "high".to_string()
            } else {
                "medium".to_string()
            },
        });
    }
}

fn workflow_disagreements(
    analyze: &Option<WorkflowPhaseSnapshot>,
    research: &Option<WorkflowPhaseSnapshot>,
    backtest: &Option<WorkflowPhaseSnapshot>,
    update: &Option<WorkflowPhaseSnapshot>,
) -> Vec<WorkflowDisagreement> {
    let mut disagreements = Vec::new();

    if let (Some(analyze), Some(update)) = (analyze, update) {
        if analyze
            .selected_direction
            .as_deref()
            .map(|direction| direction == "Bull" || direction == "Bear")
            .unwrap_or(false)
            && update.rollback_scope != "none"
        {
            disagreements.push(WorkflowDisagreement {
                id: "analyze_direction_vs_update_rollback".to_string(),
                severity: "high".to_string(),
                summary: "analyze directional bias conflicts with the latest update rollback state"
                    .to_string(),
                phases: vec![analyze.phase.clone(), update.phase.clone()],
                recommended_action: "review realized feedback against the current directional evidence before trusting deployment decisions".to_string(),
                evidence: vec![
                    format!(
                        "analyze.selected_direction={}",
                        analyze.selected_direction.clone().unwrap_or_default()
                    ),
                    format!("update.rollback_scope={}", update.rollback_scope),
                    format!(
                        "update.realized_outcome={}",
                        update.realized_outcome.clone().unwrap_or_default()
                    ),
                ],
                sources: Vec::new(),
            });
        }
    }

    if let (Some(research), Some(backtest)) = (research, backtest) {
        if research.promotion_status != backtest.promotion_status {
            disagreements.push(WorkflowDisagreement {
                id: "research_vs_backtest_promotion_status".to_string(),
                severity: "high".to_string(),
                summary: "research and backtest disagree on promotion status".to_string(),
                phases: vec![research.phase.clone(), backtest.phase.clone()],
                recommended_action:
                    "compare score deltas with backtest returns before promoting factor changes"
                        .to_string(),
                evidence: vec![
                    format!("research.promotion_status={}", research.promotion_status),
                    format!("backtest.promotion_status={}", backtest.promotion_status),
                ],
                sources: family_conflict_sources(research, backtest)
                    .into_iter()
                    .chain(factor_conflict_sources(research, backtest))
                    .collect(),
            });
        }
    }

    if let Some(analyze) = analyze {
        for downstream in [research.as_ref(), backtest.as_ref(), update.as_ref()]
            .into_iter()
            .flatten()
        {
            if analyze.pre_bayes_gate_status == "observe_only"
                && downstream.promotion_status == "promote"
            {
                let soft_divergences = pre_bayes_soft_divergence_evidence(analyze);
                disagreements.push(WorkflowDisagreement {
                    id: format!("analyze_pre_bayes_observe_only_vs_{}_promote", downstream.phase),
                    severity: "high".to_string(),
                    summary:
                        "analyze pre-bayes gate is observe-only but a downstream phase still promotes"
                            .to_string(),
                    phases: vec![analyze.phase.clone(), downstream.phase.clone()],
                    recommended_action:
                        "resolve pre-bayes evidence quality before trusting downstream promotion"
                            .to_string(),
                    evidence: vec![
                        format!(
                            "analyze.pre_bayes_gate_status={}",
                            analyze.pre_bayes_gate_status
                        ),
                        format!(
                            "analyze.pre_bayes_quality={:.3}",
                            analyze.pre_bayes_evidence_quality_score
                        ),
                        format!(
                            "analyze.pre_bayes_policy_version={}",
                            analyze.pre_bayes_policy_version
                        ),
                        format!(
                            "analyze.pre_bayes_uses_soft_evidence={}",
                            analyze.pre_bayes_uses_soft_evidence
                        ),
                        format!(
                            "analyze.pre_bayes_long_signal_probability={:.3}",
                            analyze.pre_bayes_long_signal_probability.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_short_signal_probability={:.3}",
                            analyze.pre_bayes_short_signal_probability.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_selected_entry_quality_probability={:.3}",
                            analyze
                                .pre_bayes_selected_entry_quality_probability
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_bridge_selected_entry_quality={}",
                            analyze
                                .pre_bayes_bridge_selected_entry_quality
                                .clone()
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_bridge_probability_gap={:.3}",
                            analyze.pre_bayes_bridge_probability_gap.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_direction_bias={}",
                            analyze.pre_bayes_multi_timeframe_direction_bias
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_alignment_score={:.3}",
                            analyze
                                .pre_bayes_multi_timeframe_alignment_score
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_entry_alignment_score={:.3}",
                            analyze
                                .pre_bayes_multi_timeframe_entry_alignment_score
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_soft_divergences={}",
                            if soft_divergences.is_empty() {
                                "none".to_string()
                            } else {
                                soft_divergences.join("|")
                            }
                        ),
                        format!(
                            "{}.promotion_status={}",
                            downstream.phase, downstream.promotion_status
                        ),
                    ],
                    sources: vec![WorkflowConflictSource {
                        scope: "pre_bayes_bridge".to_string(),
                        subject: "policy_version_and_selected_entry_quality".to_string(),
                        left_phase: analyze.phase.clone(),
                        left_value: format!(
                            "{}:{}",
                            analyze.pre_bayes_policy_version,
                            analyze
                                .pre_bayes_bridge_selected_entry_quality
                                .clone()
                                .unwrap_or_default()
                        ),
                        right_phase: downstream.phase.clone(),
                        right_value: downstream.promotion_status.clone(),
                        evidence: vec![
                            "observe_only gate conflicts with downstream promote".to_string(),
                            format!(
                                "uses_soft_evidence={}",
                                analyze.pre_bayes_uses_soft_evidence
                            ),
                            format!(
                                "long_short_signal_probability_gap={:.3}",
                                analyze.pre_bayes_bridge_probability_gap.unwrap_or_default()
                            ),
                            format!(
                                "multi_timeframe_direction_bias={}",
                                analyze.pre_bayes_multi_timeframe_direction_bias
                            ),
                            format!(
                                "soft_divergences={}",
                                if soft_divergences.is_empty() {
                                    "none".to_string()
                                } else {
                                    soft_divergences.join("|")
                                }
                            ),
                        ],
                    }],
                });
            }
            if analyze.pre_bayes_gate_status == "pass_neutralized"
                && downstream.promotion_status == "promote"
            {
                let soft_divergences = pre_bayes_soft_divergence_evidence(analyze);
                disagreements.push(WorkflowDisagreement {
                    id: format!(
                        "analyze_pre_bayes_neutralized_vs_{}_promote",
                        downstream.phase
                    ),
                    severity: "medium".to_string(),
                    summary:
                        "analyze pre-bayes gate is neutralized while a downstream phase still promotes"
                            .to_string(),
                    phases: vec![analyze.phase.clone(), downstream.phase.clone()],
                    recommended_action:
                        "review whether neutralized evidence is strong enough to justify promotion"
                            .to_string(),
                    evidence: vec![
                        format!(
                            "analyze.pre_bayes_gate_status={}",
                            analyze.pre_bayes_gate_status
                        ),
                        format!(
                            "analyze.pre_bayes_quality={:.3}",
                            analyze.pre_bayes_evidence_quality_score
                        ),
                        format!(
                            "analyze.pre_bayes_policy_version={}",
                            analyze.pre_bayes_policy_version
                        ),
                        format!(
                            "analyze.pre_bayes_uses_soft_evidence={}",
                            analyze.pre_bayes_uses_soft_evidence
                        ),
                        format!(
                            "analyze.pre_bayes_long_signal_probability={:.3}",
                            analyze.pre_bayes_long_signal_probability.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_short_signal_probability={:.3}",
                            analyze.pre_bayes_short_signal_probability.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_selected_entry_quality_probability={:.3}",
                            analyze
                                .pre_bayes_selected_entry_quality_probability
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_bridge_selected_entry_quality={}",
                            analyze
                                .pre_bayes_bridge_selected_entry_quality
                                .clone()
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_bridge_probability_gap={:.3}",
                            analyze.pre_bayes_bridge_probability_gap.unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_direction_bias={}",
                            analyze.pre_bayes_multi_timeframe_direction_bias
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_alignment_score={:.3}",
                            analyze
                                .pre_bayes_multi_timeframe_alignment_score
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_multi_timeframe_entry_alignment_score={:.3}",
                            analyze
                                .pre_bayes_multi_timeframe_entry_alignment_score
                                .unwrap_or_default()
                        ),
                        format!(
                            "analyze.pre_bayes_soft_divergences={}",
                            if soft_divergences.is_empty() {
                                "none".to_string()
                            } else {
                                soft_divergences.join("|")
                            }
                        ),
                        format!(
                            "{}.promotion_status={}",
                            downstream.phase, downstream.promotion_status
                        ),
                    ],
                    sources: vec![WorkflowConflictSource {
                        scope: "pre_bayes_bridge".to_string(),
                        subject: "policy_version_and_selected_entry_quality".to_string(),
                        left_phase: analyze.phase.clone(),
                        left_value: format!(
                            "{}:{}",
                            analyze.pre_bayes_policy_version,
                            analyze
                                .pre_bayes_bridge_selected_entry_quality
                                .clone()
                                .unwrap_or_default()
                        ),
                        right_phase: downstream.phase.clone(),
                        right_value: downstream.promotion_status.clone(),
                        evidence: vec![
                            "neutralized gate conflicts with downstream promote".to_string(),
                            format!(
                                "long_short_signal_probability_gap={:.3}",
                                analyze.pre_bayes_bridge_probability_gap.unwrap_or_default()
                            ),
                            format!(
                                "multi_timeframe_direction_bias={}",
                                analyze.pre_bayes_multi_timeframe_direction_bias
                            ),
                            format!(
                                "soft_divergences={}",
                                if soft_divergences.is_empty() {
                                    "none".to_string()
                                } else {
                                    soft_divergences.join("|")
                                }
                            ),
                        ],
                    }],
                });
            }
        }
    }

    for (left, right) in [
        (research.as_ref(), update.as_ref()),
        (backtest.as_ref(), update.as_ref()),
        (research.as_ref(), backtest.as_ref()),
    ] {
        if let (Some(left), Some(right)) = (left, right) {
            let score_promotes = left.promotion_status == "promote"
                && right.workflow_phase == "artifact_rollback_review";
            let reverse_score_promotes = right.promotion_status == "promote"
                && left.workflow_phase == "artifact_rollback_review";
            if score_promotes || reverse_score_promotes {
                let (promote_phase, artifact_phase) = if score_promotes {
                    (left, right)
                } else {
                    (right, left)
                };
                disagreements.push(WorkflowDisagreement {
                    id: format!(
                        "{}_vs_{}_artifact_consumption_gate",
                        promote_phase.phase, artifact_phase.phase
                    ),
                    severity: "high".to_string(),
                    summary:
                        "score-based promotion conflicts with an artifact consumption rollback gate"
                            .to_string(),
                    phases: vec![promote_phase.phase.clone(), artifact_phase.phase.clone()],
                    recommended_action:
                        "resolve artifact consumption regression before trusting score-based promotion"
                            .to_string(),
                    evidence: vec![
                        format!(
                            "{}.promotion_status={}",
                            promote_phase.phase, promote_phase.promotion_status
                        ),
                        format!(
                            "{}.workflow_phase={}",
                            artifact_phase.phase, artifact_phase.workflow_phase
                        ),
                        format!(
                            "{}.rollback_scope={}",
                            artifact_phase.phase, artifact_phase.rollback_scope
                        ),
                    ],
                    sources: family_conflict_sources(promote_phase, artifact_phase)
                        .into_iter()
                        .chain(factor_conflict_sources(promote_phase, artifact_phase))
                        .collect(),
                });
            }
        }
    }

    if let (Some(backtest), Some(update)) = (backtest, update) {
        if backtest.rollback_scope == "none" && update.rollback_scope != "none" {
            disagreements.push(WorkflowDisagreement {
                id: "backtest_stable_vs_update_rollback".to_string(),
                severity: "medium".to_string(),
                summary: "backtest stayed stable but the latest realized update recommends rollback".to_string(),
                phases: vec![backtest.phase.clone(), update.phase.clone()],
                recommended_action: "inspect live execution drift and feedback provenance before keeping or rolling back changes".to_string(),
                evidence: vec![
                    format!("backtest.rollback_scope={}", backtest.rollback_scope),
                    format!("update.rollback_scope={}", update.rollback_scope),
                ],
                sources: family_conflict_sources(backtest, update)
                    .into_iter()
                    .chain(factor_conflict_sources(backtest, update))
                    .collect(),
            });
        }
    }

    if let (Some(research), Some(backtest)) = (research, backtest) {
        let sources = family_conflict_sources(research, backtest);
        if !sources.is_empty() {
            disagreements.push(WorkflowDisagreement {
                id: "research_backtest_family_conflicts".to_string(),
                severity: "medium".to_string(),
                summary: "research and backtest disagree on family-level decisions".to_string(),
                phases: vec![research.phase.clone(), backtest.phase.clone()],
                recommended_action: "inspect family score deltas and rollback scopes before acting on a single phase".to_string(),
                evidence: sources
                    .iter()
                    .map(|source| {
                        format!(
                            "family:{} {}={} {}={}",
                            source.subject,
                            source.left_phase,
                            source.left_value,
                            source.right_phase,
                            source.right_value
                        )
                    })
                    .collect(),
                sources,
            });
        }
        let sources = factor_conflict_sources(research, backtest);
        if !sources.is_empty() {
            disagreements.push(WorkflowDisagreement {
                id: "research_backtest_factor_conflicts".to_string(),
                severity: "medium".to_string(),
                summary: "research and backtest disagree on factor-level actions".to_string(),
                phases: vec![research.phase.clone(), backtest.phase.clone()],
                recommended_action: "check factor scorecards and iteration queue ordering before selecting the next factor edit".to_string(),
                evidence: sources
                    .iter()
                    .map(|source| {
                        format!(
                            "factor:{} {}={} {}={}",
                            source.subject,
                            source.left_phase,
                            source.left_value,
                            source.right_phase,
                            source.right_value
                        )
                    })
                    .collect(),
                sources,
            });
        }
    }

    disagreements
}

fn pre_bayes_soft_divergence_evidence(snapshot: &WorkflowPhaseSnapshot) -> Vec<String> {
    snapshot
        .pre_bayes_soft_evidence
        .iter()
        .filter_map(|(node, distribution)| {
            let dominant = distribution
                .iter()
                .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))?;
            let filtered = snapshot.pre_bayes_filtered_assignments.get(node)?;
            (dominant.0 != filtered).then(|| {
                format!(
                    "{}:{}->{:.3}:filtered={}",
                    node, dominant.0, dominant.1, filtered
                )
            })
        })
        .collect()
}

fn family_conflict_sources(
    left: &WorkflowPhaseSnapshot,
    right: &WorkflowPhaseSnapshot,
) -> Vec<WorkflowConflictSource> {
    let left_map = left
        .family_states
        .iter()
        .filter_map(|item| {
            let mut parts = item.splitn(3, ':');
            Some((
                parts.next()?.to_string(),
                format!("{}:{}", parts.next()?, parts.next()?),
            ))
        })
        .collect::<BTreeMap<_, _>>();
    let right_map = right
        .family_states
        .iter()
        .filter_map(|item| {
            let mut parts = item.splitn(3, ':');
            Some((
                parts.next()?.to_string(),
                format!("{}:{}", parts.next()?, parts.next()?),
            ))
        })
        .collect::<BTreeMap<_, _>>();
    left_map
        .iter()
        .filter_map(|(family, left_value)| {
            let right_value = right_map.get(family)?;
            (left_value != right_value).then(|| WorkflowConflictSource {
                scope: "family".to_string(),
                subject: family.clone(),
                left_phase: left.phase.clone(),
                left_value: left_value.clone(),
                right_phase: right.phase.clone(),
                right_value: right_value.clone(),
                evidence: workflow_numeric_family_evidence(left, right, family),
            })
        })
        .collect()
}

fn factor_conflict_sources(
    left: &WorkflowPhaseSnapshot,
    right: &WorkflowPhaseSnapshot,
) -> Vec<WorkflowConflictSource> {
    let left_map = left
        .factor_actions
        .iter()
        .filter_map(|item| {
            let mut parts = item.splitn(3, ':');
            Some((parts.next()?.to_string(), parts.next()?.to_string()))
        })
        .collect::<BTreeMap<_, _>>();
    let right_map = right
        .factor_actions
        .iter()
        .filter_map(|item| {
            let mut parts = item.splitn(3, ':');
            Some((parts.next()?.to_string(), parts.next()?.to_string()))
        })
        .collect::<BTreeMap<_, _>>();
    left_map
        .iter()
        .filter_map(|(factor, left_value)| {
            let right_value = right_map.get(factor)?;
            (left_value != right_value).then(|| WorkflowConflictSource {
                scope: "factor".to_string(),
                subject: factor.clone(),
                left_phase: left.phase.clone(),
                left_value: left_value.clone(),
                right_phase: right.phase.clone(),
                right_value: right_value.clone(),
                evidence: workflow_numeric_factor_evidence(left, right, factor),
            })
        })
        .collect()
}

fn workflow_numeric_family_evidence(
    left: &WorkflowPhaseSnapshot,
    right: &WorkflowPhaseSnapshot,
    family: &str,
) -> Vec<String> {
    let left_score = left.family_score_map.get(family).copied();
    let right_score = right.family_score_map.get(family).copied();
    match (left_score, right_score) {
        (Some(left_score), Some(right_score)) => vec![
            format!("left_avg_score={:.4}", left_score),
            format!("right_avg_score={:.4}", right_score),
            format!("avg_score_delta={:.4}", right_score - left_score),
        ],
        _ => Vec::new(),
    }
}

fn workflow_numeric_factor_evidence(
    left: &WorkflowPhaseSnapshot,
    right: &WorkflowPhaseSnapshot,
    factor: &str,
) -> Vec<String> {
    let left_score = left.factor_score_map.get(factor).copied();
    let right_score = right.factor_score_map.get(factor).copied();
    match (left_score, right_score) {
        (Some(left_score), Some(right_score)) => vec![
            format!("left_composite_score={:.4}", left_score),
            format!("right_composite_score={:.4}", right_score),
            format!("composite_score_delta={:.4}", right_score - left_score),
        ],
        _ => Vec::new(),
    }
}

fn build_multi_timeframe_training_observations(
    primary_data: &str,
) -> Result<(Vec<Vec<f64>>, Vec<String>, usize)> {
    let resolved = resolve_multi_timeframe_inputs(primary_data, None, None, None, None, None, None);
    let mut observations = Vec::new();
    let mut summary = build_multi_timeframe_summary(primary_data, &resolved)?;
    let mut candles_total = 0usize;

    for interval in ["1d", "4h", "1h", "15m", "5m", "1m"] {
        let Some(path) = resolved.get(interval) else {
            continue;
        };
        let candles = load_candles(path)?;
        candles_total += candles.len();
        let features = build_frame_features(&candles)?;
        summary.push(format!(
            "train_interval={} candles={} observations={}",
            interval,
            candles.len(),
            features.observations.len()
        ));
        observations.extend(features.observations);
    }

    if observations.is_empty() {
        let candles = load_candles(primary_data)?;
        candles_total = candles.len();
        let features = build_frame_features(&candles)?;
        observations = features.observations;
        summary.push("train_multi_timeframe_source=primary_only".to_string());
    } else {
        summary.push(format!(
            "train_multi_timeframe_source={} total_observations={}",
            resolved.source,
            observations.len()
        ));
    }

    Ok((observations, summary, candles_total))
}

fn native_frame_weight(interval: &str) -> f64 {
    match interval {
        "1d" => 0.24,
        "4h" => 0.20,
        "1h" => 0.18,
        "15m" => 0.16,
        "5m" => 0.12,
        "1m" => 0.10,
        _ => 0.10,
    }
}

fn weighted_regime_probs(signals: &[NativeFrameComputation]) -> RegimeProbs {
    let total_weight = signals
        .iter()
        .map(|signal| signal.weight)
        .sum::<f64>()
        .max(f64::EPSILON);
    RegimeProbs {
        accumulation: signals
            .iter()
            .map(|signal| signal.regime_probs.accumulation * signal.weight)
            .sum::<f64>()
            / total_weight,
        manipulation_expansion: signals
            .iter()
            .map(|signal| signal.regime_probs.manipulation_expansion * signal.weight)
            .sum::<f64>()
            / total_weight,
        distribution: signals
            .iter()
            .map(|signal| signal.regime_probs.distribution * signal.weight)
            .sum::<f64>()
            / total_weight,
    }
}

fn weighted_majority_label<'a, I>(
    labels: I,
    positive: &str,
    negative: &str,
    neutral: &str,
) -> String
where
    I: IntoIterator<Item = (&'a str, f64)>,
{
    let mut positive_weight = 0.0;
    let mut negative_weight = 0.0;
    let mut neutral_weight = 0.0;
    for (label, weight) in labels {
        match label {
            value if value == positive => positive_weight += weight,
            value if value == negative => negative_weight += weight,
            _ => neutral_weight += weight,
        }
    }
    if positive_weight > negative_weight && positive_weight >= neutral_weight {
        positive.to_string()
    } else if negative_weight > positive_weight && negative_weight >= neutral_weight {
        negative.to_string()
    } else {
        neutral.to_string()
    }
}

fn native_frame_computations(
    params: &HMMParams,
    native_frames: AnalyzeNativeFrames<'_>,
) -> Result<Vec<NativeFrameComputation>> {
    let mut signals = Vec::new();
    for (interval, candles) in [
        ("1d", native_frames.d1),
        ("4h", native_frames.h4),
        ("1h", native_frames.h1),
        ("15m", native_frames.m15),
        ("5m", native_frames.m5),
        ("1m", native_frames.m1),
    ] {
        let Some(candles) = candles else {
            continue;
        };
        let features = build_frame_features(candles)?;
        let (log_alpha, log_likelihood) = ForwardBackward::forward(&features.observations, params);
        let log_beta = ForwardBackward::backward(&features.observations, params);
        let gamma = ForwardBackward::compute_gamma(&log_alpha, &log_beta, log_likelihood);
        let (_, viterbi_log_likelihood) = Viterbi::decode(&features.observations, params);
        signals.push(NativeFrameComputation {
            weight: native_frame_weight(interval),
            regime_probs: regime_probs_from_log_gamma(gamma.last())?,
            log_likelihood,
            viterbi_log_likelihood,
            features,
        });
    }
    Ok(signals)
}

fn train_command(symbol: &str, data: &str, epochs: usize, state_dir: &str) -> Result<()> {
    let (observations, multi_timeframe_summary, candles_total) =
        build_multi_timeframe_training_observations(data)?;
    let initial_params = load_or_init_hmm_params(symbol, state_dir);
    let trained_params = BaumWelch::fit(&observations, &initial_params, epochs, 1e-4);
    let (_, log_likelihood) = ForwardBackward::forward(&observations, &trained_params);
    let (states, viterbi_log_likelihood) = Viterbi::decode(&observations, &trained_params);
    let learning_state = load_learning_state(state_dir, symbol)?;
    let previous_runs: Vec<TrainRunRecord> =
        load_state_or_default(state_dir, symbol, TRAIN_RUNS_FILE)?;
    let provenance = run_provenance(
        &learning_state,
        &["train", data, &epochs.to_string()],
        compute_hash(&["train", symbol, data, &epochs.to_string()]),
    );
    let dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &provenance,
    );
    let workflow_state = WorkflowState {
        phase: "train_review_ready".to_string(),
        reason: "multi_timeframe_hmm_training_completed".to_string(),
    };
    let mut agent_action_plan = AgentActionPlan {
        summary: "review multi-timeframe HMM training outcome".to_string(),
        items: vec![AgentActionItem {
            stage: "train".to_string(),
            blocking: false,
            priority: "medium".to_string(),
            title: "Review Train Run".to_string(),
            rationale: format!(
                "epochs={} observations={} final_state={}",
                epochs,
                observations.len(),
                states.last().copied().map(state_name).unwrap_or("Unknown")
            ),
            expected_output: "A training review confirming whether the latest HMM state should feed the next analyze/research cycle".to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: "hmm_params".to_string(),
                direction: "trained_multi_timeframe".to_string(),
                rationale: "multi_timeframe_hmm_training_completed".to_string(),
            }],
            suggested_files: vec!["src/main.rs".to_string(), "src/hmm/baum_welch.rs".to_string()],
            suggested_commands: vec!["ict-engine analyze --data-htf <file> --data-mtf <file> --data-ltf <file>".to_string()],
        }],
    };
    let recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: Some(AnalyzeCommandSource::Files {
            data_htf: data.to_string(),
            data_mtf: data.to_string(),
            data_ltf: data.to_string(),
        }),
        research_data: Some(data.to_string()),
        paired_data: None,
        update_outcome: None,
        update_entry_signal: None,
        update_feedback_file: pending_update_artifact_path(state_dir, symbol),
        user_data_selection_required: true,
    });
    concretize_action_plan_commands(&mut agent_action_plan, &recommended_commands);
    let recommended_next_command =
        recommended_next_command(&agent_action_plan, &recommended_commands);
    let mut agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &workflow_state,
        "train_review_ready",
        &recommended_next_command,
        &recommended_commands,
        &dataset_comparability,
        &[],
        &[],
        None,
        None,
        None,
        None,
    );
    agent_context_bundle.multi_timeframe_summary = multi_timeframe_summary.clone();
    let agent_context_bundle_minimal = build_agent_context_bundle_minimal(&agent_context_bundle);
    let mut agent_prompts = AgentPromptPack {
        version: PROMPT_PACK_VERSION.to_string(),
        workflow: format!(
            "Review the latest multi-timeframe HMM training result for {} before the next analyze/research cycle.",
            symbol
        ),
        prompts: vec![dataset_audit_prompt(symbol, data, None, candles_total, None, "train")],
    };
    agent_prompts.prompts.push(AgentPrompt::new(
        "train_review",
        "train",
        "high",
        "Review whether the latest multi-timeframe HMM training result is usable.",
        "You are the train-review agent. Use the training observations, likelihoods, and multi-timeframe summary to decide whether the latest HMM training result should feed the next analysis cycle or be treated cautiously.",
        format!(
            "Symbol={} epochs={} observations={} final_state={} log_likelihood={:.4} viterbi_log_likelihood={:.4} multi_timeframe_summary={:?}",
            symbol,
            epochs,
            observations.len(),
            states.last().copied().map(state_name).unwrap_or("Unknown"),
            log_likelihood,
            viterbi_log_likelihood,
            multi_timeframe_summary
        ),
        vec![
            "Prefer using the trained HMM only when likelihoods are finite and multi-timeframe coverage is present".to_string(),
            "If multi-timeframe coverage is missing, downgrade confidence in the next analyze cycle".to_string(),
        ],
        vec!["src/main.rs".to_string(), "src/hmm/baum_welch.rs".to_string()],
    ));

    save_state(state_dir, symbol, HMM_STATE_FILE, &trained_params)?;
    append_train_run(
        state_dir,
        symbol,
        TrainRunRecord {
            run_id: format!(
                "train:{}:{}",
                symbol,
                Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
            ),
            timestamp: Utc::now(),
            symbol: symbol.to_string(),
            provenance,
            dataset_comparability,
            source_command: "train".to_string(),
            data_path: data.to_string(),
            epochs,
            candles: candles_total,
            observations: observations.len(),
            final_state: states
                .last()
                .copied()
                .map(state_name)
                .unwrap_or("Unknown")
                .to_string(),
            log_likelihood,
            viterbi_log_likelihood,
            workflow_state,
            agent_action_plan,
            recommended_commands,
            recommended_next_command,
            agent_context_bundle,
            agent_context_bundle_minimal,
            agent_prompts: agent_prompts.clone(),
            prompt_workflow: agent_prompts.workflow.clone(),
            multi_timeframe_summary: multi_timeframe_summary.clone(),
        },
    )?;
    let workflow_snapshot = refresh_workflow_snapshot(state_dir, symbol)?;

    println!(
        "train symbol={} state_dir={} epochs={} candles={} observations={} final_state={} log_likelihood={:.4} viterbi_log_likelihood={:.4} multi_timeframe_summary={:?} workflow_phase={} saved={}/{}",
        symbol,
        state_dir,
        epochs,
        candles_total,
        observations.len(),
        states.last().copied().map(state_name).unwrap_or("Unknown"),
        log_likelihood,
        viterbi_log_likelihood,
        multi_timeframe_summary,
        workflow_snapshot.current_focus_phase,
        symbol,
        HMM_STATE_FILE,
    );
    Ok(())
}

fn backtest_command(
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    state_dir: &str,
    warmup_bars: usize,
    hold_bars: usize,
    spread_bps: f64,
    slippage_bps: f64,
    fee_bps: f64,
    ambiguous_bar_policy: &str,
    online_learn: bool,
) -> Result<()> {
    let candles = load_candles(data)?;
    let paired_candles = paired_data.map(load_candles).transpose()?;
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let _ = run_factor_research(
        symbol,
        data,
        ResearchObjectiveMode::ExpansionManipulation,
        None,
        None,
        None,
        None,
        None,
        None,
        paired_data,
        None,
        state_dir,
    )?;
    let mut learning_state = load_learning_state(state_dir, symbol)?;
    let previous_rankings = learning_state.factor_rankings.clone();
    let previous_trade_outcome_cpt = trade_outcome_cpt_snapshot(&network)?;
    let realism =
        parse_execution_realism_config(spread_bps, slippage_bps, fee_bps, ambiguous_bar_policy)?;
    let (report, updated_network, trades) = run_probabilistic_backtest(
        symbol,
        state_dir,
        &candles,
        paired_candles.as_deref(),
        warmup_bars,
        hold_bars,
        &realism,
        online_learn,
        &params,
        &network,
        &mut learning_state,
    )?;
    save_learning_state(state_dir, symbol, &learning_state)?;
    save_state(state_dir, symbol, BBN_STATE_FILE, &updated_network)?;
    append_trade_history(state_dir, symbol, &trades)?;
    let report = finalize_backtest_report(
        report,
        symbol,
        data,
        paired_data,
        &candles,
        paired_candles.as_deref(),
        &learning_state,
        &previous_rankings,
        &previous_trade_outcome_cpt,
        &updated_network,
        state_dir,
        warmup_bars,
        hold_bars,
        &realism,
        online_learn,
    )?;
    let realism_summary = format!(
        "execution_realism=spread:{:.2}bps slippage:{:.2}bps fee:{:.2}bps policy={} trades={} comparable={}",
        report.spread_bps,
        report.slippage_bps,
        report.fee_bps,
        report.ambiguous_bar_policy,
        report.trades,
        report.dataset_comparability.comparable
    );
    let zero_trade_risk = if report.trades == 0 {
        vec!["no_trades_generated_under_current_constraints".to_string()]
    } else {
        Vec::new()
    };
    let compact_report = build_backtest_result_artifact(
        format!("backtest:{}", symbol),
        &[realism_summary.clone()],
        &[
            format!("symbol={}", symbol),
            format!("trades={}", report.trades),
        ],
        &zero_trade_risk,
        &[],
        report.dataset_comparability.comparable,
        &[],
    );
    let human_backtest_summary = if report.trades == 0 {
        format!(
            "Backtest ran with {} and produced no trades under the current constraints.",
            realism_summary
        )
    } else {
        format!(
            "Backtest ran with {} and produced {} trades.",
            realism_summary, report.trades
        )
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "compact_backtest_report": compact_report,
            "human_backtest_summary": human_backtest_summary,
        }))?
    );
    Ok(())
}

fn emit_update_output(report: &UpdateReport, ensemble: bool) -> Result<()> {
    let reflection_evidence = report
        .agent_prompts
        .prompts
        .iter()
        .map(|prompt| format!("{}:{}:{}", prompt.stage, prompt.id, prompt.objective))
        .collect::<Vec<_>>();
    let reflection_next_candidates = report
        .recommended_next_command
        .split(';')
        .map(str::trim)
        .filter(|candidate| !candidate.is_empty())
        .map(str::to_string)
        .collect::<Vec<_>>();
    let reflection_bundle = build_reflection_bundle(
        &report.symbol,
        report.provenance.data_fingerprint.clone(),
        report.agent_prompts.workflow.clone(),
        report.workflow_state.phase.clone(),
        report
            .agent_action_plan
            .items
            .first()
            .map(|item| item.title.clone())
            .filter(|title| !title.is_empty())
            .unwrap_or_else(|| report.realized_outcome.clone()),
        report.realized_outcome.clone(),
        &reflection_evidence,
        &reflection_next_candidates,
    );
    let ensemble_surface = if ensemble {
        report
            .workflow_snapshot
            .latest_ensemble_vote
            .as_ref()
            .map(|vote| {
                let persisted_scorecards =
                    load_ensemble_executor_scorecards(&report.state_dir, &report.symbol)
                        .unwrap_or_default();
                let (scorecards, scorecard_source) =
                    resolved_vote_scorecards(&persisted_scorecards, vote);
                serde_json::json!({
                    "ensemble_vote": vote,
                    "executor_scorecards": scorecards,
                    "executor_scorecard_source": scorecard_source,
                })
            })
    } else {
        None
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "reflection_bundle": reflection_bundle,
            "ensemble": ensemble_surface,
        }))?
    );
    Ok(())
}

fn update_command(
    symbol: &str,
    outcome: &str,
    entry_signal: Option<&str>,
    feedback_file: Option<&str>,
    state_dir: &str,
    pnl: Option<f64>,
    regime: Option<&str>,
    direction: Option<&str>,
    ensemble: bool,
) -> Result<()> {
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;

    let update_run_id = format!(
        "update:{}:{}",
        symbol,
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    );
    let mut network = load_or_init_trading_network(symbol, state_dir)?;
    let previous_runs: Vec<UpdateRunRecord> =
        load_state_or_default(state_dir, symbol, UPDATE_RUNS_FILE)?;
    let mut learning_state = load_learning_state(state_dir, symbol)?;
    let previous_rankings = learning_state.factor_rankings.clone();
    let outcome_label = normalize_trade_outcome_label(outcome);
    let entry_signal = entry_signal.unwrap_or("medium");
    let mut consumed_pending_update_artifact: Option<PendingUpdateArtifact> = None;
    let feedback = if let Some(path) = feedback_file {
        let content = std::fs::read_to_string(path)?;
        match serde_json::from_str::<FeedbackRecord>(&content) {
            Ok(feedback) => feedback_record_from_artifact(
                PendingUpdateArtifact {
                    template_feedback: feedback,
                    ..PendingUpdateArtifact::default()
                },
                &outcome_label,
                pnl,
                regime,
                direction,
            ),
            Err(_) => {
                let artifact = serde_json::from_str::<PendingUpdateArtifact>(&content)?;
                consumed_pending_update_artifact = Some(artifact.clone());
                feedback_record_from_artifact(artifact, &outcome_label, pnl, regime, direction)
            }
        }
    } else if state_exists(state_dir, symbol, PENDING_UPDATE_ARTIFACT_FILE) {
        let artifact = load_pending_update_artifact(state_dir, symbol)?;
        consumed_pending_update_artifact = Some(artifact.clone());
        feedback_record_from_artifact(artifact, &outcome_label, pnl, regime, direction)
    } else {
        FeedbackRecord {
            timestamp: Utc::now(),
            symbol: symbol.to_string(),
            source: "update_command".to_string(),
            run_id: None,
            trade_id: None,
            prompt_version: Some(PROMPT_PACK_VERSION.to_string()),
            factor_version: None,
            data_fingerprint: None,
            factors_used: Vec::new(),
            model_probabilities_before_trade: ModelProbabilitySnapshot {
                selected_direction: normalize_direction_label(direction.unwrap_or("neutral")),
                selected_probability: 0.0,
                long_score: 0.0,
                short_score: 0.0,
                win_prob_long: 0.0,
                win_prob_short: 0.0,
                uncertainty: 0.0,
            },
            realized_outcome: outcome_label.clone(),
            pnl: pnl.unwrap_or_else(|| match outcome_label.as_str() {
                "win" => 0.01,
                "loss" => -0.01,
                _ => 0.0,
            }),
            regime_at_entry: normalize_regime_label(regime.unwrap_or("manipulation_expansion")),
        }
    };
    let consumed_execution_candidate_artifact = latest_execution_candidate_for_source_run(
        state_dir,
        symbol,
        consumed_pending_update_artifact
            .as_ref()
            .and_then(|artifact| artifact.source_run_id.as_deref()),
    )?;
    let consumed_analyze_context = consumed_analyze_context_for_update(
        state_dir,
        symbol,
        consumed_pending_update_artifact.as_ref(),
        consumed_execution_candidate_artifact.as_ref(),
    )?;
    let feedback = enrich_feedback_record(
        feedback,
        &update_run_id,
        format!("{}:{}:{}", symbol, entry_signal, outcome_label),
        &learning_state,
        &compute_hash(&[
            "update",
            symbol,
            entry_signal,
            &outcome_label,
            direction.unwrap_or("neutral"),
        ]),
    );
    let consumed_feedback_pnl = feedback.pnl;
    let entry_quality = normalize_entry_quality_label(entry_signal);
    let factor_alignment = factor_alignment_label_from_feedback(&feedback);
    let factor_uncertainty = factor_uncertainty_label_from_feedback(&feedback);
    let evidence = trade_evidence_from_labels(
        &network,
        &[
            ("entry_quality", entry_quality.as_str()),
            ("factor_alignment", factor_alignment.as_str()),
            ("factor_uncertainty", factor_uncertainty.as_str()),
        ],
    )?;
    let previous_updated = network
        .nodes
        .get("trade_outcome")
        .and_then(|node| node.probabilities_for_evidence(&evidence).ok());
    let new_feedback = learning_state.merge_feedback_records(&[feedback]);
    let feedback_records_applied = new_feedback.len();

    if let Some(feedback) = new_feedback.first() {
        let realized_state_index = network
            .nodes
            .get("trade_outcome")
            .and_then(|node| {
                node.state_index(&normalize_trade_outcome_label(&feedback.realized_outcome))
            })
            .ok_or_else(|| anyhow!("unknown outcome state '{}'", feedback.realized_outcome))?;

        CPTUpdater::default().update_from_trade(
            &mut network,
            &evidence,
            TradeOutcome {
                node_id: "trade_outcome".into(),
                realized_state_index,
            },
        )?;
        WeightUpdater::default().apply_feedback(&mut learning_state, &new_feedback);
    }

    let updated_node = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let updated = updated_node.probabilities_for_evidence(&evidence)?;
    save_state(state_dir, symbol, BBN_STATE_FILE, &network)?;
    save_learning_state(state_dir, symbol, &learning_state)?;

    let factor_ranking = learning_state.factor_rankings.clone();
    let factor_iteration_queue = learning_state.iteration_queue();
    let factor_family_decisions = learning_state.family_decisions();
    let feedback_history_summary = learning_state.summary();
    let trade_outcome_map = probability_map(&updated_node.states, &updated);
    let trade_outcome_deltas = probability_diffs(
        &previous_updated.map(|values| probability_map(&updated_node.states, &values)),
        &trade_outcome_map,
    );
    let factor_score_deltas = ranking_diffs(&previous_rankings, &factor_ranking);
    let agent_prompts = build_update_agent_prompts(
        symbol,
        &factor_ranking,
        &factor_iteration_queue,
        &feedback_history_summary,
        &trade_outcome_map,
        &entry_quality,
        &factor_alignment,
        &factor_uncertainty,
        &outcome_label,
        feedback_records_applied,
        consumed_analyze_context.pre_bayes_evidence_filter.as_ref(),
        consumed_analyze_context
            .pre_bayes_entry_quality_bridge
            .as_ref(),
        &consumed_analyze_context.multi_timeframe_summary,
    );
    let mut agent_prompts = agent_prompts;
    agent_prompts.prompts.insert(
        0,
        dataset_audit_prompt(
            symbol,
            "update-command",
            None,
            feedback_records_applied.max(1),
            None,
            "update",
        ),
    );
    agent_prompts.prompts.push(update_diff_prompt(
        symbol,
        &trade_outcome_deltas,
        &factor_score_deltas,
        feedback_records_applied == 0,
    ));
    let mut ensemble_executor_scorecards = load_canonical_executor_scorecards(
        state_dir,
        symbol,
        consumed_execution_candidate_artifact
            .as_ref()
            .and_then(|artifact| artifact.source_run_id.as_deref()),
    )?;
    let ensemble_quality_adjustment = match outcome {
        "win" => 20,
        "loss" => -20,
        _ => 0,
    };
    apply_update_outcome_to_executor_scorecards(
        &mut ensemble_executor_scorecards,
        outcome,
        ensemble_quality_adjustment,
    );

    let report = UpdateReport {
        symbol: symbol.to_string(),
        timestamp: Utc::now(),
        state_dir: state_dir.to_string(),
        provenance: run_provenance(
            &learning_state,
            &[
                "update",
                entry_signal,
                &outcome_label,
                &feedback_records_applied.to_string(),
            ],
            compute_hash(&[
                "update-command",
                symbol,
                &outcome_label,
                &factor_alignment,
                &factor_uncertainty,
            ]),
        ),
        decision_thresholds: decision_thresholds(),
        dataset_comparability: DatasetComparability::default(),
        promotion_decision: PromotionDecision::default(),
        rollback_recommendation: RollbackRecommendation::default(),
        trade_outcome_deltas: trade_outcome_deltas.clone(),
        factor_score_deltas: factor_score_deltas.clone(),
        normalized_entry_quality: entry_quality,
        factor_alignment,
        factor_uncertainty,
        realized_outcome: outcome_label,
        feedback_records_applied,
        duplicate_feedback_skipped: feedback_records_applied == 0,
        consumed_pending_update_artifact_id: consumed_pending_update_artifact
            .as_ref()
            .map(|artifact| artifact.artifact_id.clone()),
        consumed_execution_candidate_artifact_id: consumed_execution_candidate_artifact
            .as_ref()
            .map(|artifact| artifact.artifact_id.clone()),
        consumed_artifact_path: consumed_pending_update_artifact.as_ref().map(|_| {
            std::path::Path::new(state_dir)
                .join(symbol)
                .join(PENDING_UPDATE_ARTIFACT_FILE)
                .to_string_lossy()
                .to_string()
        }),
        consumed_analyze_run_id: consumed_analyze_context.analyze_run_id.clone(),
        consumed_pre_bayes_evidence_filter: consumed_analyze_context
            .pre_bayes_evidence_filter
            .clone(),
        consumed_pre_bayes_entry_quality_bridge: consumed_analyze_context
            .pre_bayes_entry_quality_bridge
            .clone(),
        consumed_multi_timeframe_summary: consumed_analyze_context.multi_timeframe_summary.clone(),
        updated_trade_outcome: trade_outcome_map.clone(),
        factor_ranking,
        factor_iteration_queue,
        factor_family_decisions,
        factor_family_outcomes: Vec::new(),
        factor_family_diffs: Vec::new(),
        factor_family_history: Vec::new(),
        decision_history_summary: DecisionHistorySummary::default(),
        agent_action_plan: AgentActionPlan::default(),
        workflow_state: WorkflowState::default(),
        agent_context_bundle: AgentContextBundle::default(),
        agent_context_bundle_minimal: AgentContextBundleMinimal::default(),
        recommended_commands: CommandRecommendations::default(),
        recommended_next_command: "recommended_command_unavailable".to_string(),
        agent_prompts: agent_prompts.clone(),
        feedback_history_summary,
        artifact_action_summary: Vec::new(),
        artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary::default(),
        artifact_decision_section: ict_engine::state::ArtifactDecisionSection::default(),
        workflow_snapshot: WorkflowSnapshot::default(),
    };
    let mut report = report;
    report.dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &report.provenance,
    );
    let mut artifact_preview_ledger = load_artifact_ledger(state_dir, symbol)?;
    let preview_consumed_at = Utc::now();
    if let Some(artifact_id) = &report.consumed_pending_update_artifact_id {
        apply_artifact_consumption_preview(
            &mut artifact_preview_ledger,
            artifact_id,
            &update_run_id,
            &report.realized_outcome,
            consumed_feedback_pnl,
            preview_consumed_at,
        );
    }
    if let Some(artifact_id) = &report.consumed_execution_candidate_artifact_id {
        apply_artifact_consumption_preview(
            &mut artifact_preview_ledger,
            artifact_id,
            &update_run_id,
            &report.realized_outcome,
            consumed_feedback_pnl,
            preview_consumed_at,
        );
    }
    let artifact_consumed_impact_summary =
        build_artifact_consumed_impact_summary(&artifact_preview_ledger);
    let artifact_consumed_gate = artifact_consumed_decision_gate(&artifact_consumed_impact_summary);
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_from_ledger(&artifact_preview_ledger);
    let thresholds = decision_thresholds();
    report.promotion_decision = derive_promotion_decision(
        &report.factor_ranking,
        &report.factor_score_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.rollback_recommendation = derive_rollback_recommendation(
        &report.factor_ranking,
        &report.factor_score_deltas,
        &report.trade_outcome_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.factor_family_outcomes = derive_family_outcomes(
        &report.factor_family_decisions,
        &thresholds,
        &report.dataset_comparability,
        Some(&artifact_family_trends),
    );
    report.factor_family_diffs = family_diffs(
        previous_runs
            .last()
            .map(|run| run.factor_family_decisions.as_slice())
            .unwrap_or(&[]),
        &report.factor_family_decisions,
    );
    report.factor_family_history = family_history_from_runs(previous_runs.iter().map(|run| {
        (
            run.run_id.clone(),
            run.timestamp,
            run.factor_family_decisions.clone(),
        )
    }));
    report.decision_history_summary = decision_history_summary(previous_runs.iter().map(|run| {
        (
            run.promotion_decision.clone(),
            run.rollback_recommendation.clone(),
        )
    }));
    report.agent_action_plan = build_agent_action_plan(
        &format!(
            "update_result:{}",
            if report.duplicate_feedback_skipped {
                "duplicate_skipped"
            } else {
                "applied"
            }
        ),
        &report.promotion_decision,
        &report.rollback_recommendation,
        &report.factor_iteration_queue,
        &report.factor_family_outcomes,
    );
    if let Some(filter) = report.consumed_pre_bayes_evidence_filter.as_ref() {
        augment_action_plan_with_consumed_pre_bayes_context(
            &mut report.agent_action_plan,
            filter,
            report.consumed_pre_bayes_entry_quality_bridge.as_ref(),
        );
    }
    augment_action_plan_with_artifact_trends(
        &mut report.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_decision_summary =
        artifact_decision_summary_from_ledger(&artifact_preview_ledger);
    report.artifact_decision_section = artifact_decision_section_from_parts(
        &report.artifact_decision_summary,
        &report.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    append_artifact_decision_prompt(
        &mut report.agent_prompts,
        symbol,
        &report.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );
    report.workflow_state = workflow_state_from_context(
        &format!(
            "update_result:{}",
            if report.duplicate_feedback_skipped {
                "duplicate_skipped"
            } else {
                "applied"
            }
        ),
        &report.promotion_decision,
        &report.rollback_recommendation,
    );
    report.recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: None,
        research_data: None,
        paired_data: None,
        update_outcome: Some(report.realized_outcome.clone()),
        update_entry_signal: Some(entry_signal.to_string()),
        update_feedback_file: feedback_file.map(str::to_string),
        user_data_selection_required: true,
    });
    concretize_action_plan_commands(&mut report.agent_action_plan, &report.recommended_commands);
    report.recommended_next_command =
        recommended_next_command(&report.agent_action_plan, &report.recommended_commands);
    report.agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &report.workflow_state,
        &format!(
            "update_result:{}",
            if report.duplicate_feedback_skipped {
                "duplicate_skipped"
            } else {
                "applied"
            }
        ),
        &report.recommended_next_command,
        &report.recommended_commands,
        &report.dataset_comparability,
        &report.factor_iteration_queue,
        &report.factor_family_outcomes,
        report.consumed_pre_bayes_evidence_filter.as_ref(),
        report.consumed_pre_bayes_entry_quality_bridge.as_ref(),
        None,
        Some(&report.artifact_decision_summary),
    );
    report.agent_context_bundle.multi_timeframe_summary =
        report.consumed_multi_timeframe_summary.clone();
    report.agent_context_bundle_minimal =
        build_agent_context_bundle_minimal(&report.agent_context_bundle);
    report.agent_prompts.prompts.push(promotion_gate_prompt(
        symbol,
        &report.factor_ranking,
        &report.factor_score_deltas,
        &report.decision_thresholds,
    ));
    report.agent_prompts.prompts.push(rollback_review_prompt(
        symbol,
        &report.factor_score_deltas,
        &report.trade_outcome_deltas,
        &report.decision_thresholds,
    ));
    append_update_run(
        state_dir,
        symbol,
        UpdateRunRecord {
            run_id: format!("{}", update_run_id),
            timestamp: Utc::now(),
            symbol: symbol.to_string(),
            ensemble_executor_scorecards: ensemble_executor_scorecards,
            provenance: report.provenance.clone(),
            decision_thresholds: report.decision_thresholds.clone(),
            dataset_comparability: report.dataset_comparability.clone(),
            promotion_decision: report.promotion_decision.clone(),
            rollback_recommendation: report.rollback_recommendation.clone(),
            family_history_window: family_history_window(),
            source_command: "update".to_string(),
            normalized_entry_quality: report.normalized_entry_quality.clone(),
            factor_alignment: report.factor_alignment.clone(),
            factor_uncertainty: report.factor_uncertainty.clone(),
            realized_outcome: report.realized_outcome.clone(),
            feedback_records_applied,
            duplicate_feedback_skipped: report.duplicate_feedback_skipped,
            consumed_pending_update_artifact_id: report.consumed_pending_update_artifact_id.clone(),
            consumed_execution_candidate_artifact_id: report
                .consumed_execution_candidate_artifact_id
                .clone(),
            consumed_artifact_path: report.consumed_artifact_path.clone(),
            consumed_analyze_run_id: report.consumed_analyze_run_id.clone(),
            consumed_pre_bayes_evidence_filter: report.consumed_pre_bayes_evidence_filter.clone(),
            consumed_pre_bayes_entry_quality_bridge: report
                .consumed_pre_bayes_entry_quality_bridge
                .clone(),
            consumed_multi_timeframe_summary: report.consumed_multi_timeframe_summary.clone(),
            trade_outcome_deltas,
            factor_score_deltas,
            factor_family_decisions: report.factor_family_decisions.clone(),
            factor_family_outcomes: report.factor_family_outcomes.clone(),
            factor_family_diffs: report.factor_family_diffs.clone(),
            factor_family_history: report.factor_family_history.clone(),
            decision_history_summary: report.decision_history_summary.clone(),
            workflow_state: report.workflow_state.clone(),
            agent_action_plan: report.agent_action_plan.clone(),
            recommended_commands: report.recommended_commands.clone(),
            recommended_next_command: report.recommended_next_command.clone(),
            agent_context_bundle: report.agent_context_bundle.clone(),
            agent_context_bundle_minimal: report.agent_context_bundle_minimal.clone(),
            feedback_history_summary: report.feedback_history_summary.clone(),
            artifact_action_summary: report.artifact_action_summary.clone(),
            artifact_decision_summary: report.artifact_decision_summary.clone(),
            artifact_decision_section: report.artifact_decision_section.clone(),
            agent_prompts: report.agent_prompts.clone(),
            prompt_workflow: report.agent_prompts.workflow.clone(),
        },
    )?;
    if let Some(artifact_id) = &report.consumed_pending_update_artifact_id {
        mark_artifact_consumed(
            state_dir,
            symbol,
            artifact_id,
            &update_run_id,
            &report.realized_outcome,
            consumed_feedback_pnl,
        )?;
    }
    if let Some(artifact_id) = &report.consumed_execution_candidate_artifact_id {
        mark_artifact_consumed(
            state_dir,
            symbol,
            artifact_id,
            &update_run_id,
            &report.realized_outcome,
            consumed_feedback_pnl,
        )?;
    }
    report.workflow_snapshot = refresh_workflow_snapshot(state_dir, symbol)?;
    report.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.workflow_snapshot,
        &report.artifact_action_summary,
    );
    report.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.workflow_snapshot);
    append_artifact_decision_prompt(
        &mut report.agent_prompts,
        symbol,
        &report.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );

    emit_update_output(&report, ensemble)
}

fn factor_research_command(
    symbol: &str,
    data: &str,
    objective: &str,
    data_1m: Option<&str>,
    data_5m: Option<&str>,
    data_15m: Option<&str>,
    data_1h: Option<&str>,
    data_4h: Option<&str>,
    data_1d: Option<&str>,
    paired_data: Option<&str>,
    mutation_spec_path: Option<&str>,
    emit_mutation_evaluation: bool,
    ensemble: bool,
    state_dir: &str,
) -> Result<()> {
    let _ = migrate_ensemble_executor_scorecards(state_dir, symbol)?;
    let objective = parse_research_objective(objective)?;
    let mutation_spec = mutation_spec_path
        .map(load_factor_mutation_spec)
        .transpose()?;
    let report = run_factor_research(
        symbol,
        data,
        objective,
        data_1m,
        data_5m,
        data_15m,
        data_1h,
        data_4h,
        data_1d,
        paired_data,
        mutation_spec.as_ref(),
        state_dir,
    )?;
    if emit_mutation_evaluation {
        let next_mutation_spec_template =
            report
                .factor_mutation_evaluation
                .as_ref()
                .map(|evaluation| {
                    let base_factor = mutation_spec
                        .as_ref()
                        .map(|spec| spec.base_factor.as_str())
                        .filter(|value| !value.is_empty())
                        .or_else(|| {
                            evaluation
                                .metrics_after
                                .top_factor_names
                                .first()
                                .map(String::as_str)
                        })
                        .unwrap_or("");
                    let (preferred_direction_hints, preferred_step_size_hints) =
                        factor_specific_hint_preferences(state_dir, symbol, base_factor);
                    next_mutation_spec_template_with_preferences(
                        mutation_spec.as_ref(),
                        evaluation,
                        mutation_spec
                            .as_ref()
                            .map(|spec| spec.evaluate_expansion_preview)
                            .unwrap_or(false),
                        Some(&preferred_direction_hints),
                        Some(&preferred_step_size_hints),
                    )
                });
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({
                "symbol": symbol,
                "mutation_spec": mutation_spec,
                "factor_mutation_evaluation": report.factor_mutation_evaluation,
                "next_mutation_spec_template": next_mutation_spec_template,
                "multi_timeframe_summary": report.multi_timeframe_summary,
                "recommended_next_command": report.recommended_next_command,
                "top_factor": report.best_factor,
                "artifact_gate_status": report.artifact_decision_summary.consumed_trend_status,
            }))?
        );
    } else {
        let reflection_bundle = build_research_reflection_bundle(symbol, &report);
        let lifecycle_view = build_factor_lifecycle_view(
            mutation_spec.as_ref(),
            report.factor_mutation_evaluation.as_ref(),
            &report.promotion_decision,
            &report.rollback_recommendation,
        );
        let ensemble_surface = if ensemble {
            report
                .workflow_snapshot
                .latest_ensemble_vote
                .as_ref()
                .map(|vote| {
                    let persisted_scorecards =
                        load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
                    let (scorecards, scorecard_source) =
                        resolved_vote_scorecards(&persisted_scorecards, vote);
                    serde_json::json!({
                        "ensemble_vote": vote,
                        "executor_scorecards": scorecards,
                        "executor_scorecard_source": scorecard_source,
                    })
                })
        } else {
            None
        };
        println!(
            "{}",
            serde_json::to_string_pretty(&serde_json::json!({
                "report": report,
                "reflection_bundle": reflection_bundle,
                "ensemble": ensemble_surface,
                "factor_lifecycle": lifecycle_view,
            }))?
        );
    }
    Ok(())
}

fn factor_mutation_status_command(
    symbol: &str,
    state_dir: &str,
    source_command: Option<&str>,
    latest_only: bool,
    accepted_only: bool,
    bucket_by_source: bool,
    limit: Option<usize>,
) -> Result<()> {
    let mut runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE)?;
    if let Some(source_command) = source_command {
        runs.retain(|run| run.source_command == source_command);
    }
    runs.sort_by_key(|run| run.timestamp);
    runs.reverse();
    if latest_only {
        runs.truncate(1);
    }
    if accepted_only {
        runs.retain(|run| run.evaluation.accepted);
    }
    if let Some(limit) = limit {
        runs.truncate(limit);
    }
    let all_runs: Vec<FactorMutationRunRecord> =
        load_state_or_default(state_dir, symbol, FACTOR_MUTATION_RUNS_FILE)?;
    let all_runs = all_runs
        .into_iter()
        .filter(|run| {
            source_command
                .map(|expected| run.source_command == expected)
                .unwrap_or(true)
        })
        .collect::<Vec<_>>();
    let mut failure_tag_counts = BTreeMap::<String, usize>::new();
    let mut regression_reason_counts = BTreeMap::<String, usize>::new();
    let mut regression_reason_markets = BTreeMap::<String, BTreeSet<String>>::new();
    let mut market_reason_counts = BTreeMap::<String, usize>::new();
    let mut market_reasons = BTreeMap::<String, BTreeSet<String>>::new();
    let mut direction_hint_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut direction_hint_accepts = BTreeMap::<String, usize>::new();
    let mut step_hint_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut step_hint_accepts = BTreeMap::<String, usize>::new();
    let mut per_factor_direction_hint_deltas =
        BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut per_factor_direction_hint_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    let mut per_factor_step_hint_deltas = BTreeMap::<String, BTreeMap<String, Vec<f64>>>::new();
    let mut per_factor_step_hint_accepts = BTreeMap::<String, BTreeMap<String, usize>>::new();
    let mut cluster_deltas = BTreeMap::<String, Vec<f64>>::new();
    let mut cluster_latest = BTreeMap::<String, String>::new();
    for run in &all_runs {
        for tag in &run.evaluation.failure_tags {
            *failure_tag_counts.entry(tag.clone()).or_default() += 1;
            cluster_deltas
                .entry(tag.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            cluster_latest.insert(tag.clone(), run.evaluation.mutation_id.clone());
        }
        for (market, reasons) in &run.evaluation.metrics_after.regression_reasons_by_market {
            *market_reason_counts.entry(market.clone()).or_default() += 1;
            for reason in reasons {
                *regression_reason_counts.entry(reason.clone()).or_default() += 1;
                regression_reason_markets
                    .entry(reason.clone())
                    .or_default()
                    .insert(market.clone());
                market_reasons
                    .entry(market.clone())
                    .or_default()
                    .insert(reason.clone());
            }
        }
        for (parameter, hint) in &run.mutation_spec.direction_hints {
            let label = format!("{}:{}", parameter, hint);
            direction_hint_deltas
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            per_factor_direction_hint_deltas
                .entry(run.mutation_spec.base_factor.clone())
                .or_default()
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *direction_hint_accepts.entry(label.clone()).or_default() += 1;
                *per_factor_direction_hint_accepts
                    .entry(run.mutation_spec.base_factor.clone())
                    .or_default()
                    .entry(label)
                    .or_default() += 1;
            }
        }
        for (parameter, step) in &run.mutation_spec.step_size_hints {
            let label = format!("{}:{:.4}", parameter, step);
            step_hint_deltas
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            per_factor_step_hint_deltas
                .entry(run.mutation_spec.base_factor.clone())
                .or_default()
                .entry(label.clone())
                .or_default()
                .push(run.evaluation.score_delta);
            if run.evaluation.accepted {
                *step_hint_accepts.entry(label.clone()).or_default() += 1;
                *per_factor_step_hint_accepts
                    .entry(run.mutation_spec.base_factor.clone())
                    .or_default()
                    .entry(label)
                    .or_default() += 1;
            }
        }
    }
    let mut failure_clusters = failure_tag_counts
        .iter()
        .map(|(tag, count)| FactorMutationFailureCluster {
            tag: tag.clone(),
            count: *count,
            latest_mutation_id: cluster_latest.get(tag).cloned(),
            average_score_delta: cluster_deltas
                .get(tag)
                .map(|values| values.iter().sum::<f64>() / values.len() as f64)
                .unwrap_or_default(),
        })
        .collect::<Vec<_>>();
    failure_clusters.sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.tag.cmp(&b.tag)));
    let mut runs_by_source = BTreeMap::<String, Vec<&FactorMutationRunRecord>>::new();
    for run in &all_runs {
        runs_by_source
            .entry(run.source_command.clone())
            .or_default()
            .push(run);
    }
    let mut source_summaries = runs_by_source
        .into_iter()
        .map(
            |(source_command, grouped_runs)| FactorMutationSourceSummary {
                source_command,
                total_runs: grouped_runs.len(),
                accepted_runs: grouped_runs
                    .iter()
                    .filter(|run| run.evaluation.accepted)
                    .count(),
                latest_mutation_id: grouped_runs
                    .iter()
                    .max_by_key(|run| run.timestamp)
                    .map(|run| run.evaluation.mutation_id.clone()),
                average_score_delta: if grouped_runs.is_empty() {
                    0.0
                } else {
                    grouped_runs
                        .iter()
                        .map(|run| run.evaluation.score_delta)
                        .sum::<f64>()
                        / grouped_runs.len() as f64
                },
            },
        )
        .collect::<Vec<_>>();
    source_summaries.sort_by(|a, b| {
        b.total_runs
            .cmp(&a.total_runs)
            .then_with(|| a.source_command.cmp(&b.source_command))
    });
    let mut regression_reason_summaries = regression_reason_counts
        .into_iter()
        .map(|(reason, count)| FactorMutationReasonSummary {
            markets: regression_reason_markets
                .remove(&reason)
                .map(|items| items.into_iter().collect::<Vec<_>>())
                .unwrap_or_default(),
            reason,
            count,
        })
        .collect::<Vec<_>>();
    regression_reason_summaries
        .sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.reason.cmp(&b.reason)));
    let mut market_regression_summaries = market_reason_counts
        .into_iter()
        .map(|(market, count)| FactorMutationMarketSummary {
            reasons: market_reasons
                .remove(&market)
                .map(|items| items.into_iter().collect::<Vec<_>>())
                .unwrap_or_default(),
            market,
            count,
        })
        .collect::<Vec<_>>();
    market_regression_summaries
        .sort_by(|a, b| b.count.cmp(&a.count).then_with(|| a.market.cmp(&b.market)));
    let mut direction_hint_effectiveness = direction_hint_deltas
        .into_iter()
        .map(|(hint, deltas)| {
            build_hint_effectiveness_summary(
                &hint,
                &deltas,
                direction_hint_accepts
                    .get(&hint)
                    .copied()
                    .unwrap_or_default(),
            )
        })
        .collect::<Vec<_>>();
    direction_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
    let mut step_size_hint_effectiveness = step_hint_deltas
        .into_iter()
        .map(|(hint, deltas)| {
            build_hint_effectiveness_summary(
                &hint,
                &deltas,
                step_hint_accepts.get(&hint).copied().unwrap_or_default(),
            )
        })
        .collect::<Vec<_>>();
    step_size_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
    let mut per_factor_hint_effectiveness = per_factor_direction_hint_deltas
        .into_iter()
        .map(|(base_factor, direction_entries)| {
            let mut direction_hint_effectiveness = direction_entries
                .into_iter()
                .map(|(hint, deltas)| {
                    let accepted_runs = per_factor_direction_hint_accepts
                        .get(&base_factor)
                        .and_then(|entries| entries.get(&hint))
                        .copied()
                        .unwrap_or_default();
                    build_hint_effectiveness_summary(&hint, &deltas, accepted_runs)
                })
                .collect::<Vec<_>>();
            direction_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
            let mut step_size_hint_effectiveness = per_factor_step_hint_deltas
                .get(&base_factor)
                .cloned()
                .unwrap_or_default()
                .into_iter()
                .map(|(hint, deltas)| {
                    let accepted_runs = per_factor_step_hint_accepts
                        .get(&base_factor)
                        .and_then(|entries| entries.get(&hint))
                        .copied()
                        .unwrap_or_default();
                    build_hint_effectiveness_summary(&hint, &deltas, accepted_runs)
                })
                .collect::<Vec<_>>();
            step_size_hint_effectiveness.sort_by(|a, b| compare_hint_effectiveness(b, a));
            FactorMutationPerFactorHintSummary {
                base_factor,
                direction_hint_effectiveness,
                step_size_hint_effectiveness,
            }
        })
        .collect::<Vec<_>>();
    per_factor_hint_effectiveness.sort_by(|a, b| a.base_factor.cmp(&b.base_factor));
    let priority_markets = market_regression_summaries
        .iter()
        .take(3)
        .map(|summary| summary.market.clone())
        .collect::<Vec<_>>();
    let priority_regression_reasons = regression_reason_summaries
        .iter()
        .take(3)
        .map(|summary| summary.reason.clone())
        .collect::<Vec<_>>();
    let recommended_next_mutation_focus =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_recommended_focus(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    let latest_direction_hints =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_direction_hint_summary(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    let latest_step_size_hints =
        if let Some(latest_run) = all_runs.iter().max_by_key(|run| run.timestamp) {
            factor_mutation_step_size_hint_summary(&latest_run.evaluation)
        } else {
            Vec::new()
        };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "symbol": symbol,
            "source_command_filter": source_command,
            "bucket_by_source": bucket_by_source,
            "total_runs": all_runs.len(),
            "accepted_runs": all_runs.iter().filter(|run| run.evaluation.accepted).count(),
            "latest_run": all_runs.iter().max_by_key(|run| run.timestamp).cloned(),
            "priority_markets": priority_markets,
            "priority_regression_reasons": priority_regression_reasons,
            "recommended_next_mutation_focus": recommended_next_mutation_focus,
            "latest_direction_hints": latest_direction_hints,
            "latest_step_size_hints": latest_step_size_hints,
            "direction_hint_effectiveness": direction_hint_effectiveness,
            "step_size_hint_effectiveness": step_size_hint_effectiveness,
            "per_factor_hint_effectiveness": per_factor_hint_effectiveness,
            "failure_tag_counts": failure_tag_counts,
            "failure_clusters": failure_clusters,
            "regression_reason_summaries": regression_reason_summaries,
            "market_regression_summaries": market_regression_summaries,
            "source_summaries": if bucket_by_source { source_summaries.clone() } else { Vec::<FactorMutationSourceSummary>::new() },
            "runs": runs,
            "recommended_commands": [
                format!(
                    "ict-engine factor-mutation-status --symbol {} --state-dir {} --limit 10{}{}",
                    shell_quote(symbol),
                    shell_quote(state_dir),
                    source_command.map(|value| format!(" --source-command {}", shell_quote(value))).unwrap_or_default(),
                    if bucket_by_source { " --bucket-by-source" } else { "" }
                ),
                format!(
                    "{} --mutation-spec <spec.json> --emit-mutation-evaluation",
                    factor_mutation_research_command(symbol, "<data.json>", state_dir)
                ),
                format!(
                    "ict-engine expansion-sop --root {} --output-dir <output> --interval 15m --lookback 20 --atr-multiplier 1.50 --mutation-spec <spec.json> --emit-mutation-evaluation",
                    shell_quote(&detected_tomac_root_or_placeholder())
                ),
            ]
        }))?
    );
    Ok(())
}

fn factor_mutation_research_command(symbol: &str, data: &str, state_dir: &str) -> String {
    format!(
        "ict-engine factor-research --symbol {} --data {} --state-dir {}",
        shell_quote(symbol),
        shell_quote(data),
        shell_quote(state_dir)
    )
}

fn default_tomac_root_candidates() -> Vec<String> {
    let mut candidates = Vec::new();
    if let Ok(root) = env::var("ICT_ENGINE_TOMAC_ROOT") {
        if !root.trim().is_empty() {
            candidates.push(root);
        }
    }
    if let Ok(home) = env::var("HOME") {
        for candidate in [
            format!("{home}/Downloads/Tomac"),
            format!("{home}/Downloads/tomac"),
            format!("{home}/Documents/Tomac"),
            format!("{home}/Documents/tomac"),
        ] {
            candidates.push(candidate);
        }
    }
    candidates
}

fn find_tomac_root_from_candidates(candidates: &[String]) -> Option<String> {
    candidates.iter().find_map(|candidate| {
        let path = std::path::Path::new(candidate);
        if !path.is_dir() {
            return None;
        }
        discover_tomac_futures_datasets(candidate)
            .ok()
            .filter(|datasets| !datasets.is_empty())
            .map(|_| candidate.clone())
    })
}

fn detected_tomac_root() -> Option<String> {
    find_tomac_root_from_candidates(&default_tomac_root_candidates())
}

fn resolve_tomac_root(root: Option<&str>) -> Result<String> {
    if let Some(root) = root {
        return Ok(root.to_string());
    }
    detected_tomac_root().ok_or_else(|| {
        anyhow!(
            "no TOMAC root provided and no default TOMAC history directory detected; set --root or ICT_ENGINE_TOMAC_ROOT"
        )
    })
}

fn detected_tomac_root_or_placeholder() -> String {
    detected_tomac_root().unwrap_or_else(|| "<root>".to_string())
}

fn candle_trend(candles: &[Candle]) -> Option<f64> {
    if candles.len() < 2 {
        return None;
    }
    let first = candles
        .first()
        .map(|candle| candle.close)
        .unwrap_or_default();
    let last = candles
        .last()
        .map(|candle| candle.close)
        .unwrap_or_default();
    if first.abs() <= f64::EPSILON {
        return None;
    }
    Some((last - first) / first)
}

fn multi_timeframe_signal_from_trends(
    long_term: &[f64],
    short_term: &[f64],
) -> MultiTimeframeResearchSignal {
    let long_avg = if long_term.is_empty() {
        0.0
    } else {
        long_term.iter().sum::<f64>() / long_term.len() as f64
    };
    let short_avg = if short_term.is_empty() {
        0.0
    } else {
        short_term.iter().sum::<f64>() / short_term.len() as f64
    };
    let alignment_score = 1.0 - (long_avg - short_avg).abs().min(1.0);
    let entry_alignment_score = 1.0 - short_avg.abs().min(1.0);
    let direction_bias = if long_avg > 0.001 {
        "bullish".to_string()
    } else if long_avg < -0.001 {
        "bearish".to_string()
    } else {
        "neutral".to_string()
    };
    MultiTimeframeResearchSignal {
        summary: vec![
            format!("higher_timeframe_direction_bias={}", direction_bias),
            format!("higher_timeframe_alignment_score={:.4}", alignment_score),
            format!(
                "lower_timeframe_entry_alignment_score={:.4}",
                entry_alignment_score
            ),
        ],
    }
}

fn build_live_multi_timeframe_summary(source: &str, frames: &[(&str, &[Candle])]) -> Vec<String> {
    let covered = frames
        .iter()
        .map(|(interval, _)| *interval)
        .collect::<Vec<_>>();
    let mut summary = vec![format!(
        "multi_timeframe_source={} covered_intervals={}",
        source,
        covered.join(",")
    )];
    for (interval, candles) in frames {
        summary.push(format!("{}:{} bars source=live", interval, candles.len()));
    }
    summary
}

fn build_live_multi_timeframe_signal(frames: &[(&str, &[Candle])]) -> MultiTimeframeResearchSignal {
    let frame_map = frames
        .iter()
        .map(|(interval, candles)| ((*interval).to_string(), *candles))
        .collect::<BTreeMap<_, _>>();
    let long_term = ["1d", "4h", "1h"]
        .into_iter()
        .filter_map(|interval| {
            frame_map
                .get(interval)
                .and_then(|candles| candle_trend(candles))
        })
        .collect::<Vec<_>>();
    let short_term = ["15m", "5m", "1m"]
        .into_iter()
        .filter_map(|interval| {
            frame_map
                .get(interval)
                .and_then(|candles| candle_trend(candles))
        })
        .collect::<Vec<_>>();
    multi_timeframe_signal_from_trends(&long_term, &short_term)
}

fn build_multi_timeframe_summary(
    primary_data: &str,
    resolved: &ResolvedMultiTimeframeInputs,
) -> Result<Vec<String>> {
    let mut summary = Vec::new();
    if !resolved.paths.is_empty() {
        let covered = MULTI_TIMEFRAME_INTERVALS
            .iter()
            .filter(|interval| resolved.get(interval).is_some())
            .copied()
            .collect::<Vec<_>>();
        let missing = MULTI_TIMEFRAME_INTERVALS
            .iter()
            .filter(|interval| resolved.get(interval).is_none())
            .copied()
            .collect::<Vec<_>>();
        summary.push(format!(
            "multi_timeframe_source={} covered_intervals={}",
            resolved.source,
            covered.join(",")
        ));
        if !missing.is_empty() {
            summary.push(format!("multi_timeframe_missing={}", missing.join(",")));
        }
    }
    for interval in MULTI_TIMEFRAME_INTERVALS {
        let Some(path) = resolved.get(interval) else {
            continue;
        };
        let candles = load_candles(path)?;
        summary.push(format!("{}:{} bars path={}", interval, candles.len(), path));
    }
    if summary.is_empty() {
        let primary = load_candles(primary_data)?;
        summary.push(format!(
            "primary:{} bars path={}",
            primary.len(),
            primary_data
        ));
    }
    Ok(summary)
}

fn build_multi_timeframe_research_signal(
    resolved: &ResolvedMultiTimeframeInputs,
) -> Result<MultiTimeframeResearchSignal> {
    let load_trend = |path: Option<&str>| -> Result<Option<f64>> {
        Ok(path
            .map(load_candles)
            .transpose()?
            .as_deref()
            .and_then(candle_trend))
    };
    let long_term = [
        load_trend(resolved.get("1d"))?,
        load_trend(resolved.get("4h"))?,
        load_trend(resolved.get("1h"))?,
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>();
    let short_term = [
        load_trend(resolved.get("15m"))?,
        load_trend(resolved.get("5m"))?,
        load_trend(resolved.get("1m"))?,
    ]
    .into_iter()
    .flatten()
    .collect::<Vec<_>>();
    Ok(multi_timeframe_signal_from_trends(&long_term, &short_term))
}

fn factor_backtest_command(
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    ensemble: bool,
    state_dir: &str,
) -> Result<()> {
    let report = run_factor_backtest(symbol, data, paired_data, state_dir)?;
    let credibility_summary = serde_json::json!({
        "conformal_coverage_1sigma": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.conformal_coverage_1sigma))
            .collect::<Vec<_>>(),
        "conformal_miscoverage_1sigma": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.conformal_miscoverage_1sigma))
            .collect::<Vec<_>>(),
        "regime_break_penalty": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.regime_break_penalty))
            .collect::<Vec<_>>(),
        "structural_break_score": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_score))
            .collect::<Vec<_>>(),
        "structural_break_detected": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_detected))
            .collect::<Vec<_>>(),
        "structural_break_index": report
            .factor_results
            .iter()
            .map(|result| (result.factor_name.clone(), result.metrics.structural_break_index))
            .collect::<Vec<_>>(),
    });
    let compact_report = build_backtest_result_artifact(
        format!("factor_backtest:{}", symbol),
        &report
            .scorecards
            .iter()
            .map(|item| format!("{}:{:.3}", item.factor_name, item.composite_score))
            .collect::<Vec<_>>(),
        &[
            format!("best_factor={:?}", report.best_factor),
            format!(
                "coverage_1sigma={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.conformal_coverage_1sigma)
                    .unwrap_or_default()
            ),
            format!(
                "regime_break_penalty={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.regime_break_penalty)
                    .unwrap_or_default()
            ),
            format!(
                "structural_break_detected={}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.structural_break_detected)
                    .unwrap_or(false)
            ),
            format!(
                "structural_break_score={:.3}",
                report
                    .factor_results
                    .first()
                    .map(|result| result.metrics.structural_break_score)
                    .unwrap_or_default()
            ),
        ],
        &[],
        &[],
        true,
        &[],
    );
    let ensemble_surface = if ensemble {
        report
            .workflow_snapshot
            .latest_ensemble_vote
            .as_ref()
            .map(|vote| {
                let persisted_scorecards =
                    load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
                let (scorecards, scorecard_source) =
                    resolved_vote_scorecards(&persisted_scorecards, vote);
                serde_json::json!({
                    "ensemble_vote": vote,
                    "executor_scorecards": scorecards,
                    "executor_scorecard_source": scorecard_source,
                })
            })
    } else {
        None
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&serde_json::json!({
            "report": report,
            "compact_backtest_report": compact_report,
            "credibility_summary": credibility_summary,
            "ensemble": ensemble_surface,
        }))?
    );
    Ok(())
}

fn run_factor_research(
    symbol: &str,
    data: &str,
    objective: ResearchObjectiveMode,
    data_1m: Option<&str>,
    data_5m: Option<&str>,
    data_15m: Option<&str>,
    data_1h: Option<&str>,
    data_4h: Option<&str>,
    data_1d: Option<&str>,
    paired_data: Option<&str>,
    mutation_spec: Option<&FactorMutationSpec>,
    state_dir: &str,
) -> Result<ict_engine::factor_lab::ResearchReport> {
    let candles = load_candles(data)?;
    let paired_candles = paired_data.map(load_candles).transpose()?;
    let resolved_multi_timeframe_inputs =
        resolve_multi_timeframe_inputs(data, data_1m, data_5m, data_15m, data_1h, data_4h, data_1d);
    let multi_timeframe_summary =
        build_multi_timeframe_summary(data, &resolved_multi_timeframe_inputs)?;
    let multi_timeframe_signal =
        build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?;
    let previous_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let mut learning_state = load_learning_state(state_dir, symbol)?;
    let baseline_learning_state = learning_state.clone();
    let previous_rankings = learning_state.factor_rankings.clone();
    let existing_feedback = learning_state
        .feedback_history
        .iter()
        .map(LearningState::feedback_key)
        .collect::<std::collections::BTreeSet<_>>();
    let mut registry = FactorRegistry::default();
    let baseline_multi_timeframe_summary = multi_timeframe_summary
        .iter()
        .cloned()
        .chain(multi_timeframe_signal.summary.iter().cloned())
        .collect::<Vec<_>>();
    let baseline_metrics = mutation_spec.map(|spec| {
        baseline_factor_mutation_metrics(
            &registry,
            symbol,
            objective,
            if spec.base_factor.is_empty() {
                None
            } else {
                Some(spec.base_factor.as_str())
            },
            &baseline_learning_state,
            &candles,
            paired_candles.as_deref(),
            &baseline_multi_timeframe_summary,
            spec.evaluate_expansion_preview,
        )
    });
    if let Some(spec) = mutation_spec {
        apply_factor_mutation_spec(&mut registry, spec)?;
    }
    let objective_registry = registry.clone();
    let lab = FactorLab::new(registry);
    let report = lab.run_research(
        symbol,
        &candles,
        &FactorContext {
            paired_candles: paired_candles.as_deref(),
            auxiliary: None,
            regime: None,
        },
        Some(&mut learning_state),
        &FactorBacktestConfig::default(),
        true,
    )?;
    let new_feedback = learning_state
        .feedback_history
        .iter()
        .filter(|record| !existing_feedback.contains(&LearningState::feedback_key(record)))
        .cloned()
        .collect::<Vec<_>>();
    let run_timestamp = Utc::now();
    let run_id = format!(
        "research:{}:{}",
        symbol,
        run_timestamp.format("%Y%m%dT%H%M%S%.3fZ")
    );
    let mut report = report;
    report.research_objective = research_objective_label(objective).to_string();
    if objective == ResearchObjectiveMode::ExpansionManipulation {
        apply_expansion_manipulation_objective(
            &mut report,
            &objective_registry,
            symbol,
            &candles,
            &multi_timeframe_summary
                .iter()
                .cloned()
                .chain(multi_timeframe_signal.summary.iter().cloned())
                .collect::<Vec<_>>(),
        )?;
        learning_state.factor_rankings = report.backtest.scorecards.clone();
    }
    let score_deltas = ranking_diffs(&previous_rankings, &learning_state.factor_rankings);
    let thresholds = decision_thresholds();
    let factor_family_decisions = learning_state.family_decisions();
    report.factor_score_deltas = score_deltas.clone();
    report.feedback_history_summary = learning_state.summary();
    report.factor_family_decisions = factor_family_decisions.clone();
    report.decision_thresholds = thresholds.clone();
    report.provenance = run_provenance(
        &learning_state,
        &[
            "factor-research",
            "FactorBacktestConfig::default",
            data,
            paired_data.unwrap_or(""),
        ],
        data_fingerprint(&candles, paired_candles.as_deref(), "analyze"),
    );
    report.dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &report.provenance,
    );
    let artifact_consumed_gate = artifact_consumed_decision_gate(
        &artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?,
    );
    let (_, artifact_family_trends) = artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    report.promotion_decision = derive_promotion_decision(
        &learning_state.factor_rankings,
        &score_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.factor_family_outcomes = derive_family_outcomes(
        &factor_family_decisions,
        &thresholds,
        &report.dataset_comparability,
        Some(&artifact_family_trends),
    );
    report.factor_family_diffs = family_diffs(
        previous_runs
            .last()
            .map(|run| run.factor_family_decisions.as_slice())
            .unwrap_or(&[]),
        &factor_family_decisions,
    );
    report.factor_family_history = family_history_from_runs(previous_runs.iter().map(|run| {
        (
            run.run_id.clone(),
            run.timestamp,
            run.factor_family_decisions.clone(),
        )
    }));
    report.decision_history_summary = decision_history_summary(previous_runs.iter().map(|run| {
        (
            run.promotion_decision.clone(),
            run.rollback_recommendation.clone(),
        )
    }));
    report.backtest.provenance = report.provenance.clone();
    report.backtest.feedback_records_generated = report.feedback_records_generated;
    report.backtest.feedback_records_applied = report.feedback_records_applied;
    report.backtest.feedback_history_summary = report.feedback_history_summary.clone();
    report.backtest.dataset_comparability = report.dataset_comparability.clone();
    report.backtest.promotion_decision = report.promotion_decision.clone();
    report.backtest.decision_thresholds = report.decision_thresholds.clone();
    report.backtest.factor_family_decisions = factor_family_decisions.clone();
    report.backtest.factor_family_outcomes = report.factor_family_outcomes.clone();
    report.backtest.factor_family_diffs = report.factor_family_diffs.clone();
    report.backtest.factor_family_history = report.factor_family_history.clone();
    report.backtest.decision_history_summary = report.decision_history_summary.clone();

    let enriched_feedback = new_feedback
        .into_iter()
        .enumerate()
        .map(|(index, feedback)| {
            enrich_feedback_record(
                feedback,
                &run_id,
                format!("factor-research:{}:{}", symbol, index),
                &learning_state,
                &report.provenance.data_fingerprint,
            )
        })
        .collect::<Vec<_>>();
    let mut network = load_or_init_trading_network(symbol, state_dir)?;
    let previous_trade_outcome_cpt = trade_outcome_cpt_snapshot(&network)?;
    if !enriched_feedback.is_empty() {
        learning_state.replace_feedback_records(&enriched_feedback);
        apply_feedback_to_trade_outcome_network(&mut network, &enriched_feedback)?;
    }
    let final_trade_outcome_cpt = trade_outcome_cpt_snapshot(&network)?;
    report.backtest.trade_outcome_deltas =
        cpt_probability_diffs(&previous_trade_outcome_cpt, &final_trade_outcome_cpt);
    report.backtest.final_trade_outcome_cpt = final_trade_outcome_cpt.clone();
    report.rollback_recommendation = derive_rollback_recommendation(
        &learning_state.factor_rankings,
        &score_deltas,
        &report.backtest.trade_outcome_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.backtest.rollback_recommendation = report.rollback_recommendation.clone();
    report.agent_prompts = factor_iteration_prompt_pack(
        symbol,
        &learning_state.factor_rankings,
        &report.backtest.iteration_queue,
        &report.feedback_history_summary,
    );
    report.agent_prompts.prompts.insert(
        0,
        dataset_audit_prompt(
            symbol,
            data,
            paired_data,
            candles.len(),
            paired_candles.as_ref().map(Vec::len),
            "factor-research",
        ),
    );
    if objective != ResearchObjectiveMode::Generic {
        report.agent_prompts.prompts.insert(
            1,
            AgentPrompt::new(
                "research_objective",
                "research",
                "high",
                "Score this run against the active research objective before trusting default aggregate-return rankings.",
                "Treat the active research objective as the primary iteration gate for this run. Do not let generic aggregate-return rankings override expansion/manipulation separation quality.",
                format!(
                    "research_objective={} best_factor={:?} factor_count={} iteration_queue_len={}",
                    report.research_objective,
                    report.best_factor,
                    report.factor_count,
                    report.backtest.iteration_queue.len()
                ),
                vec![
                    "Use objective-ranked scorecards for the next mutation cycle".to_string(),
                    "Preserve liquidity-sweep manipulation discrimination while improving PreBayes gate acceptance".to_string(),
                ],
                vec!["src/main.rs".to_string(), "src/factor_lab/factor_definition.rs".to_string()],
            ),
        );
    }
    report.multi_timeframe_summary = multi_timeframe_summary
        .iter()
        .cloned()
        .chain(multi_timeframe_signal.summary.iter().cloned())
        .collect();
    report.agent_prompts.prompts.push(research_diff_prompt(
        symbol,
        &score_deltas,
        report.feedback_records_generated,
        report.feedback_records_applied,
    ));
    report.agent_prompts.prompts.push(promotion_gate_prompt(
        symbol,
        &learning_state.factor_rankings,
        &score_deltas,
        &report.decision_thresholds,
    ));
    report.agent_prompts.prompts.push(rollback_review_prompt(
        symbol,
        &score_deltas,
        &report.backtest.trade_outcome_deltas,
        &report.decision_thresholds,
    ));
    report.workflow_state = workflow_state_from_context(
        "research_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
    );
    let coverage_caution = report
        .backtest
        .factor_results
        .iter()
        .filter(|result| result.metrics.conformal_coverage_1sigma < 0.55)
        .map(|result| {
            format!(
                "conformal_coverage_low:{}:{:.3}",
                result.factor_name, result.metrics.conformal_coverage_1sigma
            )
        })
        .collect::<Vec<_>>();
    let break_caution = report
        .backtest
        .factor_results
        .iter()
        .filter(|result| result.metrics.regime_break_penalty > 0.20)
        .map(|result| {
            format!(
                "regime_break_penalty_high:{}:{:.3}",
                result.factor_name, result.metrics.regime_break_penalty
            )
        })
        .collect::<Vec<_>>();
    let structural_break_caution = report
        .backtest
        .factor_results
        .iter()
        .filter(|result| result.metrics.structural_break_detected)
        .map(|result| {
            format!(
                "structural_break_detected:{}:score={:.3}:index={:?}",
                result.factor_name,
                result.metrics.structural_break_score,
                result.metrics.structural_break_index
            )
        })
        .collect::<Vec<_>>();
    report
        .artifact_action_summary
        .extend(coverage_caution.iter().cloned());
    report.artifact_action_summary.push(format!(
        "conformal_credibility:coverage_1sigma={:.3} miscoverage_1sigma={:.3} break_penalty={:.3}",
        report
            .backtest
            .factor_results
            .first()
            .map(|result| result.metrics.conformal_coverage_1sigma)
            .unwrap_or_default(),
        report
            .backtest
            .factor_results
            .first()
            .map(|result| result.metrics.conformal_miscoverage_1sigma)
            .unwrap_or_default(),
        report
            .backtest
            .factor_results
            .first()
            .map(|result| result.metrics.regime_break_penalty)
            .unwrap_or_default()
    ));
    report
        .artifact_action_summary
        .extend(break_caution.iter().cloned());
    report
        .artifact_action_summary
        .extend(structural_break_caution.iter().cloned());
    report.agent_action_plan = build_agent_action_plan(
        "research_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
        &report.backtest.iteration_queue,
        &report.factor_family_outcomes,
    );
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    augment_action_plan_with_artifact_trends(
        &mut report.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_decision_summary = artifact_decision_summary_for_symbol(state_dir, symbol)?;
    report.artifact_decision_section = artifact_decision_section_from_parts(
        &report.artifact_decision_summary,
        &report.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    append_artifact_decision_prompt(
        &mut report.agent_prompts,
        symbol,
        &report.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );
    report.recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: Some(AnalyzeCommandSource::Files {
            data_htf: data.to_string(),
            data_mtf: data.to_string(),
            data_ltf: data.to_string(),
        }),
        research_data: Some(data.to_string()),
        paired_data: paired_data.map(str::to_string),
        update_outcome: None,
        update_entry_signal: None,
        update_feedback_file: pending_update_artifact_path(state_dir, symbol),
        user_data_selection_required: true,
    });
    if objective != ResearchObjectiveMode::Generic && report.recommended_commands.research.ready {
        report.recommended_commands.research.command = format!(
            "{} --objective {}",
            report.recommended_commands.research.command,
            shell_quote(report.research_objective.as_str())
        );
    }
    concretize_action_plan_commands(&mut report.agent_action_plan, &report.recommended_commands);
    report.recommended_next_command =
        recommended_next_command(&report.agent_action_plan, &report.recommended_commands);
    let mutation_evaluation = mutation_spec.map(|spec| {
        evaluate_factor_mutation(
            spec,
            objective,
            baseline_metrics.as_ref(),
            &report,
            &candles,
            paired_candles.as_deref(),
        )
    });
    if let Some(evaluation) = &mutation_evaluation {
        augment_action_plan_with_factor_mutation_evaluation(
            &mut report.agent_action_plan,
            evaluation,
        );
        concretize_action_plan_commands(
            &mut report.agent_action_plan,
            &report.recommended_commands,
        );
        report.recommended_next_command =
            recommended_next_command(&report.agent_action_plan, &report.recommended_commands);
        report.agent_prompts.prompts.push(AgentPrompt::new(
            "factor-mutation-evaluation",
            "iteration",
            "high",
            "Review the latest factor mutation evaluation before accepting the next factor edit.",
            "Treat the mutation evaluation as a mechanical gate. Do not accept a mutation that regresses PreBayes quality or fails the score delta check.",
            format!(
                "mutation_id={} accepted={} score_before={:.4} score_after={:.4} delta={:.4} failure_tags={}",
                evaluation.mutation_id,
                evaluation.accepted,
                evaluation.score_before,
                evaluation.score_after,
                evaluation.score_delta,
                if evaluation.failure_tags.is_empty() {
                    "none".to_string()
                } else {
                    evaluation.failure_tags.join(",")
                }
            ),
            vec![
                "Only accept positive score deltas without new PreBayes failure tags".to_string(),
                "Reject mutations that increase soft evidence divergence or collapse bridge probability gap".to_string(),
            ],
            vec!["src/main.rs".to_string(), "src/factors/registry.rs".to_string()],
        ));
        report
            .agent_prompts
            .prompts
            .push(factor_mutation_focus_prompt(
                mutation_spec,
                evaluation,
                mutation_spec
                    .map(|spec| spec.evaluate_expansion_preview)
                    .unwrap_or(false),
            ));
    }
    report.agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &report.workflow_state,
        "research_review_ready",
        &report.recommended_next_command,
        &report.recommended_commands,
        &report.dataset_comparability,
        &report.backtest.iteration_queue,
        &report.factor_family_outcomes,
        None,
        None,
        mutation_evaluation.as_ref(),
        Some(&report.artifact_decision_summary),
    );
    report.agent_context_bundle.multi_timeframe_summary = report.multi_timeframe_summary.clone();
    report.agent_context_bundle_minimal =
        build_agent_context_bundle_minimal(&report.agent_context_bundle);
    report.backtest.agent_prompts = report.agent_prompts.clone();
    report.backtest.agent_action_plan = report.agent_action_plan.clone();
    report.backtest.workflow_state = report.workflow_state.clone();
    report.backtest.recommended_next_command = report.recommended_next_command.clone();
    report.backtest.recommended_commands = report.recommended_commands.clone();
    report.backtest.artifact_action_summary = report.artifact_action_summary.clone();
    report.backtest.agent_context_bundle = report.agent_context_bundle.clone();
    report.backtest.agent_context_bundle_minimal = report.agent_context_bundle_minimal.clone();
    if !enriched_feedback.is_empty() {
        save_state(state_dir, symbol, BBN_STATE_FILE, &network)?;
    }
    save_learning_state(state_dir, symbol, &learning_state)?;
    let research_run_record = ResearchRunRecord {
        run_id,
        timestamp: run_timestamp,
        symbol: symbol.to_string(),
        research_objective: report.research_objective.clone(),
        provenance: report.provenance.clone(),
        decision_thresholds: report.decision_thresholds.clone(),
        dataset_comparability: report.dataset_comparability.clone(),
        promotion_decision: report.promotion_decision.clone(),
        rollback_recommendation: report.rollback_recommendation.clone(),
        family_history_window: family_history_window(),
        data_path: data.to_string(),
        paired_data_path: paired_data.map(str::to_string),
        candles: candles.len(),
        paired_candles: paired_candles.as_ref().map(Vec::len),
        config_name: "FactorBacktestConfig::default".to_string(),
        source_command: "factor-research".to_string(),
        factor_count: report.factor_count,
        best_factor: report.best_factor.clone(),
        aggregate_return: report.aggregate_return,
        feedback_records_generated: report.feedback_records_generated,
        feedback_records_applied: report.feedback_records_applied,
        factor_score_deltas: score_deltas,
        factor_family_decisions,
        factor_family_outcomes: report.factor_family_outcomes.clone(),
        factor_family_diffs: report.factor_family_diffs.clone(),
        factor_family_history: report.factor_family_history.clone(),
        decision_history_summary: report.decision_history_summary.clone(),
        workflow_state: report.workflow_state.clone(),
        agent_action_plan: report.agent_action_plan.clone(),
        recommended_commands: report.recommended_commands.clone(),
        recommended_next_command: report.recommended_next_command.clone(),
        agent_context_bundle: report.agent_context_bundle.clone(),
        agent_context_bundle_minimal: report.agent_context_bundle_minimal.clone(),
        feedback_history_summary: report.feedback_history_summary.clone(),
        artifact_action_summary: report.artifact_action_summary.clone(),
        artifact_decision_summary: report.artifact_decision_summary.clone(),
        artifact_decision_section: report.artifact_decision_section.clone(),
        agent_prompts: report.agent_prompts.clone(),
        prompt_workflow: report.agent_prompts.workflow.clone(),
        factor_mutation_evaluation: mutation_evaluation.clone(),
        multi_timeframe_summary: report.multi_timeframe_summary.clone(),
    };
    append_research_run(state_dir, symbol, research_run_record.clone())?;
    let research_ensemble_vote = build_stub_ensemble_vote_from_research(&report);
    let canonical_scorecards =
        load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    let research_ensemble_record = build_ensemble_vote_record(
        symbol,
        "factor-research",
        Some(research_run_record.run_id.clone()),
        &report.provenance,
        &report.dataset_comparability,
        &research_ensemble_vote,
        &canonical_scorecards,
    );
    persist_ensemble_vote_record(state_dir, &research_ensemble_record, &canonical_scorecards)?;
    if let (Some(spec), Some(evaluation)) = (mutation_spec, mutation_evaluation.clone()) {
        let mutation_run_id = format!(
            "factor-mutation:{}:{}",
            symbol,
            run_timestamp.format("%Y%m%dT%H%M%S%.3fZ")
        );
        append_factor_mutation_run(
            state_dir,
            symbol,
            FactorMutationRunRecord {
                run_id: mutation_run_id,
                timestamp: run_timestamp,
                symbol: symbol.to_string(),
                source_command: "factor-research".to_string(),
                data_path: data.to_string(),
                paired_data_path: paired_data.map(str::to_string),
                mutation_spec: spec.clone(),
                evaluation,
            },
        )?;
    }
    report.workflow_snapshot = refresh_workflow_snapshot(state_dir, symbol)?;
    report.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.workflow_snapshot,
        &report.artifact_action_summary,
    );
    report.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.workflow_snapshot);
    append_artifact_decision_prompt(
        &mut report.agent_prompts,
        symbol,
        &report.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );
    report.backtest.workflow_snapshot = report.workflow_snapshot.clone();
    report.backtest.artifact_decision_summary = report.artifact_decision_summary.clone();
    report.backtest.artifact_decision_section = report.artifact_decision_section.clone();
    report.factor_mutation_evaluation = mutation_evaluation;
    Ok(report)
}

fn load_factor_mutation_spec(path: &str) -> Result<FactorMutationSpec> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read factor mutation spec '{}'", path))?;
    let mut spec: FactorMutationSpec = serde_json::from_str(&raw)
        .with_context(|| format!("failed to parse factor mutation spec '{}'", path))?;
    if spec.mutation_id.trim().is_empty() {
        spec.mutation_id = format!(
            "mutation:{}",
            std::path::Path::new(path)
                .file_stem()
                .and_then(|stem| stem.to_str())
                .unwrap_or("unnamed")
        );
    }
    Ok(spec)
}

fn apply_factor_mutation_spec(
    registry: &mut FactorRegistry,
    spec: &FactorMutationSpec,
) -> Result<()> {
    if !spec.base_factor.is_empty() && registry.get(&spec.base_factor).is_none() {
        bail!("unknown mutation base_factor '{}'", spec.base_factor);
    }
    for (factor, enabled) in &spec.enabled_overrides {
        if !registry.set_enabled(factor, *enabled) {
            bail!("unknown factor '{}' in enabled_overrides", factor);
        }
    }
    for (parameter, value) in &spec.parameter_overrides {
        if spec.base_factor.is_empty() {
            bail!("parameter_overrides require a base_factor");
        }
        if !registry.set_parameter(&spec.base_factor, parameter, *value) {
            bail!(
                "unknown factor '{}' for parameter override '{}'",
                spec.base_factor,
                parameter
            );
        }
    }
    Ok(())
}

fn baseline_factor_mutation_metrics(
    registry: &FactorRegistry,
    symbol: &str,
    objective: ResearchObjectiveMode,
    target_factor: Option<&str>,
    baseline_learning_state: &LearningState,
    candles: &[Candle],
    paired_candles: Option<&[Candle]>,
    multi_timeframe_summary: &[String],
    evaluate_expansion_preview: bool,
) -> Result<FactorMutationMetricSet> {
    let mut learning_state = baseline_learning_state.clone();
    let lab = FactorLab::new(registry.clone());
    let mut report = lab.run_research(
        symbol,
        candles,
        &FactorContext {
            paired_candles,
            auxiliary: None,
            regime: None,
        },
        Some(&mut learning_state),
        &FactorBacktestConfig::default(),
        true,
    )?;
    report.research_objective = research_objective_label(objective).to_string();
    report.multi_timeframe_summary = multi_timeframe_summary.to_vec();
    if objective == ResearchObjectiveMode::ExpansionManipulation {
        apply_expansion_manipulation_objective(
            &mut report,
            registry,
            symbol,
            candles,
            multi_timeframe_summary,
        )?;
    }
    build_factor_mutation_metric_set(
        &report,
        symbol,
        candles,
        registry,
        target_factor,
        evaluate_expansion_preview,
    )
}

fn build_factor_mutation_metric_set(
    report: &ict_engine::factor_lab::ResearchReport,
    symbol: &str,
    candles: &[Candle],
    registry: &FactorRegistry,
    target_factor: Option<&str>,
    evaluate_expansion_preview: bool,
) -> Result<FactorMutationMetricSet> {
    let evaluated_factor = target_factor
        .filter(|value| !value.trim().is_empty())
        .or(report.best_factor.as_deref());
    let best_factor_composite_score = evaluated_factor
        .and_then(|factor_name| {
            report
                .backtest
                .scorecards
                .iter()
                .find(|score| score.factor_name == factor_name)
                .map(|score| score.composite_score)
        })
        .or_else(|| {
            report
                .backtest
                .scorecards
                .first()
                .map(|score| score.composite_score)
        })
        .unwrap_or_default();
    let mut metrics = FactorMutationMetricSet {
        best_factor_composite_score,
        aggregate_return: report.aggregate_return,
        feedback_records_generated: report.feedback_records_generated,
        feedback_records_applied: report.feedback_records_applied,
        top_factor_names: report
            .backtest
            .scorecards
            .iter()
            .take(3)
            .map(|score| score.factor_name.clone())
            .collect(),
        ..FactorMutationMetricSet::default()
    };
    for item in &report.multi_timeframe_summary {
        if let Some(value) = item.strip_prefix("higher_timeframe_direction_bias=") {
            metrics.multi_timeframe_direction_bias = Some(value.to_string());
        } else if let Some(value) = item.strip_prefix("higher_timeframe_alignment_score=") {
            metrics.multi_timeframe_alignment_score = value.parse::<f64>().ok();
        } else if let Some(value) = item.strip_prefix("lower_timeframe_entry_alignment_score=") {
            metrics.multi_timeframe_entry_alignment_score = value.parse::<f64>().ok();
        }
    }
    if evaluate_expansion_preview {
        if let Some(best_factor) = evaluated_factor {
            let pipeline = build_expansion_factor_pipeline_report_with_registry_v2(
                symbol,
                best_factor,
                candles,
                &report.multi_timeframe_summary,
                registry,
            )?;
            let bridge_diff = pre_bayes_entry_quality_bridge_diff(&pipeline.entry_quality_bridge);
            let soft_diff = pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter);
            let score = expansion_factor_scores_for_market(registry, candles, 20, 1.5)?
                .into_iter()
                .find(|item| item.factor_name == best_factor);
            metrics.expansion_selected_direction =
                Some(pipeline.bbn_support.selected_direction.clone());
            metrics.expansion_selected_win_probability =
                Some(pipeline.bbn_support.selected_win_probability);
            metrics.expansion_balanced_accuracy = score.as_ref().map(|item| item.balanced_accuracy);
            metrics.expansion_directional_accuracy =
                score.as_ref().map(|item| item.directional_accuracy);
            metrics.pre_bayes_gate_status =
                Some(pipeline.bbn_support.pre_bayes_filter.gating_status.clone());
            metrics.pre_bayes_bridge_selected_entry_quality = bridge_diff.selected_entry_quality;
            metrics.pre_bayes_bridge_probability_gap =
                Some(bridge_diff.long_short_signal_probability_gap);
            metrics.pre_bayes_soft_evidence_divergence_count = soft_diff
                .iter()
                .filter(|item| item.diverges_from_filtered_state)
                .count();
        }
    }
    Ok(metrics)
}

fn evaluate_factor_mutation(
    spec: &FactorMutationSpec,
    objective: ResearchObjectiveMode,
    baseline_metrics: Option<&Result<FactorMutationMetricSet>>,
    report: &ict_engine::factor_lab::ResearchReport,
    candles: &[Candle],
    _paired_candles: Option<&[Candle]>,
) -> FactorMutationEvaluation {
    let mut registry = FactorRegistry::default();
    let _ = apply_factor_mutation_spec(&mut registry, spec);
    let metrics_after = build_factor_mutation_metric_set(
        report,
        &report.workflow_snapshot.symbol,
        candles,
        &registry,
        if spec.base_factor.is_empty() {
            None
        } else {
            Some(spec.base_factor.as_str())
        },
        spec.evaluate_expansion_preview,
    )
    .unwrap_or_default();
    let metrics_before = baseline_metrics.and_then(|result| result.as_ref().ok().cloned());
    let score_before = metrics_before
        .as_ref()
        .map(|metrics| mechanical_mutation_score(metrics, objective))
        .unwrap_or_default();
    let score_after = mechanical_mutation_score(&metrics_after, objective);
    let score_delta = score_after - score_before;
    let mut failure_tags = Vec::new();
    if metrics_before
        .as_ref()
        .map(|before| {
            metrics_after.best_factor_composite_score + 1e-9 < before.best_factor_composite_score
        })
        .unwrap_or(false)
    {
        failure_tags.push("best_factor_composite_regressed".to_string());
    }
    if metrics_after.pre_bayes_soft_evidence_divergence_count > 0 {
        failure_tags.push("soft_evidence_conflicts_with_filtered_label".to_string());
    }
    if metrics_after
        .pre_bayes_bridge_probability_gap
        .map(|gap| gap < 0.05)
        .unwrap_or(false)
    {
        failure_tags.push("bridge_gap_too_small".to_string());
    }
    let gate_before = metrics_before
        .as_ref()
        .and_then(|metrics| metrics.pre_bayes_gate_status.as_deref())
        .unwrap_or("observe_only");
    let gate_after = metrics_after
        .pre_bayes_gate_status
        .as_deref()
        .unwrap_or("observe_only");
    if objective == ResearchObjectiveMode::ExpansionManipulation {
        if pre_bayes_gate_regressed(gate_before, gate_after) {
            failure_tags.push("pre_bayes_gate_regressed".to_string());
        }
    } else if gate_after == "observe_only" {
        failure_tags.push("pre_bayes_gate_observe_only".to_string());
    }
    if no_superior_mutation_found(score_delta, &failure_tags, objective) {
        failure_tags.push("no_superior_mutation_found".to_string());
    }
    let recommended_mutation_directions = if failure_tags.is_empty() {
        vec![
            "Keep the mutation atomic and continue searching for incremental PreBayes/bridge improvements"
                .to_string(),
        ]
    } else {
        recommended_mutation_directions_from_failure_tags(&failure_tags, &[], &BTreeMap::new())
    };
    FactorMutationEvaluation {
        mutation_id: spec.mutation_id.clone(),
        accepted: score_delta > 0.0 && failure_tags.is_empty(),
        score_before,
        score_after,
        score_delta,
        baseline_available: metrics_before.is_some(),
        reason: if score_delta > 0.0 && failure_tags.is_empty() {
            "mechanical_score_improved_without_pre_bayes_regression".to_string()
        } else if failure_tags.is_empty() {
            "mechanical_score_not_improved".to_string()
        } else {
            format!("mutation_flagged:{}", failure_tags.join(","))
        },
        failure_tags,
        recommended_mutation_directions,
        metrics_before,
        metrics_after,
    }
}

fn augment_action_plan_with_factor_mutation_evaluation(
    action_plan: &mut AgentActionPlan,
    evaluation: &FactorMutationEvaluation,
) {
    let priority_markets = factor_mutation_priority_markets(evaluation);
    let priority_reasons = factor_mutation_priority_reasons(evaluation);
    let recommended_focus = factor_mutation_recommended_focus(evaluation);
    action_plan.items.insert(
        0,
        AgentActionItem {
            stage: "iteration".to_string(),
            blocking: !evaluation.accepted,
            priority: "high".to_string(),
            title: if evaluation.accepted {
                "Promote Factor Mutation Candidate".to_string()
            } else {
                "Reject Factor Mutation Candidate".to_string()
            },
            rationale: format!(
                "mutation_id={} reason={} score_delta={:.4} priority_markets={} priority_reasons={}",
                evaluation.mutation_id,
                evaluation.reason,
                evaluation.score_delta,
                if priority_markets.is_empty() {
                    "none".to_string()
                } else {
                    priority_markets.join("|")
                },
                if priority_reasons.is_empty() {
                    "none".to_string()
                } else {
                    priority_reasons.join("|")
                }
            ),
            expected_output: "A mechanical mutation decision with explicit accept/reject status and failure tags".to_string(),
            expected_state_changes: vec![
                ExpectedStateChange {
                    target: "factor_mutation_evaluation".to_string(),
                    direction: if evaluation.accepted {
                        "accepted".to_string()
                    } else if evaluation
                        .failure_tags
                        .iter()
                        .any(|tag| tag == "no_superior_mutation_found")
                    {
                        "near_local_optimum".to_string()
                    } else {
                        "rejected".to_string()
                    },
                    rationale: if evaluation.failure_tags.is_empty() {
                        evaluation.reason.clone()
                    } else {
                        evaluation.failure_tags.join(",")
                    },
                },
                ExpectedStateChange {
                    target: "factor_mutation_focus".to_string(),
                    direction: if recommended_focus.is_empty() {
                        "review_required".to_string()
                    } else if evaluation
                        .failure_tags
                        .iter()
                        .any(|tag| tag == "no_superior_mutation_found")
                    {
                        "pivot_to_label_refinement_or_market_specific_fork".to_string()
                    } else {
                        "prioritized".to_string()
                    },
                    rationale: if recommended_focus.is_empty() {
                        "no explicit mutation focus available".to_string()
                    } else {
                        recommended_focus.join(" | ")
                    },
                },
            ],
            suggested_files: vec!["src/main.rs".to_string(), "src/factors/registry.rs".to_string()],
            suggested_commands: vec![
                "ict-engine factor-research --symbol <symbol> --data <file> --mutation-spec <spec.json> --emit-mutation-evaluation"
                    .to_string(),
            ],
        },
    );
}

fn mechanical_mutation_score(
    metrics: &FactorMutationMetricSet,
    objective: ResearchObjectiveMode,
) -> f64 {
    match objective {
        ResearchObjectiveMode::Generic => {
            metrics.best_factor_composite_score * 0.55
                + metrics.aggregate_return * 0.20
                + metrics.expansion_balanced_accuracy.unwrap_or(0.0) * 0.15
                + metrics.expansion_selected_win_probability.unwrap_or(0.0) * 0.10
                + metrics.multi_timeframe_alignment_score.unwrap_or(0.0) * 0.08
                + metrics.multi_timeframe_entry_alignment_score.unwrap_or(0.0) * 0.04
                - metrics.pre_bayes_soft_evidence_divergence_count as f64 * 0.05
                + if metrics.multi_timeframe_direction_bias.as_deref() == Some("neutral") {
                    0.0
                } else {
                    0.03
                }
        }
        ResearchObjectiveMode::ExpansionManipulation => {
            let bridge_gap_score = metrics
                .pre_bayes_bridge_probability_gap
                .map(|gap| (gap / 0.25).clamp(0.0, 1.0))
                .unwrap_or_default();
            metrics.best_factor_composite_score * 0.60
                + metrics.expansion_balanced_accuracy.unwrap_or(0.0) * 0.20
                + metrics.expansion_directional_accuracy.unwrap_or(0.0) * 0.10
                + metrics.expansion_selected_win_probability.unwrap_or(0.0) * 0.05
                + bridge_gap_score * 0.03
                + metrics.multi_timeframe_alignment_score.unwrap_or(0.0) * 0.04
                + metrics.multi_timeframe_entry_alignment_score.unwrap_or(0.0) * 0.03
                - metrics.pre_bayes_soft_evidence_divergence_count as f64 * 0.05
                + if metrics.multi_timeframe_direction_bias.as_deref() == Some("neutral") {
                    0.0
                } else {
                    0.02
                }
        }
    }
}

fn run_factor_backtest(
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    state_dir: &str,
) -> Result<ict_engine::factor_lab::BacktestResult> {
    let candles = load_candles(data)?;
    let paired_candles = paired_data.map(load_candles).transpose()?;
    let resolved_multi_timeframe_inputs =
        resolve_multi_timeframe_inputs(data, None, None, None, None, None, None);
    let multi_timeframe_summary =
        build_multi_timeframe_summary(data, &resolved_multi_timeframe_inputs)?;
    let multi_timeframe_signal =
        build_multi_timeframe_research_signal(&resolved_multi_timeframe_inputs)?;
    let previous_runs: Vec<BacktestRunRecord> =
        load_state_or_default(state_dir, symbol, BACKTEST_RUNS_FILE)?;
    let mut learning_state = load_learning_state(state_dir, symbol)?;
    let previous_rankings = learning_state.factor_rankings.clone();
    let existing_feedback = learning_state
        .feedback_history
        .iter()
        .map(LearningState::feedback_key)
        .collect::<std::collections::BTreeSet<_>>();
    let lab = FactorLab::new(FactorRegistry::default());
    let research = lab.run_research(
        symbol,
        &candles,
        &FactorContext {
            paired_candles: paired_candles.as_deref(),
            auxiliary: None,
            regime: None,
        },
        Some(&mut learning_state),
        &FactorBacktestConfig::default(),
        true,
    )?;
    let feedback_records_generated = research.feedback_records_generated;
    let feedback_records_applied = research.feedback_records_applied;
    let run_timestamp = Utc::now();
    let run_id = format!(
        "factor-backtest:{}:{}",
        symbol,
        run_timestamp.format("%Y%m%dT%H%M%S%.3fZ")
    );
    let new_feedback = learning_state
        .feedback_history
        .iter()
        .filter(|record| !existing_feedback.contains(&LearningState::feedback_key(record)))
        .cloned()
        .collect::<Vec<_>>();
    let mut report = research.backtest;
    let thresholds = decision_thresholds();
    let score_deltas = ranking_diffs(&previous_rankings, &learning_state.factor_rankings);
    let factor_family_decisions = learning_state.family_decisions();

    report.feedback_records_generated = feedback_records_generated;
    report.feedback_records_applied = feedback_records_applied;
    report.feedback_history_summary = learning_state.summary();
    report.factor_family_decisions = factor_family_decisions.clone();
    report.provenance = run_provenance(
        &learning_state,
        &[
            "factor-backtest",
            "FactorBacktestConfig::default",
            data,
            paired_data.unwrap_or(""),
        ],
        data_fingerprint(&candles, paired_candles.as_deref(), "factor-backtest"),
    );
    report.decision_thresholds = thresholds.clone();
    report.dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &report.provenance,
    );
    let artifact_consumed_gate = artifact_consumed_decision_gate(
        &artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?,
    );
    let (_, artifact_family_trends) = artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    report.promotion_decision = derive_promotion_decision(
        &learning_state.factor_rankings,
        &score_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.factor_family_outcomes = derive_family_outcomes(
        &factor_family_decisions,
        &thresholds,
        &report.dataset_comparability,
        Some(&artifact_family_trends),
    );
    report.factor_family_diffs = family_diffs(
        previous_runs
            .last()
            .map(|run| run.factor_family_decisions.as_slice())
            .unwrap_or(&[]),
        &factor_family_decisions,
    );
    report.factor_family_history = family_history_from_runs(previous_runs.iter().map(|run| {
        (
            run.run_id.clone(),
            run.timestamp,
            run.factor_family_decisions.clone(),
        )
    }));
    report.decision_history_summary = decision_history_summary(previous_runs.iter().map(|run| {
        (
            run.promotion_decision.clone(),
            run.rollback_recommendation.clone(),
        )
    }));

    let enriched_feedback = new_feedback
        .into_iter()
        .enumerate()
        .map(|(index, feedback)| {
            enrich_feedback_record(
                feedback,
                &run_id,
                format!("factor-backtest:{}:{}", symbol, index),
                &learning_state,
                &report.provenance.data_fingerprint,
            )
        })
        .collect::<Vec<_>>();
    let mut network = load_or_init_trading_network(symbol, state_dir)?;
    let previous_trade_outcome_cpt = trade_outcome_cpt_snapshot(&network)?;
    if !enriched_feedback.is_empty() {
        learning_state.replace_feedback_records(&enriched_feedback);
        apply_feedback_to_trade_outcome_network(&mut network, &enriched_feedback)?;
    }
    let final_trade_outcome_cpt = trade_outcome_cpt_snapshot(&network)?;
    report.trade_outcome_deltas =
        cpt_probability_diffs(&previous_trade_outcome_cpt, &final_trade_outcome_cpt);
    report.final_trade_outcome_cpt = final_trade_outcome_cpt.clone();
    report.rollback_recommendation = derive_rollback_recommendation(
        &learning_state.factor_rankings,
        &score_deltas,
        &report.trade_outcome_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.workflow_state = workflow_state_from_context(
        "factor_backtest_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
    );
    report.agent_action_plan = build_agent_action_plan(
        "factor_backtest_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
        &report.iteration_queue,
        &report.factor_family_outcomes,
    );
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    augment_action_plan_with_artifact_trends(
        &mut report.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_decision_summary = artifact_decision_summary_for_symbol(state_dir, symbol)?;
    report.artifact_decision_section = artifact_decision_section_from_parts(
        &report.artifact_decision_summary,
        &report.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    append_artifact_decision_prompt(
        &mut report.agent_prompts,
        symbol,
        &report.artifact_decision_section,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );
    report.recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: Some(AnalyzeCommandSource::Files {
            data_htf: data.to_string(),
            data_mtf: data.to_string(),
            data_ltf: data.to_string(),
        }),
        research_data: Some(data.to_string()),
        paired_data: paired_data.map(str::to_string),
        update_outcome: None,
        update_entry_signal: None,
        update_feedback_file: pending_update_artifact_path(state_dir, symbol),
        user_data_selection_required: true,
    });
    concretize_action_plan_commands(&mut report.agent_action_plan, &report.recommended_commands);
    report.recommended_next_command =
        recommended_next_command(&report.agent_action_plan, &report.recommended_commands);
    report.agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &report.workflow_state,
        "factor_backtest_review_ready",
        &report.recommended_next_command,
        &report.recommended_commands,
        &report.dataset_comparability,
        &report.iteration_queue,
        &report.factor_family_outcomes,
        None,
        None,
        None,
        Some(&report.artifact_decision_summary),
    );
    report.multi_timeframe_summary = multi_timeframe_summary
        .iter()
        .cloned()
        .chain(multi_timeframe_signal.summary.iter().cloned())
        .collect();
    report.agent_context_bundle.multi_timeframe_summary = report.multi_timeframe_summary.clone();
    report.agent_context_bundle_minimal =
        build_agent_context_bundle_minimal(&report.agent_context_bundle);
    report.agent_prompts = build_backtest_agent_prompts(
        symbol,
        &learning_state.factor_rankings,
        &report.iteration_queue,
        &report.feedback_history_summary,
        report.aggregate_return,
        report
            .factor_results
            .iter()
            .map(|result| result.trades.len())
            .sum(),
        &report.final_trade_outcome_cpt,
    );
    report.agent_prompts.prompts.insert(
        0,
        dataset_audit_prompt(
            symbol,
            data,
            paired_data,
            candles.len(),
            paired_candles.as_ref().map(Vec::len),
            "factor-backtest",
        ),
    );
    report.agent_prompts.prompts.push(promotion_gate_prompt(
        symbol,
        &learning_state.factor_rankings,
        &score_deltas,
        &report.decision_thresholds,
    ));
    report.agent_prompts.prompts.push(rollback_review_prompt(
        symbol,
        &score_deltas,
        &report.trade_outcome_deltas,
        &report.decision_thresholds,
    ));

    if !enriched_feedback.is_empty() {
        save_state(state_dir, symbol, BBN_STATE_FILE, &network)?;
    }
    save_learning_state(state_dir, symbol, &learning_state)?;
    append_backtest_run(
        state_dir,
        symbol,
        BacktestRunRecord {
            run_id,
            timestamp: run_timestamp,
            symbol: symbol.to_string(),
            provenance: report.provenance.clone(),
            decision_thresholds: report.decision_thresholds.clone(),
            dataset_comparability: report.dataset_comparability.clone(),
            promotion_decision: report.promotion_decision.clone(),
            rollback_recommendation: report.rollback_recommendation.clone(),
            family_history_window: family_history_window(),
            data_path: data.to_string(),
            paired_data_path: paired_data.map(str::to_string),
            candles: candles.len(),
            paired_candles: paired_candles.as_ref().map(Vec::len),
            warmup_bars: FactorBacktestConfig::default().train_bars,
            hold_bars: FactorBacktestConfig::default().max_hold_bars,
            online_learning: true,
            source_command: "factor-backtest".to_string(),
            total_return: report.aggregate_return,
            trade_count: report
                .factor_results
                .iter()
                .map(|result| result.trades.len())
                .sum(),
            conformal_coverage_1sigma: report
                .factor_results
                .first()
                .map(|result| result.metrics.conformal_coverage_1sigma)
                .unwrap_or_default(),
            conformal_miscoverage_1sigma: report
                .factor_results
                .first()
                .map(|result| result.metrics.conformal_miscoverage_1sigma)
                .unwrap_or_default(),
            mean_prediction_interval_half_width: report
                .factor_results
                .first()
                .map(|result| result.metrics.mean_prediction_interval_half_width)
                .unwrap_or_default(),
            worst_window_miscoverage: report
                .factor_results
                .first()
                .map(|result| result.metrics.worst_window_miscoverage)
                .unwrap_or_default(),
            regime_break_penalty: report
                .factor_results
                .first()
                .map(|result| result.metrics.regime_break_penalty)
                .unwrap_or_default(),
            structural_break_score: report
                .factor_results
                .first()
                .map(|result| result.metrics.structural_break_score)
                .unwrap_or_default(),
            structural_break_index: report
                .factor_results
                .first()
                .and_then(|result| result.metrics.structural_break_index),
            structural_break_detected: report
                .factor_results
                .first()
                .map(|result| result.metrics.structural_break_detected)
                .unwrap_or(false),
            signal_structural_break_score: report
                .factor_results
                .first()
                .map(|result| result.metrics.signal_structural_break_score)
                .unwrap_or_default(),
            signal_structural_break_index: report
                .factor_results
                .first()
                .and_then(|result| result.metrics.signal_structural_break_index),
            signal_structural_break_detected: report
                .factor_results
                .first()
                .map(|result| result.metrics.signal_structural_break_detected)
                .unwrap_or(false),
            residual_structural_break_score: report
                .factor_results
                .first()
                .map(|result| result.metrics.residual_structural_break_score)
                .unwrap_or_default(),
            residual_structural_break_index: report
                .factor_results
                .first()
                .and_then(|result| result.metrics.residual_structural_break_index),
            residual_structural_break_detected: report
                .factor_results
                .first()
                .map(|result| result.metrics.residual_structural_break_detected)
                .unwrap_or(false),
            rolling_ic_structural_break_score: report
                .factor_results
                .first()
                .map(|result| result.metrics.rolling_ic_structural_break_score)
                .unwrap_or_default(),
            rolling_ic_structural_break_index: report
                .factor_results
                .first()
                .and_then(|result| result.metrics.rolling_ic_structural_break_index),
            rolling_ic_structural_break_detected: report
                .factor_results
                .first()
                .map(|result| result.metrics.rolling_ic_structural_break_detected)
                .unwrap_or(false),
            factor_score_deltas: score_deltas,
            trade_outcome_deltas: report.trade_outcome_deltas.clone(),
            factor_family_decisions,
            factor_family_outcomes: report.factor_family_outcomes.clone(),
            factor_family_diffs: report.factor_family_diffs.clone(),
            factor_family_history: report.factor_family_history.clone(),
            decision_history_summary: report.decision_history_summary.clone(),
            workflow_state: report.workflow_state.clone(),
            agent_action_plan: report.agent_action_plan.clone(),
            recommended_commands: report.recommended_commands.clone(),
            recommended_next_command: report.recommended_next_command.clone(),
            agent_context_bundle: report.agent_context_bundle.clone(),
            agent_context_bundle_minimal: report.agent_context_bundle_minimal.clone(),
            feedback_history_summary: report.feedback_history_summary.clone(),
            artifact_action_summary: report.artifact_action_summary.clone(),
            artifact_decision_summary: report.artifact_decision_summary.clone(),
            artifact_decision_section: report.artifact_decision_section.clone(),
            agent_prompts: report.agent_prompts.clone(),
            prompt_workflow: report.agent_prompts.workflow.clone(),
            multi_timeframe_summary: report.multi_timeframe_summary.clone(),
        },
    )?;
    report.workflow_snapshot = refresh_workflow_snapshot(state_dir, symbol)?;
    report.artifact_decision_summary = artifact_decision_summary_from_snapshot(
        &report.workflow_snapshot,
        &report.artifact_action_summary,
    );
    report.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.workflow_snapshot);
    report.artifact_decision_section =
        artifact_decision_section_from_snapshot(&report.workflow_snapshot);
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );

    Ok(report)
}

fn build_analyze_report(
    symbol: &str,
    state_dir: &str,
    htf: &[Candle],
    mtf: &[Candle],
    ltf: &[Candle],
    params: &HMMParams,
    network: &ict_engine::bbn::BayesianNetwork,
    build_context: AnalyzeBuildContext<'_>,
) -> Result<AnalyzeReport> {
    let htf_features = build_frame_features(htf)?;
    let mtf_features = build_frame_features(mtf)?;
    let ltf_features = build_frame_features(ltf)?;
    let native_signals = native_frame_computations(params, build_context.native_frames)?;

    let regime_label = if native_signals.is_empty() {
        combine_regime_labels(&[
            htf_features.regime_label.as_str(),
            mtf_features.regime_label.as_str(),
            ltf_features.regime_label.as_str(),
        ])
    } else {
        weighted_majority_label(
            native_signals
                .iter()
                .map(|signal| (signal.features.regime_label.as_str(), signal.weight)),
            "bull",
            "bear",
            "range",
        )
    };
    let liquidity_label = if native_signals.is_empty() {
        combine_liquidity_labels(&[
            htf_features.liquidity_label.as_str(),
            mtf_features.liquidity_label.as_str(),
            ltf_features.liquidity_label.as_str(),
        ])
    } else {
        weighted_majority_label(
            native_signals
                .iter()
                .map(|signal| (signal.features.liquidity_label.as_str(), signal.weight)),
            "favorable",
            "hostile",
            "neutral",
        )
    };

    let (hmm_state, log_likelihood, viterbi_log_likelihood, regime_probs) = if native_signals
        .is_empty()
    {
        let (log_alpha, log_likelihood) =
            ForwardBackward::forward(&ltf_features.observations, params);
        let log_beta = ForwardBackward::backward(&ltf_features.observations, params);
        let gamma = ForwardBackward::compute_gamma(&log_alpha, &log_beta, log_likelihood);
        let (states, viterbi_log_likelihood) = Viterbi::decode(&ltf_features.observations, params);
        (
            states
                .last()
                .copied()
                .map(state_name)
                .unwrap_or("Unknown")
                .to_string(),
            log_likelihood,
            viterbi_log_likelihood,
            regime_probs_from_log_gamma(gamma.last())?,
        )
    } else {
        let total_weight = native_signals
            .iter()
            .map(|signal| signal.weight)
            .sum::<f64>()
            .max(f64::EPSILON);
        (
            match weighted_regime_probs(&native_signals).dominant() {
                Regime::Accumulation => "Accumulation",
                Regime::ManipulationExpansion => "ManipulationExpansion",
                Regime::Distribution => "Distribution",
            }
            .to_string(),
            native_signals
                .iter()
                .map(|signal| signal.log_likelihood * signal.weight)
                .sum::<f64>()
                / total_weight,
            native_signals
                .iter()
                .map(|signal| signal.viterbi_log_likelihood * signal.weight)
                .sum::<f64>()
                / total_weight,
            weighted_regime_probs(&native_signals),
        )
    };

    let native_htf = build_context
        .native_frames
        .h4
        .or(build_context.native_frames.h1)
        .unwrap_or(htf);
    let native_mtf = build_context.native_frames.m15.unwrap_or(mtf);
    let native_ltf = build_context
        .native_frames
        .m5
        .or(build_context.native_frames.m1)
        .unwrap_or(ltf);

    let atr_htf = left_pad(
        compute_atr(native_htf, INDICATOR_PERIOD),
        native_htf.len(),
        0.0,
    );
    let atr_ltf = left_pad(
        compute_atr(native_ltf, INDICATOR_PERIOD),
        native_ltf.len(),
        0.0,
    );
    let cascade_config = CascadeConfig::default();
    let cascade_bull = cascade_bull(
        native_htf,
        native_mtf,
        native_ltf,
        &cascade_config,
        &atr_htf,
        &atr_ltf,
    );
    let cascade_bear = cascade_bear(
        native_htf,
        native_mtf,
        native_ltf,
        &cascade_config,
        &atr_htf,
        &atr_ltf,
    );
    let pre_bayes_policy = pre_bayes_evidence_policy();
    let multi_timeframe_evidence =
        parse_multi_timeframe_evidence(build_context.multi_timeframe_summary);
    let market = infer_market_from_symbol(build_context.symbol);
    let mut factor_registry = FactorRegistry::default();
    factor_registry.apply_learning_state(build_context.learning_state);
    let factor_engine = FactorEngine::new(factor_registry);
    let factor_output = factor_engine.run(
        ltf,
        &FactorContext {
            paired_candles: build_context.paired_candles,
            auxiliary: build_context.auxiliary,
            regime: Some(regime_probs.dominant()),
        },
        Some(build_context.learning_state),
    )?;
    let pre_bayes_evidence_filter = build_pre_bayes_evidence_filter(
        &pre_bayes_policy,
        &regime_label,
        &liquidity_label,
        &factor_output.diagnostics,
        &multi_timeframe_evidence,
        Some(&market),
    );

    let evidence = trade_evidence_from_pre_bayes_filter(network, &pre_bayes_evidence_filter)?;
    let base_entry_quality = infer_entry_quality(network, &evidence)?;
    let long_entry_bias = combine_bias_vectors(
        &combine_bias_vectors(
            &entry_quality_bias_from_signal(cascade_bull.final_posterior),
            &factor_output
                .diagnostics
                .entry_bias_for_direction(Direction::Bull),
        ),
        &multi_timeframe_entry_quality_bias(&multi_timeframe_evidence, Direction::Bull),
    );
    let short_entry_bias = combine_bias_vectors(
        &combine_bias_vectors(
            &entry_quality_bias_from_signal(cascade_bear.final_posterior),
            &factor_output
                .diagnostics
                .entry_bias_for_direction(Direction::Bear),
        ),
        &multi_timeframe_entry_quality_bias(&multi_timeframe_evidence, Direction::Bear),
    );
    let long_entry_quality = infer_entry_quality_with_bias(network, &evidence, &long_entry_bias)?;
    let short_entry_quality = infer_entry_quality_with_bias(network, &evidence, &short_entry_bias)?;
    let posterior = infer_trade_outcome(network, &evidence)?;
    let bull_trade_outcome = apply_factor_outcome_overlay(
        &infer_trade_outcome_with_entry_quality_bias(network, &evidence, &long_entry_bias)?,
        factor_output.diagnostics.directional_bias(Direction::Bull),
        factor_output.diagnostics.uncertainty,
    );
    let bear_trade_outcome = apply_factor_outcome_overlay(
        &infer_trade_outcome_with_entry_quality_bias(network, &evidence, &short_entry_bias)?,
        factor_output.diagnostics.directional_bias(Direction::Bear),
        factor_output.diagnostics.uncertainty,
    );
    let trade_outcome = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let fvgs = find_unfilled_fvgs(native_mtf);
    let obs = find_untested_obs(native_mtf);
    let decision = probabilistic_decision_snapshot(
        &regime_probs,
        &cascade_bull,
        &cascade_bear,
        &bull_trade_outcome,
        &bear_trade_outcome,
    );
    let entry_quality_node = network
        .nodes
        .get("entry_quality")
        .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?;
    let selected_entry_quality_distribution = match decision.selected_direction {
        Direction::Bull => &long_entry_quality,
        Direction::Bear => &short_entry_quality,
        Direction::Neutral => &base_entry_quality,
    };
    let selected_entry_quality_state =
        select_state_name(selected_entry_quality_distribution, entry_quality_node)?;
    let pre_bayes_entry_quality_bridge = build_pre_bayes_entry_quality_bridge(
        &factor_output.diagnostics,
        &decision,
        &long_entry_bias,
        &short_entry_bias,
        &long_entry_quality,
        &short_entry_quality,
        selected_entry_quality_distribution,
        entry_quality_node,
        &multi_timeframe_evidence,
    );
    let trade_plan = generate_probabilistic_trade_plan(
        native_mtf,
        native_ltf,
        &fvgs,
        &obs,
        symbol,
        regime_probs,
        &cascade_bull,
        &cascade_bear,
        &bull_trade_outcome,
        &bear_trade_outcome,
        &ProbabilisticPlanConfig::default(),
    );
    let mut trade_plan = trade_plan;
    trade_plan.uncertainties.push(format!(
        "factor_uncertainty={:.3}",
        factor_output.diagnostics.uncertainty
    ));
    trade_plan.uncertainties.push(format!(
        "pre_bayes_gating_status={}",
        pre_bayes_evidence_filter.gating_status
    ));
    trade_plan.uncertainties.push(format!(
        "native_execution_frames=htf:{} mtf:{} ltf:{}",
        if std::ptr::eq(native_htf.as_ptr(), htf.as_ptr()) {
            "provided"
        } else {
            "native"
        },
        if std::ptr::eq(native_mtf.as_ptr(), mtf.as_ptr()) {
            "provided"
        } else {
            "native"
        },
        if std::ptr::eq(native_ltf.as_ptr(), ltf.as_ptr()) {
            "provided"
        } else {
            "native"
        }
    ));
    let price_action = build_price_action_section(native_mtf, native_ltf, &atr_ltf, &fvgs, &obs);
    let technical_price =
        build_technical_price_section(native_ltf, None, None, build_context.auxiliary);
    let smt_correlation = if let Some(paired) = build_context.paired_candles {
        let fallback_auxiliary;
        let auxiliary = if let Some(auxiliary) = build_context.auxiliary {
            auxiliary
        } else {
            fallback_auxiliary = neutral_auxiliary(symbol);
            &fallback_auxiliary
        };
        build_smt_correlation_section(
            symbol,
            &format!("{}_paired", symbol),
            native_ltf,
            paired,
            auxiliary,
        )
    } else {
        empty_smt_correlation_section()
    };
    let regime_bayesian = build_regime_bayesian_section(
        &hmm_state,
        &regime_probs,
        &regime_label,
        &liquidity_label,
        &decision,
        "hmm_prior_times_bbn_trade_probability",
        None,
    );
    let multi_timeframe_section = build_analyze_multi_timeframe_section(
        build_context.multi_timeframe_summary,
        Some(&pre_bayes_evidence_filter),
    );
    let trade_plan_section = build_trade_plan_section(&trade_plan, None);
    let factor_ranking = if build_context.learning_state.factor_rankings.is_empty() {
        analyze_signal_rankings(&factor_output.latest_signals, regime_probs.dominant())
    } else {
        build_context.learning_state.factor_rankings.clone()
    };
    let factor_iteration_queue = if build_context.learning_state.factor_rankings.is_empty() {
        factor_ranking
            .iter()
            .map(FactorIterationPrompt::from)
            .filter(|item| item.iteration_action != "keep" || item.replacement_candidate)
            .collect()
    } else {
        build_context.learning_state.iteration_queue()
    };
    let factor_family_decisions = if build_context.learning_state.factor_rankings.is_empty() {
        let mut synthetic_state = LearningState::default();
        synthetic_state.factor_rankings = factor_ranking.clone();
        synthetic_state.family_decisions()
    } else {
        build_context.learning_state.family_decisions()
    };
    let feedback_history_summary = build_context.learning_state.summary();
    let previous_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let analyze_provenance = run_provenance(
        build_context.learning_state,
        &["analyze", symbol],
        data_fingerprint(ltf, build_context.paired_candles, "analyze"),
    );
    let dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &analyze_provenance,
    );
    let thresholds = decision_thresholds();
    let base_decision_hint = build_analyze_decision_hint(
        &dataset_comparability,
        &factor_iteration_queue,
        &factor_output.diagnostics,
    );
    let multi_timeframe_hint = if build_context.multi_timeframe_summary.is_empty() {
        "|multi_timeframe_hint_unavailable".to_string()
    } else {
        format!(
            "|{}",
            multi_timeframe_phase_hint(build_context.multi_timeframe_summary)
        )
    };
    let decision_hint = format!(
        "{}|pre_bayes_gating_status={}|pre_bayes_quality_score={:.3}{}",
        base_decision_hint,
        pre_bayes_evidence_filter.gating_status,
        pre_bayes_evidence_filter.evidence_quality_score,
        multi_timeframe_hint
    );
    let (_, historical_artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let factor_family_outcomes = derive_family_outcomes(
        &factor_family_decisions,
        &thresholds,
        &dataset_comparability,
        Some(&historical_artifact_family_trends),
    );
    let factor_family_diffs = family_diffs(
        previous_runs
            .last()
            .map(|run| run.factor_family_decisions.as_slice())
            .unwrap_or(&[]),
        &factor_family_decisions,
    );
    let factor_family_history = family_history_from_runs(previous_runs.iter().map(|run| {
        (
            run.run_id.clone(),
            run.timestamp,
            run.factor_family_decisions.clone(),
        )
    }));
    let decision_history_summary = decision_history_summary(previous_runs.iter().map(|run| {
        (
            run.promotion_decision.clone(),
            run.rollback_recommendation.clone(),
        )
    }));
    let observe_promotion = PromotionDecision {
        approved: false,
        status: "observe".to_string(),
        reason: dataset_comparability.reason.clone(),
        target_factors: Vec::new(),
        target_families: Vec::new(),
    };
    let observe_rollback = RollbackRecommendation {
        should_rollback: false,
        scope: "none".to_string(),
        reason: "analyze_observe_only".to_string(),
        target_factors: Vec::new(),
        target_families: Vec::new(),
    };
    let workflow_state = workflow_state_from_pre_bayes_filter(
        workflow_state_from_context(&decision_hint, &observe_promotion, &observe_rollback),
        &pre_bayes_evidence_filter,
    );
    let mut agent_action_plan = build_agent_action_plan(
        &decision_hint,
        &observe_promotion,
        &observe_rollback,
        &factor_iteration_queue,
        &factor_family_outcomes,
    );
    augment_action_plan_with_pre_bayes_filter(&mut agent_action_plan, &pre_bayes_evidence_filter);
    let recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: None,
        research_data: None,
        paired_data: None,
        update_outcome: None,
        update_entry_signal: None,
        update_feedback_file: pending_update_artifact_path(state_dir, symbol),
        user_data_selection_required: true,
    });
    concretize_action_plan_commands(&mut agent_action_plan, &recommended_commands);
    let recommended_next_command =
        recommended_next_command(&agent_action_plan, &recommended_commands);
    let mut agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &workflow_state,
        &decision_hint,
        &recommended_next_command,
        &recommended_commands,
        &dataset_comparability,
        &factor_iteration_queue,
        &factor_family_outcomes,
        Some(&pre_bayes_evidence_filter),
        Some(&pre_bayes_entry_quality_bridge),
        None,
        None,
    );
    agent_context_bundle.multi_timeframe_summary = build_context.multi_timeframe_summary.to_vec();
    let agent_prompts = build_analyze_agent_prompts(
        symbol,
        &decision,
        &factor_output.diagnostics,
        &pre_bayes_evidence_filter,
        &factor_ranking,
        &factor_iteration_queue,
        &feedback_history_summary,
        &trade_plan,
        &dataset_comparability,
        &decision_hint,
        build_context.multi_timeframe_summary,
    );

    let canonical_belief_report = build_canonical_belief_snapshot(
        symbol,
        Some(infer_market_from_symbol(symbol).as_str()),
        &pre_bayes_evidence_filter,
    )?;

    let staged_orchestration_trace = if staged_orchestration_enabled() {
        let mut pipeline_state = PipelineState::new(
            symbol,
            Some(infer_market_from_symbol(symbol).as_str()),
            "ict_engine_staged_orchestration",
        );
        let stage_trace = run_stage_plan(&StagePlan::analyze_risk_execution(), &mut pipeline_state);
        let policy_engine = CatBoostCompatiblePolicyEngine::load_default_or_placeholder();
        let staged_artifacts = ict_engine::application::orchestration::build_staged_artifacts(
            &factor_output.diagnostics,
            &decision_hint,
            &pre_bayes_evidence_filter,
            &selected_entry_quality_state,
            trade_plan.direction,
            trade_plan.risk_reward,
            trade_plan.kelly_fraction,
            &recommended_next_command,
            &policy_engine,
        );
        let final_adapter = FinalOutputAdapter;
        let final_artifact = final_adapter.adapt(&pipeline_state, &stage_trace);
        Some(serde_json::json!({
            "pipeline_state": pipeline_state,
            "stage_trace": stage_trace,
            "staged_artifacts": staged_artifacts,
            "final_artifact": final_artifact,
        }))
    } else {
        None
    };

    Ok(AnalyzeReport {
        symbol: symbol.to_string(),
        timestamp: Utc::now(),
        analysis: AnalyzeSections {
            price_action,
            technical_price,
            smt_correlation,
            regime_bayesian,
            multi_timeframe: multi_timeframe_section,
            trade_plan: trade_plan_section,
        },
        meta: AnalyzeMeta {
            state_dir: state_dir.to_string(),
            bars: AnalyzeBars {
                htf: htf.len(),
                mtf: mtf.len(),
                ltf: ltf.len(),
                observations: ltf_features.observations.len(),
            },
            data_source: None,
        },
        supporting: AnalyzeSupporting {
            model_state: AnalyzeModelState {
                hmm_state: hmm_state.clone(),
                log_likelihood,
                viterbi_log_likelihood,
                regime_probs,
                evidence_policy:
                    "multi_timeframe_hmm_prior_times_pre_bayes_evidence_filter_times_bbn_trade_probability"
                        .to_string(),
                canonical_belief_engine: canonical_belief_report.engine_trace.primary_engine.clone(),
                canonical_shadow_status: canonical_belief_report
                    .shadow_comparison
                    .as_ref()
                    .map(|summary| summary.status.clone())
                    .unwrap_or_else(|| "shadow=unavailable".to_string()),
            },
            provenance: analyze_provenance,
            promotion_decision: observe_promotion,
            rollback_recommendation: observe_rollback,
            labels: AnalyzeLabels {
                regime_label,
                liquidity_label,
            },
            ict: AnalyzeIctSummary {
                total_sweeps: if native_signals.is_empty() {
                    htf_features.sweep_count + mtf_features.sweep_count + ltf_features.sweep_count
                } else {
                    native_signals
                        .iter()
                        .map(|signal| signal.features.sweep_count)
                        .sum()
                },
                total_fvgs: if native_signals.is_empty() {
                    htf_features.fvg_count + mtf_features.fvg_count + ltf_features.fvg_count
                } else {
                    native_signals
                        .iter()
                        .map(|signal| signal.features.fvg_count)
                        .sum()
                },
                mtf_open_fvgs: fvgs.len(),
                mtf_untested_obs: obs.len(),
                ict_role: "native_multi_timeframe_evidence_only_non_deterministic".to_string(),
            },
            entry_quality: AnalyzeEntryQualitySummary {
                base: probability_map(&entry_quality_node.states, &base_entry_quality),
                long: probability_map(&entry_quality_node.states, &long_entry_quality),
                short: probability_map(&entry_quality_node.states, &short_entry_quality),
                selected_state: selected_entry_quality_state,
            },
            auxiliary: build_context.auxiliary.cloned(),
            decision,
            trade_outcome: AnalyzeTradeOutcomeSummary {
                base: probability_map(&trade_outcome.states, &posterior),
                long: probability_map(&trade_outcome.states, &bull_trade_outcome),
                short: probability_map(&trade_outcome.states, &bear_trade_outcome),
            },
            factor_diagnostics: factor_output.diagnostics,
            pre_bayes_evidence_filter: pre_bayes_evidence_filter.clone(),
            pre_bayes_entry_quality_bridge: pre_bayes_entry_quality_bridge.clone(),
            canonical_belief_report: canonical_belief_report.clone(),
            decision_thresholds: thresholds,
            factor_ranking,
            factor_iteration_queue,
            factor_family_decisions,
            factor_family_outcomes,
            factor_family_diffs,
            factor_family_history,
            decision_history_summary,
            workflow_state,
            agent_context_bundle: agent_context_bundle.clone(),
            agent_context_bundle_minimal: build_agent_context_bundle_minimal(&agent_context_bundle),
            recommended_commands,
            recommended_next_command,
            agent_action_plan,
            dataset_comparability,
            decision_hint,
            artifact_action_summary: Vec::new(),
            artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary::default(),
            artifact_decision_section: ict_engine::state::ArtifactDecisionSection::default(),
            agent_prompts,
            feedback_history_summary,
            multi_timeframe_summary: build_context.multi_timeframe_summary.to_vec(),
            raw_trade_plan: trade_plan,
            workflow_snapshot: WorkflowSnapshot::default(),
            staged_orchestration_trace,
        },
    })
}

fn run_probabilistic_backtest(
    symbol: &str,
    state_dir: &str,
    candles: &[Candle],
    paired_candles: Option<&[Candle]>,
    warmup_bars: usize,
    hold_bars: usize,
    realism: &ExecutionRealismConfig,
    online_learn: bool,
    params: &HMMParams,
    network: &ict_engine::bbn::BayesianNetwork,
    learning_state: &mut LearningState,
) -> Result<(
    BacktestReport,
    ict_engine::bbn::BayesianNetwork,
    Vec<TradeRecord>,
)> {
    let feedback_run_id = format!(
        "probabilistic-backtest-feedback:{}:{}",
        symbol,
        Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
    );
    let feedback_data_fingerprint =
        data_fingerprint(candles, paired_candles, "probabilistic_backtest_feedback");
    let minimum_history = warmup_bars.max(INDICATOR_PERIOD * 2 + 1);
    if candles.len() <= minimum_history + hold_bars {
        bail!(
            "need more candles for backtest: got {}, require at least {}",
            candles.len(),
            minimum_history + hold_bars + 1
        );
    }
    if hold_bars == 0 {
        bail!("hold_bars must be greater than zero");
    }

    let mut trades = Vec::new();
    let mut signals = 0usize;
    let mut learning_updates = 0usize;
    let mut last_decision = None;
    let last_signal_index = candles.len().saturating_sub(hold_bars + 1);
    let mut working_network = network.clone();
    let mut feedback_records = Vec::new();
    let mut bbn_feedback = Vec::new();

    for signal_index in (minimum_history - 1)..=last_signal_index {
        let window = &candles[..=signal_index];
        let analysis = build_analyze_report(
            symbol,
            state_dir,
            window,
            window,
            window,
            params,
            &working_network,
            AnalyzeBuildContext {
                symbol,
                paired_candles: paired_candles.and_then(|series| {
                    if series.is_empty() {
                        None
                    } else {
                        Some(&series[..=signal_index.min(series.len().saturating_sub(1))])
                    }
                }),
                auxiliary: None,
                learning_state,
                multi_timeframe_summary: &[],
                native_frames: AnalyzeNativeFrames::default(),
            },
        )?;
        last_decision = Some(analysis.supporting.decision.clone());

        if analysis.supporting.raw_trade_plan.direction == Direction::Neutral
            || analysis.supporting.raw_trade_plan.kelly_fraction <= 0.0
        {
            continue;
        }

        signals += 1;

        if let Some(simulated) = BacktestEngine::simulate_trade_with_realism(
            candles,
            signal_index,
            &analysis.supporting.raw_trade_plan,
            hold_bars,
            realism,
        ) {
            trades.push(TradeRecord {
                timestamp: candles[simulated.entry_index].timestamp,
                symbol: parse_symbol(symbol),
                direction: analysis.supporting.raw_trade_plan.direction,
                entry_price: simulated.entry_price,
                exit_price: simulated.exit_price,
                pnl: simulated.pnl,
                exit_reason: Some(format!("{:?}", simulated.exit_reason)),
                regime_at_entry: analysis.supporting.model_state.regime_probs.dominant(),
                cascade_max_layer: selected_cascade_max_layer(&analysis.supporting.raw_trade_plan),
                cascade_direction: analysis.supporting.raw_trade_plan.direction,
                factor_values: decision_factor_values(
                    &analysis.supporting.decision,
                    &analysis.supporting.raw_trade_plan,
                    &analysis.supporting.factor_diagnostics,
                ),
            });

            feedback_records.push(enrich_feedback_record(
                build_feedback_record(
                    symbol,
                    "probabilistic_backtest",
                    candles[simulated.entry_index].timestamp,
                    &analysis.supporting.factor_diagnostics,
                    &analysis.supporting.decision,
                    simulated.pnl,
                    trade_outcome_label_from_pnl(simulated.pnl),
                    analysis.supporting.model_state.regime_probs.dominant(),
                ),
                &feedback_run_id,
                format!(
                    "{}:{}:{}",
                    symbol,
                    candles[simulated.entry_index].timestamp.to_rfc3339(),
                    candles[simulated.exit_index].timestamp.to_rfc3339()
                ),
                learning_state,
                &feedback_data_fingerprint,
            ));

            let outcome_label = trade_outcome_label_from_pnl(simulated.pnl);
            let evidence = trade_evidence_from_labels(
                &working_network,
                &[
                    (
                        "entry_quality",
                        analysis.supporting.entry_quality.selected_state.as_str(),
                    ),
                    (
                        "factor_alignment",
                        analysis
                            .supporting
                            .factor_diagnostics
                            .alignment_label
                            .as_str(),
                    ),
                    (
                        "factor_uncertainty",
                        analysis
                            .supporting
                            .factor_diagnostics
                            .uncertainty_label
                            .as_str(),
                    ),
                ],
            )?;
            let realized_state_index = working_network
                .nodes
                .get("trade_outcome")
                .and_then(|node| node.state_index(&outcome_label))
                .ok_or_else(|| anyhow!("unknown trade outcome state '{}'", outcome_label))?;

            if online_learn {
                CPTUpdater::default().update_from_trade(
                    &mut working_network,
                    &evidence,
                    TradeOutcome {
                        node_id: "trade_outcome".into(),
                        realized_state_index,
                    },
                )?;
                if let Some(last_feedback) = feedback_records.last().cloned() {
                    let new_feedback = learning_state.merge_feedback_records(&[last_feedback]);
                    WeightUpdater::default().apply_feedback(learning_state, &new_feedback);
                }
                learning_updates += 1;
            } else {
                bbn_feedback.push((
                    evidence,
                    TradeOutcome {
                        node_id: "trade_outcome".into(),
                        realized_state_index,
                    },
                ));
            }
        }
    }

    if !bbn_feedback.is_empty() && !online_learn {
        CPTUpdater::default().batch_update(&mut working_network, &bbn_feedback)?;
        learning_updates = bbn_feedback.len();
        let new_feedback = learning_state.merge_feedback_records(&feedback_records);
        WeightUpdater::default().apply_feedback(learning_state, &new_feedback);
    }

    let trade_returns: Vec<f64> = trades.iter().map(|trade| trade.pnl).collect();
    let equity_curve = build_equity_curve(&trade_returns);
    let total_return = equity_curve.last().copied().unwrap_or(1.0) - 1.0;
    let regime_metrics = RegimeSplit::regime_metrics(&trades)
        .into_iter()
        .map(|(regime, win_rate, avg_pnl)| BacktestRegimeSummary {
            regime,
            win_rate,
            avg_pnl,
        })
        .collect();
    let recent_trades = trades
        .iter()
        .rev()
        .take(5)
        .map(backtest_trade_sample)
        .collect::<Vec<_>>()
        .into_iter()
        .rev()
        .collect();
    let factor_ranking = learning_state.factor_rankings.clone();
    let factor_iteration_queue = learning_state.iteration_queue();
    let factor_family_decisions = learning_state.family_decisions();
    let feedback_history_summary = learning_state.summary();
    let final_trade_outcome_cpt = trade_outcome_cpt_snapshot(&working_network)?;
    let agent_prompts = build_backtest_agent_prompts(
        symbol,
        &factor_ranking,
        &factor_iteration_queue,
        &feedback_history_summary,
        total_return,
        trades.len(),
        &final_trade_outcome_cpt,
    );

    let report = BacktestReport {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        provenance: RunProvenance::default(),
        decision_thresholds: decision_thresholds(),
        dataset_comparability: DatasetComparability::default(),
        promotion_decision: PromotionDecision::default(),
        rollback_recommendation: RollbackRecommendation::default(),
        bars: candles.len(),
        warmup_bars: minimum_history,
        hold_bars,
        spread_bps: realism.spread_bps,
        slippage_bps: realism.slippage_bps,
        fee_bps: realism.fee_bps,
        ambiguous_bar_policy: ambiguous_bar_policy_label(realism.ambiguous_bar_policy),
        window_mode: "expanding".to_string(),
        evidence_policy: "same_as_analyze_json_snapshot".to_string(),
        ict_role: "evidence_only_non_deterministic".to_string(),
        online_learning: online_learn,
        learning_updates,
        signals,
        trades: trades.len(),
        metrics: BacktestMetricsSummary {
            total_return,
            sharpe: Metrics::sharpe(&trade_returns, 0.0),
            max_drawdown: Metrics::max_drawdown(&equity_curve),
            win_rate: Metrics::win_rate(&trades),
            profit_factor: Metrics::profit_factor(&trades),
            conformal_coverage_1sigma: 0.0,
            conformal_miscoverage_1sigma: 0.0,
            mean_prediction_interval_half_width: 0.0,
            worst_window_miscoverage: 0.0,
            regime_break_penalty: 0.0,
            structural_break_score: 0.0,
            structural_break_index: None,
            structural_break_detected: false,
            signal_structural_break_score: 0.0,
            signal_structural_break_index: None,
            signal_structural_break_detected: false,
            residual_structural_break_score: 0.0,
            residual_structural_break_index: None,
            residual_structural_break_detected: false,
            rolling_ic_structural_break_score: 0.0,
            rolling_ic_structural_break_index: None,
            rolling_ic_structural_break_detected: false,
        },
        equity_curve,
        regime_metrics,
        factor_ranking,
        factor_score_deltas: Vec::new(),
        trade_outcome_deltas: Vec::new(),
        factor_iteration_queue,
        factor_family_decisions,
        factor_family_outcomes: Vec::new(),
        factor_family_diffs: Vec::new(),
        factor_family_history: Vec::new(),
        decision_history_summary: DecisionHistorySummary::default(),
        agent_action_plan: AgentActionPlan::default(),
        workflow_state: WorkflowState::default(),
        agent_context_bundle: AgentContextBundle::default(),
        agent_context_bundle_minimal: AgentContextBundleMinimal::default(),
        recommended_commands: CommandRecommendations::default(),
        recommended_next_command: "recommended_command_unavailable".to_string(),
        artifact_action_summary: Vec::new(),
        artifact_decision_summary: ict_engine::state::ArtifactDecisionSummary::default(),
        artifact_decision_section: ict_engine::state::ArtifactDecisionSection::default(),
        agent_prompts,
        feedback_history_summary,
        multi_timeframe_summary: Vec::new(),
        last_decision,
        final_trade_outcome_cpt,
        recent_trades,
        workflow_snapshot: WorkflowSnapshot::default(),
    };

    Ok((report, working_network, trades))
}

fn build_price_action_section(
    mtf: &[Candle],
    ltf: &[Candle],
    atr_ltf: &[f64],
    fvgs: &[ict_engine::types::FairValueGap],
    obs: &[ict_engine::types::OrderBlock],
) -> PriceActionSection {
    let swing_highs = find_swing_highs(mtf, 3);
    let swing_lows = find_swing_lows(mtf, 3);
    let breaks = detect_structure_breaks(mtf, &swing_highs, &swing_lows);
    let latest_break = breaks
        .last()
        .map(|brk| format!("{:?}_{:?}", brk.break_type, brk.direction));
    let recent_break_count = count_recent_breaks(&breaks, 20, mtf.len());
    let pools = detect_liquidity_pools(mtf, atr_ltf, 0.5, 2);
    let sweeps = detect_liquidity_sweep(mtf, &pools, 5);
    let liquidity_sweeps_recent = count_recent_sweeps(mtf, &sweeps, 20);
    let bullish_cisds = detect_cisd(ltf, &detect_order_blocks(ltf), 1);
    let bullish_cisd = bullish_cisds.iter().any(|cisd| {
        cisd.direction == Direction::Bull && cisd.confirm_bar >= ltf.len().saturating_sub(10)
    });
    let bearish_cisd = bullish_cisds.iter().any(|cisd| {
        cisd.direction == Direction::Bear && cisd.confirm_bar >= ltf.len().saturating_sub(10)
    });
    let bull_expansion = check_bull_expansion_exists(mtf, 20, 1.5);
    let bear_expansion = check_bear_expansion_exists(mtf, 20, 1.5);
    let structure_bias = if bull_expansion && !bear_expansion {
        Direction::Bull
    } else if bear_expansion && !bull_expansion {
        Direction::Bear
    } else {
        breaks
            .last()
            .map(|brk| brk.direction)
            .unwrap_or(Direction::Neutral)
    };
    let rejection_block_present = has_recent_pinbar(ltf, atr_ltf, 5);
    let narrative = if structure_bias == Direction::Bull {
        "bullish_price_action_with_higher_probability_if_execution_confirms".to_string()
    } else if structure_bias == Direction::Bear {
        "bearish_price_action_with_higher_probability_if_execution_confirms".to_string()
    } else {
        "mixed_price_action_no_decisive_structure_edge".to_string()
    };

    PriceActionSection {
        probability_role: "structural_evidence_for_probability_model".to_string(),
        structure_bias,
        latest_break,
        recent_break_count,
        swing_highs: swing_highs.len(),
        swing_lows: swing_lows.len(),
        bull_expansion,
        bear_expansion,
        expansion_strength: expansion_strength(mtf, 20),
        liquidity_sweeps_recent,
        open_fvgs: fvgs.len(),
        untested_order_blocks: obs.len(),
        bullish_cisd,
        bearish_cisd,
        rejection_block_present,
        narrative,
    }
}

fn build_regime_bayesian_section(
    hmm_state: &str,
    regime_probs: &RegimeProbs,
    regime_label: &str,
    liquidity_label: &str,
    decision: &ProbabilisticDecisionSnapshot,
    evidence_policy: &str,
    options_hedging: Option<&OptionsHedgingSection>,
) -> RegimeBayesianSection {
    let mut evidence_policy = evidence_policy.to_string();
    if let Some(hedging) = options_hedging {
        if hedging.hedge_pressure_direction.is_some() {
            evidence_policy.push_str("+options_hedging_overlay");
        }
    }

    RegimeBayesianSection {
        hmm_state: hmm_state.to_string(),
        regime_probs: *regime_probs,
        regime_label: regime_label.to_string(),
        liquidity_label: liquidity_label.to_string(),
        long_score: decision.long_score,
        short_score: decision.short_score,
        win_prob_long: decision.win_prob_long,
        win_prob_short: decision.win_prob_short,
        selected_direction: decision.selected_direction,
        evidence_policy,
        ict_role: decision.ict_role.clone(),
    }
}

fn build_trade_plan_section(
    trade_plan: &TradePlan,
    options_hedging: Option<&OptionsHedgingSection>,
) -> TradePlanSection {
    let actionable = trade_plan.direction != Direction::Neutral && trade_plan.position_size > 0.0;
    let hedge_fragment = options_hedging
        .and_then(|hedging| hedging.hedge_pressure_direction.as_deref())
        .map(|direction| format!(";options_hedging_bias={direction}"));
    let narrative = if actionable {
        format!(
            "preferred_{:?}_entry_with_defined_risk_and_positive_position_size{}",
            trade_plan.direction,
            hedge_fragment.clone().unwrap_or_default()
        )
    } else if trade_plan.direction != Direction::Neutral {
        format!(
            "{:?}_bias_exists_but_position_size_is_zero_due_to_probability_risk_constraints{}",
            trade_plan.direction,
            hedge_fragment.unwrap_or_default()
        )
    } else {
        "no_trade_due_to_insufficient_edge".to_string()
    };

    TradePlanSection {
        probability_role: "execution_plan_derived_from_probability_model".to_string(),
        actionable,
        direction: trade_plan.direction,
        entry: trade_plan.entry,
        stop_loss: trade_plan.stop_loss,
        take_profits: vec![trade_plan.tp1, trade_plan.tp2, trade_plan.tp3],
        risk_reward: trade_plan.risk_reward,
        posterior: trade_plan.posterior,
        win_probability: trade_plan.win_probability,
        kelly_fraction: trade_plan.kelly_fraction,
        position_size: trade_plan.position_size,
        uncertainties: trade_plan.uncertainties.clone(),
        narrative,
    }
}

fn pre_bayes_policy_diff(
    previous: Option<&ict_engine::state::PreBayesEvidencePolicy>,
    current: &ict_engine::state::PreBayesEvidencePolicy,
) -> ict_engine::state::PreBayesPolicyDiff {
    let mut changed_fields = Vec::new();
    if let Some(previous) = previous {
        if previous.min_directional_support_gap != current.min_directional_support_gap {
            changed_fields.push("min_directional_support_gap".to_string());
        }
        if previous.high_uncertainty_threshold != current.high_uncertainty_threshold {
            changed_fields.push("high_uncertainty_threshold".to_string());
        }
        if previous.min_multi_timeframe_alignment_score
            != current.min_multi_timeframe_alignment_score
        {
            changed_fields.push("min_multi_timeframe_alignment_score".to_string());
        }
        if previous.min_multi_timeframe_entry_alignment_score
            != current.min_multi_timeframe_entry_alignment_score
        {
            changed_fields.push("min_multi_timeframe_entry_alignment_score".to_string());
        }
        if previous.hard_pass_quality_threshold != current.hard_pass_quality_threshold {
            changed_fields.push("hard_pass_quality_threshold".to_string());
        }
        if previous.neutralized_quality_threshold != current.neutralized_quality_threshold {
            changed_fields.push("neutralized_quality_threshold".to_string());
        }
        if previous.directional_conflict_penalty != current.directional_conflict_penalty {
            changed_fields.push("directional_conflict_penalty".to_string());
        }
        if previous.mixed_alignment_penalty != current.mixed_alignment_penalty {
            changed_fields.push("mixed_alignment_penalty".to_string());
        }
        if previous.multi_timeframe_direction_conflict_penalty
            != current.multi_timeframe_direction_conflict_penalty
        {
            changed_fields.push("multi_timeframe_direction_conflict_penalty".to_string());
        }
        if previous.multi_timeframe_alignment_penalty != current.multi_timeframe_alignment_penalty {
            changed_fields.push("multi_timeframe_alignment_penalty".to_string());
        }
        if previous.multi_timeframe_entry_penalty != current.multi_timeframe_entry_penalty {
            changed_fields.push("multi_timeframe_entry_penalty".to_string());
        }
        if previous.multi_timeframe_alignment_bonus != current.multi_timeframe_alignment_bonus {
            changed_fields.push("multi_timeframe_alignment_bonus".to_string());
        }
        if previous.hostile_liquidity_penalty != current.hostile_liquidity_penalty {
            changed_fields.push("hostile_liquidity_penalty".to_string());
        }
        if previous.favorable_liquidity_bonus != current.favorable_liquidity_bonus {
            changed_fields.push("favorable_liquidity_bonus".to_string());
        }
        if previous.hostile_liquidity_forces_high_uncertainty
            != current.hostile_liquidity_forces_high_uncertainty
        {
            changed_fields.push("hostile_liquidity_forces_high_uncertainty".to_string());
        }
    } else {
        changed_fields.push("initial_policy".to_string());
    }
    ict_engine::state::PreBayesPolicyDiff {
        previous_version: previous.map(|policy| policy.version.clone()),
        summary: if changed_fields.is_empty() {
            "policy_unchanged".to_string()
        } else {
            format!("changed_fields={:?}", changed_fields)
        },
        changed_fields,
    }
}

fn pre_bayes_policy_lineage_summary(
    history: &[PreBayesPolicyRecord],
    latest_gate_status: &str,
) -> ict_engine::state::PreBayesPolicyLineageSummary {
    let latest = history.last();
    let previous = history.iter().rev().nth(1);
    let changed_fields_union = history
        .iter()
        .flat_map(|record| record.diff_from_previous.changed_fields.clone())
        .collect::<std::collections::BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>();
    let rollback_candidate_version =
        if matches!(latest_gate_status, "observe_only" | "pass_neutralized") {
            previous.map(|record| record.policy.version.clone())
        } else {
            None
        };
    let rollback_reason = if rollback_candidate_version.is_some() {
        format!(
            "latest_gate_status={} suggests reverting to previous stable policy version",
            latest_gate_status
        )
    } else {
        "no_policy_rollback_suggested".to_string()
    };
    ict_engine::state::PreBayesPolicyLineageSummary {
        latest_version: latest.map(|record| record.policy.version.clone()),
        previous_version: previous.map(|record| record.policy.version.clone()),
        total_versions: history.len(),
        changed_fields_union,
        rollback_candidate_version,
        rollback_reason,
    }
}

fn pre_bayes_soft_evidence_diff(
    filter: &PreBayesEvidenceFilter,
) -> Vec<ict_engine::state::PreBayesSoftEvidenceNodeDiff> {
    [
        (
            "market_regime",
            &filter.filtered_market_regime_label,
            &filter.soft_market_regime_distribution,
        ),
        (
            "liquidity_context",
            &filter.filtered_liquidity_context_label,
            &filter.soft_liquidity_context_distribution,
        ),
        (
            "factor_alignment",
            &filter.filtered_factor_alignment,
            &filter.soft_factor_alignment_distribution,
        ),
        (
            "factor_uncertainty",
            &filter.filtered_factor_uncertainty,
            &filter.soft_factor_uncertainty_distribution,
        ),
        (
            "multi_timeframe_resonance",
            &filter.filtered_multi_timeframe_resonance_label,
            &filter.soft_multi_timeframe_resonance_distribution,
        ),
    ]
    .into_iter()
    .map(|(node, filtered_state, distribution)| {
        let dominant = distribution
            .iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal));
        let entropy = distribution
            .values()
            .copied()
            .filter(|value| *value > f64::EPSILON)
            .map(|value| -value * value.ln())
            .sum::<f64>();
        ict_engine::state::PreBayesSoftEvidenceNodeDiff {
            node: node.to_string(),
            filtered_state: filtered_state.to_string(),
            dominant_soft_state: dominant.map(|(state, _)| state.clone()),
            dominant_soft_probability: dominant.map(|(_, value)| *value).unwrap_or(0.0),
            entropy,
            diverges_from_filtered_state: dominant
                .map(|(state, _)| state != filtered_state)
                .unwrap_or(false),
        }
    })
    .collect()
}

fn max_probability_label(distribution: &BTreeMap<String, f64>) -> (Option<String>, f64) {
    distribution
        .iter()
        .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(label, value)| (Some(label.clone()), *value))
        .unwrap_or((None, 0.0))
}

fn pre_bayes_entry_quality_bridge_diff(
    bridge: &ict_engine::state::PreBayesEntryQualityBridge,
) -> ict_engine::state::PreBayesEntryQualityBridgeDiff {
    let (dominant_long_entry_quality, dominant_long_entry_quality_probability) =
        max_probability_label(&bridge.long_entry_quality);
    let (dominant_short_entry_quality, dominant_short_entry_quality_probability) =
        max_probability_label(&bridge.short_entry_quality);
    let (selected_entry_quality, selected_entry_quality_probability) =
        max_probability_label(&bridge.selected_entry_quality);
    ict_engine::state::PreBayesEntryQualityBridgeDiff {
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
        rationale_summary: bridge.rationale.iter().take(5).cloned().collect(),
    }
}

fn pre_bayes_report_summary(
    policy: Option<&ict_engine::state::PreBayesEvidencePolicy>,
    bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
) -> Vec<String> {
    let mut summary = Vec::new();
    if let Some(policy) = policy {
        summary.push(format!(
            "policy_version={} source={} hard_pass={:.2} neutralized_pass={:.2}",
            policy.version,
            policy.source,
            policy.hard_pass_quality_threshold,
            policy.neutralized_quality_threshold
        ));
    }
    if let Some(bridge) = bridge {
        let bridge_diff = pre_bayes_entry_quality_bridge_diff(bridge);
        summary.extend(bridge_diff.rationale_summary.clone());
        summary.push(format!(
            "selected_entry_quality={:?} selected_probability={:.3} long_short_gap={:.3} mtf_direction={} mtf_alignment={:.3} mtf_entry_alignment={:.3}",
            bridge_diff.selected_entry_quality,
            bridge_diff.selected_entry_quality_probability,
            bridge_diff.long_short_signal_probability_gap,
            bridge_diff.multi_timeframe_direction_bias,
            bridge_diff.multi_timeframe_alignment_score.unwrap_or_default(),
            bridge_diff
                .multi_timeframe_entry_alignment_score
                .unwrap_or_default()
        ));
    }
    summary
}

fn combine_regime_labels(labels: &[&str]) -> String {
    let bull = labels.iter().filter(|label| **label == "bull").count();
    let bear = labels.iter().filter(|label| **label == "bear").count();

    if bull > bear && bull >= 2 {
        "bull".to_string()
    } else if bear > bull && bear >= 2 {
        "bear".to_string()
    } else {
        "range".to_string()
    }
}

fn combine_liquidity_labels(labels: &[&str]) -> String {
    let hostile = labels.iter().filter(|label| **label == "hostile").count();
    let favorable = labels.iter().filter(|label| **label == "favorable").count();

    if hostile >= 2 {
        "hostile".to_string()
    } else if favorable == labels.len() {
        "favorable".to_string()
    } else {
        "neutral".to_string()
    }
}

fn resolve_live_backend_base_url(
    backend: &str,
    openalice_base_url: &str,
    nofx_base_url: &str,
) -> String {
    match backend.trim().to_ascii_lowercase().as_str() {
        "openbb" => "native://openbb".to_string(),
        "openalice" => openalice_base_url.to_string(),
        "nofx" => nofx_base_url.to_string(),
        _ => "native://openbb".to_string(),
    }
}

fn parse_symbol(symbol: &str) -> Symbol {
    match symbol.to_uppercase().as_str() {
        "NQ" => Symbol::NQ,
        "ES" => Symbol::ES,
        "YM" => Symbol::YM,
        "GC" => Symbol::GC,
        "CL" => Symbol::CL,
        _ => Symbol::NQ,
    }
}

fn selected_cascade_max_layer(plan: &TradePlan) -> CascadeLayer {
    let cascade = match plan.direction {
        Direction::Bull => &plan.cascade_bull,
        Direction::Bear => &plan.cascade_bear,
        Direction::Neutral => &plan.cascade_bull,
    };

    cascade
        .steps
        .iter()
        .rev()
        .find(|step| step.satisfied)
        .map(|step| step.layer)
        .unwrap_or(CascadeLayer::L1)
}

fn decision_factor_values(
    decision: &ProbabilisticDecisionSnapshot,
    trade_plan: &TradePlan,
    factor_diagnostics: &FactorDiagnostics,
) -> HashMap<String, f64> {
    HashMap::from([
        ("long_score".to_string(), decision.long_score),
        ("short_score".to_string(), decision.short_score),
        ("win_prob_long".to_string(), decision.win_prob_long),
        ("win_prob_short".to_string(), decision.win_prob_short),
        ("selected_score".to_string(), decision.selected_score),
        (
            "selected_win_probability".to_string(),
            decision.selected_win_probability,
        ),
        ("kelly_fraction".to_string(), trade_plan.kelly_fraction),
        ("posterior".to_string(), trade_plan.posterior),
        ("ict_support_long".to_string(), decision.ict_support_long),
        ("ict_support_short".to_string(), decision.ict_support_short),
        (
            "factor_support_long".to_string(),
            factor_diagnostics.long_support,
        ),
        (
            "factor_support_short".to_string(),
            factor_diagnostics.short_support,
        ),
        (
            "factor_uncertainty".to_string(),
            factor_diagnostics.uncertainty,
        ),
    ])
}

fn build_equity_curve(returns: &[f64]) -> Vec<f64> {
    let mut equity = 1.0;
    let mut curve = vec![equity];

    for trade_return in returns {
        equity *= 1.0 + trade_return;
        curve.push(equity);
    }

    curve
}

fn backtest_trade_sample(trade: &TradeRecord) -> BacktestTradeSample {
    BacktestTradeSample {
        timestamp: trade.timestamp,
        direction: trade.direction,
        entry_price: trade.entry_price,
        exit_price: trade.exit_price,
        pnl: trade.pnl,
        long_score: *trade.factor_values.get("long_score").unwrap_or(&0.0),
        short_score: *trade.factor_values.get("short_score").unwrap_or(&0.0),
        win_prob_long: *trade.factor_values.get("win_prob_long").unwrap_or(&0.0),
        win_prob_short: *trade.factor_values.get("win_prob_short").unwrap_or(&0.0),
        ict_role: "evidence_only_non_deterministic".to_string(),
    }
}

fn trade_outcome_label_from_pnl(pnl: f64) -> String {
    if pnl > 1e-12 {
        "win".to_string()
    } else if pnl < -1e-12 {
        "loss".to_string()
    } else {
        "breakeven".to_string()
    }
}

fn select_state_name(distribution: &[f64], node: &ict_engine::bbn::Node) -> Result<String> {
    let state_index = distribution
        .iter()
        .copied()
        .enumerate()
        .max_by(|a, b| a.1.partial_cmp(&b.1).unwrap_or(std::cmp::Ordering::Equal))
        .map(|(idx, _)| idx)
        .ok_or_else(|| anyhow!("empty state distribution for '{}'", node.id))?;

    node.state_name(state_index)
        .map(str::to_string)
        .ok_or_else(|| {
            anyhow!(
                "state index {} out of bounds for '{}'",
                state_index,
                node.id
            )
        })
}

fn trade_outcome_cpt_snapshot(
    network: &ict_engine::bbn::BayesianNetwork,
) -> Result<BTreeMap<String, BTreeMap<String, f64>>> {
    let trade_outcome = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let entry_quality = network
        .nodes
        .get("entry_quality")
        .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?;

    let mut snapshot = BTreeMap::new();
    let factor_alignment = network
        .nodes
        .get("factor_alignment")
        .ok_or_else(|| anyhow!("missing node 'factor_alignment'"))?;
    let factor_uncertainty = network
        .nodes
        .get("factor_uncertainty")
        .ok_or_else(|| anyhow!("missing node 'factor_uncertainty'"))?;
    let alignment_index = factor_alignment
        .state_index("mixed")
        .ok_or_else(|| anyhow!("missing state 'mixed' on factor_alignment"))?;
    let uncertainty_index = factor_uncertainty
        .state_index("low")
        .ok_or_else(|| anyhow!("missing state 'low' on factor_uncertainty"))?;
    for (entry_index, entry_state) in entry_quality.states.iter().enumerate() {
        let probabilities = trade_outcome
            .cpt
            .get(&vec![entry_index, alignment_index, uncertainty_index])
            .ok_or_else(|| {
                anyhow!(
                    "missing CPT entry for entry_quality index {} with baseline factor evidence",
                    entry_index
                )
            })?;
        snapshot.insert(
            entry_state.clone(),
            probability_map(&trade_outcome.states, probabilities),
        );
    }

    Ok(snapshot)
}

fn load_or_init_hmm_params(symbol: &str, state_dir: &str) -> HMMParams {
    if !state_exists(state_dir, symbol, HMM_STATE_FILE) {
        return init_hmm_params(OBS_DIM);
    }

    match load_state::<HMMParams, _>(state_dir, symbol, HMM_STATE_FILE) {
        Ok(params) if hmm_params_compatible(&params) => params,
        Ok(_) => init_hmm_params(OBS_DIM),
        Err(err) => {
            eprintln!(
                "warning: failed to load HMM state for '{}' from '{}': {}",
                symbol, state_dir, err
            );
            init_hmm_params(OBS_DIM)
        }
    }
}

fn load_or_init_trading_network(
    symbol: &str,
    state_dir: &str,
) -> Result<ict_engine::bbn::BayesianNetwork> {
    if !state_exists(state_dir, symbol, BBN_STATE_FILE) {
        return build_trading_network();
    }

    match load_state::<ict_engine::bbn::BayesianNetwork, _>(state_dir, symbol, BBN_STATE_FILE) {
        Ok(mut network) => {
            upgrade_trading_network(&mut network)?;
            Ok(network)
        }
        Err(err) => {
            eprintln!(
                "warning: failed to load BBN state for '{}' from '{}': {}",
                symbol, state_dir, err
            );
            build_trading_network()
        }
    }
}

fn hmm_params_compatible(params: &HMMParams) -> bool {
    params.n_states == 3
        && params.transition.len() == params.n_states
        && params.initial_probs.len() == params.n_states
        && params.emission_means.len() == params.n_states
        && params.emission_stds.len() == params.n_states
        && params.emission_means.iter().all(|row| row.len() == OBS_DIM)
        && params.emission_stds.iter().all(|row| row.len() == OBS_DIM)
}

fn entry_quality_label_from_probability(probability: f64) -> &'static str {
    if probability >= 0.66 {
        "high"
    } else if probability <= 0.33 {
        "low"
    } else {
        "medium"
    }
}

fn apply_feedback_to_trade_outcome_network(
    network: &mut ict_engine::bbn::BayesianNetwork,
    feedback: &[FeedbackRecord],
) -> Result<usize> {
    let mut updates = Vec::new();

    for record in feedback {
        let entry_quality = entry_quality_label_from_probability(
            record.model_probabilities_before_trade.selected_probability,
        );
        let factor_alignment = factor_alignment_label_from_feedback(record);
        let factor_uncertainty = factor_uncertainty_label_from_feedback(record);
        let evidence = trade_evidence_from_labels(
            network,
            &[
                ("entry_quality", entry_quality),
                ("factor_alignment", factor_alignment.as_str()),
                ("factor_uncertainty", factor_uncertainty.as_str()),
            ],
        )?;
        let outcome_label = normalize_trade_outcome_label(&record.realized_outcome);
        let realized_state_index = network
            .nodes
            .get("trade_outcome")
            .and_then(|node| node.state_index(&outcome_label))
            .ok_or_else(|| anyhow!("unknown trade outcome state '{}'", outcome_label))?;
        updates.push((
            evidence,
            TradeOutcome {
                node_id: "trade_outcome".into(),
                realized_state_index,
            },
        ));
    }

    if updates.is_empty() {
        return Ok(0);
    }

    CPTUpdater::default().batch_update(network, &updates)?;
    Ok(updates.len())
}

fn factor_alignment_label_from_feedback(record: &FeedbackRecord) -> String {
    if record.factors_used.is_empty() {
        return match record.model_probabilities_before_trade.selected_direction {
            Direction::Bull => "bullish".to_string(),
            Direction::Bear => "bearish".to_string(),
            Direction::Neutral => "mixed".to_string(),
        };
    }

    let long_support = record
        .factors_used
        .iter()
        .map(|factor| factor.long_support)
        .sum::<f64>();
    let short_support = record
        .factors_used
        .iter()
        .map(|factor| factor.short_support)
        .sum::<f64>();

    if long_support > short_support + 0.05 {
        "bullish".to_string()
    } else if short_support > long_support + 0.05 {
        "bearish".to_string()
    } else {
        "mixed".to_string()
    }
}

fn factor_uncertainty_label_from_feedback(record: &FeedbackRecord) -> String {
    let uncertainty = if record.factors_used.is_empty() {
        record.model_probabilities_before_trade.uncertainty
    } else {
        record
            .factors_used
            .iter()
            .map(|factor| factor.uncertainty_contribution)
            .sum::<f64>()
    };
    if uncertainty >= 0.45 {
        "high".to_string()
    } else {
        "low".to_string()
    }
}

fn regime_probs_from_log_gamma(log_gamma: Option<&Vec<f64>>) -> Result<RegimeProbs> {
    let log_gamma = log_gamma.ok_or_else(|| anyhow!("missing HMM posterior probabilities"))?;
    if log_gamma.len() < 3 {
        bail!("expected 3 HMM states, got {}", log_gamma.len());
    }

    let accumulation = log_gamma[0].exp();
    let manipulation_expansion = log_gamma[1].exp();
    let distribution = log_gamma[2].exp();
    let sum = accumulation + manipulation_expansion + distribution;
    if sum <= f64::EPSILON {
        bail!("invalid HMM posterior: probabilities sum to zero");
    }

    Ok(RegimeProbs {
        accumulation: accumulation / sum,
        manipulation_expansion: manipulation_expansion / sum,
        distribution: distribution / sum,
    })
}

fn distribution_from_map(states: &[String], probabilities: &BTreeMap<String, f64>) -> Vec<f64> {
    states
        .iter()
        .map(|state| probabilities.get(state).copied().unwrap_or(0.0))
        .collect()
}

fn build_feedback_record(
    symbol: &str,
    source: &str,
    timestamp: chrono::DateTime<Utc>,
    factor_diagnostics: &FactorDiagnostics,
    decision: &ProbabilisticDecisionSnapshot,
    pnl: f64,
    realized_outcome: String,
    regime_at_entry: Regime,
) -> FeedbackRecord {
    let mut factors_used = Vec::new();
    for factor in factor_diagnostics
        .bullish_factors
        .iter()
        .chain(factor_diagnostics.bearish_factors.iter())
        .chain(factor_diagnostics.uncertainty_factors.iter())
    {
        factors_used.push(FeedbackFactorUsage {
            factor_name: factor.factor_name.clone(),
            category: factor.category.clone(),
            direction: factor.direction,
            value: factor.value,
            confidence: factor.confidence,
            weight: factor.weighted_score.abs(),
            long_support: if factor.direction == Direction::Bull {
                factor.weighted_score.max(0.0)
            } else {
                0.0
            },
            short_support: if factor.direction == Direction::Bear {
                factor.weighted_score.abs()
            } else {
                0.0
            },
            uncertainty_contribution: factor.uncertainty_contribution,
        });
    }

    FeedbackRecord {
        timestamp,
        symbol: symbol.to_string(),
        source: source.to_string(),
        run_id: None,
        trade_id: None,
        prompt_version: Some(PROMPT_PACK_VERSION.to_string()),
        factor_version: None,
        data_fingerprint: None,
        factors_used,
        model_probabilities_before_trade: ModelProbabilitySnapshot {
            selected_direction: decision.selected_direction,
            selected_probability: decision.selected_win_probability,
            long_score: decision.long_score,
            short_score: decision.short_score,
            win_prob_long: decision.win_prob_long,
            win_prob_short: decision.win_prob_short,
            uncertainty: factor_diagnostics.uncertainty,
        },
        realized_outcome,
        pnl,
        regime_at_entry,
    }
}

fn enrich_feedback_record(
    mut feedback: FeedbackRecord,
    run_id: &str,
    trade_id: impl Into<String>,
    learning_state: &LearningState,
    data_fingerprint: &str,
) -> FeedbackRecord {
    if feedback.run_id.is_none() {
        feedback.run_id = Some(run_id.to_string());
    }
    if feedback.trade_id.is_none() {
        feedback.trade_id = Some(trade_id.into());
    }
    if feedback.prompt_version.is_none() {
        feedback.prompt_version = Some(PROMPT_PACK_VERSION.to_string());
    }
    if feedback.factor_version.is_none() {
        feedback.factor_version = Some(factor_version(learning_state));
    }
    if feedback.data_fingerprint.is_none() {
        feedback.data_fingerprint = Some(data_fingerprint.to_string());
    }
    feedback
}

fn build_analyze_agent_prompts(
    symbol: &str,
    decision: &ProbabilisticDecisionSnapshot,
    factor_diagnostics: &FactorDiagnostics,
    pre_bayes_evidence_filter: &PreBayesEvidenceFilter,
    factor_ranking: &[PersistedFactorRanking],
    factor_iteration_queue: &[FactorIterationPrompt],
    feedback_history_summary: &FeedbackHistorySummary,
    trade_plan: &TradePlan,
    dataset_comparability: &DatasetComparability,
    decision_hint: &str,
    multi_timeframe_summary: &[String],
) -> AgentPromptPack {
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
        AgentPrompt::new(
            "pre_bayes_evidence_review",
            "pre_bayes_filter",
            "high",
            "Review whether raw regime/liquidity/factor evidence should be passed to BBN directly or neutralized first.",
            "You are the pre-bayes evidence gate. Compare raw labels with filtered labels, conflicts, and evidence quality before trusting the downstream Bayesian inference.",
            format!(
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
            vec![
                "State explicitly whether the filtered evidence should be trusted as hard evidence or soft evidence".to_string(),
                "If regime and factor alignment conflict, prefer neutralization over direct Bayesian commitment".to_string(),
            ],
            vec![
                "src/main.rs".to_string(),
                "src/bbn/trading/update.rs".to_string(),
                "src/factor_lab/engine.rs".to_string(),
            ],
        ),
    );
    if pre_bayes_evidence_filter.uses_soft_evidence {
        pack.prompts.insert(
            2,
            AgentPrompt::new(
                "pre_bayes_soft_evidence_review",
                "pre_bayes_soft_evidence",
                "high",
                "Review whether soft evidence diverges materially from filtered labels before trusting BBN output.",
                "You are the pre-bayes soft-evidence reviewer. Compare filtered states with soft evidence distributions and explain whether the Bayesian layer is receiving stable or ambiguous evidence.",
                format!(
                    "Symbol={} filtered_assignments={:?} soft_market_regime={:?} soft_liquidity_context={:?} soft_factor_alignment={:?} soft_factor_uncertainty={:?} soft_mtf_resonance={:?}",
                    symbol,
                    pre_bayes_evidence_filter.evidence_assignments,
                    pre_bayes_evidence_filter.soft_market_regime_distribution,
                    pre_bayes_evidence_filter.soft_liquidity_context_distribution,
                    pre_bayes_evidence_filter.soft_factor_alignment_distribution,
                    pre_bayes_evidence_filter.soft_factor_uncertainty_distribution,
                    pre_bayes_evidence_filter.soft_multi_timeframe_resonance_distribution
                ),
                vec![
                    "Call out when the dominant soft-evidence state diverges from the filtered hard label".to_string(),
                    "If entropy is high, prefer observe-only or neutralized review over confident Bayesian commitment".to_string(),
                ],
                vec![
                    "src/main.rs".to_string(),
                    "src/bbn/node.rs".to_string(),
                    "src/bbn/trading/update.rs".to_string(),
                ],
            ),
        );
    }
    pack.prompts.insert(
        if pre_bayes_evidence_filter.uses_soft_evidence { 3 } else { 2 },
        AgentPrompt::new(
            "analysis_market_review",
            "market_analysis",
            "high",
            "Review the current market conclusion and identify whether factor evidence supports the selected direction.",
            "You are the market-review agent. Challenge the current trade direction using price-action evidence, factor diagnostics, and uncertainty. Do not change factor definitions here; decide whether the current conclusion is supported or should be downgraded.",
            format!(
                "Symbol={} decision_hint={} dataset_comparability={{comparable:{}, reason:{}}} multi_timeframe_summary={:?} selected_direction={:?} selected_score={:.3} selected_win_probability={:.3} trade_direction={:?} posterior={:.3} factor_alignment={} factor_uncertainty={} long_support={:.3} short_support={:.3} uncertainty={:.3} bullish_factors={:?} bearish_factors={:?}",
                symbol,
                decision_hint,
                dataset_comparability.comparable,
                dataset_comparability.reason,
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
            vec![
                "Explicitly name which factors support long, which support short, and which only add uncertainty".to_string(),
                "If uncertainty is high, recommend what evidence the next agent should wait for".to_string(),
            ],
            vec![
                "src/main.rs".to_string(),
                "src/factor_lab/engine.rs".to_string(),
                "src/bbn/trading/topology.rs".to_string(),
            ],
        ),
    );
    pack
}

fn build_backtest_agent_prompts(
    symbol: &str,
    factor_ranking: &[PersistedFactorRanking],
    factor_iteration_queue: &[FactorIterationPrompt],
    feedback_history_summary: &FeedbackHistorySummary,
    total_return: f64,
    trades: usize,
    final_trade_outcome_cpt: &BTreeMap<String, BTreeMap<String, f64>>,
) -> AgentPromptPack {
    let mut pack = factor_iteration_prompt_pack(
        symbol,
        factor_ranking,
        factor_iteration_queue,
        feedback_history_summary,
    );
    pack.workflow = format!(
        "Use backtest performance, updated factor scorecards, and final trade_outcome CPT state to decide the next agent iteration plan for {}.",
        symbol
    );
    pack.prompts.push(AgentPrompt::new(
        "backtest_model_review",
        "backtest_review",
        "high",
        "Review whether factor/BBN updates improved the model or just overfit recent trades.",
        "You are the backtest-review agent. Use the final CPT snapshot, total return, trade count, and factor iteration queue to decide whether the next change should target factor definitions, factor weighting, or BBN evidence mapping.",
        format!(
            "Symbol={} total_return={:.6} trade_count={} factor_iteration_queue={:?} final_trade_outcome_cpt={:?}",
            symbol, total_return, trades, factor_iteration_queue, final_trade_outcome_cpt
        ),
        vec![
            "Prefer factor replacement only when composite score and CPT-adjusted evidence both remain weak".to_string(),
            "If BBN outcome probabilities shifted but factor scores did not improve, review evidence mapping before replacing factors".to_string(),
        ],
        vec![
            "src/main.rs".to_string(),
            "src/factors/weight_updater.rs".to_string(),
            "src/bbn/trading/topology.rs".to_string(),
        ],
    ));
    pack
}

fn analyze_signal_rankings(
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

fn build_analyze_decision_hint(
    dataset_comparability: &DatasetComparability,
    factor_iteration_queue: &[FactorIterationPrompt],
    factor_diagnostics: &FactorDiagnostics,
) -> String {
    if !dataset_comparability.comparable {
        return format!(
            "observe_only_not_comparable_to_last_analyze:{}",
            dataset_comparability.reason
        );
    }
    if factor_diagnostics.uncertainty >= 0.45 {
        return "wait_for_clearer_evidence_due_to_high_uncertainty".to_string();
    }
    if let Some(next) = factor_iteration_queue.first() {
        return format!(
            "market_view_is_comparable_but_factor_backlog_requires_{}:{}",
            next.iteration_action, next.factor_name
        );
    }
    "market_view_comparable_and_factor_stack_stable".to_string()
}

fn family_diffs(
    previous: &[FactorFamilyDecision],
    current: &[FactorFamilyDecision],
) -> Vec<FactorFamilyDiff> {
    let previous_map = previous
        .iter()
        .map(|item| (item.family.clone(), item))
        .collect::<HashMap<_, _>>();
    let mut diffs = current
        .iter()
        .map(|item| {
            let previous = previous_map.get(&item.family).copied();
            FactorFamilyDiff {
                family: item.family.clone(),
                previous_avg_score: previous.map(|entry| entry.avg_score),
                new_avg_score: item.avg_score,
                avg_score_delta: item.avg_score
                    - previous.map(|entry| entry.avg_score).unwrap_or(0.0),
                previous_replacement_count: previous
                    .map(|entry| entry.replacement_candidates.len())
                    .unwrap_or(0),
                new_replacement_count: item.replacement_candidates.len(),
            }
        })
        .collect::<Vec<_>>();
    diffs.sort_by(|a, b| {
        b.avg_score_delta
            .abs()
            .partial_cmp(&a.avg_score_delta.abs())
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    diffs
}

fn family_history_from_runs<I>(runs: I) -> Vec<FactorFamilyHistory>
where
    I: IntoIterator<Item = (String, chrono::DateTime<Utc>, Vec<FactorFamilyDecision>)>,
{
    let runs = runs.into_iter().collect::<Vec<_>>();
    let window_size = family_history_window();
    let mut grouped = BTreeMap::<
        String,
        (
            Vec<String>,
            Vec<chrono::DateTime<Utc>>,
            Vec<f64>,
            Vec<usize>,
        ),
    >::new();
    for (run_id, timestamp, run) in runs.into_iter().rev().take(window_size).rev() {
        for family in run {
            let entry = grouped.entry(family.family.clone()).or_default();
            entry.0.push(run_id.clone());
            entry.1.push(timestamp);
            entry.2.push(family.avg_score);
            entry.3.push(family.replacement_candidates.len());
        }
    }

    grouped
        .into_iter()
        .map(
            |(
                family,
                (recent_run_ids, recent_timestamps, recent_avg_scores, recent_replacement_counts),
            )| {
                let score_trend = trend_label_f64(&recent_avg_scores);
                let replacement_trend = trend_label_usize(&recent_replacement_counts);
                FactorFamilyHistory {
                    family,
                    window_size,
                    recent_run_ids,
                    recent_timestamps,
                    recent_avg_scores,
                    recent_replacement_counts,
                    score_trend,
                    replacement_trend,
                }
            },
        )
        .collect()
}

fn decision_history_summary<I>(runs: I) -> DecisionHistorySummary
where
    I: IntoIterator<Item = (PromotionDecision, RollbackRecommendation)>,
{
    let runs = runs.into_iter().collect::<Vec<_>>();
    let total_runs = runs.len();
    let promotion_approved_runs = runs
        .iter()
        .filter(|(promotion, _)| promotion.approved)
        .count();
    let rollback_recommended_runs = runs
        .iter()
        .filter(|(_, rollback)| rollback.should_rollback)
        .count();
    let latest_promotion_status = runs.last().map(|(promotion, _)| promotion.status.clone());
    let latest_rollback_scope = runs.last().map(|(_, rollback)| rollback.scope.clone());

    DecisionHistorySummary {
        total_runs,
        promotion_approved_runs,
        rollback_recommended_runs,
        latest_promotion_status,
        latest_rollback_scope,
    }
}

#[derive(Debug, Clone)]
enum AnalyzeCommandSource {
    Files {
        data_htf: String,
        data_mtf: String,
        data_ltf: String,
    },
    Live {
        source: LiveDataSourceProvenance,
    },
}

#[derive(Debug, Clone, Default)]
struct CommandContext {
    symbol: String,
    state_dir: String,
    analyze: Option<AnalyzeCommandSource>,
    research_data: Option<String>,
    paired_data: Option<String>,
    update_outcome: Option<String>,
    update_entry_signal: Option<String>,
    update_feedback_file: Option<String>,
    user_data_selection_required: bool,
}

fn shell_quote(value: &str) -> String {
    if value.is_empty() {
        "''".to_string()
    } else if value
        .chars()
        .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '/' | ':' | '.' | '_' | '-'))
    {
        value.to_string()
    } else {
        format!("'{}'", value.replace('\'', "'\"'\"'"))
    }
}

fn recommended_command(
    command: String,
    ready: bool,
    missing_inputs: Vec<String>,
    rationale: impl Into<String>,
) -> RecommendedCommand {
    RecommendedCommand {
        command,
        ready,
        missing_inputs,
        rationale: rationale.into(),
        user_data_selection_required: false,
        user_data_selection_prompt: "user_data_selection_not_required".to_string(),
        recorded_data_paths: Vec::new(),
    }
}

fn user_data_selection_prompt(symbol: &str, data_paths: &[String]) -> String {
    let recorded = if data_paths.is_empty() {
        "recorded_paths=[]".to_string()
    } else {
        format!("recorded_paths={}", data_paths.join(", "))
    };
    format!(
        "Before using historical data for {} again, ask the user which dataset to use. {}",
        symbol, recorded
    )
}

fn render_recommended_command(command: &RecommendedCommand) -> String {
    if command.user_data_selection_required {
        let rendered_command = if command.command.is_empty() {
            "choose historical dataset with user before running command".to_string()
        } else {
            command.command.clone()
        };
        let prompt = if command.user_data_selection_prompt.is_empty() {
            "ask user which historical dataset to use".to_string()
        } else {
            command.user_data_selection_prompt.clone()
        };
        return format!(
            "ask-user: {} | blocked until user_selected_historical_data | then {}",
            prompt, rendered_command
        );
    }
    if command.ready {
        command.command.clone()
    } else if !command.command.is_empty() {
        format!(
            "blocked: {} missing={}",
            command.command,
            command.missing_inputs.join(",")
        )
    } else if !command.rationale.is_empty() {
        format!(
            "blocked: {} missing={}",
            command.rationale,
            command.missing_inputs.join(",")
        )
    } else {
        "blocked".to_string()
    }
}

fn recommended_next_command(
    action_plan: &AgentActionPlan,
    commands: &CommandRecommendations,
) -> String {
    action_plan
        .items
        .iter()
        .max_by(|a, b| {
            action_priority(a)
                .cmp(&action_priority(b))
                .then_with(|| priority_rank(&a.priority).cmp(&priority_rank(&b.priority)))
        })
        .and_then(|item| {
            item.suggested_commands
                .iter()
                .find(|command| {
                    !command.is_empty()
                        && !command.starts_with("blocked:")
                        && !(command.contains('<') && command.contains('>'))
                })
                .cloned()
                .or_else(|| {
                    let command = command_for_stage(&item.stage, commands);
                    command.ready.then(|| command.command.clone())
                })
        })
        .or_else(|| {
            [
                &commands.analyze,
                &commands.research,
                &commands.backtest,
                &commands.update,
            ]
            .into_iter()
            .find(|command| command.ready)
            .map(|command| command.command.clone())
        })
        .unwrap_or_default()
}

fn command_recommendations(context: &CommandContext) -> CommandRecommendations {
    let mut recorded_data_paths = Vec::new();
    if let Some(analyze) = &context.analyze {
        match analyze {
            AnalyzeCommandSource::Files {
                data_htf,
                data_mtf,
                data_ltf,
            } => {
                for path in [data_htf, data_mtf, data_ltf] {
                    if !recorded_data_paths.contains(path) {
                        recorded_data_paths.push(path.clone());
                    }
                }
            }
            AnalyzeCommandSource::Live { source } => {
                for path in [
                    source.persisted_htf_path.clone(),
                    source.persisted_mtf_path.clone(),
                    source.persisted_ltf_path.clone(),
                    source.persisted_spot_path.clone(),
                ]
                .into_iter()
                .flatten()
                {
                    if !recorded_data_paths.contains(&path) {
                        recorded_data_paths.push(path);
                    }
                }
            }
        }
    }
    if let Some(data) = &context.research_data {
        if !recorded_data_paths.contains(data) {
            recorded_data_paths.push(data.clone());
        }
    }
    if let Some(data) = &context.paired_data {
        if !recorded_data_paths.contains(data) {
            recorded_data_paths.push(data.clone());
        }
    }
    let user_prompt = user_data_selection_prompt(&context.symbol, &recorded_data_paths);
    let analyze = match &context.analyze {
        Some(AnalyzeCommandSource::Files {
            data_htf,
            data_mtf,
            data_ltf,
        }) => recommended_command(
            format!(
                "ict-engine analyze --symbol {} --data-htf {} --data-mtf {} --data-ltf {} --state-dir {}",
                shell_quote(&context.symbol),
                shell_quote(data_htf),
                shell_quote(data_mtf),
                shell_quote(data_ltf),
                shell_quote(&context.state_dir)
            ),
            true,
            Vec::new(),
            "replay analyze with the same dataset",
        ),
        Some(AnalyzeCommandSource::Live { source }) => recommended_command(
            format!(
                "ict-engine analyze-live --symbol {} --futures-symbol {} --spot-symbol {} --options-symbol {} --spot-kind {} --futures-backend {} --aux-backend {} --openalice-base-url {} --nofx-base-url {} --state-dir {}",
                shell_quote(&context.symbol),
                shell_quote(&source.futures_symbol),
                shell_quote(&source.spot_symbol),
                shell_quote(&source.options_symbol),
                shell_quote(&source.spot_kind),
                shell_quote(&source.futures_backend),
                shell_quote(&source.aux_backend),
                shell_quote(&source.futures_base_url),
                shell_quote(&source.aux_base_url),
                shell_quote(&context.state_dir)
            ),
            true,
            Vec::new(),
            "replay live analyze with the same provider configuration",
        ),
        None => recommended_command(
            "recommended_command_unavailable".to_string(),
            false,
            vec!["analyze_input_context".to_string()],
            "analyze inputs are not available in this run context",
        ),
    };

    let mut research = if let Some(data) = &context.research_data {
        recommended_command(
            format!(
                "ict-engine factor-research --symbol {} --data {}{} --state-dir {}",
                shell_quote(&context.symbol),
                shell_quote(data),
                context
                    .paired_data
                    .as_ref()
                    .map(|paired| format!(" --paired-data {}", shell_quote(paired)))
                    .unwrap_or_default(),
                shell_quote(&context.state_dir)
            ),
            true,
            Vec::new(),
            "rerun factor research on the same dataset",
        )
    } else {
        recommended_command(
            "recommended_command_unavailable".to_string(),
            false,
            vec!["research_data_path".to_string()],
            "factor research requires a persisted data path",
        )
    };

    let mut backtest = if let Some(data) = &context.research_data {
        recommended_command(
            format!(
                "ict-engine factor-backtest --symbol {} --data {}{} --state-dir {}",
                shell_quote(&context.symbol),
                shell_quote(data),
                context
                    .paired_data
                    .as_ref()
                    .map(|paired| format!(" --paired-data {}", shell_quote(paired)))
                    .unwrap_or_default(),
                shell_quote(&context.state_dir)
            ),
            true,
            Vec::new(),
            "rerun factor backtest on the same dataset",
        )
    } else {
        recommended_command(
            "recommended_command_unavailable".to_string(),
            false,
            vec!["backtest_data_path".to_string()],
            "factor backtest requires a persisted data path",
        )
    };

    if context.user_data_selection_required {
        for command in [&mut research, &mut backtest] {
            command.user_data_selection_required = true;
            command.user_data_selection_prompt = user_prompt.clone();
            command.recorded_data_paths = recorded_data_paths.clone();
            if command.ready {
                command.ready = false;
                command
                    .missing_inputs
                    .push("user_selected_historical_data".to_string());
                command.rationale = format!(
                    "{} User must explicitly choose one of the recorded historical datasets before rerun.",
                    command.rationale
                );
            }
        }
    } else {
        for command in [&mut research, &mut backtest] {
            command.recorded_data_paths = recorded_data_paths.clone();
        }
    }

    let mut update = if let Some(feedback_file) = &context.update_feedback_file {
        let command = format!(
            "ict-engine update --symbol {} --outcome {} --state-dir {}",
            shell_quote(&context.symbol),
            context
                .update_outcome
                .as_deref()
                .unwrap_or("<win|loss|breakeven>"),
            shell_quote(&context.state_dir)
        );
        if context.update_outcome.is_some() {
            recommended_command(
                command,
                true,
                Vec::new(),
                format!(
                    "apply the persisted pending feedback artifact at {}",
                    feedback_file
                ),
            )
        } else {
            recommended_command(
                command,
                false,
                vec!["realized_outcome".to_string()],
                format!(
                    "pending update artifact exists at {} but realized outcome is still missing",
                    feedback_file
                ),
            )
        }
    } else if let Some(outcome) = &context.update_outcome {
        recommended_command(
            format!(
                "ict-engine update --symbol {} --outcome {}{} --state-dir {}",
                shell_quote(&context.symbol),
                shell_quote(outcome),
                context
                    .update_entry_signal
                    .as_ref()
                    .map(|signal| format!(" --entry-signal {}", shell_quote(signal)))
                    .unwrap_or_default(),
                shell_quote(&context.state_dir)
            ),
            true,
            Vec::new(),
            "replay the same realized outcome update",
        )
    } else {
        recommended_command(
            "recommended_command_unavailable".to_string(),
            false,
            vec!["outcome_or_feedback_file".to_string()],
            "update requires a realized outcome or feedback file",
        )
    };

    update.recorded_data_paths = recorded_data_paths.clone();

    CommandRecommendations {
        analyze,
        research,
        backtest,
        update,
    }
}

fn command_for_stage<'a>(
    stage: &str,
    commands: &'a CommandRecommendations,
) -> &'a RecommendedCommand {
    match stage {
        "analyze" | "market_analysis" => &commands.analyze,
        "promotion" | "family_review" => &commands.research,
        "iteration" => &commands.backtest,
        "artifact_consumption" => {
            if commands.update.ready {
                &commands.update
            } else if commands.research.ready {
                &commands.research
            } else {
                &commands.backtest
            }
        }
        "rollback" => {
            if commands.update.ready {
                &commands.update
            } else if commands.research.ready {
                &commands.research
            } else {
                &commands.update
            }
        }
        _ => &commands.analyze,
    }
}

fn workflow_state_from_context(
    decision_hint: &str,
    promotion_decision: &PromotionDecision,
    rollback_recommendation: &RollbackRecommendation,
) -> WorkflowState {
    if rollback_recommendation.should_rollback {
        WorkflowState {
            phase: if rollback_recommendation.scope.contains("artifact")
                || rollback_recommendation
                    .reason
                    .contains("artifact_consumption_validated_regression")
            {
                "artifact_rollback_review".to_string()
            } else {
                "rollback_review".to_string()
            },
            reason: rollback_recommendation.reason.clone(),
        }
    } else if !promotion_decision.approved {
        WorkflowState {
            phase: "research_iteration".to_string(),
            reason: promotion_decision.reason.clone(),
        }
    } else {
        WorkflowState {
            phase: "observe_or_deploy".to_string(),
            reason: decision_hint.to_string(),
        }
    }
}

fn workflow_state_from_pre_bayes_filter(
    base: WorkflowState,
    filter: &PreBayesEvidenceFilter,
) -> WorkflowState {
    match filter.gating_status.as_str() {
        "observe_only" => WorkflowState {
            phase: "pre_bayes_observe_only".to_string(),
            reason: filter.rationale.join(";"),
        },
        "pass_neutralized" => WorkflowState {
            phase: "pre_bayes_neutralized_review".to_string(),
            reason: filter.rationale.join(";"),
        },
        _ => base,
    }
}

fn augment_action_plan_with_pre_bayes_filter(
    action_plan: &mut AgentActionPlan,
    filter: &PreBayesEvidenceFilter,
) {
    if filter.gating_status == "pass_hard" && filter.conflict_flags.is_empty() {
        return;
    }
    action_plan.items.insert(
        0,
        AgentActionItem {
            stage: "analyze".to_string(),
            blocking: filter.gating_status == "observe_only",
            priority: "high".to_string(),
            title: "Review Pre-Bayes Evidence Gate".to_string(),
            rationale: filter.rationale.join(";"),
            expected_output:
                "A pre-Bayes gate review confirming whether evidence should pass hard, pass neutralized, or remain observe-only".to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: "pre_bayes_evidence_filter".to_string(),
                direction: filter.gating_status.clone(),
                rationale: filter.rationale.join(";"),
            }],
            suggested_files: vec![
                "src/main.rs".to_string(),
                "src/factor_lab/engine.rs".to_string(),
                "src/bbn/trading/update.rs".to_string(),
            ],
            suggested_commands: vec![
                "ict-engine analyze --data-htf <file> --data-mtf <file> --data-ltf <file>"
                    .to_string(),
            ],
        },
    );
}

fn augment_action_plan_with_consumed_pre_bayes_context(
    action_plan: &mut AgentActionPlan,
    filter: &PreBayesEvidenceFilter,
    bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
) {
    let bridge_diff = bridge.map(pre_bayes_entry_quality_bridge_diff);
    action_plan.items.insert(
        0,
        AgentActionItem {
            stage: "update".to_string(),
            blocking: filter.gating_status == "observe_only" || filter.uses_soft_evidence,
            priority: "high".to_string(),
            title: "Review Consumed Pre-Bayes".to_string(),
            rationale: format!(
                "consumed_gate_status={} consumed_quality={:.3} consumed_bridge_selected_entry_quality={:?}",
                filter.gating_status,
                filter.evidence_quality_score,
                bridge_diff
                    .as_ref()
                    .and_then(|diff| diff.selected_entry_quality.clone())
            ),
            expected_output:
                "A feedback note that judges whether the realized outcome confirms or invalidates the consumed pre-bayes gate and bridge".to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: "consumed_pre_bayes_context".to_string(),
                direction: "review_against_realized_outcome".to_string(),
                rationale: filter.rationale.join(";"),
            }],
            suggested_files: vec![
                "src/main.rs".to_string(),
                "src/bbn/trading/update.rs".to_string(),
                "src/state/types.rs".to_string(),
            ],
            suggested_commands: vec!["ict-engine update --feedback-file <file>".to_string()],
        },
    );
}

fn build_agent_context_bundle(
    symbol: &str,
    state_dir: &str,
    workflow_state: &WorkflowState,
    decision_hint: &str,
    recommended_next_command: &str,
    recommended_commands: &CommandRecommendations,
    dataset_comparability: &DatasetComparability,
    factor_iteration_queue: &[FactorIterationPrompt],
    family_outcomes: &[FactorFamilyOutcome],
    pre_bayes_evidence_filter: Option<&PreBayesEvidenceFilter>,
    pre_bayes_entry_quality_bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
    factor_mutation_evaluation: Option<&FactorMutationEvaluation>,
    artifact_decision_summary: Option<&ict_engine::state::ArtifactDecisionSummary>,
) -> AgentContextBundle {
    let pre_bayes_gate_status = pre_bayes_evidence_filter
        .map(|filter| filter.gating_status.clone())
        .unwrap_or_default();
    let pre_bayes_uses_soft_evidence = pre_bayes_evidence_filter
        .map(|filter| filter.uses_soft_evidence)
        .unwrap_or(false);
    let pre_bayes_evidence_quality_score = pre_bayes_evidence_filter
        .map(|filter| filter.evidence_quality_score)
        .unwrap_or_default();
    let pre_bayes_conflict_flags = pre_bayes_evidence_filter
        .map(|filter| filter.conflict_flags.clone())
        .unwrap_or_default();
    let pre_bayes_filtered_assignments = pre_bayes_evidence_filter
        .map(|filter| filter.evidence_assignments.clone())
        .unwrap_or_default();
    let pre_bayes_soft_evidence = pre_bayes_evidence_filter
        .map(|filter| {
            BTreeMap::from([
                (
                    "market_regime".to_string(),
                    filter.soft_market_regime_distribution.clone(),
                ),
                (
                    "liquidity_context".to_string(),
                    filter.soft_liquidity_context_distribution.clone(),
                ),
                (
                    "factor_alignment".to_string(),
                    filter.soft_factor_alignment_distribution.clone(),
                ),
                (
                    "factor_uncertainty".to_string(),
                    filter.soft_factor_uncertainty_distribution.clone(),
                ),
                (
                    "multi_timeframe_resonance".to_string(),
                    filter.soft_multi_timeframe_resonance_distribution.clone(),
                ),
            ])
        })
        .unwrap_or_default();
    let pre_bayes_policy_version = pre_bayes_evidence_filter
        .map(|filter| filter.policy.version.clone())
        .unwrap_or_default();
    let pre_bayes_multi_timeframe_direction_bias = pre_bayes_evidence_filter
        .map(|filter| filter.filtered_multi_timeframe_direction_bias.clone())
        .unwrap_or_default();
    let pre_bayes_multi_timeframe_alignment_score = pre_bayes_evidence_filter
        .and_then(|filter| filter.filtered_multi_timeframe_alignment_score);
    let pre_bayes_multi_timeframe_entry_alignment_score = pre_bayes_evidence_filter
        .and_then(|filter| filter.filtered_multi_timeframe_entry_alignment_score);
    let pre_bayes_soft_evidence_diff = pre_bayes_evidence_filter
        .map(pre_bayes_soft_evidence_diff)
        .unwrap_or_default();
    let pre_bayes_entry_quality_bridge_diff_summary =
        pre_bayes_entry_quality_bridge.map(pre_bayes_entry_quality_bridge_diff);
    let pre_bayes_entry_quality_bridge_summary = pre_bayes_entry_quality_bridge
        .map(|bridge| {
            let bridge_diff = pre_bayes_entry_quality_bridge_diff(bridge);
            let mut summary = bridge.rationale.clone();
            summary.push(format!(
                "long_signal_probability={:.3} short_signal_probability={:.3}",
                bridge.long_signal_probability, bridge.short_signal_probability
            ));
            summary.push(format!(
                "selected_entry_quality={:?} selected_probability={:.3} probability_gap={:.3}",
                bridge_diff.selected_entry_quality,
                bridge_diff.selected_entry_quality_probability,
                bridge_diff.long_short_signal_probability_gap
            ));
            summary.push(format!(
                "multi_timeframe_direction_bias={} multi_timeframe_alignment_score={:.3} multi_timeframe_entry_alignment_score={:.3}",
                bridge_diff.multi_timeframe_direction_bias,
                bridge_diff.multi_timeframe_alignment_score.unwrap_or_default(),
                bridge_diff
                    .multi_timeframe_entry_alignment_score
                    .unwrap_or_default()
            ));
            summary
        })
        .unwrap_or_default();
    let factor_mutation_priority_markets = factor_mutation_evaluation
        .map(factor_mutation_priority_markets)
        .unwrap_or_default();
    let factor_mutation_priority_reasons = factor_mutation_evaluation
        .map(factor_mutation_priority_reasons)
        .unwrap_or_default();
    let factor_mutation_recommended_focus = factor_mutation_evaluation
        .map(factor_mutation_recommended_focus)
        .unwrap_or_default();
    let factor_mutation_direction_hints = factor_mutation_evaluation
        .map(factor_mutation_direction_hint_summary)
        .unwrap_or_default();
    let factor_mutation_step_size_hints = factor_mutation_evaluation
        .map(factor_mutation_step_size_hint_summary)
        .unwrap_or_default();
    let artifact_gate_status = artifact_decision_summary
        .map(|summary| summary.consumed_trend_status.clone())
        .unwrap_or_default();
    let artifact_gate_reason = artifact_decision_summary
        .map(|summary| summary.consumed_trend_reason.clone())
        .unwrap_or_default();
    let artifact_gate_targets = artifact_decision_summary
        .map(|summary| summary.consumed_target_kinds.clone())
        .unwrap_or_default();
    AgentContextBundle {
        workflow_state: workflow_state.clone(),
        decision_hint: decision_hint.to_string(),
        recommended_next_command: recommended_next_command.to_string(),
        recommended_commands: recommended_commands.clone(),
        family_history_window: family_history_window(),
        comparable_to_last_run: dataset_comparability.comparable,
        pre_bayes_gate_status,
        pre_bayes_uses_soft_evidence,
        pre_bayes_evidence_quality_score,
        pre_bayes_conflict_flags,
        pre_bayes_filtered_assignments,
        pre_bayes_soft_evidence,
        pre_bayes_policy_version,
        pre_bayes_multi_timeframe_direction_bias,
        pre_bayes_multi_timeframe_alignment_score,
        pre_bayes_multi_timeframe_entry_alignment_score,
        pre_bayes_entry_quality_bridge_summary,
        pre_bayes_soft_evidence_diff,
        pre_bayes_entry_quality_bridge_diff: pre_bayes_entry_quality_bridge_diff_summary,
        factor_mutation_evaluation: factor_mutation_evaluation.cloned(),
        factor_mutation_priority_markets,
        factor_mutation_priority_reasons,
        factor_mutation_recommended_focus,
        factor_mutation_direction_hints,
        factor_mutation_step_size_hints,
        multi_timeframe_summary: Vec::new(),
        artifact_consumed_gate_status: artifact_gate_status,
        artifact_consumed_gate_reason: artifact_gate_reason,
        artifact_consumed_gate_targets: artifact_gate_targets,
        top_factor_actions: factor_iteration_queue
            .iter()
            .take(3)
            .map(|item| {
                format!(
                    "{}:{}:{:.2}",
                    item.factor_name, item.iteration_action, item.composite_score
                )
            })
            .collect(),
        family_actions: family_outcomes
            .iter()
            .map(|item| {
                format!(
                    "{}:{}:{}",
                    item.family, item.promotion_decision.status, item.rollback_recommendation.scope
                )
            })
            .collect(),
        stage_views: build_stage_views(
            symbol,
            state_dir,
            recommended_commands,
            factor_iteration_queue,
            family_outcomes,
            pre_bayes_evidence_filter,
            artifact_decision_summary,
        ),
    }
}

fn build_agent_context_bundle_minimal(bundle: &AgentContextBundle) -> AgentContextBundleMinimal {
    AgentContextBundleMinimal {
        workflow_phase: bundle.workflow_state.phase.clone(),
        recommended_next_command: bundle.recommended_next_command.clone(),
        family_history_window: bundle.family_history_window,
        comparable_to_last_run: bundle.comparable_to_last_run,
        pre_bayes_gate_status: bundle.pre_bayes_gate_status.clone(),
        pre_bayes_uses_soft_evidence: bundle.pre_bayes_uses_soft_evidence,
        pre_bayes_policy_version: bundle.pre_bayes_policy_version.clone(),
        pre_bayes_soft_evidence_divergence_count: bundle
            .pre_bayes_soft_evidence_diff
            .iter()
            .filter(|item| item.diverges_from_filtered_state)
            .count(),
        pre_bayes_bridge_selected_entry_quality: bundle
            .pre_bayes_entry_quality_bridge_diff
            .as_ref()
            .and_then(|diff| diff.selected_entry_quality.clone())
            .unwrap_or_default(),
        factor_mutation_acceptance_status: bundle
            .factor_mutation_evaluation
            .as_ref()
            .map(|evaluation| {
                if evaluation.accepted {
                    "accepted".to_string()
                } else {
                    "rejected".to_string()
                }
            })
            .unwrap_or_default(),
        factor_mutation_failure_tags: bundle
            .factor_mutation_evaluation
            .as_ref()
            .map(|evaluation| evaluation.failure_tags.clone())
            .unwrap_or_default(),
        factor_mutation_priority_markets: bundle.factor_mutation_priority_markets.clone(),
        factor_mutation_priority_reasons: bundle.factor_mutation_priority_reasons.clone(),
        factor_mutation_direction_hints: bundle.factor_mutation_direction_hints.clone(),
        factor_mutation_step_size_hints: bundle.factor_mutation_step_size_hints.clone(),
        multi_timeframe_summary: bundle.multi_timeframe_summary.clone(),
        artifact_consumed_gate_status: bundle.artifact_consumed_gate_status.clone(),
        top_factor_actions: bundle.top_factor_actions.clone(),
        stage_views: bundle
            .stage_views
            .iter()
            .map(|view| StageAgentContextMinimal {
                stage: view.stage.clone(),
                recommended_command: view.recommended_command.clone(),
                gate_status: view.gate_status.clone(),
            })
            .collect(),
    }
}

fn build_stage_views(
    symbol: &str,
    state_dir: &str,
    recommended_commands: &CommandRecommendations,
    factor_iteration_queue: &[FactorIterationPrompt],
    family_outcomes: &[FactorFamilyOutcome],
    pre_bayes_evidence_filter: Option<&PreBayesEvidenceFilter>,
    artifact_decision_summary: Option<&ict_engine::state::ArtifactDecisionSummary>,
) -> Vec<StageAgentContext> {
    let pre_bayes_gate_status = pre_bayes_evidence_filter
        .map(|filter| filter.gating_status.clone())
        .unwrap_or_default();
    let pre_bayes_gate_reason = pre_bayes_evidence_filter
        .map(|filter| filter.rationale.join(";"))
        .unwrap_or_default();
    let artifact_gate_status = artifact_decision_summary
        .map(|summary| summary.consumed_trend_status.clone())
        .unwrap_or_default();
    let artifact_gate_reason = artifact_decision_summary
        .map(|summary| summary.consumed_trend_reason.clone())
        .unwrap_or_default();
    let mut views = vec![
        StageAgentContext {
            stage: "analyze".to_string(),
            blocking_items: 0,
            recommended_command: render_recommended_command(&recommended_commands.analyze),
            actions: if recommended_commands.analyze.ready {
                vec!["observe current market state".to_string()]
            } else {
                vec![format!(
                    "blocked_by:{}",
                    recommended_commands.analyze.missing_inputs.join(",")
                )]
            },
            gate_status: pre_bayes_gate_status.clone(),
            gate_reason: pre_bayes_gate_reason.clone(),
        },
        StageAgentContext {
            stage: "research".to_string(),
            blocking_items: family_outcomes
                .iter()
                .filter(|family| !family.promotion_decision.approved)
                .count(),
            recommended_command: render_recommended_command(&recommended_commands.research),
            actions: if recommended_commands.research.ready {
                family_outcomes
                    .iter()
                    .filter(|family| !family.promotion_decision.approved)
                    .map(|family| {
                        format!(
                            "family:{} promotion={}",
                            family.family, family.promotion_decision.status
                        )
                    })
                    .collect()
            } else {
                vec![format!(
                    "blocked_by:{}",
                    recommended_commands.research.missing_inputs.join(",")
                )]
            },
            gate_status: artifact_gate_status.clone(),
            gate_reason: artifact_gate_reason.clone(),
        },
        StageAgentContext {
            stage: "backtest".to_string(),
            blocking_items: factor_iteration_queue
                .iter()
                .filter(|item| item.iteration_action == "replace")
                .count(),
            recommended_command: render_recommended_command(&recommended_commands.backtest),
            actions: if recommended_commands.backtest.ready {
                factor_iteration_queue
                    .iter()
                    .take(3)
                    .map(|item| format!("{}:{}", item.factor_name, item.iteration_action))
                    .collect()
            } else {
                vec![format!(
                    "blocked_by:{}",
                    recommended_commands.backtest.missing_inputs.join(",")
                )]
            },
            gate_status: artifact_gate_status.clone(),
            gate_reason: artifact_gate_reason.clone(),
        },
        StageAgentContext {
            stage: "update".to_string(),
            blocking_items: family_outcomes
                .iter()
                .filter(|family| family.rollback_recommendation.should_rollback)
                .count(),
            recommended_command: render_recommended_command(&recommended_commands.update),
            actions: if recommended_commands.update.ready {
                family_outcomes
                    .iter()
                    .filter(|family| family.rollback_recommendation.should_rollback)
                    .map(|family| format!("family:{} rollback", family.family))
                    .collect()
            } else {
                vec![format!(
                    "blocked_by:{}",
                    recommended_commands.update.missing_inputs.join(",")
                )]
            },
            gate_status: artifact_gate_status.clone(),
            gate_reason: artifact_gate_reason.clone(),
        },
    ];
    if !artifact_gate_status.is_empty() {
        views.push(StageAgentContext {
            stage: "artifact_consumption".to_string(),
            blocking_items: usize::from(artifact_gate_status == "validated_regressing"),
            recommended_command: format!(
                "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-consumed-gate",
                shell_quote(symbol),
                shell_quote(state_dir)
            ),
            actions: if artifact_gate_reason.is_empty() {
                Vec::new()
            } else {
                vec![artifact_gate_reason.clone()]
            },
            gate_status: artifact_gate_status,
            gate_reason: artifact_gate_reason,
        });
    }
    views
}

fn build_agent_action_plan(
    decision_hint: &str,
    promotion_decision: &PromotionDecision,
    rollback_recommendation: &RollbackRecommendation,
    factor_iteration_queue: &[FactorIterationPrompt],
    family_outcomes: &[FactorFamilyOutcome],
) -> AgentActionPlan {
    let mut items = Vec::new();

    if rollback_recommendation.should_rollback {
        items.push(AgentActionItem {
            stage: "rollback".to_string(),
            blocking: true,
            priority: "high".to_string(),
            title: "Review Rollback".to_string(),
            rationale: rollback_recommendation.reason.clone(),
            expected_output:
                "Updated rollback assessment with confirmed scope and impacted factors".to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: "rollback_recommendation".to_string(),
                direction: "confirm_or_narrow_scope".to_string(),
                rationale: rollback_recommendation.reason.clone(),
            }],
            suggested_files: vec![
                "src/main.rs".to_string(),
                "src/factors/weight_updater.rs".to_string(),
            ],
            suggested_commands: vec!["ict-engine update --feedback-file <file>".to_string()],
        });
    }

    if !promotion_decision.approved {
        items.push(AgentActionItem {
            stage: "promotion".to_string(),
            blocking: true,
            priority: "high".to_string(),
            title: "Block Promotion".to_string(),
            rationale: promotion_decision.reason.clone(),
            expected_output: "Promotion decision resolved with explicit hold or approval rationale"
                .to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: "promotion_decision".to_string(),
                direction: "hold_until_thresholds_met".to_string(),
                rationale: promotion_decision.reason.clone(),
            }],
            suggested_files: vec![
                "src/state/types.rs".to_string(),
                "src/agent/prompts.rs".to_string(),
            ],
            suggested_commands: vec!["ict-engine factor-research --data <file>".to_string()],
        });
    }

    if let Some(next) = factor_iteration_queue.first() {
        items.push(AgentActionItem {
            stage: "iteration".to_string(),
            blocking: false,
            priority: "medium".to_string(),
            title: format!(
                "{} {}",
                next.iteration_action.to_uppercase(),
                next.factor_name
            ),
            rationale: next.prompt.clone(),
            expected_output: "A revised factor implementation or parameter set benchmarked against the current baseline".to_string(),
            expected_state_changes: vec![ExpectedStateChange {
                target: format!("factor:{}", next.factor_name),
                direction: next.iteration_action.clone(),
                rationale: next.prompt.clone(),
            }],
            suggested_files: vec![
                "src/factor_lab/factor_definition.rs".to_string(),
                "src/factors/registry.rs".to_string(),
            ],
            suggested_commands: vec!["ict-engine factor-backtest --data <file>".to_string()],
        });
    }

    for family in family_outcomes.iter().take(2) {
        if family.rollback_recommendation.should_rollback || !family.promotion_decision.approved {
            items.push(AgentActionItem {
                stage: "family_review".to_string(),
                blocking: false,
                priority: "medium".to_string(),
                title: format!("Family Review {}", family.family),
                rationale: if family.rollback_recommendation.should_rollback {
                    family.rollback_recommendation.reason.clone()
                } else {
                    family.promotion_decision.reason.clone()
                },
                expected_output: format!(
                    "A family-level decision note covering whether {} should be tuned, replaced, or held",
                    family.family
                ),
                expected_state_changes: vec![ExpectedStateChange {
                    target: format!("family:{}", family.family),
                    direction: if family.rollback_recommendation.should_rollback {
                        "review_for_rollback".to_string()
                    } else {
                        family.promotion_decision.status.clone()
                    },
                    rationale: if family.rollback_recommendation.should_rollback {
                        family.rollback_recommendation.reason.clone()
                    } else {
                        family.promotion_decision.reason.clone()
                    },
                }],
                suggested_files: vec![
                    "src/factor_lab/factor_definition.rs".to_string(),
                    "src/factors/weight_updater.rs".to_string(),
                ],
                suggested_commands: vec!["ict-engine factor-research --data <file>".to_string()],
            });
        }
    }

    AgentActionPlan {
        summary: decision_hint.to_string(),
        items,
    }
}

fn concretize_action_plan_commands(
    action_plan: &mut AgentActionPlan,
    recommended_commands: &CommandRecommendations,
) {
    for item in &mut action_plan.items {
        let rendered =
            render_recommended_command(command_for_stage(&item.stage, recommended_commands));
        let has_template = item
            .suggested_commands
            .iter()
            .any(|command| command.contains('<') && command.contains('>'));
        if has_template {
            item.suggested_commands
                .retain(|command| !(command.contains('<') && command.contains('>')));
        }
        if !rendered.is_empty()
            && !item
                .suggested_commands
                .iter()
                .any(|command| command == &rendered)
        {
            item.suggested_commands.insert(0, rendered);
        }
    }
}

fn artifact_trend_summaries_for_symbol(
    state_dir: &str,
    symbol: &str,
) -> Result<(
    Vec<ict_engine::state::ArtifactFactorTrendSummary>,
    Vec<ict_engine::state::ArtifactFamilyTrendSummary>,
)> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    Ok((
        build_artifact_factor_trends(&ledger, &None, &None, &None),
        build_artifact_family_trends(&ledger, &None, &None, &None),
    ))
}

fn artifact_trend_summaries_from_ledger(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> (
    Vec<ict_engine::state::ArtifactFactorTrendSummary>,
    Vec<ict_engine::state::ArtifactFamilyTrendSummary>,
) {
    (
        build_artifact_factor_trends(artifact_ledger, &None, &None, &None),
        build_artifact_family_trends(artifact_ledger, &None, &None, &None),
    )
}

fn artifact_decision_summary_for_symbol(
    state_dir: &str,
    symbol: &str,
) -> Result<ict_engine::state::ArtifactDecisionSummary> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    Ok(artifact_decision_summary_from_ledger(&ledger))
}

fn artifact_decision_summary_from_ledger(
    artifact_ledger: &[ArtifactLedgerEntry],
) -> ict_engine::state::ArtifactDecisionSummary {
    let actionable_artifacts = artifact_ledger
        .iter()
        .filter(|entry| entry.actionable && entry.consumed_by_update_run_id.is_none())
        .cloned()
        .collect::<Vec<_>>();
    let latest_promotable_artifact = artifact_ledger
        .iter()
        .filter(|entry| entry.promote_candidate && entry.consumed_by_update_run_id.is_none())
        .max_by_key(|entry| artifact_generated_recency_key(entry))
        .cloned();
    let lineage = build_artifact_lineage_summaries(artifact_ledger);
    let (factor_trends, family_trends) = artifact_trend_summaries_from_ledger(artifact_ledger);
    let consumed_impact_summary = build_artifact_consumed_impact_summary(artifact_ledger);
    artifact_decision_summary_from_trends(
        &actionable_artifacts,
        latest_promotable_artifact.as_ref(),
        &lineage,
        &factor_trends,
        &family_trends,
        &consumed_impact_summary,
    )
}

fn artifact_rule_break_effects_for_symbol(
    state_dir: &str,
    symbol: &str,
) -> Result<Vec<ict_engine::state::ArtifactRuleBreakEffect>> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    Ok(build_artifact_rule_break_effects(&ledger))
}

fn artifact_consumed_impact_summary_for_symbol(
    state_dir: &str,
    symbol: &str,
) -> Result<ict_engine::state::ArtifactConsumedImpactSummary> {
    let ledger = load_artifact_ledger(state_dir, symbol)?;
    Ok(build_artifact_consumed_impact_summary(&ledger))
}

fn augment_action_plan_with_artifact_trends(
    action_plan: &mut AgentActionPlan,
    symbol: &str,
    state_dir: &str,
    factor_trends: &[ict_engine::state::ArtifactFactorTrendSummary],
    family_trends: &[ict_engine::state::ArtifactFamilyTrendSummary],
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) {
    let mut seen_titles = action_plan
        .items
        .iter()
        .map(|item| item.title.clone())
        .collect::<std::collections::BTreeSet<_>>();

    for trend in factor_trends.iter().take(2) {
        if trend.decision_status == "observe" {
            continue;
        }
        let title = format!("Artifact Factor {}", trend.factor_name);
        if !seen_titles.insert(title.clone()) {
            continue;
        }
        action_plan.items.push(AgentActionItem {
            stage: "artifact_factor_review".to_string(),
            blocking: false,
            priority: if trend.rollback_link_status != "none" {
                "high".to_string()
            } else {
                "medium".to_string()
            },
            title,
            rationale: trend.decision_reason.clone(),
            expected_output: format!(
                "Factor-level artifact review for {} with explicit keep/tune/rollback conclusion",
                trend.factor_name
            ),
            expected_state_changes: vec![ExpectedStateChange {
                target: format!("artifact_factor:{}", trend.factor_name),
                direction: trend.decision_status.clone(),
                rationale: trend.decision_reason.clone(),
            }],
            suggested_files: vec![
                "src/state/types.rs".to_string(),
                "src/factors/weight_updater.rs".to_string(),
            ],
            suggested_commands: vec![
                format!(
                    "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-factor-trends",
                    symbol, state_dir
                ),
                format!(
                    "ict-engine artifact-status --symbol {} --state-dir {} --kind pending_update --sort-by improvement --limit 5",
                    symbol, state_dir
                ),
            ],
        });
    }

    for trend in family_trends.iter().take(2) {
        if trend.decision_status == "observe" {
            continue;
        }
        let title = format!("Artifact Family {}", trend.family);
        if !seen_titles.insert(title.clone()) {
            continue;
        }
        action_plan.items.push(AgentActionItem {
            stage: "artifact_family_review".to_string(),
            blocking: false,
            priority: if trend.rollback_link_status != "none" {
                "high".to_string()
            } else {
                "medium".to_string()
            },
            title,
            rationale: trend.decision_reason.clone(),
            expected_output: format!(
                "Family-level artifact review for {} with promotion/rollback linkage",
                trend.family
            ),
            expected_state_changes: vec![ExpectedStateChange {
                target: format!("artifact_family:{}", trend.family),
                direction: trend.decision_status.clone(),
                rationale: trend.decision_reason.clone(),
            }],
            suggested_files: vec![
                "src/state/types.rs".to_string(),
                "src/factor_lab/factor_definition.rs".to_string(),
            ],
            suggested_commands: vec![
                format!(
                    "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-family-trends",
                    symbol, state_dir
                ),
                format!(
                    "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-family-rule-break-impacts",
                    symbol, state_dir
                ),
            ],
        });
    }

    let (consumed_trend_status, consumed_trend_reason, consumed_target_kinds) =
        artifact_consumed_trend_signal(consumed_impact_summary);
    if matches!(
        consumed_trend_status.as_str(),
        "validated_improving" | "validated_regressing"
    ) {
        let title = "Artifact Consumption Validation".to_string();
        if seen_titles.insert(title.clone()) {
            let mut expected_state_changes = vec![ExpectedStateChange {
                target: "artifact_consumption".to_string(),
                direction: consumed_trend_status.clone(),
                rationale: consumed_trend_reason.clone(),
            }];
            expected_state_changes.extend(consumed_target_kinds.iter().map(|kind| {
                ExpectedStateChange {
                    target: format!("artifact_kind:{}", kind),
                    direction: consumed_trend_status.clone(),
                    rationale: consumed_trend_reason.clone(),
                }
            }));
            action_plan.items.push(AgentActionItem {
                stage: "artifact_consumption_review".to_string(),
                blocking: consumed_trend_status == "validated_regressing",
                priority: if consumed_trend_status == "validated_regressing" {
                    "high".to_string()
                } else {
                    "medium".to_string()
                },
                title,
                rationale: consumed_trend_reason,
                expected_output:
                    "A consumption-validation note covering whether realized artifact use is improving or regressing".to_string(),
                expected_state_changes,
                suggested_files: vec![
                    "src/main.rs".to_string(),
                    "src/state/types.rs".to_string(),
                    "src/factors/weight_updater.rs".to_string(),
                ],
                suggested_commands: vec![
                    format!(
                        "ict-engine workflow-status --symbol {} --state-dir {} --phase artifact-impact-consumed-trend",
                        symbol, state_dir
                    ),
                    format!(
                        "ict-engine artifact-status --symbol {} --state-dir {} --consumed-only --sort-by regression --limit 5",
                        symbol, state_dir
                    ),
                ],
            });
        }
    }
}

fn artifact_action_summary(
    factor_trends: &[ict_engine::state::ArtifactFactorTrendSummary],
    family_trends: &[ict_engine::state::ArtifactFamilyTrendSummary],
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> Vec<String> {
    let mut summary = Vec::new();
    summary.extend(
        factor_trends
            .iter()
            .filter(|trend| trend.decision_status != "observe")
            .take(3)
            .map(|trend| {
                format!(
                    "factor:{} status={} reason={}",
                    trend.factor_name, trend.decision_status, trend.decision_reason
                )
            }),
    );
    summary.extend(
        family_trends
            .iter()
            .filter(|trend| trend.decision_status != "observe")
            .take(3)
            .map(|trend| {
                format!(
                    "family:{} status={} reason={}",
                    trend.family, trend.decision_status, trend.decision_reason
                )
            }),
    );
    let (consumed_trend_status, consumed_trend_reason, _) =
        artifact_consumed_trend_signal(consumed_impact_summary);
    if matches!(
        consumed_trend_status.as_str(),
        "validated_improving" | "validated_regressing"
    ) {
        summary.push(format!(
            "consumed:{} reason={}",
            consumed_trend_status, consumed_trend_reason
        ));
    }
    summary
}

fn artifact_decision_summary_from_snapshot(
    snapshot: &WorkflowSnapshot,
    artifact_action_summary: &[String],
) -> ict_engine::state::ArtifactDecisionSummary {
    let (consumed_trend_status, consumed_trend_reason, consumed_target_kinds) =
        artifact_consumed_trend_signal(&snapshot.artifact_consumed_impact_summary);
    let mut promotion_strength = if snapshot.latest_promotable_artifact.is_some()
        && snapshot.actionable_artifacts.len() >= 2
    {
        "high".to_string()
    } else if snapshot.latest_promotable_artifact.is_some() {
        "medium".to_string()
    } else {
        "low".to_string()
    };
    let mut rollback_strength = if snapshot
        .artifact_factor_trends
        .iter()
        .any(|trend| trend.rollback_link_status == "rollback_watch")
        || snapshot
            .artifact_family_trends
            .iter()
            .any(|trend| trend.rollback_link_status == "rollback_watch")
    {
        "high".to_string()
    } else {
        "low".to_string()
    };
    match consumed_trend_status.as_str() {
        "validated_improving" if snapshot.latest_promotable_artifact.is_some() => {
            promotion_strength = "high".to_string();
        }
        "validated_regressing" => {
            promotion_strength = "low".to_string();
            rollback_strength = "high".to_string();
        }
        _ => {}
    }
    ict_engine::state::ArtifactDecisionSummary {
        actionable_artifact_count: snapshot.actionable_artifacts.len(),
        latest_promotable_artifact_id: snapshot
            .latest_promotable_artifact
            .as_ref()
            .map(|entry| entry.artifact_id.clone()),
        artifact_rule_break_count: snapshot
            .artifact_lineage_summaries
            .iter()
            .map(|summary| summary.review_rule_break_count)
            .sum(),
        highlighted_actions: artifact_action_summary.to_vec(),
        highlighted_factor_targets: snapshot
            .artifact_factor_trends
            .iter()
            .filter(|trend| trend.decision_status != "observe")
            .map(|trend| trend.factor_name.clone())
            .collect(),
        highlighted_family_targets: snapshot
            .artifact_family_trends
            .iter()
            .filter(|trend| trend.decision_status != "observe")
            .map(|trend| trend.family.clone())
            .collect(),
        promotion_strength,
        rollback_strength,
        consumed_trend_status: consumed_trend_status.clone(),
        consumed_trend_reason: consumed_trend_reason.clone(),
        consumed_target_kinds: consumed_target_kinds.clone(),
        summary: format!(
            "actionable_artifacts={} latest_promotable={:?} rule_breaks={} consumed_trend={}",
            snapshot.actionable_artifacts.len(),
            snapshot
                .latest_promotable_artifact
                .as_ref()
                .map(|entry| entry.artifact_id.clone()),
            snapshot
                .artifact_lineage_summaries
                .iter()
                .map(|summary| summary.review_rule_break_count)
                .sum::<usize>(),
            consumed_trend_status
        ),
    }
}

fn artifact_decision_section_from_parts(
    summary: &ict_engine::state::ArtifactDecisionSummary,
    action_summary: &[String],
    factor_trends: &[ict_engine::state::ArtifactFactorTrendSummary],
    family_trends: &[ict_engine::state::ArtifactFamilyTrendSummary],
    rule_break_effects: &[ict_engine::state::ArtifactRuleBreakEffect],
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> ict_engine::state::ArtifactDecisionSection {
    ict_engine::state::ArtifactDecisionSection {
        summary: summary.clone(),
        action_summary: action_summary.to_vec(),
        top_factor_trends: factor_trends.iter().take(3).cloned().collect(),
        top_family_trends: family_trends.iter().take(3).cloned().collect(),
        top_rule_break_effects: rule_break_effects.iter().take(3).cloned().collect(),
        top_consumed_trend_comparisons: top_consumed_trend_comparisons(consumed_impact_summary),
    }
}

fn artifact_decision_section_from_snapshot(
    snapshot: &WorkflowSnapshot,
) -> ict_engine::state::ArtifactDecisionSection {
    ict_engine::state::ArtifactDecisionSection {
        summary: snapshot.artifact_decision_summary.clone(),
        action_summary: snapshot
            .artifact_decision_summary
            .highlighted_actions
            .clone(),
        top_factor_trends: snapshot
            .artifact_factor_trends
            .iter()
            .take(3)
            .cloned()
            .collect(),
        top_family_trends: snapshot
            .artifact_family_trends
            .iter()
            .take(3)
            .cloned()
            .collect(),
        top_rule_break_effects: snapshot
            .artifact_rule_break_effects
            .iter()
            .take(3)
            .cloned()
            .collect(),
        top_consumed_trend_comparisons: top_consumed_trend_comparisons(
            &snapshot.artifact_consumed_impact_summary,
        ),
    }
}

fn link_artifact_decision_summary_to_decisions(
    artifact_summary: &ict_engine::state::ArtifactDecisionSummary,
    promotion_decision: &mut PromotionDecision,
    rollback_recommendation: &mut RollbackRecommendation,
) {
    let artifact_reason = format!(
        "artifact_actionable_count={} artifact_latest_promotable={:?} artifact_rule_breaks={} artifact_consumed_trend_status={} artifact_consumed_targets={:?}",
        artifact_summary.actionable_artifact_count,
        artifact_summary.latest_promotable_artifact_id,
        artifact_summary.artifact_rule_break_count,
        artifact_summary.consumed_trend_status,
        artifact_summary.consumed_target_kinds
    );
    if !artifact_reason.is_empty() {
        promotion_decision.reason = format!("{}|{}", promotion_decision.reason, artifact_reason);
        rollback_recommendation.reason =
            format!("{}|{}", rollback_recommendation.reason, artifact_reason);
    }
    promotion_decision.reason = format!(
        "{}|artifact_promotion_strength={}",
        promotion_decision.reason, artifact_summary.promotion_strength
    );
    rollback_recommendation.reason = format!(
        "{}|artifact_rollback_strength={}",
        rollback_recommendation.reason, artifact_summary.rollback_strength
    );
    if !artifact_summary.consumed_trend_reason.is_empty() {
        promotion_decision.reason = format!(
            "{}|artifact_consumed_trend_reason={}",
            promotion_decision.reason, artifact_summary.consumed_trend_reason
        );
        rollback_recommendation.reason = format!(
            "{}|artifact_consumed_trend_reason={}",
            rollback_recommendation.reason, artifact_summary.consumed_trend_reason
        );
    }
    for factor in &artifact_summary.highlighted_factor_targets {
        if !promotion_decision.target_factors.contains(factor) {
            promotion_decision.target_factors.push(factor.clone());
        }
        if !rollback_recommendation.target_factors.contains(factor) {
            rollback_recommendation.target_factors.push(factor.clone());
        }
    }
    for family in &artifact_summary.highlighted_family_targets {
        if !promotion_decision.target_families.contains(family) {
            promotion_decision.target_families.push(family.clone());
        }
        if !rollback_recommendation.target_families.contains(family) {
            rollback_recommendation.target_families.push(family.clone());
        }
    }
}

fn artifact_consumed_trend_signal(
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> (String, String, Vec<String>) {
    if consumed_impact_summary.total_consumed == 0 {
        return (
            "no_consumed_validation".to_string(),
            "no_consumed_artifacts".to_string(),
            Vec::new(),
        );
    }
    let primary = consumed_impact_summary
        .trend_comparisons
        .iter()
        .max_by(|left, right| {
            left.recent.count.cmp(&right.recent.count).then_with(|| {
                left.average_quality_score_delta
                    .abs()
                    .partial_cmp(&right.average_quality_score_delta.abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
        });
    let consumed_target_kinds = consumed_impact_summary
        .by_kind_trend_comparisons
        .iter()
        .filter_map(|(kind, comparisons)| {
            let (status, _) = consumed_validation_status_from_comparisons(comparisons);
            matches!(
                status.as_str(),
                "validated_improving" | "validated_regressing"
            )
            .then(|| kind.clone())
        })
        .collect::<Vec<_>>();
    let (status, reason) = consumed_validation_status_from_comparisons(
        primary
            .map(|comparison| vec![comparison.clone()])
            .unwrap_or_default()
            .as_slice(),
    );
    match primary {
        Some(_) => (
            status,
            format!("{} target_kinds={:?}", reason, consumed_target_kinds),
            consumed_target_kinds,
        ),
        None => (
            "insufficient_consumed_history".to_string(),
            format!(
                "consumed_total={} requires_more_consumed_windows",
                consumed_impact_summary.total_consumed
            ),
            Vec::new(),
        ),
    }
}

fn artifact_consumed_decision_gate(
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> ArtifactConsumedDecisionGate {
    let (status, reason, target_kinds) = artifact_consumed_trend_signal(consumed_impact_summary);
    ArtifactConsumedDecisionGate {
        status,
        reason,
        target_kinds,
    }
}

fn consumed_validation_rank(status: &str) -> u8 {
    match status {
        "validated_regressing" => 3,
        "validated_improving" => 2,
        "validated_stable" => 1,
        _ => 0,
    }
}

fn consumed_validation_score(status: &str, reason: &str) -> f64 {
    let quality_delta = reason
        .split("avg_quality_score_delta=")
        .nth(1)
        .and_then(|rest| rest.split_whitespace().next())
        .and_then(|value| value.trim_end_matches(',').parse::<f64>().ok())
        .unwrap_or(0.0);
    let positive_rate_delta = reason
        .split("positive_rate_delta=")
        .nth(1)
        .and_then(|rest| rest.split_whitespace().next())
        .and_then(|value| value.trim_end_matches(',').parse::<f64>().ok())
        .unwrap_or(0.0);
    let magnitude = quality_delta.abs().max((positive_rate_delta * 100.0).abs());
    match status {
        "validated_regressing" => -magnitude,
        "validated_improving" => magnitude,
        _ => 0.0,
    }
}

fn sorted_artifact_factor_consumed_validation(
    snapshot: &WorkflowSnapshot,
) -> Vec<ict_engine::state::ArtifactFactorTrendSummary> {
    let mut trends = snapshot
        .artifact_factor_trends
        .iter()
        .filter(|trend| trend.consumed_entries > 0)
        .cloned()
        .collect::<Vec<_>>();
    trends.sort_by(|left, right| {
        consumed_validation_rank(&right.consumed_validation_status)
            .cmp(&consumed_validation_rank(&left.consumed_validation_status))
            .then_with(|| right.consumed_entries.cmp(&left.consumed_entries))
            .then_with(|| {
                right
                    .consumed_validation_score
                    .abs()
                    .partial_cmp(&left.consumed_validation_score.abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    trends
}

fn sorted_artifact_family_consumed_validation(
    snapshot: &WorkflowSnapshot,
) -> Vec<ict_engine::state::ArtifactFamilyTrendSummary> {
    let mut trends = snapshot
        .artifact_family_trends
        .iter()
        .filter(|trend| trend.consumed_entries > 0)
        .cloned()
        .collect::<Vec<_>>();
    trends.sort_by(|left, right| {
        consumed_validation_rank(&right.consumed_validation_status)
            .cmp(&consumed_validation_rank(&left.consumed_validation_status))
            .then_with(|| right.consumed_entries.cmp(&left.consumed_entries))
            .then_with(|| {
                right
                    .consumed_validation_score
                    .abs()
                    .partial_cmp(&left.consumed_validation_score.abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    trends
}

fn apply_artifact_consumption_preview(
    artifact_ledger: &mut [ArtifactLedgerEntry],
    artifact_id: &str,
    update_run_id: &str,
    realized_outcome: &str,
    pnl: f64,
    consumed_at: chrono::DateTime<Utc>,
) {
    for entry in artifact_ledger {
        if entry.artifact_id != artifact_id {
            continue;
        }
        entry.consumed_by_update_run_id = Some(update_run_id.to_string());
        entry.consumed_at = Some(consumed_at);
        entry.consumed_outcome = Some(realized_outcome.to_string());
        entry.regraded_at = Some(consumed_at);
        let (regrade_status, regrade_reason, quality_adjustment) = match realized_outcome {
            "win" if pnl > 0.0 => ("validated_positive", "consumed_with_positive_pnl", 20),
            "win" => ("validated_positive", "consumed_with_win_outcome", 10),
            "loss" if pnl < 0.0 => ("validated_negative", "consumed_with_negative_pnl", -20),
            "loss" => ("validated_negative", "consumed_with_loss_outcome", -10),
            _ => ("validated_neutral", "consumed_with_breakeven_outcome", 0),
        };
        entry.consumption_regrade_status = Some(regrade_status.to_string());
        entry.consumption_regrade_reason = Some(regrade_reason.to_string());
        entry.quality_score += quality_adjustment;
        entry.actionable = false;
        entry.promote_candidate = false;
    }
}

fn consumed_validation_status_from_comparisons(
    comparisons: &[ict_engine::state::ArtifactConsumedImpactTrendComparison],
) -> (String, String) {
    let thresholds = decision_thresholds();
    let primary = comparisons
        .iter()
        .filter(|comparison| comparison.recent.count >= thresholds.artifact_consumed_min_window)
        .max_by(|left, right| {
            left.recent.count.cmp(&right.recent.count).then_with(|| {
                left.average_quality_score_delta
                    .abs()
                    .partial_cmp(&right.average_quality_score_delta.abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
        });
    match primary {
        Some(primary)
            if primary.average_quality_score_delta
                >= thresholds.artifact_consumed_improvement_quality_delta
                || primary.positive_rate_delta
                    >= thresholds.artifact_consumed_improvement_positive_rate_delta =>
        {
            (
                "validated_improving".to_string(),
                format!(
                    "label={} avg_quality_score_delta={:.2} positive_rate_delta={:.3} min_window={} improvement_thresholds=({:.2},{:.3})",
                    primary.label,
                    primary.average_quality_score_delta,
                    primary.positive_rate_delta,
                    thresholds.artifact_consumed_min_window,
                    thresholds.artifact_consumed_improvement_quality_delta,
                    thresholds.artifact_consumed_improvement_positive_rate_delta
                ),
            )
        }
        Some(primary)
            if primary.average_quality_score_delta
                <= thresholds.artifact_consumed_regression_quality_delta
                || primary.positive_rate_delta
                    <= thresholds.artifact_consumed_regression_positive_rate_delta =>
        {
            (
                "validated_regressing".to_string(),
                format!(
                    "label={} avg_quality_score_delta={:.2} positive_rate_delta={:.3} min_window={} regression_thresholds=({:.2},{:.3})",
                    primary.label,
                    primary.average_quality_score_delta,
                    primary.positive_rate_delta,
                    thresholds.artifact_consumed_min_window,
                    thresholds.artifact_consumed_regression_quality_delta,
                    thresholds.artifact_consumed_regression_positive_rate_delta
                ),
            )
        }
        Some(primary) => (
            "validated_stable".to_string(),
            format!(
                "label={} avg_quality_score_delta={:.2} positive_rate_delta={:.3} thresholds_not_crossed",
                primary.label, primary.average_quality_score_delta, primary.positive_rate_delta
            ),
        ),
        None if comparisons.is_empty() => (
            "insufficient_consumed_history".to_string(),
            format!(
                "no_comparisons_available min_window={}",
                thresholds.artifact_consumed_min_window
            ),
        ),
        None => (
            "insufficient_consumed_history".to_string(),
            format!(
                "comparisons_below_min_window min_window={}",
                thresholds.artifact_consumed_min_window
            ),
        ),
    }
}

fn top_consumed_trend_comparisons(
    consumed_impact_summary: &ict_engine::state::ArtifactConsumedImpactSummary,
) -> Vec<ict_engine::state::ArtifactConsumedImpactTrendComparison> {
    let mut comparisons = consumed_impact_summary.trend_comparisons.clone();
    comparisons.sort_by(|left, right| {
        (right.conclusion != "stable")
            .cmp(&(left.conclusion != "stable"))
            .then_with(|| right.recent.count.cmp(&left.recent.count))
            .then_with(|| {
                right
                    .average_quality_score_delta
                    .abs()
                    .partial_cmp(&left.average_quality_score_delta.abs())
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });
    comparisons.truncate(3);
    comparisons
}

fn family_history_window() -> usize {
    env::var("ICT_ENGINE_FAMILY_HISTORY_WINDOW")
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .map(|value| value.clamp(1, 20))
        .unwrap_or(5)
}

fn env_f64(name: &str, default: f64) -> f64 {
    env::var(name)
        .ok()
        .and_then(|value| value.parse::<f64>().ok())
        .unwrap_or(default)
}

fn env_bool(name: &str, default: bool) -> bool {
    env::var(name)
        .ok()
        .and_then(|value| match value.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => Some(true),
            "0" | "false" | "no" | "off" => Some(false),
            _ => None,
        })
        .unwrap_or(default)
}

fn env_f64_with_source(name: &str, default: f64) -> (f64, String) {
    match env::var(name)
        .ok()
        .and_then(|value| value.parse::<f64>().ok().map(|parsed| (parsed, value)))
    {
        Some((parsed, raw)) => (parsed, format!("env:{}={}", name, raw)),
        None => (default, "default".to_string()),
    }
}

fn env_bool_with_source(name: &str, default: bool) -> (bool, String) {
    match env::var(name).ok() {
        Some(raw) => match raw.trim().to_ascii_lowercase().as_str() {
            "1" | "true" | "yes" | "on" => (true, format!("env:{}={}", name, raw)),
            "0" | "false" | "no" | "off" => (false, format!("env:{}={}", name, raw)),
            _ => (default, "default".to_string()),
        },
        None => (default, "default".to_string()),
    }
}

fn artifact_review_rules() -> ict_engine::state::ArtifactReviewRules {
    ict_engine::state::ArtifactReviewRules {
        pending_update: ict_engine::state::PendingUpdateReviewRules {
            min_probability_improvement: env_f64(
                "ICT_ENGINE_PENDING_MIN_PROBABILITY_IMPROVEMENT",
                0.03,
            ),
            min_top_factor_score_improvement: env_f64(
                "ICT_ENGINE_PENDING_MIN_TOP_FACTOR_SCORE_IMPROVEMENT",
                0.05,
            ),
            min_avg_family_score_improvement: env_f64(
                "ICT_ENGINE_PENDING_MIN_AVG_FAMILY_SCORE_IMPROVEMENT",
                0.03,
            ),
            require_same_data: env_bool("ICT_ENGINE_PENDING_REQUIRE_SAME_DATA", true),
            require_same_factor_version: env_bool(
                "ICT_ENGINE_PENDING_REQUIRE_SAME_FACTOR_VERSION",
                true,
            ),
            require_same_prompt_version: env_bool(
                "ICT_ENGINE_PENDING_REQUIRE_SAME_PROMPT_VERSION",
                true,
            ),
        },
        execution_candidate: ict_engine::state::ExecutionCandidateReviewRules {
            min_posterior_improvement: env_f64(
                "ICT_ENGINE_EXECUTION_MIN_POSTERIOR_IMPROVEMENT",
                0.03,
            ),
            min_win_probability_improvement: env_f64(
                "ICT_ENGINE_EXECUTION_MIN_WIN_PROBABILITY_IMPROVEMENT",
                0.03,
            ),
            require_same_data: env_bool("ICT_ENGINE_EXECUTION_REQUIRE_SAME_DATA", true),
            require_same_factor_version: env_bool(
                "ICT_ENGINE_EXECUTION_REQUIRE_SAME_FACTOR_VERSION",
                true,
            ),
        },
    }
}

fn artifact_review_rule_sources() -> ict_engine::state::ArtifactReviewRuleSources {
    let mut pending_update = BTreeMap::new();
    let (_, source) = env_f64_with_source("ICT_ENGINE_PENDING_MIN_PROBABILITY_IMPROVEMENT", 0.03);
    pending_update.insert("min_probability_improvement".to_string(), source);
    let (_, source) =
        env_f64_with_source("ICT_ENGINE_PENDING_MIN_TOP_FACTOR_SCORE_IMPROVEMENT", 0.05);
    pending_update.insert("min_top_factor_score_improvement".to_string(), source);
    let (_, source) =
        env_f64_with_source("ICT_ENGINE_PENDING_MIN_AVG_FAMILY_SCORE_IMPROVEMENT", 0.03);
    pending_update.insert("min_avg_family_score_improvement".to_string(), source);
    let (_, source) = env_bool_with_source("ICT_ENGINE_PENDING_REQUIRE_SAME_DATA", true);
    pending_update.insert("require_same_data".to_string(), source);
    let (_, source) = env_bool_with_source("ICT_ENGINE_PENDING_REQUIRE_SAME_FACTOR_VERSION", true);
    pending_update.insert("require_same_factor_version".to_string(), source);
    let (_, source) = env_bool_with_source("ICT_ENGINE_PENDING_REQUIRE_SAME_PROMPT_VERSION", true);
    pending_update.insert("require_same_prompt_version".to_string(), source);

    let mut execution_candidate = BTreeMap::new();
    let (_, source) = env_f64_with_source("ICT_ENGINE_EXECUTION_MIN_POSTERIOR_IMPROVEMENT", 0.03);
    execution_candidate.insert("min_posterior_improvement".to_string(), source);
    let (_, source) =
        env_f64_with_source("ICT_ENGINE_EXECUTION_MIN_WIN_PROBABILITY_IMPROVEMENT", 0.03);
    execution_candidate.insert("min_win_probability_improvement".to_string(), source);
    let (_, source) = env_bool_with_source("ICT_ENGINE_EXECUTION_REQUIRE_SAME_DATA", true);
    execution_candidate.insert("require_same_data".to_string(), source);
    let (_, source) =
        env_bool_with_source("ICT_ENGINE_EXECUTION_REQUIRE_SAME_FACTOR_VERSION", true);
    execution_candidate.insert("require_same_factor_version".to_string(), source);

    ict_engine::state::ArtifactReviewRuleSources {
        pending_update,
        execution_candidate,
    }
}

fn pending_update_review_rule_version(
    rules: &ict_engine::state::PendingUpdateReviewRules,
) -> String {
    compute_hash(&[
        format!("{:.6}", rules.min_probability_improvement),
        format!("{:.6}", rules.min_top_factor_score_improvement),
        format!("{:.6}", rules.min_avg_family_score_improvement),
        rules.require_same_data.to_string(),
        rules.require_same_factor_version.to_string(),
        rules.require_same_prompt_version.to_string(),
    ])
}

fn execution_candidate_review_rule_version(
    rules: &ict_engine::state::ExecutionCandidateReviewRules,
) -> String {
    compute_hash(&[
        format!("{:.6}", rules.min_posterior_improvement),
        format!("{:.6}", rules.min_win_probability_improvement),
        rules.require_same_data.to_string(),
        rules.require_same_factor_version.to_string(),
    ])
}

fn trend_label_f64(values: &[f64]) -> String {
    match (values.first(), values.last()) {
        (Some(first), Some(last)) if last - first > 0.05 => "improving".to_string(),
        (Some(first), Some(last)) if first - last > 0.05 => "deteriorating".to_string(),
        (Some(_), Some(_)) => "stable".to_string(),
        _ => "insufficient_history".to_string(),
    }
}

fn trend_label_usize(values: &[usize]) -> String {
    match (values.first(), values.last()) {
        (Some(first), Some(last)) if last > first => "worsening".to_string(),
        (Some(first), Some(last)) if last < first => "improving".to_string(),
        (Some(_), Some(_)) => "stable".to_string(),
        _ => "insufficient_history".to_string(),
    }
}

fn action_priority(item: &AgentActionItem) -> u8 {
    let stage_score = match item.stage.as_str() {
        "artifact_consumption" => 5,
        "rollback" => 4,
        "promotion" => 3,
        "iteration" => 2,
        "family_review" => 1,
        _ => 0,
    };
    stage_score + if item.blocking { 10 } else { 0 }
}

fn priority_rank(priority: &str) -> u8 {
    match priority {
        "high" => 3,
        "medium" => 2,
        "low" => 1,
        _ => 0,
    }
}

fn finalize_backtest_report(
    mut report: BacktestReport,
    symbol: &str,
    data: &str,
    paired_data: Option<&str>,
    candles: &[Candle],
    paired_candles_slice: Option<&[Candle]>,
    learning_state: &LearningState,
    previous_rankings: &[PersistedFactorRanking],
    previous_trade_outcome_cpt: &BTreeMap<String, BTreeMap<String, f64>>,
    updated_network: &ict_engine::bbn::BayesianNetwork,
    state_dir: &str,
    warmup_bars: usize,
    hold_bars: usize,
    realism: &ExecutionRealismConfig,
    online_learning: bool,
) -> Result<BacktestReport> {
    let previous_runs: Vec<BacktestRunRecord> =
        load_state_or_default(state_dir, symbol, BACKTEST_RUNS_FILE)?;
    let score_deltas = ranking_diffs(previous_rankings, &report.factor_ranking);
    let final_trade_outcome_cpt = trade_outcome_cpt_snapshot(updated_network)?;
    let probability_deltas =
        cpt_probability_diffs(previous_trade_outcome_cpt, &final_trade_outcome_cpt);
    report.provenance = run_provenance(
        learning_state,
        &[
            "backtest",
            data,
            paired_data.unwrap_or(""),
            &warmup_bars.to_string(),
            &hold_bars.to_string(),
            &format!("spread_bps={:.4}", realism.spread_bps),
            &format!("slippage_bps={:.4}", realism.slippage_bps),
            &format!("fee_bps={:.4}", realism.fee_bps),
            &ambiguous_bar_policy_label(realism.ambiguous_bar_policy),
            &online_learning.to_string(),
        ],
        data_fingerprint(candles, paired_candles_slice, "backtest"),
    );
    report.dataset_comparability = dataset_comparability(
        previous_runs.last().map(|run| run.run_id.clone()),
        previous_runs.last().map(|run| &run.provenance),
        &report.provenance,
    );
    let thresholds = decision_thresholds();
    report.decision_thresholds = thresholds.clone();
    let artifact_consumed_gate = artifact_consumed_decision_gate(
        &artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?,
    );
    let (_, artifact_family_trends) = artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    report.promotion_decision = derive_promotion_decision(
        &report.factor_ranking,
        &score_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.rollback_recommendation = derive_rollback_recommendation(
        &report.factor_ranking,
        &score_deltas,
        &probability_deltas,
        &report.dataset_comparability,
        &thresholds,
        Some(&artifact_consumed_gate),
    );
    report.factor_family_outcomes = derive_family_outcomes(
        &report.factor_family_decisions,
        &thresholds,
        &report.dataset_comparability,
        Some(&artifact_family_trends),
    );
    report.factor_family_diffs = family_diffs(
        previous_runs
            .last()
            .map(|run| run.factor_family_decisions.as_slice())
            .unwrap_or(&[]),
        &report.factor_family_decisions,
    );
    report.decision_history_summary = decision_history_summary(previous_runs.iter().map(|run| {
        (
            run.promotion_decision.clone(),
            run.rollback_recommendation.clone(),
        )
    }));
    report.factor_family_history = family_history_from_runs(previous_runs.iter().map(|run| {
        (
            run.run_id.clone(),
            run.timestamp,
            run.factor_family_decisions.clone(),
        )
    }));
    report.agent_action_plan = build_agent_action_plan(
        "backtest_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
        &report.factor_iteration_queue,
        &report.factor_family_outcomes,
    );
    let (artifact_factor_trends, artifact_family_trends) =
        artifact_trend_summaries_for_symbol(state_dir, symbol)?;
    let artifact_consumed_impact_summary =
        artifact_consumed_impact_summary_for_symbol(state_dir, symbol)?;
    augment_action_plan_with_artifact_trends(
        &mut report.agent_action_plan,
        symbol,
        state_dir,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_action_summary = artifact_action_summary(
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_consumed_impact_summary,
    );
    report.artifact_decision_summary = artifact_decision_summary_for_symbol(state_dir, symbol)?;
    report.artifact_decision_section = artifact_decision_section_from_parts(
        &report.artifact_decision_summary,
        &report.artifact_action_summary,
        &artifact_factor_trends,
        &artifact_family_trends,
        &artifact_rule_break_effects_for_symbol(state_dir, symbol)?,
        &artifact_consumed_impact_summary,
    );
    link_artifact_decision_summary_to_decisions(
        &report.artifact_decision_summary,
        &mut report.promotion_decision,
        &mut report.rollback_recommendation,
    );
    report.workflow_state = workflow_state_from_context(
        "backtest_review_ready",
        &report.promotion_decision,
        &report.rollback_recommendation,
    );
    report.recommended_commands = command_recommendations(&CommandContext {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        analyze: Some(AnalyzeCommandSource::Files {
            data_htf: data.to_string(),
            data_mtf: data.to_string(),
            data_ltf: data.to_string(),
        }),
        research_data: Some(data.to_string()),
        paired_data: paired_data.map(str::to_string),
        update_outcome: None,
        update_entry_signal: None,
        update_feedback_file: None,
        user_data_selection_required: true,
    });
    concretize_action_plan_commands(&mut report.agent_action_plan, &report.recommended_commands);
    report.recommended_next_command =
        recommended_next_command(&report.agent_action_plan, &report.recommended_commands);
    report.agent_context_bundle = build_agent_context_bundle(
        symbol,
        state_dir,
        &report.workflow_state,
        "backtest_review_ready",
        &report.recommended_next_command,
        &report.recommended_commands,
        &report.dataset_comparability,
        &report.factor_iteration_queue,
        &report.factor_family_outcomes,
        None,
        None,
        None,
        Some(&report.artifact_decision_summary),
    );

    report.factor_score_deltas = score_deltas.clone();
    report.trade_outcome_deltas = probability_deltas.clone();
    report.final_trade_outcome_cpt = final_trade_outcome_cpt.clone();
    report.agent_prompts.prompts.insert(
        0,
        dataset_audit_prompt(
            symbol,
            data,
            paired_data,
            candles.len(),
            paired_candles_slice.map(|items| items.len()),
            "backtest",
        ),
    );
    report.agent_prompts.prompts.push(promotion_gate_prompt(
        symbol,
        &report.factor_ranking,
        &score_deltas,
        &report.decision_thresholds,
    ));
    report.agent_prompts.prompts.push(rollback_review_prompt(
        symbol,
        &score_deltas,
        &probability_deltas,
        &report.decision_thresholds,
    ));

    append_backtest_run(
        state_dir,
        symbol,
        BacktestRunRecord {
            run_id: format!(
                "backtest:{}:{}",
                symbol,
                Utc::now().format("%Y%m%dT%H%M%S%.3fZ")
            ),
            timestamp: Utc::now(),
            symbol: symbol.to_string(),
            provenance: report.provenance.clone(),
            decision_thresholds: report.decision_thresholds.clone(),
            dataset_comparability: report.dataset_comparability.clone(),
            promotion_decision: report.promotion_decision.clone(),
            rollback_recommendation: report.rollback_recommendation.clone(),
            family_history_window: family_history_window(),
            data_path: data.to_string(),
            paired_data_path: paired_data.map(str::to_string),
            candles: candles.len(),
            paired_candles: paired_candles_slice.map(|items| items.len()),
            warmup_bars,
            hold_bars,
            online_learning,
            source_command: "backtest".to_string(),
            total_return: report.metrics.total_return,
            trade_count: report.trades,
            conformal_coverage_1sigma: report.metrics.conformal_coverage_1sigma,
            conformal_miscoverage_1sigma: report.metrics.conformal_miscoverage_1sigma,
            mean_prediction_interval_half_width: report.metrics.mean_prediction_interval_half_width,
            worst_window_miscoverage: report.metrics.worst_window_miscoverage,
            regime_break_penalty: report.metrics.regime_break_penalty,
            structural_break_score: report.metrics.structural_break_score,
            structural_break_index: report.metrics.structural_break_index,
            structural_break_detected: report.metrics.structural_break_detected,
            signal_structural_break_score: report.metrics.signal_structural_break_score,
            signal_structural_break_index: report.metrics.signal_structural_break_index,
            signal_structural_break_detected: report.metrics.signal_structural_break_detected,
            residual_structural_break_score: report.metrics.residual_structural_break_score,
            residual_structural_break_index: report.metrics.residual_structural_break_index,
            residual_structural_break_detected: report.metrics.residual_structural_break_detected,
            rolling_ic_structural_break_score: report.metrics.rolling_ic_structural_break_score,
            rolling_ic_structural_break_index: report.metrics.rolling_ic_structural_break_index,
            rolling_ic_structural_break_detected: report.metrics.rolling_ic_structural_break_detected,
            factor_score_deltas: score_deltas,
            trade_outcome_deltas: probability_deltas,
            factor_family_decisions: report.factor_family_decisions.clone(),
            factor_family_outcomes: report.factor_family_outcomes.clone(),
            factor_family_diffs: report.factor_family_diffs.clone(),
            factor_family_history: report.factor_family_history.clone(),
            decision_history_summary: report.decision_history_summary.clone(),
            workflow_state: report.workflow_state.clone(),
            agent_action_plan: report.agent_action_plan.clone(),
            recommended_commands: report.recommended_commands.clone(),
            recommended_next_command: report.recommended_next_command.clone(),
            agent_context_bundle: report.agent_context_bundle.clone(),
            agent_context_bundle_minimal: report.agent_context_bundle_minimal.clone(),
            feedback_history_summary: report.feedback_history_summary.clone(),
            artifact_action_summary: report.artifact_action_summary.clone(),
            artifact_decision_summary: report.artifact_decision_summary.clone(),
            artifact_decision_section: report.artifact_decision_section.clone(),
            agent_prompts: report.agent_prompts.clone(),
            prompt_workflow: report.agent_prompts.workflow.clone(),
            multi_timeframe_summary: Vec::new(),
        },
    )?;
    report.workflow_snapshot = refresh_workflow_snapshot(state_dir, symbol)?;

    Ok(report)
}

fn build_update_agent_prompts(
    symbol: &str,
    factor_ranking: &[PersistedFactorRanking],
    factor_iteration_queue: &[FactorIterationPrompt],
    feedback_history_summary: &FeedbackHistorySummary,
    updated_trade_outcome: &BTreeMap<String, f64>,
    normalized_entry_quality: &str,
    factor_alignment: &str,
    factor_uncertainty: &str,
    realized_outcome: &str,
    feedback_records_applied: usize,
    consumed_pre_bayes_evidence_filter: Option<&PreBayesEvidenceFilter>,
    consumed_pre_bayes_entry_quality_bridge: Option<&ict_engine::state::PreBayesEntryQualityBridge>,
    consumed_multi_timeframe_summary: &[String],
) -> AgentPromptPack {
    let mut pack = factor_iteration_prompt_pack(
        symbol,
        factor_ranking,
        factor_iteration_queue,
        feedback_history_summary,
    );
    pack.workflow = format!(
        "Use the realized update for {} to review whether the latest result should change factor weights, factor evidence interpretation, or future trade acceptance thresholds.",
        symbol
    );
    pack.prompts.insert(
        0,
        AgentPrompt::new(
            "update_feedback_review",
            "feedback_update",
            "high",
            "Review the newly realized outcome and decide what the next agent iteration should target.",
            "You are the realized-feedback agent. Use the updated trade_outcome distribution plus factor scorecards to decide whether the latest result strengthens confidence, exposes a factor weakness, or suggests a problem in evidence mapping.",
            format!(
                "Symbol={} entry_quality={} factor_alignment={} factor_uncertainty={} realized_outcome={} feedback_records_applied={} updated_trade_outcome={:?} iteration_queue={:?}",
                symbol,
                normalized_entry_quality,
                factor_alignment,
                factor_uncertainty,
                realized_outcome,
                feedback_records_applied,
                updated_trade_outcome,
                factor_iteration_queue
            ),
            vec![
                "If duplicate_feedback_skipped is true, do not infer a new learning event".to_string(),
                "If factor_alignment and realized_outcome disagree repeatedly, prioritize evidence-mapping review or factor replacement".to_string(),
                "If updated_trade_outcome improves while factor scores stay weak, review BBN calibration before editing factor code".to_string(),
            ],
            vec![
                "src/main.rs".to_string(),
                "src/factors/weight_updater.rs".to_string(),
                "src/bbn/trading/topology.rs".to_string(),
                "src/agent/prompts.rs".to_string(),
            ],
        ),
    );
    if let Some(filter) = consumed_pre_bayes_evidence_filter {
        let bridge_diff =
            consumed_pre_bayes_entry_quality_bridge.map(pre_bayes_entry_quality_bridge_diff);
        pack.prompts.insert(
            1,
            AgentPrompt::new(
                "update_consumed_pre_bayes_review",
                "feedback_update",
                "high",
                "Review the consumed analyze pre-bayes evidence against the realized outcome.",
                "You are the update-pre-bayes reviewer. Compare the realized outcome with the consumed analyze pre-bayes gate, bridge, and multi-timeframe summary before deciding whether to revise factor logic, evidence mapping, or BBN calibration.",
                format!(
                    "Symbol={} realized_outcome={} consumed_pre_bayes_gate_status={} consumed_pre_bayes_quality={:.3} consumed_pre_bayes_conflicts={:?} consumed_pre_bayes_filtered_assignments={:?} consumed_multi_timeframe_summary={:?} consumed_bridge_selected_entry_quality={:?} consumed_bridge_probability_gap={:.3}",
                    symbol,
                    realized_outcome,
                    filter.gating_status,
                    filter.evidence_quality_score,
                    filter.conflict_flags,
                    filter.evidence_assignments,
                    consumed_multi_timeframe_summary,
                    bridge_diff.as_ref().and_then(|diff| diff.selected_entry_quality.clone()),
                    bridge_diff
                        .as_ref()
                        .map(|diff| diff.long_short_signal_probability_gap)
                        .unwrap_or_default()
                ),
                vec![
                    "If the consumed pre-bayes gate was weak or soft-evidence-heavy, prefer calibration review over factor churn".to_string(),
                    "Use the consumed multi-timeframe context to judge whether the realized outcome invalidates the previous resonance mapping or only the execution result".to_string(),
                ],
                vec![
                    "src/main.rs".to_string(),
                    "src/bbn/trading/update.rs".to_string(),
                    "src/state/types.rs".to_string(),
                ],
            ),
        );
    }
    pack
}

fn append_artifact_decision_prompt(
    pack: &mut AgentPromptPack,
    symbol: &str,
    section: &ict_engine::state::ArtifactDecisionSection,
) {
    pack.prompts.push(AgentPrompt::new(
        "artifact_decision_review",
        "artifact_decision",
        "high",
        "Review artifact-driven actions and ensure they align with the next code or model iteration.",
        "You are the artifact-decision agent. Use the artifact decision section to validate whether the current pending/execution artifacts strengthen promotion, trigger rollback review, or should only be observed.",
        format!(
            "Symbol={} artifact_summary={} consumed_trend_status={} consumed_trend_reason={} highlighted_actions={:?} top_factor_trends={:?} top_family_trends={:?} top_rule_break_effects={:?} top_consumed_trends={:?}",
            symbol,
            section.summary.summary,
            section.summary.consumed_trend_status,
            section.summary.consumed_trend_reason,
            section.action_summary,
            section
                .top_factor_trends
                .iter()
                .map(|trend| format!("{}:{}:{}", trend.factor_name, trend.decision_status, trend.average_quality_score))
                .collect::<Vec<_>>(),
            section
                .top_family_trends
                .iter()
                .map(|trend| format!("{}:{}:{:?}", trend.family, trend.decision_status, trend.latest_score))
                .collect::<Vec<_>>(),
            section
                .top_rule_break_effects
                .iter()
                .map(|effect| format!("{}:{}->{}:{}", effect.artifact_kind, effect.from_rule_version, effect.to_rule_version, effect.conclusion))
                .collect::<Vec<_>>(),
            section
                .top_consumed_trend_comparisons
                .iter()
                .map(|trend| format!(
                    "{}:{}:{:.2}:{:.3}",
                    trend.label,
                    trend.conclusion,
                    trend.average_quality_score_delta,
                    trend.positive_rate_delta
                ))
                .collect::<Vec<_>>()
        ),
        vec![
            "Explicitly state whether artifact evidence strengthens promotion, rollback review, or observation only".to_string(),
            "Do not ignore rule-break effects when artifact review versions changed".to_string(),
            "Use consumed validation trends when realized artifact outcomes are available".to_string(),
            "Name the artifact-driven factor/family targets before recommending code edits".to_string(),
        ],
        vec![
            "src/main.rs".to_string(),
            "src/state/types.rs".to_string(),
            "src/agent/prompts.rs".to_string(),
        ],
    ));
    if matches!(
        section.summary.consumed_trend_status.as_str(),
        "validated_improving" | "validated_regressing" | "validated_stable"
    ) {
        pack.prompts.push(AgentPrompt::new(
            "artifact_consumption_review",
            "artifact_consumption",
            "high",
            "Review realized artifact consumption validation before trusting promotion or rollback conclusions.",
            "You are the artifact-consumption agent. Use realized artifact outcomes, consumed validation trends, and target kinds to decide whether artifact evidence confirms promotion, forces rollback, or only warrants observation.",
            format!(
                "Symbol={} consumed_trend_status={} consumed_trend_reason={} consumed_target_kinds={:?} top_consumed_trends={:?}",
                symbol,
                section.summary.consumed_trend_status,
                section.summary.consumed_trend_reason,
                section.summary.consumed_target_kinds,
                section
                    .top_consumed_trend_comparisons
                    .iter()
                    .map(|trend| format!(
                        "{}:{}:{:.2}:{:.3}",
                        trend.label,
                        trend.conclusion,
                        trend.average_quality_score_delta,
                        trend.positive_rate_delta
                    ))
                    .collect::<Vec<_>>()
            ),
            vec![
                "State explicitly whether consumed artifact evidence validates or invalidates recent promotion logic".to_string(),
                "If consumed validation regresses, prefer rollback review before further factor promotion".to_string(),
                "Name which artifact kinds are implicated before recommending the next iteration".to_string(),
            ],
            vec![
                "src/main.rs".to_string(),
                "src/state/types.rs".to_string(),
                "src/factors/weight_updater.rs".to_string(),
            ],
        ));
    }
}

fn ranking_diffs(
    previous: &[PersistedFactorRanking],
    current: &[PersistedFactorRanking],
) -> Vec<RankingDiffItem> {
    let previous_map = previous
        .iter()
        .map(|item| (item.factor_name.clone(), item))
        .collect::<HashMap<_, _>>();
    let mut diffs = current
        .iter()
        .map(|item| {
            let previous = previous_map.get(&item.factor_name).copied();
            RankingDiffItem {
                factor_name: item.factor_name.clone(),
                previous_score: previous.map(|entry| entry.composite_score),
                new_score: item.composite_score,
                score_delta: item.composite_score
                    - previous.map(|entry| entry.composite_score).unwrap_or(0.0),
                previous_weight: previous.map(|entry| entry.weight),
                new_weight: item.weight,
                weight_delta: item.weight - previous.map(|entry| entry.weight).unwrap_or(0.0),
                previous_action: previous.map(|entry| entry.iteration_action.clone()),
                new_action: item.iteration_action.clone(),
            }
        })
        .collect::<Vec<_>>();
    diffs.sort_by(|a, b| {
        b.score_delta
            .abs()
            .partial_cmp(&a.score_delta.abs())
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    diffs
}

fn probability_diffs(
    previous: &Option<BTreeMap<String, f64>>,
    current: &BTreeMap<String, f64>,
) -> Vec<ProbabilityDiff> {
    let mut keys = current.keys().cloned().collect::<Vec<_>>();
    keys.sort();
    keys.into_iter()
        .map(|state| {
            let new = current.get(&state).copied().unwrap_or(0.0);
            let previous_value = previous.as_ref().and_then(|map| map.get(&state).copied());
            ProbabilityDiff {
                state,
                previous: previous_value,
                new,
                delta: new - previous_value.unwrap_or(0.0),
            }
        })
        .collect()
}

fn cpt_probability_diffs(
    previous: &BTreeMap<String, BTreeMap<String, f64>>,
    current: &BTreeMap<String, BTreeMap<String, f64>>,
) -> Vec<ProbabilityDiff> {
    let mut diffs = Vec::new();
    for (entry_quality, current_probs) in current {
        let previous_probs = previous.get(entry_quality).cloned();
        for diff in probability_diffs(&previous_probs, current_probs) {
            diffs.push(ProbabilityDiff {
                state: format!("{}:{}", entry_quality, diff.state),
                previous: diff.previous,
                new: diff.new,
                delta: diff.delta,
            });
        }
    }
    diffs
}

fn dataset_comparability(
    previous_run_id: Option<String>,
    previous: Option<&RunProvenance>,
    current: &RunProvenance,
) -> DatasetComparability {
    match previous {
        None => DatasetComparability {
            comparable: false,
            previous_run_id,
            reason: "no_previous_run".to_string(),
            comparison_class: "no_previous_run".to_string(),
            same_data: false,
            same_config: false,
            same_prompt_version: false,
            same_factor_version: false,
        },
        Some(previous) if previous.data_fingerprint == current.data_fingerprint => {
            let same_config = previous.config_hash == current.config_hash;
            DatasetComparability {
                comparable: true,
                previous_run_id,
                reason: if same_config {
                    "same_data_same_config".to_string()
                } else {
                    "same_data_different_config".to_string()
                },
                comparison_class: if same_config {
                    "same_data_same_config".to_string()
                } else {
                    "same_data_different_config".to_string()
                },
                same_data: true,
                same_config,
                same_prompt_version: previous.prompt_version == current.prompt_version,
                same_factor_version: previous.factor_version == current.factor_version,
            }
        }
        Some(previous) => DatasetComparability {
            comparable: false,
            previous_run_id,
            reason: "different_data_fingerprint".to_string(),
            comparison_class: "different_data_fingerprint".to_string(),
            same_data: false,
            same_config: false,
            same_prompt_version: previous.prompt_version == current.prompt_version,
            same_factor_version: previous.factor_version == current.factor_version,
        },
    }
}

fn decision_thresholds() -> DecisionThresholds {
    DecisionThresholds::default()
}

fn compute_hash(parts: &[impl AsRef<str>]) -> String {
    let mut hasher = DefaultHasher::new();
    for part in parts {
        part.as_ref().hash(&mut hasher);
    }
    format!("{:016x}", hasher.finish())
}

fn data_fingerprint(
    candles: &[Candle],
    paired_candles: Option<&[Candle]>,
    source_tag: &str,
) -> String {
    let mut parts = vec![
        source_tag.to_string(),
        candles.len().to_string(),
        candles
            .first()
            .map(|candle| candle.timestamp.to_rfc3339())
            .unwrap_or_default(),
        candles
            .last()
            .map(|candle| candle.timestamp.to_rfc3339())
            .unwrap_or_default(),
        candles
            .first()
            .map(|candle| format!("{:.6}", candle.close))
            .unwrap_or_default(),
        candles
            .last()
            .map(|candle| format!("{:.6}", candle.close))
            .unwrap_or_default(),
    ];

    if let Some(paired) = paired_candles {
        parts.push(format!("paired:{}", paired.len()));
        parts.push(
            paired
                .first()
                .map(|candle| candle.timestamp.to_rfc3339())
                .unwrap_or_default(),
        );
        parts.push(
            paired
                .last()
                .map(|candle| candle.timestamp.to_rfc3339())
                .unwrap_or_default(),
        );
    }

    compute_hash(&parts)
}

fn ambiguous_bar_policy_label(policy: AmbiguousBarPolicy) -> String {
    match policy {
        AmbiguousBarPolicy::FavorStopLoss => "favor_stop_loss".to_string(),
        AmbiguousBarPolicy::FavorTakeProfit => "favor_take_profit".to_string(),
    }
}

fn parse_execution_realism_config(
    spread_bps: f64,
    slippage_bps: f64,
    fee_bps: f64,
    ambiguous_bar_policy: &str,
) -> Result<ExecutionRealismConfig> {
    if spread_bps < 0.0 || slippage_bps < 0.0 || fee_bps < 0.0 {
        bail!("spread/slippage/fee bps must be non-negative");
    }
    let ambiguous_bar_policy = match ambiguous_bar_policy.trim().to_ascii_lowercase().as_str() {
        "favor_stop_loss" | "stop" | "stop_loss" => AmbiguousBarPolicy::FavorStopLoss,
        "favor_take_profit" | "tp" | "take_profit" => AmbiguousBarPolicy::FavorTakeProfit,
        other => bail!("unsupported ambiguous_bar_policy '{}'", other),
    };
    Ok(ExecutionRealismConfig {
        spread_bps,
        slippage_bps,
        fee_bps,
        ambiguous_bar_policy,
    })
}

fn factor_version(learning_state: &LearningState) -> String {
    let parts = learning_state
        .factor_profiles
        .iter()
        .map(|(name, profile)| {
            format!(
                "{}:{}:{:.6}:{:.6}:{:?}:{:?}",
                name,
                profile.enabled,
                profile.base_weight,
                profile.posterior_reliability,
                profile.parameters,
                profile.regime_stats
            )
        })
        .collect::<Vec<_>>();
    compute_hash(&parts)
}

fn run_provenance(
    learning_state: &LearningState,
    config_hash_source: &[impl AsRef<str>],
    data_fingerprint: String,
) -> RunProvenance {
    let mut config_parts = config_hash_source
        .iter()
        .map(|part| part.as_ref().to_string())
        .collect::<Vec<_>>();
    config_parts.push(format!("family_history_window={}", family_history_window()));
    RunProvenance {
        prompt_version: PROMPT_PACK_VERSION.to_string(),
        factor_version: factor_version(learning_state),
        config_hash: compute_hash(&config_parts),
        data_fingerprint,
    }
}

fn normalize_direction_label(input: &str) -> Direction {
    match input.trim().to_ascii_lowercase().as_str() {
        "bull" | "long" | "buy" => Direction::Bull,
        "bear" | "short" | "sell" => Direction::Bear,
        _ => Direction::Neutral,
    }
}

fn normalize_regime_label(input: &str) -> Regime {
    match input.trim().to_ascii_lowercase().as_str() {
        "accumulation" | "accum" => Regime::Accumulation,
        "distribution" | "dist" => Regime::Distribution,
        _ => Regime::ManipulationExpansion,
    }
}

fn neutral_auxiliary(symbol: &str) -> AuxiliaryMarketEvidence {
    AuxiliaryMarketEvidence {
        spot_symbol: symbol.to_string(),
        options_symbol: symbol.to_string(),
        spot_kind: SpotInstrumentKind::Equity,
        spot_last_close: None,
        futures_last_close: None,
        spot_return: None,
        futures_return: None,
        raw_basis_bps: None,
        normalized_basis_bps: None,
        rolling_price_ratio_mean: None,
        put_call_oi_ratio: None,
        put_call_volume_ratio: None,
        near_atm_implied_volatility: None,
        near_atm_delta: None,
        near_atm_gamma: None,
        near_atm_vega: None,
        call_gamma_oi: None,
        put_gamma_oi: None,
        gamma_skew: None,
        hedge_pressure_direction: None,
        hedge_pressure_score: Some(0.0),
        long_bias: 0.0,
        short_bias: 0.0,
        uncertainty_penalty: 0.0,
        notes: vec!["neutral_auxiliary".to_string()],
    }
}

fn neutral_options_summary(
    symbol: &str,
) -> ict_engine::data::realtime::openalice::OptionsChainSummary {
    ict_engine::data::realtime::openalice::OptionsChainSummary {
        symbol: symbol.to_string(),
        underlying_price: None,
        call_open_interest: 0.0,
        put_open_interest: 0.0,
        put_call_oi_ratio: None,
        call_volume: 0.0,
        put_volume: 0.0,
        put_call_volume_ratio: None,
        near_atm_implied_volatility: None,
        near_atm_delta: None,
        near_atm_gamma: None,
        near_atm_vega: None,
        call_gamma_oi: None,
        put_gamma_oi: None,
        gamma_skew: None,
        nearest_expiration_dte: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, TimeZone};
    use ict_engine::analyze::multi_timeframe_parse::ParsedMultiTimeframeEvidence;
    use ict_engine::bbn::trading::topology::build_trading_network;
    use ict_engine::config::build_frame_features_for_market;
    use ict_engine::state::FactorPipelineLabelSource;

    fn sample_candles(count: usize) -> Vec<Candle> {
        let start = Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap();
        (0..count)
            .map(|index| {
                let drift = index as f64 * 0.35;
                Candle {
                    timestamp: start + Duration::minutes(index as i64),
                    open: 100.0 + drift,
                    high: 100.6 + drift,
                    low: 99.4 + drift,
                    close: 100.3 + drift,
                    volume: 1_000.0 + index as f64,
                }
            })
            .collect()
    }

    #[test]
    fn test_trade_outcome_label_from_pnl() {
        assert_eq!(trade_outcome_label_from_pnl(0.01), "win");
        assert_eq!(trade_outcome_label_from_pnl(-0.01), "loss");
        assert_eq!(trade_outcome_label_from_pnl(0.0), "breakeven");
    }

    #[test]
    fn test_trade_outcome_cpt_snapshot_contains_all_entry_quality_states() {
        let network = build_trading_network().unwrap();
        let snapshot = trade_outcome_cpt_snapshot(&network).unwrap();

        assert!(snapshot.contains_key("high"));
        assert!(snapshot.contains_key("medium"));
        assert!(snapshot.contains_key("low"));
        assert_eq!(snapshot["high"].len(), 3);
    }

    #[test]
    fn test_build_frame_features_for_market_neutralizes_nq_hostile_sweep_bias() {
        let candles = sample_candles(140);
        let baseline = build_frame_features(&candles).unwrap();
        let nq = build_frame_features_for_market(&candles, Some("NQ")).unwrap();

        assert_eq!(nq.market.as_deref(), Some("NQ"));
        if baseline.sweep_count > baseline.fvg_count.saturating_mul(2) {
            assert_eq!(nq.regime_label, "range");
        }
        if baseline.liquidity_label == "hostile" && baseline.fvg_count > 0 {
            assert_eq!(nq.liquidity_label, "neutral");
        }
    }

    #[test]
    fn test_build_frame_features_for_market_applies_market_overrides_conditionally() {
        let candles = sample_candles(140);
        let baseline = build_frame_features(&candles).unwrap();
        let es = build_frame_features_for_market(&candles, Some("ES")).unwrap();
        let ym = build_frame_features_for_market(&candles, Some("YM")).unwrap();
        let gc = build_frame_features_for_market(&candles, Some("GC")).unwrap();
        let cl = build_frame_features_for_market(&candles, Some("CL")).unwrap();

        assert_eq!(es.market.as_deref(), Some("ES"));
        assert_eq!(ym.market.as_deref(), Some("YM"));
        assert_eq!(gc.market.as_deref(), Some("GC"));
        assert_eq!(cl.market.as_deref(), Some("CL"));
        if baseline.regime_label == "range" && baseline.fvg_count > baseline.sweep_count {
            assert_eq!(es.regime_label, "bull");
        }
        if baseline.liquidity_label == "hostile"
            && baseline.fvg_count >= baseline.sweep_count
            && baseline.fvg_count > 0
        {
            assert_eq!(es.liquidity_label, "neutral");
        }
        if baseline.regime_label == "range" && baseline.sweep_count <= baseline.fvg_count {
            assert_eq!(ym.regime_label, "bull");
        }
        if baseline.liquidity_label == "hostile" && baseline.fvg_count > 0 {
            assert_eq!(ym.liquidity_label, "neutral");
        }
        if baseline.regime_label == "range"
            && baseline.fvg_count >= baseline.sweep_count.saturating_add(1)
        {
            assert_eq!(gc.regime_label, "bull");
        }
        if baseline.liquidity_label == "favorable" && baseline.fvg_count > 0 {
            assert_eq!(gc.liquidity_label, "neutral");
        }
        if baseline.regime_label == "bear" && baseline.sweep_count > baseline.fvg_count {
            assert_eq!(cl.regime_label, "range");
        }
        if baseline.liquidity_label == "favorable" && baseline.sweep_count >= 1 {
            assert_eq!(cl.liquidity_label, "neutral");
        }
    }

    #[test]
    fn test_parse_symbol_supports_gc_and_cl() {
        assert!(matches!(parse_symbol("GC"), Symbol::GC));
        assert!(matches!(parse_symbol("CL"), Symbol::CL));
    }

    #[test]
    fn test_emit_human_report_mentions_market_family_surface() {
        let price = "能源结构偏向：空头占优，但随时防剧烈反抽。这类盘最怕突发冲击，先防假突破和急反转；原始标签=bearish_price_action。";
        let technical = "能源技术面：指标易被波动放大，先看节奏是否稳定，再看趋势是否继续；原始标签=technicals_mixed。";
        let smt = "能源联动面：相关市场常会同步放大波动，若联动发散，先减信号强度；原始标签=paired_markets_offer_mixed_confirmation。";
        let regime = format!(
            "能源品种视角：regime={} liquidity={} direction={:?}。当前更该尊重波动冲击与状态切换，先防急拉急杀再谈延续；subgraph={}",
            "bull",
            "neutral",
            Direction::Bull,
            "energy_transition_subgraph"
        );
        assert!(price.contains("能源结构偏向"));
        assert!(technical.contains("能源技术面"));
        assert!(smt.contains("能源联动面"));
        assert!(regime.contains("能源品种视角"));
        assert!(regime.contains("subgraph=energy_transition_subgraph"));
    }
    #[test]
    fn test_live_inferable_defaults_cover_gc_and_cl() {
        let defaults = BTreeMap::from([
            (
                "GC".to_string(),
                BTreeMap::from([
                    ("futures_symbol".to_string(), "GC=F".to_string()),
                    ("spot_symbol".to_string(), "GLD".to_string()),
                    ("options_symbol".to_string(), "GLD".to_string()),
                    ("spot_kind".to_string(), "etf".to_string()),
                ]),
            ),
            (
                "CL".to_string(),
                BTreeMap::from([
                    ("futures_symbol".to_string(), "CL=F".to_string()),
                    ("spot_symbol".to_string(), "USO".to_string()),
                    ("options_symbol".to_string(), "USO".to_string()),
                    ("spot_kind".to_string(), "etf".to_string()),
                ]),
            ),
        ]);
        assert_eq!(defaults["GC"]["futures_symbol"], "GC=F");
        assert_eq!(defaults["CL"]["spot_symbol"], "USO");
    }

    #[test]
    fn test_analyze_live_symbol_can_infer_gc_and_cl_defaults() {
        let gc = match "GC" {
            "GC" => Some(("GC=F", "GLD", "GLD", "etf")),
            _ => None,
        }
        .unwrap();
        let cl = match "CL" {
            "CL" => Some(("CL=F", "USO", "USO", "etf")),
            _ => None,
        }
        .unwrap();
        assert_eq!(gc.0, "GC=F");
        assert_eq!(gc.1, "GLD");
        assert_eq!(cl.0, "CL=F");
        assert_eq!(cl.1, "USO");
    }

    #[test]
    fn test_pre_bayes_market_policy_overrides_apply_market_profiles() {
        let policy = pre_bayes_evidence_policy();
        let diagnostics = FactorDiagnostics {
            alignment_label: "bullish".to_string(),
            uncertainty_label: "low".to_string(),
            long_support: 0.82,
            short_support: 0.18,
            uncertainty: 0.20,
            ..FactorDiagnostics::default()
        };
        let multi_timeframe_evidence = ParsedMultiTimeframeEvidence {
            direction_bias: "bullish".to_string(),
            alignment_score: Some(0.80),
            entry_alignment_score: Some(0.78),
            ..ParsedMultiTimeframeEvidence::default()
        };

        let generic = build_pre_bayes_evidence_filter(
            &policy,
            "bull",
            "hostile",
            &diagnostics,
            &multi_timeframe_evidence,
            None,
        );
        let es = build_pre_bayes_evidence_filter(
            &policy,
            "bull",
            "hostile",
            &diagnostics,
            &multi_timeframe_evidence,
            Some("ES"),
        );
        let ym = build_pre_bayes_evidence_filter(
            &policy,
            "bull",
            "hostile",
            &diagnostics,
            &multi_timeframe_evidence,
            Some("YM"),
        );
        let gc = build_pre_bayes_evidence_filter(
            &policy,
            "bull",
            "hostile",
            &diagnostics,
            &multi_timeframe_evidence,
            Some("GC"),
        );

        assert_eq!(generic.filtered_factor_uncertainty, "high");
        assert_eq!(es.filtered_factor_uncertainty, "low");
        assert_eq!(ym.filtered_factor_uncertainty, "low");
        assert_eq!(gc.filtered_factor_uncertainty, "low");
        assert!(es.evidence_quality_score > generic.evidence_quality_score);
        assert!(ym.evidence_quality_score > generic.evidence_quality_score);
        assert!(gc.evidence_quality_score > generic.evidence_quality_score);
        assert!(es
            .rationale
            .iter()
            .any(|line| line.contains("market_policy=ES")));
        assert!(ym
            .rationale
            .iter()
            .any(|line| line.contains("market_policy=YM")));
        assert!(gc
            .rationale
            .iter()
            .any(|line| line.contains("market_policy=GC")));
    }

    #[test]
    fn test_canonical_shadow_status_defaults_to_unavailable_without_shadow() {
        let summary = None::<ict_engine::domain::belief::ShadowComparisonSummary>;
        let status = summary
            .as_ref()
            .map(|item| item.status.clone())
            .unwrap_or_else(|| "shadow=unavailable".to_string());
        assert_eq!(status, "shadow=unavailable");
    }

    #[test]
    fn test_run_factor_research_persists_rankings_and_run_record() {
        let temp = tempfile::tempdir().unwrap();
        let data = temp.path().join("candles.json");
        std::fs::write(
            &data,
            serde_json::to_string(&serde_json::json!({
                "candles": sample_candles(140)
            }))
            .unwrap(),
        )
        .unwrap();

        let report = run_factor_research(
            "NQ",
            data.to_str().unwrap(),
            ResearchObjectiveMode::Generic,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            temp.path().to_str().unwrap(),
        )
        .unwrap();
        let learning_state = load_learning_state(temp.path(), "NQ").unwrap();
        let runs: Vec<ResearchRunRecord> =
            load_state(temp.path(), "NQ", ict_engine::state::RESEARCH_RUNS_FILE).unwrap();
        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();

        assert!(!report.backtest.scorecards.is_empty());
        assert!(!learning_state.factor_rankings.is_empty());
        assert_eq!(report.research_objective, "generic");
        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].research_objective, "generic");
        let ensemble: EnsembleVoteRecord =
            load_state(temp.path(), "NQ", ict_engine::state::ENSEMBLE_VOTE_FILE).unwrap();
        assert_eq!(ensemble.symbol, "NQ");
        assert_eq!(ensemble.source_phase, "factor-research");
        assert!(snapshot.latest_research.is_some());
        assert!(snapshot.latest_ensemble_vote.is_some());
        assert_eq!(snapshot.current_focus_phase, "research");
        assert!(snapshot
            .latest_research
            .as_ref()
            .unwrap()
            .phase_summary
            .contains("objective=generic"));
    }

    #[test]
    fn test_train_command_persists_train_run_and_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        for interval in MULTI_TIMEFRAME_INTERVALS {
            let dir = temp.path().join(format!("cleaned-{}", interval));
            std::fs::create_dir_all(&dir).unwrap();
            std::fs::write(
                dir.join(format!("nq.continuous-{}.json", interval)),
                serde_json::to_string(&CleanedCandleOutput {
                    symbol: "NQ".to_string(),
                    candles: sample_candles(40),
                })
                .unwrap(),
            )
            .unwrap();
        }
        let primary = temp
            .path()
            .join("cleaned-15m")
            .join("nq.continuous-15m.json");

        train_command(
            "NQ",
            primary.to_str().unwrap(),
            5,
            temp.path().to_str().unwrap(),
        )
        .unwrap();

        let runs: Vec<TrainRunRecord> =
            load_state(temp.path(), "NQ", ict_engine::state::TRAIN_RUNS_FILE).unwrap();
        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();

        assert_eq!(runs.len(), 1);
        assert!(runs[0].observations > 0);
        assert!(!runs[0].multi_timeframe_summary.is_empty());
        assert!(snapshot.latest_train.is_some());
    }

    #[test]
    fn test_run_factor_backtest_persists_backtest_run_and_agent_bundle() {
        let temp = tempfile::tempdir().unwrap();
        let data = temp.path().join("candles.json");
        std::fs::write(
            &data,
            serde_json::to_string(&serde_json::json!({
                "candles": sample_candles(140)
            }))
            .unwrap(),
        )
        .unwrap();

        let report = run_factor_backtest(
            "NQ",
            data.to_str().unwrap(),
            None,
            temp.path().to_str().unwrap(),
        )
        .unwrap();
        let learning_state = load_learning_state(temp.path(), "NQ").unwrap();
        let runs: Vec<BacktestRunRecord> =
            load_state(temp.path(), "NQ", ict_engine::state::BACKTEST_RUNS_FILE).unwrap();
        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();

        assert!(!report.factor_family_decisions.is_empty());
        assert!(!report.agent_action_plan.items.is_empty());
        assert!(!report.final_trade_outcome_cpt.is_empty());
        assert!(!learning_state.feedback_history.is_empty());
        assert_eq!(runs.len(), 1);
        assert_eq!(
            runs[0].recommended_next_command,
            report.recommended_next_command
        );
        assert!(!runs[0].agent_prompts.prompts.is_empty());
        assert!(!runs[0].agent_context_bundle.stage_views.is_empty());
        assert!(snapshot.latest_backtest.is_some());
        assert_eq!(snapshot.current_focus_phase, "backtest");
    }

    #[test]
    fn test_analyze_command_persists_analyze_run() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");

        for (path, count) in [(&htf, 220usize), (&mtf, 180usize), (&ltf, 140usize)] {
            std::fs::write(
                path,
                serde_json::to_string(&serde_json::json!({
                    "candles": sample_candles(count)
                }))
                .unwrap(),
            )
            .unwrap();
        }

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();

        let runs: Vec<AnalyzeRunRecord> =
            load_state(temp.path(), "NQ", ict_engine::state::ANALYZE_RUNS_FILE).unwrap();
        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();

        assert_eq!(runs.len(), 1);
        assert_eq!(runs[0].source_command, "analyze");
        assert!(!runs[0].recommended_next_command.is_empty());
        assert_eq!(runs[0].promotion_decision.status, "observe");
        assert_eq!(runs[0].rollback_recommendation.scope, "none");
        assert!(!runs[0].factor_family_decisions.is_empty());
        assert!(!runs[0].agent_prompts.prompts.is_empty());
        assert!(!runs[0].agent_context_bundle.stage_views.is_empty());
        let ensemble: EnsembleVoteRecord =
            load_state(temp.path(), "NQ", ict_engine::state::ENSEMBLE_VOTE_FILE).unwrap();
        assert_eq!(ensemble.symbol, "NQ");
        assert_eq!(ensemble.source_phase, "analyze");
        assert!(snapshot.latest_analyze.is_some());
        assert!(snapshot.latest_ensemble_vote.is_some());
        assert_eq!(snapshot.current_focus_phase, "analyze");
    }

    #[test]
    fn test_format_executor_summary_lines_clones_executor_summaries() {
        let lines = format_executor_summary_lines(&[
            "executor=catboost_file action=observe confidence=0.55 weight=0.55".to_string(),
            "executor=xgboost_file action=hold confidence=0.45 weight=0.45".to_string(),
        ]);

        assert_eq!(lines.len(), 2);
        assert!(lines[0].contains("executor=catboost_file"));
        assert!(lines[1].contains("executor=xgboost_file"));
    }

    #[test]
    fn test_emit_analyze_output_includes_executor_scorecard_summary() {
        let temp = tempfile::tempdir().unwrap();
        let htf = sample_candles(220);
        let mtf = sample_candles(180);
        let ltf = sample_candles(140);
        let params = load_or_init_hmm_params("NQ", temp.path().to_str().unwrap());
        let network = load_or_init_trading_network("NQ", temp.path().to_str().unwrap()).unwrap();
        let learning_state = load_learning_state(temp.path(), "NQ").unwrap();
        let report = build_analyze_report(
            "NQ",
            temp.path().to_str().unwrap(),
            &htf,
            &mtf,
            &ltf,
            &params,
            &network,
            AnalyzeBuildContext {
                symbol: "NQ",
                paired_candles: None,
                auxiliary: None,
                learning_state: &learning_state,
                multi_timeframe_summary: &[],
                native_frames: AnalyzeNativeFrames::default(),
            },
        )
        .unwrap();

        let ensemble_vote = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
            symbol: report.symbol.clone(),
            state_dir: None,
            recommended_next_command: report.supporting.recommended_next_command.clone(),
            provenance: report.supporting.provenance.clone(),
            dataset_comparability: report.supporting.dataset_comparability.clone(),
            belief: report.supporting.canonical_belief_report.clone(),
        });
        let summary = format_executor_summary_lines(&ensemble_vote.executor_summaries);

        assert!(!summary.is_empty());
        assert!(summary[0].contains("executor=catboost_file"));
    }

    #[test]
    fn test_factor_research_output_summary_uses_executor_summaries() {
        let temp = tempfile::tempdir().unwrap();
        let data = temp.path().join("candles.json");
        std::fs::write(
            &data,
            serde_json::to_string(&serde_json::json!({
                "candles": sample_candles(140)
            }))
            .unwrap(),
        )
        .unwrap();

        let report = run_factor_research(
            "NQ",
            data.to_str().unwrap(),
            ResearchObjectiveMode::Generic,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            temp.path().to_str().unwrap(),
        )
        .unwrap();
        let ensemble_vote = build_stub_ensemble_vote_from_research(&report);
        let summary = format_executor_summary_lines(&ensemble_vote.executor_summaries);

        assert!(!summary.is_empty());
        assert!(summary
            .iter()
            .any(|line| line.contains("executor=catboost") || line.contains("executor=xgboost")));
    }

    #[test]
    fn test_analyze_command_persists_pending_update_artifact() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");

        for (path, count) in [(&htf, 220usize), (&mtf, 180usize), (&ltf, 140usize)] {
            std::fs::write(
                path,
                serde_json::to_string(&serde_json::json!({
                    "candles": sample_candles(count)
                }))
                .unwrap(),
            )
            .unwrap();
        }

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();

        let artifact: PendingUpdateArtifact = load_state(
            temp.path(),
            "NQ",
            ict_engine::state::PENDING_UPDATE_ARTIFACT_FILE,
        )
        .unwrap();
        assert_eq!(artifact.symbol, "NQ");
        assert_eq!(artifact.source_phase, "analyze");
        assert_eq!(artifact.template_feedback.realized_outcome, "pending");
        assert!(!artifact.template_feedback.factors_used.is_empty());
        assert!(artifact.pre_bayes_evidence_filter.is_some());
        assert!(artifact.pre_bayes_entry_quality_bridge.is_some());
        assert!(!artifact.multi_timeframe_summary.is_empty());
        assert_eq!(artifact.version, 1);
        assert_eq!(artifact.review_decision.status, "promote_latest");
    }

    #[test]
    fn test_pending_update_artifact_history_versions_increment() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");

        for (path, count) in [(&htf, 220usize), (&mtf, 180usize), (&ltf, 140usize)] {
            std::fs::write(
                path,
                serde_json::to_string(&serde_json::json!({
                    "candles": sample_candles(count)
                }))
                .unwrap(),
            )
            .unwrap();
        }

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();
        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();

        let history = load_pending_update_history(temp.path(), "NQ").unwrap();
        assert_eq!(history.len(), 2);
        assert_eq!(history[0].version, 1);
        assert_eq!(history[1].version, 2);
        assert_eq!(history[1].review_decision.status, "discard");
        assert!(history[1].diff_from_previous.comparable_same_data);
        assert!(history[1].diff_from_previous.comparable_same_factor_version);
    }

    #[test]
    fn test_analyze_command_persists_execution_candidate_artifact() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");

        for (path, count) in [(&htf, 220usize), (&mtf, 180usize), (&ltf, 140usize)] {
            std::fs::write(
                path,
                serde_json::to_string(&serde_json::json!({
                    "candles": sample_candles(count)
                }))
                .unwrap(),
            )
            .unwrap();
        }

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();

        let candidate: ExecutionCandidateArtifact = load_state(
            temp.path(),
            "NQ",
            ict_engine::state::EXECUTION_CANDIDATE_FILE,
        )
        .unwrap();
        assert_eq!(candidate.version, 1);
        assert!(!candidate.candidate_status.is_empty());
        assert!(candidate.pre_bayes_evidence_filter.is_some());
        assert!(candidate.pre_bayes_entry_quality_bridge.is_some());
        assert!(!candidate.multi_timeframe_summary.is_empty());
        let snapshot: WorkflowSnapshot =
            load_state(temp.path(), "NQ", ict_engine::state::WORKFLOW_SNAPSHOT_FILE).unwrap();
        assert!(snapshot.latest_execution_candidate.is_some());
    }

    #[test]
    fn test_workflow_status_command_reads_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let snapshot = WorkflowSnapshot {
            symbol: "NQ".to_string(),
            current_focus_phase: "research".to_string(),
            recommended_next_command:
                "ict-engine factor-research --symbol NQ --data ltf.json --state-dir state"
                    .to_string(),
            ..WorkflowSnapshot::default()
        };
        save_workflow_snapshot(temp.path(), "NQ", &snapshot).unwrap();

        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            None,
            false,
            false,
            false,
        )
        .unwrap();
        let loaded = load_workflow_snapshot(temp.path(), "NQ").unwrap();

        assert_eq!(loaded.current_focus_phase, "research");
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("diffs"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("execution-candidate-history"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("ensemble-vote"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("ensemble-vote-history"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("ensemble-scorecards"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            None,
            true,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            None,
            false,
            false,
            true,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-history-summary"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-review-rules"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("agent-bootstrap"),
            false,
            false,
            false,
        )
        .unwrap();
    }

    #[test]
    fn test_workflow_snapshot_contains_actionable_and_promotable_artifacts() {
        let pending = PendingUpdateArtifact {
            artifact_id: "pending-1".to_string(),
            version: 1,
            generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("analyze:1".to_string()),
            decision_hint: "hint".to_string(),
            review_decision: PendingUpdateArtifactDecision {
                status: "promote_latest".to_string(),
                reason: "strict_probability_and_score_improvement".to_string(),
                supersedes_artifact_id: None,
            },
            ..PendingUpdateArtifact::default()
        };
        let execution = ExecutionCandidateArtifact {
            artifact_id: "candidate-1".to_string(),
            version: 1,
            generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 1, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("analyze:1".to_string()),
            decision_hint: "hint".to_string(),
            trade_direction: Direction::Bull,
            actionable: true,
            candidate_status: "ready".to_string(),
            ..ExecutionCandidateArtifact::default()
        };

        let snapshot = build_workflow_snapshot(
            "state",
            "NQ",
            None,
            None,
            None,
            None,
            None,
            &[],
            &[pending],
            &[execution],
            &[
                ArtifactLedgerEntry {
                    entry_id: "ledger:pending-1".to_string(),
                    artifact_kind: "pending_update".to_string(),
                    artifact_id: "pending-1".to_string(),
                    version: 1,
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                    symbol: "NQ".to_string(),
                    source_phase: "analyze".to_string(),
                    source_run_id: Some("analyze:1".to_string()),
                    path: "state/NQ/pending_update_feedback.json".to_string(),
                    status: "promote_latest".to_string(),
                    promote_candidate: true,
                    actionable: true,
                    decision_hint: "hint".to_string(),
                    review_reason: "strict_probability_and_score_improvement".to_string(),
                    review_rule_version: "rules-v1".to_string(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("keep".to_string()),
                    family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.72)]),
                    supersedes_artifact_id: None,
                    quality_score: 80,
                    consumed_by_update_run_id: None,
                    consumed_at: None,
                    consumed_outcome: None,
                    regraded_at: None,
                    consumption_regrade_status: None,
                    consumption_regrade_reason: None,
                },
                ArtifactLedgerEntry {
                    entry_id: "ledger:candidate-1".to_string(),
                    artifact_kind: "execution_candidate".to_string(),
                    artifact_id: "candidate-1".to_string(),
                    version: 1,
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 1, 0, 0).unwrap(),
                    symbol: "NQ".to_string(),
                    source_phase: "analyze".to_string(),
                    source_run_id: Some("analyze:1".to_string()),
                    path: "state/NQ/execution_candidate.json".to_string(),
                    status: "ready".to_string(),
                    promote_candidate: true,
                    actionable: true,
                    decision_hint: "hint".to_string(),
                    review_reason: "low".to_string(),
                    review_rule_version: "rules-v1".to_string(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("keep".to_string()),
                    family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.72)]),
                    supersedes_artifact_id: None,
                    quality_score: 70,
                    consumed_by_update_run_id: None,
                    consumed_at: None,
                    consumed_outcome: None,
                    regraded_at: None,
                    consumption_regrade_status: None,
                    consumption_regrade_reason: None,
                },
            ],
        );

        assert_eq!(snapshot.actionable_artifacts.len(), 2);
        assert!(snapshot.latest_promotable_artifact.is_some());
        assert!(!snapshot.artifact_factor_trends.is_empty());
        assert!(!snapshot.artifact_family_trends.is_empty());
        assert!(!snapshot.artifact_lineage_summaries.is_empty());
        assert!(
            snapshot
                .artifact_review_rules
                .pending_update
                .require_same_data
        );
        assert!(!snapshot
            .artifact_review_rule_sources
            .pending_update
            .is_empty());
    }

    #[test]
    fn test_artifact_status_and_diff_commands_run() {
        let temp = tempfile::tempdir().unwrap();
        append_artifact_ledger_entry(
            temp.path(),
            "NQ",
            ArtifactLedgerEntry {
                entry_id: "ledger:pending-1".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "pending-1".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                path: "state/NQ/pending_update_feedback.json".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: true,
                decision_hint: "hint".to_string(),
                review_reason: "strict_probability_and_score_improvement".to_string(),
                review_rule_version: "rules-v1".to_string(),
                top_factor_name: Some("trend_momentum".to_string()),
                top_factor_action: Some("tune".to_string()),
                family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.45)]),
                supersedes_artifact_id: None,
                quality_score: 80,
                consumed_by_update_run_id: None,
                consumed_at: None,
                consumed_outcome: None,
                regraded_at: None,
                consumption_regrade_status: None,
                consumption_regrade_reason: None,
            },
        )
        .unwrap();
        append_artifact_ledger_entry(
            temp.path(),
            "NQ",
            ArtifactLedgerEntry {
                entry_id: "ledger:pending-2".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "pending-2".to_string(),
                version: 2,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 1, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:2".to_string()),
                path: "state/NQ/pending_update_feedback.json".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: true,
                decision_hint: "hint-2".to_string(),
                review_reason: "strict_probability_and_score_improvement".to_string(),
                review_rule_version: "rules-v1".to_string(),
                top_factor_name: Some("trend_momentum".to_string()),
                top_factor_action: Some("keep".to_string()),
                family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.74)]),
                supersedes_artifact_id: Some("pending-1".to_string()),
                quality_score: 90,
                consumed_by_update_run_id: None,
                consumed_at: None,
                consumed_outcome: None,
                regraded_at: None,
                consumption_regrade_status: None,
                consumption_regrade_reason: None,
            },
        )
        .unwrap();
        append_pending_update_artifact_history(
            temp.path(),
            "NQ",
            PendingUpdateArtifact {
                artifact_id: "pending-1".to_string(),
                version: 1,
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                entry_quality: "high".to_string(),
                factor_alignment: "bullish".to_string(),
                factor_uncertainty: "low".to_string(),
                selected_win_probability: 0.64,
                top_factor_score: 0.72,
                avg_family_score: 0.68,
                ..PendingUpdateArtifact::default()
            },
        )
        .unwrap();
        append_pending_update_artifact_history(
            temp.path(),
            "NQ",
            PendingUpdateArtifact {
                artifact_id: "pending-2".to_string(),
                version: 2,
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:2".to_string()),
                entry_quality: "high".to_string(),
                factor_alignment: "bullish".to_string(),
                factor_uncertainty: "low".to_string(),
                selected_win_probability: 0.69,
                top_factor_score: 0.80,
                avg_family_score: 0.74,
                ..PendingUpdateArtifact::default()
            },
        )
        .unwrap();

        artifact_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            Some("pending_update"),
            true,
            false,
            false,
            "generated",
            true,
            None,
            None,
            false,
            false,
            "kind",
            None,
        )
        .unwrap();
        artifact_diff_command(
            "NQ",
            temp.path().to_str().unwrap(),
            "pending-1",
            "pending-2",
        )
        .unwrap();
        artifact_lineage_command(
            "NQ",
            temp.path().to_str().unwrap(),
            Some("pending-2"),
            false,
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-factor-trends"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-lineage-summaries"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-decision-summary"),
            false,
            false,
            false,
        )
        .unwrap();
        artifact_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            Some("pending_update"),
            false,
            false,
            true,
            "generated",
            true,
            None,
            None,
            false,
            false,
            "kind",
            None,
        )
        .unwrap();
        artifact_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            Some("pending_update"),
            false,
            false,
            false,
            "quality",
            true,
            Some(1),
            None,
            false,
            false,
            "kind",
            None,
        )
        .unwrap();
        artifact_lineage_command(
            "NQ",
            temp.path().to_str().unwrap(),
            None,
            false,
            false,
            false,
            true,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-impact-leaderboard"),
            false,
            false,
            false,
        )
        .unwrap();
        workflow_status_command(
            "NQ",
            temp.path().to_str().unwrap(),
            false,
            Some("artifact-impact-consumed-trend"),
            false,
            false,
            false,
        )
        .unwrap();
        pre_bayes_status_command("NQ", temp.path().to_str().unwrap(), false, Some("policy"))
            .unwrap();
    }

    #[test]
    fn test_artifact_diff_view_includes_lineage_chain() {
        let temp = tempfile::tempdir().unwrap();
        append_artifact_ledger_entry(
            temp.path(),
            "NQ",
            ArtifactLedgerEntry {
                entry_id: "ledger:pending-1".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "pending-1".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:1".to_string()),
                path: "state/NQ/pending_update_feedback.json".to_string(),
                status: "observe".to_string(),
                promote_candidate: false,
                actionable: true,
                decision_hint: "hint-1".to_string(),
                review_reason: "observe".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: Some("trend_momentum".to_string()),
                top_factor_action: Some("tune".to_string()),
                family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.45)]),
                supersedes_artifact_id: None,
                quality_score: 40,
                consumed_by_update_run_id: None,
                consumed_at: None,
                consumed_outcome: None,
                regraded_at: None,
                consumption_regrade_status: None,
                consumption_regrade_reason: None,
            },
        )
        .unwrap();
        append_artifact_ledger_entry(
            temp.path(),
            "NQ",
            ArtifactLedgerEntry {
                entry_id: "ledger:pending-2".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "pending-2".to_string(),
                version: 2,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 1, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: Some("analyze:2".to_string()),
                path: "state/NQ/pending_update_feedback.json".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: true,
                decision_hint: "hint-2".to_string(),
                review_reason: "promote".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: Some("trend_momentum".to_string()),
                top_factor_action: Some("keep".to_string()),
                family_scores: BTreeMap::from([("trend_momentum".to_string(), 0.72)]),
                supersedes_artifact_id: Some("pending-1".to_string()),
                quality_score: 80,
                consumed_by_update_run_id: None,
                consumed_at: None,
                consumed_outcome: None,
                regraded_at: None,
                consumption_regrade_status: None,
                consumption_regrade_reason: None,
            },
        )
        .unwrap();
        append_pending_update_artifact_history(
            temp.path(),
            "NQ",
            PendingUpdateArtifact {
                artifact_id: "pending-1".to_string(),
                version: 1,
                entry_quality: "medium".to_string(),
                factor_alignment: "mixed".to_string(),
                factor_uncertainty: "low".to_string(),
                selected_win_probability: 0.50,
                top_factor_score: 0.45,
                avg_family_score: 0.45,
                pre_bayes_evidence_filter: Some(PreBayesEvidenceFilter {
                    gating_status: "observe_only".to_string(),
                    policy: ict_engine::state::PreBayesEvidencePolicy {
                        version: "policy-a".to_string(),
                        ..ict_engine::state::PreBayesEvidencePolicy::default()
                    },
                    filtered_multi_timeframe_resonance_label: "mixed".to_string(),
                    ..PreBayesEvidenceFilter::default()
                }),
                pre_bayes_entry_quality_bridge: Some(
                    ict_engine::state::PreBayesEntryQualityBridge {
                        selected_entry_quality: BTreeMap::from([("medium".to_string(), 0.7)]),
                        ..ict_engine::state::PreBayesEntryQualityBridge::default()
                    },
                ),
                multi_timeframe_summary: vec!["higher_timeframe_direction_bias=bullish".to_string()],
                ..PendingUpdateArtifact::default()
            },
        )
        .unwrap();
        append_pending_update_artifact_history(
            temp.path(),
            "NQ",
            PendingUpdateArtifact {
                artifact_id: "pending-2".to_string(),
                version: 2,
                entry_quality: "high".to_string(),
                factor_alignment: "bullish".to_string(),
                factor_uncertainty: "low".to_string(),
                selected_win_probability: 0.70,
                top_factor_score: 0.72,
                avg_family_score: 0.72,
                pre_bayes_evidence_filter: Some(PreBayesEvidenceFilter {
                    gating_status: "pass_hard".to_string(),
                    policy: ict_engine::state::PreBayesEvidencePolicy {
                        version: "policy-b".to_string(),
                        ..ict_engine::state::PreBayesEvidencePolicy::default()
                    },
                    filtered_multi_timeframe_resonance_label: "aligned".to_string(),
                    ..PreBayesEvidenceFilter::default()
                }),
                pre_bayes_entry_quality_bridge: Some(
                    ict_engine::state::PreBayesEntryQualityBridge {
                        selected_entry_quality: BTreeMap::from([("high".to_string(), 0.8)]),
                        long_signal_probability: 0.7,
                        short_signal_probability: 0.3,
                        ..ict_engine::state::PreBayesEntryQualityBridge::default()
                    },
                ),
                multi_timeframe_summary: vec!["higher_timeframe_direction_bias=bearish".to_string()],
                ..PendingUpdateArtifact::default()
            },
        )
        .unwrap();

        let ledger = load_artifact_ledger(temp.path(), "NQ").unwrap();
        let diff = artifact_diff_view_for_pending_update(
            &ledger,
            temp.path().to_str().unwrap(),
            "NQ",
            "pending-1",
            "pending-2",
        )
        .unwrap();

        assert_eq!(diff.lineage_artifact_ids, vec!["pending-1", "pending-2"]);
        assert!(!diff.lineage_numeric_evidence.is_empty());
        assert!(!diff.embedded_pre_bayes_evidence.is_empty());
        assert!(diff
            .embedded_pre_bayes_evidence
            .iter()
            .any(|item| item.contains("pre_bayes_policy_version:policy-a->policy-b")));
    }

    #[test]
    fn test_artifact_lineage_summary_counts_embedded_pre_bayes_changes() {
        let ledger = vec![
            ArtifactLedgerEntry {
                artifact_id: "pending-1".to_string(),
                artifact_kind: "pending_update".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                ..ArtifactLedgerEntry::default()
            },
            ArtifactLedgerEntry {
                artifact_id: "pending-2".to_string(),
                artifact_kind: "pending_update".to_string(),
                version: 2,
                supersedes_artifact_id: Some("pending-1".to_string()),
                generated_at: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                ..ArtifactLedgerEntry::default()
            },
        ];
        let summaries = build_artifact_lineage_summaries_with_embedded_snapshots(
            &ledger,
            &[
                PendingUpdateArtifact {
                    artifact_id: "pending-1".to_string(),
                    pre_bayes_evidence_filter: Some(PreBayesEvidenceFilter {
                        gating_status: "observe_only".to_string(),
                        filtered_multi_timeframe_direction_bias: "bullish".to_string(),
                        policy: ict_engine::state::PreBayesEvidencePolicy {
                            version: "policy-a".to_string(),
                            ..ict_engine::state::PreBayesEvidencePolicy::default()
                        },
                        ..PreBayesEvidenceFilter::default()
                    }),
                    ..PendingUpdateArtifact::default()
                },
                PendingUpdateArtifact {
                    artifact_id: "pending-2".to_string(),
                    pre_bayes_evidence_filter: Some(PreBayesEvidenceFilter {
                        gating_status: "pass_hard".to_string(),
                        filtered_multi_timeframe_direction_bias: "bearish".to_string(),
                        policy: ict_engine::state::PreBayesEvidencePolicy {
                            version: "policy-b".to_string(),
                            ..ict_engine::state::PreBayesEvidencePolicy::default()
                        },
                        ..PreBayesEvidenceFilter::default()
                    }),
                    ..PendingUpdateArtifact::default()
                },
            ],
            &[],
        );

        assert_eq!(summaries.len(), 1);
        assert_eq!(summaries[0].embedded_pre_bayes_change_count, 1);
        assert_eq!(summaries[0].latest_pre_bayes_gate_status, "pass_hard");
        assert_eq!(
            summaries[0].latest_pre_bayes_multi_timeframe_direction_bias,
            "bearish"
        );
    }

    #[test]
    fn test_dataset_comparability_exposes_structured_diff_dimensions() {
        let previous = RunProvenance {
            prompt_version: "prompt-v1".to_string(),
            factor_version: "factor-v1".to_string(),
            config_hash: "config-a".to_string(),
            data_fingerprint: "data-a".to_string(),
        };
        let current = RunProvenance {
            prompt_version: "prompt-v2".to_string(),
            factor_version: "factor-v1".to_string(),
            config_hash: "config-b".to_string(),
            data_fingerprint: "data-a".to_string(),
        };

        let comparability =
            dataset_comparability(Some("run-1".to_string()), Some(&previous), &current);

        assert!(comparability.comparable);
        assert!(comparability.same_data);
        assert!(!comparability.same_config);
        assert!(!comparability.same_prompt_version);
        assert!(comparability.same_factor_version);
        assert_eq!(comparability.comparison_class, "same_data_different_config");
    }

    #[test]
    fn test_workflow_snapshot_detects_analyze_update_disagreement() {
        let analyze = AnalyzeRunRecord {
            run_id: "analyze:1".to_string(),
            timestamp: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            selected_direction: Direction::Bull,
            selected_entry_quality: "high".to_string(),
            workflow_state: WorkflowState {
                phase: "observe_or_deploy".to_string(),
                reason: "bull_bias".to_string(),
            },
            recommended_next_command:
                "ict-engine factor-research --symbol NQ --data ltf.json --state-dir state"
                    .to_string(),
            ..AnalyzeRunRecord::default()
        };
        let update = UpdateRunRecord {
            run_id: "update:1".to_string(),
            timestamp: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            ensemble_executor_scorecards: vec![EnsembleExecutorScorecard {
                executor: "catboost_file".to_string(),
                wins: 1,
                ..EnsembleExecutorScorecard::default()
            }],
            rollback_recommendation: RollbackRecommendation {
                should_rollback: true,
                scope: "targeted".to_string(),
                reason: "outcome_calibration_regressed".to_string(),
                target_factors: vec!["trend_momentum".to_string()],
                target_families: Vec::new(),
            },
            workflow_state: WorkflowState {
                phase: "rollback_review".to_string(),
                reason: "outcome_calibration_regressed".to_string(),
            },
            realized_outcome: "loss".to_string(),
            recommended_next_command:
                "ict-engine update --symbol NQ --outcome loss --state-dir state".to_string(),
            ..UpdateRunRecord::default()
        };

        let snapshot = build_workflow_snapshot(
            "state",
            "NQ",
            None,
            Some(&analyze),
            None,
            None,
            Some(&update),
            &[],
            &[],
            &[],
            &[],
        );

        assert!(snapshot
            .disagreements
            .iter()
            .any(|item| item.id == "analyze_direction_vs_update_rollback"));
    }

    #[test]
    fn test_workflow_snapshot_exposes_family_factor_conflict_sources() {
        let research = WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            family_states: vec!["trend_momentum:hold:none".to_string()],
            factor_actions: vec!["trend_momentum:replace:0.31".to_string()],
            family_score_map: BTreeMap::from([("trend_momentum".to_string(), 0.41)]),
            factor_score_map: BTreeMap::from([("trend_momentum".to_string(), 0.31)]),
            ..WorkflowPhaseSnapshot::default()
        };
        let backtest = WorkflowPhaseSnapshot {
            phase: "backtest".to_string(),
            family_states: vec!["trend_momentum:promote:none".to_string()],
            factor_actions: vec!["trend_momentum:keep:0.72".to_string()],
            family_score_map: BTreeMap::from([("trend_momentum".to_string(), 0.73)]),
            factor_score_map: BTreeMap::from([("trend_momentum".to_string(), 0.72)]),
            ..WorkflowPhaseSnapshot::default()
        };

        let family_sources = family_conflict_sources(&research, &backtest);
        let factor_sources = factor_conflict_sources(&research, &backtest);

        assert_eq!(family_sources[0].scope, "family");
        assert_eq!(family_sources[0].subject, "trend_momentum");
        assert_eq!(factor_sources[0].scope, "factor");
        assert_eq!(factor_sources[0].subject, "trend_momentum");
        assert!(!family_sources[0].evidence.is_empty());
        assert!(!factor_sources[0].evidence.is_empty());
    }

    #[test]
    fn test_workflow_snapshot_detects_score_vs_artifact_gate_conflict() {
        let research = WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            promotion_status: "promote".to_string(),
            ..WorkflowPhaseSnapshot::default()
        };
        let update = WorkflowPhaseSnapshot {
            phase: "update".to_string(),
            workflow_phase: "artifact_rollback_review".to_string(),
            rollback_scope: "artifact".to_string(),
            ..WorkflowPhaseSnapshot::default()
        };

        let disagreements = workflow_disagreements(&None, &Some(research), &None, &Some(update));

        assert!(disagreements
            .iter()
            .any(|item| item.summary.contains("artifact consumption rollback gate")));
    }

    #[test]
    fn test_workflow_snapshot_detects_pre_bayes_gate_vs_promotion_conflict() {
        let analyze = WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            pre_bayes_gate_status: "observe_only".to_string(),
            pre_bayes_evidence_quality_score: 0.22,
            ..WorkflowPhaseSnapshot::default()
        };
        let research = WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            promotion_status: "promote".to_string(),
            ..WorkflowPhaseSnapshot::default()
        };

        let disagreements = workflow_disagreements(&Some(analyze), &Some(research), &None, &None);

        assert!(disagreements
            .iter()
            .any(|item| item.id.contains("pre_bayes_observe_only")));
    }

    #[test]
    fn test_workflow_disagreement_exposes_pre_bayes_bridge_evidence() {
        let analyze = WorkflowPhaseSnapshot {
            phase: "analyze".to_string(),
            pre_bayes_gate_status: "observe_only".to_string(),
            pre_bayes_uses_soft_evidence: true,
            pre_bayes_policy_version: "policy-v2".to_string(),
            pre_bayes_filtered_assignments: BTreeMap::from([(
                "market_regime".to_string(),
                "range".to_string(),
            )]),
            pre_bayes_soft_evidence: BTreeMap::from([(
                "market_regime".to_string(),
                BTreeMap::from([("bull".to_string(), 0.60), ("range".to_string(), 0.40)]),
            )]),
            pre_bayes_bridge_selected_entry_quality: Some("medium".to_string()),
            pre_bayes_bridge_probability_gap: Some(0.18),
            ..WorkflowPhaseSnapshot::default()
        };
        let research = WorkflowPhaseSnapshot {
            phase: "research".to_string(),
            promotion_status: "promote".to_string(),
            ..WorkflowPhaseSnapshot::default()
        };

        let disagreements = workflow_disagreements(&Some(analyze), &Some(research), &None, &None);
        let disagreement = disagreements
            .iter()
            .find(|item| item.id.contains("pre_bayes_observe_only"))
            .expect("missing observe_only disagreement");

        assert!(disagreement
            .evidence
            .iter()
            .any(|item| item.contains("pre_bayes_bridge_selected_entry_quality=medium")));
        assert!(disagreement
            .evidence
            .iter()
            .any(|item| item.contains("pre_bayes_uses_soft_evidence=true")));
        assert!(disagreement
            .sources
            .iter()
            .any(|item| item.left_value.contains("policy-v2:medium")));
    }

    #[test]
    fn test_futures_sop_report_can_hold_pre_bayes_summary() {
        let report = FuturesSopReport {
            sop_version: "futures-sop-v1".to_string(),
            generated_at: Utc::now(),
            root: "root".to_string(),
            output_dir: "out".to_string(),
            cleaned_dir: "clean".to_string(),
            state_dir: "state".to_string(),
            interval: "15m".to_string(),
            selection_policy: "policy".to_string(),
            clean_report: CleanFuturesReport {
                root: "root".to_string(),
                output_dir: "out".to_string(),
                interval: "15m".to_string(),
                datasets: Vec::new(),
            },
            market_reports: vec![FuturesSopMarketReport {
                market: "NQ".to_string(),
                cleaned_path: "nq.json".to_string(),
                candle_count: 100,
                multi_timeframe_summary: Vec::new(),
                best_factor: Some("structure_ict".to_string()),
                promotion_status: "hold".to_string(),
                rollback_scope: "none".to_string(),
                workflow_phase: "research_iteration".to_string(),
                artifact_gate_status: "no_consumed_validation".to_string(),
                recommended_next_command: "cmd".to_string(),
                aggregate_return: 0.0,
                aggregate_return_warning: None,
                top_scorecards: Vec::new(),
                pipeline: None,
            }],
            global_factor_leaderboard: Vec::new(),
            recommended_global_factor: Some("structure_ict".to_string()),
            recommended_global_pre_bayes_policy: Some(pre_bayes_evidence_policy()),
            recommended_global_pre_bayes_entry_quality_bridge: Some(
                ict_engine::state::PreBayesEntryQualityBridge::default(),
            ),
            recommended_global_pre_bayes_summary: vec!["summary".to_string()],
            recommended_global_pre_bayes_policy_lineage: Some(
                ict_engine::state::PreBayesPolicyLineageSummary::default(),
            ),
            recommended_global_pre_bayes_soft_evidence_diff: Vec::new(),
            recommended_global_pipeline_debug: None,
            recommended_market_factors: BTreeMap::new(),
            warnings: Vec::new(),
            recommended_commands: Vec::new(),
        };

        assert_eq!(
            report.recommended_global_pre_bayes_summary,
            vec!["summary".to_string()]
        );
    }

    #[test]
    fn test_build_factor_pipeline_debug_report_contains_required_trace_fields() {
        let mut evidence_assignments = BTreeMap::new();
        evidence_assignments.insert("market_regime".to_string(), "bull".to_string());
        evidence_assignments.insert(
            "liquidity_context".to_string(),
            "sweep_supportive".to_string(),
        );
        evidence_assignments.insert("factor_alignment".to_string(), "aligned".to_string());
        evidence_assignments.insert("factor_uncertainty".to_string(), "stable".to_string());
        evidence_assignments.insert(
            "multi_timeframe_resonance".to_string(),
            "aligned".to_string(),
        );

        let bridge = ict_engine::state::PreBayesEntryQualityBridge {
            long_signal_probability: 0.72,
            short_signal_probability: 0.28,
            selected_entry_quality: BTreeMap::from([
                ("medium".to_string(), 0.35),
                ("high".to_string(), 0.65),
            ]),
            rationale: vec!["bridge_confirms_high".to_string()],
            ..ict_engine::state::PreBayesEntryQualityBridge::default()
        };

        let pipeline = ExpansionFactorPipelineReport {
            factor_name: "structure_ict".to_string(),
            parameters: BTreeMap::from([("lookback".to_string(), 20.0)]),
            latest_signal: ict_engine::application::belief::pipeline_types::ExpansionLatestSignal {
                timestamp: Utc::now(),
                direction: "bull".to_string(),
                value: 0.81,
                confidence: 0.74,
                explanation: "recent_sweep_then_displacement".to_string(),
            },
            probability_support:
                ict_engine::application::belief::pipeline_types::ExpansionProbabilitySupport {
                    long_support: 0.72,
                    short_support: 0.28,
                    support_gap: 0.44,
                    alignment_threshold: 0.10,
                    uncertainty: 0.18,
                    alignment_label: "aligned".to_string(),
                    uncertainty_label: "stable".to_string(),
                    long_entry_bias: vec![0.2, 0.3, 0.5],
                    short_entry_bias: vec![0.5, 0.3, 0.2],
                    bullish_factors: vec![ict_engine::factor_lab::FactorContribution {
                        factor_name: "structure_ict".to_string(),
                        category: "structure".to_string(),
                        direction: Direction::Bull,
                        value: 0.81,
                        confidence: 0.74,
                        weighted_score: 0.72,
                        uncertainty_contribution: 0.05,
                        explanation: "recent_sweep_then_displacement".to_string(),
                    }],
                    bearish_factors: vec![ict_engine::factor_lab::FactorContribution {
                        factor_name: "structure_ict_counterflow".to_string(),
                        category: "structure".to_string(),
                        direction: Direction::Bear,
                        value: -0.22,
                        confidence: 0.40,
                        weighted_score: -0.28,
                        uncertainty_contribution: 0.08,
                        explanation: "late bear expansion overlap".to_string(),
                    }],
                    uncertainty_factors: vec![ict_engine::factor_lab::FactorContribution {
                        factor_name: "multi_timeframe_noise".to_string(),
                        category: "context".to_string(),
                        direction: Direction::Neutral,
                        value: 0.0,
                        confidence: 0.52,
                        weighted_score: 0.0,
                        uncertainty_contribution: 0.18,
                        explanation: "entry window still carries opposing noise".to_string(),
                    }],
                },
            entry_quality_bridge: bridge.clone(),
            bbn_support: ict_engine::application::belief::pipeline_types::ExpansionBbnSupport {
                market_regime_label: "bull".to_string(),
                liquidity_context_label: "sweep_supportive".to_string(),
                evidence_policy: "policy-v2".to_string(),
                pre_bayes_filter: PreBayesEvidenceFilter {
                    raw_multi_timeframe_resonance_label: "mixed".to_string(),
                    filtered_multi_timeframe_resonance_label: "aligned".to_string(),
                    evidence_quality_score: 0.77,
                    gating_status: "pass_hard".to_string(),
                    evidence_assignments: evidence_assignments.clone(),
                    soft_multi_timeframe_resonance_distribution: BTreeMap::from([
                        ("aligned".to_string(), 0.68),
                        ("mixed".to_string(), 0.24),
                        ("dislocated".to_string(), 0.08),
                    ]),
                    ..PreBayesEvidenceFilter::default()
                },
                evidence_assignments,
                raw_market_regime_trace: FactorPipelineLabelSource {
                    label: "bull".to_string(),
                    derivation: "build_frame_features.regime_label".to_string(),
                    evidence: vec!["hmm_regime=bull".to_string()],
                },
                raw_liquidity_context_trace: FactorPipelineLabelSource {
                    label: "sweep_supportive".to_string(),
                    derivation: "build_frame_features.liquidity_label".to_string(),
                    evidence: vec!["frame_liquidity_label=sweep_supportive".to_string()],
                },
                raw_multi_timeframe_resonance_trace: FactorPipelineLabelSource {
                    label: "mixed".to_string(),
                    derivation: "classify_multi_timeframe_resonance".to_string(),
                    evidence: vec!["direction_conflict=false".to_string()],
                },
                entry_quality_base: BTreeMap::new(),
                entry_quality_long: BTreeMap::new(),
                entry_quality_short: BTreeMap::new(),
                trade_outcome_long: BTreeMap::new(),
                trade_outcome_short: BTreeMap::new(),
                selected_direction: "bull".to_string(),
                selected_win_probability: 0.66,
            },
            pipeline_summary: "latest sample clears pre-bayes and bridge".to_string(),
            recommended_actions: vec!["inspect_latest_sample".to_string()],
        };

        let report = build_factor_pipeline_debug_report_v2(
            "NQ",
            "/tmp/nq.json",
            "expansion_manipulation",
            &pipeline.factor_name,
            DebugExpansionLatestSignal {
                timestamp: pipeline.latest_signal.timestamp,
                direction: pipeline.latest_signal.direction.clone(),
                value: pipeline.latest_signal.value,
                confidence: pipeline.latest_signal.confidence,
                explanation: pipeline.latest_signal.explanation.clone(),
            },
            DebugExpansionProbabilitySupport {
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
            DebugExpansionBbnSupport {
                market_regime_label: pipeline.bbn_support.market_regime_label.clone(),
                liquidity_context_label: pipeline.bbn_support.liquidity_context_label.clone(),
                evidence_policy: pipeline.bbn_support.evidence_policy.clone(),
                pre_bayes_filter: pipeline.bbn_support.pre_bayes_filter.clone(),
                evidence_assignments: pipeline.bbn_support.evidence_assignments.clone(),
                raw_market_regime_trace: ict_engine::state::FactorPipelineLabelSource {
                    label: pipeline.bbn_support.raw_market_regime_trace.label.clone(),
                    derivation: pipeline
                        .bbn_support
                        .raw_market_regime_trace
                        .derivation
                        .clone(),
                    evidence: pipeline
                        .bbn_support
                        .raw_market_regime_trace
                        .evidence
                        .clone(),
                },
                raw_liquidity_context_trace: ict_engine::state::FactorPipelineLabelSource {
                    label: pipeline
                        .bbn_support
                        .raw_liquidity_context_trace
                        .label
                        .clone(),
                    derivation: pipeline
                        .bbn_support
                        .raw_liquidity_context_trace
                        .derivation
                        .clone(),
                    evidence: pipeline
                        .bbn_support
                        .raw_liquidity_context_trace
                        .evidence
                        .clone(),
                },
                raw_multi_timeframe_resonance_trace: ict_engine::state::FactorPipelineLabelSource {
                    label: pipeline
                        .bbn_support
                        .raw_multi_timeframe_resonance_trace
                        .label
                        .clone(),
                    derivation: pipeline
                        .bbn_support
                        .raw_multi_timeframe_resonance_trace
                        .derivation
                        .clone(),
                    evidence: pipeline
                        .bbn_support
                        .raw_multi_timeframe_resonance_trace
                        .evidence
                        .clone(),
                },
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
            &[
                "1m bull continuation".to_string(),
                "5m aligned".to_string(),
                "15m displacement confirmed".to_string(),
                "1h bullish structure".to_string(),
                "4h premium reprice".to_string(),
                "1d higher-timeframe support".to_string(),
            ],
            BTreeMap::from([
                (
                    "market_regime".to_string(),
                    pipeline.bbn_support.market_regime_label.clone(),
                ),
                (
                    "liquidity_context".to_string(),
                    pipeline.bbn_support.liquidity_context_label.clone(),
                ),
                (
                    "factor_alignment".to_string(),
                    pipeline.probability_support.alignment_label.clone(),
                ),
                (
                    "factor_uncertainty".to_string(),
                    pipeline.probability_support.uncertainty_label.clone(),
                ),
                (
                    "multi_timeframe_resonance".to_string(),
                    pipeline
                        .bbn_support
                        .pre_bayes_filter
                        .raw_multi_timeframe_resonance_label
                        .clone(),
                ),
            ]),
            pre_bayes_soft_evidence_diff(&pipeline.bbn_support.pre_bayes_filter),
            0.12,
        )
        .unwrap();

        assert_eq!(report.symbol, "NQ");
        assert_eq!(report.factor_name, "structure_ict");
        assert_eq!(report.objective, "expansion_manipulation");
        assert_eq!(report.gating_status, "pass_hard");
        assert_eq!(report.selected_entry_quality, "high");
        assert_eq!(report.factor_diagnostics.support_gap, 0.44);
        assert_eq!(report.factor_diagnostics.alignment_threshold, 0.10);
        assert_eq!(report.factor_diagnostics.bullish_factors.len(), 1);
        assert_eq!(report.factor_diagnostics.bearish_factors.len(), 1);
        assert_eq!(report.factor_diagnostics.uncertainty_factors.len(), 1);
        assert_eq!(report.raw_label_trace.market_regime.label, "bull");
        assert_eq!(
            report.raw_label_trace.market_regime.derivation,
            "build_frame_features.regime_label"
        );
        assert_eq!(
            report.raw_label_trace.liquidity_context.label,
            "sweep_supportive"
        );
        assert_eq!(
            report.raw_label_trace.multi_timeframe_resonance.label,
            "mixed"
        );
        assert!(report.bridge_gap > 0.0);
        assert_eq!(
            report
                .raw_pre_bayes_labels
                .get("multi_timeframe_resonance")
                .map(String::as_str),
            Some("mixed")
        );
        assert_eq!(
            report
                .filtered_pre_bayes_labels
                .get("multi_timeframe_resonance")
                .map(String::as_str),
            Some("aligned")
        );
        assert_eq!(report.six_timeframe_resonance.len(), 6);
    }

    #[test]
    fn test_expansion_sop_report_recommended_commands_include_objective_and_debug() {
        let report = ExpansionSopReport {
            sop_version: "expansion-sop-v1".to_string(),
            generated_at: Utc::now(),
            root: "/tmp/root".to_string(),
            output_dir: "/tmp/out".to_string(),
            cleaned_dir: "/tmp/out/cleaned-15m".to_string(),
            interval: "15m".to_string(),
            expansion_lookback: 20,
            expansion_atr_multiplier: 1.5,
            clean_report: CleanFuturesReport {
                root: "/tmp/root".to_string(),
                output_dir: "/tmp/out".to_string(),
                interval: "15m".to_string(),
                datasets: Vec::new(),
            },
            market_reports: Vec::new(),
            global_factor_leaderboard: Vec::new(),
            recommended_global_factor: Some("structure_ict".to_string()),
            recommended_global_pre_bayes_policy: None,
            recommended_global_pre_bayes_entry_quality_bridge: None,
            recommended_global_pre_bayes_summary: Vec::new(),
            recommended_global_pre_bayes_policy_lineage: None,
            recommended_global_pre_bayes_soft_evidence_diff: Vec::new(),
            recommended_global_pipeline_debug: None,
            recommended_market_factors: BTreeMap::new(),
            mutation_spec: None,
            factor_mutation_evaluation: None,
            warnings: Vec::new(),
            recommended_commands: vec![
                "ict-engine expansion-sop --root /tmp/root --output-dir /tmp/out --interval 15m --lookback 20 --atr-multiplier 1.50 --objective expansion_manipulation".to_string(),
                "ict-engine factor-pipeline-debug --symbol NQ --data /tmp/out/cleaned-15m/nq.continuous-15m.json --factor structure_ict --objective expansion_manipulation".to_string(),
            ],
        };

        assert!(report
            .recommended_commands
            .iter()
            .any(|cmd| cmd.contains("--objective expansion_manipulation")));
        assert!(report
            .recommended_commands
            .iter()
            .any(|cmd| cmd.contains("factor-pipeline-debug")));
    }

    #[test]
    fn test_apply_update_outcome_to_executor_scorecards_updates_counts() {
        let mut scorecards = vec![EnsembleExecutorScorecard {
            executor: "catboost_file".to_string(),
            ..EnsembleExecutorScorecard::default()
        }];
        apply_update_outcome_to_executor_scorecards(&mut scorecards, "win", 20);
        assert_eq!(scorecards[0].wins, 1);
        assert_eq!(scorecards[0].validated_positive, 1);
        assert_eq!(scorecards[0].cumulative_quality_score, 20);
    }

    #[test]
    fn test_update_command_records_consumed_artifacts_and_marks_ledger() {
        let temp = tempfile::tempdir().unwrap();
        let htf = temp.path().join("htf.json");
        let mtf = temp.path().join("mtf.json");
        let ltf = temp.path().join("ltf.json");

        for (path, count) in [(&htf, 220usize), (&mtf, 180usize), (&ltf, 140usize)] {
            std::fs::write(
                path,
                serde_json::to_string(&serde_json::json!({
                    "candles": sample_candles(count)
                }))
                .unwrap(),
            )
            .unwrap();
        }

        analyze_command(
            "NQ",
            htf.to_str().unwrap(),
            mtf.to_str().unwrap(),
            ltf.to_str().unwrap(),
            temp.path().to_str().unwrap(),
        )
        .unwrap();
        update_command(
            "NQ",
            "win",
            Some("strong_buy"),
            None,
            temp.path().to_str().unwrap(),
            None,
            None,
            None,
            false,
        )
        .unwrap();

        let runs: Vec<UpdateRunRecord> =
            load_state(temp.path(), "NQ", ict_engine::state::UPDATE_RUNS_FILE).unwrap();
        let ledger = load_artifact_ledger(temp.path(), "NQ").unwrap();

        assert_eq!(runs.len(), 1);
        assert!(runs[0].consumed_pending_update_artifact_id.is_some());
        assert!(runs[0].consumed_execution_candidate_artifact_id.is_some());
        assert!(runs[0].consumed_artifact_path.is_some());
        assert!(runs[0].consumed_analyze_run_id.is_some());
        assert!(runs[0].consumed_pre_bayes_evidence_filter.is_some());
        assert!(!runs[0].consumed_multi_timeframe_summary.is_empty());
        assert!(!runs[0].ensemble_executor_scorecards.is_empty());
        assert!(runs[0]
            .ensemble_executor_scorecards
            .iter()
            .any(|scorecard| !scorecard.executor.is_empty()));
        assert!(ledger.iter().any(|entry| {
            entry.consumed_by_update_run_id.as_deref() == Some(runs[0].run_id.as_str())
        }));
    }

    #[test]
    fn test_build_artifact_consumed_impact_summary_tracks_quality_deltas() {
        let summary = build_artifact_consumed_impact_summary(&[
            ArtifactLedgerEntry {
                entry_id: "a".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "a".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 80,
                consumed_by_update_run_id: Some("u1".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap()),
                consumed_outcome: Some("win".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_positive".to_string()),
                consumption_regrade_reason: Some("ok".to_string()),
            },
            ArtifactLedgerEntry {
                entry_id: "b".to_string(),
                artifact_kind: "execution_candidate".to_string(),
                artifact_id: "b".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "observe".to_string(),
                promote_candidate: false,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 55,
                consumed_by_update_run_id: Some("u2".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap()),
                consumed_outcome: Some("loss".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_negative".to_string()),
                consumption_regrade_reason: Some("bad".to_string()),
            },
        ]);

        assert_eq!(summary.total_consumed, 2);
        assert_eq!(summary.positive_consumed, 1);
        assert_eq!(summary.negative_consumed, 1);
        assert_eq!(summary.points[1].quality_delta_from_previous_consumed, -25);
        assert_eq!(
            summary.by_kind["pending_update"].average_quality_score,
            80.0
        );
        assert!(summary.trend_comparisons.is_empty());
    }

    #[test]
    fn test_build_artifact_consumed_impact_summary_sorts_by_consumed_at_and_builds_windows() {
        let summary = build_artifact_consumed_impact_summary(&[
            ArtifactLedgerEntry {
                entry_id: "late".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "late".to_string(),
                version: 2,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 90,
                consumed_by_update_run_id: Some("u4".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap()),
                consumed_outcome: Some("win".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_positive".to_string()),
                consumption_regrade_reason: Some("good".to_string()),
            },
            ArtifactLedgerEntry {
                entry_id: "early".to_string(),
                artifact_kind: "execution_candidate".to_string(),
                artifact_id: "early".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "observe".to_string(),
                promote_candidate: false,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 40,
                consumed_by_update_run_id: Some("u1".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap()),
                consumed_outcome: Some("loss".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_negative".to_string()),
                consumption_regrade_reason: Some("bad".to_string()),
            },
            ArtifactLedgerEntry {
                entry_id: "mid".to_string(),
                artifact_kind: "pending_update".to_string(),
                artifact_id: "mid".to_string(),
                version: 1,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "promote_latest".to_string(),
                promote_candidate: true,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 65,
                consumed_by_update_run_id: Some("u2".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap()),
                consumed_outcome: Some("neutral".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_neutral".to_string()),
                consumption_regrade_reason: Some("flat".to_string()),
            },
            ArtifactLedgerEntry {
                entry_id: "later".to_string(),
                artifact_kind: "execution_candidate".to_string(),
                artifact_id: "later".to_string(),
                version: 2,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 5, 0, 0, 0).unwrap(),
                symbol: "NQ".to_string(),
                source_phase: "analyze".to_string(),
                source_run_id: None,
                path: "p".to_string(),
                status: "observe".to_string(),
                promote_candidate: false,
                actionable: false,
                decision_hint: "decision_hint_unavailable".to_string(),
                review_reason: "review_reason_unavailable".to_string(),
                review_rule_version: "r1".to_string(),
                top_factor_name: None,
                top_factor_action: None,
                family_scores: BTreeMap::new(),
                supersedes_artifact_id: None,
                quality_score: 88,
                consumed_by_update_run_id: Some("u3".to_string()),
                consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap()),
                consumed_outcome: Some("win".to_string()),
                regraded_at: Some(Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap()),
                consumption_regrade_status: Some("validated_positive".to_string()),
                consumption_regrade_reason: Some("good".to_string()),
            },
        ]);

        assert_eq!(
            summary
                .points
                .iter()
                .map(|point| point.artifact_id.as_str())
                .collect::<Vec<_>>(),
            vec!["early", "mid", "later", "late"]
        );
        assert_eq!(summary.points[3].quality_delta_from_previous_consumed, 2);
        assert!(summary
            .recent_windows
            .iter()
            .any(|window| window.label == "recent_3" && window.count == 3));
        assert!(summary.trend_comparisons.iter().any(|comparison| {
            comparison.label == "recent_3_vs_previous_1"
                && comparison.conclusion == "improving"
                && comparison.average_quality_score_delta > 0.0
        }));
    }

    #[test]
    fn test_artifact_entry_is_rule_break_requires_parent_version_change() {
        let parent = ArtifactLedgerEntry {
            entry_id: "parent".to_string(),
            artifact_kind: "pending_update".to_string(),
            artifact_id: "parent".to_string(),
            version: 1,
            generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: None,
            path: "p".to_string(),
            status: "observe".to_string(),
            promote_candidate: false,
            actionable: false,
            decision_hint: "decision_hint_unavailable".to_string(),
            review_reason: "review_reason_unavailable".to_string(),
            review_rule_version: "rules-v1".to_string(),
            top_factor_name: None,
            top_factor_action: None,
            family_scores: BTreeMap::new(),
            supersedes_artifact_id: None,
            quality_score: 50,
            consumed_by_update_run_id: None,
            consumed_at: None,
            consumed_outcome: None,
            regraded_at: None,
            consumption_regrade_status: None,
            consumption_regrade_reason: None,
        };
        let same = ArtifactLedgerEntry {
            artifact_id: "same".to_string(),
            supersedes_artifact_id: Some("parent".to_string()),
            review_rule_version: "rules-v1".to_string(),
            ..parent.clone()
        };
        let changed = ArtifactLedgerEntry {
            artifact_id: "changed".to_string(),
            supersedes_artifact_id: Some("parent".to_string()),
            review_rule_version: "rules-v2".to_string(),
            ..parent.clone()
        };

        assert!(!artifact_entry_is_rule_break(
            &[parent.clone(), same.clone()],
            &same
        ));
        assert!(artifact_entry_is_rule_break(
            &[parent, changed.clone()],
            &changed
        ));
    }

    #[test]
    fn test_artifact_decision_summary_uses_consumed_validation_signal() {
        let consumed_impact_summary = ict_engine::state::ArtifactConsumedImpactSummary {
            total_consumed: 4,
            trend_comparisons: vec![ict_engine::state::ArtifactConsumedImpactTrendComparison {
                label: "recent_3_vs_previous_1".to_string(),
                recent: ict_engine::state::ArtifactConsumedImpactWindow {
                    label: "recent_3".to_string(),
                    count: 3,
                    positive: 0,
                    negative: 2,
                    neutral: 1,
                    average_quality_score: 41.0,
                    cumulative_quality_delta: -18,
                },
                baseline: ict_engine::state::ArtifactConsumedImpactWindow {
                    label: "previous_1".to_string(),
                    count: 1,
                    positive: 1,
                    negative: 0,
                    neutral: 0,
                    average_quality_score: 83.0,
                    cumulative_quality_delta: 0,
                },
                average_quality_score_delta: -42.0,
                cumulative_quality_delta_delta: -18,
                positive_rate_delta: -1.0,
                conclusion: "regressing".to_string(),
            }],
            by_kind_trend_comparisons: BTreeMap::from([(
                "execution_candidate".to_string(),
                vec![ict_engine::state::ArtifactConsumedImpactTrendComparison {
                    label: "recent_3_vs_previous_1".to_string(),
                    recent: ict_engine::state::ArtifactConsumedImpactWindow {
                        label: "recent_3".to_string(),
                        count: 3,
                        positive: 0,
                        negative: 2,
                        neutral: 1,
                        average_quality_score: 41.0,
                        cumulative_quality_delta: -18,
                    },
                    baseline: ict_engine::state::ArtifactConsumedImpactWindow {
                        label: "previous_1".to_string(),
                        count: 1,
                        positive: 1,
                        negative: 0,
                        neutral: 0,
                        average_quality_score: 83.0,
                        cumulative_quality_delta: 0,
                    },
                    average_quality_score_delta: -42.0,
                    cumulative_quality_delta_delta: -18,
                    positive_rate_delta: -1.0,
                    conclusion: "regressing".to_string(),
                }],
            )]),
            ..ict_engine::state::ArtifactConsumedImpactSummary::default()
        };
        let summary = artifact_decision_summary_from_trends(
            &[ArtifactLedgerEntry {
                artifact_id: "pending-1".to_string(),
                artifact_kind: "pending_update".to_string(),
                actionable: true,
                promote_candidate: true,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                ..ArtifactLedgerEntry::default()
            }],
            Some(&ArtifactLedgerEntry {
                artifact_id: "pending-1".to_string(),
                artifact_kind: "pending_update".to_string(),
                actionable: true,
                promote_candidate: true,
                generated_at: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                ..ArtifactLedgerEntry::default()
            }),
            &[],
            &[],
            &[],
            &consumed_impact_summary,
        );

        assert_eq!(summary.consumed_trend_status, "validated_regressing");
        assert_eq!(summary.promotion_strength, "low");
        assert_eq!(summary.rollback_strength, "high");
        assert!(summary
            .highlighted_actions
            .iter()
            .any(|item| item.contains("consumed:validated_regressing")));
        assert_eq!(
            summary.consumed_target_kinds,
            vec!["execution_candidate".to_string()]
        );
    }

    #[test]
    fn test_derive_decisions_apply_artifact_consumed_gate() {
        let gate = ArtifactConsumedDecisionGate {
            status: "validated_regressing".to_string(),
            reason: "label=recent_3_vs_previous_1 regression_thresholds=(-5.00,-0.25)".to_string(),
            target_kinds: vec!["pending_update".to_string()],
        };
        let promotion = derive_promotion_decision(
            &[PersistedFactorRanking {
                factor_name: "trend_momentum".to_string(),
                composite_score: 0.82,
                conformal_coverage_1sigma: 0.80,
                regime_break_penalty: 0.05,
                ..PersistedFactorRanking::default()
            }],
            &[RankingDiffItem {
                factor_name: "trend_momentum".to_string(),
                score_delta: 0.15,
                ..RankingDiffItem::default()
            }],
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            &decision_thresholds(),
            Some(&gate),
        );
        let rollback = derive_rollback_recommendation(
            &[PersistedFactorRanking {
                factor_name: "trend_momentum".to_string(),
                composite_score: 0.82,
                conformal_coverage_1sigma: 0.80,
                regime_break_penalty: 0.05,
                ..PersistedFactorRanking::default()
            }],
            &[],
            &[],
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            &decision_thresholds(),
            Some(&gate),
        );

        assert!(!promotion.approved);
        assert_eq!(promotion.status, "hold");
        assert!(promotion
            .reason
            .contains("artifact_consumption_validated_regression"));
        assert!(rollback.should_rollback);
        assert_eq!(rollback.scope, "artifact");
        assert!(rollback
            .reason
            .contains("artifact_consumption_validated_regression"));
    }

    #[test]
    fn test_derive_decisions_hold_on_credibility_regression() {
        let rankings = [PersistedFactorRanking {
            factor_name: "fragile_alpha".to_string(),
            composite_score: 0.91,
            conformal_coverage_1sigma: 0.42,
            regime_break_penalty: 0.31,
            ..PersistedFactorRanking::default()
        }];
        let promotion = derive_promotion_decision(
            &rankings,
            &[RankingDiffItem {
                factor_name: "fragile_alpha".to_string(),
                score_delta: 0.20,
                ..RankingDiffItem::default()
            }],
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            &decision_thresholds(),
            None,
        );
        let rollback = derive_rollback_recommendation(
            &rankings,
            &[],
            &[],
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            &decision_thresholds(),
            None,
        );
        assert!(!promotion.approved);
        assert_eq!(promotion.status, "hold");
        assert!(promotion.reason.contains("conformal_coverage_low"));
        assert!(rollback.should_rollback);
        assert!(
            rollback.reason.contains("conformal_coverage_low")
                || rollback.reason.contains("regime_break_penalty_high")
        );
    }

    #[test]
    fn test_derive_family_outcomes_apply_artifact_family_consumed_gate() {
        let outcomes = derive_family_outcomes(
            &[FactorFamilyDecision {
                family: "trend_momentum".to_string(),
                avg_score: 0.78,
                replacement_candidates: Vec::new(),
                actions: vec!["trend_factor:keep".to_string()],
                ..FactorFamilyDecision::default()
            }],
            &decision_thresholds(),
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            Some(&[ict_engine::state::ArtifactFamilyTrendSummary {
                family: "trend_momentum".to_string(),
                consumed_entries: 4,
                consumed_validation_status: "validated_regressing".to_string(),
                consumed_validation_reason:
                    "label=recent_3_vs_previous_1 regression_thresholds=(-5.00,-0.25)".to_string(),
                ..ict_engine::state::ArtifactFamilyTrendSummary::default()
            }]),
        );

        assert_eq!(outcomes[0].promotion_decision.status, "hold");
        assert!(!outcomes[0].promotion_decision.approved);
        assert!(outcomes[0]
            .promotion_decision
            .reason
            .contains("family_artifact_consumption_validated_regression"));
        assert!(outcomes[0].rollback_recommendation.should_rollback);
        assert_eq!(outcomes[0].rollback_recommendation.scope, "family_artifact");
    }

    #[test]
    fn test_augment_action_plan_with_artifact_trends_adds_consumed_validation_item() {
        let mut plan = AgentActionPlan::default();
        let consumed_impact_summary = ict_engine::state::ArtifactConsumedImpactSummary {
            total_consumed: 4,
            trend_comparisons: vec![ict_engine::state::ArtifactConsumedImpactTrendComparison {
                label: "recent_3_vs_previous_1".to_string(),
                recent: ict_engine::state::ArtifactConsumedImpactWindow {
                    label: "recent_3".to_string(),
                    count: 3,
                    positive: 0,
                    negative: 2,
                    neutral: 1,
                    average_quality_score: 41.0,
                    cumulative_quality_delta: -18,
                },
                baseline: ict_engine::state::ArtifactConsumedImpactWindow {
                    label: "previous_1".to_string(),
                    count: 1,
                    positive: 1,
                    negative: 0,
                    neutral: 0,
                    average_quality_score: 83.0,
                    cumulative_quality_delta: 0,
                },
                average_quality_score_delta: -42.0,
                cumulative_quality_delta_delta: -18,
                positive_rate_delta: -1.0,
                conclusion: "regressing".to_string(),
            }],
            by_kind_trend_comparisons: BTreeMap::from([(
                "pending_update".to_string(),
                vec![ict_engine::state::ArtifactConsumedImpactTrendComparison {
                    label: "recent_3_vs_previous_1".to_string(),
                    recent: ict_engine::state::ArtifactConsumedImpactWindow {
                        label: "recent_3".to_string(),
                        count: 3,
                        positive: 0,
                        negative: 2,
                        neutral: 1,
                        average_quality_score: 41.0,
                        cumulative_quality_delta: -18,
                    },
                    baseline: ict_engine::state::ArtifactConsumedImpactWindow {
                        label: "previous_1".to_string(),
                        count: 1,
                        positive: 1,
                        negative: 0,
                        neutral: 0,
                        average_quality_score: 83.0,
                        cumulative_quality_delta: 0,
                    },
                    average_quality_score_delta: -42.0,
                    cumulative_quality_delta_delta: -18,
                    positive_rate_delta: -1.0,
                    conclusion: "regressing".to_string(),
                }],
            )]),
            ..ict_engine::state::ArtifactConsumedImpactSummary::default()
        };

        augment_action_plan_with_artifact_trends(
            &mut plan,
            "NQ",
            "state",
            &[],
            &[],
            &consumed_impact_summary,
        );

        assert!(plan.items.iter().any(|item| {
            item.stage == "artifact_consumption_review"
                && item.blocking
                && item
                    .suggested_commands
                    .iter()
                    .any(|command| command.contains("--symbol NQ"))
                && item
                    .expected_state_changes
                    .iter()
                    .any(|change| change.target == "artifact_kind:pending_update")
        }));
    }

    #[test]
    fn test_concretize_action_plan_commands_replaces_template_commands() {
        let mut plan = AgentActionPlan {
            summary: "test".to_string(),
            items: vec![
                AgentActionItem {
                    stage: "promotion".to_string(),
                    suggested_commands: vec!["ict-engine factor-research --data <file>".to_string()],
                    ..AgentActionItem::default()
                },
                AgentActionItem {
                    stage: "iteration".to_string(),
                    suggested_commands: vec!["ict-engine factor-backtest --data <file>".to_string()],
                    ..AgentActionItem::default()
                },
            ],
        };
        let commands = CommandRecommendations {
            research: RecommendedCommand {
                command:
                    "ict-engine factor-research --symbol NQ --data /tmp/ltf.json --state-dir state"
                        .to_string(),
                ready: true,
                ..RecommendedCommand::default()
            },
            backtest: RecommendedCommand {
                command:
                    "ict-engine factor-backtest --symbol NQ --data /tmp/ltf.json --state-dir state"
                        .to_string(),
                ready: true,
                ..RecommendedCommand::default()
            },
            ..CommandRecommendations::default()
        };

        concretize_action_plan_commands(&mut plan, &commands);

        assert_eq!(
            plan.items[0].suggested_commands[0],
            "ict-engine factor-research --symbol NQ --data /tmp/ltf.json --state-dir state"
        );
        assert_eq!(
            plan.items[1].suggested_commands[0],
            "ict-engine factor-backtest --symbol NQ --data /tmp/ltf.json --state-dir state"
        );
        assert!(plan.items[0]
            .suggested_commands
            .iter()
            .all(|command| !command.contains("<file>")));
    }

    #[test]
    fn test_build_artifact_factor_trends_exposes_consumed_validation() {
        let trends = build_artifact_factor_trends(
            &[
                ArtifactLedgerEntry {
                    artifact_id: "f1".to_string(),
                    artifact_kind: "pending_update".to_string(),
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("keep".to_string()),
                    consumed_by_update_run_id: Some("u1".to_string()),
                    consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap()),
                    consumption_regrade_status: Some("validated_positive".to_string()),
                    quality_score: 85,
                    ..ArtifactLedgerEntry::default()
                },
                ArtifactLedgerEntry {
                    artifact_id: "f2".to_string(),
                    artifact_kind: "pending_update".to_string(),
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("keep".to_string()),
                    consumed_by_update_run_id: Some("u2".to_string()),
                    consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap()),
                    consumption_regrade_status: Some("validated_negative".to_string()),
                    quality_score: 45,
                    ..ArtifactLedgerEntry::default()
                },
                ArtifactLedgerEntry {
                    artifact_id: "f3".to_string(),
                    artifact_kind: "pending_update".to_string(),
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("replace".to_string()),
                    consumed_by_update_run_id: Some("u3".to_string()),
                    consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 3, 0, 0, 0).unwrap()),
                    consumption_regrade_status: Some("validated_negative".to_string()),
                    quality_score: 35,
                    ..ArtifactLedgerEntry::default()
                },
                ArtifactLedgerEntry {
                    artifact_id: "f4".to_string(),
                    artifact_kind: "pending_update".to_string(),
                    generated_at: Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap(),
                    top_factor_name: Some("trend_momentum".to_string()),
                    top_factor_action: Some("replace".to_string()),
                    consumed_by_update_run_id: Some("u4".to_string()),
                    consumed_at: Some(Utc.with_ymd_and_hms(2024, 1, 4, 0, 0, 0).unwrap()),
                    consumption_regrade_status: Some("validated_negative".to_string()),
                    quality_score: 30,
                    ..ArtifactLedgerEntry::default()
                },
            ],
            &None,
            &None,
            &None,
        );

        assert_eq!(trends[0].factor_name, "trend_momentum");
        assert_eq!(trends[0].consumed_validation_status, "validated_regressing");
        assert_eq!(trends[0].decision_status, "rollback_watch");
        assert!(trends[0]
            .consumed_validation_reason
            .contains("regression_thresholds"));
    }

    #[test]
    fn test_append_artifact_decision_prompt_adds_artifact_consumption_prompt() {
        let mut pack = AgentPromptPack::default();
        append_artifact_decision_prompt(
            &mut pack,
            "NQ",
            &ict_engine::state::ArtifactDecisionSection {
                summary: ict_engine::state::ArtifactDecisionSummary {
                    consumed_trend_status: "validated_regressing".to_string(),
                    consumed_trend_reason: "regression".to_string(),
                    consumed_target_kinds: vec!["pending_update".to_string()],
                    ..ict_engine::state::ArtifactDecisionSummary::default()
                },
                top_consumed_trend_comparisons: vec![
                    ict_engine::state::ArtifactConsumedImpactTrendComparison {
                        label: "recent_3_vs_previous_1".to_string(),
                        conclusion: "regressing".to_string(),
                        average_quality_score_delta: -20.0,
                        positive_rate_delta: -0.5,
                        ..ict_engine::state::ArtifactConsumedImpactTrendComparison::default()
                    },
                ],
                ..ict_engine::state::ArtifactDecisionSection::default()
            },
        );

        assert!(pack
            .prompts
            .iter()
            .any(|prompt| prompt.id == "artifact_consumption_review"));
    }

    #[test]
    fn test_build_analyze_agent_prompts_adds_pre_bayes_soft_evidence_prompt() {
        let prompts = build_analyze_agent_prompts(
            "NQ",
            &ProbabilisticDecisionSnapshot {
                long_score: 0.4,
                short_score: 0.2,
                win_prob_long: 0.55,
                win_prob_short: 0.45,
                ict_support_long: 0.4,
                ict_support_short: 0.2,
                selected_direction: Direction::Bull,
                selected_score: 0.4,
                selected_win_probability: 0.55,
                ict_role: "test".to_string(),
            },
            &FactorDiagnostics::default(),
            &PreBayesEvidenceFilter {
                uses_soft_evidence: true,
                filtered_market_regime_label: "range".to_string(),
                filtered_liquidity_context_label: "neutral".to_string(),
                filtered_factor_alignment: "mixed".to_string(),
                filtered_factor_uncertainty: "high".to_string(),
                soft_market_regime_distribution: BTreeMap::from([
                    ("bull".to_string(), 0.2),
                    ("bear".to_string(), 0.2),
                    ("range".to_string(), 0.6),
                ]),
                soft_liquidity_context_distribution: BTreeMap::from([
                    ("favorable".to_string(), 0.2),
                    ("neutral".to_string(), 0.6),
                    ("hostile".to_string(), 0.2),
                ]),
                soft_factor_alignment_distribution: BTreeMap::from([
                    ("bullish".to_string(), 0.2),
                    ("mixed".to_string(), 0.6),
                    ("bearish".to_string(), 0.2),
                ]),
                soft_factor_uncertainty_distribution: BTreeMap::from([
                    ("low".to_string(), 0.3),
                    ("high".to_string(), 0.7),
                ]),
                ..PreBayesEvidenceFilter::default()
            },
            &[],
            &[],
            &FeedbackHistorySummary::default(),
            &TradePlan {
                symbol: Symbol::NQ,
                direction: Direction::Bull,
                entry: 100.0,
                stop_loss: 99.0,
                tp1: 101.0,
                tp2: 102.0,
                tp3: 103.0,
                risk_reward: 1.0,
                kelly_fraction: 0.1,
                position_size: 10.0,
                regime: Regime::ManipulationExpansion,
                posterior: 0.55,
                win_probability: 0.55,
                cascade_bull: ict_engine::types::CascadeResult {
                    direction: Direction::Bull,
                    stopped_at: None,
                    steps: Vec::new(),
                    final_posterior: 0.55,
                },
                cascade_bear: ict_engine::types::CascadeResult {
                    direction: Direction::Bear,
                    stopped_at: None,
                    steps: Vec::new(),
                    final_posterior: 0.45,
                },
                uncertainties: Vec::new(),
            },
            &DatasetComparability::default(),
            "hint",
            &["higher_timeframe_direction_bias=bullish".to_string()],
        );

        assert!(prompts
            .prompts
            .iter()
            .any(|prompt| prompt.id == "pre_bayes_soft_evidence_review"));
        assert!(prompts
            .prompts
            .iter()
            .find(|prompt| prompt.id == "analysis_market_review")
            .map(|prompt| prompt
                .user_prompt
                .contains("higher_timeframe_direction_bias=bullish"))
            .unwrap_or(false));
    }

    #[test]
    fn test_workflow_snapshot_uses_full_ledger_for_actionable_artifacts() {
        let ledger = (0..11)
            .map(|index| ArtifactLedgerEntry {
                artifact_id: format!("artifact-{}", index),
                artifact_kind: if index % 2 == 0 {
                    "pending_update".to_string()
                } else {
                    "execution_candidate".to_string()
                },
                generated_at: Utc
                    .with_ymd_and_hms(2024, 1, 1 + index as u32, 0, 0, 0)
                    .unwrap(),
                actionable: index == 0,
                promote_candidate: index == 0,
                ..ArtifactLedgerEntry::default()
            })
            .collect::<Vec<_>>();

        let snapshot = build_workflow_snapshot(
            "state",
            "NQ",
            None,
            None,
            None,
            None,
            None,
            &[],
            &[],
            &[],
            &ledger,
        );

        assert_eq!(snapshot.recent_artifacts.len(), 10);
        assert_eq!(snapshot.actionable_artifacts.len(), 1);
        assert_eq!(
            snapshot
                .latest_promotable_artifact
                .as_ref()
                .map(|entry| entry.artifact_id.as_str()),
            Some("artifact-0")
        );
        assert!(!snapshot
            .recent_artifacts
            .iter()
            .any(|entry| entry.artifact_id == "artifact-0"));
        assert_eq!(
            snapshot.artifact_decision_summary.consumed_trend_status,
            "no_consumed_validation"
        );
    }

    #[test]
    fn test_command_recommendations_for_live_context_use_persisted_paths() {
        let commands = command_recommendations(&CommandContext {
            symbol: "NQ".to_string(),
            state_dir: "state".to_string(),
            analyze: Some(AnalyzeCommandSource::Live {
                source: LiveDataSourceProvenance {
                    futures_backend: "openbb".to_string(),
                    aux_backend: "openalice".to_string(),
                    futures_base_url: "http://127.0.0.1:8080".to_string(),
                    aux_base_url: "http://127.0.0.1:6901/api/v1".to_string(),
                    futures_symbol: "NQ".to_string(),
                    spot_symbol: "QQQ".to_string(),
                    options_symbol: "QQQ".to_string(),
                    spot_kind: "equity".to_string(),
                    fetched_at: Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                    persisted_htf_path: Some("/tmp/htf.json".to_string()),
                    persisted_h4_path: Some("/tmp/h4.json".to_string()),
                    persisted_mtf_path: Some("/tmp/mtf.json".to_string()),
                    persisted_m5_path: Some("/tmp/m5.json".to_string()),
                    persisted_ltf_path: Some("/tmp/ltf.json".to_string()),
                    persisted_m1_path: Some("/tmp/m1.json".to_string()),
                    persisted_spot_path: Some("/tmp/spot.json".to_string()),
                },
            }),
            research_data: Some("/tmp/ltf.json".to_string()),
            paired_data: Some("/tmp/spot.json".to_string()),
            update_outcome: None,
            update_entry_signal: None,
            update_feedback_file: None,
            user_data_selection_required: true,
        });

        assert!(!commands.research.ready);
        assert!(!commands.backtest.ready);
        assert!(commands.research.command.contains("/tmp/ltf.json"));
        assert!(commands.backtest.command.contains("/tmp/spot.json"));
        assert!(commands.analyze.command.contains("analyze-live"));
        assert!(commands.research.user_data_selection_required);
        assert!(commands.backtest.user_data_selection_required);
        assert!(commands
            .research
            .missing_inputs
            .contains(&"user_selected_historical_data".to_string()));
        assert!(commands
            .research
            .user_data_selection_prompt
            .contains("ask the user"));
        assert!(commands
            .research
            .recorded_data_paths
            .contains(&"/tmp/ltf.json".to_string()));
    }

    #[test]
    fn test_build_feedback_record_keeps_trade_timestamp() {
        let timestamp = Utc.with_ymd_and_hms(2024, 2, 1, 12, 0, 0).unwrap();
        let feedback = build_feedback_record(
            "NQ",
            "test",
            timestamp,
            &FactorDiagnostics {
                bullish_factors: vec![ict_engine::factor_lab::FactorContribution {
                    factor_name: "trend_momentum".to_string(),
                    category: "trend_momentum".to_string(),
                    direction: Direction::Bull,
                    value: 0.7,
                    confidence: 0.8,
                    weighted_score: 0.25,
                    uncertainty_contribution: 0.1,
                    explanation: "test".to_string(),
                }],
                long_support: 0.4,
                short_support: 0.1,
                uncertainty: 0.2,
                ..FactorDiagnostics::default()
            },
            &ProbabilisticDecisionSnapshot {
                long_score: 0.6,
                short_score: 0.3,
                win_prob_long: 0.58,
                win_prob_short: 0.42,
                ict_support_long: 0.7,
                ict_support_short: 0.3,
                selected_direction: Direction::Bull,
                selected_score: 0.6,
                selected_win_probability: 0.58,
                ict_role: "evidence_only_non_deterministic".to_string(),
            },
            0.02,
            "win".to_string(),
            Regime::ManipulationExpansion,
        );

        assert_eq!(feedback.timestamp, timestamp);
        assert_eq!(feedback.factors_used.len(), 1);
    }

    #[test]
    fn test_apply_feedback_to_trade_outcome_network_updates_cpt() {
        let mut network = build_trading_network().unwrap();
        let before = network.nodes["trade_outcome"].cpt.entries[&vec![0, 0, 0]][0];
        let feedback = FeedbackRecord {
            timestamp: Utc.with_ymd_and_hms(2024, 2, 1, 12, 0, 0).unwrap(),
            symbol: "NQ".to_string(),
            source: "factor_research_backtest".to_string(),
            run_id: None,
            trade_id: None,
            prompt_version: None,
            factor_version: None,
            data_fingerprint: None,
            factors_used: vec![FeedbackFactorUsage {
                factor_name: "trend_momentum".to_string(),
                category: "factor_backtest".to_string(),
                direction: Direction::Bull,
                value: 0.8,
                confidence: 0.8,
                weight: 0.3,
                long_support: 0.3,
                short_support: 0.0,
                uncertainty_contribution: 0.1,
            }],
            model_probabilities_before_trade: ModelProbabilitySnapshot {
                selected_direction: Direction::Bull,
                selected_probability: 0.8,
                long_score: 0.3,
                short_score: 0.0,
                win_prob_long: 0.8,
                win_prob_short: 0.0,
                uncertainty: 0.1,
            },
            realized_outcome: "win".to_string(),
            pnl: 0.02,
            regime_at_entry: Regime::ManipulationExpansion,
        };

        let updates = apply_feedback_to_trade_outcome_network(&mut network, &[feedback]).unwrap();
        let after = network.nodes["trade_outcome"].cpt.entries[&vec![0, 0, 0]][0];

        assert_eq!(updates, 1);
        assert!(after > before);
    }

    #[test]
    fn test_build_update_agent_prompts_contains_feedback_review_stage() {
        let prompts = build_update_agent_prompts(
            "NQ",
            &[],
            &[],
            &FeedbackHistorySummary::default(),
            &BTreeMap::from([
                ("win".to_string(), 0.6),
                ("breakeven".to_string(), 0.2),
                ("loss".to_string(), 0.2),
            ]),
            "high",
            "bullish",
            "low",
            "win",
            1,
            None,
            None,
            &[],
        );

        assert!(!prompts.prompts.is_empty());
        assert_eq!(prompts.prompts[0].id, "update_feedback_review");
        assert_eq!(prompts.prompts[0].stage, "feedback_update");
    }

    #[test]
    fn test_dataset_audit_prompt_is_added_to_research_prompt_pack() {
        let prompt = dataset_audit_prompt("NQ", "data.json", None, 140, None, "factor-research");
        assert_eq!(prompt.id, "dataset_audit");
        assert_eq!(prompt.stage, "dataset_audit");
        assert!(prompt.user_prompt.contains("data.json"));
    }

    #[test]
    fn test_ranking_diffs_reports_score_and_weight_changes() {
        let previous = vec![PersistedFactorRanking {
            factor_name: "trend_momentum".to_string(),
            composite_score: 0.40,
            weight: 0.20,
            iteration_action: "tune".to_string(),
            ..PersistedFactorRanking::default()
        }];
        let current = vec![PersistedFactorRanking {
            factor_name: "trend_momentum".to_string(),
            composite_score: 0.65,
            weight: 0.32,
            iteration_action: "keep".to_string(),
            ..PersistedFactorRanking::default()
        }];

        let diff = ranking_diffs(&previous, &current);
        assert_eq!(diff.len(), 1);
        assert!(diff[0].score_delta > 0.0);
        assert!(diff[0].weight_delta > 0.0);
        assert_eq!(diff[0].previous_action.as_deref(), Some("tune"));
        assert_eq!(diff[0].new_action, "keep");
    }

    #[test]
    fn test_probability_diffs_reports_before_after_delta() {
        let previous = Some(BTreeMap::from([
            ("win".to_string(), 0.50),
            ("breakeven".to_string(), 0.20),
            ("loss".to_string(), 0.30),
        ]));
        let current = BTreeMap::from([
            ("win".to_string(), 0.58),
            ("breakeven".to_string(), 0.18),
            ("loss".to_string(), 0.24),
        ]);

        let diff = probability_diffs(&previous, &current);
        assert_eq!(diff.len(), 3);
        assert!(diff
            .iter()
            .any(|item| item.state == "win" && item.delta > 0.0));
        assert!(diff
            .iter()
            .any(|item| item.state == "loss" && item.delta < 0.0));
    }

    #[test]
    fn test_build_analyze_decision_hint_for_non_comparable_data() {
        let hint = build_analyze_decision_hint(
            &DatasetComparability {
                comparable: false,
                previous_run_id: Some("run-1".to_string()),
                reason: "different_data_fingerprint".to_string(),
                comparison_class: "different_data_fingerprint".to_string(),
                ..DatasetComparability::default()
            },
            &[],
            &FactorDiagnostics::default(),
        );
        assert!(hint.contains("observe_only_not_comparable"));
    }

    #[test]
    fn test_resolve_multi_timeframe_inputs_auto_detects_cleaned_siblings() {
        let temp = tempfile::tempdir().unwrap();
        for interval in MULTI_TIMEFRAME_INTERVALS {
            let dir = temp.path().join(format!("cleaned-{}", interval));
            std::fs::create_dir_all(&dir).unwrap();
            std::fs::write(
                dir.join(format!("nq.continuous-{}.json", interval)),
                serde_json::to_string(&CleanedCandleOutput {
                    symbol: "NQ".to_string(),
                    candles: sample_candles(8),
                })
                .unwrap(),
            )
            .unwrap();
        }

        let primary = temp
            .path()
            .join("cleaned-15m")
            .join("nq.continuous-15m.json")
            .to_string_lossy()
            .to_string();
        let resolved = resolve_multi_timeframe_inputs(&primary, None, None, None, None, None, None);
        let summary = build_multi_timeframe_summary(&primary, &resolved).unwrap();

        assert_eq!(resolved.source, "auto_from_cleaned_siblings");
        assert_eq!(resolved.paths.len(), MULTI_TIMEFRAME_INTERVALS.len());
        assert!(summary
            .iter()
            .any(|item| item.contains("covered_intervals=1m,5m,15m,1h,4h,1d")));
    }

    #[test]
    fn test_resolve_analyze_cli_inputs_from_data_root() {
        let temp = tempfile::tempdir().unwrap();
        for interval in ["1d", "1h", "15m"] {
            let dir = temp.path().join(format!("cleaned-{}", interval));
            std::fs::create_dir_all(&dir).unwrap();
            std::fs::write(
                dir.join(format!("nq.continuous-{}.json", interval)),
                serde_json::to_string(&CleanedCandleOutput {
                    symbol: "NQ".to_string(),
                    candles: sample_candles(40),
                })
                .unwrap(),
            )
            .unwrap();
        }

        let (htf, mtf, ltf) = resolve_analyze_cli_inputs(
            "NQ",
            None,
            None,
            None,
            Some(temp.path().to_str().unwrap()),
            None,
        )
        .unwrap();

        assert!(htf.ends_with("cleaned-1d/nq.continuous-1d.json"));
        assert!(mtf.ends_with("cleaned-1h/nq.continuous-1h.json"));
        assert!(ltf.ends_with("cleaned-15m/nq.continuous-15m.json"));
    }

    #[test]
    fn test_build_analyze_multi_timeframe_section_parses_summary() {
        let section = build_analyze_multi_timeframe_section(
            &[
                "multi_timeframe_source=auto_from_cleaned_siblings covered_intervals=1m,5m,15m,1h,4h,1d"
                    .to_string(),
                "higher_timeframe_direction_bias=bullish".to_string(),
                "higher_timeframe_alignment_score=0.7500".to_string(),
                "lower_timeframe_entry_alignment_score=0.6200".to_string(),
                "1d:40 bars path=/tmp/1d.json".to_string(),
                "15m:120 bars path=/tmp/15m.json".to_string(),
            ],
            Some(&PreBayesEvidenceFilter {
                filtered_multi_timeframe_resonance_label: "aligned".to_string(),
                ..PreBayesEvidenceFilter::default()
            }),
        );

        assert_eq!(section.direction_bias, "bullish");
        assert_eq!(section.alignment_score, Some(0.75));
        assert_eq!(section.entry_alignment_score, Some(0.62));
        assert_eq!(section.resonance_label, "aligned");
        assert_eq!(section.intervals.len(), 2);
    }

    #[test]
    fn test_build_multi_timeframe_training_observations_uses_all_intervals() {
        let temp = tempfile::tempdir().unwrap();
        for interval in MULTI_TIMEFRAME_INTERVALS {
            let dir = temp.path().join(format!("cleaned-{}", interval));
            std::fs::create_dir_all(&dir).unwrap();
            std::fs::write(
                dir.join(format!("nq.continuous-{}.json", interval)),
                serde_json::to_string(&CleanedCandleOutput {
                    symbol: "NQ".to_string(),
                    candles: sample_candles(40),
                })
                .unwrap(),
            )
            .unwrap();
        }

        let primary = temp
            .path()
            .join("cleaned-15m")
            .join("nq.continuous-15m.json")
            .to_string_lossy()
            .to_string();
        let (observations, summary, candles_total) =
            build_multi_timeframe_training_observations(&primary).unwrap();

        assert!(candles_total >= 40 * MULTI_TIMEFRAME_INTERVALS.len());
        assert!(!observations.is_empty());
        assert!(summary
            .iter()
            .any(|item| item.contains("train_multi_timeframe_source=auto_from_cleaned_siblings")));
    }

    #[test]
    fn test_find_tomac_root_from_candidates_requires_tomac_layout() {
        let temp = tempfile::tempdir().unwrap();
        let invalid = temp.path().join("invalid_tomac");
        let valid = temp.path().join("valid_tomac");
        std::fs::create_dir_all(&invalid).unwrap();
        let market_dir = valid.join("nq future 2021-2025");
        std::fs::create_dir_all(&market_dir).unwrap();
        std::fs::write(
            market_dir.join("glbx-mdp3-20100606-20260403.ohlcv-1m.csv"),
            "",
        )
        .unwrap();
        std::fs::write(market_dir.join("symbology.csv"), "").unwrap();

        let candidates = vec![
            invalid.to_string_lossy().to_string(),
            valid.to_string_lossy().to_string(),
        ];
        let detected = find_tomac_root_from_candidates(&candidates).unwrap();

        assert_eq!(detected, valid.to_string_lossy());
    }

    #[test]
    fn test_resolve_tomac_root_prefers_explicit_argument() {
        let resolved = resolve_tomac_root(Some("/tmp/custom-tomac")).unwrap();
        assert_eq!(resolved, "/tmp/custom-tomac");
    }

    #[test]
    fn test_build_pre_bayes_evidence_filter_neutralizes_conflicting_labels() {
        let filter = build_pre_bayes_evidence_filter(
            &pre_bayes_evidence_policy(),
            "bull",
            "hostile",
            &FactorDiagnostics {
                long_support: 0.30,
                short_support: 0.28,
                uncertainty: 0.52,
                alignment_label: "bearish".to_string(),
                uncertainty_label: "low".to_string(),
                ..FactorDiagnostics::default()
            },
            &ParsedMultiTimeframeEvidence::default(),
            None,
        );

        assert_eq!(filter.filtered_factor_alignment, "mixed");
        assert_eq!(filter.filtered_factor_uncertainty, "high");
        assert!(!filter.conflict_flags.is_empty());
        assert!(matches!(
            filter.gating_status.as_str(),
            "pass_neutralized" | "observe_only"
        ));
    }

    #[test]
    fn test_build_pre_bayes_evidence_filter_uses_multi_timeframe_conflicts() {
        let filter = build_pre_bayes_evidence_filter(
            &pre_bayes_evidence_policy(),
            "bull",
            "neutral",
            &FactorDiagnostics {
                long_support: 0.34,
                short_support: 0.10,
                uncertainty: 0.20,
                alignment_label: "bullish".to_string(),
                uncertainty_label: "low".to_string(),
                ..FactorDiagnostics::default()
            },
            &ParsedMultiTimeframeEvidence {
                direction_bias: "bearish".to_string(),
                alignment_score: Some(0.42),
                entry_alignment_score: Some(0.35),
                covered_count: 6,
            },
            None,
        );

        assert!(filter
            .conflict_flags
            .iter()
            .any(|flag| flag == "multi_timeframe_direction_conflict"));
        assert!(filter
            .conflict_flags
            .iter()
            .any(|flag| flag == "multi_timeframe_alignment_weak"));
        assert!(filter
            .conflict_flags
            .iter()
            .any(|flag| flag == "multi_timeframe_entry_alignment_weak"));
        assert_eq!(filter.filtered_factor_alignment, "mixed");
        assert_eq!(filter.filtered_factor_uncertainty, "high");
    }

    #[test]
    fn test_pre_bayes_gate_regression_uses_formal_status_ordering() {
        assert!(pre_bayes_gate_is_hard_pass("pass_hard"));
        assert!(!pre_bayes_gate_is_hard_pass("pass_neutralized"));
        assert!(pre_bayes_gate_regressed("pass_hard", "pass_neutralized"));
        assert!(pre_bayes_gate_regressed("pass_neutralized", "observe_only"));
        assert!(!pre_bayes_gate_regressed("pass_neutralized", "pass_hard"));
    }

    #[test]
    fn test_workflow_state_from_pre_bayes_filter_promotes_observe_only_phase() {
        let state = workflow_state_from_pre_bayes_filter(
            WorkflowState {
                phase: "observe_or_deploy".to_string(),
                reason: "base".to_string(),
            },
            &PreBayesEvidenceFilter {
                gating_status: "observe_only".to_string(),
                rationale: vec!["low_quality".to_string()],
                ..PreBayesEvidenceFilter::default()
            },
        );

        assert_eq!(state.phase, "pre_bayes_observe_only");
        assert!(state.reason.contains("low_quality"));
    }

    #[test]
    fn test_workflow_phase_snapshot_tracks_explicit_pre_bayes_soft_flag() {
        let snapshot = workflow_phase_snapshot_from_analyze_run(&AnalyzeRunRecord {
            run_id: "analyze:1".to_string(),
            source_command: "analyze".to_string(),
            multi_timeframe_summary: vec![
                "multi_timeframe_source=analyze_explicit_with_auto_fill covered_intervals=1m,5m,15m,1h,4h,1d"
                    .to_string(),
                "higher_timeframe_direction_bias=bullish".to_string(),
            ],
            pre_bayes_evidence_filter: PreBayesEvidenceFilter {
                gating_status: "pass_hard".to_string(),
                uses_soft_evidence: false,
                policy: ict_engine::state::PreBayesEvidencePolicy {
                    version: "policy-v1".to_string(),
                    ..ict_engine::state::PreBayesEvidencePolicy::default()
                },
                evidence_assignments: BTreeMap::from([(
                    "market_regime".to_string(),
                    "bull".to_string(),
                )]),
                soft_market_regime_distribution: BTreeMap::from([
                    ("bull".to_string(), 1.0),
                    ("bear".to_string(), 0.0),
                ]),
                ..PreBayesEvidenceFilter::default()
            },
            ..AnalyzeRunRecord::default()
        });

        assert_eq!(snapshot.pre_bayes_policy_version, "policy-v1");
        assert!(!snapshot.pre_bayes_uses_soft_evidence);
        assert!(snapshot
            .pre_bayes_soft_evidence
            .contains_key("market_regime"));
        assert!(snapshot.phase_summary.contains("mtf_direction=bullish"));
        assert_eq!(snapshot.multi_timeframe_summary.len(), 2);
    }

    #[test]
    fn test_multi_timeframe_entry_quality_bias_respects_direction() {
        let supportive = multi_timeframe_entry_quality_bias(
            &ParsedMultiTimeframeEvidence {
                direction_bias: "bullish".to_string(),
                alignment_score: Some(0.80),
                entry_alignment_score: Some(0.75),
                covered_count: 6,
            },
            Direction::Bull,
        );
        let hostile = multi_timeframe_entry_quality_bias(
            &ParsedMultiTimeframeEvidence {
                direction_bias: "bullish".to_string(),
                alignment_score: Some(0.80),
                entry_alignment_score: Some(0.75),
                covered_count: 6,
            },
            Direction::Bear,
        );

        assert!(supportive[0] > hostile[0]);
        assert!(supportive[2] < hostile[2]);
    }

    #[test]
    fn test_pre_bayes_entry_quality_bridge_diff_exposes_multi_timeframe_fields() {
        let diff =
            pre_bayes_entry_quality_bridge_diff(&ict_engine::state::PreBayesEntryQualityBridge {
                long_signal_probability: 0.62,
                short_signal_probability: 0.38,
                multi_timeframe_direction_bias: "bullish".to_string(),
                multi_timeframe_alignment_score: Some(0.77),
                multi_timeframe_entry_alignment_score: Some(0.71),
                ..ict_engine::state::PreBayesEntryQualityBridge::default()
            });

        assert_eq!(diff.multi_timeframe_direction_bias, "bullish");
        assert_eq!(diff.multi_timeframe_alignment_score, Some(0.77));
        assert_eq!(diff.multi_timeframe_entry_alignment_score, Some(0.71));
    }

    #[test]
    fn test_build_agent_action_plan_prioritizes_rollback() {
        let plan = build_agent_action_plan(
            "hint",
            &PromotionDecision {
                approved: false,
                status: "hold".to_string(),
                reason: "insufficient_improvement".to_string(),
                target_factors: vec![],
                target_families: vec![],
            },
            &RollbackRecommendation {
                should_rollback: true,
                scope: "targeted".to_string(),
                reason: "factor_score_regression".to_string(),
                target_factors: vec!["trend_momentum".to_string()],
                target_families: vec![],
            },
            &[],
            &[],
        );

        assert!(!plan.items.is_empty());
        assert_eq!(plan.items[0].title, "Review Rollback");
        assert!(plan.items[0].blocking);
    }

    #[test]
    fn test_recommended_next_command_prefers_blocking_high_priority_items() {
        let plan = AgentActionPlan {
            summary: "test".to_string(),
            items: vec![
                AgentActionItem {
                    stage: "iteration".to_string(),
                    blocking: false,
                    priority: "medium".to_string(),
                    title: "Tune".to_string(),
                    rationale: "tune".to_string(),
                    expected_output: "tuned factor".to_string(),
                    expected_state_changes: vec![],
                    suggested_files: vec![],
                    suggested_commands: vec!["ict-engine factor-backtest --data a.json".to_string()],
                },
                AgentActionItem {
                    stage: "rollback".to_string(),
                    blocking: true,
                    priority: "high".to_string(),
                    title: "Rollback".to_string(),
                    rationale: "rollback".to_string(),
                    expected_output: "rollback decision".to_string(),
                    expected_state_changes: vec![],
                    suggested_files: vec![],
                    suggested_commands: vec!["ict-engine update --feedback-file f.json".to_string()],
                },
            ],
        };

        let commands = command_recommendations(&CommandContext {
            symbol: "NQ".to_string(),
            state_dir: "state".to_string(),
            analyze: None,
            research_data: Some("a.json".to_string()),
            paired_data: None,
            update_outcome: Some("loss".to_string()),
            update_entry_signal: None,
            update_feedback_file: Some("f.json".to_string()),
            user_data_selection_required: false,
        });

        let mut plan = plan;
        concretize_action_plan_commands(&mut plan, &commands);

        assert_eq!(
            recommended_next_command(&plan, &commands),
            "ict-engine update --symbol NQ --outcome loss --state-dir state"
        );
    }

    #[test]
    fn test_recommended_next_command_prefers_artifact_consumption_suggested_command() {
        let plan = AgentActionPlan {
            summary: "test".to_string(),
            items: vec![
                AgentActionItem {
                    stage: "artifact_consumption".to_string(),
                    blocking: true,
                    priority: "high".to_string(),
                    title: "Artifact Consumption".to_string(),
                    rationale: "artifact gate".to_string(),
                    expected_output: "expected_output_unavailable".to_string(),
                    expected_state_changes: vec![],
                    suggested_files: vec![],
                    suggested_commands: vec![
                        "ict-engine workflow-status --symbol NQ --state-dir state --phase artifact-consumed-gate".to_string()
                    ],
                },
                AgentActionItem {
                    stage: "rollback".to_string(),
                    blocking: true,
                    priority: "high".to_string(),
                    title: "Rollback".to_string(),
                    rationale: "rollback".to_string(),
                    expected_output: "expected_output_unavailable".to_string(),
                    expected_state_changes: vec![],
                    suggested_files: vec![],
                    suggested_commands: vec![
                        "ict-engine update --symbol NQ --outcome loss --state-dir state".to_string()
                    ],
                },
            ],
        };

        let commands = CommandRecommendations {
            update: recommended_command(
                "ict-engine update --symbol NQ --outcome loss --state-dir state".to_string(),
                true,
                Vec::new(),
                "",
            ),
            ..CommandRecommendations::default()
        };

        assert_eq!(
            recommended_next_command(&plan, &commands),
            "ict-engine workflow-status --symbol NQ --state-dir state --phase artifact-consumed-gate"
        );
    }

    #[test]
    fn test_humanize_workflow_command_for_user_data_gate() {
        let rendered = humanize_workflow_command(
            "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state"
        );
        assert_eq!(
            rendered,
            "Ask the user to choose the historical dataset. Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json Then run: ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state"
        );
    }

    #[test]
    fn test_workflow_status_human_view_exposes_candidates() {
        let snapshot = sample_human_workflow_snapshot();
        let value = workflow_status_human_view(&snapshot, &[]);
        assert_eq!(value["symbol"], "NQ");
        assert_eq!(value["current_status"]["focus_phase"], "update");
        assert!(value["what_you_should_do_now"]
            .as_str()
            .unwrap()
            .contains("Ask the user to choose the historical dataset"));
        assert_eq!(value["historical_data_candidates"][0], "/tmp/a.json");
        assert_eq!(value["ensemble_consensus"]["final_action"], "observe");
        assert!(value["ensemble_consensus"]["human_next_triage"]
            .as_str()
            .unwrap()
            .contains("ensemble_action=observe"));
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecards"][0]["executor"],
            "catboost_stub"
        );
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecards"][0]["latest_weight_hint"],
            0.55
        );
        assert_eq!(
            value["jump_model"],
            serde_json::json!(
                "jump_model active_state=jump_transition confidence=0.500 transition_risk=0.500"
            )
        );
    }

    #[test]
    fn test_workflow_status_human_view_prefers_persisted_scorecards() {
        let snapshot = sample_human_workflow_snapshot();
        let persisted = vec![EnsembleExecutorScorecard {
            executor: "xgboost_file".to_string(),
            latest_weight_hint: Some(0.72),
            wins: 3,
            ..EnsembleExecutorScorecard::default()
        }];
        let value = workflow_status_human_view(&snapshot, &persisted);
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecards"][0]["executor"],
            "xgboost_file"
        );
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecard_source"],
            "persisted"
        );
        assert_eq!(
            value["ensemble_consensus"]["executor_scorecards"][0]["latest_weight_hint"],
            0.72
        );
    }

    #[test]
    fn test_executor_scorecard_surface_marks_fallback_and_persisted() {
        let fallback = vec![EnsembleExecutorScorecard {
            executor: "catboost_stub".to_string(),
            ..EnsembleExecutorScorecard::default()
        }];
        let persisted = vec![EnsembleExecutorScorecard {
            executor: "xgboost_file".to_string(),
            ..EnsembleExecutorScorecard::default()
        }];

        let (fallback_surface, fallback_source) = executor_scorecard_surface(&[], &fallback);
        assert_eq!(fallback_source, "fallback");
        assert_eq!(fallback_surface[0].executor, "catboost_stub");

        let (persisted_surface, persisted_source) =
            executor_scorecard_surface(&persisted, &fallback);
        assert_eq!(persisted_source, "persisted");
        assert_eq!(persisted_surface[0].executor, "xgboost_file");
    }

    #[test]
    fn test_ensemble_vote_history_view_uses_resolved_scorecard_source() {
        let vote = sample_human_workflow_snapshot()
            .latest_ensemble_vote
            .expect("sample ensemble vote");
        let persisted = vec![EnsembleExecutorScorecard {
            executor: "xgboost_file".to_string(),
            latest_weight_hint: Some(0.80),
            ..EnsembleExecutorScorecard::default()
        }];
        let value = serde_json::json!([vote]
            .iter()
            .map(|vote| {
                let (scorecards, scorecard_source) = resolved_vote_scorecards(&persisted, vote);
                serde_json::json!({
                    "artifact_id": vote.artifact_id,
                    "executor_scorecards": scorecards,
                    "executor_scorecard_source": scorecard_source,
                })
            })
            .collect::<Vec<_>>());
        assert_eq!(value[0]["executor_scorecard_source"], "persisted");
        assert_eq!(
            value[0]["executor_scorecards"][0]["executor"],
            "xgboost_file"
        );
    }

    #[test]
    fn test_load_canonical_executor_scorecards_falls_back_to_vote_record() {
        let temp = tempfile::tempdir().unwrap();
        let record = EnsembleVoteRecord {
            artifact_id: "ensemble-vote:test".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-1".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2-weighted".to_string(),
            final_action: "observe".to_string(),
            recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                .to_string(),
            human_next_triage: "ensemble_action=observe".to_string(),
            confidence: 0.5,
            consensus_strength: 0.5,
            disagreement_flags: Vec::new(),
            executor_summaries: vec![
                "executor=catboost_stub action=observe confidence=0.500".to_string()
            ],
            split_explanations: vec!["active_regime=research".to_string()],
            executor_scorecards: vec![EnsembleExecutorScorecard {
                executor: "catboost_stub".to_string(),
                latest_weight_hint: Some(0.55),
                ..EnsembleExecutorScorecard::default()
            }],
            executor_scorecards_source: Some("fallback".to_string()),
            posterior_fingerprint: "fp-test".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "research".to_string(),
            posterior_confidence: Some(0.5),
            posterior_probabilities: BTreeMap::new(),
            posterior_evidence: vec!["mtf=test".to_string()],
        };
        save_ensemble_vote_artifact(temp.path(), "NQ", &record).unwrap();
        append_ensemble_vote_history(temp.path(), "NQ", record).unwrap();

        let scorecards =
            load_canonical_executor_scorecards(temp.path().to_str().unwrap(), "NQ", Some("run-1"))
                .unwrap();
        assert_eq!(scorecards[0].executor, "catboost_stub");
        assert_eq!(scorecards[0].latest_weight_hint, Some(0.55));
    }

    fn save_then_load_vote_record_for_test(
        dir: &std::path::Path,
        record: &EnsembleVoteRecord,
    ) -> EnsembleVoteRecord {
        save_ensemble_vote_artifact(dir, "NQ", record).unwrap();
        load_state(dir, "NQ", ict_engine::state::ENSEMBLE_VOTE_FILE).unwrap()
    }

    #[test]
    fn test_persist_ensemble_vote_record_writes_canonical_scorecards_not_mirror() {
        let temp = tempfile::tempdir().unwrap();
        let record = EnsembleVoteRecord {
            artifact_id: "ensemble-vote:test".to_string(),
            generated_at: Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-1".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2-weighted".to_string(),
            final_action: "observe".to_string(),
            recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                .to_string(),
            human_next_triage: "ensemble_action=observe".to_string(),
            confidence: 0.5,
            consensus_strength: 0.5,
            disagreement_flags: Vec::new(),
            executor_summaries: vec![
                "executor=catboost_stub action=observe confidence=0.500".to_string()
            ],
            split_explanations: vec!["active_regime=research".to_string()],
            executor_scorecards: vec![EnsembleExecutorScorecard {
                executor: "mirror_only".to_string(),
                ..EnsembleExecutorScorecard::default()
            }],
            executor_scorecards_source: Some("fallback".to_string()),
            posterior_fingerprint: "fp-test".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "research".to_string(),
            posterior_confidence: Some(0.5),
            posterior_probabilities: BTreeMap::new(),
            posterior_evidence: vec!["mtf=test".to_string()],
        };
        let canonical = vec![EnsembleExecutorScorecard {
            executor: "canonical_only".to_string(),
            latest_weight_hint: Some(0.77),
            ..EnsembleExecutorScorecard::default()
        }];
        persist_ensemble_vote_record(temp.path().to_str().unwrap(), &record, &canonical).unwrap();

        let saved = load_ensemble_executor_scorecards(temp.path(), "NQ").unwrap();
        let saved_vote = save_then_load_vote_record_for_test(temp.path(), &record);
        assert_eq!(saved[0].executor, "canonical_only");
        assert_eq!(saved_vote.executor_scorecards[0].executor, "mirror_only");
    }

    #[test]
    fn test_command_recommendations_map_stages_to_commands() {
        let commands = command_recommendations(&CommandContext {
            symbol: "NQ".to_string(),
            state_dir: "state".to_string(),
            analyze: Some(AnalyzeCommandSource::Files {
                data_htf: "htf.json".to_string(),
                data_mtf: "mtf.json".to_string(),
                data_ltf: "ltf.json".to_string(),
            }),
            research_data: Some("a.json".to_string()),
            paired_data: None,
            update_outcome: Some("win".to_string()),
            update_entry_signal: None,
            update_feedback_file: Some("f.json".to_string()),
            user_data_selection_required: true,
        });
        assert_eq!(
            commands.research.command,
            "ict-engine factor-research --symbol NQ --data a.json --state-dir state"
        );
        assert_eq!(
            commands.update.command,
            "ict-engine update --symbol NQ --outcome win --state-dir state"
        );
        assert!(commands.research.user_data_selection_required);
        assert!(commands.backtest.user_data_selection_required);
        assert!(!commands.research.ready);
        assert!(commands
            .research
            .missing_inputs
            .contains(&"user_selected_historical_data".to_string()));
        assert_eq!(
            render_recommended_command(&commands.research),
            "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=htf.json, mtf.json, ltf.json, a.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data a.json --state-dir state"
        );
    }

    #[test]
    fn test_build_agent_context_bundle_contains_stage_views_and_window() {
        let bundle = build_agent_context_bundle(
            "NQ",
            "state",
            &WorkflowState {
                phase: "research_iteration".to_string(),
                reason: "need_tuning".to_string(),
            },
            "hint",
            "ict-engine factor-research --data a.json",
            &CommandRecommendations {
                analyze: recommended_command("a".to_string(), true, Vec::new(), ""),
                research: recommended_command("r".to_string(), true, Vec::new(), ""),
                backtest: recommended_command("b".to_string(), true, Vec::new(), ""),
                update: recommended_command("u".to_string(), true, Vec::new(), ""),
            },
            &DatasetComparability {
                comparable: true,
                previous_run_id: Some("run-1".to_string()),
                reason: "same_data_same_config".to_string(),
                comparison_class: "same_data_same_config".to_string(),
                same_data: true,
                same_config: true,
                same_prompt_version: true,
                same_factor_version: true,
                ..DatasetComparability::default()
            },
            &[FactorIterationPrompt {
                factor_name: "trend_momentum".to_string(),
                composite_score: 0.4,
                grade: "D".to_string(),
                iteration_action: "replace".to_string(),
                replacement_candidate: true,
                prompt: "replace".to_string(),
            }],
            &[FactorFamilyOutcome {
                family: "trend_momentum".to_string(),
                promotion_decision: PromotionDecision {
                    approved: false,
                    status: "hold".to_string(),
                    reason: "weak".to_string(),
                    target_factors: vec![],
                    target_families: vec![],
                },
                rollback_recommendation: RollbackRecommendation {
                    should_rollback: true,
                    scope: "family".to_string(),
                    reason: "weak".to_string(),
                    target_factors: vec![],
                    target_families: vec![],
                },
            }],
            Some(&PreBayesEvidenceFilter {
                gating_status: "pass_neutralized".to_string(),
                evidence_quality_score: 0.42,
                rationale: vec!["neutralized".to_string()],
                evidence_assignments: BTreeMap::from([
                    ("market_regime".to_string(), "range".to_string()),
                    ("liquidity_context".to_string(), "neutral".to_string()),
                ]),
                ..PreBayesEvidenceFilter::default()
            }),
            Some(&ict_engine::state::PreBayesEntryQualityBridge {
                rationale: vec!["bridge".to_string()],
                ..ict_engine::state::PreBayesEntryQualityBridge::default()
            }),
            None,
            Some(&ict_engine::state::ArtifactDecisionSummary {
                consumed_trend_status: "validated_regressing".to_string(),
                consumed_trend_reason: "regression".to_string(),
                consumed_target_kinds: vec!["pending_update".to_string()],
                ..ict_engine::state::ArtifactDecisionSummary::default()
            }),
        );

        assert_eq!(bundle.family_history_window, 5);
        assert_eq!(bundle.stage_views.len(), 5);
        assert_eq!(bundle.stage_views[1].stage, "research");
        assert_eq!(bundle.artifact_consumed_gate_status, "validated_regressing");
        assert!(bundle
            .stage_views
            .iter()
            .any(|view| view.stage == "artifact_consumption"));
    }

    #[test]
    fn test_agent_context_bundle_minimal_uses_explicit_pre_bayes_soft_flag() {
        let bundle = build_agent_context_bundle(
            "NQ",
            "state",
            &WorkflowState {
                phase: "observe_or_deploy".to_string(),
                reason: "stable".to_string(),
            },
            "hint",
            "ict-engine analyze --symbol NQ",
            &CommandRecommendations::default(),
            &DatasetComparability {
                comparable: true,
                ..DatasetComparability::default()
            },
            &[],
            &[],
            Some(&PreBayesEvidenceFilter {
                gating_status: "pass_hard".to_string(),
                uses_soft_evidence: false,
                evidence_assignments: BTreeMap::from([(
                    "market_regime".to_string(),
                    "bull".to_string(),
                )]),
                soft_market_regime_distribution: BTreeMap::from([
                    ("bull".to_string(), 1.0),
                    ("bear".to_string(), 0.0),
                ]),
                soft_liquidity_context_distribution: BTreeMap::from([
                    ("favorable".to_string(), 1.0),
                    ("neutral".to_string(), 0.0),
                ]),
                ..PreBayesEvidenceFilter::default()
            }),
            Some(&ict_engine::state::PreBayesEntryQualityBridge::default()),
            None,
            None,
        );

        let minimal = build_agent_context_bundle_minimal(&bundle);
        assert!(!minimal.pre_bayes_uses_soft_evidence);
    }

    #[test]
    fn test_family_diffs_reports_family_level_score_changes() {
        let previous = vec![FactorFamilyDecision {
            family: "trend_momentum".to_string(),
            factor_count: 1,
            avg_score: 0.40,
            actions: vec!["trend_momentum:tune".to_string()],
            replacement_candidates: vec![],
            ..FactorFamilyDecision::default()
        }];
        let current = vec![FactorFamilyDecision {
            family: "trend_momentum".to_string(),
            factor_count: 1,
            avg_score: 0.62,
            actions: vec!["trend_momentum:keep".to_string()],
            replacement_candidates: vec![],
            ..FactorFamilyDecision::default()
        }];

        let diffs = family_diffs(&previous, &current);
        assert_eq!(diffs.len(), 1);
        assert!(diffs[0].avg_score_delta > 0.0);
    }

    #[test]
    fn test_family_history_from_runs_tracks_trend() {
        let history = family_history_from_runs(vec![
            (
                "run-1".to_string(),
                Utc.with_ymd_and_hms(2024, 1, 1, 0, 0, 0).unwrap(),
                vec![FactorFamilyDecision {
                    family: "trend_momentum".to_string(),
                    factor_count: 1,
                    avg_score: 0.40,
                    actions: vec![],
                    replacement_candidates: vec![],
                    ..FactorFamilyDecision::default()
                }],
            ),
            (
                "run-2".to_string(),
                Utc.with_ymd_and_hms(2024, 1, 2, 0, 0, 0).unwrap(),
                vec![FactorFamilyDecision {
                    family: "trend_momentum".to_string(),
                    factor_count: 1,
                    avg_score: 0.58,
                    actions: vec![],
                    replacement_candidates: vec!["trend_momentum".to_string()],
                    ..FactorFamilyDecision::default()
                }],
            ),
        ]);

        assert_eq!(history.len(), 1);
        assert_eq!(history[0].window_size, 5);
        assert_eq!(history[0].score_trend, "improving");
        assert_eq!(history[0].replacement_trend, "worsening");
        assert_eq!(history[0].recent_run_ids.len(), 2);
    }

    #[test]
    fn test_decision_history_summary_counts_runs() {
        let summary = decision_history_summary(vec![
            (
                PromotionDecision {
                    approved: true,
                    status: "promote".to_string(),
                    reason: "ok".to_string(),
                    target_factors: vec![],
                    target_families: vec![],
                },
                RollbackRecommendation {
                    should_rollback: false,
                    scope: "none".to_string(),
                    reason: "ok".to_string(),
                    target_factors: vec![],
                    target_families: vec![],
                },
            ),
            (
                PromotionDecision {
                    approved: false,
                    status: "hold".to_string(),
                    reason: "weak".to_string(),
                    target_factors: vec![],
                    target_families: vec![],
                },
                RollbackRecommendation {
                    should_rollback: true,
                    scope: "targeted".to_string(),
                    reason: "regression".to_string(),
                    target_factors: vec!["trend_momentum".to_string()],
                    target_families: vec![],
                },
            ),
        ]);

        assert_eq!(summary.total_runs, 2);
        assert_eq!(summary.promotion_approved_runs, 1);
        assert_eq!(summary.rollback_recommended_runs, 1);
        assert_eq!(summary.latest_rollback_scope.as_deref(), Some("targeted"));
    }
}
