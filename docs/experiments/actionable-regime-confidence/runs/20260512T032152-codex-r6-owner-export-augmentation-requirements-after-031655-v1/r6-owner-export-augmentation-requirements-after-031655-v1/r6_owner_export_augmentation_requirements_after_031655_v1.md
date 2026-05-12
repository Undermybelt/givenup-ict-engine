# R6 Owner-Export Augmentation Requirements After 031655 v1

Run id: `20260512T032152-codex-r6-owner-export-augmentation-requirements-after-031655-v1`
Generated at UTC: `2026-05-11T19:23:20.111437+00:00`

## Result

- Gate result: `r6_owner_export_augmentation_requirements_after_031655_v1=requirements_quantified_no_source_rows_acquired_no_promotion`.
- Required rows per class per evaluated cell: `73` (`MIN_SUPPORT=50` and Wilson95 perfect-row LCB `0.950006246616`).
- This packet is requirements-only: it acquired `0` rows, added `0` accepted rows, left the canonical owner root untouched, and did not rerun downstream promotion.
- Latest audit gate: `current_objective_completion_audit_after_031435_v1=not_complete_latest_r6_packets_nonpromoting_source_controls_downstream_blocked`.
- Root readback: canonical R6 owner root exists `false`, R3 native root exists `false`, R5 recency root exists `false`.
- Approval readback: approval `false`, FLIP controls `false`, canonical merge `false`, downstream rerun `false`.

## Deficit Summary

| Split Family | Failed Cells | Positive Rows Needed | Matched Controls Needed | Combined Rows Needed | Worst Wilson95 LCB |
|---|---:|---:|---:|---:|---:|
| chronological_group_split | 3 | 142 | 142 | 284 | 0.824115449418 |
| heldout_symbol_exact | 40 | 2843 | 2843 | 5686 | 0.000000000000 |
| heldout_venue_exact | 11 | 726 | 726 | 1452 | 0.000000000000 |

## Chronological Cells

| Cell | Positive Support | Control Support | Positive Need | Control Need |
|---|---:|---:|---:|---:|
| chronological_calibration | 18 | 18 | 55 | 55 |
| chronological_test | 19 | 19 | 54 | 54 |
| chronological_train | 40 | 40 | 33 | 33 |

## Largest Venue Deficits

| Venue Cell | Positive Support | Control Support | Positive Need | Control Need |
|---|---:|---:|---:|---:|
| IFEU electronic market | 1 | 1 | 72 | 72 |
| LME and COMEX | 2 | 0 | 71 | 73 |
| CBOT | 2 | 2 | 71 | 71 |
| CME Group registered futures market (source order) | 3 | 3 | 70 | 70 |
| US futures exchange / CFTC complaint | 3 | 3 | 70 | 70 |

## Largest Symbol Deficits

| Symbol Cell | Positive Support | Control Support | Positive Need | Control Need |
|---|---:|---:|---:|---:|
| 10-Year T-Note Futures contract, December 2011 expiry | 1 | 1 | 72 | 72 |
| 10-Year T-Note Futures contract, March 2010 expiry | 1 | 1 | 72 | 72 |
| CBOT soybean call options | 0 | 2 | 73 | 71 |
| COMEX Gold Futures June delivery | 1 | 1 | 72 | 72 |
| COMEX Silver Futures | 1 | 1 | 72 | 72 |
| COMEX copper futures | 0 | 2 | 73 | 71 |
| December 2014 E-mini S&P 500 futures | 1 | 1 | 72 | 72 |
| December 2017 Gold futures | 1 | 1 | 72 | 72 |

## Filename Contract

Owner/export delivery is not verifier-ready unless `/tmp/ict-engine-board-a-r6-owner-export-v1` contains verifier-native names:

- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

The conceptual request-package names from the earlier dispatch packet must be delivered under these names or mapped by an explicit verifier/mapping update before rerun.

## Boundary

This packet does not promote `031316` staging evidence, `031435` local triplet sidecars/projections, readiness packets, local caches, Auto-Quant readiness/backtests, or FLIP rows without explicit approval.

## Next

Acquire source-owned owner/operator rows and matched controls for the deficit cells listed in the CSVs. After real delivery or explicit approval, rerun the direct verifier, rerun split calibration, and only then rerun provider/Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution tree.
