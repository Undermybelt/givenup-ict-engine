# RootTransitionTriadV1 Branch RC-SPA v1

Run id: `20260511T192018+0800-codex-board-b-root-transition-triad-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `90.7807`
- Selected trade rows: `3358`
- Variant matrix rows: `16418`
- Branch paths evaluated: `5`
- Branch paths passed: `2`
- Selected root trade counts: `{'Bull': 2748, 'Bear': 71, 'Sideways': 487, 'Crisis': 52, 'Manipulation(scoped)': 0}`
- Matrix root trade counts: `{'Bull': 12911, 'Bear': 611, 'Sideways': 2732, 'Crisis': 164, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bear=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Matrix

| Market | TF | Variant | Bars | Signals | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| NQ/USD | 5m | `bull_transition_pullback` | 564040 | 34460 | 1484 | 0.001241 | 0.5620 | 1.840946 |
| NQ/USD | 5m | `root_continuation` | 564040 | 31605 | 1248 | 0.001446 | 0.5857 | 1.804211 |
| NQ/USD | 5m | `sideways_range_reversion` | 564040 | 18243 | 1603 | 0.000887 | 0.5639 | 1.422634 |
| NQ/USD | 5m | `bear_crisis_relief` | 564040 | 104 | 28 | 0.012879 | 0.5714 | 0.360623 |
| NQ/USD | 5m | `compressed_break_continuation` | 564040 | 3265 | 709 | 0.000449 | 0.5487 | 0.318588 |
| NQ/USD | 15m | `bull_transition_pullback` | 188077 | 11803 | 1269 | 0.000899 | 0.5697 | 1.140776 |
| NQ/USD | 15m | `root_continuation` | 188077 | 11609 | 1180 | 0.001490 | 0.5822 | 1.757876 |
| NQ/USD | 15m | `sideways_range_reversion` | 188077 | 6432 | 1162 | 0.000696 | 0.5620 | 0.809225 |
| NQ/USD | 15m | `bear_crisis_relief` | 188077 | 53 | 22 | -0.001288 | 0.4091 | -0.028326 |
| NQ/USD | 15m | `compressed_break_continuation` | 188077 | 1724 | 576 | 0.001800 | 0.5903 | 1.036579 |
| NQ/USD | 1h | `bull_transition_pullback` | 47263 | 3801 | 1075 | 0.000880 | 0.5730 | 0.946463 |
| NQ/USD | 1h | `root_continuation` | 47263 | 3659 | 1060 | 0.001067 | 0.5821 | 1.131021 |
| NQ/USD | 1h | `sideways_range_reversion` | 47263 | 1308 | 567 | 0.000653 | 0.5838 | 0.370510 |
| NQ/USD | 1h | `bear_crisis_relief` | 47263 | 30 | 23 | -0.001040 | 0.4783 | -0.023920 |
| NQ/USD | 1h | `compressed_break_continuation` | 47263 | 2649 | 910 | 0.001186 | 0.5824 | 1.079557 |
| NQ/USD | 1d | `bull_transition_pullback` | 2492 | 602 | 289 | 0.000627 | 0.5813 | 0.181184 |
| NQ/USD | 1d | `root_continuation` | 2492 | 790 | 413 | 0.000509 | 0.5593 | 0.210079 |
| NQ/USD | 1d | `sideways_range_reversion` | 2492 | 91 | 58 | 0.001070 | 0.5172 | 0.062063 |
| NQ/USD | 1d | `bear_crisis_relief` | 2492 | 51 | 38 | -0.000095 | 0.4737 | -0.003595 |
| NQ/USD | 1d | `compressed_break_continuation` | 2492 | 542 | 226 | 0.001798 | 0.5841 | 0.406401 |
| SPY/USD | 15m | `bull_transition_pullback` | 6490 | 1602 | 60 | 0.003429 | 0.6167 | 0.205737 |
| SPY/USD | 15m | `root_continuation` | 6490 | 1639 | 98 | 0.000376 | 0.5408 | 0.036891 |
| SPY/USD | 15m | `sideways_range_reversion` | 6490 | 672 | 76 | 0.002919 | 0.6579 | 0.221873 |
| SPY/USD | 15m | `bear_crisis_relief` | 6490 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 15m | `compressed_break_continuation` | 6490 | 1087 | 62 | 0.001042 | 0.5645 | 0.064606 |
| SPY/USD | 1h | `bull_transition_pullback` | 1746 | 556 | 57 | 0.003101 | 0.6140 | 0.176735 |
| SPY/USD | 1h | `root_continuation` | 1746 | 518 | 80 | 0.000379 | 0.6125 | 0.030314 |
| SPY/USD | 1h | `sideways_range_reversion` | 1746 | 142 | 34 | 0.003017 | 0.6471 | 0.102570 |
| SPY/USD | 1h | `bear_crisis_relief` | 1746 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| SPY/USD | 1h | `compressed_break_continuation` | 1746 | 346 | 41 | 0.004638 | 0.6585 | 0.190167 |
| QQQ/USD | 1h | `bull_transition_pullback` | 1735 | 507 | 63 | 0.001371 | 0.6349 | 0.086398 |
| QQQ/USD | 1h | `root_continuation` | 1735 | 417 | 79 | 0.000568 | 0.5696 | 0.044844 |
| QQQ/USD | 1h | `sideways_range_reversion` | 1735 | 114 | 25 | -0.002034 | 0.4800 | -0.050848 |
| QQQ/USD | 1h | `bear_crisis_relief` | 1735 | 5 | 4 | 0.010020 | 0.5000 | 0.040080 |
| QQQ/USD | 1h | `compressed_break_continuation` | 1735 | 342 | 47 | 0.003787 | 0.6809 | 0.177972 |
| QQQ/USD | 1d | `bull_transition_pullback` | 250 | 57 | 30 | 0.002207 | 0.6000 | 0.066203 |
| QQQ/USD | 1d | `root_continuation` | 250 | 84 | 44 | 0.000570 | 0.5682 | 0.025059 |
| QQQ/USD | 1d | `sideways_range_reversion` | 250 | 5 | 5 | -0.014000 | 0.2000 | -0.070000 |
| QQQ/USD | 1d | `bear_crisis_relief` | 250 | 5 | 4 | 0.007500 | 0.5000 | 0.030000 |
| QQQ/USD | 1d | `compressed_break_continuation` | 250 | 66 | 28 | -0.000324 | 0.6071 | -0.009073 |
| IWM/USD | 15m | `bull_transition_pullback` | 6490 | 1542 | 61 | 0.002454 | 0.5410 | 0.149716 |
| IWM/USD | 15m | `root_continuation` | 6490 | 1488 | 100 | 0.000093 | 0.5100 | 0.009272 |
| IWM/USD | 15m | `sideways_range_reversion` | 6490 | 767 | 82 | 0.004025 | 0.5976 | 0.330046 |
| IWM/USD | 15m | `bear_crisis_relief` | 6490 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 15m | `compressed_break_continuation` | 6490 | 901 | 61 | 0.002794 | 0.5574 | 0.170412 |
| IWM/USD | 1h | `bull_transition_pullback` | 1746 | 500 | 59 | 0.003982 | 0.6102 | 0.234947 |
| IWM/USD | 1h | `root_continuation` | 1746 | 450 | 79 | 0.001329 | 0.5570 | 0.104962 |
| IWM/USD | 1h | `sideways_range_reversion` | 1746 | 167 | 38 | 0.007515 | 0.6579 | 0.285588 |
| IWM/USD | 1h | `bear_crisis_relief` | 1746 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| IWM/USD | 1h | `compressed_break_continuation` | 1746 | 269 | 44 | 0.001869 | 0.5682 | 0.082240 |
| DIA/USD | 15m | `bull_transition_pullback` | 6490 | 1420 | 60 | 0.002616 | 0.5667 | 0.156987 |
| DIA/USD | 15m | `root_continuation` | 6490 | 1405 | 92 | 0.000391 | 0.6196 | 0.035951 |
| DIA/USD | 15m | `sideways_range_reversion` | 6490 | 784 | 85 | 0.003303 | 0.6235 | 0.280723 |
| DIA/USD | 15m | `bear_crisis_relief` | 6490 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 15m | `compressed_break_continuation` | 6490 | 864 | 63 | -0.000450 | 0.4921 | -0.028348 |
| DIA/USD | 1h | `bull_transition_pullback` | 1746 | 558 | 59 | 0.002084 | 0.5254 | 0.122953 |
| DIA/USD | 1h | `root_continuation` | 1746 | 437 | 75 | 0.001485 | 0.5733 | 0.111368 |
| DIA/USD | 1h | `sideways_range_reversion` | 1746 | 167 | 36 | 0.001247 | 0.6389 | 0.044901 |
| DIA/USD | 1h | `bear_crisis_relief` | 1746 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| DIA/USD | 1h | `compressed_break_continuation` | 1746 | 268 | 44 | 0.002216 | 0.5682 | 0.097510 |
| GLD/USD | 15m | `bull_transition_pullback` | 6487 | 1189 | 54 | 0.006196 | 0.5741 | 0.334579 |
| GLD/USD | 15m | `root_continuation` | 6487 | 1419 | 91 | 0.003667 | 0.5714 | 0.333671 |
| GLD/USD | 15m | `sideways_range_reversion` | 6487 | 715 | 84 | 0.004132 | 0.6310 | 0.347119 |
| GLD/USD | 15m | `bear_crisis_relief` | 6487 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 15m | `compressed_break_continuation` | 6487 | 828 | 66 | 0.003880 | 0.5758 | 0.256086 |
| GLD/USD | 1h | `bull_transition_pullback` | 1742 | 283 | 43 | 0.002610 | 0.5581 | 0.112249 |
| GLD/USD | 1h | `root_continuation` | 1742 | 390 | 66 | 0.005635 | 0.6212 | 0.371903 |
| GLD/USD | 1h | `sideways_range_reversion` | 1742 | 187 | 43 | 0.002407 | 0.5814 | 0.103484 |
| GLD/USD | 1h | `bear_crisis_relief` | 1742 | 0 | 0 | 0.000000 | 0.0000 | 0.000000 |
| GLD/USD | 1h | `compressed_break_continuation` | 1742 | 223 | 35 | 0.009570 | 0.6857 | 0.334938 |
| BTCY/USD | 1d | `bull_transition_pullback` | 351 | 54 | 34 | -0.006308 | 0.4118 | -0.214470 |
| BTCY/USD | 1d | `root_continuation` | 351 | 59 | 39 | -0.002743 | 0.3846 | -0.106989 |
| BTCY/USD | 1d | `sideways_range_reversion` | 351 | 23 | 17 | 0.000884 | 0.5882 | 0.015028 |
| BTCY/USD | 1d | `bear_crisis_relief` | 351 | 5 | 5 | 0.003021 | 0.4000 | 0.015106 |
| BTCY/USD | 1d | `compressed_break_continuation` | 351 | 56 | 26 | 0.006936 | 0.5769 | 0.180339 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `sideways_range_reversion` | 2748 | 9 | 50 | 1.0000 | 0.001149 | 0.143 | 7.7330 | 90.5479 | `pass` |
| Bear | `bear_crisis_relief` | 71 | 8 | 1 | 0.8750 | -0.007073 | 0.329 | -0.0268 | 24.2585 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `compressed_break_continuation` | 487 | 9 | 11 | 0.8889 | 0.001280 | 0.087 | 3.5508 | 90.7807 | `pass` |
| Crisis | `compressed_break_continuation` | 52 | 3 | 6 | 0.6667 | -0.001473 | 1.000 | 1.1271 | 45.7356 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_selected_rows_v1.csv`
- All variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_all_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/branch-rc-spa/root_transition_triad_panel_summary_v1.csv`
- ict-engine wire JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/ict-engine-fail-closed/root_transition_triad_real_trades_wire_v1.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T192018-codex-board-b-root-transition-triad-v1/checks/root_transition_triad_v1_assertions.out`

## Next

- B2R-repeat: keep RootTransitionTriad fail-closed; source direct Manipulation executable PnL and repair any listed root failures without relaxing RC-SPA.
