# Stock Panel Root-Hedge RC-SPA v1

Run id: `20260511T203803+0800-codex-board-b-stock-panel-root-hedge-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `75.4500`
- Variant rows: `709`
- Selected rows: `346`
- Branch paths passed: `0/5`
- Selected root counts: `{'Bear': 3, 'Bull': 108, 'Crisis': 0, 'Manipulation(scoped)': 0, 'Sideways': 235}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_insufficient_test_folds|reject_cost_fragile|reject_overfit_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `gold_defensive_long` | 108 | 2 | 16 | 1.0000 | 0.000874 | 1.000 | 2.1065 | 72.6952 | `fail:reject_insufficient_test_folds|reject_cost_fragile|reject_overfit_risk` |
| Bear | `risk_on_momentum_fast` | 3 | 1 | 3 | 1.0000 | 0.024367 | 1.000 | 4.6533 | 75.4500 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | `sideways_range_reversion` | 235 | 4 | 6 | 0.5000 | -0.002193 | 1.000 | -0.1736 | 22.5000 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `risk_on_momentum_fast` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^GSPC`
- Panel: SPY, QQQ, IWM, DIA, GLD across 1h/4h plus SPY/QQQ/ES/AAPL daily where available.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/branch-rc-spa/stock_panel_root_hedge_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/branch-rc-spa/stock_panel_root_hedge_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/branch-rc-spa/stock_panel_root_hedge_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/branch-rc-spa/stock_panel_root_hedge_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/branch-rc-spa/stock_panel_root_hedge_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/ict-engine-fail-closed/stock_panel_root_hedge_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T203803-codex-board-b-stock-panel-root-hedge-v1/checks/stock_panel_root_hedge_v1_assertions.out`

## Next

- B2R-repeat: StockPanelRootHedgeV1 failed all required branch gates; use a broader crisis-bearing provider panel or source executable scoped Manipulation PnL rows before any downstream promotion.
