# Kaggle Bear/Sideways MainRegimeV2 Root Gate

Run id: `20260511T040137+0800-codex-kaggle-bear-sideways-root-gate`.

## Decision

- Gate result: `blocked_kaggle_bear_sideways_root_gate_below_95`
- Accepted new roots: none
- Effective accepted roots: Bull, Crisis
- Missing roots: Bear, Sideways, Manipulation

## Results

| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |
|---|---|---|---:|---:|---:|---:|---:|---|
| Bear | blocked | `ret20 <= -0.0620298245081 AND ret5 <= -0.01290654584` | 6040 | 0.829929 | 5469 | 0.825561 | 0.835619 | calibration_wilson95_below_0_95, test_wilson95_below_0_95 |
| Sideways | blocked | `ret20 <= 0.00252597008559 AND vol20_mean <= 0.14444726432` | 3227 | 0.711042 | 2694 | 0.711549 | 0.728656 | calibration_wilson95_below_0_95, test_wilson95_below_0_95 |

## Policy

- Thresholds were selected on the train split only.
- The train selector required a coverage buffer of at least 0.045 before held-out calibration/test checks.
- `regime_label` was used only as the target label; `future_*`, `target_*`, and `next_*` predictors stayed blocked.
- Raw provider data and the full feature table stayed under `/private/tmp`.
