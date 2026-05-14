# R6 Shak CFTC Row Uplift v1

- Decision: `r6_shak_cftc_row_uplift_v1=direct_intake_rows_uplifted_schema_ready_calibration_still_blocked`.
- Positive rows added: `5`; matched negative rows added: `5`.
- Positive rows now: `37`; matched negative rows now: `37`.
- Unique dates: `17`; symbols: `10`; venues: `5`.
- Wilson95 LCB positive/negative/min: `0.905942` / `0.905942` / `0.905942`.
- Chronological split ok: `true`; heldout symbol/venue ok: `true`.
- Broad normal sample: `false`.
- Verifier status: `schema_ready_unscored`; return code: `0`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Source Rows Added

| Class | Added | Total |
|---|---:|---:|
| `positive` | `5` | `37` |
| `matched_negative` | `5` | `37` |

## Calibration Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `37` | `50` | `false` |
| `negative_support` | `37` | `50` | `false` |
| `chronological_split` | `17` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=10;venues=5` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.905942` | `>=0.95` | `false` |
| `broad_normal_sample` | `CFTC public order/complaint same-event genuine-order legs are source-described schema/control seeds only; they are not a broad normal-market calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Boundary

The added Shak rows are public CFTC same-event positive/control seeds. They improve direct R6 support and date/symbol coverage, but they remain same-complaint controls, not broad normal-market calibration controls.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211628-codex-r6-shak-cftc-row-uplift-v1/r6-shak-cftc-row-uplift/r6_shak_cftc_row_uplift_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211628-codex-r6-shak-cftc-row-uplift-v1/r6-shak-cftc-row-uplift/r6_shak_cftc_row_uplift_v1_gates.csv`
- Intake summary CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211628-codex-r6-shak-cftc-row-uplift-v1/r6-shak-cftc-row-uplift/r6_shak_cftc_row_uplift_v1_intake_summary.csv`
- Verifier stdout: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211628-codex-r6-shak-cftc-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T211628-codex-r6-shak-cftc-row-uplift-v1/checks/r6_shak_cftc_row_uplift_v1_assertions.out`
