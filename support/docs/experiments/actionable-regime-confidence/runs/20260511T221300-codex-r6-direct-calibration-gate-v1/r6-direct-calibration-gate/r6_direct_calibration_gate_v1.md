# R6 Direct Calibration Gate v1

- Decision: `r6_direct_calibration_gate_v1=chronological_heldout_calibration_fail_closed`.
- Direct intake rows: positives `57`, matched negatives `57`, matched groups `56`.
- Pooled Wilson95 min LCB: `0.936859`; pooled 95 gate: `false`.
- Chronological/heldout split gate: `false`.
- Broad normal sample: `false`; direct species closed: `false`.
- Accepted gate: `false`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Split Metrics

| Split Family | Split | Pos | Neg | Min Wilson95 LCB | Pass | Blocker |
|---|---|---:|---:|---:|---:|---|
| `pooled_all_source_rows` | `all_rows` | `57` | `57` | `0.936859` | `false` | `wilson95_below_0.95` |
| `chronological_group_split` | `chronological_train` | `29` | `29` | `0.883026` | `false` | `support_below_50;wilson95_below_0.95` |
| `chronological_group_split` | `chronological_calibration` | `14` | `14` | `0.784683` | `false` | `support_below_50;wilson95_below_0.95` |
| `chronological_group_split` | `chronological_test` | `14` | `14` | `0.784683` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `April 2017 Gold futures` | `2` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `August-delivery Gold Futures` | `3` | `3` | `0.438494` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `CBOT soybean call options` | `0` | `2` | `0.000000` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `CBOT soybean futures` | `4` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `CLM0-CLU0 crude oil June-September 2020 calendar spread` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `CLM0-CLZ0 crude oil June-December 2020 calendar spread` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `COMEX Gold Futures` | `6` | `6` | `0.609657` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `COMEX Gold Futures June delivery` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `COMEX Silver Futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `COMEX copper futures` | `0` | `2` | `0.000000` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December 2013 E-mini Dow futures` | `2` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December 2013 E-mini NASDAQ futures` | `5` | `5` | `0.565509` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December 2014 E-mini S&P 500 futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December 2017 Gold futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December 2017 Silver futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `December-delivery Gold Futures` | `7` | `7` | `0.645661` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `E-mini S&P 500 futures` | `3` | `3` | `0.438494` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `ICE Brent/WTI crude spread April 2020` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `LME copper futures` | `2` | `0` | `0.000000` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `March 2014 E-mini S&P 500 futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `March 2018 Crude Oil futures` | `4` | `4` | `0.510100` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `March 2018 Silver futures` | `4` | `4` | `0.510100` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `March-delivery Silver Futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `NGH0-NGJ0 natural gas March-April 2020 calendar spread` | `2` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `RBOB gasoline futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `Soft Red Winter wheat futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_symbol_exact` | `light sweet crude oil futures` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `CBOT` | `2` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `CBOT/CME Globex` | `4` | `4` | `0.510100` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `CME` | `7` | `7` | `0.645661` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `CME Globex` | `3` | `3` | `0.438494` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `CME Group registered futures market (source order)` | `3` | `3` | `0.438494` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `COMEX` | `8` | `8` | `0.675584` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `COMEX/CME Globex` | `19` | `19` | `0.831816` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `IFEU electronic market` | `1` | `1` | `0.206543` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `LME and COMEX cross-market` | `2` | `2` | `0.342372` | `false` | `support_below_50;wilson95_below_0.95` |
| `heldout_venue_exact` | `NYMEX/CME Globex` | `8` | `8` | `0.675584` | `false` | `support_below_50;wilson95_below_0.95` |

## Boundary

This is a calibration readback over source-owned/direct rows already in `/tmp`. It does not add rows and does not convert same-event genuine-order controls into independent broad normal-market controls.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T221300-codex-r6-direct-calibration-gate-v1/r6-direct-calibration-gate/r6_direct_calibration_gate_v1.json`
- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T221300-codex-r6-direct-calibration-gate-v1/r6-direct-calibration-gate/r6_direct_calibration_split_metrics_v1.csv`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260511T221300-codex-r6-direct-calibration-gate-v1/scripts/r6_direct_calibration_gate_v1.py`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T221300-codex-r6-direct-calibration-gate-v1/checks/r6_direct_calibration_gate_v1_assertions.out`
