//! Parser for `run_ibkr.log` (Auto-Quant's per-strategy --- block log).
//!
//! Used as a redundant cross-check during `auto-quant-results-import`:
//! the manifest produced by `export_strategy_library.py` is the
//! canonical source of metrics, but this parser lets us verify that
//! the manifest matches what was actually emitted by the most recent
//! `run_ibkr.py` invocation. It mirrors the producer-side parser in
//! `Auto-Quant/export_strategy_library.py:parse_log` so block format
//! drift on either side is loud, not silent.

use std::collections::BTreeMap;
use std::path::Path;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

use super::manifest::StrategyLibraryValidationMetrics;

/// One `---` block lifted from a `run_ibkr.log`.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct RunIbkrLogBlock {
    pub strategy: String,
    pub commit: String,
    pub config: String,
    pub timerange: String,
    pub pairs: Vec<String>,
    pub auto_quant_meta: Option<serde_json::Value>,
    /// "ok" | "error" — derived from a `status: ERROR` line in the block.
    pub status: String,
    pub error_type: String,
    pub error_msg: String,
    pub aggregate: StrategyLibraryValidationMetrics,
    pub per_pair: BTreeMap<String, StrategyLibraryValidationMetrics>,
}

/// Parse the entire log into a list of `RunIbkrLogBlock`s, in source order.
pub fn parse_run_ibkr_log<P: AsRef<Path>>(path: P) -> Result<Vec<RunIbkrLogBlock>> {
    let path = path.as_ref();
    let text = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read run_ibkr log '{}'", path.display()))?;
    Ok(parse_run_ibkr_log_text(&text))
}

/// In-memory variant; useful for unit tests.
pub fn parse_run_ibkr_log_text(text: &str) -> Vec<RunIbkrLogBlock> {
    let mut blocks: Vec<RunIbkrLogBlock> = Vec::new();
    let mut current: Option<RunIbkrLogBlock> = None;
    let mut in_per_pair = false;

    for raw in text.lines() {
        if raw.trim() == "---" {
            if let Some(block) = current.take() {
                blocks.push(block);
            }
            current = Some(RunIbkrLogBlock {
                status: "ok".to_string(),
                ..Default::default()
            });
            in_per_pair = false;
            continue;
        }
        let Some(block) = current.as_mut() else {
            continue;
        };

        if raw.starts_with("per_pair:") {
            in_per_pair = true;
            continue;
        }

        if in_per_pair {
            if let Some((pair, metrics)) = parse_per_pair_line(raw) {
                block.per_pair.insert(pair, metrics);
                continue;
            }
            // Non-matching line ends the per_pair section.
            in_per_pair = false;
        }

        if let Some((key, value)) = parse_kv(raw) {
            apply_kv(block, &key, value.trim());
        }
    }
    if let Some(block) = current.take() {
        blocks.push(block);
    }
    blocks
}

fn parse_kv(line: &str) -> Option<(String, &str)> {
    let mut chars = line.chars();
    let mut key = String::new();
    while let Some(ch) = chars.clone().next() {
        if ch.is_ascii_alphanumeric() || ch == '_' {
            key.push(ch);
            chars.next();
        } else {
            break;
        }
    }
    if key.is_empty() {
        return None;
    }
    let rest = chars.as_str();
    rest.strip_prefix(':').map(|tail| (key, tail))
}

fn apply_kv(block: &mut RunIbkrLogBlock, key: &str, value: &str) {
    match key {
        "strategy" => block.strategy = value.to_string(),
        "commit" => block.commit = value.to_string(),
        "config" => block.config = value.to_string(),
        "timerange" => block.timerange = value.to_string(),
        "pairs" => {
            block.pairs = value
                .split(',')
                .filter(|p| !p.is_empty())
                .map(|p| p.trim().to_string())
                .collect();
        }
        "auto_quant_meta" => {
            block.auto_quant_meta = serde_json::from_str(value).ok();
        }
        "status" => {
            block.status = if value.eq_ignore_ascii_case("ERROR") {
                "error".to_string()
            } else {
                "ok".to_string()
            };
        }
        "error_type" => block.error_type = value.to_string(),
        "error_msg" => block.error_msg = value.to_string(),
        "sharpe" => {
            if let Ok(v) = value.parse() {
                block.aggregate.sharpe = v;
            }
        }
        "sortino" => {
            if let Ok(v) = value.parse() {
                block.aggregate.sortino = v;
            }
        }
        "calmar" => {
            if let Ok(v) = value.parse() {
                block.aggregate.calmar = v;
            }
        }
        "total_profit_pct" => {
            if let Ok(v) = value.parse() {
                block.aggregate.total_profit_pct = v;
            }
        }
        "max_drawdown_pct" => {
            if let Ok(v) = value.parse() {
                block.aggregate.max_drawdown_pct = v;
            }
        }
        "trade_count" => {
            if let Ok(v) = value.parse() {
                block.aggregate.trade_count = v;
            }
        }
        "win_rate_pct" => {
            if let Ok(v) = value.parse() {
                block.aggregate.win_rate_pct = v;
            }
        }
        "profit_factor" => {
            if let Ok(v) = value.parse() {
                block.aggregate.profit_factor = v;
            }
        }
        _ => {}
    }
}

/// Parse a per_pair indented line of the form
/// `  PAIR: sharpe=… trades=… profit_pct=… dd_pct=… wr=… pf=…`
fn parse_per_pair_line(raw: &str) -> Option<(String, StrategyLibraryValidationMetrics)> {
    let trimmed = raw.trim_start();
    let (pair, rest) = trimmed.split_once(':')?;
    let pair = pair.trim().to_string();
    if pair.is_empty() {
        return None;
    }
    let mut metrics = StrategyLibraryValidationMetrics::default();
    let mut found_any = false;
    for token in rest.split_whitespace() {
        let Some((field, value)) = token.split_once('=') else {
            continue;
        };
        let parsed = value.parse::<f64>().ok();
        let parsed_int = value.parse::<u32>().ok();
        match (field, parsed, parsed_int) {
            ("sharpe", Some(v), _) => {
                metrics.sharpe = v;
                found_any = true;
            }
            ("trades", _, Some(v)) => {
                metrics.trade_count = v;
                found_any = true;
            }
            ("profit_pct", Some(v), _) => {
                metrics.total_profit_pct = v;
                found_any = true;
            }
            ("dd_pct", Some(v), _) => {
                metrics.max_drawdown_pct = v;
                found_any = true;
            }
            ("wr", Some(v), _) => {
                metrics.win_rate_pct = v;
                found_any = true;
            }
            ("pf", Some(v), _) => {
                metrics.profit_factor = v;
                found_any = true;
            }
            _ => {}
        }
    }
    if found_any {
        Some((pair, metrics))
    } else {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SAMPLE_LOG: &str = "preamble line\n\
---\n\
strategy:         GoodStrat\n\
commit:           abc1234\n\
config:           config.ibkr.json\n\
timerange:        20240101-20240201\n\
pairs:            SPY/USD,QQQ/USD\n\
auto_quant_meta:  {\"strategy\":\"GoodStrat\",\"mutation_id\":\"mb-001\",\"base_factor\":\"f\",\"hypothesis\":\"h\",\"paradigm\":\"p\",\"expected_regime\":\"r\",\"factors_used\":[\"bos\"],\"parent\":\"root\",\"asset_class\":\"equities\",\"status\":\"active\",\"created\":\"\"}\n\
sharpe:           1.4200\n\
sortino:          2.1300\n\
calmar:           4.5000\n\
total_profit_pct: 12.3000\n\
max_drawdown_pct: -3.2000\n\
trade_count:      87\n\
win_rate_pct:     54.5000\n\
profit_factor:    1.8500\n\
per_pair:\n\
  SPY/USD: sharpe=1.5000 trades=50 profit_pct=15.00 dd_pct=-2.50 wr=58.0 pf=2.10\n\
  QQQ/USD: sharpe=1.3000 trades=37 profit_pct=8.50 dd_pct=-3.80 wr=49.0 pf=1.55\n\
\n\
---\n\
strategy:         BrokenStrat\n\
commit:           abc1234\n\
config:           config.ibkr.json\n\
auto_quant_meta:  {\"strategy\":\"BrokenStrat\",\"mutation_id\":\"mb-002\",\"base_factor\":\"f\",\"hypothesis\":\"h\",\"paradigm\":\"p\",\"expected_regime\":\"r\",\"factors_used\":[\"x\"],\"parent\":\"root\",\"asset_class\":\"equities\",\"status\":\"active\",\"created\":\"\"}\n\
status:           ERROR\n\
error_type:       ValueError\n\
error_msg:        boom\n\
traceback:\n\
  File \"x\", line 1\n";

    #[test]
    fn parses_two_blocks_with_status_split() {
        let blocks = parse_run_ibkr_log_text(SAMPLE_LOG);
        assert_eq!(blocks.len(), 2);
        assert_eq!(blocks[0].status, "ok");
        assert_eq!(blocks[1].status, "error");
    }

    #[test]
    fn extracts_aggregate_metrics() {
        let blocks = parse_run_ibkr_log_text(SAMPLE_LOG);
        let good = &blocks[0];
        assert_eq!(good.strategy, "GoodStrat");
        assert!((good.aggregate.sharpe - 1.42).abs() < 1e-9);
        assert_eq!(good.aggregate.trade_count, 87);
        assert!((good.aggregate.win_rate_pct - 54.5).abs() < 1e-9);
    }

    #[test]
    fn extracts_per_pair_metrics() {
        let blocks = parse_run_ibkr_log_text(SAMPLE_LOG);
        let good = &blocks[0];
        assert_eq!(good.per_pair.len(), 2);
        let spy = good.per_pair.get("SPY/USD").unwrap();
        assert_eq!(spy.trade_count, 50);
        assert!((spy.win_rate_pct - 58.0).abs() < 1e-9);
    }

    #[test]
    fn captures_error_type_and_msg() {
        let blocks = parse_run_ibkr_log_text(SAMPLE_LOG);
        let bad = &blocks[1];
        assert_eq!(bad.error_type, "ValueError");
        assert_eq!(bad.error_msg, "boom");
    }

    #[test]
    fn captures_auto_quant_meta_json() {
        let blocks = parse_run_ibkr_log_text(SAMPLE_LOG);
        let good = &blocks[0];
        let meta = good.auto_quant_meta.as_ref().unwrap();
        assert_eq!(
            meta.get("mutation_id").and_then(|v| v.as_str()),
            Some("mb-001")
        );
    }
}
