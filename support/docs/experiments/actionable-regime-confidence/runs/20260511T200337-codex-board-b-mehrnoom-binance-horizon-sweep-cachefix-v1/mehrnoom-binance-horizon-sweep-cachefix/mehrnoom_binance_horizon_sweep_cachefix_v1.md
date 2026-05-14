# Mehrnoom Binance Intraday Horizon Sweep Cachefix v1

Run ID: `20260511T200337+0800-codex-board-b-mehrnoom-binance-horizon-sweep-cachefix-v1`

## Decision

- Gate result: `fail:no_horizon_positive_vs_controls`
- Best horizon: `1h`
- Best positive-control diff: `0.000414`
- Best LCB 5%: `-0.000077`
- Horizons passed: `[]`
- Downstream consumption: `not_started:diagnostic_only_full_board_b_still_requires_all_root_rc_spa`

## Horizon Summary

| Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean | Ctrl Mean | Diff | LCB 5% | Fold+ | Gate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 13534 | 7142 | 12 | 0.000561 | 0.000146 | 0.000414 | -0.000077 | 0.7500 | `fail:reject_lcb_nonpositive` |
| 2 | 13531 | 7130 | 12 | 0.000632 | 0.000195 | 0.000437 | -0.000123 | 0.6667 | `fail:reject_lcb_nonpositive` |
| 3 | 13516 | 7130 | 12 | 0.000794 | 0.000752 | 0.000042 | -0.000586 | 0.5833 | `fail:reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 4 | 13506 | 7116 | 12 | 0.000366 | 0.001114 | -0.000748 | -0.001432 | 0.5000 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 6 | 13458 | 7102 | 12 | 0.000954 | 0.001809 | -0.000855 | -0.001632 | 0.4167 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 8 | 13469 | 7102 | 12 | 0.001056 | 0.002407 | -0.001350 | -0.002239 | 0.4167 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 12 | 13440 | 7100 | 12 | 0.001378 | 0.003767 | -0.002389 | -0.003454 | 0.3333 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 18 | 13402 | 7060 | 12 | 0.002154 | 0.005843 | -0.003690 | -0.005090 | 0.4167 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 24 | 13448 | 7085 | 12 | 0.002414 | 0.008482 | -0.006068 | -0.007768 | 0.4167 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 36 | 13389 | 7121 | 12 | 0.003537 | 0.015566 | -0.012030 | -0.014215 | 0.2500 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |
| 48 | 13448 | 7088 | 12 | 0.004027 | 0.022206 | -0.018179 | -0.020722 | 0.2500 | `fail:reject_positive_underperforms_control|reject_lcb_nonpositive|reject_fold_positive_rate_lt60pct` |

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T200337-codex-board-b-mehrnoom-binance-horizon-sweep-cachefix-v1/mehrnoom-binance-horizon-sweep-cachefix/mehrnoom_binance_horizon_sweep_cachefix_v1.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T200337-codex-board-b-mehrnoom-binance-horizon-sweep-cachefix-v1/mehrnoom-binance-horizon-sweep-cachefix/mehrnoom_binance_horizon_sweep_cachefix_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T200337-codex-board-b-mehrnoom-binance-horizon-sweep-cachefix-v1/checks/mehrnoom_binance_horizon_sweep_cachefix_v1_assertions.out`

## Next

- B2R-repeat: direct Manipulation horizon sweep failed; switch source/family or source-owned exits before promotion.
