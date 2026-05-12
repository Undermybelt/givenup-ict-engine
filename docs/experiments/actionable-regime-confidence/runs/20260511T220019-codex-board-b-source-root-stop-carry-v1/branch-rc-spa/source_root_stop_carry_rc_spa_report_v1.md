# Source Root Stop Carry RC-SPA v1

Run id: `20260511T220019+0800-codex-board-b-source-root-stop-carry-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `78.7013`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `6839`
- Selected rows: `4083`
- Selected root counts: `{'Bull': 2388, 'Bear': 376, 'Sideways': 1271, 'Crisis': 48, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_carry_breakout` | 2388 | 16 | 31 | 0.6875 | -0.000064 | 1.000 | 1.4608 | 45.3125 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Bear | `bear_defensive_carry` | 376 | 12 | 6 | 0.4167 | -0.003201 | 0.800 | -0.6881 | 21.2500 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `sideways_stop_hunt_reversal` | 1271 | 16 | 1 | 0.3125 | -0.001491 | 1.000 | -1.3230 | 19.6875 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_defensive_carry` | 48 | 3 | 4 | 1.0000 | 0.006888 | 1.000 | 3.4966 | 78.7013 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- YFinance ETF cache: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache`
- Auto-Quant 4h panels: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^GSPC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/ict-engine-fail-closed/source_root_stop_carry_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/checks/source_root_stop_carry_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or provider panel; do not relax RC-SPA.
