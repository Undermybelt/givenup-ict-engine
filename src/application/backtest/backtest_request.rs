use serde::Serialize;

#[derive(Debug, Clone, Serialize, Default)]
pub struct BacktestRequest {
    pub symbol: String,
    pub market: String,
    pub interval: String,
    pub window: String,
    pub objective: String,
    pub factor_filter: Vec<String>,
    pub regime_filter: Vec<String>,
    pub use_multi_timeframe: bool,
    pub source: String,
}

pub fn build_backtest_request(
    symbol: impl Into<String>,
    market: impl Into<String>,
    interval: impl Into<String>,
    window: impl Into<String>,
    objective: impl Into<String>,
    factor_filter: &[String],
    regime_filter: &[String],
    use_multi_timeframe: bool,
    source: impl Into<String>,
) -> BacktestRequest {
    BacktestRequest {
        symbol: symbol.into(),
        market: market.into(),
        interval: interval.into(),
        window: window.into(),
        objective: objective.into(),
        factor_filter: factor_filter.to_vec(),
        regime_filter: regime_filter.to_vec(),
        use_multi_timeframe,
        source: source.into(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn backtest_request_builder_keeps_market() {
        let req = build_backtest_request(
            "NQ", "futures", "15m", "2024Q1", "generic", &[], &[], true, "history"
        );
        assert_eq!(req.market, "futures");
        assert!(req.use_multi_timeframe);
    }
}
