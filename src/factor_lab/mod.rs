pub mod backtest;
pub mod engine;
pub mod factor_definition;
pub mod metrics;
pub mod research;

pub use backtest::{BacktestConfig, BacktestResult, FactorBacktestEngine};
pub use engine::{FactorContext, FactorEngine, FactorResearchEngine, FactorSignal};
pub use factor_definition::FactorDefinition;
pub use metrics::BacktestMetrics;
pub use research::{FactorLab, ResearchReport};
