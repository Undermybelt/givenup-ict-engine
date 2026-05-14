# Kaggle Direct Regime-Label Root Gate

Run id: `20260511T033017+0800-codex-kaggle-regime-label-root-gate`.

## Decision

- Gate result: `blocked_kaggle_regime_label_root_gate_below_95`
- Accepted new roots: none
- Missing roots: Bull, Bear, Sideways, Manipulation
- Runtime code changed: `false`
- Thresholds relaxed: `false`

## Results

| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |
|---|---:|---|---:|---:|---:|---:|---:|---|
| Bull | blocked | `close_drawdown60 >= 0 AND volatility <= 0.152179344579` | 1498 | 0.962320 | 2210 | 0.966224 | 0.973756 | calibration_coverage_below_0_03 |
| Bear | blocked | `ret20 <= -0.043667898623 AND vix >= 29.5200004578` | 2548 | 0.750466 | 2545 | 0.836720 | 0.851081 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, ece_above_0_05 |
| Sideways | blocked | `ret20 <= 0.00252597008559 AND vol20_mean <= 0.129492491459` | 2166 | 0.727793 | 1681 | 0.745385 | 0.766211 | calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_coverage_below_0_03 |

## Policy

- Source `regime_label` is used only as the target label.
- Source `regime_confidence` and future/target/next columns are blocked as predictors.
- Candidate roots are active MainRegimeV2 parent labels `Bull`, `Bear`, and `Sideways` only.
- `Manipulation` is not evaluated because this source is not direct event/order-lifecycle/L2 evidence.
- Raw Kaggle ZIP/CSV and the full derived feature table stay under `/private/tmp` and are not committed to the repo.
- Repo artifacts are compact: report JSON/MD, summary CSV, assertion output, and feature sample only.
