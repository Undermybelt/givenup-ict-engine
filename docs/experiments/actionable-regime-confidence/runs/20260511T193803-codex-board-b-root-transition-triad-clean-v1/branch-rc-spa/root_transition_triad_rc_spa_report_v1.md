# Root Transition Triad RC-SPA v1

Run id: `20260511T193803+0800-codex-board-b-root-transition-triad-clean-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `76.2500`
- Variant rows: `61896`
- Selected rows: `11633`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root counts: `{'Bull': 6548, 'Bear': 2161, 'Sideways': 2896, 'Crisis': 28, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Panel / Variant Summary

| Market | TF | Variant | Trades | Mean | Win Rate | Net R |
|---|---:|---|---:|---:|---:|---:|
| NQ/USD | 1h | `trend_follow_fast` | 6903 | -0.000484 | 0.4520 | -3.343476 |
| NQ/USD | 1h | `trend_follow_slow` | 3923 | -0.000209 | 0.4978 | -0.818004 |
| NQ/USD | 1h | `range_reversion_dense` | 3788 | -0.000758 | 0.4316 | -2.870965 |
| NQ/USD | 1h | `tail_breakdown_short` | 6016 | -0.000245 | 0.4752 | -1.473902 |
| NQ/USD | 1h | `defensive_rotation` | 5216 | -0.000220 | 0.4781 | -1.146701 |
| NQ/USD | 4h | `trend_follow_fast` | 2587 | -0.000144 | 0.4986 | -0.372080 |
| NQ/USD | 4h | `trend_follow_slow` | 1885 | -0.000200 | 0.5125 | -0.376841 |
| NQ/USD | 4h | `range_reversion_dense` | 1378 | -0.000493 | 0.4884 | -0.679114 |
| NQ/USD | 4h | `tail_breakdown_short` | 2368 | -0.000257 | 0.5051 | -0.608011 |
| NQ/USD | 4h | `defensive_rotation` | 2369 | -0.000254 | 0.5082 | -0.602231 |
| NQ/USD | 1d | `trend_follow_fast` | 606 | 0.001766 | 0.5578 | 1.069948 |
| NQ/USD | 1d | `trend_follow_slow` | 373 | 0.002319 | 0.5845 | 0.864838 |
| NQ/USD | 1d | `range_reversion_dense` | 295 | 0.000244 | 0.5051 | 0.072062 |
| NQ/USD | 1d | `tail_breakdown_short` | 529 | 0.001892 | 0.5747 | 1.000750 |
| NQ/USD | 1d | `defensive_rotation` | 438 | 0.001985 | 0.5502 | 0.869623 |
| BTC/USDT | 4h | `trend_follow_fast` | 1002 | -0.000344 | 0.4481 | -0.344330 |
| BTC/USDT | 4h | `trend_follow_slow` | 708 | -0.001359 | 0.4675 | -0.961917 |
| BTC/USDT | 4h | `range_reversion_dense` | 500 | -0.002585 | 0.4560 | -1.292431 |
| BTC/USDT | 4h | `tail_breakdown_short` | 942 | -0.001208 | 0.4299 | -1.137478 |
| BTC/USDT | 4h | `defensive_rotation` | 928 | -0.001871 | 0.4353 | -1.735900 |
| BTC/USDT | 1d | `trend_follow_fast` | 192 | 0.001564 | 0.4479 | 0.300313 |
| BTC/USDT | 1d | `trend_follow_slow` | 118 | 0.009419 | 0.5424 | 1.111390 |
| BTC/USDT | 1d | `range_reversion_dense` | 100 | -0.005009 | 0.4700 | -0.500888 |
| BTC/USDT | 1d | `tail_breakdown_short` | 176 | 0.001453 | 0.4489 | 0.255773 |
| BTC/USDT | 1d | `defensive_rotation` | 145 | 0.004234 | 0.4966 | 0.613901 |
| ETH/USDT | 4h | `trend_follow_fast` | 1013 | -0.000684 | 0.4798 | -0.692581 |
| ETH/USDT | 4h | `trend_follow_slow` | 726 | -0.000294 | 0.4573 | -0.213766 |
| ETH/USDT | 4h | `range_reversion_dense` | 525 | -0.003259 | 0.4743 | -1.711232 |
| ETH/USDT | 4h | `tail_breakdown_short` | 933 | -0.000504 | 0.4770 | -0.470145 |
| ETH/USDT | 4h | `defensive_rotation` | 911 | -0.000346 | 0.4863 | -0.315510 |
| ETH/USDT | 1d | `trend_follow_fast` | 196 | 0.005130 | 0.5000 | 1.005574 |
| ETH/USDT | 1d | `trend_follow_slow` | 118 | 0.017529 | 0.5339 | 2.068460 |
| ETH/USDT | 1d | `range_reversion_dense` | 98 | -0.007063 | 0.4796 | -0.692192 |
| ETH/USDT | 1d | `tail_breakdown_short` | 173 | 0.017788 | 0.5723 | 3.077239 |
| ETH/USDT | 1d | `defensive_rotation` | 148 | 0.022193 | 0.5676 | 3.284550 |
| BNB/USDT | 4h | `trend_follow_fast` | 1038 | 0.002207 | 0.4778 | 2.290662 |
| BNB/USDT | 4h | `trend_follow_slow` | 730 | 0.003020 | 0.4822 | 2.204891 |
| BNB/USDT | 4h | `range_reversion_dense` | 506 | -0.000673 | 0.5079 | -0.340449 |
| BNB/USDT | 4h | `tail_breakdown_short` | 965 | 0.000985 | 0.4674 | 0.950888 |
| BNB/USDT | 4h | `defensive_rotation` | 946 | 0.001180 | 0.4810 | 1.116750 |
| SOL/USDT | 4h | `trend_follow_fast` | 989 | 0.004510 | 0.5116 | 4.460007 |
| SOL/USDT | 4h | `trend_follow_slow` | 706 | 0.006111 | 0.5127 | 4.314119 |
| SOL/USDT | 4h | `range_reversion_dense` | 524 | -0.001432 | 0.4733 | -0.750586 |
| SOL/USDT | 4h | `tail_breakdown_short` | 896 | 0.004706 | 0.5067 | 4.216201 |
| SOL/USDT | 4h | `defensive_rotation` | 903 | 0.003749 | 0.4828 | 3.385169 |
| AVAX/USDT | 4h | `trend_follow_fast` | 961 | 0.004170 | 0.4776 | 4.006938 |
| AVAX/USDT | 4h | `trend_follow_slow` | 674 | 0.004549 | 0.4896 | 3.066344 |
| AVAX/USDT | 4h | `range_reversion_dense` | 522 | -0.004685 | 0.4598 | -2.445590 |
| AVAX/USDT | 4h | `tail_breakdown_short` | 881 | 0.001995 | 0.4835 | 1.757752 |
| AVAX/USDT | 4h | `defensive_rotation` | 871 | 0.003534 | 0.4948 | 3.077999 |
| SPY/USD | 1d | `trend_follow_fast` | 100 | 0.001189 | 0.5500 | 0.118862 |
| SPY/USD | 1d | `trend_follow_slow` | 62 | 0.001464 | 0.5484 | 0.090737 |
| SPY/USD | 1d | `range_reversion_dense` | 43 | 0.000335 | 0.5349 | 0.014414 |
| SPY/USD | 1d | `tail_breakdown_short` | 91 | 0.001415 | 0.5495 | 0.128805 |
| SPY/USD | 1d | `defensive_rotation` | 74 | 0.004885 | 0.5946 | 0.361527 |
| ES/USD | 1d | `trend_follow_fast` | 100 | 0.000520 | 0.6000 | 0.052006 |
| ES/USD | 1d | `trend_follow_slow` | 62 | 0.006127 | 0.6452 | 0.379859 |
| ES/USD | 1d | `range_reversion_dense` | 39 | 0.001255 | 0.5128 | 0.048948 |
| ES/USD | 1d | `tail_breakdown_short` | 90 | 0.002522 | 0.5667 | 0.226962 |
| ES/USD | 1d | `defensive_rotation` | 73 | 0.004882 | 0.5753 | 0.356375 |
| AAPL/USD | 1d | `trend_follow_fast` | 88 | 0.003664 | 0.5114 | 0.322453 |
| AAPL/USD | 1d | `trend_follow_slow` | 53 | 0.003545 | 0.6226 | 0.187885 |
| AAPL/USD | 1d | `range_reversion_dense` | 35 | -0.000609 | 0.4286 | -0.021308 |
| AAPL/USD | 1d | `tail_breakdown_short` | 74 | 0.004478 | 0.5135 | 0.331348 |
| AAPL/USD | 1d | `defensive_rotation` | 62 | 0.003271 | 0.5645 | 0.202801 |
| GLD/USD | 1h | `trend_follow_fast` | 93 | 0.001154 | 0.4946 | 0.107281 |
| GLD/USD | 1h | `trend_follow_slow` | 50 | 0.005790 | 0.5600 | 0.289511 |
| GLD/USD | 1h | `range_reversion_dense` | 43 | 0.000595 | 0.6047 | 0.025588 |
| GLD/USD | 1h | `tail_breakdown_short` | 81 | 0.002467 | 0.5556 | 0.199825 |
| GLD/USD | 1h | `defensive_rotation` | 10 | -0.000165 | 0.3000 | -0.001654 |
| GLD/USD | 4h | `trend_follow_fast` | 43 | 0.003347 | 0.6279 | 0.143909 |
| GLD/USD | 4h | `trend_follow_slow` | 33 | 0.009341 | 0.6364 | 0.308255 |
| GLD/USD | 4h | `range_reversion_dense` | 18 | -0.004185 | 0.3889 | -0.075330 |
| GLD/USD | 4h | `tail_breakdown_short` | 38 | 0.006928 | 0.6316 | 0.263252 |
| GLD/USD | 4h | `defensive_rotation` | 3 | -0.007762 | 0.3333 | -0.023285 |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `trend_follow_slow` | 6548 | 16 | 49 | 0.7500 | 0.001953 | 0.312 | 5.6708 | 76.2500 | `fail:reject_overfit_risk` |
| Bear | `tail_breakdown_short` | 2161 | 13 | 28 | 0.6154 | -0.000329 | 0.615 | 1.2139 | 44.2308 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `trend_follow_fast` | 2896 | 16 | 13 | 0.1250 | -0.002568 | 0.625 | -3.8330 | 16.8750 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `range_reversion_dense` | 28 | 4 | 1 | 0.7500 | -0.003988 | 0.200 | 0.6592 | 39.5710 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/ict-engine-fail-closed/root_transition_triad_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/checks/root_transition_triad_v1_assertions.out`

## Next

- B2R-repeat: keep RootTransitionTriad as fail-closed evidence; direct Manipulation still needs trade/PnL rows, and failed roots need a different family or provider panel without relaxing RC-SPA.
