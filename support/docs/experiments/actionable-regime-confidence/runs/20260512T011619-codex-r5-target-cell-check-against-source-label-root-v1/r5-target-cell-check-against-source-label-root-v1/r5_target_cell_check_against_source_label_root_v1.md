# R5 Target Cell Check Against Source Label Root v1

- Run id: `20260512T011619-codex-r5-target-cell-check-against-source-label-root-v1`.
- Gate result: `r5_target_cell_check_against_source_label_root_v1=source_label_root_has_no_post_cutoff_r5_target_rows`.
- Source-label rows present: `true`.
- R5 recency root files: `none`.
- R5 cutoff: rows must be after `2026-01-30`.
- All R5 targets satisfied: `false`.
- Accepted rows added: `0`; new confidence gate: false; downstream chain rerun allowed: false.
- Strict full objective achieved: false. `update_goal=false`.

## Target Cells

- `XOM` / `Sideways`: total `2067`, latest `2025-12-19`, post-cutoff `0`.
- `UNH` / `Bear`: total `1225`, latest `2025-12-31`, post-cutoff `0`.
- `^DJI` / `Sideways`: total `2198`, latest `2025-12-01`, post-cutoff `0`.
- `AMD` / `Bear`: total `1667`, latest `2025-12-11`, post-cutoff `0`.

## Boundary

The live source-label equivalence root is schema-ready but cannot fill the R5 post-cutoff recency-extension root. Do not copy these rows into the R5 root or treat historical pre-cutoff labels as R5 recency evidence.
