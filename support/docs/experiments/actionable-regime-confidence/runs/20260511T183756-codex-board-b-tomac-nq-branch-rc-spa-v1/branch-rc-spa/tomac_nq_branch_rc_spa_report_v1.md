# Tomac NQ Branch RC-SPA v1

Run id: `20260511T183756+0800-codex-board-b-tomac-nq-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `76.0000`
- Total trade rows: `450`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 355, 'Bear': 15, 'Sideways': 68, 'Crisis': 12, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: TomacNQ_KillzoneBreakout proves the synthetic NQ/USD Auto-Quant path can add a broader 2011-2025 crisis-capable panel, but this existing single recipe has no variant/PBO matrix and does not pass all branch hard gates.

## Auto-Quant / Freqtrade Readback

| Segment | Timerange | Trades | Win rate % | Profit % | Sharpe | Log |
|---|---|---:|---:|---:|---:|---|
| `full_2011_2025` | `20110101-20251231` | 450 | 52.222 | 19.540 | 0.0839 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_full_2011_2025.out` |
| `fold_2011_2014` | `20110101-20141231` | 138 | 47.101 | 0.960 | 0.0171 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_fold_2011_2014.out` |
| `fold_2015_2018` | `20150101-20181231` | 136 | 45.588 | 11.760 | 0.2234 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_fold_2015_2018.out` |
| `fold_2019_2021` | `20190101-20211231` | 102 | 62.745 | 10.900 | 0.2702 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_fold_2019_2021.out` |
| `fold_2022_2023` | `20220101-20231231` | 9 | 44.444 | -5.810 | -0.1410 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_fold_2022_2023.out` |
| `fold_2024_2025` | `20240101-20251231` | 0 | 0.000 | 0.000 | 0.0000 | `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/logs/freqtrade_backtest_fold_2024_2025.out` |

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 355 | 5 | 71 | 0.8000 | 0.000062 | 1.00 | 1.7239 | 76.0000 | `fail:reject_cost_fragile|reject_pbo_not_estimated_single_existing_recipe` |
| Bear | 15 | 5 | 3 | 0.0000 | -0.013118 | 1.00 | -2.8507 | 13.0000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_pbo_not_estimated_single_existing_recipe|reject_dsr_nonpositive|reject_rc_spa_below_60` |
| Sideways | 68 | 5 | 13 | 0.6000 | -0.000548 | 1.00 | 1.1057 | 45.6000 | `fail:reject_thin_trades|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_pbo_not_estimated_single_existing_recipe|reject_rc_spa_below_60` |
| Crisis | 12 | 5 | 2 | 0.4000 | -0.006751 | 1.00 | -0.4371 | 20.4000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_pbo_not_estimated_single_existing_recipe|reject_dsr_nonpositive|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_pbo_not_estimated_single_existing_recipe|reject_dsr_nonpositive|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/branch-rc-spa/tomac_nq_branch_rc_spa_report_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/branch-rc-spa/tomac_nq_branch_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/branch-rc-spa/tomac_nq_branch_rc_spa_summary_v1.csv`
- Timerange summary: `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/branch-rc-spa/tomac_nq_timerange_summaries_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T183756-codex-board-b-tomac-nq-branch-rc-spa-v1/checks/tomac_nq_branch_rc_spa_v1_assertions.out`

## Next

- B2R-repeat: synthesize a root-aware NQ variant matrix from this Tomac path, or extend the source panel so Crisis and scoped Manipulation have enough direct rows.
