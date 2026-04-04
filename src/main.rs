use anyhow::{anyhow, bail, Result};
use chrono::{Duration, Utc};
use clap::{Parser, Subcommand};
use ict_engine::backtest::{BacktestEngine, Metrics, RegimeSplit};
use ict_engine::bayesian::{cascade_bear, cascade_bull, CascadeConfig};
use ict_engine::bbn::learning::cpt_updater::{CPTUpdater, TradeOutcome};
use ict_engine::bbn::trading::{
    topology::build_trading_network,
    update::{
        entry_quality_bias_from_signal, infer_entry_quality, infer_entry_quality_with_bias,
        infer_trade_outcome, infer_trade_outcome_with_entry_quality_bias,
        trade_evidence_from_labels,
    },
};
use ict_engine::data::{
    candles_to_prices, load_candles_json,
    realtime::{
        build_live_data_source,
        openalice::{AuxiliaryMarketEvidence, SpotInstrumentKind},
        LiveDataBackend,
    },
};
use ict_engine::factor_lab::FactorLab;
use ict_engine::factors::FactorRegistry;
use ict_engine::hmm::{
    build_observations, init_hmm_params, state_name, BaumWelch, ForwardBackward, Viterbi,
};
use ict_engine::ict::{
    check_bear_expansion_exists, check_bull_expansion_exists, count_recent_breaks,
    count_recent_sweeps, detect_cisd, detect_fvg, detect_liquidity_pools, detect_liquidity_sweep,
    detect_order_blocks, detect_structure_breaks, expansion_strength, find_swing_highs,
    find_swing_lows, find_unfilled_fvgs, find_untested_obs, has_recent_pinbar,
};
use ict_engine::indicators::{
    atr_percent, compute_adx, compute_atr, compute_rsi, latest_adx, latest_atr, latest_bollinger,
    latest_ema, latest_macd, latest_rsi,
};
use ict_engine::kalman::KalmanFilter;
use ict_engine::planner::{
    generate_probabilistic_trade_plan, probabilistic_decision_snapshot,
    ProbabilisticDecisionSnapshot, ProbabilisticPlanConfig,
};
use ict_engine::smt::{Cointegration, Correlation, Divergence};
use ict_engine::state::{load_state, save_state, state_exists};
use ict_engine::types::{
    Candle, CascadeLayer, Direction, HMMParams, Regime, RegimeProbs, Symbol, TradePlan,
    TradeRecord, OBS_DIM,
};
use serde::Serialize;
use std::collections::{BTreeMap, HashMap};

const HMM_STATE_FILE: &str = "hmm_params.json";
const BBN_STATE_FILE: &str = "bbn_network.json";
const INDICATOR_PERIOD: usize = 14;

#[derive(Debug)]
struct FrameFeatures {
    observations: Vec<Vec<f64>>,
    regime_label: String,
    liquidity_label: String,
    sweep_count: usize,
    fvg_count: usize,
}

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
    data_source: Option<LiveDataSource>,
}

#[derive(Debug, Serialize)]
struct AnalyzeSupporting {
    model_state: AnalyzeModelState,
    labels: AnalyzeLabels,
    ict: AnalyzeIctSummary,
    entry_quality: AnalyzeEntryQualitySummary,
    #[serde(skip_serializing_if = "Option::is_none")]
    auxiliary: Option<AuxiliaryMarketEvidence>,
    decision: ProbabilisticDecisionSnapshot,
    trade_outcome: AnalyzeTradeOutcomeSummary,
    raw_trade_plan: TradePlan,
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
struct TechnicalPriceSection {
    probability_role: String,
    last_closed_bar_close: f64,
    live_market_price: Option<f64>,
    live_spot_price: Option<f64>,
    ema20: Option<f64>,
    ema50: Option<f64>,
    rsi14: Option<f64>,
    adx14: Option<f64>,
    atr14: Option<f64>,
    macd_line: Option<f64>,
    macd_signal: Option<f64>,
    macd_histogram: Option<f64>,
    bollinger_upper: Option<f64>,
    bollinger_middle: Option<f64>,
    bollinger_lower: Option<f64>,
    bollinger_squeeze: bool,
    momentum_5_bar: Option<f64>,
    options_hedging: OptionsHedgingSection,
    narrative: String,
}

#[derive(Debug, Serialize)]
struct OptionsHedgingSection {
    probability_role: String,
    options_symbol: Option<String>,
    put_call_oi_ratio: Option<f64>,
    put_call_volume_ratio: Option<f64>,
    near_atm_implied_volatility: Option<f64>,
    near_atm_delta: Option<f64>,
    near_atm_gamma: Option<f64>,
    near_atm_vega: Option<f64>,
    call_gamma_oi: Option<f64>,
    put_gamma_oi: Option<f64>,
    gamma_skew: Option<f64>,
    hedge_pressure_direction: Option<String>,
    hedge_pressure_score: Option<f64>,
    long_bias_contribution: Option<f64>,
    short_bias_contribution: Option<f64>,
    uncertainty_penalty_contribution: Option<f64>,
    narrative: String,
}

#[derive(Debug, Serialize)]
struct SmtCorrelationSection {
    probability_role: String,
    paired_market_available: bool,
    futures_symbol: Option<String>,
    spot_symbol: Option<String>,
    rolling_correlation_20: Option<f64>,
    rolling_correlation_50: Option<f64>,
    divergence_detected: Option<bool>,
    cointegration_stat: Option<f64>,
    cointegrated: Option<bool>,
    raw_basis_bps: Option<f64>,
    normalized_basis_bps: Option<f64>,
    rolling_price_ratio_mean: Option<f64>,
    notes: Vec<String>,
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
struct LiveDataSource {
    provider: String,
    base_url: String,
    futures_symbol: String,
    spot_symbol: String,
    options_symbol: String,
    spot_kind: SpotInstrumentKind,
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
    bars: usize,
    warmup_bars: usize,
    hold_bars: usize,
    window_mode: String,
    evidence_policy: String,
    ict_role: String,
    online_learning: bool,
    learning_updates: usize,
    signals: usize,
    trades: usize,
    metrics: BacktestMetricsSummary,
    regime_metrics: Vec<BacktestRegimeSummary>,
    last_decision: Option<ProbabilisticDecisionSnapshot>,
    final_trade_outcome_cpt: BTreeMap<String, BTreeMap<String, f64>>,
    recent_trades: Vec<BacktestTradeSample>,
}

#[derive(Debug, Serialize)]
struct BacktestMetricsSummary {
    total_return: f64,
    sharpe: f64,
    max_drawdown: f64,
    win_rate: f64,
    profit_factor: f64,
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
        data_htf: String,
        #[arg(long)]
        data_mtf: String,
        #[arg(long)]
        data_ltf: String,
        #[arg(long, default_value = "state")]
        state_dir: String,
    },
    /// Analyze live futures with integrated backends and spot/options auxiliary evidence
    AnalyzeLive {
        #[arg(long)]
        symbol: String,
        #[arg(long)]
        futures_symbol: String,
        #[arg(long)]
        spot_symbol: String,
        #[arg(long)]
        options_symbol: Option<String>,
        #[arg(long, default_value = "equity")]
        spot_kind: String,
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
        #[arg(long, default_value = "state")]
        state_dir: String,
        #[arg(long, default_value = "60")]
        warmup_bars: usize,
        #[arg(long, default_value = "10")]
        hold_bars: usize,
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
    },
    /// Run factor research sandbox
    FactorResearch {
        #[arg(long)]
        data: String,
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
            state_dir,
        } => analyze_command(&symbol, &data_htf, &data_mtf, &data_ltf, &state_dir)?,
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
            &futures_symbol,
            &spot_symbol,
            options_symbol.as_deref(),
            &spot_kind,
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
            state_dir,
            warmup_bars,
            hold_bars,
            online_learn,
        } => backtest_command(
            &symbol,
            &data,
            &state_dir,
            warmup_bars,
            hold_bars,
            online_learn,
        )?,
        Commands::Update {
            symbol,
            outcome,
            entry_signal,
            state_dir,
        } => update_command(&symbol, &outcome, &entry_signal, &state_dir)?,
        Commands::FactorResearch { data } => factor_research_command(&data)?,
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
    let htf = load_candles_json(data_htf)?;
    let mtf = load_candles_json(data_mtf)?;
    let ltf = load_candles_json(data_ltf)?;
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let report = build_analyze_report(symbol, state_dir, &htf, &mtf, &ltf, &params, &network)?;

    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn analyze_live_command(
    symbol: &str,
    futures_symbol: &str,
    spot_symbol: &str,
    options_symbol: Option<&str>,
    spot_kind: &str,
    futures_backend: &str,
    aux_backend: &str,
    futures_base_url: &str,
    aux_base_url: &str,
    state_dir: &str,
) -> Result<()> {
    let options_symbol = options_symbol.unwrap_or(spot_symbol);
    let spot_kind = SpotInstrumentKind::parse(spot_kind)?;
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

    let (spot_interval, spot_lookback_days) = match spot_kind {
        SpotInstrumentKind::Commodity => ("1d", 420),
        SpotInstrumentKind::Equity | SpotInstrumentKind::Index => ("15m", 45),
    };
    let futures_live_price = futures_provider.fetch_futures_last_price(futures_symbol).ok();
    let spot_candles = aux_provider.fetch_spot_candles(
        spot_kind,
        spot_symbol,
        Some(spot_interval),
        now - Duration::days(spot_lookback_days),
        now,
    )?;
    let spot_live_price = aux_provider.fetch_spot_last_price(spot_kind, spot_symbol).ok();
    let options_summary = aux_provider
        .fetch_options_chain_summary(options_symbol)
        .unwrap_or_else(|_| neutral_options_summary(options_symbol));

    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let mut report = build_analyze_report(symbol, state_dir, &htf, &mtf, &ltf, &params, &network)?;
    let auxiliary = aux_provider.build_auxiliary_evidence(
        spot_kind,
        spot_symbol,
        options_symbol,
        &ltf,
        &spot_candles,
        &options_summary,
    );

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

    report.meta.data_source = Some(LiveDataSource {
        provider: format!(
            "futures={}/aux={}",
            futures_backend.as_str(),
            aux_backend.as_str()
        ),
        base_url: format!("futures:{}|aux:{}", futures_base_url, aux_base_url),
        futures_symbol: futures_symbol.to_string(),
        spot_symbol: spot_symbol.to_string(),
        options_symbol: options_symbol.to_string(),
        spot_kind,
    });
    report.supporting.auxiliary = Some(auxiliary);
    report.supporting.model_state.evidence_policy =
        "hmm_prior_times_bbn_trade_probability_plus_spot_options_auxiliary".to_string();
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
    report.analysis.trade_plan = build_trade_plan_section(
        &report.supporting.raw_trade_plan,
        Some(&report.analysis.technical_price.options_hedging),
    );

    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn train_command(symbol: &str, data: &str, epochs: usize, state_dir: &str) -> Result<()> {
    let candles = load_candles_json(data)?;
    let features = build_frame_features(&candles)?;
    let initial_params = load_or_init_hmm_params(symbol, state_dir);
    let trained_params = BaumWelch::fit(&features.observations, &initial_params, epochs, 1e-4);
    let (_, log_likelihood) = ForwardBackward::forward(&features.observations, &trained_params);
    let (states, viterbi_log_likelihood) = Viterbi::decode(&features.observations, &trained_params);

    save_state(state_dir, symbol, HMM_STATE_FILE, &trained_params)?;

    println!(
        "train symbol={} state_dir={} epochs={} candles={} observations={} final_state={} log_likelihood={:.4} viterbi_log_likelihood={:.4} saved={}/{}",
        symbol,
        state_dir,
        epochs,
        candles.len(),
        features.observations.len(),
        states.last().copied().map(state_name).unwrap_or("Unknown"),
        log_likelihood,
        viterbi_log_likelihood,
        symbol,
        HMM_STATE_FILE,
    );
    Ok(())
}

fn backtest_command(
    symbol: &str,
    data: &str,
    state_dir: &str,
    warmup_bars: usize,
    hold_bars: usize,
    online_learn: bool,
) -> Result<()> {
    let candles = load_candles_json(data)?;
    let params = load_or_init_hmm_params(symbol, state_dir);
    let network = load_or_init_trading_network(symbol, state_dir)?;
    let report = run_probabilistic_backtest(
        symbol,
        state_dir,
        &candles,
        warmup_bars,
        hold_bars,
        online_learn,
        &params,
        &network,
    )?;
    println!("{}", serde_json::to_string_pretty(&report)?);
    Ok(())
}

fn update_command(symbol: &str, outcome: &str, entry_signal: &str, state_dir: &str) -> Result<()> {
    let mut network = load_or_init_trading_network(symbol, state_dir)?;
    let entry_quality = normalize_entry_quality_label(entry_signal);
    let outcome_label = normalize_trade_outcome_label(outcome);

    let evidence =
        trade_evidence_from_labels(&network, &[("entry_quality", entry_quality.as_str())])?;
    let outcome_node = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let realized_state_index = outcome_node
        .state_index(&outcome_label)
        .ok_or_else(|| anyhow!("unknown outcome state '{}'", outcome_label))?;

    CPTUpdater::default().update_from_trade(
        &mut network,
        &evidence,
        TradeOutcome {
            node_id: "trade_outcome".into(),
            realized_state_index,
        },
    )?;

    let updated_node = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let updated = updated_node.probabilities_for_evidence(&evidence)?;
    save_state(state_dir, symbol, BBN_STATE_FILE, &network)?;

    println!(
        "update symbol={} state_dir={} entry_signal={} normalized_entry_quality={} outcome={} updated_trade_outcome={}",
        symbol,
        state_dir,
        entry_signal,
        entry_quality,
        outcome_label,
        format_probability_map(&updated_node.states, &updated),
    );
    Ok(())
}

fn factor_research_command(data: &str) -> Result<()> {
    let candles = load_candles_json(data)?;
    let lab = FactorLab::new(FactorRegistry::default());
    let report = lab.run_research(&candles)?;
    println!(
        "factor-research factors={} best_factor={:?} aggregate_return={:.6}",
        report.factor_count, report.best_factor, report.aggregate_return
    );
    Ok(())
}

fn build_analyze_report(
    symbol: &str,
    state_dir: &str,
    htf: &[Candle],
    mtf: &[Candle],
    ltf: &[Candle],
    params: &HMMParams,
    network: &ict_engine::bbn::BayesianNetwork,
) -> Result<AnalyzeReport> {
    let htf_features = build_frame_features(htf)?;
    let mtf_features = build_frame_features(mtf)?;
    let ltf_features = build_frame_features(ltf)?;

    let regime_label = combine_regime_labels(&[
        htf_features.regime_label.as_str(),
        mtf_features.regime_label.as_str(),
        ltf_features.regime_label.as_str(),
    ]);
    let liquidity_label = combine_liquidity_labels(&[
        htf_features.liquidity_label.as_str(),
        mtf_features.liquidity_label.as_str(),
        ltf_features.liquidity_label.as_str(),
    ]);

    let (log_alpha, log_likelihood) = ForwardBackward::forward(&ltf_features.observations, params);
    let log_beta = ForwardBackward::backward(&ltf_features.observations, params);
    let gamma = ForwardBackward::compute_gamma(&log_alpha, &log_beta, log_likelihood);
    let (states, viterbi_log_likelihood) = Viterbi::decode(&ltf_features.observations, params);
    let regime_probs = regime_probs_from_log_gamma(gamma.last())?;

    let atr_htf = left_pad(compute_atr(htf, INDICATOR_PERIOD), htf.len(), 0.0);
    let atr_ltf = left_pad(compute_atr(ltf, INDICATOR_PERIOD), ltf.len(), 0.0);
    let cascade_config = CascadeConfig::default();
    let cascade_bull = cascade_bull(htf, mtf, ltf, &cascade_config, &atr_htf, &atr_ltf);
    let cascade_bear = cascade_bear(htf, mtf, ltf, &cascade_config, &atr_htf, &atr_ltf);

    let evidence = trade_evidence_from_labels(
        network,
        &[
            ("market_regime", regime_label.as_str()),
            ("liquidity_context", liquidity_label.as_str()),
        ],
    )?;
    let base_entry_quality = infer_entry_quality(network, &evidence)?;
    let long_entry_quality = infer_entry_quality_with_bias(
        network,
        &evidence,
        &entry_quality_bias_from_signal(cascade_bull.final_posterior),
    )?;
    let short_entry_quality = infer_entry_quality_with_bias(
        network,
        &evidence,
        &entry_quality_bias_from_signal(cascade_bear.final_posterior),
    )?;
    let posterior = infer_trade_outcome(network, &evidence)?;
    let bull_trade_outcome = infer_trade_outcome_with_entry_quality_bias(
        network,
        &evidence,
        &entry_quality_bias_from_signal(cascade_bull.final_posterior),
    )?;
    let bear_trade_outcome = infer_trade_outcome_with_entry_quality_bias(
        network,
        &evidence,
        &entry_quality_bias_from_signal(cascade_bear.final_posterior),
    )?;
    let trade_outcome = network
        .nodes
        .get("trade_outcome")
        .ok_or_else(|| anyhow!("missing node 'trade_outcome'"))?;
    let fvgs = find_unfilled_fvgs(mtf);
    let obs = find_untested_obs(mtf);
    let decision = probabilistic_decision_snapshot(
        &regime_probs,
        &cascade_bull,
        &cascade_bear,
        &bull_trade_outcome,
        &bear_trade_outcome,
    );
    let selected_entry_quality_distribution = match decision.selected_direction {
        Direction::Bull => &long_entry_quality,
        Direction::Bear => &short_entry_quality,
        Direction::Neutral => &base_entry_quality,
    };
    let selected_entry_quality_state = select_state_name(
        selected_entry_quality_distribution,
        network
            .nodes
            .get("entry_quality")
            .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?,
    )?;
    let trade_plan = generate_probabilistic_trade_plan(
        mtf,
        ltf,
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
    let price_action = build_price_action_section(mtf, ltf, &atr_ltf, &fvgs, &obs);
    let technical_price = build_technical_price_section(ltf, None, None, None);
    let smt_correlation = empty_smt_correlation_section();
    let regime_bayesian = build_regime_bayesian_section(
        states.last().copied().map(state_name).unwrap_or("Unknown"),
        &regime_probs,
        &regime_label,
        &liquidity_label,
        &decision,
        "hmm_prior_times_bbn_trade_probability",
        None,
    );
    let trade_plan_section = build_trade_plan_section(&trade_plan, None);

    Ok(AnalyzeReport {
        symbol: symbol.to_string(),
        timestamp: Utc::now(),
        analysis: AnalyzeSections {
            price_action,
            technical_price,
            smt_correlation,
            regime_bayesian,
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
                hmm_state: states
                    .last()
                    .copied()
                    .map(state_name)
                    .unwrap_or("Unknown")
                    .to_string(),
                log_likelihood,
                viterbi_log_likelihood,
                regime_probs,
                evidence_policy: "hmm_prior_times_bbn_trade_probability".to_string(),
            },
            labels: AnalyzeLabels {
                regime_label,
                liquidity_label,
            },
            ict: AnalyzeIctSummary {
                total_sweeps: htf_features.sweep_count
                    + mtf_features.sweep_count
                    + ltf_features.sweep_count,
                total_fvgs: htf_features.fvg_count
                    + mtf_features.fvg_count
                    + ltf_features.fvg_count,
                mtf_open_fvgs: fvgs.len(),
                mtf_untested_obs: obs.len(),
                ict_role: "evidence_only_non_deterministic".to_string(),
            },
            entry_quality: AnalyzeEntryQualitySummary {
                base: probability_map(
                    &network
                        .nodes
                        .get("entry_quality")
                        .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?
                        .states,
                    &base_entry_quality,
                ),
                long: probability_map(
                    &network
                        .nodes
                        .get("entry_quality")
                        .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?
                        .states,
                    &long_entry_quality,
                ),
                short: probability_map(
                    &network
                        .nodes
                        .get("entry_quality")
                        .ok_or_else(|| anyhow!("missing node 'entry_quality'"))?
                        .states,
                    &short_entry_quality,
                ),
                selected_state: selected_entry_quality_state,
            },
            auxiliary: None,
            decision,
            trade_outcome: AnalyzeTradeOutcomeSummary {
                base: probability_map(&trade_outcome.states, &posterior),
                long: probability_map(&trade_outcome.states, &bull_trade_outcome),
                short: probability_map(&trade_outcome.states, &bear_trade_outcome),
            },
            raw_trade_plan: trade_plan,
        },
    })
}

fn run_probabilistic_backtest(
    symbol: &str,
    state_dir: &str,
    candles: &[Candle],
    warmup_bars: usize,
    hold_bars: usize,
    online_learn: bool,
    params: &HMMParams,
    network: &ict_engine::bbn::BayesianNetwork,
) -> Result<BacktestReport> {
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
        )?;
        last_decision = Some(analysis.supporting.decision.clone());

        if analysis.supporting.raw_trade_plan.direction == Direction::Neutral
            || analysis.supporting.raw_trade_plan.kelly_fraction <= 0.0
        {
            continue;
        }

        signals += 1;

        if let Some(simulated) = BacktestEngine::simulate_trade(
            candles,
            signal_index,
            &analysis.supporting.raw_trade_plan,
            hold_bars,
        )
        {
            trades.push(TradeRecord {
                timestamp: candles[simulated.entry_index].timestamp,
                symbol: parse_symbol(symbol),
                direction: analysis.supporting.raw_trade_plan.direction,
                entry_price: simulated.entry_price,
                exit_price: simulated.exit_price,
                pnl: simulated.pnl,
                regime_at_entry: analysis.supporting.model_state.regime_probs.dominant(),
                cascade_max_layer: selected_cascade_max_layer(&analysis.supporting.raw_trade_plan),
                cascade_direction: analysis.supporting.raw_trade_plan.direction,
                factor_values: decision_factor_values(
                    &analysis.supporting.decision,
                    &analysis.supporting.raw_trade_plan,
                ),
            });

            if online_learn {
                let outcome_label = trade_outcome_label_from_pnl(simulated.pnl);
                let evidence = trade_evidence_from_labels(
                    &working_network,
                    &[(
                        "entry_quality",
                        analysis.supporting.entry_quality.selected_state.as_str(),
                    )],
                )?;
                let realized_state_index = working_network
                    .nodes
                    .get("trade_outcome")
                    .and_then(|node| node.state_index(&outcome_label))
                    .ok_or_else(|| anyhow!("unknown trade outcome state '{}'", outcome_label))?;

                CPTUpdater::default().update_from_trade(
                    &mut working_network,
                    &evidence,
                    TradeOutcome {
                        node_id: "trade_outcome".into(),
                        realized_state_index,
                    },
                )?;
                learning_updates += 1;
            }
        }
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

    Ok(BacktestReport {
        symbol: symbol.to_string(),
        state_dir: state_dir.to_string(),
        bars: candles.len(),
        warmup_bars: minimum_history,
        hold_bars,
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
        },
        regime_metrics,
        last_decision,
        final_trade_outcome_cpt: trade_outcome_cpt_snapshot(&working_network)?,
        recent_trades,
    })
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

fn build_technical_price_section(
    ltf: &[Candle],
    live_market_price: Option<f64>,
    live_spot_price: Option<f64>,
    auxiliary: Option<&AuxiliaryMarketEvidence>,
) -> TechnicalPriceSection {
    let last_close = ltf.last().map(|candle| candle.close).unwrap_or(0.0);
    let atr14 = Some(latest_atr(ltf, 14)).filter(|value| *value > 0.0);
    let rsi14 = Some(latest_rsi(ltf, 14));
    let adx14 = Some(latest_adx(ltf, 14));
    let ema20 = Some(latest_ema(ltf, 20)).filter(|value| *value > 0.0);
    let ema50 = Some(latest_ema(ltf, 50)).filter(|value| *value > 0.0);
    let macd = latest_macd(ltf, 12, 26, 9);
    let bollinger = latest_bollinger(ltf, 20, 2.0);
    let momentum_5_bar = if ltf.len() > 5 {
        let previous = ltf[ltf.len() - 6].close;
        if previous.abs() > f64::EPSILON {
            Some((last_close - previous) / previous)
        } else {
            None
        }
    } else {
        None
    };
    let narrative = match (rsi14, adx14, macd) {
        (Some(rsi), Some(adx), Some((_, _, histogram)))
            if rsi > 55.0 && adx > 20.0 && histogram > 0.0 =>
        {
            "technicals_support_bullish_continuation".to_string()
        }
        (Some(rsi), Some(adx), Some((_, _, histogram)))
            if rsi < 45.0 && adx > 20.0 && histogram < 0.0 =>
        {
            "technicals_support_bearish_continuation".to_string()
        }
        _ => "technicals_mixed_or_range_bound".to_string(),
    };

    TechnicalPriceSection {
        probability_role: "technical_and_derivatives_evidence_for_probability_model".to_string(),
        last_closed_bar_close: last_close,
        live_market_price,
        live_spot_price,
        ema20,
        ema50,
        rsi14,
        adx14,
        atr14,
        macd_line: macd.map(|value| value.0),
        macd_signal: macd.map(|value| value.1),
        macd_histogram: macd.map(|value| value.2),
        bollinger_upper: bollinger.map(|value| value.0),
        bollinger_middle: bollinger.map(|value| value.1),
        bollinger_lower: bollinger.map(|value| value.2),
        bollinger_squeeze: ict_engine::indicators::is_squeeze(ltf, 20, 2.0, 0.05),
        momentum_5_bar,
        options_hedging: build_options_hedging_section(auxiliary),
        narrative,
    }
}

fn build_options_hedging_section(
    auxiliary: Option<&AuxiliaryMarketEvidence>,
) -> OptionsHedgingSection {
    let narrative = if let Some(aux) = auxiliary {
        let mut parts = Vec::new();

        if let Some(iv) = aux.near_atm_implied_volatility {
            if iv >= 0.35 {
                parts.push("high_iv_can_force_more_aggressive_hedging");
            } else if iv <= 0.18 {
                parts.push("contained_iv_limits_hedging_urgency");
            } else {
                parts.push("moderate_iv_environment");
            }
        }

        if let Some(gamma) = aux.near_atm_gamma {
            if gamma >= 0.05 {
                parts.push("elevated_gamma_makes_delta_hedging_more_sensitive");
            } else if gamma <= 0.02 {
                parts.push("subdued_gamma_reduces_convexity_pressure");
            }
        }

        if let Some(vega) = aux.near_atm_vega {
            if vega >= 0.20 {
                parts.push("vega_exposure_means_volatility_shifts_matter");
            }
        }

        match aux.hedge_pressure_direction.as_deref() {
            Some("bullish") => parts.push("dealer_hedging_bias_supports_upside"),
            Some("bearish") => parts.push("dealer_hedging_bias_supports_downside"),
            Some("neutral") | None => {}
            _ => {}
        }

        if aux
            .notes
            .iter()
            .any(|note| note == "options_volatility_proxy_only")
        {
            parts.push("options_signal_uses_proxy_not_full_chain");
        }

        if parts.is_empty() {
            "options_data_available_but_hedging_bias_is_neutral".to_string()
        } else {
            parts.join(";")
        }
    } else {
        "options_hedging_data_unavailable_or_proxied".to_string()
    };

    OptionsHedgingSection {
        probability_role: "options_hedging_is_auxiliary_evidence_not_trade_trigger".to_string(),
        options_symbol: auxiliary.map(|aux| aux.options_symbol.clone()),
        put_call_oi_ratio: auxiliary.and_then(|aux| aux.put_call_oi_ratio),
        put_call_volume_ratio: auxiliary.and_then(|aux| aux.put_call_volume_ratio),
        near_atm_implied_volatility: auxiliary.and_then(|aux| aux.near_atm_implied_volatility),
        near_atm_delta: auxiliary.and_then(|aux| aux.near_atm_delta),
        near_atm_gamma: auxiliary.and_then(|aux| aux.near_atm_gamma),
        near_atm_vega: auxiliary.and_then(|aux| aux.near_atm_vega),
        call_gamma_oi: auxiliary.and_then(|aux| aux.call_gamma_oi),
        put_gamma_oi: auxiliary.and_then(|aux| aux.put_gamma_oi),
        gamma_skew: auxiliary.and_then(|aux| aux.gamma_skew),
        hedge_pressure_direction: auxiliary.and_then(|aux| aux.hedge_pressure_direction.clone()),
        hedge_pressure_score: auxiliary.and_then(|aux| aux.hedge_pressure_score),
        long_bias_contribution: auxiliary.map(|aux| aux.long_bias),
        short_bias_contribution: auxiliary.map(|aux| aux.short_bias),
        uncertainty_penalty_contribution: auxiliary.map(|aux| aux.uncertainty_penalty),
        narrative,
    }
}

fn empty_smt_correlation_section() -> SmtCorrelationSection {
    SmtCorrelationSection {
        probability_role: "cross_market_confirmation_for_probability_model".to_string(),
        paired_market_available: false,
        futures_symbol: None,
        spot_symbol: None,
        rolling_correlation_20: None,
        rolling_correlation_50: None,
        divergence_detected: None,
        cointegration_stat: None,
        cointegrated: None,
        raw_basis_bps: None,
        normalized_basis_bps: None,
        rolling_price_ratio_mean: None,
        notes: vec!["paired_market_not_provided".to_string()],
        narrative: "smt_analysis_unavailable_without_paired_market".to_string(),
    }
}

fn build_smt_correlation_section(
    futures_symbol: &str,
    spot_symbol: &str,
    futures_candles: &[Candle],
    spot_candles: &[Candle],
    auxiliary: &AuxiliaryMarketEvidence,
) -> SmtCorrelationSection {
    let (futures_series, spot_series) = aligned_close_series(futures_candles, spot_candles);
    let futures_returns = close_to_returns(&futures_series);
    let spot_returns = close_to_returns(&spot_series);
    let rolling_correlation_20 = Correlation::rolling(&futures_returns, &spot_returns, 20)
        .last()
        .copied();
    let rolling_correlation_50 = Correlation::rolling(&futures_returns, &spot_returns, 50)
        .last()
        .copied();
    let divergence_detected = Divergence::detect(&futures_series, &spot_series, 20)
        .last()
        .copied();
    let (cointegration_stat, cointegrated) =
        Cointegration::engle_granger(&futures_series, &spot_series);
    let narrative = if cointegrated && rolling_correlation_20.unwrap_or(0.0) > 0.6 {
        "paired_markets_are_aligned_and_statistically_supportive".to_string()
    } else if divergence_detected.unwrap_or(false) {
        "paired_markets_show_divergence_so_smt_confidence_is_reduced".to_string()
    } else {
        "paired_markets_offer_mixed_confirmation".to_string()
    };

    SmtCorrelationSection {
        probability_role: "cross_market_confirmation_for_probability_model".to_string(),
        paired_market_available: true,
        futures_symbol: Some(futures_symbol.to_string()),
        spot_symbol: Some(spot_symbol.to_string()),
        rolling_correlation_20,
        rolling_correlation_50,
        divergence_detected,
        cointegration_stat: Some(cointegration_stat),
        cointegrated: Some(cointegrated),
        raw_basis_bps: auxiliary.raw_basis_bps,
        normalized_basis_bps: auxiliary.normalized_basis_bps,
        rolling_price_ratio_mean: auxiliary.rolling_price_ratio_mean,
        notes: auxiliary.notes.clone(),
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

fn aligned_close_series(
    futures_candles: &[Candle],
    spot_candles: &[Candle],
) -> (Vec<f64>, Vec<f64>) {
    let len = futures_candles.len().min(spot_candles.len());
    let futures = futures_candles[futures_candles.len().saturating_sub(len)..]
        .iter()
        .map(|candle| candle.close)
        .collect();
    let spot = spot_candles[spot_candles.len().saturating_sub(len)..]
        .iter()
        .map(|candle| candle.close)
        .collect();
    (futures, spot)
}

fn close_to_returns(closes: &[f64]) -> Vec<f64> {
    closes
        .windows(2)
        .filter_map(|window| {
            let prev = window[0];
            let next = window[1];
            if prev.abs() <= f64::EPSILON {
                None
            } else {
                Some((next - prev) / prev)
            }
        })
        .collect()
}

fn build_frame_features(candles: &[Candle]) -> Result<FrameFeatures> {
    if candles.len() < INDICATOR_PERIOD * 2 + 1 {
        bail!(
            "need at least {} candles to build features, got {}",
            INDICATOR_PERIOD * 2 + 1,
            candles.len()
        );
    }

    let prices = candles_to_prices(candles);
    let initial_price = prices
        .first()
        .copied()
        .ok_or_else(|| anyhow!("candle series is empty"))?;

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

    let observations = build_observations(
        candles,
        candles,
        &implied_vol,
        &smoothed_prices,
        &atr,
        &rsi,
        &adx,
        &fvgs,
        &sweeps,
    );
    if observations.is_empty() {
        bail!(
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
        sweep_count: sweeps.len(),
        fvg_count: fvgs.len(),
    })
}

fn left_pad(values: Vec<f64>, target_len: usize, fill: f64) -> Vec<f64> {
    if values.len() >= target_len {
        return values[values.len() - target_len..].to_vec();
    }

    let mut padded = vec![fill; target_len - values.len()];
    padded.extend(values);
    padded
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
    for (entry_index, entry_state) in entry_quality.states.iter().enumerate() {
        let probabilities = trade_outcome
            .cpt
            .get(&vec![entry_index])
            .ok_or_else(|| anyhow!("missing CPT entry for entry_quality index {}", entry_index))?;
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
            network.topological_sort()?;
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

fn normalize_entry_quality_label(entry_signal: &str) -> String {
    let normalized = entry_signal.trim().to_ascii_lowercase();
    match normalized.as_str() {
        "high" | "strong_buy" | "strong_sell" | "a+" => "high".to_string(),
        "low" | "weak" | "invalid" | "no_trade" => "low".to_string(),
        "medium" | "buy" | "sell" | "valid" => "medium".to_string(),
        _ if normalized.contains("strong") || normalized.contains("high") => "high".to_string(),
        _ if normalized.contains("weak") || normalized.contains("low") => "low".to_string(),
        _ => "medium".to_string(),
    }
}

fn normalize_trade_outcome_label(outcome: &str) -> String {
    let normalized = outcome.trim().to_ascii_lowercase();
    match normalized.as_str() {
        "win" | "profit" | "tp" | "take_profit" => "win".to_string(),
        "loss" | "lose" | "sl" | "stop" | "stop_loss" => "loss".to_string(),
        _ => "breakeven".to_string(),
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

fn probability_map(states: &[String], probabilities: &[f64]) -> BTreeMap<String, f64> {
    states
        .iter()
        .cloned()
        .zip(probabilities.iter().copied())
        .collect()
}

fn distribution_from_map(states: &[String], probabilities: &BTreeMap<String, f64>) -> Vec<f64> {
    states
        .iter()
        .map(|state| probabilities.get(state).copied().unwrap_or(0.0))
        .collect()
}

fn neutral_options_summary(symbol: &str) -> ict_engine::data::realtime::openalice::OptionsChainSummary {
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

fn format_probability_map(states: &[String], probabilities: &[f64]) -> String {
    serde_json::to_string(&probability_map(states, probabilities))
        .unwrap_or_else(|_| "{}".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use ict_engine::bbn::trading::topology::build_trading_network;

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
}
