# Mendeley Mt. Gox HGB Wash-Trading Gate

Run id: `20260511T082521+0800-codex-mendeley-v3-gox-refetch-reaudit`.

## Decision

- Gate result: `blocked_mendeley_gox_hgb_wash_below_95`
- Accepted 95 `Manipulation`: `false`
- Runtime code changed: `false`
- Thresholds relaxed: `false`
- Trade usable: `false`

## Source

- Dataset: Mendeley Data `Detecting Crypto Wash Trades via Machine Learning`, DOI `10.17632/4hyxfwzpgg.3`
- File: `gox_ml_samples.csv`
- Label polarity: `wash=true` is source wash-trading positive; `wash=false` is negative.
- Chronology: indirect source-script chronology; upstream `gox_ml_sample.py` sorts by `time` before writing the ML CSV, but the emitted CSV no longer carries timestamps.
- Blocked predictors: label, diagnostic wash percent, timestamps, future/target/next fields.

## Metrics

| Split | Rows | Support | Precision | Wilson95 LCB | Coverage | ECE |
|---|---:|---:|---:|---:|---:|---:|
| calibration | 1107450 | 33610 | 0.978340 | 0.976728 | 0.030349 | 0.081712 |
| test | 1107451 | 9961 | 0.987953 | 0.985615 | 0.008995 | 0.115501 |

## Result

The Mt. Gox HGB wash-trading model improves source coverage but remains blocked under the unchanged direct-evidence gate.
