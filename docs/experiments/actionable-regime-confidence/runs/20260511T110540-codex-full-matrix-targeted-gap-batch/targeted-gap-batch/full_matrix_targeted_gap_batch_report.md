# Full-Matrix Targeted Gap Batch

Run ID: `20260511T110540+0800-codex-full-matrix-targeted-gap-batch`

## Result

- Accepted 95 roots in this slice: `[]`.
- Blocked roots in this slice: `['Crisis', 'Bull', 'Bear', 'Sideways']`.
- Gate result: `blocked_targeted_gap_batch_no_new_full_matrix_slice`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Root Results

| Root | State | Calibration Wilson95 | Test Wilson95 | Test Coverage | Blockers |
|---|---|---:|---:|---:|---|
| Crisis | `blocked` | `0.390574` | `0.246776` | `0.035601` | `calibration_wilson95_below_0_95; test_wilson95_below_0_95; calibration_coverage_below_min; ece_above_0_05` |
| Bull | `blocked` | `0.436269` | `0.316151` | `0.038122` | `calibration_wilson95_below_0_95; test_wilson95_below_0_95; calibration_coverage_below_min; ece_above_0_05` |
| Bear | `blocked` | `0.241498` | `0.219833` | `0.042314` | `calibration_wilson95_below_0_95; test_wilson95_below_0_95; ece_above_0_05; calibration_validation_timeframes_below_2; test_validation_timeframes_below_2` |
| Sideways | `blocked` | `0.277869` | `0.282312` | `0.014771` | `calibration_wilson95_below_0_95; test_wilson95_below_0_95; calibration_coverage_below_min; test_coverage_below_min` |

## Decision

This is not a completion artifact. It is a bounded targeted batch against known gaps.

If a root passed here, it is only a scoped gap slice. The full observed matrix remains incomplete until every active parent root passes across the current provider/context/timeframe matrix and `Manipulation` covers direct evidence varieties beyond the scoped event feeds.
