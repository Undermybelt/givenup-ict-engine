# R6 Shak Duplicate Row Cleanup v1

- Decision: `r6_shak_duplicate_row_cleanup_v1=duplicate_rows_removed_calibration_still_blocked`.
- Removed only rows introduced by `20260511T211628-codex-r6-shak-cftc-row-uplift-v1`: positive `5`, matched negative `5`.
- Positive rows now: `32`; matched negative rows now: `32`.
- Unique dates: `17`; symbols: `10`; venues: `5`.
- Wilson95 LCB positive/negative/min: `0.892821` / `0.892821` / `0.892821`.
- Verifier status: `schema_ready_unscored`; return code: `0`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This cleanup removes only the duplicate rows created by this agent's `211628` slice. It preserves the concurrent `211606` Shak rows and all other shared intake additions.

## Gates

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `positive_support` | `32` | `50` | `false` |
| `negative_support` | `32` | `50` | `false` |
| `chronological_split` | `17` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=10;venues=5` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.892821` | `>=0.95` | `false` |
| `broad_normal_sample` | `CFTC public order/complaint same-event genuine-order legs are source-described schema/control seeds only; they are not a broad normal-market calibration sample.` | `source-owned broad normal activity sample` | `false` |

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1/r6-shak-duplicate-row-cleanup/r6_shak_duplicate_row_cleanup_v1.json`
- Gate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1/r6-shak-duplicate-row-cleanup/r6_shak_duplicate_row_cleanup_v1_gates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T212004-codex-r6-shak-duplicate-row-cleanup-v1/checks/r6_shak_duplicate_row_cleanup_v1_assertions.out`
