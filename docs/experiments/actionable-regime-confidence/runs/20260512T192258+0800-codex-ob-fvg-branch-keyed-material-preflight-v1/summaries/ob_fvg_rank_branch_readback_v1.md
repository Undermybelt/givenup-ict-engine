# OB/FVG Rank Branch Readback v1

- Joined rows: `60/60`.
- Missing rows: `0`.
- Branch count: `10`.
- Provider count: `6`.
- Nonzero trade rows: `20`.
- Zero trade rows: `40`.
- Total trade count: `1485`.
- Rank joined to explicit branch fields: `true`.
- Quality weight for downstream learning: `0_for_bbn_catboost_execution_tree_learning`.
- Pre-Bayes/filter allowed: `false`.
- BBN learning allowed: `false`.
- CatBoost/path-ranker learning allowed: `false`.
- Execution-tree branch-weight update allowed: `false`.

## Branch Stats

| Branch path | Rows | Nonzero | Trades | Positive rows | Negative rows | Zero rows |
|---|---:|---:|---:|---:|---:|---:|
| `CrossMarketConfirmation -> SMTConfirmedContinuation -> fvg_or_order_block_retest -> smt_confirmed_ob_fvg_continuation_v1` | 6 | 2 | 143 | 1 | 1 | 4 |
| `SessionContinuation -> KillzoneRetest -> session_fvg_retest -> session_fvg_continuation_v1` | 6 | 2 | 277 | 0 | 2 | 4 |
| `SessionContinuation -> KillzoneRetest -> session_order_block_retest -> session_ob_continuation_v1` | 6 | 2 | 140 | 0 | 2 | 4 |
| `Transition -> RiskSuppression -> failed_mitigation_guard -> ob_fvg_failed_mitigation_guard_v1` | 6 | 2 | 106 | 2 | 0 | 4 |
| `TrendExpansion -> OTERetracement -> ote_plus_fvg_retest -> ote_fvg_continuation_long_v1` | 6 | 2 | 168 | 0 | 2 | 4 |
| `TrendExpansion -> OTERetracement -> ote_plus_order_block_retest -> ote_ob_continuation_long_v1` | 6 | 2 | 75 | 1 | 1 | 4 |
| `TrendExpansion -> PullbackContinuation -> bullish_order_block_retest -> order_block_retest_continuation_long_v1` | 6 | 2 | 107 | 0 | 2 | 4 |
| `TrendExpansion -> PullbackContinuation -> fair_value_gap_retest -> fvg_retest_continuation_long_v1` | 6 | 2 | 162 | 0 | 2 | 4 |
| `TrendExpansion -> PullbackContinuation -> fvg_plus_order_block_confluence -> ob_fvg_confluence_continuation_long_v1` | 6 | 2 | 122 | 0 | 2 | 4 |
| `VolatilityCompression -> LiquidityExpansion -> displacement_fvg_retest -> fvg_displacement_retest_expansion_v1` | 6 | 2 | 185 | 0 | 2 | 4 |
