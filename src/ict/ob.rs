use crate::ict::breaker::detect_breaker_blocks;
use crate::ict::mitigation::detect_mitigation_blocks_default;
use crate::ict::rb::detect_pinbar;
use crate::types::{
    Candle, Direction, OrderBlock, OrderBlockVariantClassification, OrderBlockVariantKind,
};

/// Detect Order Blocks
/// Bullish OB: Last bearish candle before a bullish expansion
/// Bearish OB: Last bullish candle before a bearish expansion
pub fn detect_order_blocks(candles: &[Candle]) -> Vec<OrderBlock> {
    if candles.len() < 3 {
        return Vec::new();
    }

    let mut obs = Vec::new();

    for i in 2..candles.len() {
        let prev2 = &candles[i - 2];
        let prev1 = &candles[i - 1];
        let curr = &candles[i];

        // Bullish OB: prev1 is bearish, curr is bullish with significant move
        if prev1.is_bearish() && curr.is_bullish() && curr.close > prev2.high {
            obs.push(OrderBlock {
                high: prev1.high,
                low: prev1.low,
                ob_type: Direction::Bull,
                bar_index: i - 1,
                tested: false,
            });
        }

        // Bearish OB: prev1 is bullish, curr is bearish with significant move
        if prev1.is_bullish() && curr.is_bearish() && curr.close < prev2.low {
            obs.push(OrderBlock {
                high: prev1.high,
                low: prev1.low,
                ob_type: Direction::Bear,
                bar_index: i - 1,
                tested: false,
            });
        }
    }

    obs
}

/// Check if an Order Block has been tested
pub fn check_ob_tested(candles: &[Candle], ob: &OrderBlock) -> bool {
    for candle in candles.iter().skip(ob.bar_index + 1) {
        if ob.ob_type == Direction::Bull {
            // Bullish OB is tested when price returns to it
            if candle.low <= ob.high && candle.high >= ob.low {
                return true;
            }
        } else {
            // Bearish OB is tested when price returns to it
            if candle.high >= ob.low && candle.low <= ob.high {
                return true;
            }
        }
    }

    false
}

/// Find untested Order Blocks
pub fn find_untested_obs(candles: &[Candle]) -> Vec<OrderBlock> {
    let mut obs = detect_order_blocks(candles);

    for ob in &mut obs {
        ob.tested = check_ob_tested(candles, ob);
    }

    obs.retain(|o| !o.tested);
    obs
}

/// Count nearby untested Order Blocks
pub fn count_nearby_obs(candles: &[Candle], lookback: usize) -> usize {
    let obs = find_untested_obs(candles);
    let threshold = candles.len().saturating_sub(lookback);
    obs.iter().filter(|o| o.bar_index >= threshold).count()
}

/// Find the nearest Order Block to a given price
pub fn find_nearest_ob(candles: &[Candle], price: f64, direction: Direction) -> Option<OrderBlock> {
    let obs = find_untested_obs(candles);

    obs.iter()
        .filter(|o| o.ob_type == direction)
        .min_by(|a, b| {
            let dist_a = ((a.high + a.low) / 2.0 - price).abs();
            let dist_b = ((b.high + b.low) / 2.0 - price).abs();
            dist_a
                .partial_cmp(&dist_b)
                .unwrap_or(std::cmp::Ordering::Equal)
        })
        .cloned()
}

pub fn classify_order_block_variant(
    candles: &[Candle],
    atr: &[f64],
    last_close: f64,
    obs: &[OrderBlock],
) -> OrderBlockVariantClassification {
    if candles.len() < 4 {
        return OrderBlockVariantClassification::fail_closed(
            "insufficient_candles_for_order_block_variant",
        );
    }

    let nearest_ob = obs.iter().min_by(|left, right| {
        order_block_distance_to_price(left, last_close)
            .partial_cmp(&order_block_distance_to_price(right, last_close))
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    let mitigations = detect_mitigation_blocks_default(candles);
    let breakers = detect_breaker_blocks(candles);
    if let Some(breaker) = breakers.last() {
        return OrderBlockVariantClassification {
            variant: OrderBlockVariantKind::BreakerBlock,
            direction: breaker.direction,
            high: Some(breaker.high),
            low: Some(breaker.low),
            midpoint: Some((breaker.high + breaker.low) / 2.0),
            validation_state: "breaker_confirmed".to_string(),
            mitigation_count: mitigations.len(),
            breaker_confirmed: true,
            rejection_confirmed: false,
            confidence: 0.78,
            fail_closed_reason: None,
        };
    }

    if let Some(mitigation) = mitigations.last() {
        return OrderBlockVariantClassification {
            variant: OrderBlockVariantKind::MitigationBlock,
            direction: mitigation.direction,
            high: Some(mitigation.level),
            low: Some(mitigation.level),
            midpoint: Some(mitigation.level),
            validation_state: "mitigation_confirmed".to_string(),
            mitigation_count: mitigations.len(),
            breaker_confirmed: false,
            rejection_confirmed: false,
            confidence: 0.64,
            fail_closed_reason: None,
        };
    }

    if let Some(rejection) = detect_pinbar(candles, atr).last() {
        let candle = &candles[rejection.bar_index];
        return OrderBlockVariantClassification {
            variant: OrderBlockVariantKind::RejectionBlock,
            direction: rejection.direction,
            high: Some(candle.high),
            low: Some(candle.low),
            midpoint: Some(candle.midpoint()),
            validation_state: "rejection_confirmed".to_string(),
            mitigation_count: 0,
            breaker_confirmed: false,
            rejection_confirmed: true,
            confidence: 0.58,
            fail_closed_reason: None,
        };
    }

    if let Some(ob) = nearest_ob {
        return OrderBlockVariantClassification {
            variant: OrderBlockVariantKind::OrderBlock,
            direction: ob.ob_type,
            high: Some(ob.high),
            low: Some(ob.low),
            midpoint: Some((ob.high + ob.low) / 2.0),
            validation_state: if ob.tested {
                "tested_needs_followup".to_string()
            } else {
                "untested_active".to_string()
            },
            mitigation_count: 0,
            breaker_confirmed: false,
            rejection_confirmed: false,
            confidence: if ob.tested { 0.38 } else { 0.46 },
            fail_closed_reason: None,
        };
    }

    OrderBlockVariantClassification::fail_closed("no_order_block_variant_detected")
}

fn order_block_distance_to_price(ob: &OrderBlock, price: f64) -> f64 {
    ((ob.high + ob.low) / 2.0 - price).abs()
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
    fn classify_order_block_variant_returns_plain_untested_ob() {
        let candles = vec![
            candle(1, 100.0, 101.0, 99.5, 100.5),
            candle(2, 100.6, 101.0, 99.8, 100.0),
            candle(3, 100.1, 102.0, 100.0, 101.6),
            candle(4, 101.6, 102.1, 101.2, 101.8),
        ];
        let obs = detect_order_blocks(&candles);

        let evidence =
            classify_order_block_variant(&candles, &vec![1.0; candles.len()], 101.8, &obs);

        assert_eq!(evidence.variant, OrderBlockVariantKind::OrderBlock);
        assert_eq!(evidence.validation_state, "untested_active");
        assert_eq!(evidence.direction, Direction::Bull);
    }

    #[test]
    fn classify_order_block_variant_prefers_rejection_over_plain_ob() {
        let candles = vec![
            candle(1, 100.0, 101.0, 99.5, 100.5),
            candle(2, 100.6, 101.0, 99.8, 100.0),
            candle(3, 100.1, 102.0, 100.0, 101.6),
            candle(4, 101.6, 105.0, 101.5, 101.8),
        ];
        let obs = detect_order_blocks(&candles);

        let evidence =
            classify_order_block_variant(&candles, &vec![1.0; candles.len()], 101.8, &obs);

        assert_eq!(evidence.variant, OrderBlockVariantKind::RejectionBlock);
        assert_eq!(evidence.validation_state, "rejection_confirmed");
        assert!(evidence.rejection_confirmed);
    }
}
