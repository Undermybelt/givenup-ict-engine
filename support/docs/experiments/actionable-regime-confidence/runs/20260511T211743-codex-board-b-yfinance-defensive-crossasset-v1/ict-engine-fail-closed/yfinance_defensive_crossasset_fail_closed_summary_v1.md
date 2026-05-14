# YFinance Defensive Cross-Asset ict-engine Fail-Closed Summary v1

Run id: `20260511T211743+0800-codex-board-b-yfinance-defensive-crossasset-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required price-root branch hard gate passed.
- This is a fail-closed readback, not a promoted profitability packet.

Primary blocker: Bull=fail:reject_fold_trade_depth|reject_tail_risk; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_overfit_risk; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency
