# Root plus Manipulation Bridge RC-SPA v1

Run ID: `20260511T194231+0800-codex-board-b-root-plus-manip-bridge-rc-spa-v1`

## Decision

- Gate result: `fail:required_root_or_manipulation_branch_hard_gates_failed`
- Stable profit score proxy: `76.2500`
- Branch paths passed: `0/5`
- Root rows: `11633` selected / `61896` variant
- Direct Manipulation rows: `13535` positive / `7149` controls
- Direct Manipulation diff 6h: `-0.000872`
- Direct Manipulation diff LCB 5%: `-0.001630`
- Downstream consumption: `not_started:blocked_by_combined_branch_rc_spa_hard_gates`
- Primary blocker: root=fail:required_root_branch_hard_gates_failed (Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60); manipulation=fail:direct_manipulation_intraday_pnl_bridge_not_accepted (reject_positive_underperforms_control;reject_bootstrap_diff_lcb_nonpositive;reject_fold_positive_rate_lt60pct)

## Inputs

- Root report: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_rc_spa_report_v1.json`
- Manipulation report: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_v1.json`

## Next

- B2R-repeat: do not promote; direct Manipulation underperforms controls and RootTransitionTriad still has failed root branches. Source stronger direct PnL rows or switch to a different root-aware family/panel.
