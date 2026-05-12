# Manipulation Stop/Take-Profit v1

Run ID: `20260511T204718+0800-codex-board-b-manipulation-stop-tp-v1`

## Decision

- Gate result: `fail:no_tradeable_stop_tp_action_surface`
- Tradeable candidates: `[]`
- Best variant: `short_tp080_sl050_h48`
- Best positive mean net: `0.002767`
- Best positive LCB 5%: `0.001992`
- Best specificity edge: `0.007463`
- Best specificity LCB 5%: `0.006133`
- Branch rows: `108280`
- Downstream consumption: `not_started:full_board_b_branch_gate_not_satisfied`

## Summary

| Variant | Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean Net | Ctrl Mean Net | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `long_tp015_sl020_h6` | `long_stop_tp` | 6h | 13535 | 7149 | 12 | -0.001811 | -0.001735 | -0.000076 | -0.002026 | -0.000438 | 0.2500 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp030_sl020_h12` | `long_stop_tp` | 12h | 13535 | 7149 | 12 | -0.001226 | 0.000349 | -0.001575 | -0.001532 | -0.002094 | 0.2500 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp050_sl030_h24` | `long_stop_tp` | 24h | 13535 | 7149 | 12 | -0.001267 | 0.001643 | -0.002910 | -0.001741 | -0.003709 | 0.3333 | 0.6667 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `long_tp080_sl050_h48` | `long_stop_tp` | 48h | 13535 | 7149 | 12 | -0.001839 | 0.008978 | -0.010817 | -0.002590 | -0.012123 | 0.3333 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `short_tp015_sl020_h6` | `short_stop_tp` | 6h | 13535 | 7149 | 12 | -0.002063 | -0.002029 | -0.000033 | -0.002278 | -0.000395 | 0.2500 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `short_tp030_sl020_h12` | `short_stop_tp` | 12h | 13535 | 7149 | 12 | -0.001542 | -0.002546 | 0.001003 | -0.001848 | 0.000494 | 0.4167 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `short_tp050_sl030_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | -0.000089 | -0.004089 | 0.004000 | -0.000568 | 0.003208 | 0.5833 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl050_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.002767 | -0.004696 | 0.007463 | 0.001992 | 0.006133 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |

## Interpretation

- This is an executable provider-OHLC path probe: entries use the reconstructed next-bar open, then stop/take-profit logic over Binance 1h bars.
- Same-bar stop/take-profit collisions are resolved conservatively as stop first.
- Full Board B promotion still requires Bull, Bear, Sideways, Crisis, and scoped Manipulation to pass branch gates before Pre-Bayes / BBN / CatBoost / execution tree consumption.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T204718-codex-board-b-manipulation-stop-tp-v1/manipulation-stop-tp/manipulation_stop_tp_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T204718-codex-board-b-manipulation-stop-tp-v1/manipulation-stop-tp/manipulation_stop_tp_summary_v1.csv`
- Branch rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T204718-codex-board-b-manipulation-stop-tp-v1/manipulation-stop-tp/manipulation_stop_tp_branch_rows_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T204718-codex-board-b-manipulation-stop-tp-v1/checks/manipulation_stop_tp_v1_assertions.out`
- Fail-closed summary: `docs/experiments/actionable-regime-confidence/runs/20260511T204718-codex-board-b-manipulation-stop-tp-v1/ict-engine-fail-closed/manipulation_stop_tp_fail_closed_summary_v1.md`

## Next

- B2R-repeat: if a direct Manipulation stop/take-profit candidate passed, combine it only with a separate root-branch candidate that passes Bull/Bear/Sideways/Crisis RC-SPA; otherwise switch source.
