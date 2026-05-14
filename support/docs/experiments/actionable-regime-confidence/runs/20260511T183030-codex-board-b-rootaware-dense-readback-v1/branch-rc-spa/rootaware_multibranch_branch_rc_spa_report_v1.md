# RootAwareDenseReadbackV1 Branch RC-SPA v1

Run id: `20260511T183030+0800-codex-board-b-rootaware-dense-readback-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `34.8283`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Required roots covered before RC-SPA: `True`
- Root trade counts: `{'Bull': 2550, 'Bear': 1420, 'Sideways': 1134, 'Crisis': 94}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: RootAwareDenseReadbackV1 emits root-first branches and real Auto-Quant/Freqtrade trade rows, but required root branches still fail RC-SPA hard gates; crisis support is structurally thin in the current Board A panel (8 dominant Crisis sessions in 2021-2025), so downstream runtime promotion remains blocked.

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 2550 | 5 | 197 | 0.2000 | -0.001613 | 0.00 | -1.7632 | 28.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | 1420 | 5 | 38 | 0.0000 | -0.005224 | 0.00 | -5.6714 | 25.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 1134 | 5 | 62 | 0.0000 | -0.006012 | 0.00 | -5.9527 | 25.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 94 | 1 | 94 | 1.0000 | -0.003228 | 1.00 | 0.0486 | 34.8283 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.json`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/strategy/RootAwareDenseReadbackV1.py`
- Root schedule: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/strategy/board_a_root_schedule_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_branch_path_trades_v1.csv`
- Variant branch rows: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_variant_branch_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_summary_v1.csv`
- Timerange summary: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/branch-rc-spa/rootaware_multibranch_timerange_backtest_summaries_v1.csv`
- Backtest stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/checks/rootaware_multibranch_freqtrade_backtests.out`
- Backtest stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T183030-codex-board-b-rootaware-dense-readback-v1/checks/rootaware_multibranch_freqtrade_backtests.err`

## Next

- B2R-repeat: either acquire a broader crisis-capable Board A root panel / market set, or synthesize a second root-aware recipe with enough Bear/Sideways/Crisis trade and fold depth before attempting downstream branch consumption.
