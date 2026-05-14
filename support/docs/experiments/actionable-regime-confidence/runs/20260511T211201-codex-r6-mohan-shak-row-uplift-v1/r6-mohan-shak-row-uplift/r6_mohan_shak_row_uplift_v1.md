# R6 Mohan/Shak Row Uplift v1

Decision: `r6_mohan_shak_row_uplift_v1=rows_added_schema_ready_calibration_blocked`.

Result:
- Positive rows added to `/tmp` intake: `11`; matched negative rows added: `11`.
- Total direct intake rows after uplift: positives `32`, matched negatives `32`, matched groups `31`.
- Unique positive dates/symbols/venues: `17` / `10` / `5`.
- Wilson95 LCB positive/negative/min: `0.892821` / `0.892821` / `0.892821`.
- Required all-success support for Wilson95 `>=0.95`: `73`.
- Source text checks ok: `true`; verifier status: `schema_ready_unscored`.
- Broad normal sample: `false`; direct species coverage still only `spoofing_layering`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `source_text_checks` | `True` | `True` | `true` |
| `positive_rows_added` | `11` | `>0` | `true` |
| `negative_rows_added` | `11` | `>0` | `true` |
| `verifier_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `positive_support` | `32` | `73` | `false` |
| `negative_support` | `32` | `73` | `false` |
| `chronological_train_calibration_test` | `17` | `3` | `true` |
| `heldout_symbol_or_venue` | `symbols=10;venues=5` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.892821` | `>=0.95` | `false` |
| `broad_normal_sample` | `same-source public CFTC genuine-order counterparts` | `source-owned broad normal activity sample` | `false` |
| `direct_species_coverage` | `spoofing_layering` | `spoofing_layering;quote_spoofing;quote_stuffing;pinging;bear_raid;painting_tape` | `false` |

Interpretation:
The uplift materially increases the public CFTC direct-row seed, adds COMEX metals and CBOT/CME E-mini Dow coverage, and preserves chronological plus heldout-symbol/venue breadth. It still cannot satisfy the strict confidence objective because support remains far below Wilson95 `>=0.95`, controls are same-source enforcement-example genuine orders rather than broad normal-market controls, and non-spoofing direct species remain absent.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211201-codex-r6-mohan-shak-row-uplift-v1/r6-mohan-shak-row-uplift/r6_mohan_shak_row_uplift_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211201-codex-r6-mohan-shak-row-uplift-v1/r6-mohan-shak-row-uplift/r6_mohan_shak_row_uplift_v1_gates.csv`
- Additions CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211201-codex-r6-mohan-shak-row-uplift-v1/r6-mohan-shak-row-uplift/r6_mohan_shak_row_uplift_v1_additions.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T211201-codex-r6-mohan-shak-row-uplift-v1/r6-mohan-shak-row-uplift/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211201-codex-r6-mohan-shak-row-uplift-v1/checks/r6_mohan_shak_row_uplift_v1_assertions.out`
