# VRP V2.5 ict-engine Fail-Closed Summary v1

Run id: `20260511T190356+0800-codex-board-b-vrp-v25-root-branch-rc-spa-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Pre-Bayes / BBN / CatBoost / execution-tree were not started because required branch hard gates did not all pass.
- This is a fail-closed readback, not a promoted profitability packet.
- Selected-row ict-engine wire dry-run: `1184/1184` parsed, `trades_invalid=0`.
- Pre-Bayes readback: `gate=unavailable`; structural path-ranker target export missing; workflow status `no_workflow_state`.

Primary blocker: Bull=fail:reject_cost_fragile; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Sideways=fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60
