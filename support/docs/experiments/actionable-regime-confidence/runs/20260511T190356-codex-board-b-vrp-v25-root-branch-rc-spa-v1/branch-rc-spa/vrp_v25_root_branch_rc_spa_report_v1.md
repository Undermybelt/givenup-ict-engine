# VRP V2.5 Root-Branch RC-SPA v1

Run id: `20260511T190356+0800-codex-board-b-vrp-v25-root-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `63.3458`
- Selected trade rows: `1184`
- Variant matrix rows: `8436`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root trade counts: `{'Bull': 1000, 'Bear': 17, 'Sideways': 157, 'Crisis': 10, 'Manipulation(scoped)': 0}`
- Matrix root trade counts: `{'Bull': 7286, 'Bear': 62, 'Sideways': 991, 'Crisis': 97, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_cost_fragile; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Sideways=fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Matrix

| Market | TF | Variant | Bars | Signals | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| NQ/USD | 5m | `v2_baseline` | 563777 | 7918 | 845 | 0.000464 | 0.2450 | 0.392464 |
| NQ/USD | 5m | `v25_strict_compression` | 563777 | 5480 | 605 | 0.000416 | 0.2496 | 0.251712 |
| NQ/USD | 5m | `v25_low_vvix` | 563777 | 6397 | 673 | 0.000505 | 0.2541 | 0.340088 |
| NQ/USD | 5m | `v25_no_body_filter` | 563777 | 14165 | 853 | 0.000476 | 0.2474 | 0.406373 |
| NQ/USD | 5m | `v25_rth_tight` | 563777 | 6664 | 702 | 0.000485 | 0.2621 | 0.340433 |
| NQ/USD | 5m | `v25_local_trend_only` | 563777 | 8622 | 783 | 0.000541 | 0.2810 | 0.423987 |
| NQ/USD | 15m | `v2_baseline` | 187990 | 3054 | 418 | 0.000963 | 0.3397 | 0.402674 |
| NQ/USD | 15m | `v25_strict_compression` | 187990 | 2147 | 309 | 0.000783 | 0.3333 | 0.242092 |
| NQ/USD | 15m | `v25_low_vvix` | 187990 | 2482 | 347 | 0.000807 | 0.3343 | 0.279893 |
| NQ/USD | 15m | `v25_no_body_filter` | 187990 | 5219 | 428 | 0.000965 | 0.3341 | 0.412883 |
| NQ/USD | 15m | `v25_rth_tight` | 187990 | 2558 | 355 | 0.000971 | 0.3493 | 0.344863 |
| NQ/USD | 15m | `v25_local_trend_only` | 187990 | 3348 | 415 | 0.001042 | 0.3614 | 0.432525 |
| NQ/USD | 1h | `v2_baseline` | 47242 | 978 | 170 | 0.001709 | 0.4412 | 0.290462 |
| NQ/USD | 1h | `v25_strict_compression` | 47242 | 693 | 127 | 0.001746 | 0.4409 | 0.221682 |
| NQ/USD | 1h | `v25_low_vvix` | 47242 | 796 | 140 | 0.002076 | 0.4714 | 0.290589 |
| NQ/USD | 1h | `v25_no_body_filter` | 47242 | 1604 | 176 | 0.001946 | 0.4489 | 0.342500 |
| NQ/USD | 1h | `v25_rth_tight` | 47242 | 829 | 168 | 0.001383 | 0.4286 | 0.232312 |
| NQ/USD | 1h | `v25_local_trend_only` | 47242 | 1047 | 176 | 0.001582 | 0.4318 | 0.278383 |
| SPY/USD | 15m | `v2_baseline` | 4228 | 482 | 35 | 0.001313 | 0.3714 | 0.045960 |
| SPY/USD | 15m | `v25_strict_compression` | 4228 | 366 | 20 | 0.001682 | 0.4000 | 0.033639 |
| SPY/USD | 15m | `v25_low_vvix` | 4228 | 409 | 22 | 0.002596 | 0.4545 | 0.057104 |
| SPY/USD | 15m | `v25_no_body_filter` | 4228 | 871 | 37 | 0.001131 | 0.3514 | 0.041840 |
| SPY/USD | 15m | `v25_rth_tight` | 4228 | 447 | 33 | 0.001219 | 0.3636 | 0.040232 |
| SPY/USD | 15m | `v25_local_trend_only` | 4228 | 584 | 35 | 0.001568 | 0.4286 | 0.054878 |
| IWM/USD | 15m | `v2_baseline` | 4228 | 423 | 47 | 0.001351 | 0.3191 | 0.063506 |
| IWM/USD | 15m | `v25_strict_compression` | 4228 | 298 | 33 | 0.001269 | 0.3030 | 0.041876 |
| IWM/USD | 15m | `v25_low_vvix` | 4228 | 339 | 35 | 0.001671 | 0.3143 | 0.058482 |
| IWM/USD | 15m | `v25_no_body_filter` | 4228 | 769 | 49 | 0.000945 | 0.3061 | 0.046291 |
| IWM/USD | 15m | `v25_rth_tight` | 4228 | 396 | 45 | 0.000517 | 0.2667 | 0.023253 |
| IWM/USD | 15m | `v25_local_trend_only` | 4228 | 500 | 52 | 0.000264 | 0.3077 | 0.013738 |
| DIA/USD | 15m | `v2_baseline` | 4228 | 370 | 36 | 0.000478 | 0.3056 | 0.017221 |
| DIA/USD | 15m | `v25_strict_compression` | 4228 | 281 | 29 | 0.000033 | 0.2759 | 0.000962 |
| DIA/USD | 15m | `v25_low_vvix` | 4228 | 307 | 31 | 0.000667 | 0.3226 | 0.020681 |
| DIA/USD | 15m | `v25_no_body_filter` | 4228 | 687 | 37 | 0.000249 | 0.2973 | 0.009220 |
| DIA/USD | 15m | `v25_rth_tight` | 4228 | 343 | 33 | 0.000072 | 0.2424 | 0.002363 |
| DIA/USD | 15m | `v25_local_trend_only` | 4228 | 472 | 35 | 0.000204 | 0.2571 | 0.007134 |
| GLD/USD | 15m | `v2_baseline` | 4228 | 338 | 18 | 0.004566 | 0.3889 | 0.082193 |
| GLD/USD | 15m | `v25_strict_compression` | 4228 | 260 | 15 | 0.004766 | 0.4000 | 0.071489 |
| GLD/USD | 15m | `v25_low_vvix` | 4228 | 274 | 15 | 0.004790 | 0.4000 | 0.071846 |
| GLD/USD | 15m | `v25_no_body_filter` | 4228 | 612 | 18 | 0.004665 | 0.3889 | 0.083962 |
| GLD/USD | 15m | `v25_rth_tight` | 4228 | 309 | 18 | 0.004368 | 0.3889 | 0.078631 |
| GLD/USD | 15m | `v25_local_trend_only` | 4228 | 382 | 18 | 0.005593 | 0.4444 | 0.100681 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `v25_strict_compression` | 1000 | 5 | 51 | 1.0000 | 0.000610 | 0.200 | 4.9261 | 63.3458 | `fail:reject_cost_fragile` |
| Bear | `v25_local_trend_only` | 17 | 2 | 6 | 1.0000 | 0.000846 | 1.000 | 1.8923 | 50.4111 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Sideways | `v25_local_trend_only` | 157 | 3 | 25 | 0.6667 | 0.000104 | 1.000 | 1.7937 | 49.4620 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `v25_strict_compression` | 10 | 1 | 10 | 1.0000 | -0.001117 | 1.000 | 0.8776 | 44.4181 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- NQ/timeframe and cross-market feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Volatility sidecars: `/tmp/ict-engine-ibkr-probe`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/branch-rc-spa/vrp_v25_root_branch_rc_spa_report_v1.json`
- Selected trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/branch-rc-spa/vrp_v25_selected_branch_rows_v1.csv`
- All variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/branch-rc-spa/vrp_v25_all_variant_branch_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/branch-rc-spa/vrp_v25_branch_rc_spa_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/branch-rc-spa/vrp_v25_panel_variant_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/ict-engine-fail-closed/vrp_v25_ict_engine_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T190356-codex-board-b-vrp-v25-root-branch-rc-spa-v1/checks/vrp_v25_root_branch_rc_spa_v1_assertions.out`

## Next

- B2R-repeat: keep VRP as fail-closed evidence; next slice needs direct scoped Manipulation rows and a branch family that repairs the listed root failures without relaxing RC-SPA.
