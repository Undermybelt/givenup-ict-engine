use crate::{math::ema, types::Candle};

#[derive(Debug, Clone)]
pub struct MACD {
    pub macd_line: Vec<f64>,
    pub signal_line: Vec<f64>,
    pub histogram: Vec<f64>,
}

/// Compute MACD (12, 26, 9)
pub fn compute_macd(candles: &[Candle], fast: usize, slow: usize, signal: usize) -> MACD {
    let prices: Vec<f64> = candles.iter().map(|c| c.close).collect();

    let ema_fast = ema(&prices, fast);
    let ema_slow = ema(&prices, slow);

    if ema_fast.is_empty() || ema_slow.is_empty() {
        return MACD {
            macd_line: Vec::new(),
            signal_line: Vec::new(),
            histogram: Vec::new(),
        };
    }

    // Align the EMAs (slow EMA starts later)
    let offset = slow - fast;
    let macd_line: Vec<f64> = ema_fast[offset..]
        .iter()
        .zip(ema_slow.iter())
        .map(|(fast, slow)| fast - slow)
        .collect();

    // Signal line is EMA of MACD line
    let signal_line = ema(&macd_line, signal);

    // Histogram is MACD - Signal
    let signal_offset = signal - 1;
    let histogram: Vec<f64> = macd_line[signal_offset..]
        .iter()
        .zip(signal_line.iter())
        .map(|(macd, signal)| macd - signal)
        .collect();

    MACD {
        macd_line,
        signal_line,
        histogram,
    }
}

/// Get the latest MACD values
pub fn latest_macd(
    candles: &[Candle],
    fast: usize,
    slow: usize,
    signal: usize,
) -> Option<(f64, f64, f64)> {
    let macd = compute_macd(candles, fast, slow, signal);
    if macd.macd_line.is_empty() {
        None
    } else {
        Some((
            *macd.macd_line.last().unwrap(),
            *macd.signal_line.last().unwrap(),
            *macd.histogram.last().unwrap(),
        ))
    }
}

/// Check if MACD histogram is bullish (positive and increasing)
pub fn is_macd_bullish(candles: &[Candle], fast: usize, slow: usize, signal: usize) -> bool {
    let macd = compute_macd(candles, fast, slow, signal);
    if macd.histogram.len() < 2 {
        return false;
    }

    let last = macd.histogram.last().unwrap();
    let prev = macd.histogram[macd.histogram.len() - 2];

    *last > 0.0 && *last > prev
}

/// Check if MACD histogram is bearish (negative and decreasing)
pub fn is_macd_bearish(candles: &[Candle], fast: usize, slow: usize, signal: usize) -> bool {
    let macd = compute_macd(candles, fast, slow, signal);
    if macd.histogram.len() < 2 {
        return false;
    }

    let last = macd.histogram.last().unwrap();
    let prev = macd.histogram[macd.histogram.len() - 2];

    *last < 0.0 && *last < prev
}
