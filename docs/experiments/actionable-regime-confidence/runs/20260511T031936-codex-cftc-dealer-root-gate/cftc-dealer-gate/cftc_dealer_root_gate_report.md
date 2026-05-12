# CFTC Dealer Root Gate

Run id: `20260511T031936+0800-codex-cftc-dealer-root-gate`.

## Decision

- Gate result: `blocked_cftc_dealer_root_gate_below_95`
- Accepted new roots: none
- Missing roots: Bull, Bear, Sideways, Manipulation
- Runtime code changed: `false`
- Thresholds relaxed: `false`

## Results

| Root | State | Rule | Cal support | Cal LCB | Test support | Test LCB | Test precision | Blockers |
|---|---:|---|---:|---:|---:|---:|---:|---|
| Bull | blocked | `other_rept_long_short_ratio <= 0.449266312832 AND asset_mgr_short_oi <= 0.221553068053` | 43 | 0.224186 | 4 | 0.045587 | 0.250000 | calibration_support_below_80, test_support_below_40, calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_coverage_below_0_03, ece_above_0_05, validation_instruments_below_2 |
| Bear | blocked | `lev_money_long_oi_z52 <= -1.13922347602 AND lev_money_gross_oi <= 0.518950239533` | 42 | 0.134810 | 52 | 0.107960 | 0.192308 | calibration_support_below_80, calibration_wilson95_below_0_95, test_wilson95_below_0_95 |
| Sideways | blocked | `lev_money_long_oi >= 0.259752807321 AND dealer_long_short_ratio <= 0.50103166667` | 0 | 0.000000 | 0 | 0.000000 | 0.000000 | calibration_support_below_80, test_support_below_40, calibration_wilson95_below_0_95, test_wilson95_below_0_95, calibration_coverage_below_0_03, test_coverage_below_0_03, ece_above_0_05, validation_instruments_below_2 |

## Policy

- Candidate roots are active MainRegimeV2 parent labels `Bull`, `Bear`, and `Sideways` only.
- CFTC dealer, asset-manager, leveraged-money, and other-reportable positioning fields are predictors; future return label columns are blocked.
- `Manipulation` is not evaluated because this source is weekly positioning, not direct event/order-lifecycle/L2 evidence.
- Raw CFTC ZIPs stay under `/private/tmp` and are not committed to the repo.
