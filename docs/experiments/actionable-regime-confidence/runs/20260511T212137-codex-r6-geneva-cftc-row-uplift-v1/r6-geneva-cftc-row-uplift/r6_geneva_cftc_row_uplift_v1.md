# R6 Geneva CFTC Row Uplift v1

- Decision: `r6_geneva_cftc_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked`.
- Positive rows added/materialized by this run: `3`; matched negative rows added/materialized by this run: `3`.
- Positive rows now: `24`; matched negative rows now: `24`.
- Unique dates: `20`; symbols: `13`; venues: `5`.
- Wilson95 LCB positive/negative/min: `0.862024` / `0.862024` / `0.862024`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Verifier status: `schema_ready_unscored`; return code: `0`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Source Rows Added

| Class | Added | Total |
|---|---:|---:|
| `positive` | `3` | `24` |
| `matched_negative` | `3` | `24` |

## Boundary

The Geneva rows are public CFTC same-order positive/control seeds from a cached source. They improve direct R6 support and breadth but do not satisfy the broad normal-market calibration-control requirement.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/r6-geneva-cftc-row-uplift/r6_geneva_cftc_row_uplift_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/r6-geneva-cftc-row-uplift/r6_geneva_cftc_row_uplift_v1.md`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/r6-geneva-cftc-row-uplift/r6_geneva_cftc_row_uplift_v1_gates.csv`
- Intake summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/r6-geneva-cftc-row-uplift/r6_geneva_cftc_row_uplift_v1_intake_summary.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212137-codex-r6-geneva-cftc-row-uplift-v1/checks/r6_geneva_cftc_row_uplift_v1_assertions.out`
