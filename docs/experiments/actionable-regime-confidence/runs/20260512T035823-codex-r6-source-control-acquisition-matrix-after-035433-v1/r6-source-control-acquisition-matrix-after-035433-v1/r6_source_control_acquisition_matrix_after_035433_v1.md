# R6 Source-Control Acquisition Matrix After 035433 v1

Run id: `20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1`
Gate result: `r6_source_control_acquisition_matrix_after_035433_v1=split_gap_matrix_ready_no_rows_acquired_no_promotion`

## Why This Exists

The upstream staging triplet passed only the pooled Wilson95 diagnostic. It failed chronological, heldout-symbol, heldout-venue, broad-control, owner-export, approval, and downstream gates. This packet converts those real split gaps into an acquisition matrix; it does not authorize copying any local triplet into the active owner-export root.

## Summary

- Pooled diagnostic Wilson95 LCB: `0.952479911333` with pooled pass `True`.
- Total additional paired rows if every exact failing cell must pass: `3717`.
- Family summaries: `[{'split_family': 'chronological_group_split', 'failing_cells': 3, 'max_pair_rows_needed_min': 55, 'sum_pair_rows_needed_min_if_exact_cells_must_all_pass': 142}, {'split_family': 'heldout_symbol_exact', 'failing_cells': 40, 'max_pair_rows_needed_min': 73, 'sum_pair_rows_needed_min_if_exact_cells_must_all_pass': 2847}, {'split_family': 'heldout_venue_exact', 'failing_cells': 11, 'max_pair_rows_needed_min': 73, 'sum_pair_rows_needed_min_if_exact_cells_must_all_pass': 728}]`.
- Active R6/R3/R5 source roots remain absent or incomplete.
- Explicit approval and `FLIP` control approval remain false.

## Worst Cells

- `chronological_group_split` / `chronological_calibration` needs at least `55` paired source-owned rows; route hint: same approved owner-export family, balanced by chronological split bucket.
- `chronological_group_split` / `chronological_test` needs at least `54` paired source-owned rows; route hint: same approved owner-export family, balanced by chronological split bucket.
- `chronological_group_split` / `chronological_train` needs at least `33` paired source-owned rows; route hint: same approved owner-export family, balanced by chronological split bucket.
- `heldout_symbol_exact` / `CBOT soybean call options` needs at least `73` paired source-owned rows; route hint: CME/CBOT owner export with source-owned broad normal controls.
- `heldout_symbol_exact` / `COMEX copper futures` needs at least `73` paired source-owned rows; route hint: CME/COMEX owner export with source-owned broad normal controls.
- `heldout_symbol_exact` / `LME copper futures / COMEX copper futures cross-market example` needs at least `73` paired source-owned rows; route hint: LME plus linked COMEX owner export or licensed cross-market support route.
- `heldout_symbol_exact` / `10-Year T-Note Futures contract, December 2011 expiry` needs at least `72` paired source-owned rows; route hint: CME/CME DataMine Market Depth or Market-by-Order owner export.
- `heldout_symbol_exact` / `10-Year T-Note Futures contract, March 2010 expiry` needs at least `72` paired source-owned rows; route hint: CME/CME DataMine Market Depth or Market-by-Order owner export.
- `heldout_symbol_exact` / `COMEX Gold Futures June delivery` needs at least `72` paired source-owned rows; route hint: CME/COMEX owner export with source-owned broad normal controls.
- `heldout_symbol_exact` / `COMEX Silver Futures` needs at least `72` paired source-owned rows; route hint: CME/COMEX owner export with source-owned broad normal controls.

## Decision

No promotion. This is a request/coverage artifact only: rows acquired false, active owner-export root complete false, approval false, canonical merge false, downstream promotion false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- Matrix JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1/r6-source-control-acquisition-matrix-after-035433-v1/r6_source_control_acquisition_matrix_after_035433_v1.json`
- Matrix CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1/r6-source-control-acquisition-matrix-after-035433-v1/r6_source_control_acquisition_matrix_after_035433_v1.csv`
- Family summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1/r6-source-control-acquisition-matrix-after-035433-v1/r6_source_control_acquisition_family_summary_v1.csv`
- Board hash readback: `docs/experiments/actionable-regime-confidence/runs/20260512T035823-codex-r6-source-control-acquisition-matrix-after-035433-v1/command-output/board_sha256_before_matrix.txt`
