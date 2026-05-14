# Manipulation Stop/Take-Profit v1

Run ID: `20260511T205047+0800-codex-board-b-manipulation-stop-tp-grid-v2`

## Decision

- Gate result: `pass:direct_manipulation_stop_tp_candidate`
- Tradeable candidates: `['short_tp060_sl050_h36:36h', 'short_tp060_sl060_h36:36h', 'short_tp100_sl040_h36:36h', 'short_tp100_sl050_h36:36h', 'short_tp100_sl060_h36:36h', 'short_tp120_sl040_h36:36h', 'short_tp120_sl050_h36:36h', 'short_tp120_sl060_h36:36h', 'short_tp080_sl040_h48:48h', 'short_tp100_sl050_h48:48h', 'short_tp100_sl060_h48:48h', 'short_tp060_sl050_h72:72h', 'short_tp060_sl060_h72:72h', 'short_tp080_sl040_h72:72h', 'short_tp080_sl050_h72:72h', 'short_tp080_sl060_h72:72h', 'short_tp100_sl060_h72:72h', 'short_tp120_sl060_h72:72h']`
- Best variant: `short_tp120_sl060_h72`
- Best positive mean net: `0.006652`
- Best positive LCB 5%: `0.005609`
- Best specificity edge: `0.009914`
- Best specificity LCB 5%: `0.008658`
- Branch rows: `771495`
- Downstream consumption: `not_started:full_board_b_branch_gate_not_satisfied`

## Summary

| Variant | Action | Horizon | Pos Rows | Ctrl Rows | Folds | Pos Mean Net | Ctrl Mean Net | Edge | Pos LCB | Edge LCB | Fold+ Abs | Fold+ Ctrl | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `short_tp060_sl040_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | -0.000107 | -0.004386 | 0.004279 | -0.000670 | 0.003360 | 0.6667 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl050_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.000500 | -0.003433 | 0.003933 | -0.000103 | 0.002954 | 0.6667 | 0.5000 | `fail:reject_absolute_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl060_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.000753 | -0.003072 | 0.003825 | 0.000122 | 0.002805 | 0.6667 | 0.4167 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl040_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.000489 | -0.003416 | 0.003905 | -0.000127 | 0.002898 | 0.6667 | 0.5833 | `fail:reject_absolute_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl050_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.000979 | -0.002329 | 0.003309 | 0.000320 | 0.002236 | 0.6667 | 0.3333 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl060_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001307 | -0.002030 | 0.003337 | 0.000618 | 0.002223 | 0.7500 | 0.3333 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl040_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001213 | -0.003089 | 0.004302 | 0.000548 | 0.003226 | 0.6667 | 0.5000 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl050_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001759 | -0.002130 | 0.003889 | 0.001049 | 0.002746 | 0.6667 | 0.3333 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl060_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001952 | -0.001788 | 0.003740 | 0.001213 | 0.002553 | 0.7500 | 0.4167 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl040_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001388 | -0.002933 | 0.004320 | 0.000694 | 0.003194 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl050_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.001922 | -0.001975 | 0.003897 | 0.001181 | 0.002700 | 0.6667 | 0.4167 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl060_h24` | `short_stop_tp` | 24h | 13535 | 7149 | 12 | 0.002166 | -0.001653 | 0.003820 | 0.001394 | 0.002579 | 0.7500 | 0.4167 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl040_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.000443 | -0.006615 | 0.007058 | -0.000163 | 0.006040 | 0.6667 | 0.6667 | `fail:reject_absolute_lcb_nonpositive` |
| `short_tp060_sl050_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.001096 | -0.006252 | 0.007347 | 0.000443 | 0.006243 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp060_sl060_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.001415 | -0.006048 | 0.007463 | 0.000726 | 0.006299 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp080_sl040_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.001391 | -0.004837 | 0.006229 | 0.000713 | 0.005086 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl050_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.001966 | -0.004317 | 0.006283 | 0.001238 | 0.005051 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl060_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.002344 | -0.004038 | 0.006382 | 0.001577 | 0.005087 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl040_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.002291 | -0.004190 | 0.006480 | 0.001554 | 0.005248 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp100_sl050_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.003005 | -0.003804 | 0.006809 | 0.002213 | 0.005484 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp100_sl060_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.003308 | -0.003379 | 0.006687 | 0.002476 | 0.005295 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp120_sl040_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.002664 | -0.003818 | 0.006482 | 0.001884 | 0.005180 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp120_sl050_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.003414 | -0.003348 | 0.006762 | 0.002577 | 0.005363 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp120_sl060_h36` | `short_stop_tp` | 36h | 13535 | 7149 | 12 | 0.003894 | -0.003016 | 0.006910 | 0.003013 | 0.005444 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp060_sl040_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.000861 | -0.006594 | 0.007455 | 0.000227 | 0.006381 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl050_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.001600 | -0.007200 | 0.008799 | 0.000912 | 0.007622 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl060_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.002125 | -0.007789 | 0.009914 | 0.001396 | 0.008658 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl040_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.002107 | -0.004406 | 0.006513 | 0.001390 | 0.005293 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp080_sl050_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.002767 | -0.004696 | 0.007463 | 0.001992 | 0.006133 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp080_sl060_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.003368 | -0.005191 | 0.008559 | 0.002548 | 0.007147 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl040_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.003123 | -0.003104 | 0.006226 | 0.002337 | 0.004887 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl050_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.003886 | -0.003478 | 0.007364 | 0.003040 | 0.005912 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp100_sl060_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.004452 | -0.003902 | 0.008354 | 0.003558 | 0.006816 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp120_sl040_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.003420 | -0.002570 | 0.005990 | 0.002589 | 0.004569 | 0.7500 | 0.5000 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl050_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.004291 | -0.002883 | 0.007174 | 0.003395 | 0.005637 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl060_h48` | `short_stop_tp` | 48h | 13535 | 7149 | 12 | 0.004967 | -0.003522 | 0.008489 | 0.004021 | 0.006869 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp060_sl040_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.001127 | -0.006486 | 0.007613 | 0.000462 | 0.006495 | 0.5833 | 0.6667 | `fail:reject_absolute_fold_positive_rate_lt60pct` |
| `short_tp060_sl050_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.002100 | -0.006872 | 0.008972 | 0.001376 | 0.007737 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp060_sl060_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.002671 | -0.006966 | 0.009637 | 0.001898 | 0.008307 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp080_sl040_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.002838 | -0.003804 | 0.006642 | 0.002078 | 0.005355 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp080_sl050_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.003699 | -0.003893 | 0.007592 | 0.002875 | 0.006182 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp080_sl060_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.004164 | -0.003807 | 0.007971 | 0.003288 | 0.006462 | 0.6667 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp100_sl040_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.004017 | -0.002106 | 0.006123 | 0.003172 | 0.004691 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl050_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.004952 | -0.002144 | 0.007096 | 0.004040 | 0.005538 | 0.6667 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp100_sl060_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.005449 | -0.001818 | 0.007268 | 0.004482 | 0.005603 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `short_tp120_sl040_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.005008 | -0.001041 | 0.006049 | 0.004094 | 0.004503 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl050_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.006047 | -0.000835 | 0.006883 | 0.005061 | 0.005202 | 0.7500 | 0.5833 | `fail:reject_specificity_fold_rate_lt60pct` |
| `short_tp120_sl060_h72` | `short_stop_tp` | 72h | 13535 | 7149 | 12 | 0.006652 | -0.000733 | 0.007386 | 0.005609 | 0.005602 | 0.7500 | 0.6667 | `pass:tradeable_manipulation_stop_tp_candidate` |
| `long_tp030_sl030_h12` | `long_stop_tp` | 12h | 13535 | 7149 | 12 | -0.001511 | 0.000945 | -0.002456 | -0.001864 | -0.003046 | 0.2500 | 0.3333 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp050_sl030_h12` | `long_stop_tp` | 12h | 13535 | 7149 | 12 | -0.001446 | 0.000287 | -0.001733 | -0.001858 | -0.002408 | 0.2500 | 0.3333 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp080_sl030_h12` | `long_stop_tp` | 12h | 13535 | 7149 | 12 | -0.001684 | 0.000124 | -0.001809 | -0.002134 | -0.002539 | 0.3333 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp030_sl030_h24` | `long_stop_tp` | 24h | 13535 | 7149 | 12 | -0.001833 | 0.001598 | -0.003432 | -0.002223 | -0.004092 | 0.2500 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp050_sl030_h24` | `long_stop_tp` | 24h | 13535 | 7149 | 12 | -0.001267 | 0.001643 | -0.002910 | -0.001741 | -0.003709 | 0.3333 | 0.6667 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive` |
| `long_tp080_sl030_h24` | `long_stop_tp` | 24h | 13535 | 7149 | 12 | -0.001061 | 0.001761 | -0.002823 | -0.001602 | -0.003721 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp030_sl030_h48` | `long_stop_tp` | 48h | 13535 | 7149 | 12 | -0.001763 | 0.003544 | -0.005306 | -0.002177 | -0.006010 | 0.1667 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp050_sl030_h48` | `long_stop_tp` | 48h | 13535 | 7149 | 12 | -0.001093 | 0.006665 | -0.007758 | -0.001612 | -0.008673 | 0.3333 | 0.4167 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |
| `long_tp080_sl030_h48` | `long_stop_tp` | 48h | 13535 | 7149 | 12 | -0.000921 | 0.008301 | -0.009222 | -0.001541 | -0.010327 | 0.3333 | 0.5833 | `fail:reject_no_positive_absolute_edge_after_cost|reject_absolute_lcb_nonpositive|reject_absolute_fold_positive_rate_lt60pct|reject_no_regime_specificity_vs_controls|reject_specificity_lcb_nonpositive|reject_specificity_fold_rate_lt60pct` |

## Interpretation

- This is an executable provider-OHLC path probe: entries use the reconstructed next-bar open, then stop/take-profit logic over Binance 1h bars.
- Same-bar stop/take-profit collisions are resolved conservatively as stop first.
- Full Board B promotion still requires Bull, Bear, Sideways, Crisis, and scoped Manipulation to pass branch gates before Pre-Bayes / BBN / CatBoost / execution tree consumption.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2.json`
- Summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_summary.csv`
- Branch rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/manipulation-stop-tp-grid-v2/manipulation_stop_tp_grid_v2_branch_rows.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/checks/manipulation_stop_tp_grid_v2_assertions.out`
- Fail-closed summary: `docs/experiments/actionable-regime-confidence/runs/20260511T205047-codex-board-b-manipulation-stop-tp-grid-v2/ict-engine-fail-closed/manipulation_stop_tp_grid_v2_fail_closed_summary.md`

## Next

- B2R-repeat: if a direct Manipulation stop/take-profit candidate passed, combine it only with a separate root-branch candidate that passes Bull/Bear/Sideways/Crisis RC-SPA; otherwise switch source.
