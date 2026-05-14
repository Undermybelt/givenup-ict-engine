# Cross-Run Root Ensemble RC-SPA v1

Run id: `20260511T215453+0800-codex-board-b-cross-run-root-ensemble-v1`.

## Decision

- Gate result: `fail:required_root_branch_hard_gates_failed`
- Stable profit score: `83.9626`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `True`
- Variant rows: `112459`
- Selected rows: `951`
- Selected root counts: `{'Bull': 22, 'Bear': 20, 'Sideways': 856, 'Crisis': 53, 'Manipulation(scoped)': 13535}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: Bull=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk; Bear=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth; Sideways=fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60; Crisis=fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk

## Source Pool

| Source | Rows | Status |
|---|---:|---|
| `CryptoLiquidityRootFamilyV2` | 33059 | `loaded` |
| `YFinanceDefensiveCrossAssetV1Repaired` | 8763 | `loaded` |
| `ProviderRawDailyConsensusV1` | 843 | `loaded` |
| `SessionLiquidityIntradayV1` | 19959 | `loaded` |
| `VolStressTermStructureBreadthV1` | 7955 | `loaded` |
| `IntradayRiskDefensiveRotationV1` | 41880 | `loaded` |

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `ProviderRawDailyConsensusV1::provider_pullback_reclaim` | 22 | 3 | 2 | 1.0000 | 0.014129 | 0.438 | 3.0875 | 76.4499 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Bear | `ProviderRawDailyConsensusV1::defensive_fx_long` | 20 | 3 | 2 | 1.0000 | 0.001229 | 0.077 | 1.9657 | 83.9626 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth` |
| Sideways | `YFinanceDefensiveCrossAssetV1Repaired::low_vol_carry` | 856 | 16 | 1 | 0.6875 | 0.000130 | 0.062 | 1.7998 | 55.4088 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60` |
| Crisis | `VolStressTermStructureBreadthV1::crisis_tail_hedge_breakout` | 53 | 3 | 4 | 1.0000 | 0.008435 | 0.400 | 4.0061 | 79.4353 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_overfit_risk` |
| Manipulation(scoped) | `short_tp120_sl060_h72` | 13535 | 12 | 1127 | 0.7500 | 0.005609 | 0.000 | 1.0000 | 100.0000 | `pass` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/branch-rc-spa/cross_run_root_ensemble_rc_spa_report_v1.json`
- Selected rows: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/branch-rc-spa/cross_run_root_ensemble_selected_rows_v1.csv`
- Variant rows: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/branch-rc-spa/cross_run_root_ensemble_variant_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/branch-rc-spa/cross_run_root_ensemble_branch_summary_v1.csv`
- Source summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/branch-rc-spa/cross_run_root_ensemble_source_summary_v1.csv`
- Fail-closed downstream summary: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/ict-engine-fail-closed/cross_run_root_ensemble_fail_closed_summary_v1.md`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T215453-codex-board-b-cross-run-root-ensemble-v1/checks/cross_run_root_ensemble_v1_assertions.out`

## Next

- B2R-repeat: source a genuinely different family/provider panel; do not keep recombining failed source variants.
