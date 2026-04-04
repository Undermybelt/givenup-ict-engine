use anyhow::{Context, Result};
use std::fs;
use std::path::Path;

use crate::types::Candle;

#[derive(Debug, serde::Deserialize)]
struct CandleJson {
    timestamp: String,
    open: f64,
    high: f64,
    low: f64,
    close: f64,
    volume: f64,
}

#[derive(Debug, serde::Deserialize)]
struct CandleData {
    #[serde(rename = "symbol")]
    _symbol: Option<String>,
    candles: Vec<CandleJson>,
}

pub fn load_candles_json<P: AsRef<Path>>(path: P) -> Result<Vec<Candle>> {
    let content = fs::read_to_string(&path)
        .with_context(|| format!("Failed to read file: {:?}", path.as_ref()))?;

    let data: CandleData = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse JSON: {:?}", path.as_ref()))?;

    let candles: Result<Vec<Candle>> = data
        .candles
        .into_iter()
        .map(|c| {
            let timestamp = chrono::DateTime::parse_from_rfc3339(&c.timestamp)
                .with_context(|| format!("Invalid timestamp: {}", c.timestamp))?
                .with_timezone(&chrono::Utc);
            Ok(Candle {
                timestamp,
                open: c.open,
                high: c.high,
                low: c.low,
                close: c.close,
                volume: c.volume,
            })
        })
        .collect();

    candles
}

pub fn load_candles_csv<P: AsRef<Path>>(path: P) -> Result<Vec<Candle>> {
    let content = fs::read_to_string(&path)
        .with_context(|| format!("Failed to read file: {:?}", path.as_ref()))?;

    let mut reader = csv::Reader::from_reader(content.as_bytes());
    let mut candles = Vec::new();

    for result in reader.records() {
        let record = result.context("Failed to read CSV record")?;
        let timestamp = chrono::DateTime::parse_from_rfc3339(&record[0])
            .with_context(|| format!("Invalid timestamp: {}", &record[0]))?
            .with_timezone(&chrono::Utc);

        candles.push(Candle {
            timestamp,
            open: record[1].parse().context("Invalid open price")?,
            high: record[2].parse().context("Invalid high price")?,
            low: record[3].parse().context("Invalid low price")?,
            close: record[4].parse().context("Invalid close price")?,
            volume: record[5].parse().context("Invalid volume")?,
        });
    }

    Ok(candles)
}

pub fn candles_to_prices(candles: &[Candle]) -> Vec<f64> {
    candles.iter().map(|c| c.close).collect()
}

pub fn candles_to_returns(candles: &[Candle]) -> Vec<f64> {
    candles
        .windows(2)
        .map(|w| (w[1].close / w[0].close).ln())
        .collect()
}
