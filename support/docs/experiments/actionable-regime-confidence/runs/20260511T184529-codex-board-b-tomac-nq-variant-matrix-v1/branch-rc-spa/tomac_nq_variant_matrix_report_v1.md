# Tomac NQ Root-Aware Variant Matrix v1

Run id: `20260511T184529+0800-codex-board-b-tomac-nq-variant-matrix-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `60.0389`
- Variant trade rows: `5397`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 3949, 'Bear': 329, 'Sideways': 985, 'Crisis': 134, 'Manipulation(scoped)': 0}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Tomac NQ variant matrix ran real Auto-Quant/Freqtrade variants and estimated PBO, but no root branch passed RC-SPA hard gates; downstream promotion remains blocked.

## Auto-Quant / Freqtrade Variant Readback

| Variant | Strategy | Trades | Win rate % | Profit % | Sharpe | PF | Log |
|---|---|---:|---:|---:|---:|---:|---|
| `baseline` | `TomacNQVariantBaseline` | 450 | 52.222 | 19.540 | 0.0839 | 1.138 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_baseline.out` |
| `tight_trail` | `TomacNQVariantTightTrail` | 549 | 59.016 | 0.590 | 0.0042 | 1.005 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_tight_trail.out` |
| `dense_session` | `TomacNQVariantDenseSession` | 809 | 51.298 | 6.150 | 0.0371 | 1.034 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_dense_session.out` |
| `conservative_trend` | `TomacNQVariantConservativeTrend` | 393 | 54.453 | 11.360 | 0.0664 | 1.119 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_conservative_trend.out` |
| `loose_crisis` | `TomacNQVariantLooseCrisis` | 1153 | 49.176 | 86.220 | 0.3563 | 1.278 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_loose_crisis.out` |
| `bear_sideways_dense` | `TomacNQVariantBearSidewaysDense` | 1217 | 50.452 | -25.210 | -0.2278 | 0.871 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_bear_sideways_dense.out` |
| `full_day_trend` | `TomacNQVariantFullDayTrend` | 826 | 45.642 | -20.330 | -0.1412 | 0.886 | `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/logs/freqtrade_backtest_full_day_trend.out` |

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Specificity | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 3949 | 5 | 76 | 0.8000 | 0.000244 | 0.00 | 4.0014 | 999.000 | 60.0389 | `fail:reject_cost_fragile` |
| Bear | 329 | 5 | 10 | 0.2000 | -0.003807 | 1.00 | -5.3383 | 0.000 | 18.0000 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 985 | 5 | 13 | 0.6000 | -0.000197 | 0.20 | 0.8604 | 1.428 | 43.1901 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_rc_spa_below_60` |
| Crisis | 134 | 5 | 0 | 0.4000 | -0.001866 | 0.80 | -0.4980 | 0.000 | 26.4036 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 5 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 0.000 | 10.0000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/branch-rc-spa/tomac_nq_variant_matrix_report_v1.json`
- Generated strategy: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/strategy/TomacNQRootAwareVariantMatrixV1.py`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/branch-rc-spa/tomac_nq_variant_matrix_branch_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/branch-rc-spa/tomac_nq_variant_matrix_branch_rc_spa_summary_v1.csv`
- Variant fold matrix: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/branch-rc-spa/tomac_nq_variant_matrix_variant_fold_returns_v1.csv`
- Variant result summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/branch-rc-spa/tomac_nq_variant_matrix_variant_results_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T184529-codex-board-b-tomac-nq-variant-matrix-v1/checks/tomac_nq_variant_matrix_v1_assertions.out`

## Next

- B2R-repeat: extend direct Crisis/scoped Manipulation rows or test a different root-aware NQ family before downstream branch consumption.
