# CrashRebound Branch RC-SPA v1

Run id: `20260511T180504+0800-codex-board-b-crashrebound-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `80.0000`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: CrashRebound has real trade rows and root-first branch paths, but no branch path passes RC-SPA because branch-level trade depth/fold depth and single-recipe PBO hard gates fail; downstream runtime promotion remains blocked.

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 145 | 5 | 15 | 1.0000 | 0.005011 | 1.00 | 2.8707 | 80.0000 | `fail:reject_overfit_risk` |
| Bear | 34 | 4 | 1 | 0.7500 | -0.015265 | 1.00 | 0.5042 | 23.9130 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 28 | 4 | 2 | 0.5000 | -0.028460 | 1.00 | -0.9385 | 11.7000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_report_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_path_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_branch_rc_spa_summary_v1.csv`
- Timerange summary: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/branch-rc-spa/crashrebound_timerange_backtest_summaries_v1.csv`
- Backtest stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/checks/crashrebound_freqtrade_backtests.out`
- Backtest stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T180504-codex-board-b-crashrebound-branch-rc-spa-v1/checks/crashrebound_freqtrade_backtests.err`

## Next

- B3-repeat: source more branch-path trade rows from provider-backed Auto-Quant runs or choose a denser recipe before attempting Pre-Bayes -> BBN -> CatBoost -> execution-tree branch consumption.
