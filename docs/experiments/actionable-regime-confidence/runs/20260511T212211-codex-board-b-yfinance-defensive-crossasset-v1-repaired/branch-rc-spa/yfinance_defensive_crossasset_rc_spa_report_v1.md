# YFinance Defensive Cross-Asset RC-SPA v1 Repaired

Run id: `20260511T212211+0800-codex-board-b-yfinance-defensive-crossasset-v1-repaired`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `77.3886`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `8763`
- Selected rows: `2787`
- Selected root counts: `{'Bull': 1712, 'Bear': 200, 'Sideways': 856, 'Crisis': 19, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_trade_depth|reject_fold_inconsistency; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_on_momentum_20d` | 1712 | 16 | 6 | 0.6250 | 0.001819 | 0.200 | 4.0772 | 76.3750 | `fail:reject_fold_trade_depth|reject_fold_inconsistency` |
| Bear | `defensive_duration` | 200 | 12 | 5 | 0.6667 | -0.001457 | 0.125 | 0.5236 | 45.0967 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Sideways | `low_vol_carry` | 856 | 16 | 1 | 0.6875 | 0.000046 | 1.000 | 1.7998 | 46.2274 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Crisis | `crisis_defensive_duration` | 19 | 2 | 9 | 1.0000 | 0.002137 | 1.000 | 1.9664 | 77.3886 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- YFinance cache: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider-cache`
- Provider status: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/provider/yfinance_defensive_crossasset_provider_status.csv`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^GSPC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/yfinance_defensive_crossasset_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/yfinance_defensive_crossasset_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/yfinance_defensive_crossasset_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/yfinance_defensive_crossasset_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/branch-rc-spa/yfinance_defensive_crossasset_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/ict-engine-fail-closed/yfinance_defensive_crossasset_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212211-codex-board-b-yfinance-defensive-crossasset-v1-repaired/checks/yfinance_defensive_crossasset_v1_assertions.out`

## Next

- B2R-repeat: keep the 205047 scoped Manipulation component, but find a price-root family where Bull/Bear/Sideways/Crisis all pass unchanged RC-SPA before downstream promotion.
