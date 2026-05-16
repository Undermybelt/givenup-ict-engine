use chrono::{Datelike, Duration, NaiveDate, Utc};
use chrono_tz::America::New_York;
use serde::{Deserialize, Serialize};

use crate::types::Candle;

const NY_TRADING_DAY_ROLLOVER_HOURS: i64 = 7;
const RECENT_WEEK_GAP_TARGET: usize = 4;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct GapReferenceLevel {
    pub label: String,
    pub period_key: Option<String>,
    pub previous_close: Option<f64>,
    pub current_open: Option<f64>,
    pub upper: Option<f64>,
    pub lower: Option<f64>,
    pub midpoint: Option<f64>,
    pub size: Option<f64>,
    pub direction: Option<String>,
    pub active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct ReferenceLiquidityLevelsEvidence {
    pub factor_name: String,
    pub source_frame: String,
    pub timezone: String,
    pub trading_day_rollover: String,
    pub current_trading_day: Option<String>,
    pub current_trading_week: Option<String>,
    pub current_trading_month: Option<String>,
    pub previous_day_high: Option<f64>,
    pub previous_day_low: Option<f64>,
    pub previous_day_close: Option<f64>,
    pub current_day_open: Option<f64>,
    pub previous_week_high: Option<f64>,
    pub previous_week_low: Option<f64>,
    pub previous_week_close: Option<f64>,
    pub current_week_open: Option<f64>,
    pub previous_month_high: Option<f64>,
    pub previous_month_low: Option<f64>,
    pub current_day_gap: Option<GapReferenceLevel>,
    pub current_week_gap: Option<GapReferenceLevel>,
    pub recent_week_open_gaps: Vec<GapReferenceLevel>,
    pub confidence: f64,
    pub fail_closed_reason: Option<String>,
}

impl ReferenceLiquidityLevelsEvidence {
    pub fn fail_closed(source_frame: impl Into<String>, reason: impl Into<String>) -> Self {
        Self {
            factor_name: "reference_liquidity_levels".to_string(),
            source_frame: source_frame.into(),
            timezone: "America/New_York".to_string(),
            trading_day_rollover: "ny_1700_session_date".to_string(),
            confidence: 0.0,
            fail_closed_reason: Some(reason.into()),
            ..Self::default()
        }
    }
}

#[derive(Debug, Clone)]
struct PeriodAggregate {
    key: String,
    open: f64,
    high: f64,
    low: f64,
    close: f64,
}

pub fn detect_reference_liquidity_levels(
    candles: &[Candle],
    source_frame: &str,
) -> ReferenceLiquidityLevelsEvidence {
    if candles.len() < 2 {
        return ReferenceLiquidityLevelsEvidence::fail_closed(
            source_frame,
            "insufficient_candles_for_reference_liquidity_levels",
        );
    }

    let day_aggregates = build_period_aggregates(candles, trading_day_key_string);
    let week_aggregates = build_period_aggregates(candles, trading_week_key_string);
    let month_aggregates = build_period_aggregates(candles, trading_month_key_string);

    if day_aggregates.len() < 2 {
        return ReferenceLiquidityLevelsEvidence::fail_closed(
            source_frame,
            "insufficient_trading_day_history_for_reference_liquidity_levels",
        );
    }

    let current_day = day_aggregates.last();
    let previous_day = nth_from_end(&day_aggregates, 2);
    let current_week = week_aggregates.last();
    let previous_week = nth_from_end(&week_aggregates, 2);
    let previous_month = nth_from_end(&month_aggregates, 2);

    let recent_week_open_gaps = week_aggregates
        .windows(2)
        .rev()
        .take(RECENT_WEEK_GAP_TARGET)
        .filter_map(|window| {
            let previous = window.first()?;
            let current = window.get(1)?;
            Some(build_gap_reference(
                "week_open_gap",
                Some(current.key.clone()),
                Some(previous.close),
                Some(current.open),
            ))
        })
        .collect::<Vec<_>>();

    let mut missing = Vec::new();
    let mut present_core_fields = 0usize;
    for (name, value) in [
        ("previous_day_high", previous_day.map(|item| item.high)),
        ("previous_day_low", previous_day.map(|item| item.low)),
        ("previous_day_close", previous_day.map(|item| item.close)),
        ("current_day_open", current_day.map(|item| item.open)),
        ("previous_week_high", previous_week.map(|item| item.high)),
        ("previous_week_low", previous_week.map(|item| item.low)),
        ("previous_week_close", previous_week.map(|item| item.close)),
        ("current_week_open", current_week.map(|item| item.open)),
        ("previous_month_high", previous_month.map(|item| item.high)),
        ("previous_month_low", previous_month.map(|item| item.low)),
    ] {
        if value.is_some() {
            present_core_fields += 1;
        } else {
            missing.push(format!("missing_{name}"));
        }
    }

    if recent_week_open_gaps.len() < RECENT_WEEK_GAP_TARGET {
        missing.push("insufficient_recent_week_gap_history".to_string());
    }

    let core_confidence = present_core_fields as f64 / 10.0;
    let recent_gap_confidence = recent_week_open_gaps.len().min(RECENT_WEEK_GAP_TARGET) as f64
        / RECENT_WEEK_GAP_TARGET as f64;
    let confidence = (core_confidence * 0.85 + recent_gap_confidence * 0.15).clamp(0.0, 1.0);

    ReferenceLiquidityLevelsEvidence {
        factor_name: "reference_liquidity_levels".to_string(),
        source_frame: source_frame.to_string(),
        timezone: "America/New_York".to_string(),
        trading_day_rollover: "ny_1700_session_date".to_string(),
        current_trading_day: current_day.map(|item| item.key.clone()),
        current_trading_week: current_week.map(|item| item.key.clone()),
        current_trading_month: month_aggregates.last().map(|item| item.key.clone()),
        previous_day_high: previous_day.map(|item| item.high),
        previous_day_low: previous_day.map(|item| item.low),
        previous_day_close: previous_day.map(|item| item.close),
        current_day_open: current_day.map(|item| item.open),
        previous_week_high: previous_week.map(|item| item.high),
        previous_week_low: previous_week.map(|item| item.low),
        previous_week_close: previous_week.map(|item| item.close),
        current_week_open: current_week.map(|item| item.open),
        previous_month_high: previous_month.map(|item| item.high),
        previous_month_low: previous_month.map(|item| item.low),
        current_day_gap: Some(build_gap_reference(
            "day_open_gap",
            current_day.map(|item| item.key.clone()),
            previous_day.map(|item| item.close),
            current_day.map(|item| item.open),
        )),
        current_week_gap: Some(build_gap_reference(
            "week_open_gap",
            current_week.map(|item| item.key.clone()),
            previous_week.map(|item| item.close),
            current_week.map(|item| item.open),
        )),
        recent_week_open_gaps,
        confidence,
        fail_closed_reason: (!missing.is_empty()).then(|| missing.join("|")),
    }
}

fn nth_from_end<T>(items: &[T], n: usize) -> Option<&T> {
    if n == 0 || items.len() < n {
        None
    } else {
        items.get(items.len() - n)
    }
}

fn build_period_aggregates<F>(candles: &[Candle], key_fn: F) -> Vec<PeriodAggregate>
where
    F: Fn(&Candle) -> String,
{
    let mut iter = candles.iter();
    let Some(first) = iter.next() else {
        return Vec::new();
    };
    let mut aggregates = Vec::new();
    let mut current_key = key_fn(first);
    let mut current = PeriodAggregate {
        key: current_key.clone(),
        open: first.open,
        high: first.high,
        low: first.low,
        close: first.close,
    };

    for candle in iter {
        let key = key_fn(candle);
        if key != current_key {
            aggregates.push(current);
            current_key = key.clone();
            current = PeriodAggregate {
                key,
                open: candle.open,
                high: candle.high,
                low: candle.low,
                close: candle.close,
            };
            continue;
        }
        current.high = current.high.max(candle.high);
        current.low = current.low.min(candle.low);
        current.close = candle.close;
    }

    aggregates.push(current);
    aggregates
}

fn trading_day_key_string(candle: &Candle) -> String {
    trading_session_date(candle.timestamp)
        .format("%Y-%m-%d")
        .to_string()
}

fn trading_week_key_string(candle: &Candle) -> String {
    let session_date = trading_session_date(candle.timestamp);
    let iso = session_date.iso_week();
    format!("{:04}-W{:02}", iso.year(), iso.week())
}

fn trading_month_key_string(candle: &Candle) -> String {
    let session_date = trading_session_date(candle.timestamp);
    format!("{:04}-{:02}", session_date.year(), session_date.month())
}

fn trading_session_date(timestamp: chrono::DateTime<Utc>) -> NaiveDate {
    let ny = timestamp.with_timezone(&New_York) + Duration::hours(NY_TRADING_DAY_ROLLOVER_HOURS);
    ny.date_naive()
}

fn build_gap_reference(
    label: &str,
    period_key: Option<String>,
    previous_close: Option<f64>,
    current_open: Option<f64>,
) -> GapReferenceLevel {
    let (upper, lower, midpoint, size, direction, active) = match (previous_close, current_open) {
        (Some(previous_close), Some(current_open)) => {
            let upper = previous_close.max(current_open);
            let lower = previous_close.min(current_open);
            let midpoint = (upper + lower) * 0.5;
            let size = current_open - previous_close;
            let direction = if size > 0.0 {
                Some("up_gap".to_string())
            } else if size < 0.0 {
                Some("down_gap".to_string())
            } else {
                Some("flat_open".to_string())
            };
            (
                Some(upper),
                Some(lower),
                Some(midpoint),
                Some(size),
                direction,
                size.abs() > f64::EPSILON,
            )
        }
        _ => (None, None, None, None, None, false),
    };

    GapReferenceLevel {
        label: label.to_string(),
        period_key,
        previous_close,
        current_open,
        upper,
        lower,
        midpoint,
        size,
        direction,
        active,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn candle(day: &str, open: f64, high: f64, low: f64, close: f64) -> Candle {
        let timestamp = chrono::DateTime::parse_from_rfc3339(&format!("{day}T15:00:00Z"))
            .unwrap()
            .with_timezone(&Utc);
        Candle {
            timestamp,
            open,
            high,
            low,
            close,
            volume: 1.0,
        }
    }

    #[test]
    fn detects_reference_liquidity_levels_and_recent_week_gaps() {
        let mut candles = Vec::new();
        for (idx, day) in [
            "2026-02-02",
            "2026-02-03",
            "2026-02-04",
            "2026-02-05",
            "2026-02-06",
            "2026-02-09",
            "2026-02-10",
            "2026-02-11",
            "2026-02-12",
            "2026-02-13",
            "2026-02-16",
            "2026-02-17",
            "2026-02-18",
            "2026-02-19",
            "2026-02-20",
            "2026-02-23",
            "2026-02-24",
            "2026-02-25",
            "2026-02-26",
            "2026-02-27",
            "2026-03-02",
            "2026-03-03",
        ]
        .iter()
        .enumerate()
        {
            let base = 100.0 + idx as f64 * 10.0;
            candles.push(candle(day, base, base + 5.0, base - 3.0, base + 2.0));
        }

        let evidence = detect_reference_liquidity_levels(&candles, "mtf");

        assert_eq!(evidence.factor_name, "reference_liquidity_levels");
        assert_eq!(evidence.source_frame, "mtf");
        assert_eq!(evidence.current_trading_day.as_deref(), Some("2026-03-03"));
        assert_eq!(evidence.current_trading_week.as_deref(), Some("2026-W10"));
        assert_eq!(evidence.current_trading_month.as_deref(), Some("2026-03"));
        assert_eq!(evidence.previous_day_high, Some(305.0));
        assert_eq!(evidence.previous_day_low, Some(297.0));
        assert_eq!(evidence.previous_day_close, Some(302.0));
        assert_eq!(evidence.current_day_open, Some(310.0));
        assert_eq!(evidence.previous_week_high, Some(295.0));
        assert_eq!(evidence.previous_week_low, Some(247.0));
        assert_eq!(evidence.previous_week_close, Some(292.0));
        assert_eq!(evidence.current_week_open, Some(300.0));
        assert_eq!(evidence.previous_month_high, Some(295.0));
        assert_eq!(evidence.previous_month_low, Some(97.0));

        let day_gap = evidence.current_day_gap.as_ref().unwrap();
        assert_eq!(day_gap.upper, Some(310.0));
        assert_eq!(day_gap.lower, Some(302.0));
        assert_eq!(day_gap.direction.as_deref(), Some("up_gap"));
        assert!(day_gap.active);

        let week_gap = evidence.current_week_gap.as_ref().unwrap();
        assert_eq!(week_gap.upper, Some(300.0));
        assert_eq!(week_gap.lower, Some(292.0));
        assert_eq!(week_gap.period_key.as_deref(), Some("2026-W10"));

        assert_eq!(evidence.recent_week_open_gaps.len(), 4);
        assert_eq!(
            evidence.recent_week_open_gaps[0].period_key.as_deref(),
            Some("2026-W10")
        );
        assert!(
            evidence.fail_closed_reason.is_none(),
            "unexpected fail_closed_reason: {:?}",
            evidence.fail_closed_reason
        );
        assert!(evidence.confidence > 0.99);
    }

    #[test]
    fn fail_closes_when_history_is_too_short() {
        let candles = vec![candle("2026-03-03", 100.0, 101.0, 99.0, 100.5)];
        let evidence = detect_reference_liquidity_levels(&candles, "ltf");
        assert_eq!(evidence.source_frame, "ltf");
        assert_eq!(evidence.confidence, 0.0);
        assert_eq!(
            evidence.fail_closed_reason.as_deref(),
            Some("insufficient_candles_for_reference_liquidity_levels")
        );
    }
}
