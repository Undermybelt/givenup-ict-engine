use crate::types::{
    Candle, Direction, LiquidityPool, LiquidityPoolTextureClassification, LiquidityPoolTextureKind,
    LiquiditySweep,
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
    let touch_score = (touch_count as f64 / 6.0).min(1.0);
    let clean_sweep_likelihood =
        (0.20 + touch_score * 0.35 + consistency_for_texture * 0.35).clamp(0.0, 0.90);
    let confidence = (0.32 + touch_score * 0.26 + consistency_for_texture * 0.22).clamp(0.0, 0.82);

    LiquidityPoolTextureClassification {
        texture,
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
        assert!(evidence.spacing_consistency.unwrap() >= 0.65);
        assert!(evidence.clean_sweep_likelihood.unwrap() > 0.65);
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
        assert!(evidence.spacing_consistency.unwrap() < 0.4);
    }
}
