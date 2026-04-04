use anyhow::Result;

use crate::factor_lab::{BacktestConfig, FactorBacktestEngine, FactorResearchEngine};
use crate::factors::FactorRegistry;
use crate::types::Candle;

#[derive(Debug, Clone, Default)]
pub struct ResearchReport {
    pub factor_count: usize,
    pub best_factor: Option<String>,
    pub aggregate_return: f64,
}

pub struct FactorLab {
    registry: FactorRegistry,
}

impl FactorLab {
    pub fn new(registry: FactorRegistry) -> Self {
        Self { registry }
    }

    pub fn run_research(&self, candles: &[Candle]) -> Result<ResearchReport> {
        let mut registry = FactorRegistry::new();
        let factor_names: Vec<String> = self
            .registry
            .list()
            .iter()
            .map(|factor| {
                registry.register((*factor).clone());
                factor.name.clone()
            })
            .collect();

        let engine = FactorResearchEngine::new(registry);
        let backtest = FactorBacktestEngine::new(engine);
        let result = backtest.run(candles, &BacktestConfig::default())?;

        Ok(ResearchReport {
            factor_count: factor_names.len(),
            best_factor: factor_names.first().cloned(),
            aggregate_return: result.metrics.total_return,
        })
    }
}
