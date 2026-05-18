//! Volume Imbalance detector.
//!
//! Single-bar volume z-score outlier over a rolling baseline window.
//! Distinct from `PropulsionBlock` in that volume imbalance does not
//! require body / range structure — only the volume anomaly. ICT
//! treats VI as evidence of stop-runs and absorption, independent of
//! whether the bar happens to also be a propulsion bar.
//!
//! Forward-leak: baseline window is `[i - window .. i)` — excludes
//! the current bar so the z-score is unbiased.

use crate::types::{Candle, Direction, VolumeImbalance, VolumeImbalanceGap};

pub const DEFAULT_VOLUME_IMBALANCE_WINDOW: usize = 20;
pub const DEFAULT_VOLUME_IMBALANCE_Z_MIN: f64 = 2.5;

pub fn detect_volume_imbalances(
    candles: &[Candle],
    window: usize,
    z_threshold: f64,
) -> Vec<VolumeImbalance> {
    if candles.len() <= window || window == 0 {
        return Vec::new();
    }
    let mut out = Vec::new();
    for i in window..candles.len() {
        let candle = &candles[i];
        let baseline = &candles[i - window..i];
        let (mean, std_dev) = volume_stats(baseline);
        if std_dev <= f64::EPSILON {
            continue;
        }
        let z_score = (candle.volume - mean) / std_dev;
        if z_score < z_threshold {
            continue;
        }
        let direction = if candle.close > candle.open {
            Direction::Bull
        } else if candle.close < candle.open {
            Direction::Bear
        } else {
            Direction::Neutral
        };
        out.push(VolumeImbalance {
            bar_index: i,
            direction,
            volume: candle.volume,
            mean,
            std_dev,
            z_score,
        });
    }
    out
}

pub fn detect_volume_imbalances_default(candles: &[Candle]) -> Vec<VolumeImbalance> {
    detect_volume_imbalances(
        candles,
        DEFAULT_VOLUME_IMBALANCE_WINDOW,
        DEFAULT_VOLUME_IMBALANCE_Z_MIN,
    )
}

/// Detect ICT-style volume imbalance gaps.
///
/// This is the delivery-gap variant: the untraded price band between
/// the previous candle close and the current candle open. It is a
/// separate geometry from the rolling volume z-score anomaly above.
pub fn detect_volume_imbalance_gaps(candles: &[Candle], min_gap: f64) -> Vec<VolumeImbalanceGap> {
    if candles.len() < 2 {
        return Vec::new();
    }

    let mut out = Vec::new();
    for i in 1..candles.len() {
        let prev_close = candles[i - 1].close;
        let curr_open = candles[i].open;
        let gap = (curr_open - prev_close).abs();
        if gap <= min_gap.max(0.0) {
            continue;
        }

        let direction = if curr_open > prev_close {
            Direction::Bull
        } else {
            Direction::Bear
        };
        let top = curr_open.max(prev_close);
        let bottom = curr_open.min(prev_close);
        let mut imbalance = VolumeImbalanceGap {
            top,
            bottom,
            direction,
            start_bar: i,
            filled: false,
        };
        imbalance.filled = check_volume_imbalance_gap_filled(candles, &imbalance);
        out.push(imbalance);
    }
    out
}

pub fn detect_volume_imbalance_gaps_default(candles: &[Candle]) -> Vec<VolumeImbalanceGap> {
    detect_volume_imbalance_gaps(candles, f64::EPSILON)
}

pub fn check_volume_imbalance_gap_filled(
    candles: &[Candle],
    imbalance: &VolumeImbalanceGap,
) -> bool {
    for candle in candles.iter().skip(imbalance.start_bar + 1) {
        if candle.low <= imbalance.top && candle.high >= imbalance.bottom {
            return true;
        }
    }
    false
}

fn volume_stats(window: &[Candle]) -> (f64, f64) {
    let n = window.len() as f64;
    if n == 0.0 {
        return (0.0, 0.0);
    }
    let mean = window.iter().map(|c| c.volume).sum::<f64>() / n;
    let var = window
        .iter()
        .map(|c| {
            let diff = c.volume - mean;
            diff * diff
        })
        .sum::<f64>()
        / n;
    (mean, var.sqrt())
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, TimeZone, Utc};

    fn ts(n: i64) -> chrono::DateTime<Utc> {
        Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap() + Duration::minutes(n)
    }

    fn candle(idx: i64, close: f64, volume: f64) -> Candle {
        Candle {
            timestamp: ts(idx),
            open: 100.0,
            high: 100.5,
            low: 99.5,
            close,
            volume,
        }
    }

    #[test]
    fn empty_yields_empty() {
        assert!(detect_volume_imbalances_default(&[]).is_empty());
    }

    #[test]
    fn flat_volume_yields_no_imbalance() {
        // All identical volumes ⇒ std = 0 ⇒ no detection.
        let candles: Vec<Candle> = (0..40).map(|i| candle(i as i64, 100.1, 1_000.0)).collect();
        let out = detect_volume_imbalances_default(&candles);
        assert!(out.is_empty());
    }

    #[test]
    fn isolated_volume_spike_is_detected() {
        let mut candles: Vec<Candle> = (0..40)
            .map(|i| {
                let v = 1_000.0 + ((i % 5) as f64) * 25.0;
                candle(i as i64, 100.1, v)
            })
            .collect();
        candles[30] = candle(30, 101.0, 12_000.0);
        let out = detect_volume_imbalances_default(&candles);
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].bar_index, 30);
        assert_eq!(out[0].direction, Direction::Bull);
        assert!(out[0].z_score >= 2.5);
    }

    #[test]
    fn bear_close_yields_bear_direction() {
        let mut candles: Vec<Candle> = (0..40)
            .map(|i| {
                let v = 1_000.0 + ((i % 5) as f64) * 25.0;
                candle(i as i64, 100.1, v)
            })
            .collect();
        candles[30] = candle(30, 99.0, 12_000.0);
        let out = detect_volume_imbalances_default(&candles);
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].direction, Direction::Bear);
    }

    #[test]
    fn forward_leak_guard_holds() {
        let mut candles: Vec<Candle> = (0..50)
            .map(|i| {
                let v = 1_000.0 + ((i % 5) as f64) * 25.0;
                candle(i as i64, 100.1, v)
            })
            .collect();
        candles[35] = candle(35, 101.0, 12_000.0);

        let full = detect_volume_imbalances_default(&candles);
        let prefix = detect_volume_imbalances_default(&candles[..=35]);
        let f35: Vec<&VolumeImbalance> = full.iter().filter(|v| v.bar_index == 35).collect();
        let p35: Vec<&VolumeImbalance> = prefix.iter().filter(|v| v.bar_index == 35).collect();
        assert_eq!(f35.len(), p35.len());
        if !f35.is_empty() {
            assert!((f35[0].z_score - p35[0].z_score).abs() < 1e-9);
        }
    }

    #[test]
    fn detects_bullish_delivery_gap_volume_imbalance() {
        let candles = vec![
            candle(0, 100.0, 1_000.0),
            Candle {
                timestamp: ts(1),
                open: 101.0,
                high: 101.5,
                low: 100.8,
                close: 101.2,
                volume: 1_000.0,
            },
        ];
        let out = detect_volume_imbalance_gaps_default(&candles);
        assert_eq!(out.len(), 1);
        assert_eq!(out[0].direction, Direction::Bull);
        assert_eq!(out[0].start_bar, 1);
        assert!((out[0].top - 101.0).abs() < 1e-9);
        assert!((out[0].bottom - 100.0).abs() < 1e-9);
        assert!(!out[0].filled);
    }

    #[test]
    fn marks_delivery_gap_filled_on_later_overlap() {
        let candles = vec![
            candle(0, 100.0, 1_000.0),
            Candle {
                timestamp: ts(1),
                open: 101.0,
                high: 101.5,
                low: 100.9,
                close: 101.2,
                volume: 1_000.0,
            },
            Candle {
                timestamp: ts(2),
                open: 101.2,
                high: 101.3,
                low: 100.5,
                close: 100.7,
                volume: 1_000.0,
            },
        ];
        let out = detect_volume_imbalance_gaps_default(&candles);
        assert_eq!(out.len(), 1);
        assert!(out[0].filled);
    }
}
