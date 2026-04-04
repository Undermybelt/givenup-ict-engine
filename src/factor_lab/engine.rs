use anyhow::Result;

use crate::factors::registry::FactorRegistry;
use crate::types::Candle;

#[derive(Debug, Clone, Default)]
pub struct FactorContext;

#[derive(Debug, Clone, Default)]
pub struct FactorSignal {
    pub value: f64,
}

pub struct FactorEngine {
    pub registry: FactorRegistry,
}

impl FactorEngine {
    pub fn new(registry: FactorRegistry) -> Self {
        Self { registry }
    }

    pub fn run(&self, candles: &[Candle], _context: &FactorContext) -> Result<Vec<FactorSignal>> {
        let count = candles.len().saturating_sub(1);
        Ok((0..count).map(|_| FactorSignal { value: 0.0 }).collect())
    }
}

pub type FactorResearchEngine = FactorEngine;
