# R6 Flotron CFTC Row Uplift v1

- Decision: `r6_flotron_cftc_row_uplift_v1=no_new_unique_rows_calibration_still_blocked`.
- Positive rows added by this run: `0`; matched negative rows added by this run: `0`.
- Positive rows now: `34`; matched negative rows now: `34`.
- Unique dates: `28`; symbols: `16`; venues: `5`.
- Wilson95 LCB positive/negative/min: `0.898485` / `0.898485` / `0.898485`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Direct species closed: `false`.
- Verifier status: `schema_ready_unscored`; return code: `0`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Source Rows Added

| Class | Added | Total |
|---|---:|---:|
| `positive` | `0` | `34` |
| `matched_negative` | `0` | `34` |

## Boundary

The Flotron rows are official CFTC same-complaint positive/control seeds. They improve direct R6 support and exact source breadth, but the controls remain same-event genuine-order legs, not independent broad normal-market calibration controls.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/r6-flotron-cftc-row-uplift/r6_flotron_cftc_row_uplift_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/r6-flotron-cftc-row-uplift/r6_flotron_cftc_row_uplift_v1.md`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/r6-flotron-cftc-row-uplift/r6_flotron_cftc_row_uplift_v1_gates.csv`
- Intake summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/r6-flotron-cftc-row-uplift/r6_flotron_cftc_row_uplift_v1_intake_summary.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213312-codex-r6-flotron-cftc-row-uplift-v1/checks/r6_flotron_cftc_row_uplift_v1_assertions.out`
