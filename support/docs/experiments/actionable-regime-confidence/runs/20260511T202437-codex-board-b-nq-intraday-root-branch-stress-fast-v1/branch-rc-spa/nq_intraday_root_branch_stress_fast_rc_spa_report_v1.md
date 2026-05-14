# Root Transition Triad RC-SPA v1

Run id: `20260511T202437+0800-codex-board-b-nq-intraday-root-branch-stress-fast-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `31.0000`
- Variant rows: `527959`
- Selected rows: `79369`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root counts: `{'Bull': 42109, 'Bear': 5839, 'Sideways': 30890, 'Crisis': 531, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| NQ/USD | 5m | `bear_intraday_breakdown_short` | 29979 | -0.000659 | 0.3038 | -19.752336 |
| NQ/USD | 5m | `bear_intraday_relief_long` | 39131 | -0.000740 | 0.2521 | -28.945504 |
| NQ/USD | 5m | `bear_intraday_vol_compression_short` | 22295 | -0.000632 | 0.3322 | -14.089565 |
| NQ/USD | 5m | `sideways_intraday_band_reversion` | 61584 | -0.000765 | 0.2395 | -47.097482 |
| NQ/USD | 5m | `sideways_intraday_range_breakout` | 41041 | -0.000714 | 0.2703 | -29.320707 |
| NQ/USD | 5m | `sideways_intraday_microtrend_filter` | 38392 | -0.000704 | 0.2926 | -27.019336 |
| NQ/USD | 5m | `crisis_intraday_tail_short` | 27319 | -0.000689 | 0.2867 | -18.822751 |
| NQ/USD | 5m | `crisis_intraday_relief_long` | 41345 | -0.000741 | 0.2219 | -30.655513 |
| NQ/USD | 5m | `crisis_intraday_abstain_defensive` | 31677 | -0.000724 | 0.2381 | -22.934919 |
| NQ/USD | 15m | `bear_intraday_breakdown_short` | 14043 | -0.000551 | 0.3741 | -7.739924 |
| NQ/USD | 15m | `bear_intraday_relief_long` | 17717 | -0.000685 | 0.3190 | -12.129233 |
| NQ/USD | 15m | `bear_intraday_vol_compression_short` | 10271 | -0.000420 | 0.3985 | -4.314335 |
| NQ/USD | 15m | `sideways_intraday_band_reversion` | 24103 | -0.000721 | 0.3232 | -17.380153 |
| NQ/USD | 15m | `sideways_intraday_range_breakout` | 17210 | -0.000610 | 0.3507 | -10.500189 |
| NQ/USD | 15m | `sideways_intraday_microtrend_filter` | 19691 | -0.000628 | 0.3496 | -12.370590 |
| NQ/USD | 15m | `crisis_intraday_tail_short` | 12610 | -0.000580 | 0.3612 | -7.309389 |
| NQ/USD | 15m | `crisis_intraday_relief_long` | 16491 | -0.000638 | 0.3135 | -10.529467 |
| NQ/USD | 15m | `crisis_intraday_abstain_defensive` | 14757 | -0.000644 | 0.3167 | -9.501316 |
| NQ/USD | 1h | `bear_intraday_breakdown_short` | 5102 | -0.000143 | 0.4567 | -0.731129 |
| NQ/USD | 1h | `bear_intraday_relief_long` | 5739 | -0.000428 | 0.4276 | -2.457099 |
| NQ/USD | 1h | `bear_intraday_vol_compression_short` | 3939 | -0.000008 | 0.4740 | -0.030308 |
| NQ/USD | 1h | `sideways_intraday_band_reversion` | 7178 | -0.000504 | 0.4209 | -3.616883 |
| NQ/USD | 1h | `sideways_intraday_range_breakout` | 5184 | -0.000190 | 0.4585 | -0.982682 |
| NQ/USD | 1h | `sideways_intraday_microtrend_filter` | 6193 | -0.000332 | 0.4482 | -2.054635 |
| NQ/USD | 1h | `crisis_intraday_tail_short` | 4481 | -0.000211 | 0.4628 | -0.945365 |
| NQ/USD | 1h | `crisis_intraday_relief_long` | 5363 | -0.000313 | 0.4333 | -1.679040 |
| NQ/USD | 1h | `crisis_intraday_abstain_defensive` | 5124 | -0.000409 | 0.4219 | -2.096016 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bear_intraday_breakdown_short` | 42109 | 15 | 509 | 0.0000 | -0.000612 | 0.000 | -40.1056 | 25.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | `bear_intraday_vol_compression_short` | 5839 | 13 | 101 | 0.0769 | -0.000537 | 0.077 | -3.8747 | 23.0769 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `sideways_intraday_band_reversion` | 30890 | 15 | 677 | 0.0000 | -0.000871 | 0.133 | -46.4058 | 19.6667 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_intraday_relief_long` | 531 | 5 | 29 | 0.4000 | -0.000870 | 0.000 | -2.2174 | 31.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/branch-rc-spa/nq_intraday_root_branch_stress_fast_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/branch-rc-spa/nq_intraday_root_branch_stress_fast_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/branch-rc-spa/nq_intraday_root_branch_stress_fast_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/branch-rc-spa/nq_intraday_root_branch_stress_fast_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/branch-rc-spa/nq_intraday_root_branch_stress_fast_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/ict-engine-fail-closed/nq_intraday_root_branch_stress_fast_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T202437-codex-board-b-nq-intraday-root-branch-stress-fast-v1/checks/nq_intraday_root_branch_stress_fast_v1_assertions.out`

## Next

- B2R-repeat: keep RootTransitionTriad as fail-closed evidence; direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA.
