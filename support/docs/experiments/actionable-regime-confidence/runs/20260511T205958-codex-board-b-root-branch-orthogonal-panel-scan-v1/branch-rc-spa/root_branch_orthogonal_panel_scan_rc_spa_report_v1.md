# Root Branch Orthogonal Panel Scan RC-SPA v1

Run id: `20260511T205958+0800-codex-board-b-root-branch-orthogonal-panel-scan-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `75.7386`
- Variant rows: `57940`
- Selected rows: `8070`
- Branch paths passed: `0/5`
- Selected root counts: `{'Bear': 7, 'Bull': 7456, 'Crisis': 598, 'Manipulation(scoped)': 0, 'Sideways': 9}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Sideways=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Crisis=fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60; Manipulation(scoped)=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60

## Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `bull_crypto_carry` | 7456 | 6 | 116 | 0.3333 | -0.000037 | 0.333 | 1.6508 | 40.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Bear | `bear_defensive_long` | 7 | 3 | 1 | 1.0000 | 0.003137 | 1.000 | 2.0332 | 75.7386 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Sideways | `sideways_breakout_failure` | 9 | 2 | 3 | 0.5000 | -0.010213 | 1.000 | 0.0670 | 22.3415 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Crisis | `crisis_tail_short` | 598 | 3 | 101 | 0.6667 | -0.001307 | 1.000 | 0.4667 | 37.0008 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Inputs

- Local Auto-Quant feathers: `/Users/thrill3r/Auto-Quant/user_data/data`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source root schedule: `/Users/thrill3r/Downloads/stock-market-regimes-20002026/stock_market_regimes_2000_2026.csv` / `^IXIC`
- Panel: multi-asset local Auto-Quant feathers across NQ, equity ETFs, crypto, GLD, EUR, ES, AAPL, and BTCY where available.
- Scoped Manipulation component: existing `20260511T205047` stop/take-profit grid pass; not consumed downstream by this root-only scan.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_branch_summary_v1.csv`
- Panel summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/branch-rc-spa/root_branch_orthogonal_panel_scan_panel_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/ict-engine-fail-closed/root_branch_orthogonal_panel_scan_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205958-codex-board-b-root-branch-orthogonal-panel-scan-v1/checks/root_branch_orthogonal_panel_scan_v1_assertions.out`

## Next

- Keep Board B in research_watch/fail-closed: this root-only scan did not produce passing Bull/Bear/Sideways/Crisis roots under unchanged RC-SPA, so do not combine it with the 205047 Manipulation component for downstream promotion.
