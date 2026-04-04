use anyhow::Result;

use crate::factor_lab::{BacktestMetrics, FactorContext, FactorEngine};
use crate::types::Candle;

#[derive(Debug, Clone)]
pub struct BacktestConfig {
    pub initial_capital: f64,
    pub signal_threshold: f64,
}

impl Default for BacktestConfig {
    fn default() -> Self {
        Self {
            initial_capital: 100_000.0,
            signal_threshold: 0.0,
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct BacktestResult {
    pub equity_curve: Vec<f64>,
    pub metrics: BacktestMetrics,
}

pub struct FactorBacktestEngine {
    factor_engine: FactorEngine,
}

impl FactorBacktestEngine {
    pub fn new(factor_engine: FactorEngine) -> Self {
        Self { factor_engine }
    }

    pub fn run(&self, candles: &[Candle], config: &BacktestConfig) -> Result<BacktestResult> {
        let signals = self.factor_engine.run(candles, &FactorContext::default())?;
        let mut equity = config.initial_capital;
        let mut curve = vec![equity];
        let mut wins = 0usize;
        let mut trades = 0usize;

        for signal in signals {
            if signal.value.abs() < config.signal_threshold {
                continue;
            }
            trades += 1;
            let pnl = signal.value * 100.0;
            if pnl > 0.0 {
                wins += 1;
            }
            equity += pnl;
            curve.push(equity);
        }

        let total_return = if config.initial_capital > 0.0 {
            (equity - config.initial_capital) / config.initial_capital
        } else {
            0.0
        };
        let hit_rate = if trades > 0 {
            wins as f64 / trades as f64
        } else {
            0.0
        };

        Ok(BacktestResult {
            equity_curve: curve,
            metrics: BacktestMetrics {
                total_return,
                sharpe: 0.0,
                max_drawdown: 0.0,
                hit_rate,
            },
        })
    }
}
