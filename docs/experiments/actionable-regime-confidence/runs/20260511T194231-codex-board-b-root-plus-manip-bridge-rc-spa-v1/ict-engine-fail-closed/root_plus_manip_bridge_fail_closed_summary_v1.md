# Root plus Manipulation Bridge Fail-Closed Summary v1

Run ID: `20260511T194231+0800-codex-board-b-root-plus-manip-bridge-rc-spa-v1`

- Gate result: `fail:required_root_or_manipulation_branch_hard_gates_failed`
- Downstream consumption: `not_started:blocked_by_combined_branch_rc_spa_hard_gates`
- Pre-Bayes / BBN / CatBoost / execution-tree promotion was not started.
- Provider status readback: yfinance and TradingView MCP ready; kraken CLI ready; IBKR gateway reachable but runtime dependencies missing; crypto public provider Python deps missing.
- Pre-Bayes status: `gate=unavailable`, `policy=unavailable`, `soft_evidence=unavailable`.
- CatBoost/path-ranker status: `runtime_selection=disabled`, `runtime_matches=0`, `ready=false`.
- Workflow status: `no_workflow_state`.
- This is a fail-closed combined readback, not a promoted profitability packet.

Primary blocker: root=fail:required_root_branch_hard_gates_failed (Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60); manipulation=fail:direct_manipulation_intraday_pnl_bridge_not_accepted (reject_positive_underperforms_control;reject_bootstrap_diff_lcb_nonpositive;reject_fold_positive_rate_lt60pct)
