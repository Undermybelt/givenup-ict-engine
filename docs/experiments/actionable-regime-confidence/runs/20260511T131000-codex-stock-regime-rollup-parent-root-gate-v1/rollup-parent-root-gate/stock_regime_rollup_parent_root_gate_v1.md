# Stock Regime Rollup Parent-Root Gate v1

Run ID: `20260511T131000+0800-codex-stock-regime-rollup-parent-root-gate-v1`

## Result

- Accepted 95 rollup roots: `Bull`.
- Missing rollup roots: `Bear, Crisis, Sideways`.
- Gate result: `partial_rollup_stock_regime_roots_full_matrix_still_blocked`.
- Full objective achieved: `false`.

## Gates

| Root | Accepted | Rule | Cal LCB | Heldout-Time LCB | Heldout-Ticker LCB | Blockers |
|---|---|---|---:|---:|---:|---|
| Bull | `true` | `range_pos_52 >= 1` | 0.973784 | 0.977731 | 0.981804 | none |
| Bear | `false` | `range_pos_52 <= 0 AND ret_4 <= -0.152861040021` | 0.659679 | 0.873907 | 0.859840 | calibration_wilson95_below_0_95, heldout_time_wilson95_below_0_95, heldout_ticker_wilson95_below_0_95 |
| Sideways | `false` | `range_width_12 <= 0.0682262708984 AND mean_regime_confidence >= 0.9` | 0.860243 | 0.742427 | 0.890964 | calibration_support_below_50, calibration_wilson95_below_0_95, heldout_time_support_below_50, heldout_time_wilson95_below_0_95, heldout_ticker_wilson95_below_0_95 |
| Crisis | `false` | `mean_daily_volatility >= 0.451649739122 AND drawdown_52 <= -0.260962534771` | 0.634221 | 0.526297 | 0.552965 | calibration_wilson95_below_0_95, heldout_time_wilson95_below_0_95, heldout_ticker_wilson95_below_0_95 |

## Guardrails

- Same-source 1w/1mo stock-market-regimes rollup only.
- Thresholds selected on train split only.
- No source-window projection, no runtime code change, no raw data commit.
