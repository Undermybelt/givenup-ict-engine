# 175350 High-Density Multibranch Provider Materials v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T175350+0800-codex-high-density-multibranch-six-provider-aq-v1`

Purpose: materialize a Board B profitability-factor packet that keeps the regime-factor root as the first-class branch key.

Branch paths:
- `TrendExpansion -> NormalVolatility -> MomentumPullbackFast -> ema_rsi_pullback_density_v1`
- `TrendExpansion -> HighVolatility -> BreakoutContinuationFast -> donchian_volume_breakout_density_v1`
- `RangeConsolidation -> NormalVolatility -> MeanReversionFast -> rsi_bollinger_reversion_density_v1`
- `Transition -> VolatilityCompression -> CompressionBreakoutFast -> atr_compression_breakout_density_v1`

Provider handling:
- Six provider rows and six agent-material JSON files are generated under this root.
- Data files are same-root copies of prior verified provider-normalized artifacts, not newly acquired provider fetches in this step.
- Current provider-status and TVR harness readbacks must be stored separately before any downstream promotion claim.

Gate:
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
