# Cross-Run Root Ensemble ict-engine Fail-Closed Summary v1

Run id: `20260511T215453+0800-codex-board-b-cross-run-root-ensemble-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.
- The 205047 scoped Manipulation component is recorded as a component pass only, not an aggregate promotion.
- This is fail-closed unless all four price roots and scoped Manipulation pass together.

Primary blocker: Bull=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk
