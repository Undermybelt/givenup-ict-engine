# PerPairMR Branch RC-SPA v1

Run id: `20260511T182219+0800-codex-board-b-perpairmr-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `53.0927`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: PerPairMR has real trade rows and root-first branch paths, but downstream runtime promotion remains blocked unless at least one branch path passes all RC-SPA hard gates, including fail-closed PBO for the selected recipe.

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 420 | 5 | 21 | 0.8000 | 0.001523 | 1.00 | 2.4680 | 53.0927 | `fail:reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Bear | 53 | 5 | 4 | 0.0000 | -0.015057 | 1.00 | -1.0586 | 7.9500 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 46 | 5 | 1 | 0.6000 | -0.011841 | 1.00 | -0.0353 | 15.9000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/branch-rc-spa/perpairmr_branch_rc_spa_report_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/branch-rc-spa/perpairmr_branch_path_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/branch-rc-spa/perpairmr_branch_rc_spa_summary_v1.csv`
- Timerange summary: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/branch-rc-spa/perpairmr_timerange_backtest_summaries_v1.csv`
- Backtest stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/checks/perpairmr_freqtrade_backtests.out`
- Backtest stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T182219-codex-board-b-perpairmr-branch-rc-spa-v1/checks/perpairmr_freqtrade_backtests.err`

## Next

- B3-repeat: if PerPairMR fails, synthesize a parameter/candidate matrix for the strongest root branch or choose a denser branch-specific recipe before attempting Pre-Bayes -> BBN -> CatBoost -> execution-tree branch consumption.
