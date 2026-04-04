/// Wilder's smoothing (similar to EMA with alpha = 1/period)
pub fn wilder_smooth(values: &[f64], period: usize) -> Vec<f64> {
    if values.len() < period {
        return Vec::new();
    }

    let mut result = Vec::with_capacity(values.len());

    // First value is SMA
    let first: f64 = values[..period].iter().sum();
    result.push(first / period as f64);

    // Subsequent values use Wilder's smoothing
    for i in period..values.len() {
        let prev = result.last().unwrap();
        let smoothed = (prev * (period - 1) as f64 + values[i]) / period as f64;
        result.push(smoothed);
    }

    result
}

/// Simple Moving Average
pub fn sma(values: &[f64], period: usize) -> Vec<f64> {
    if values.len() < period {
        return Vec::new();
    }

    values
        .windows(period)
        .map(|w| w.iter().sum::<f64>() / period as f64)
        .collect()
}

/// Exponential Moving Average
pub fn ema(values: &[f64], period: usize) -> Vec<f64> {
    if values.is_empty() {
        return Vec::new();
    }

    let multiplier = 2.0 / (period as f64 + 1.0);
    let mut result = Vec::with_capacity(values.len());

    // First EMA is SMA
    if values.len() >= period {
        let first_sma: f64 = values[..period].iter().sum::<f64>() / period as f64;
        result.push(first_sma);

        for i in period..values.len() {
            let ema = (values[i] - result.last().unwrap()) * multiplier + result.last().unwrap();
            result.push(ema);
        }
    }

    result
}

/// Standard deviation
pub fn std_dev(values: &[f64], mean: f64) -> f64 {
    if values.is_empty() {
        return 0.0;
    }

    let variance: f64 =
        values.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / values.len() as f64;
    variance.sqrt()
}
