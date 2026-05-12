# Stock Market Regimes Parent-Root Abstaining Gate

Run ID: `20260511T125122+0800-codex-stock-market-regimes-parent-root-abstain`

This run uses the confirmed source panel at `/Users/thrill3r/Downloads/stock-market-regimes-20002026`.
It targets `MainRegimeV2` parent roots directly: `Bull`, `Bear`, `Sideways`, and `Crisis`.

It does not claim full-market/full-timeframe completion. Scope is daily US equities and US equity indices after the 252-day warmup.

| Regime | Gate | Mode | Rule | Cal Wilson95 | Heldout-Time Wilson95 | Heldout-Ticker Wilson95 | Accepted |
|---|---|---|---|---:|---:|---:|---|
| `Bull` | `bull_252d_upper_range_abstain_v1` | `feature_only_non_future` | `range_pos_252 >= 0.97` | 0.980946 | 0.979723 | 0.983693 | `true` |
| `Bear` | `bear_20d_selloff_cross_section_bottom_abstain_v1` | `feature_only_non_future_panel_cross_section` | `ret_sum_20 <= -0.0477408661 AND range_pos_252_date_rank <= 0.05555555556 AND range_pos_252 <= 0.102802065` | 0.974782 | 0.963920 | 0.981443 | `true` |
| `Sideways` | `sideways_source_confidence_low_range_abstain_v1` | `source_confidence_assisted_non_future_features` | `regime_confidence >= 0.857 AND volatility <= 0.25 AND range_width_60 <= 0.25 AND abs(ret_sum_20) <= 0.05` | 0.996869 | 0.993711 | 0.998719 | `true` |
| `Crisis` | `crisis_deep_drawdown_rebound_high_vol_abstain_v1` | `feature_only_non_future` | `drawdown_252 <= -0.4112279736 AND ret_sum_20 >= 0.1485748712 AND volatility >= 0.443713301` | 0.961906 | 0.974701 | 0.975366 | `true` |

## Decision

- Accepted scoped parent roots: `Bear, Bull, Crisis, Sideways`.
- Full objective achieved: `false`.
- Gate result: `accepted_95_scoped_stock_market_regimes_parent_roots_full_matrix_still_blocked`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Guardrails

- These are parent-root gates, not child/sub-regime packets.
- `Sideways` depends on the source panel's `regime_confidence`; without that field, keep `Sideways` abstained instead of replacing it with `RangeConsolidation`.
- This daily source panel does not close intraday/multi-asset/full-species requirements.
- `Manipulation` remains direct-event/order-flow/order-lifecycle evidence only.
