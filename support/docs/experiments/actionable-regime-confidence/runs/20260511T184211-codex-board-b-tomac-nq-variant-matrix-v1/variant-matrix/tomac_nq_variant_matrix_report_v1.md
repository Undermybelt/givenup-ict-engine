# Tomac NQ Variant Matrix v1

Run id: `20260511T184211+0800-codex-board-b-tomac-nq-variant-matrix-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `69.5742`
- Variant matrix: `8` variants x `5` folds
- Full-matrix trade rows: `4074`
- Branch paths passed: `0` / `5`
- Selected root trade counts: `{'Bull': 538, 'Bear': 45, 'Sideways': 113, 'Crisis': 7, 'Manipulation(scoped)': 0}`
- Required failed roots: `['Bear', 'Sideways', 'Crisis', 'Manipulation(scoped)']`
- Downstream consumption: `not_started:blocked_by_required_branch_rc_spa_hard_gates`
- Primary blocker: TomacNQVariantMatrixV1 estimates PBO from 8 variants x 5 folds, but required Bear/Sideways/Crisis/Manipulation branch paths still do not all satisfy RC-SPA.

## Selected Branch Summary

| Root | Selected Variant | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | Tail p95 | Specificity | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `TomacNQ_VM_Tight12_AM13_15` | 538 | 5 | 0 | 0.8000 | 0.000171 | 1.00 | 2.3981 | 0.0102 | 3.0000 | 61.2865 | `fail:reject_fold_trade_depth|reject_cost_fragile|reject_overfit_risk` |
| Bear | `TomacNQ_VM_CrisisWide12_AM12_16` | 45 | 5 | 0 | 0.4000 | -0.007228 | 1.00 | -1.8522 | 0.0250 | 0.0000 | 16.5001 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | `TomacNQ_VM_Fast18_AM13_16` | 113 | 5 | 0 | 0.6000 | -0.000463 | 0.75 | 1.1037 | 0.0138 | 1.8799 | 50.5380 | `fail:reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_rc_spa_below_60` |
| Crisis | `TomacNQ_VM_Wide36_AM14_15` | 7 | 5 | 0 | 0.6000 | 0.002235 | 0.33 | 2.7454 | 0.0019 | 8.1691 | 69.5742 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_overfit_risk` |
| Manipulation(scoped) | `TomacNQ_VM_Base24_AM13_15` | 0 | 5 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 0.0000 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Variant Full-Window Readback

| Variant | Trades | Net R | Win Rate | Root Counts |
|---|---:|---:|---:|---|
| `TomacNQ_VM_Base24_AM13_15` | 450 | 0.230004 | 0.5222 | `{'Bull': 355, 'Bear': 15, 'Sideways': 68, 'Crisis': 12, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_Fast18_AM13_16` | 634 | 0.344467 | 0.5457 | `{'Bull': 470, 'Bear': 32, 'Sideways': 113, 'Crisis': 19, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_Tight12_AM13_15` | 720 | 0.368036 | 0.5611 | `{'Bull': 538, 'Bear': 40, 'Sideways': 122, 'Crisis': 20, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_Wide36_AM14_15` | 302 | 0.230403 | 0.4901 | `{'Bull': 236, 'Bear': 7, 'Sideways': 52, 'Crisis': 7, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_NoTrend24_AM13_15` | 450 | 0.230004 | 0.5222 | `{'Bull': 355, 'Bear': 15, 'Sideways': 68, 'Crisis': 12, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_CrisisWide12_AM12_16` | 708 | 0.240592 | 0.5212 | `{'Bull': 517, 'Bear': 45, 'Sideways': 122, 'Crisis': 24, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_Sideways18_AM12_15` | 524 | 0.048317 | 0.4676 | `{'Bull': 407, 'Bear': 19, 'Sideways': 83, 'Crisis': 15, 'Manipulation(scoped)': 0}` |
| `TomacNQ_VM_Conservative48_AM13_14` | 286 | 0.196223 | 0.4790 | `{'Bull': 237, 'Bear': 6, 'Sideways': 36, 'Crisis': 7, 'Manipulation(scoped)': 0}` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/variant-matrix/tomac_nq_variant_matrix_report_v1.json`
- Full trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/variant-matrix/tomac_nq_variant_matrix_trades_v1.csv`
- Selected branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/variant-matrix/tomac_nq_variant_matrix_root_summary_v1.csv`
- Variant summary: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/variant-matrix/tomac_nq_variant_matrix_variant_summary_v1.csv`
- Fold matrix: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/variant-matrix/tomac_nq_variant_matrix_fold_matrix_v1.csv`
- Run-local strategies: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/strategies`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T184211-codex-board-b-tomac-nq-variant-matrix-v1/checks/tomac_nq_variant_matrix_v1_assertions.out`

## Next

- B2R-repeat: extend direct crisis/manipulation rows or synthesize a branch-specific recipe that increases Bear/Sideways/Crisis fold depth without losing edge.
