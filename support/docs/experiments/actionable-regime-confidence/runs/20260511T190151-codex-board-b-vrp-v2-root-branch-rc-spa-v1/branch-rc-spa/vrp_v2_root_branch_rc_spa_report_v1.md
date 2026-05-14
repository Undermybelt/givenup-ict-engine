# VRP V2 Root Branch RC-SPA v1

Run id: `20260511T190151+0800-codex-board-b-vrp-v2-root-branch-rc-spa-v1`.

## Decision

- Gate result: `fail:all_branch_paths_failed_rc_spa_hard_gates`
- Stable profit score: `67.9374`
- Branch paths evaluated: `5`
- Branch paths passed: `0`
- Root trade counts: `{'Bull': 554, 'Bear': 46, 'Sideways': 193, 'Crisis': 22}`
- Downstream consumption: `not_started:blocked_by_branch_rc_spa_hard_gates`
- Primary blocker: VRP V2 is a different Auto-Quant artifact family and carries root-first branch paths, but downstream promotion is blocked unless every required root branch clears RC-SPA; scoped Manipulation still has no direct rows.

## Inputs

- VRP realized trades: `/private/tmp/vrp_v2_realized_trades.jsonl`
- VRP strategy library: `/private/tmp/vrp_v2_strategy_library.json`
- Prior runtime closure: `/private/tmp/vrp-v2-runtime-closure`
- Board A consumer map: `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv`
- Source anchor: `^IXIC`; target: `NQ`; source artifact is existing Auto-Quant/Pandas VRP V2.

## Branch Summary

| Root | Trades | Folds | Min Fold Trades | Fold Positive Rate | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | 554 | 3 | 92 | 0.3333 | -0.000253 | 1.00 | -2.8053 | 20.0000 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Bear | 46 | 3 | 11 | 0.3333 | -0.000609 | 1.00 | -1.4815 | 20.5235 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Sideways | 193 | 3 | 33 | 0.3333 | 0.000554 | 1.00 | 6.7778 | 67.9374 | `fail:reject_insufficient_test_folds|reject_fold_inconsistency|reject_overfit_risk` |
| Crisis | 22 | 1 | 22 | 0.0000 | -0.001000 | 1.00 | -21133400260813024.0000 | 12.4683 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |
| Manipulation(scoped) | 0 | 0 | 0 | 0.0000 | 0.000000 | 1.00 | 0.0000 | 10.0000 | `fail:reject_thin_trades|reject_insufficient_test_folds|reject_fold_trade_depth|reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_dsr_nonpositive|reject_no_regime_specificity|reject_rc_spa_below_60` |

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/branch-rc-spa/vrp_v2_root_branch_rc_spa_report_v1.json`
- Trade rows: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/branch-rc-spa/vrp_v2_root_branch_trades_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/branch-rc-spa/vrp_v2_root_branch_rc_spa_summary_v1.csv`
- ict-engine wire JSONL: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/ict-engine-fail-closed/vrp_v2_real_trades_wire_v1.jsonl`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T190151-codex-board-b-vrp-v2-root-branch-rc-spa-v1/checks/vrp_v2_root_branch_rc_spa_v1_assertions.out`

## Next

- If VRP is reused, convert it into a true multi-root parameter matrix or add direct Manipulation rows before downstream promotion; do not treat aggregate Sharpe as enough.
