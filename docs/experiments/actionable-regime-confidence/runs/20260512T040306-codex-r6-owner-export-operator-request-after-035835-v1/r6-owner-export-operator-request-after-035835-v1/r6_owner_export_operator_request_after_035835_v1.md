# R6 Owner-Export Operator Request After 035835 v1

Run id: `20260512T040306-codex-r6-owner-export-operator-request-after-035835-v1`

Gate result: `r6_owner_export_operator_request_after_035835_v1=operator_request_ready_no_rows_acquired_no_promotion`

Board sha256 before request artifact: `4c9de6acc66964b31ca28e839461fbe437ab3f6a1d5c04be841ebcd1309f57be`

## Purpose

This packet converts the `035823` acquisition matrix and `035835` owner-export gap addendum into an operator-facing request. It does not acquire rows, mutate source roots, copy local triplets, approve `FLIP` controls, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Required Delivery Root

Populate only after owner/export delivery or explicit approval:

- `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required files:

- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

Required provenance fields:

- owner/export ticket or approval id
- raw delivery file hashes
- source license or access note
- field mapping from raw export to verifier schema
- positive-row event/source identifiers
- negative-row normal-control policy
- whether same-exhibit `FLIP` rows are explicitly approved as controls
- raw-data commit restriction

## Minimum Row Request

The pooled staging diagnostic already passed Wilson95 with LCB `0.952479911333`, but split validation failed. If exact failing cells must all pass, the current gap matrix needs `3717` additional paired rows:

- `chronological_group_split`: `3` failing cells, up to `55` paired rows in the weakest cell, `142` paired rows total if exact cells must all pass.
- `heldout_symbol_exact`: `40` failing cells, up to `73` paired rows in the weakest cell, `2847` paired rows total if exact cells must all pass.
- `heldout_venue_exact`: `11` failing cells, up to `73` paired rows in the weakest cell, `728` paired rows total if exact cells must all pass.

Highest-priority cells:

| Split family | Cell | Additional paired rows needed | Route hint |
|---|---|---:|---|
| `chronological_group_split` | `chronological_calibration` | 55 | Same approved owner/export family, balanced by chronological split bucket |
| `chronological_group_split` | `chronological_test` | 54 | Same approved owner/export family, balanced by chronological split bucket |
| `chronological_group_split` | `chronological_train` | 33 | Same approved owner/export family, balanced by chronological split bucket |
| `heldout_symbol_exact` | `CBOT soybean call options` | 73 | CME/CBOT owner export with source-owned broad normal controls |
| `heldout_symbol_exact` | `COMEX copper futures` | 73 | CME/COMEX owner export with source-owned broad normal controls |
| `heldout_symbol_exact` | `LME copper futures / COMEX copper futures cross-market example` | 73 | LME plus linked COMEX owner export or licensed cross-market support route |
| `heldout_venue_exact` | `LME and COMEX` | 73 | LME plus COMEX owner export or licensed cross-venue support route |
| `heldout_symbol_exact` | `10-Year T-Note Futures contract, December 2011 expiry` | 72 | CME DataMine Market Depth or Market-by-Order owner export |
| `heldout_symbol_exact` | `10-Year T-Note Futures contract, March 2010 expiry` | 72 | CME DataMine Market Depth or Market-by-Order owner export |
| `heldout_symbol_exact` | `COMEX Gold Futures June delivery` | 72 | CME/COMEX owner export with source-owned broad normal controls |
| `heldout_symbol_exact` | `COMEX Silver Futures` | 72 | CME/COMEX owner export with source-owned broad normal controls |

The full source/control matrix remains in:

- `docs/experiments/actionable-regime-confidence/runs/20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1/r6-source-control-acquisition-matrix-after-035433-v1/r6_source_control_acquisition_matrix_after_035433_v1.csv`
- `docs/experiments/actionable-regime-confidence/runs/20260512T035835-codex-r6-owner-export-gap-addendum-after-035433-v1/r6-owner-export-gap-addendum-after-035433-v1/r6_owner_export_gap_addendum_top_cells_v1.csv`

## Controls Policy

- Source-owned broad normal controls are required.
- Same-exhibit `FLIP` rows remain invalid controls unless explicitly approved.
- Local verifier-shaped triplets remain non-promoting unless source-owned control provenance or explicit approval is supplied.
- Do not copy `/tmp/ict-engine-direct-manipulation-row-intake`, `/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake`, or `/tmp/ict-engine-r6-direct-intake-v56-clean-readback/intake` into the owner-export root without approval.

## After Delivery

Only after the target root is populated with approved source/control rows:

1. Rerun the direct verifier on `/tmp/ict-engine-board-a-r6-owner-export-v1`.
2. Rerun split calibration for chronological, heldout-symbol, heldout-venue, and broad-control gates.
3. If the split gates pass, run canonical merge.
4. Rerun provider/AutoQuant.
5. Rerun filter/Pre-Bayes and BBN.
6. Rerun CatBoost/path-ranking.
7. Rerun execution-tree/workflow readback.
8. Append the promotion or blocked decision to the board.

## Decision

Accepted rows added `0`; source/control evidence acquired `false`; explicit approval `false`; `FLIP` controls approved `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.
