//! Market Structure Regime Classification
//!
//! 分类市场结构状态：Trending / MeanReverting / Ranging
//! 及 Wyckoff 周期：Accumulation / Markup / Distribution / Markdown

use crate::types::Candle;
use serde::{Deserialize, Serialize};

/// 市场结构状态
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum MarketStructureRegime {
    /// 趋势状态：价格持续朝一个方向运动
    Trending,
    /// 均值回归状态：价格在均值附近震荡
    MeanReverting,
    /// 区间震荡：价格在支撑阻力间波动
    Ranging,
    /// Wyckoff 积累阶段
    Accumulation,
    /// Wyckoff 派发阶段
    Distribution,
    /// 突破中
    Breakout,
    /// 突破失败
    Breakdown,
    #[default]
    Unknown,
}

/// ATR-compressed oscillation box state.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
pub struct OscillationBoxState {
    pub active: bool,
    pub box_high: Option<f64>,
    pub box_low: Option<f64>,
    pub touch_count: usize,
    pub atr_compression_ratio: f64,
    pub spacing_consistency: f64,
    pub confidence: f64,
    pub exit_reason: Option<String>,
}

impl MarketStructureRegime {
    pub fn label(&self) -> &'static str {
        match self {
            MarketStructureRegime::Trending => "trending",
            MarketStructureRegime::MeanReverting => "mean_reverting",
            MarketStructureRegime::Ranging => "ranging",
            MarketStructureRegime::Accumulation => "accumulation",
            MarketStructureRegime::Distribution => "distribution",
            MarketStructureRegime::Breakout => "breakout",
            MarketStructureRegime::Breakdown => "breakdown",
            MarketStructureRegime::Unknown => "unknown",
        }
    }
}

/// 市场结构分类器阈值配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StructureThresholds {
    /// ADX 趋势强度阈值：> trend_threshold 为趋势
    pub trend_threshold: f64,
    /// 均值回归阈值：价格偏离均值的程度
    pub mean_revert_threshold: f64,
    /// 区间识别：价格范围占比
    pub range_ratio_threshold: f64,
    /// ADX 计算周期
    pub adx_period: usize,
    /// 均值计算周期
    pub ma_period: usize,
    /// 区间识别回看窗口
    pub range_lookback: usize,
}

impl Default for StructureThresholds {
    fn default() -> Self {
        Self {
            trend_threshold: 25.0,       // ADX > 25 为趋势
            mean_revert_threshold: 0.02, // 价格偏离 2% 触发均值回归
            range_ratio_threshold: 0.6,  // 区间占比 > 60% 为震荡
            adx_period: 14,
            ma_period: 20,
            range_lookback: 50,
        }
    }
}

/// 市场结构分类器
pub struct MarketStructureClassifier {
    thresholds: StructureThresholds,
}

/// Box-specific thresholds are intentionally strict: the box must be
/// visibly compressed relative to ATR and have repeated boundary touches.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OscillationBoxThresholds {
    pub atr_period: usize,
    pub compression_threshold: f64,
    pub min_touch_count: usize,
    pub max_box_range_atr: f64,
    pub spacing_tolerance: f64,
    pub lookback: usize,
}

impl Default for OscillationBoxThresholds {
    fn default() -> Self {
        Self {
            atr_period: 14,
            compression_threshold: 0.65,
            min_touch_count: 3,
            max_box_range_atr: 2.0,
            spacing_tolerance: 0.35,
            lookback: 48,
        }
    }
}

impl MarketStructureClassifier {
    pub fn new() -> Self {
        Self::with_thresholds(StructureThresholds::default())
    }

    pub fn with_thresholds(thresholds: StructureThresholds) -> Self {
        Self { thresholds }
    }

    /// 分类市场结构状态，返回 (状态, 置信度)
    pub fn classify(&self, candles: &[Candle]) -> (MarketStructureRegime, f64) {
        if candles.len() < self.thresholds.adx_period + 1 {
            return (MarketStructureRegime::Unknown, 0.0);
        }

        let oscillation_box =
            self.detect_oscillation_box(candles, &OscillationBoxThresholds::default());
        let previous_box = if candles.len() > self.thresholds.adx_period + 2 {
            self.detect_oscillation_box(
                &candles[..candles.len() - 1],
                &OscillationBoxThresholds::default(),
            )
        } else {
            OscillationBoxState::default()
        };

        // 1. 计算 ADX（趋势强度）
        let adx = self.compute_adx(candles);
        let current_adx = *adx.last().unwrap_or(&20.0);

        // 2. 计算价格相对于均值的偏离
        let closes: Vec<f64> = candles.iter().map(|c| c.close).collect();
        let ma = self.compute_ma(&closes);
        let last_close = closes.last().copied().unwrap_or(0.0);
        let deviation = (last_close - ma).abs() / ma.max(1e-10);

        // 3. 计算区间特征
        let range_score = self.compute_range_score(&closes);

        // 4. 检测 Wyckoff 阶段
        let wyckoff_score = self.detect_wyckoff_phase(candles);

        let latest_atr = crate::indicators::atr::latest_atr(candles, 14);
        let last_candle = candles.last().expect("checked non-empty above");
        let breakout_buffer = latest_atr * 0.10;

        // 5. 综合分类
        let (regime, confidence) = if previous_box.active
            && last_candle.close
                > previous_box.box_high.unwrap_or(last_candle.close) + breakout_buffer
        {
            (
                MarketStructureRegime::Breakout,
                (previous_box.confidence + (current_adx / 50.0).min(1.0) * 0.35).clamp(0.55, 1.0),
            )
        } else if previous_box.active
            && last_candle.close
                < previous_box.box_low.unwrap_or(last_candle.close) - breakout_buffer
        {
            (
                MarketStructureRegime::Breakdown,
                (previous_box.confidence + (current_adx / 50.0).min(1.0) * 0.35).clamp(0.55, 1.0),
            )
        } else if oscillation_box.active {
            (
                MarketStructureRegime::Ranging,
                oscillation_box.confidence.max(range_score).clamp(0.55, 1.0),
            )
        } else if current_adx >= self.thresholds.trend_threshold {
            // 强趋势
            let conf = (current_adx / 50.0).min(1.0); // ADX 50 = 最高置信
            (MarketStructureRegime::Trending, conf)
        } else if wyckoff_score.0 > 0.6 {
            // Wyckoff 阶段检测
            (wyckoff_score.1, wyckoff_score.0)
        } else if deviation > self.thresholds.mean_revert_threshold {
            // 价格偏离均值较大，可能均值回归
            let conf = (deviation / 0.05).min(1.0);
            (MarketStructureRegime::MeanReverting, conf)
        } else if range_score > self.thresholds.range_ratio_threshold {
            // 区间震荡
            (MarketStructureRegime::Ranging, range_score)
        } else {
            (MarketStructureRegime::Unknown, 0.3)
        };

        (regime, confidence)
    }

    /// Detect an ATR-compressed oscillation box.
    pub fn detect_oscillation_box(
        &self,
        candles: &[Candle],
        thresholds: &OscillationBoxThresholds,
    ) -> OscillationBoxState {
        if candles.len() < thresholds.atr_period + 5 {
            return OscillationBoxState {
                exit_reason: Some("insufficient_bars".to_string()),
                ..OscillationBoxState::default()
            };
        }

        let lookback = thresholds.lookback.min(candles.len());
        let min_window = (thresholds.atr_period + 2)
            .max(thresholds.min_touch_count * 3)
            .min(lookback);
        let start = candles.len() - lookback;

        let mut best_active: Option<(usize, OscillationBoxState)> = None;
        let mut best_inactive: Option<(usize, OscillationBoxState)> = None;

        for window_len in min_window..=lookback {
            let window = &candles[candles.len() - window_len..];
            let candidate = self.evaluate_oscillation_box_window(window, thresholds);
            if candidate.active {
                let replace = match &best_active {
                    None => true,
                    Some((best_len, best_state)) => {
                        candidate.confidence > best_state.confidence
                            || (candidate.confidence - best_state.confidence).abs() < 1e-9
                                && window_len > *best_len
                    }
                };
                if replace {
                    best_active = Some((window_len, candidate));
                }
            } else {
                let replace = match &best_inactive {
                    None => true,
                    Some((best_len, best_state)) => {
                        candidate.touch_count > best_state.touch_count
                            || (candidate.touch_count == best_state.touch_count
                                && candidate.atr_compression_ratio
                                    < best_state.atr_compression_ratio)
                            || (candidate.touch_count == best_state.touch_count
                                && (candidate.atr_compression_ratio
                                    - best_state.atr_compression_ratio)
                                    .abs()
                                    < 1e-9
                                && window_len > *best_len)
                    }
                };
                if replace {
                    best_inactive = Some((window_len, candidate));
                }
            }
        }

        best_active
            .map(|(_, state)| state)
            .or_else(|| best_inactive.map(|(_, state)| state))
            .unwrap_or(OscillationBoxState {
                exit_reason: Some(format!("no_candidate_window_from_{}", start)),
                ..OscillationBoxState::default()
            })
    }

    fn evaluate_oscillation_box_window(
        &self,
        window: &[Candle],
        thresholds: &OscillationBoxThresholds,
    ) -> OscillationBoxState {
        let atr_series = crate::indicators::atr::compute_atr(window, thresholds.atr_period);
        let Some(&latest_atr) = atr_series.last() else {
            return OscillationBoxState {
                exit_reason: Some("atr_unavailable".to_string()),
                ..OscillationBoxState::default()
            };
        };
        if latest_atr <= f64::EPSILON {
            return OscillationBoxState {
                exit_reason: Some("zero_atr".to_string()),
                ..OscillationBoxState::default()
            };
        }

        let top_k = thresholds.min_touch_count.max(2).min(window.len());
        let mut highs = window.iter().map(|c| c.high).collect::<Vec<_>>();
        highs.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        let mut lows = window.iter().map(|c| c.low).collect::<Vec<_>>();
        lows.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));
        let box_high = highs[top_k - 1];
        let box_low = lows[top_k - 1];
        let box_range = box_high - box_low;
        let atr_compression_ratio = (box_range / latest_atr).clamp(0.0, 10.0);

        let mid = (box_high + box_low) / 2.0;
        let touches = window
            .iter()
            .filter(|c| {
                (c.high - box_high).abs() <= latest_atr * 0.15
                    || (c.low - box_low).abs() <= latest_atr * 0.15
                    || (c.close - mid).abs() <= latest_atr * 0.10
            })
            .count();
        let touch_count = touches.min(window.len());
        let spacing_consistency = self.compute_spacing_consistency(window, box_high, box_low);
        let compressed = box_range <= latest_atr * thresholds.max_box_range_atr
            && atr_compression_ratio <= thresholds.max_box_range_atr
            && atr_compression_ratio <= thresholds.compression_threshold * 4.0;
        let active = compressed && touch_count >= thresholds.min_touch_count;
        let confidence = if active {
            (1.0 - (atr_compression_ratio / thresholds.max_box_range_atr).min(1.0)) * 0.45
                + (touch_count as f64 / (thresholds.min_touch_count as f64 + 2.0)).min(1.0) * 0.35
                + spacing_consistency * 0.20
        } else {
            0.0
        }
        .clamp(0.0, 1.0);

        let exit_reason = if active {
            None
        } else if !compressed {
            Some("atr_not_compressed".to_string())
        } else {
            Some("insufficient_touches".to_string())
        };

        OscillationBoxState {
            active,
            box_high: Some(box_high),
            box_low: Some(box_low),
            touch_count,
            atr_compression_ratio,
            spacing_consistency,
            confidence,
            exit_reason,
        }
    }

    fn compute_spacing_consistency(&self, candles: &[Candle], box_high: f64, box_low: f64) -> f64 {
        if candles.len() < 4 {
            return 0.0;
        }
        let mid = (box_high + box_low) / 2.0;
        let mut touch_positions = Vec::new();
        for (idx, candle) in candles.iter().enumerate() {
            if (candle.high - box_high).abs() <= (box_high - box_low) * 0.08
                || (candle.low - box_low).abs() <= (box_high - box_low) * 0.08
                || (candle.close - mid).abs() <= (box_high - box_low) * 0.06
            {
                touch_positions.push(idx as f64);
            }
        }
        if touch_positions.len() < 3 {
            return 0.0;
        }
        let mut gaps = Vec::new();
        for win in touch_positions.windows(2) {
            gaps.push(win[1] - win[0]);
        }
        let mean = gaps.iter().sum::<f64>() / gaps.len() as f64;
        if mean <= f64::EPSILON {
            return 0.0;
        }
        let variance = gaps.iter().map(|gap| (gap - mean).powi(2)).sum::<f64>() / gaps.len() as f64;
        (1.0 / (1.0 + variance.sqrt() / mean)).clamp(0.0, 1.0)
    }

    /// 计算 ADX（Average Directional Index）
    fn compute_adx(&self, candles: &[Candle]) -> Vec<f64> {
        let period = self.thresholds.adx_period;
        if candles.len() < period + 1 {
            return vec![20.0]; // 默认中等趋势
        }

        // 计算 +DM 和 -DM
        let mut plus_dm = vec![0.0];
        let mut minus_dm = vec![0.0];
        let mut tr = vec![0.0];

        for i in 1..candles.len() {
            let up_move = candles[i].high - candles[i - 1].high;
            let down_move = candles[i - 1].low - candles[i].low;

            let plus = if up_move > down_move && up_move > 0.0 {
                up_move
            } else {
                0.0
            };
            let minus = if down_move > up_move && down_move > 0.0 {
                down_move
            } else {
                0.0
            };

            plus_dm.push(plus);
            minus_dm.push(minus);

            let true_range = (candles[i].high - candles[i].low)
                .max((candles[i].high - candles[i - 1].close).abs())
                .max((candles[i].low - candles[i - 1].close).abs());
            tr.push(true_range);
        }

        // 平滑处理
        let smooth_plus = self.ema(&plus_dm, period);
        let smooth_minus = self.ema(&minus_dm, period);
        let smooth_tr = self.ema(&tr, period);

        // 计算 +DI 和 -DI
        let mut adx = Vec::new();
        for i in 0..smooth_plus
            .len()
            .min(smooth_minus.len())
            .min(smooth_tr.len())
        {
            let plus_di = if smooth_tr[i] > 0.0 {
                100.0 * smooth_plus[i] / smooth_tr[i]
            } else {
                0.0
            };
            let minus_di = if smooth_tr[i] > 0.0 {
                100.0 * smooth_minus[i] / smooth_tr[i]
            } else {
                0.0
            };

            let dx = if plus_di + minus_di > 0.0 {
                100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di)
            } else {
                0.0
            };
            adx.push(dx);
        }

        // 再次平滑得到 ADX
        self.ema(&adx, period)
    }

    /// EMA 平滑
    fn ema(&self, data: &[f64], period: usize) -> Vec<f64> {
        if data.is_empty() {
            return Vec::new();
        }

        let multiplier = 2.0 / (period as f64 + 1.0);
        let mut result = vec![data[0]];

        for i in 1..data.len() {
            let ema_val = data[i] * multiplier + result[i - 1] * (1.0 - multiplier);
            result.push(ema_val);
        }

        result
    }

    /// 计算简单移动平均
    fn compute_ma(&self, closes: &[f64]) -> f64 {
        let period = self.thresholds.ma_period.min(closes.len());
        if period == 0 {
            return closes.last().copied().unwrap_or(0.0);
        }

        let slice = &closes[closes.len() - period..];
        slice.iter().sum::<f64>() / period as f64
    }

    /// 计算区间震荡分数
    fn compute_range_score(&self, closes: &[f64]) -> f64 {
        let lookback = self.thresholds.range_lookback.min(closes.len());
        if lookback < 2 {
            return 0.0;
        }

        let slice = &closes[closes.len() - lookback..];
        let high = slice.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let low = slice.iter().cloned().fold(f64::INFINITY, f64::min);
        let range = high - low;

        if range < 1e-10 {
            return 0.0;
        }

        // 计算价格穿越中值的次数
        let mid = (high + low) / 2.0;
        let mut crosses = 0;
        for i in 1..slice.len() {
            if (slice[i] - mid) * (slice[i - 1] - mid) < 0.0 {
                crosses += 1;
            }
        }

        // 穿越次数越多，区间特征越明显
        crosses as f64 / (lookback as f64 / 2.0)
    }

    /// 检测 Wyckoff 阶段（简化版）
    fn detect_wyckoff_phase(&self, candles: &[Candle]) -> (f64, MarketStructureRegime) {
        if candles.len() < 100 {
            return (0.0, MarketStructureRegime::Unknown);
        }

        let closes: Vec<f64> = candles.iter().map(|c| c.close).collect();
        let volumes: Vec<f64> = candles.iter().map(|c| c.volume).collect();

        let lookback = 50.min(closes.len());
        let recent = &closes[closes.len() - lookback..];
        let recent_vol = &volumes[volumes.len() - lookback..];

        let high = recent.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
        let low = recent.iter().cloned().fold(f64::INFINITY, f64::min);
        let mid = (high + low) / 2.0;

        // 低位缩量震荡 + 突破放量 = Accumulation
        // 高位放量震荡 + 破位缩量 = Distribution

        let avg_vol = recent_vol.iter().sum::<f64>() / recent_vol.len() as f64;
        let last_vol = *recent_vol.last().unwrap_or(&avg_vol);
        let last_close = *recent.last().unwrap_or(&mid);

        // 价格在低位区间 + 成交量萎缩
        let is_accumulation = last_close < mid && last_vol < avg_vol * 0.8;
        // 价格在高位区间 + 成交量放大
        let is_distribution = last_close > mid && last_vol > avg_vol * 1.2;

        if is_accumulation {
            (0.65, MarketStructureRegime::Accumulation)
        } else if is_distribution {
            (0.65, MarketStructureRegime::Distribution)
        } else {
            (0.0, MarketStructureRegime::Unknown)
        }
    }
}

impl Default for MarketStructureClassifier {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::indicators::atr::compute_atr;
    use chrono::{TimeZone, Utc};

    fn trend_candles(count: usize, direction: f64) -> Vec<Candle> {
        (0..count)
            .map(|i| {
                let base = 100.0 + direction * i as f64;
                Candle {
                    timestamp: Utc.timestamp_opt(1_700_000_000 + i as i64 * 60, 0).unwrap(),
                    open: base,
                    high: base + 1.0,
                    low: base - 0.5,
                    close: base + direction * 0.5,
                    volume: 1000.0,
                }
            })
            .collect()
    }

    fn range_candles(count: usize) -> Vec<Candle> {
        (0..count)
            .map(|i| {
                let base = 100.0 + (i as f64 % 10.0 - 5.0) * 2.0; // 震荡
                Candle {
                    timestamp: Utc.timestamp_opt(1_700_000_000 + i as i64 * 60, 0).unwrap(),
                    open: base,
                    high: base + 1.0,
                    low: base - 1.0,
                    close: base,
                    volume: 1000.0,
                }
            })
            .collect()
    }

    fn box_candles(count: usize) -> Vec<Candle> {
        let template = [
            100.00, 100.18, 100.04, 100.16, 100.02, 100.17, 100.05, 100.15, 100.03, 100.19,
        ];
        (0..count)
            .map(|i| {
                let close = template[i % template.len()];
                Candle {
                    timestamp: Utc.timestamp_opt(1_700_500_000 + i as i64 * 60, 0).unwrap(),
                    open: close - 0.02,
                    high: close + 0.03,
                    low: close - 0.03,
                    close,
                    volume: 900.0 + (i % 3) as f64 * 20.0,
                }
            })
            .collect()
    }

    fn box_candles_with_single_outlier(count: usize) -> Vec<Candle> {
        let mut candles = box_candles(count);
        let idx = count / 2;
        candles[idx].high += 1.50;
        candles[idx].low -= 1.20;
        candles
    }

    fn expanding_history_then_box(count: usize) -> Vec<Candle> {
        let mut candles = trend_candles(count / 2, 0.6);
        let mut tail = box_candles(count - candles.len());
        let offset = candles.last().map(|c| c.close - 100.0).unwrap_or_default();
        for candle in &mut tail {
            candle.open += offset;
            candle.high += offset;
            candle.low += offset;
            candle.close += offset;
        }
        candles.extend(tail);
        candles
    }

    #[test]
    fn trending_detection() {
        let candles = trend_candles(100, 0.5); // 上涨趋势
        let classifier = MarketStructureClassifier::new();
        let (regime, _conf) = classifier.classify(&candles);

        assert!(matches!(
            regime,
            MarketStructureRegime::Trending | MarketStructureRegime::Unknown
        ));
    }

    #[test]
    fn ranging_detection() {
        let candles = range_candles(100); // 震荡
        let classifier = MarketStructureClassifier::new();
        let (regime, _conf) = classifier.classify(&candles);

        assert!(matches!(
            regime,
            MarketStructureRegime::Ranging
                | MarketStructureRegime::MeanReverting
                | MarketStructureRegime::Unknown
        ));
    }

    #[test]
    fn detects_atr_compressed_box() {
        let candles = box_candles(80);
        let classifier = MarketStructureClassifier::new();
        let state =
            classifier.detect_oscillation_box(&candles, &OscillationBoxThresholds::default());

        assert!(state.active, "{state:?}");
        assert!(state.box_high.unwrap() > state.box_low.unwrap());
        assert!(state.touch_count >= 3);
        assert!(state.atr_compression_ratio > 0.0);
        assert!(state.confidence > 0.0);
    }

    #[test]
    fn box_biases_classification_toward_ranging() {
        let candles = box_candles(80);
        let classifier = MarketStructureClassifier::new();
        let (regime, conf) = classifier.classify(&candles);

        assert_eq!(regime, MarketStructureRegime::Ranging);
        assert!(conf >= 0.55, "{conf}");
    }

    #[test]
    fn rejects_strong_trend_as_box() {
        let candles = trend_candles(80, 0.8);
        let classifier = MarketStructureClassifier::new();
        let state =
            classifier.detect_oscillation_box(&candles, &OscillationBoxThresholds::default());

        assert!(!state.active);
        assert!(matches!(
            state.exit_reason.as_deref(),
            Some("atr_not_compressed") | Some("insufficient_touches")
        ));
        assert_eq!(state.confidence, 0.0);
        assert!(!compute_atr(&candles, 14).is_empty());
    }

    #[test]
    fn classifies_breakout_after_atr_box_exit() {
        let mut candles = box_candles(79);
        candles.push(Candle {
            timestamp: Utc.timestamp_opt(1_700_500_000 + 79 * 60, 0).unwrap(),
            open: 100.18,
            high: 100.62,
            low: 100.14,
            close: 100.58,
            volume: 1200.0,
        });
        let classifier = MarketStructureClassifier::new();
        let (regime, confidence) = classifier.classify(&candles);

        assert_eq!(
            regime,
            MarketStructureRegime::Breakout,
            "{regime:?} / {confidence}"
        );
        assert!(confidence > 0.0);
    }

    #[test]
    fn single_outlier_does_not_destroy_box_detection() {
        let candles = box_candles_with_single_outlier(80);
        let classifier = MarketStructureClassifier::new();
        let state =
            classifier.detect_oscillation_box(&candles, &OscillationBoxThresholds::default());

        assert!(state.active, "{state:?}");
        assert!(state.confidence > 0.0);
    }

    #[test]
    fn older_expansion_does_not_destroy_recent_box() {
        let candles = expanding_history_then_box(80);
        let classifier = MarketStructureClassifier::new();
        let state =
            classifier.detect_oscillation_box(&candles, &OscillationBoxThresholds::default());

        assert!(state.active, "{state:?}");
        assert!(state.touch_count >= 3);
    }
}
