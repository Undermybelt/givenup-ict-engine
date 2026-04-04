#[derive(Debug, Clone, Default)]
pub struct BacktestMetrics {
    pub total_return: f64,
    pub sharpe: f64,
    pub max_drawdown: f64,
    pub hit_rate: f64,
}
