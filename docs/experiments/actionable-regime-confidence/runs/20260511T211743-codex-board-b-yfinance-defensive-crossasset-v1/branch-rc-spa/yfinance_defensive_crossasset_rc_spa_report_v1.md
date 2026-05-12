# YFinance Defensive Cross-Asset RC-SPA v1

Run id: `20260511T211743+0800-codex-board-b-yfinance-defensive-crossasset-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `81.2179`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `16125`
- Selected rows: `1164`
- Selected root counts: `{'Bull': 623, 'Bear': 203, 'Sideways': 301, 'Crisis': 37, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_trade_depth|reject_tail_risk; Bear=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60; Sideways=fail:reject_fold_trade_depth|reject_overfit_risk; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `risk_on_momentum_h20` | 623 | 15 | 8 | 0.8667 | 0.021930 | 0.250 | 5.9591 | 78.0000 | `fail:reject_fold_trade_depth|reject_tail_risk` |
| Bear | `defensive_rotation_long_h10` | 203 | 13 | 6 | 0.5385 | -0.002067 | 0.231 | 0.5714 | 37.4170 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Sideways | `low_vol_carry_h20` | 301 | 14 | 6 | 0.7857 | 0.006355 | 0.375 | 5.0647 | 79.6666 | `fail:reject_fold_trade_depth|reject_overfit_risk` |
| Crisis | `crisis_defensive_long_h5` | 37 | 3 | 4 | 0.6667 | 0.000902 | 0.000 | 1.7614 | 81.2179 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Inputs

- Cached yfinance daily close panel: `/private/tmp/ict-regime-hmm-markov-root/yfinance_cross_asset_daily_close.csv`
- Provider probe: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/provider/yfinance_defensive_crossasset_provider_probe_v1.json`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Scoped Manipulation component: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.md`

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/branch-rc-spa/yfinance_defensive_crossasset_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/branch-rc-spa/yfinance_defensive_crossasset_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/branch-rc-spa/yfinance_defensive_crossasset_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/branch-rc-spa/yfinance_defensive_crossasset_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/branch-rc-spa/yfinance_defensive_crossasset_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/ict-engine-fail-closed/yfinance_defensive_crossasset_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211743-codex-board-b-yfinance-defensive-crossasset-v1/checks/yfinance_defensive_crossasset_v1_assertions.out`

## Next

- B2R-repeat: keep 205047 Manipulation component, but choose a different Bull/Bear/Sideways/Crisis root family or provider panel; do not relax RC-SPA.
