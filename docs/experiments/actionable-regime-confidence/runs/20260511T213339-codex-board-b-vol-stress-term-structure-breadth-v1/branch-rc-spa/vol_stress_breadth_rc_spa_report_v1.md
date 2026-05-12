# Vol Stress Term-Structure Breadth RC-SPA v1

Run id: `20260511T213339+0800-codex-board-b-vol-stress-term-structure-breadth-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `79.4353`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `7955`
- Selected rows: `3419`
- Selected root counts: `{'Bull': 1923, 'Bear': 12, 'Sideways': 1431, 'Crisis': 53, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60; Bear=fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_defense_spread_continuation` | 1923 | 16 | 8 | 0.6250 | 0.000418 | 0.154 | 2.5208 | 56.5752 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60` |
| Bear | `vol_expansion_failed_reclaim_short` | 12 | 4 | 1 | 0.2500 | -0.008038 | 1.000 | 0.5853 | 26.7328 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Sideways | `low_vol_band_reversion` | 1431 | 16 | 5 | 0.3125 | -0.002097 | 1.000 | -3.5273 | 19.6875 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `crisis_tail_hedge_breakout` | 53 | 3 | 4 | 1.0000 | 0.008793 | 1.000 | 4.0061 | 79.4353 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- YFinance daily ETF cache: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^GSPC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/vol_stress_breadth_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/vol_stress_breadth_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/vol_stress_breadth_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/vol_stress_breadth_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/branch-rc-spa/vol_stress_breadth_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/ict-engine-fail-closed/vol_stress_breadth_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213339-codex-board-b-vol-stress-term-structure-breadth-v1/checks/vol_stress_breadth_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but repair Bull/Bear/Sideways/Crisis with a different root family or provider panel; do not relax RC-SPA.
