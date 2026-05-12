# Corrected Advanced Feature Readback

Date: 2026-05-11

Purpose: record the result of the corrected-axis advanced OHLCV-derived feature run without overwriting the newer `20260510T234759-corrected-root-train-select-refinement` artifacts.

Source run:
- `docs/experiments/actionable-regime-confidence/runs/20260510T234600-main-regime-v2-corrected-advanced-features/root-v2/corrected_advanced_root_feature_report.json`
- `docs/experiments/actionable-regime-confidence/runs/20260510T234600-main-regime-v2-corrected-advanced-features/checks/corrected_advanced_root_feature_assertions.out`

Result:
- `accepted_root_classes_95`: none
- `blocked_root_classes`: `Bull`, `Bear`, `Sideways`, `Crisis`, `Manipulation`
- `accepted_gate`: `none_for_MainRegimeV2`
- `thresholds_relaxed`: false
- `blocked_future_target_predictors`: true

Best corrected-axis advanced feature candidates:

| Root Class | Best Test Wilson95 LCB | Test Support | Blockers |
|---|---:|---:|---|
| `Bull` | 0.474209 | 142 | calibration/test Wilson below 95; ECE above 0.05 |
| `Bear` | 0.259321 | 436 | calibration/test Wilson below 95; ECE above 0.05 |
| `Sideways` | 0.333684 | 149 | calibration/test Wilson below 95 |
| `Crisis` | 0.460786 | 194 | calibration support below 120; Wilson below 95; ECE above 0.05; timeframe coverage only 1h |
| `Manipulation` | 0.0 | 0 | missing direct required inputs |

Interpretation:
- Deterministic directional-change, persistence, and state-score features did not close any corrected MainRegimeV2 root class.
- More OHLCV-derived threshold search is now low-value evidence.
- The next useful step is new root evidence: breadth/intermarket/carry/order-flow/L2/event inputs, plus direct manipulation inputs.
