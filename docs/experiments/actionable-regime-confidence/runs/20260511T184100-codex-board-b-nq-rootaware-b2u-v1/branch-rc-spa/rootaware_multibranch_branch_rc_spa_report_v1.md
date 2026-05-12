# NQRootAwareB2UV1 Branch RC-SPA v1

Run id: `20260511T184100+0800-codex-board-b-nq-rootaware-b2u-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `78.9516`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Required roots covered before RC-SPA: `True`
- Root trade counts: `{'Bull': 138, 'Bear': 21, 'Sideways': 40, 'Crisis': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: NQRootAwareB2UV1 emits root-first branches and real Auto-Quant/Freqtrade trade rows, but required root branches still fail RC-SPA hard gates; crisis support is structurally thin in the current Board A panel (36 dominant Crisis sessions in 2011-2025), so downstream runtime promotion remains blocked.

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 138 | 14 | 1 | 0.5714 | -0.002145 | 0.22 | 0.3789 | 33.8083 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | 21 | 11 | 1 | 0.8182 | 0.012718 | 0.51 | 3.2950 | 77.1947 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | 40 | 14 | 1 | 0.7143 | 0.003397 | 0.89 | 2.3954 | 78.9516 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_overfit_risk` |
| Crisis | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_report_v1.json`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/strategy/NQRootAwareB2UV1.py`
- Root schedule: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/strategy/board_a_root_schedule_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/branch-rc-spa/rootaware_multibranch_branch_path_trades_v1.csv`
- Variant branch rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/branch-rc-spa/rootaware_multibranch_variant_branch_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/branch-rc-spa/rootaware_multibranch_branch_rc_spa_summary_v1.csv`
- Timerange summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/branch-rc-spa/rootaware_multibranch_timerange_backtest_summaries_v1.csv`
- Backtest stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/checks/rootaware_multibranch_freqtrade_backtests.out`
- Backtest stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T184100-codex-board-b-nq-rootaware-b2u-v1/checks/rootaware_multibranch_freqtrade_backtests.err`

## Next

- B2R-repeat: either acquire a broader crisis-capable Board A root panel / market set, or synthesize a second root-aware recipe with enough Bear/Sideways/Crisis trade and fold depth before attempting downstream branch consumption.
