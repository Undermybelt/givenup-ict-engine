# Tomac NQ Root-Aware Variant Matrix B2U v1

Run id: `20260511T184420+0800-codex-board-b-tomac-nq-variant-matrix-b2u-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `66.0472`
- Selected trade rows: `2135`
- Variant matrix rows: `5109`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Selected root trade counts: `{'Bull': 431, 'Bear': 522, 'Sideways': 1119, 'Crisis': 63, 'Manipulation(scoped)': 0}`
- Matrix root trade counts: `{'Bull': 1232, 'Bear': 1187, 'Sideways': 2579, 'Crisis': 111, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: The NQ/Tomac root-aware variant matrix produced real Auto-Quant/Freqtrade rows and an estimable variant PBO proxy, but at least one required root branch still failed RC-SPA hard gates; no downstream Pre-Bayes/BBN/CatBoost/execution-tree promotion is allowed until all required root branches pass with direct rows.

## Auto-Quant / Freqtrade Variant Matrix

| Variant | Trades | Win rate % | Profit % | Sharpe | Log |
|---|---:|---:|---:|---:|---|
| `tomac_baseline_bull` | 431 | 48.724 | 35.460 | 0.2195 | `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/logs/freqtrade_backtest_tomac_baseline_bull.out` |
| `bull_cost_filtered` | 238 | 48.319 | 9.960 | 0.0718 | `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/logs/freqtrade_backtest_bull_cost_filtered.out` |
| `bear_sideways_reversion` | 1160 | 61.983 | -47.860 | -0.3748 | `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/logs/freqtrade_backtest_bear_sideways_reversion.out` |
| `crisis_dense_rebound` | 1231 | 62.632 | -54.940 | -0.4483 | `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/logs/freqtrade_backtest_crisis_dense_rebound.out` |
| `all_root_dense` | 2049 | 56.223 | -43.810 | -0.3893 | `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/logs/freqtrade_backtest_all_root_dense.out` |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `tomac_baseline_bull` | 431 | 13 | 8 | 0.8462 | 0.000375 | 0.017 | 2.9202 | 66.0472 | `fail:reject_fold_trade_depth|reject_cost_fragile` |
| Bear | `all_root_dense` | 522 | 7 | 18 | 0.1429 | -0.001362 | 0.743 | -1.8847 | 17.1429 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `all_root_dense` | 1119 | 9 | 4 | 0.2222 | -0.000711 | 0.302 | -2.4938 | 18.3333 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Crisis | `all_root_dense` | 63 | 3 | 5 | 0.6667 | -0.001279 | 1.000 | 0.3600 | 36.4364 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Manipulation(scoped) | `no_direct_event_rows` | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/branch-rc-spa/tomac_nq_variant_matrix_branch_rc_spa_report_v1.json`
- Selected trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/branch-rc-spa/tomac_nq_variant_matrix_selected_branch_trades_v1.csv`
- All variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/branch-rc-spa/tomac_nq_variant_matrix_all_variant_branch_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/branch-rc-spa/tomac_nq_variant_matrix_branch_rc_spa_summary_v1.csv`
- Variant summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/branch-rc-spa/tomac_nq_variant_matrix_variant_summary_v1.csv`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/strategy/TomacNQRootAwareVariantMatrixB2U.py`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T184420-codex-board-b-tomac-nq-variant-matrix-b2u-v1/checks/tomac_nq_variant_matrix_b2u_v1_assertions.out`

## Next

- B2R-repeat: inspect selected branch failures, then either add a real crisis/direct-event source panel for scoped Manipulation or synthesize another NQ/root-aware recipe that improves failing Bear/Sideways/Crisis depth without relaxing RC-SPA gates.
