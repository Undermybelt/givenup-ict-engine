use crate::types::{Candle, Direction, StructureBreak, StructureType, SwingPoint};

/// Detect Break of Structure (BOS) and Change of Character (CHoCH)
pub fn detect_structure_breaks(
    candles: &[Candle],
    swing_highs: &[SwingPoint],
    swing_lows: &[SwingPoint],
) -> Vec<StructureBreak> {
    let mut breaks = Vec::new();
    let mut last_trend = Direction::Neutral;
    let mut sorted_highs: Vec<_> = swing_highs.iter().collect();
    let mut sorted_lows: Vec<_> = swing_lows.iter().collect();
    sorted_highs.sort_by_key(|sp| sp.index);
    sorted_lows.sort_by_key(|sp| sp.index);

    let mut next_high = 0;
    let mut next_low = 0;
    let mut last_high = None;
    let mut last_low = None;

    for (i, candle) in candles.iter().enumerate() {
        while next_high < sorted_highs.len() && sorted_highs[next_high].index < i {
            last_high = Some(sorted_highs[next_high]);
            next_high += 1;
        }
        while next_low < sorted_lows.len() && sorted_lows[next_low].index < i {
            last_low = Some(sorted_lows[next_low]);
            next_low += 1;
        }

        // Check for bullish break (breaking above last swing high)
        if let Some(last_high) = last_high {
            if candle.high > last_high.price {
                let break_type = if last_trend == Direction::Bear {
                    StructureType::CHoCH // Change of character
                } else {
                    StructureType::BOS // Break of structure
                };

                breaks.push(StructureBreak {
                    bar_index: i,
                    break_type,
                    direction: Direction::Bull,
                    level: last_high.price,
                });

                last_trend = Direction::Bull;
            }
        }

        // Check for bearish break (breaking below last swing low)
        if let Some(last_low) = last_low {
            if candle.low < last_low.price {
                let break_type = if last_trend == Direction::Bull {
                    StructureType::CHoCH // Change of character
                } else {
                    StructureType::BOS // Break of structure
                };

                breaks.push(StructureBreak {
                    bar_index: i,
                    break_type,
                    direction: Direction::Bear,
                    level: last_low.price,
                });

                last_trend = Direction::Bear;
            }
        }
    }

    breaks
}

/// Get the latest structure break
pub fn latest_structure_break(breaks: &[StructureBreak]) -> Option<&StructureBreak> {
    breaks.iter().max_by_key(|b| b.bar_index)
}

/// Count recent structure breaks
pub fn count_recent_breaks(
    breaks: &[StructureBreak],
    lookback: usize,
    total_candles: usize,
) -> usize {
    let threshold = total_candles.saturating_sub(lookback);
    breaks.iter().filter(|b| b.bar_index >= threshold).count()
}

/// Detect trend based on structure breaks
pub fn detect_trend_from_breaks(breaks: &[StructureBreak]) -> Direction {
    if let Some(latest) = latest_structure_break(breaks) {
        latest.direction
    } else {
        Direction::Neutral
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, TimeZone, Utc};
    use std::time::Instant;

    fn candle(index: usize, high: f64, low: f64) -> Candle {
        Candle {
            timestamp: Utc.timestamp_opt(1_700_000_000 + index as i64, 0).unwrap(),
            open: (high + low) / 2.0,
            high,
            low,
            close: (high + low) / 2.0,
            volume: 1_000.0,
        }
    }

    fn legacy_detect_structure_breaks(
        candles: &[Candle],
        swing_highs: &[SwingPoint],
        swing_lows: &[SwingPoint],
    ) -> Vec<StructureBreak> {
        let mut breaks = Vec::new();
        let mut last_trend = Direction::Neutral;

        for (i, candle) in candles.iter().enumerate() {
            if let Some(last_high) = swing_highs
                .iter()
                .filter(|sp| sp.index < i)
                .max_by_key(|sp| sp.index)
            {
                if candle.high > last_high.price {
                    let break_type = if last_trend == Direction::Bear {
                        StructureType::CHoCH
                    } else {
                        StructureType::BOS
                    };
                    breaks.push(StructureBreak {
                        bar_index: i,
                        break_type,
                        direction: Direction::Bull,
                        level: last_high.price,
                    });
                    last_trend = Direction::Bull;
                }
            }

            if let Some(last_low) = swing_lows
                .iter()
                .filter(|sp| sp.index < i)
                .max_by_key(|sp| sp.index)
            {
                if candle.low < last_low.price {
                    let break_type = if last_trend == Direction::Bull {
                        StructureType::CHoCH
                    } else {
                        StructureType::BOS
                    };
                    breaks.push(StructureBreak {
                        bar_index: i,
                        break_type,
                        direction: Direction::Bear,
                        level: last_low.price,
                    });
                    last_trend = Direction::Bear;
                }
            }
        }

        breaks
    }

    #[test]
    fn detect_structure_breaks_handles_large_swing_sets_without_quadratic_scan() {
        let candles: Vec<_> = (0..20_000)
            .map(|index| {
                let price = 10_000.0 + index as f64 * 0.25;
                candle(index, price + 1.0, price - 1.0)
            })
            .collect();
        let swing_highs: Vec<_> = (0..20_000)
            .step_by(2)
            .map(|index| SwingPoint {
                index,
                price: 9_990.0 + index as f64 * 0.25,
                sp_type: Direction::Bear,
            })
            .collect();
        let swing_lows: Vec<_> = (0..20_000)
            .step_by(2)
            .map(|index| SwingPoint {
                index,
                price: 10_010.0 + index as f64 * 0.25,
                sp_type: Direction::Bull,
            })
            .collect();

        let expected = legacy_detect_structure_breaks(
            &candles[..512],
            &swing_highs[..256],
            &swing_lows[..256],
        );
        let actual_sample =
            detect_structure_breaks(&candles[..512], &swing_highs[..256], &swing_lows[..256]);
        assert_eq!(actual_sample.len(), expected.len());
        for (actual, expected) in actual_sample.iter().zip(expected.iter()) {
            assert_eq!(actual.bar_index, expected.bar_index);
            assert_eq!(actual.direction, expected.direction);
            assert_eq!(actual.break_type, expected.break_type);
            assert!((actual.level - expected.level).abs() < f64::EPSILON);
        }

        let started_at = Instant::now();
        let breaks = detect_structure_breaks(&candles, &swing_highs, &swing_lows);
        let elapsed = started_at.elapsed();

        assert!(!breaks.is_empty());
        assert!(
            elapsed < Duration::milliseconds(500).to_std().unwrap(),
            "structure break detection took {elapsed:?}; large analyze frames need linear last-swing lookup"
        );
    }
}
