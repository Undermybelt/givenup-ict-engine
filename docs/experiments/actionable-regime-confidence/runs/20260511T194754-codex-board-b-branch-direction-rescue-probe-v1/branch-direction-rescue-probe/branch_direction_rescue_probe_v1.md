# Branch Direction Rescue Probe v1

Run id: `20260511T194754+0800-codex-board-b-branch-direction-rescue-probe-v1`

## Decision

- Gate result: `fail:direction_rescue_probe_not_promotion_grade`
- Stable profit score: `81.2500`
- Branch paths passed: `1/5`
- Numeric candidates before diagnostic blockers: `1`
- Downstream consumption: `not_started:direction_probe_not_promotion_grade`

## Selected Branch Summary

| Root | Variant | Trades | Folds | Min Fold Trades | LCB 5% | PBO | DSR | RC-SPA | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Bull | `trend_follow_slow__as_recorded` | 6548 | 16 | 49 | 0.001972 | 0.125 | 5.6708 | 81.2500 | `pass` |
| Bear | `tail_breakdown_short__as_recorded` | 2161 | 13 | 28 | -0.000194 | 0.615 | 1.2139 | 44.2308 | `fail:reject_fold_inconsistency|reject_no_positive_edge|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |
| Sideways | `trend_follow_slow__inverse_direction_probe` | 1850 | 16 | 10 | 0.000180 | 0.125 | 1.9753 | 53.9150 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_rc_spa_below_60|reject_posthoc_inverse_direction_probe_not_predeclared_recipe` |
| Crisis | `trend_follow_fast__inverse_direction_probe` | 275 | 5 | 9 | -0.001149 | 0.200 | 0.8731 | 47.0959 | `fail:reject_fold_trade_depth|reject_no_positive_edge|reject_cost_fragile|reject_tail_risk|reject_rc_spa_below_60|reject_posthoc_inverse_direction_probe_not_predeclared_recipe` |
| Manipulation(scoped) | `manipulation_event_long_24h` | 13535 | 12 | 32 | 0.000388 | 0.333 | 2.2514 | 51.5006 | `fail:reject_fold_inconsistency|reject_cost_fragile|reject_overfit_risk|reject_tail_risk|reject_rc_spa_below_60` |

## Interpretation

- This is a diagnostic-only post-hoc direction/sign probe, not a promoted Auto-Quant recipe.
- Inverse-direction candidates remain blocked unless re-authored as predeclared recipes and rerun through RC-SPA.
- Short Manipulation probes remain blocked without borrow/perp execution evidence.

## Artifacts

- Report JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T194754-codex-board-b-branch-direction-rescue-probe-v1/branch-direction-rescue-probe/branch_direction_rescue_probe_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T194754-codex-board-b-branch-direction-rescue-probe-v1/branch-direction-rescue-probe/branch_direction_rescue_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T194754-codex-board-b-branch-direction-rescue-probe-v1/checks/branch_direction_rescue_probe_v1_assertions.out`
