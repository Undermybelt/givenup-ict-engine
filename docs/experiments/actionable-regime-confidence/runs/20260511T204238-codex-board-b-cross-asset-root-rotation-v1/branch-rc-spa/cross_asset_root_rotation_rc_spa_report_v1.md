# Cross-Asset Root Rotation RC-SPA v1

Run id: `20260511T204238+0800-codex-board-b-cross-asset-root-rotation-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `73.3023`
- Variant rows: `12593`
- Selected rows: `6076`
- Branch paths passed: `0/5`
- Selected root counts: `{'Bear': 1137, 'Bull': 4874, 'Crisis': 35, 'Manipulation(scoped)': 0, 'Sideways': 30}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60; Sideways=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_overfit_risk; Crisis=fail:reject_thin_trades|reject_fold_trade_depth|reject_overfit_risk; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_on_momentum_fast` | 4874 | 16 | 56 | 0.6250 | 0.001096 | 1.000 | 3.7279 | 64.3750 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk` |
| Bear | `risk_off_short` | 1137 | 13 | 9 | 0.6923 | -0.000675 | 1.000 | 1.2462 | 45.3846 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `defensive_rotation` | 30 | 2 | 9 | 0.5000 | 0.001148 | 1.000 | 1.9311 | 70.3611 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_overfit_risk` |
| Crisis | `panic_reversal` | 35 | 4 | 1 | 0.7500 | 0.001509 | 1.000 | 1.8232 | 73.3023 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_overfit_risk` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Base RC-SPA evaluator: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/board_b_root_transition_triad_clean_v1.py`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/branch-rc-spa/cross_asset_root_rotation_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/branch-rc-spa/cross_asset_root_rotation_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/branch-rc-spa/cross_asset_root_rotation_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/branch-rc-spa/cross_asset_root_rotation_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/branch-rc-spa/cross_asset_root_rotation_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/ict-engine-fail-closed/cross_asset_root_rotation_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T204238-codex-board-b-cross-asset-root-rotation-v1/checks/cross_asset_root_rotation_v1_assertions.out`

## Next

- B2R-repeat: cross-asset root rotation did not clear required branch hard gates; switch family/panel or source executable Manipulation rows before downstream promotion.
