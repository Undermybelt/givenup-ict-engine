# Manipulation Action Surface v1

Run ID: `20260511T203620+0800-codex-board-b-manipulation-action-surface-v1`

## Decision

- Gate result: `fail:no_tradeable_manipulation_action_surface`
- Tradeable candidates: `[]`
- Best trade action: `event_long` / `48h`
- Best trade mean net: `0.002527`
- Best trade LCB 5%: `0.001178`
- Best specificity action: `event_short` / `48h`
- Best specificity edge: `0.018179`
- Best specificity LCB 5%: `0.015635`
- Branch rows: `296282`
- Downstream consumption: `not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa`

## Summary

| Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean Net | Ctrl Mean Net | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `event_long` | 1h | 13534 | 7142 | 12 | -0.000939 | -0.001354 | 0.000414 | -0.001270 | -0.000077 | 0.2500 | 0.7500 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_lcb_nonpositive` |
| `event_long` | 2h | 13531 | 7130 | 12 | -0.000868 | -0.001305 | 0.000437 | -0.001240 | -0.000123 | 0.4167 | 0.6667 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_lcb_nonpositive` |
| `event_long` | 3h | 13516 | 7130 | 12 | -0.000706 | -0.000748 | 0.000042 | -0.001126 | -0.000586 | 0.4167 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 4h | 13506 | 7116 | 12 | -0.001134 | -0.000386 | -0.000748 | -0.001590 | -0.001432 | 0.3333 | 0.5000 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 6h | 13458 | 7102 | 12 | -0.000546 | 0.000309 | -0.000855 | -0.001068 | -0.001632 | 0.5000 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 8h | 13469 | 7102 | 12 | -0.000444 | 0.000907 | -0.001350 | -0.001032 | -0.002239 | 0.4167 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 12h | 13440 | 7100 | 12 | -0.000122 | 0.002267 | -0.002389 | -0.000817 | -0.003454 | 0.5000 | 0.3333 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 18h | 13402 | 7060 | 12 | 0.000654 | 0.004343 | -0.003690 | -0.000231 | -0.005090 | 0.4167 | 0.4167 | `fail:reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 24h | 13448 | 7085 | 12 | 0.000914 | 0.006982 | -0.006068 | -0.000112 | -0.007768 | 0.5000 | 0.4167 | `fail:reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 36h | 13389 | 7121 | 12 | 0.002037 | 0.014066 | -0.012030 | 0.000839 | -0.014215 | 0.4167 | 0.2500 | `fail:reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_long` | 48h | 13448 | 7088 | 12 | 0.002527 | 0.020706 | -0.018179 | 0.001178 | -0.020722 | 0.4167 | 0.2500 | `fail:reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 1h | 13534 | 7142 | 12 | -0.002061 | -0.001646 | -0.000414 | -0.002391 | -0.000905 | 0.0000 | 0.2500 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 2h | 13531 | 7130 | 12 | -0.002132 | -0.001695 | -0.000437 | -0.002505 | -0.000998 | 0.0833 | 0.3333 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 3h | 13516 | 7130 | 12 | -0.002294 | -0.002252 | -0.000042 | -0.002713 | -0.000670 | 0.2500 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 4h | 13506 | 7116 | 12 | -0.001866 | -0.002614 | 0.000748 | -0.002321 | 0.000065 | 0.2500 | 0.5000 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 6h | 13458 | 7102 | 12 | -0.002454 | -0.003309 | 0.000855 | -0.002977 | 0.000077 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 8h | 13469 | 7102 | 12 | -0.002556 | -0.003907 | 0.001350 | -0.003145 | 0.000462 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 12h | 13440 | 7100 | 12 | -0.002878 | -0.005267 | 0.002389 | -0.003574 | 0.001324 | 0.3333 | 0.6667 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct` |
| `event_short` | 18h | 13402 | 7060 | 12 | -0.003654 | -0.007343 | 0.003690 | -0.004539 | 0.002289 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 24h | 13448 | 7085 | 12 | -0.003914 | -0.009982 | 0.006068 | -0.004940 | 0.004369 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `event_short` | 36h | 13389 | 7121 | 12 | -0.005037 | -0.017066 | 0.012030 | -0.006234 | 0.009845 | 0.5000 | 0.7500 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct` |
| `event_short` | 48h | 13448 | 7088 | 12 | -0.005527 | -0.023706 | 0.018179 | -0.006876 | 0.015635 | 0.5833 | 0.7500 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct` |
| `cooldown_relative` | 1h | 13534 | 7142 | 12 | 0.000561 | 0.000146 | 0.000414 | 0.000230 | -0.000077 | 0.6667 | 0.7500 | `fail:diagnostic_only:not_tradeable_profit_row|reject_specificity_lcb_nonpositive` |
| `cooldown_relative` | 2h | 13531 | 7130 | 12 | 0.000632 | 0.000195 | 0.000437 | 0.000260 | -0.000123 | 0.6667 | 0.6667 | `fail:diagnostic_only:not_tradeable_profit_row|reject_specificity_lcb_nonpositive` |
| `cooldown_relative` | 3h | 13516 | 7130 | 12 | 0.000794 | 0.000752 | 0.000042 | 0.000374 | -0.000586 | 0.6667 | 0.5833 | `fail:diagnostic_only:not_tradeable_profit_row|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 4h | 13506 | 7116 | 12 | 0.000366 | 0.001114 | -0.000748 | -0.000090 | -0.001432 | 0.5833 | 0.5000 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 6h | 13458 | 7102 | 12 | 0.000954 | 0.001809 | -0.000855 | 0.000432 | -0.001632 | 0.5833 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 8h | 13469 | 7102 | 12 | 0.001056 | 0.002407 | -0.001350 | 0.000468 | -0.002239 | 0.6667 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 12h | 13440 | 7100 | 12 | 0.001378 | 0.003767 | -0.002389 | 0.000683 | -0.003454 | 0.5833 | 0.3333 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 18h | 13402 | 7060 | 12 | 0.002154 | 0.005843 | -0.003690 | 0.001269 | -0.005090 | 0.5833 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 24h | 13448 | 7085 | 12 | 0.002414 | 0.008482 | -0.006068 | 0.001388 | -0.007768 | 0.5000 | 0.4167 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 36h | 13389 | 7121 | 12 | 0.003537 | 0.015566 | -0.012030 | 0.002339 | -0.014215 | 0.5000 | 0.2500 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `cooldown_relative` | 48h | 13448 | 7088 | 12 | 0.004027 | 0.022206 | -0.018179 | 0.002678 | -0.020722 | 0.4167 | 0.2500 | `fail:diagnostic_only:not_tradeable_profit_row|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |

## Interpretation

- `event_long` and `event_short` are tradeable action probes and include roundtrip cost.
- `cooldown_relative` measures event underperformance versus controls only; it is not a tradeable PnL row and cannot promote downstream.
- Full Board B promotion remains impossible unless Bull, Bear, Sideways, Crisis, and scoped Manipulation all pass branch RC-SPA.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T203620-codex-board-b-manipulation-action-surface-v1/manipulation-action-surface/manipulation_action_surface_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T203620-codex-board-b-manipulation-action-surface-v1/manipulation-action-surface/manipulation_action_surface_summary_v1.csv`
- Branch rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T203620-codex-board-b-manipulation-action-surface-v1/manipulation-action-surface/manipulation_action_surface_branch_rows_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T203620-codex-board-b-manipulation-action-surface-v1/checks/manipulation_action_surface_v1_assertions.out`

## Next

- B2R-repeat: scoped Manipulation still lacks tradeable PnL edge; switch source/family/panel before downstream promotion.
