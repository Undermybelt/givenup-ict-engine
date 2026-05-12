# Root Plus Manipulation Bridge RC-SPA v1

Run ID: `20260511T194231+0800-codex-board-b-root-plus-manip-bridge-rc-spa-v1`

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `76.2500`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Manipulation bridge gate: `fail:direct_manipulation_intraday_pnl_bridge_not_accepted`
- Manipulation positive/control rows: `13535` / `7149`

## Branch Failures

- `Bull`: `fail:reject_overfit_risk`
- `Bear`: `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60`
- `Sideways`: `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60`
- `Crisis`: `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60`
- `Manipulation(scoped)`: `fail:reject_positive_underperforms_control|reject_bootstrap_diff_lcb_nonpositive|reject_fold_positive_rate_lt60pct|reject_no_positive_edge`

## Why Downstream Is Not Started

- The clean root scorer still has no required branch pass.
- The direct Manipulation bridge provides executable intraday rows, but its own gate is not accepted against controls.
- The branch path is preserved in artifacts, but RC-SPA hard gates block Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree promotion.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/root-plus-manip-bridge-rc-spa/root_plus_manip_bridge_rc_spa_v1.json`
- Combined branch CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/root-plus-manip-bridge-rc-spa/root_plus_manip_bridge_branch_summary_v1.csv`
- Root report: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/branch-rc-spa/root_transition_triad_rc_spa_report_v1.json`
- Manipulation report: `docs/experiments/actionable-regime-confidence/runs/20260511T194035-codex-board-b-mehrnoom-binance-intraday-pnl-v1/mehrnoom-binance-intraday-pnl/mehrnoom_binance_intraday_pnl_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/checks/root_plus_manip_bridge_rc_spa_v1_assertions.out`

## Next

- Do not start Pre-Bayes/BBN/CatBoost/execution-tree promotion. Direct Manipulation has executable intraday rows but fails edge/control gates; Bear, Sideways, and Crisis still require a different root-aware family or panel.
