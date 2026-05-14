# R6 Owner-Export Gap Addendum After 035433 v1

Run id: `20260512T035835-codex-r6-owner-export-gap-addendum-after-035433-v1`

Gate result: `r6_owner_export_gap_addendum_after_035433_v1=gap_addendum_ready_rows_not_acquired_no_promotion`

## Source

- Source split calibration: `20260512T035433-codex-r6-staging-triplet-split-calibration-after-035233-v1`.
- Source gate: `r6_staging_triplet_split_calibration_after_035233_v1=staging_pooled95_pass_split_support_broad_controls_and_policy_blocked_no_promotion`.
- Pooled Wilson95 LCB: `0.952479911333`; pooled gate `True`.
- Chronological split gate `False`, heldout-symbol gate `False`, heldout-venue gate `False`, broad independent normal controls `False`.

## Gap Addendum

The current owner/export request should not ask only for pooled support. It must cover these split gaps with source-owned positive rows plus independent normal/non-manipulation controls:

- `chronological_group_split`: `3` failing cells, max `55` additional pairs, sum `142` if exact cells must all pass; worst cell `chronological_calibration`.
- `heldout_symbol_exact`: `40` failing cells, max `73` additional pairs, sum `2847` if exact cells must all pass; worst cell `CBOT soybean call options`.
- `heldout_venue_exact`: `11` failing cells, max `73` additional pairs, sum `728` if exact cells must all pass; worst cell `LME and COMEX`.

Top gap cells:

| Split family | Cell | Positive support | Negative support | Additional paired rows needed |
|---|---|---:|---:|---:|
| `heldout_symbol_exact` | CBOT soybean call options | 0 | 2 | 73 |
| `heldout_symbol_exact` | COMEX copper futures | 0 | 2 | 73 |
| `heldout_symbol_exact` | LME copper futures / COMEX copper futures cross-market example | 2 | 0 | 73 |
| `heldout_venue_exact` | LME and COMEX | 2 | 0 | 73 |
| `heldout_symbol_exact` | 10-Year T-Note Futures contract, December 2011 expiry | 1 | 1 | 72 |
| `heldout_symbol_exact` | 10-Year T-Note Futures contract, March 2010 expiry | 1 | 1 | 72 |
| `heldout_symbol_exact` | COMEX Gold Futures June delivery | 1 | 1 | 72 |
| `heldout_symbol_exact` | COMEX Silver Futures | 1 | 1 | 72 |
| `heldout_symbol_exact` | December 2014 E-mini S&P 500 futures | 1 | 1 | 72 |
| `heldout_symbol_exact` | December 2017 Gold futures | 1 | 1 | 72 |
| `heldout_symbol_exact` | December 2017 Silver futures | 1 | 1 | 72 |
| `heldout_symbol_exact` | Gold Futures contract, April 2014 expiry | 1 | 1 | 72 |

## Delivery Contract

- Populate only after owner/export delivery or explicit approval: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required files remain `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.
- Same-exhibit `FLIP` rows remain invalid controls unless explicitly approved.
- Preserve ticket/export/license identifiers, raw delivery hashes, field mapping, normal-control policy, and raw-data commit restrictions in provenance.

## Decision

This is a request addendum only. It acquires no rows, mutates no roots, approves no controls, and does not justify canonical merge or downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree rerun.

Accepted rows added `0`; new confidence gate `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.
