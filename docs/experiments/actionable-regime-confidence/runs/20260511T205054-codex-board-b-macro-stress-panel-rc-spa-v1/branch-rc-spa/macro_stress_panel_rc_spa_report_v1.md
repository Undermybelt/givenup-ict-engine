# Macro-Stress Panel RC-SPA v1

Run id: `20260511T205054+0800-codex-board-b-macro-stress-panel-rc-spa-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `75.5000`
- Variant rows: `2588`
- Selected rows: `1585`
- Branch paths passed: `0/5`
- Selected root counts: `{'Bear': 107, 'Bull': 1100, 'Crisis': 16, 'Manipulation(scoped)': 0, 'Sideways': 362}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_overfit_risk; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Boundary

- The macro-stress CSV is used as a daily price/feature panel only.
- The NIFTY files from the same live scout remain duplicate/blocked source-label material without an owner-approved MainRegimeV2 crosswalk.
- No raw Kaggle files were copied into the repo; this run writes derived RC-SPA evidence only.

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_on_momentum` | 1100 | 10 | 14 | 0.7000 | 0.001047 | 1.000 | 2.5357 | 75.5000 | `fail:reject_fold_inconsistency|reject_overfit_risk` |
| Bear | `defensive_long` | 107 | 10 | 4 | 0.6000 | -0.002026 | 0.500 | 0.9047 | 42.5711 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Sideways | `range_reversion` | 362 | 13 | 2 | 0.3077 | -0.003878 | 1.000 | -1.4294 | 19.6154 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_defensive_long` | 16 | 2 | 5 | 0.5000 | -0.001252 | 1.000 | 1.1126 | 38.2726 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Macro-stress panel CSV: `/tmp/ict-engine-public-source-intake-scout/macro/Global_Market_Stress_and_Liquidity_Regimes.csv`
- Base RC-SPA evaluator: `docs/experiments/actionable-regime-confidence/runs/20260511T193803-codex-board-b-root-transition-triad-clean-v1/scripts/board_b_root_transition_triad_clean_v1.py`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/branch-rc-spa/macro_stress_panel_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/branch-rc-spa/macro_stress_panel_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/branch-rc-spa/macro_stress_panel_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/branch-rc-spa/macro_stress_panel_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/branch-rc-spa/macro_stress_panel_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/ict-engine-fail-closed/macro_stress_panel_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205054-codex-board-b-macro-stress-panel-rc-spa-v1/checks/macro_stress_panel_rc_spa_v1_assertions.out`

## Next

- B2R-repeat: macro-stress panel is scored fail-closed; do not reuse NIFTY/macro as source labels without owner-approved crosswalk, and acquire tradeable scoped Manipulation rows before downstream promotion.
