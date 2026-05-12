# Stock Panel Root-Hedge ict-engine Fail-Closed Summary v1

Run id: `20260511T203803+0800-codex-board-b-stock-panel-root-hedge-v1`.

- Branch RC-SPA gate: `fail:required_root_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Pre-Bayes / BBN / CatBoost / execution-tree were not started unless every required branch hard gate passed.
- This is a fail-closed readback, not a promoted profitability packet.
- Provider readback: yfinance ready; TradingView MCP ready_degraded; Kraken CLI ready; IBKR gateway reachable but Rust runtime dependencies unhealthy; kraken_public unhealthy due missing Python provider dependencies.
- ict-engine readback: `pre-bayes-status` exited 0 with empty latest state; `policy-training-status` reported structural path-ranking export missing/disabled before export; `workflow-status --phase execution-candidate` wrote `no workflow phase snapshots available`; `export-structural-path-ranking-target` emitted one unobserved bootstrap row with `mature_rows=0` and no raw/calibrated path scores.

Primary blocker: Bull=fail:reject_insufficient_test_folds|reject_cost_fragile|reject_overfit_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60
