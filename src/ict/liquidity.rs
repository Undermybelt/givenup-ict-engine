use crate::types::{
    Candle, Direction, LiquidityPool, LiquidityPoolSubtypeKind, LiquidityPoolTextureClassification,
    LiquidityPoolTextureKind, LiquiditySweep, LiquiditySweepQualityClassification,
    LiquiditySweepQualityKind,
};

/// Detect liquidity pools (areas where multiple swing points cluster)
pub fn detect_liquidity_pools(
    candles: &[Candle],
    atr: &[f64],
    atr_multiplier: f64,
    min_touches: usize,
) -> Vec<LiquidityPool> {
    let swings = super::swing::find_all_swing_points(candles, 3);
    let mut pools = Vec::new();

    // Group swing points by price level
    let tolerance = if atr.is_empty() {
        10.0
    } else {
        atr.last().copied().unwrap_or(10.0) * atr_multiplier
    };

    let mut used = vec![false; swings.len()];

    for i in 0..swings.len() {
        if used[i] {
            continue;
        }

        let mut cluster = vec![&swings[i]];
        used[i] = true;

        for j in i + 1..swings.len() {
            if used[j] {
                continue;
            }

            if (swings[j].price - swings[i].price).abs() <= tolerance {
                cluster.push(&swings[j]);
                used[j] = true;
            }
        }

        if cluster.len() >= min_touches {
            let avg_price: f64 =
                cluster.iter().map(|sp| sp.price).sum::<f64>() / cluster.len() as f64;
            let pool_type = if cluster.iter().any(|sp| sp.sp_type == Direction::Bear) {
                Direction::Bear // Resistance
            } else {
                Direction::Bull // Support
            };

            pools.push(LiquidityPool {
                price_level: avg_price,
                sp_count: cluster.len(),
                pool_type,
            });
        }
    }

    pools.sort_by(|a, b| {
        a.price_level
            .partial_cmp(&b.price_level)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    pools
}

/// Detect liquidity sweeps (price breaks through pool then returns)
pub fn detect_liquidity_sweep(
    candles: &[Candle],
    pools: &[LiquidityPool],
    return_bars: usize,
) -> Vec<LiquiditySweep> {
    if candles.len() <= return_bars {
        return Vec::new();
    }

    let mut sweeps = Vec::new();

    for pool in pools {
        for i in 0..candles.len() - return_bars {
            let candle = &candles[i];

            // Check for sweep above resistance
            if pool.pool_type == Direction::Bear && candle.high > pool.price_level {
                // Check if price returns below within return_bars
                let mut returned = false;
                let mut return_bar = i;

                for (j, candle) in candles
                    .iter()
                    .enumerate()
                    .skip(i + 1)
                    .take(return_bars.min(candles.len() - i - 1))
                {
                    if candle.close < pool.price_level {
                        returned = true;
                        return_bar = j;
                        break;
                    }
                }

                if returned {
                    sweeps.push(LiquiditySweep {
                        sweep_bar: i,
                        return_bar,
                        pool_price: pool.price_level,
                        sweep_direction: Direction::Bear, // Sweep above then return down
                    });
                }
            }

            // Check for sweep below support
            if pool.pool_type == Direction::Bull && candle.low < pool.price_level {
                // Check if price returns above within return_bars
                let mut returned = false;
                let mut return_bar = i;

                for (j, candle) in candles
                    .iter()
                    .enumerate()
                    .skip(i + 1)
                    .take(return_bars.min(candles.len() - i - 1))
                {
                    if candle.close > pool.price_level {
                        returned = true;
                        return_bar = j;
                        break;
                    }
                }

                if returned {
                    sweeps.push(LiquiditySweep {
                        sweep_bar: i,
                        return_bar,
                        pool_price: pool.price_level,
                        sweep_direction: Direction::Bull, // Sweep below then return up
                    });
                }
            }
        }
    }

    sweeps
}

/// Count recent liquidity sweeps
pub fn count_recent_sweeps(
    candles: &[Candle],
    sweeps: &[LiquiditySweep],
    lookback: usize,
) -> usize {
    let threshold = candles.len().saturating_sub(lookback);
    sweeps.iter().filter(|s| s.sweep_bar >= threshold).count()
}

pub fn classify_liquidity_sweep_quality(
    candles: &[Candle],
    atr: &[f64],
    sweep: Option<&LiquiditySweep>,
) -> LiquiditySweepQualityClassification {
    let Some(sweep) = sweep else {
        return LiquiditySweepQualityClassification::fail_closed("no_liquidity_sweep_detected");
    };
    if sweep.sweep_bar >= candles.len() || sweep.return_bar >= candles.len() {
        return LiquiditySweepQualityClassification::fail_closed(
            "liquidity_sweep_index_out_of_range",
        );
    }
    let Some(atr_at_sweep) = atr_value_for_bar(candles, atr, sweep.sweep_bar) else {
        return LiquiditySweepQualityClassification::fail_closed(
            "missing_atr_for_liquidity_sweep_quality",
        );
    };
    if sweep.return_bar < sweep.sweep_bar {
        return LiquiditySweepQualityClassification::fail_closed(
            "liquidity_sweep_return_before_sweep",
        );
    }

    let sweep_candle = &candles[sweep.sweep_bar];
    let return_candle = &candles[sweep.return_bar];
    let displacement = match sweep.sweep_direction {
        Direction::Bear => (sweep_candle.high - sweep.pool_price).max(0.0),
        Direction::Bull => (sweep.pool_price - sweep_candle.low).max(0.0),
        Direction::Neutral => 0.0,
    };
    let displacement_atr = displacement / atr_at_sweep;
    let return_bars = sweep.return_bar.saturating_sub(sweep.sweep_bar);
    let close_reclaim = match sweep.sweep_direction {
        Direction::Bear => return_candle.close < sweep.pool_price,
        Direction::Bull => return_candle.close > sweep.pool_price,
        Direction::Neutral => false,
    };
    let wick_only = match sweep.sweep_direction {
        Direction::Bear => sweep_candle.close <= sweep.pool_price,
        Direction::Bull => sweep_candle.close >= sweep.pool_price,
        Direction::Neutral => false,
    };
    let follow_through = post_sweep_contamination(candles, sweep);
    let fast_return = return_bars <= 3;
    let adequate_displacement = (0.05..=1.25).contains(&displacement_atr);

    let quality = if close_reclaim && fast_return && adequate_displacement && wick_only {
        LiquiditySweepQualityKind::Clean
    } else if !close_reclaim || return_bars > 8 || displacement_atr > 1.75 || follow_through {
        LiquiditySweepQualityKind::Dirty
    } else {
        LiquiditySweepQualityKind::Mixed
    };
    let confidence = match quality {
        LiquiditySweepQualityKind::Clean => (0.45
            + (1.0 - (return_bars as f64 / 8.0)).max(0.0) * 0.20
            + (1.25 - displacement_atr).max(0.0).min(1.0) * 0.15)
            .clamp(0.0, 0.82),
        LiquiditySweepQualityKind::Dirty => {
            (0.42 + (return_bars as f64 / 10.0).min(0.25) + (displacement_atr / 4.0).min(0.20))
                .clamp(0.0, 0.78)
        }
        LiquiditySweepQualityKind::Mixed => 0.48,
        LiquiditySweepQualityKind::None => 0.0,
    };

    LiquiditySweepQualityClassification {
        quality,
        sweep_bar: Some(sweep.sweep_bar),
        return_bar: Some(sweep.return_bar),
        pool_price: Some(sweep.pool_price),
        displacement_atr: Some(displacement_atr),
        return_bars: Some(return_bars),
        close_reclaim: Some(close_reclaim),
        confidence,
        fail_closed_reason: None,
    }
}

fn atr_value_for_bar(candles: &[Candle], atr: &[f64], bar: usize) -> Option<f64> {
    if candles.is_empty() || atr.is_empty() {
        return None;
    }
    let atr_idx = bar.saturating_sub(candles.len().saturating_sub(atr.len()));
    atr.get(atr_idx.min(atr.len() - 1))
        .copied()
        .filter(|value| value.is_finite() && *value > 0.0)
}

fn post_sweep_contamination(candles: &[Candle], sweep: &LiquiditySweep) -> bool {
    let end = (sweep.return_bar + 3).min(candles.len().saturating_sub(1));
    if sweep.return_bar >= end {
        return false;
    }
    candles[sweep.return_bar + 1..=end]
        .iter()
        .any(|candle| match sweep.sweep_direction {
            Direction::Bear => candle.close > sweep.pool_price,
            Direction::Bull => candle.close < sweep.pool_price,
            Direction::Neutral => false,
        })
}

pub fn classify_liquidity_pool_texture(
    candles: &[Candle],
    atr: &[f64],
    pool: Option<&LiquidityPool>,
) -> LiquidityPoolTextureClassification {
    let Some(pool) = pool else {
        return LiquidityPoolTextureClassification::fail_closed("no_liquidity_pool_detected");
    };
    let Some(atr_last) = atr
        .iter()
        .rev()
        .copied()
        .find(|value| value.is_finite() && *value > 0.0)
    else {
        return LiquidityPoolTextureClassification::fail_closed(
            "missing_atr_for_liquidity_pool_texture",
        );
    };
    if candles.len() < 5 {
        return LiquidityPoolTextureClassification::fail_closed(
            "insufficient_candles_for_liquidity_pool_texture",
        );
    }

    let tolerance = (atr_last * 0.35).max(pool.price_level.abs() * 0.0002);
    let touch_indices = candles
        .iter()
        .enumerate()
        .filter_map(|(index, candle)| {
            let touched = match pool.pool_type {
                Direction::Bear => (candle.high - pool.price_level).abs() <= tolerance,
                Direction::Bull => (candle.low - pool.price_level).abs() <= tolerance,
                Direction::Neutral => {
                    candle.low <= pool.price_level + tolerance
                        && candle.high >= pool.price_level - tolerance
                }
            };
            touched.then_some(index)
        })
        .collect::<Vec<_>>();
    let touch_count = pool.sp_count.max(touch_indices.len());
    if touch_count < 2 {
        return LiquidityPoolTextureClassification::fail_closed(
            "insufficient_pool_touches_for_texture",
        );
    }

    let spacing_consistency = spacing_consistency_score(&touch_indices);
    let consistency_for_texture = spacing_consistency.unwrap_or(0.35);
    let texture = if touch_count >= 3 && consistency_for_texture >= 0.65 {
        LiquidityPoolTextureKind::Smooth
    } else if consistency_for_texture < 0.4 {
        LiquidityPoolTextureKind::Jagged
    } else {
        LiquidityPoolTextureKind::Mixed
    };
    let subtype = classify_liquidity_pool_subtype(pool.pool_type, texture);
    let touch_score = (touch_count as f64 / 6.0).min(1.0);
    let clean_sweep_likelihood =
        (0.20 + touch_score * 0.35 + consistency_for_texture * 0.35).clamp(0.0, 0.90);
    let confidence = (0.32 + touch_score * 0.26 + consistency_for_texture * 0.22).clamp(0.0, 0.82);

    LiquidityPoolTextureClassification {
        texture,
        subtype,
        level: Some(pool.price_level),
        high: Some(pool.price_level + tolerance),
        low: Some(pool.price_level - tolerance),
        touch_count,
        spacing_consistency,
        clean_sweep_likelihood: Some(clean_sweep_likelihood),
        confidence,
        fail_closed_reason: None,
    }
}

fn classify_liquidity_pool_subtype(
    pool_type: Direction,
    texture: LiquidityPoolTextureKind,
) -> LiquidityPoolSubtypeKind {
    match (pool_type, texture) {
        (Direction::Bear, LiquidityPoolTextureKind::Smooth) => {
            LiquidityPoolSubtypeKind::EqualHighPool
        }
        (Direction::Bull, LiquidityPoolTextureKind::Smooth) => {
            LiquidityPoolSubtypeKind::EqualLowPool
        }
        (Direction::Bear, LiquidityPoolTextureKind::Jagged | LiquidityPoolTextureKind::Mixed) => {
            LiquidityPoolSubtypeKind::RelativeEqualHigh
        }
        (Direction::Bull, LiquidityPoolTextureKind::Jagged | LiquidityPoolTextureKind::Mixed) => {
            LiquidityPoolSubtypeKind::RelativeEqualLow
        }
        _ => LiquidityPoolSubtypeKind::None,
    }
}

fn spacing_consistency_score(indices: &[usize]) -> Option<f64> {
    if indices.len() < 3 {
        return None;
    }
    let gaps = indices
        .windows(2)
        .filter_map(|pair| pair[1].checked_sub(pair[0]))
        .filter(|gap| *gap > 0)
        .map(|gap| gap as f64)
        .collect::<Vec<_>>();
    if gaps.len() < 2 {
        return None;
    }
    let mean = gaps.iter().sum::<f64>() / gaps.len() as f64;
    if mean <= f64::EPSILON {
        return None;
    }
    let variance = gaps
        .iter()
        .map(|gap| {
            let diff = gap - mean;
            diff * diff
        })
        .sum::<f64>()
        / gaps.len() as f64;
    let cv = variance.sqrt() / mean;
    Some((1.0 - cv).clamp(0.0, 1.0))
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{TimeZone, Utc};

    fn candle(ts: i64, open: f64, high: f64, low: f64, close: f64) -> Candle {
        Candle {
            timestamp: Utc.timestamp_opt(ts, 0).single().expect("valid ts"),
            open,
            high,
            low,
            close,
            volume: 1.0,
        }
    }

    #[test]
    fn detect_liquidity_sweep_returns_empty_for_short_windows() {
        let candles = vec![
            candle(1, 100.0, 101.0, 99.0, 100.5),
            candle(2, 100.5, 101.5, 100.0, 101.0),
            candle(3, 101.0, 102.0, 100.5, 101.5),
        ];
        let pools = vec![LiquidityPool {
            price_level: 101.0,
            sp_count: 2,
            pool_type: Direction::Bear,
        }];

        let sweeps = detect_liquidity_sweep(&candles, &pools, 5);
        assert!(sweeps.is_empty());
    }

    #[test]
    fn classify_liquidity_pool_texture_scores_smooth_pool() {
        let candles = vec![
            candle(1, 98.0, 98.5, 97.5, 98.2),
            candle(2, 98.2, 100.1, 98.0, 99.3),
            candle(3, 99.2, 99.4, 98.4, 98.8),
            candle(4, 98.8, 100.0, 98.5, 99.2),
            candle(5, 99.2, 99.5, 98.7, 99.1),
            candle(6, 99.1, 100.2, 98.9, 99.4),
            candle(7, 99.4, 99.7, 98.8, 99.0),
            candle(8, 99.0, 100.1, 98.7, 99.2),
        ];
        let pool = LiquidityPool {
            price_level: 100.0,
            sp_count: 4,
            pool_type: Direction::Bear,
        };
        let evidence =
            classify_liquidity_pool_texture(&candles, &vec![1.0; candles.len()], Some(&pool));
        assert_eq!(evidence.texture, LiquidityPoolTextureKind::Smooth);
        assert_eq!(evidence.subtype, LiquidityPoolSubtypeKind::EqualHighPool);
        assert!(evidence.spacing_consistency.unwrap() >= 0.65);
        assert!(evidence.clean_sweep_likelihood.unwrap() > 0.65);
    }

    #[test]
    fn classify_liquidity_pool_texture_labels_equal_low_pool() {
        let candles = vec![
            candle(1, 101.5, 102.0, 100.1, 101.0),
            candle(2, 101.0, 101.4, 100.0, 100.8),
            candle(3, 100.8, 101.2, 100.2, 101.0),
            candle(4, 101.0, 101.3, 100.1, 100.9),
            candle(5, 100.9, 101.5, 100.3, 101.1),
            candle(6, 101.1, 101.4, 100.0, 100.7),
            candle(7, 100.7, 101.3, 100.2, 101.0),
            candle(8, 101.0, 101.4, 100.1, 100.9),
        ];
        let pool = LiquidityPool {
            price_level: 100.0,
            sp_count: 4,
            pool_type: Direction::Bull,
        };

        let evidence =
            classify_liquidity_pool_texture(&candles, &vec![1.0; candles.len()], Some(&pool));

        assert_eq!(evidence.texture, LiquidityPoolTextureKind::Smooth);
        assert_eq!(evidence.subtype, LiquidityPoolSubtypeKind::EqualLowPool);
    }

    #[test]
    fn classify_liquidity_pool_texture_scores_jagged_pool() {
        let candles = vec![
            candle(1, 98.0, 100.1, 97.5, 98.2),
            candle(2, 98.2, 100.2, 98.0, 98.3),
            candle(3, 98.3, 99.0, 98.1, 98.7),
            candle(4, 98.7, 99.2, 98.2, 99.1),
            candle(5, 99.1, 99.4, 98.7, 99.2),
            candle(6, 99.2, 99.5, 98.9, 99.3),
            candle(7, 99.3, 99.7, 98.8, 99.4),
            candle(8, 99.4, 99.6, 98.7, 99.0),
            candle(9, 99.0, 100.1, 98.7, 99.2),
        ];
        let pool = LiquidityPool {
            price_level: 100.0,
            sp_count: 3,
            pool_type: Direction::Bear,
        };
        let evidence =
            classify_liquidity_pool_texture(&candles, &vec![1.0; candles.len()], Some(&pool));
        assert_eq!(evidence.texture, LiquidityPoolTextureKind::Jagged);
        assert_eq!(
            evidence.subtype,
            LiquidityPoolSubtypeKind::RelativeEqualHigh
        );
        assert!(evidence.spacing_consistency.unwrap() < 0.4);
    }

    #[test]
    fn classify_liquidity_sweep_quality_clean_wick_reclaim() {
        let candles = vec![
            candle(1, 99.5, 100.0, 99.2, 99.8),
            candle(2, 99.8, 100.3, 99.4, 99.9),
            candle(3, 99.9, 100.1, 99.5, 99.7),
        ];
        let sweep = LiquiditySweep {
            sweep_bar: 1,
            return_bar: 2,
            pool_price: 100.0,
            sweep_direction: Direction::Bear,
        };

        let evidence =
            classify_liquidity_sweep_quality(&candles, &vec![1.0; candles.len()], Some(&sweep));

        assert_eq!(evidence.quality, LiquiditySweepQualityKind::Clean);
        assert_eq!(evidence.return_bars, Some(1));
        assert_eq!(evidence.close_reclaim, Some(true));
        assert!(evidence.confidence > 0.55);
    }

    #[test]
    fn classify_liquidity_sweep_quality_dirty_continuation() {
        let candles = vec![
            candle(1, 99.5, 100.0, 99.2, 99.8),
            candle(2, 99.8, 102.4, 99.4, 101.8),
            candle(3, 101.8, 102.2, 100.7, 101.4),
            candle(4, 101.4, 101.8, 99.7, 99.8),
        ];
        let sweep = LiquiditySweep {
            sweep_bar: 1,
            return_bar: 3,
            pool_price: 100.0,
            sweep_direction: Direction::Bear,
        };

        let evidence =
            classify_liquidity_sweep_quality(&candles, &vec![1.0; candles.len()], Some(&sweep));

        assert_eq!(evidence.quality, LiquiditySweepQualityKind::Dirty);
        assert!(evidence.displacement_atr.unwrap() > 1.75);
    }
}
