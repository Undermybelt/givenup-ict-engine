# Root Plus Manipulation Bridge RC-SPA v1

Run id: `20260511T194231+0800-codex-board-b-root-plus-manip-bridge-rc-spa-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `76.2500`
- Selected rows: `14844`
- Variant / matrix rows: `65107`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root counts: `{'Bull': 6548, 'Bear': 2161, 'Sideways': 2896, 'Crisis': 28, 'Manipulation(scoped)': 3211}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_overfit_risk; Bear=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Selected Branch Summary

| Root | Trades | Folds | Min Fold Trades | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 6548 | 16 | 49 | 0.001953 | 0.312 | 5.6708 | 999.000000 | 76.2500 | `fail:reject_overfit_risk` |
| Bear | 2161 | 13 | 28 | -0.000329 | 0.615 | 1.2139 | 2.018508 | 44.2308 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | 2896 | 16 | 13 | -0.002568 | 0.625 | -3.8330 | 0.000000 | 16.8750 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 28 | 4 | 1 | -0.003988 | 0.200 | 0.6592 | 999.000000 | 39.5710 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Manipulation(scoped) | 3211 | 13 | 1 | -0.001004 | 1.000 | 0.6958 | -0.019742 | 30.0000 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Interpretation

- The direct scoped Manipulation branch now has executable provider-reconstructed intraday PnL rows instead of zero rows.
- The bridge is still not promotion-grade because positive event provider-open returns underperform same-coin controls and no combined five-root RC-SPA pass exists.
- Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree promotion remain stopped.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/root_plus_manip_bridge_rc_spa_report_v1.json`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/root_plus_manip_bridge_branch_summary_v1.csv`
- Combined rows: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/branch-rc-spa/root_plus_manip_bridge_rows_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T194231-codex-board-b-root-plus-manip-bridge-rc-spa-v1/checks/root_plus_manip_bridge_rc_spa_v1_assertions.out`

## Next

- B2R-repeat: Manipulation no longer has zero direct rows, but direct bridge underperforms controls and root branches still fail; switch or repair Bear/Sideways/Crisis without relaxing RC-SPA.
