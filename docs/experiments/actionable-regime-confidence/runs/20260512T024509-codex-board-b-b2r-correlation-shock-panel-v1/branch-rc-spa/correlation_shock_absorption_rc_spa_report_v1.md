# Correlation Shock Absorption RC-SPA v1

Run id: `20260512T024509+0800-codex-board-b-b2r-correlation-shock-panel-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `75.8886`
- Variant trade rows: `47,843`
- Selected trade rows: `13,275`
- Required branch paths passed: `0/5`
- Downstream: `not_started:blocked_by_branch_rc_spa_hard_gates`

## Selected Root Counts

| Root | Selected Rows | Gate |
|---|---:|---|
| Bull | 6,563 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Bear | 8 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | 6,280 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | 424 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Provider Context

- Provider status summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance: ready.
- Kraken CLI: ready.
- IBKR: runtime dependencies unhealthy, gateway reachable.
- TradingViewRemix MCP: connectivity probe failed.

## Artifacts

- Canonical readback: `docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/checks/correlation_shock_absorption_canonical_readback_v3.json`
- Completion check: `docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/checks/correlation_shock_absorption_completion_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/branch-rc-spa/correlation_shock_absorption_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/branch-rc-spa/correlation_shock_absorption_variant_rows_v1.csv`
- Provider status: `docs/experiments/actionable-regime-confidence/runs/20260512T024509-codex-board-b-b2r-correlation-shock-panel-v1/command-output/00_provider_status.out`

## Next

Keep fail-closed and do not run Pre-Bayes/BBN/CatBoost/execution-tree for this candidate. Use the packet as nursery feedback: the next production-gate repeat must repair Bear thinness, Sideways negative edge/specificity, Crisis fold/edge weakness, and direct Manipulation zero rows before ordered downstream consumption.
