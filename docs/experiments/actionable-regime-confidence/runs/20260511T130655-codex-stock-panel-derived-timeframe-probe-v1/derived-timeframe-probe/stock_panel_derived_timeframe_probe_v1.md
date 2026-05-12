# Stock Panel Derived Timeframe Probe v1

Run ID: `20260511T130655+0800-codex-stock-panel-derived-timeframe-probe-v1`

This probe derives `1w` and `1mo` parent labels by majority vote from the daily stock-market-regimes source panel.
It is a targeted full-matrix gap probe, not a native timeframe source-label acceptance.

| Timeframe | Root | Rule | Cal LCB | Heldout-Time LCB | Heldout-Ticker LCB | Accepted |
|---|---|---|---:|---:|---:|---|
| `1w` | `Bull` | `avg_regime_confidence >= 0.9666 AND ret_sum_4 >= 0.02710841687` | 0.983916 | 0.967122 | 0.985817 | `true` |
| `1w` | `Bear` | `range_pos_52 <= 0.1104018897 AND runup_13 <= 0.0216180473 AND runup_52 <= 0.03326387538` | 0.871965 | 0.880167 | 0.909888 | `false` |
| `1w` | `Sideways` | `avg_regime_confidence >= 0.833 AND ret_sum_4 <= 0.002940090941 AND range_width_13 <= 0.1248950282` | 0.977113 | 0.955765 | 0.971387 | `true` |
| `1w` | `Crisis` | `ret_sum_4 >= 0.1464923854 AND drawdown_52 <= -0.2754686015 AND volatility >= 0.3911786717` | 0.872457 | 0.865399 | 0.916337 | `false` |
| `1mo` | `Bull` | `range_pos_24 >= 1 AND runup_3 >= 0.0984973185 AND ret_sum_3 >= 0.07753638232` | 0.931942 | 0.950542 | 0.933787 | `false` |
| `1mo` | `Bear` | `runup_12 <= 0.007596319686 AND ret_sum_3 <= -0.06931598493` | 0.829670 | 0.825997 | 0.831766 | `false` |
| `1mo` | `Sideways` | `avg_regime_confidence >= 0.7909090909 AND runup_3 <= 0.02124159043 AND range_width_6 <= 0.1694708623` | 0.698719 | 0.685313 | 0.871562 | `false` |
| `1mo` | `Crisis` | `max_regime_confidence <= 0.455 AND avg_daily_abs_ret >= 0.02073235445` | 0.710074 | 0.691612 | 0.682532 | `false` |

## Decision

- New derived timeframe gates accepted: `1w:Bull`, `1w:Sideways`.
- `1w:Bear`, `1w:Crisis`, and all `1mo` roots remain below 95% in this probe.
- Full objective achieved: `false`.
- Gate result: `partial_derived_weekly_parent_roots_bull_sideways_only_full_matrix_still_blocked`.

## Guardrails

- Derived weekly/monthly labels are majority-vote aggregates from daily source labels; they are not native source labels.
- This probe targets `MainRegimeV2` parent roots only; no child/sub-regime packets are promoted.
- Raw aggregated rows are not committed.
