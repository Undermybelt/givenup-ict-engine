use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

use crate::config::FrameFeatures;
use crate::domain::execution::{estimate_ou_execution_metrics, OuExecutionMetrics};
use crate::domain::regime::{estimate_ising_state, IsingState};
use crate::ict::{measure_pythagorean_extension, PythagoreanExtensionMetrics};
use crate::math::geometry::Point2;
use crate::types::Candle;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ExecutionPhysicsOverlay {
    pub ou: Option<OuExecutionMetrics>,
    pub ising: Option<IsingState>,
    pub pythagorean: Option<PythagoreanExtensionMetrics>,
}

pub fn build_execution_physics_overlay(
    candles: &[Candle],
    frame_features: &FrameFeatures,
) -> ExecutionPhysicsOverlay {
    let prices = candles.iter().map(|candle| candle.close).collect::<Vec<_>>();
    let timestamps = candles
        .iter()
        .map(|candle| candle.timestamp)
        .collect::<Vec<DateTime<Utc>>>();
    let ou = estimate_ou_execution_metrics(&prices, &timestamps);

    let pythagorean = if candles.len() >= 2 {
        let anchor_a = Point2 {
            x: 0.0,
            y: candles.first().map(|candle| candle.close).unwrap_or_default(),
        };
        let anchor_b = Point2 {
            x: (candles.len() - 1) as f64,
            y: candles
                .first()
                .map(|candle| candle.close)
                .unwrap_or_default()
                + frame_features.normalized_distance_to_projected_trend_bps / 10_000.0,
        };
        let current = Point2 {
            x: (candles.len() - 1) as f64,
            y: candles.last().map(|candle| candle.close).unwrap_or_default(),
        };
        Some(measure_pythagorean_extension(anchor_a, anchor_b, current))
    } else {
        None
    };

    let aligned_signals = [
        match frame_features.regime_label.as_str() {
            "bull" => 1.0,
            "bear" => -1.0,
            _ => 0.0,
        },
        match frame_features.liquidity_label.as_str() {
            "favorable" => 0.8,
            "hostile" => -0.8,
            _ => 0.0,
        },
        (1.0 - frame_features.ou_pullback_expectation_zscore.abs() / 5.0).clamp(-1.0, 1.0),
    ];
    let participation_weights = [
        (frame_features.sweep_count as f64 + 1.0).clamp(1.0, 10.0),
        (frame_features.fvg_count as f64 + 1.0).clamp(1.0, 10.0),
        (frame_features.pythagorean_overstretch.unwrap_or_default() + 1.0).clamp(1.0, 2.0),
    ];
    let ising = estimate_ising_state(&aligned_signals, &participation_weights);

    ExecutionPhysicsOverlay {
        ou,
        ising,
        pythagorean,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use chrono::{Duration, TimeZone};

    fn sample_candles() -> Vec<Candle> {
        let start = Utc.with_ymd_and_hms(2026, 1, 1, 0, 0, 0).unwrap();
        (0..48)
            .map(|i| {
                let close = 100.0 + (i as f64 * 0.1).sin() + i as f64 * 0.02;
                Candle {
                    timestamp: start + Duration::minutes(i as i64),
                    open: close - 0.1,
                    high: close + 0.2,
                    low: close - 0.2,
                    close,
                    volume: 1_000.0 + i as f64,
                }
            })
            .collect()
    }

    #[test]
    fn builds_execution_physics_overlay_from_candles_and_frame_features() {
        let candles = sample_candles();
        let frame = crate::config::build_frame_features(&candles).unwrap();
        let overlay = build_execution_physics_overlay(&candles, &frame);

        assert!(overlay.pythagorean.is_some());
        assert!(overlay.ising.is_some());
    }
}
