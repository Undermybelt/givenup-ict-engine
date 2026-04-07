use crate::state::{regime_key, FactorLearningProfile, RegimeFactorStats};
use crate::types::Regime;

/// Regime-conditional factor evaluation and learning.
pub struct RegimeConditional;

impl RegimeConditional {
    pub fn evaluate(
        factor_value: f64,
        regime: Regime,
        profile: Option<&FactorLearningProfile>,
    ) -> f64 {
        factor_value * Self::multiplier_opt(profile, regime)
    }

    pub fn multiplier(profile: &FactorLearningProfile, regime: Regime) -> f64 {
        Self::multiplier_opt(Some(profile), regime)
    }

    pub fn multiplier_opt(profile: Option<&FactorLearningProfile>, regime: Regime) -> f64 {
        profile
            .and_then(|profile| profile.regime_stats.get(regime_key(regime)))
            .map(|stats| {
                if stats.multiplier.abs() <= f64::EPSILON {
                    1.0
                } else {
                    stats.multiplier
                }
            })
            .unwrap_or_else(|| match regime {
                Regime::Accumulation => 0.95,
                Regime::ManipulationExpansion => 1.05,
                Regime::Distribution => 0.90,
            })
    }

    pub fn update_profile(
        profile: &mut FactorLearningProfile,
        regime: Regime,
        effective_success: bool,
        pnl: f64,
    ) {
        let stats = profile
            .regime_stats
            .entry(regime_key(regime).to_string())
            .or_insert_with(|| RegimeFactorStats {
                multiplier: 1.0,
                ..RegimeFactorStats::default()
            });

        stats.observations += 1;
        if effective_success {
            stats.wins += 1;
        }

        let n = stats.observations as f64;
        stats.avg_pnl = if n <= 1.0 {
            pnl
        } else {
            ((stats.avg_pnl * (n - 1.0)) + pnl) / n
        };
        let hit_rate = stats.wins as f64 / stats.observations.max(1) as f64;
        stats.multiplier = (0.5 + hit_rate + stats.avg_pnl.tanh() * 0.25).clamp(0.4, 1.6);
    }
}
