use serde::Serialize;

use crate::types::{Direction, RegimeProbs};

pub use crate::analyze::multi_timeframe_section::AnalyzeMultiTimeframeSection;
pub use crate::analyze::options_hedging_section::OptionsHedgingSection;
pub use crate::analyze::smt_correlation_section::{
    empty_smt_correlation_section, SmtCorrelationSection,
};
pub use crate::analyze::technical_price_section::TechnicalPriceSection;
pub use crate::ict::{GapReferenceLevel, ReferenceLiquidityLevelsEvidence};

#[derive(Debug, Serialize)]
pub struct AnalyzeSections {
    pub price_action: PriceActionSection,
    pub technical_price: TechnicalPriceSection,
    pub smt_correlation: SmtCorrelationSection,
    pub regime_bayesian: RegimeBayesianSection,
    pub multi_timeframe: AnalyzeMultiTimeframeSection,
    pub trade_plan: TradePlanSection,
}

#[derive(Debug, Serialize)]
pub struct PriceActionSection {
    pub probability_role: String,
    pub structure_bias: Direction,
    pub latest_break: Option<String>,
    pub latest_break_level: Option<f64>,
    pub latest_swing_high: Option<f64>,
    pub latest_swing_low: Option<f64>,
    pub recent_break_count: usize,
    pub swing_highs: usize,
    pub swing_lows: usize,
    pub bull_expansion: bool,
    pub bear_expansion: bool,
    pub expansion_strength: f64,
    pub liquidity_sweeps_recent: usize,
    pub nearest_liquidity_pool_level: Option<f64>,
    pub liquidity_pool_texture: LiquidityPoolTextureEvidence,
    pub latest_liquidity_sweep_level: Option<f64>,
    pub liquidity_sweep_quality: LiquiditySweepQualityEvidence,
    pub reference_liquidity_levels: ReferenceLiquidityLevelsEvidence,
    pub volume_imbalance_gap: VolumeImbalanceGapEvidence,
    pub open_fvgs: usize,
    pub nearest_open_fvg_top: Option<f64>,
    pub nearest_open_fvg_bottom: Option<f64>,
    pub untested_order_blocks: usize,
    pub nearest_untested_order_block_high: Option<f64>,
    pub nearest_untested_order_block_low: Option<f64>,
    pub order_block_variant: OrderBlockVariantEvidence,
    pub bullish_cisd: bool,
    pub bearish_cisd: bool,
    pub rejection_block_present: bool,
    pub narrative: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct LiquidityPoolTextureEvidence {
    pub factor_name: String,
    pub texture: String,
    pub subtype: String,
    pub level: Option<f64>,
    pub high: Option<f64>,
    pub low: Option<f64>,
    pub touch_count: usize,
    pub spacing_consistency: Option<f64>,
    pub clean_sweep_likelihood: Option<f64>,
    pub confidence: f64,
    pub fail_closed_reason: Option<String>,
}

impl LiquidityPoolTextureEvidence {
    pub fn fail_closed(reason: impl Into<String>) -> Self {
        Self {
            factor_name: "liquidity_pool_texture".to_string(),
            texture: "none".to_string(),
            subtype: "none".to_string(),
            level: None,
            high: None,
            low: None,
            touch_count: 0,
            spacing_consistency: None,
            clean_sweep_likelihood: None,
            confidence: 0.0,
            fail_closed_reason: Some(reason.into()),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct LiquiditySweepQualityEvidence {
    pub factor_name: String,
    pub quality: String,
    pub sweep_bar: Option<usize>,
    pub return_bar: Option<usize>,
    pub pool_price: Option<f64>,
    pub displacement_atr: Option<f64>,
    pub return_bars: Option<usize>,
    pub close_reclaim: Option<bool>,
    pub confidence: f64,
    pub fail_closed_reason: Option<String>,
}

impl LiquiditySweepQualityEvidence {
    pub fn fail_closed(reason: impl Into<String>) -> Self {
        Self {
            factor_name: "liquidity_sweep_quality".to_string(),
            quality: "none".to_string(),
            sweep_bar: None,
            return_bar: None,
            pool_price: None,
            displacement_atr: None,
            return_bars: None,
            close_reclaim: None,
            confidence: 0.0,
            fail_closed_reason: Some(reason.into()),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct VolumeImbalanceGapEvidence {
    pub factor_name: String,
    pub direction: Direction,
    pub top: Option<f64>,
    pub bottom: Option<f64>,
    pub midpoint: Option<f64>,
    pub start_bar: Option<usize>,
    pub filled: bool,
    pub active: bool,
    pub confidence: f64,
    pub fail_closed_reason: Option<String>,
}

impl VolumeImbalanceGapEvidence {
    pub fn fail_closed(reason: impl Into<String>) -> Self {
        Self {
            factor_name: "volume_imbalance_gap".to_string(),
            direction: Direction::Neutral,
            top: None,
            bottom: None,
            midpoint: None,
            start_bar: None,
            filled: false,
            active: false,
            confidence: 0.0,
            fail_closed_reason: Some(reason.into()),
        }
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct OrderBlockVariantEvidence {
    pub factor_name: String,
    pub variant: String,
    pub direction: Direction,
    pub high: Option<f64>,
    pub low: Option<f64>,
    pub midpoint: Option<f64>,
    pub validation_state: String,
    pub mitigation_count: usize,
    pub breaker_confirmed: bool,
    pub rejection_confirmed: bool,
    pub confidence: f64,
    pub fail_closed_reason: Option<String>,
}

impl OrderBlockVariantEvidence {
    pub fn fail_closed(reason: impl Into<String>) -> Self {
        Self {
            factor_name: "order_block_variant_classifier".to_string(),
            variant: "none".to_string(),
            direction: Direction::Neutral,
            high: None,
            low: None,
            midpoint: None,
            validation_state: "fail_closed".to_string(),
            mitigation_count: 0,
            breaker_confirmed: false,
            rejection_confirmed: false,
            confidence: 0.0,
            fail_closed_reason: Some(reason.into()),
        }
    }
}

#[derive(Debug, Serialize)]
pub struct RegimeBayesianSection {
    pub hmm_state: String,
    pub regime_probs: RegimeProbs,
    pub regime_label: String,
    pub liquidity_label: String,
    pub hybrid_regime_label: Option<String>,
    pub hybrid_transition_hazard: Option<f64>,
    pub hybrid_duration_model: Option<String>,
    pub hybrid_remaining_expected_bars: Option<f64>,
    pub pda_cluster_family: Option<String>,
    pub pda_hybrid_alignment: Option<bool>,
    pub long_score: f64,
    pub short_score: f64,
    pub win_prob_long: f64,
    pub win_prob_short: f64,
    pub selected_direction: Direction,
    pub evidence_policy: String,
    pub ict_role: String,
}

#[derive(Debug, Serialize)]
pub struct TradePlanSection {
    pub probability_role: String,
    pub actionable: bool,
    pub direction: Direction,
    pub entry: f64,
    pub stop_loss: f64,
    pub take_profits: Vec<f64>,
    pub risk_reward: f64,
    pub posterior: f64,
    pub win_probability: f64,
    pub kelly_fraction: f64,
    pub position_size: f64,
    pub uncertainties: Vec<String>,
    pub narrative: String,
}
