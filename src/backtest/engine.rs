use crate::types::{Candle, Direction, TradePlan, TradeRecord};

#[derive(Debug, Clone)]
pub struct SimulatedTrade {
    pub entry_index: usize,
    pub exit_index: usize,
    pub entry_price: f64,
    pub exit_price: f64,
    pub pnl: f64,
}

/// Backtest engine
pub struct BacktestEngine {
    pub trades: Vec<TradeRecord>,
}

impl BacktestEngine {
    pub fn new() -> Self {
        Self { trades: Vec::new() }
    }

    /// Run backtest
    pub fn run(&mut self, candles: &[Candle], strategy: &dyn Fn(&[Candle]) -> Vec<TradeRecord>) {
        self.trades = strategy(candles);
    }

    /// Get trades
    pub fn get_trades(&self) -> &[TradeRecord] {
        &self.trades
    }

    pub fn simulate_trade(
        candles: &[Candle],
        signal_index: usize,
        plan: &TradePlan,
        hold_bars: usize,
    ) -> Option<SimulatedTrade> {
        if plan.direction == Direction::Neutral
            || hold_bars == 0
            || signal_index + 1 >= candles.len()
        {
            return None;
        }

        let search_end = (signal_index + hold_bars).min(candles.len().saturating_sub(1));
        let entry_index = (signal_index + 1..=search_end)
            .find(|&idx| price_touches(&candles[idx], plan.entry))?;

        let exit_end = (entry_index + hold_bars).min(candles.len().saturating_sub(1));
        for exit_index in entry_index..=exit_end {
            let candle = &candles[exit_index];

            match plan.direction {
                Direction::Bull => {
                    if candle.low <= plan.stop_loss {
                        return Some(Self::build_result(
                            plan,
                            entry_index,
                            exit_index,
                            plan.entry,
                            plan.stop_loss,
                        ));
                    }
                    if candle.high >= plan.tp1 {
                        return Some(Self::build_result(
                            plan,
                            entry_index,
                            exit_index,
                            plan.entry,
                            plan.tp1,
                        ));
                    }
                }
                Direction::Bear => {
                    if candle.high >= plan.stop_loss {
                        return Some(Self::build_result(
                            plan,
                            entry_index,
                            exit_index,
                            plan.entry,
                            plan.stop_loss,
                        ));
                    }
                    if candle.low <= plan.tp1 {
                        return Some(Self::build_result(
                            plan,
                            entry_index,
                            exit_index,
                            plan.entry,
                            plan.tp1,
                        ));
                    }
                }
                Direction::Neutral => return None,
            }
        }

        Some(Self::build_result(
            plan,
            entry_index,
            exit_end,
            plan.entry,
            candles[exit_end].close,
        ))
    }

    fn build_result(
        plan: &TradePlan,
        entry_index: usize,
        exit_index: usize,
        entry_price: f64,
        exit_price: f64,
    ) -> SimulatedTrade {
        let signed_return = match plan.direction {
            Direction::Bull => (exit_price - entry_price) / entry_price.max(f64::EPSILON),
            Direction::Bear => (entry_price - exit_price) / entry_price.max(f64::EPSILON),
            Direction::Neutral => 0.0,
        };

        SimulatedTrade {
            entry_index,
            exit_index,
            entry_price,
            exit_price,
            pnl: signed_return * plan.kelly_fraction,
        }
    }
}

fn price_touches(candle: &Candle, price: f64) -> bool {
    candle.low <= price && candle.high >= price
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{CascadeResult, Direction, Regime, Symbol, TradePlan};
    use chrono::Utc;

    fn candle(open: f64, high: f64, low: f64, close: f64) -> Candle {
        Candle {
            timestamp: Utc::now(),
            open,
            high,
            low,
            close,
            volume: 1_000.0,
        }
    }

    fn plan(direction: Direction) -> TradePlan {
        TradePlan {
            symbol: Symbol::NQ,
            direction,
            entry: 100.0,
            stop_loss: 98.0,
            tp1: 103.0,
            tp2: 104.0,
            tp3: 105.0,
            risk_reward: 1.5,
            kelly_fraction: 0.1,
            position_size: 10.0,
            regime: Regime::ManipulationExpansion,
            posterior: 0.2,
            win_probability: 0.6,
            cascade_bull: CascadeResult {
                direction: Direction::Bull,
                stopped_at: None,
                steps: Vec::new(),
                final_posterior: 0.7,
            },
            cascade_bear: CascadeResult {
                direction: Direction::Bear,
                stopped_at: None,
                steps: Vec::new(),
                final_posterior: 0.3,
            },
            uncertainties: Vec::new(),
        }
    }

    #[test]
    fn test_simulate_trade_hits_take_profit() {
        let candles = vec![
            candle(99.0, 99.5, 98.5, 99.2),
            candle(99.5, 100.5, 99.0, 100.0),
            candle(100.0, 103.5, 99.8, 103.0),
        ];

        let simulated =
            BacktestEngine::simulate_trade(&candles, 0, &plan(Direction::Bull), 2).unwrap();
        assert_eq!(simulated.entry_index, 1);
        assert_eq!(simulated.exit_index, 2);
        assert!(simulated.pnl > 0.0);
    }

    #[test]
    fn test_simulate_trade_requires_entry_touch() {
        let candles = vec![
            candle(99.0, 99.5, 98.5, 99.2),
            candle(104.0, 105.0, 103.5, 104.5),
            candle(104.5, 105.5, 104.0, 105.0),
        ];

        let simulated = BacktestEngine::simulate_trade(&candles, 0, &plan(Direction::Bull), 2);
        assert!(simulated.is_none());
    }
}
