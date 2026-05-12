# R6 Mohan/Shak Duplicate Cleanup v1

Decision: `r6_mohan_shak_duplicate_cleanup_v1=duplicate_rows_removed_calibration_still_blocked`.

Result:
- Removed duplicate rows introduced by my `211201` uplift only: positives `11`, matched negatives `11`.
- Corrected live direct intake: positives `24`, matched negatives `24`, matched groups `23`.
- Unique positive dates/symbols/venues: `20` / `13` / `5`.
- Wilson95 LCB positive/negative/min: `0.862024` / `0.862024` / `0.862024`.
- Verifier status: `schema_ready_unscored`.
- Broad normal sample: `false`; direct species coverage still limited.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `removed_only_211201_positive_rows` | `11` | `11` | `true` |
| `removed_only_211201_negative_rows` | `11` | `11` | `true` |
| `verifier_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `positive_support` | `24` | `50` | `false` |
| `negative_support` | `24` | `50` | `false` |
| `orphan_groups` | `0` | `0` | `true` |
| `chronological_split` | `20` | `2` | `true` |
| `heldout_symbol_or_venue` | `symbols=13;venues=5` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.862024` | `>=0.95` | `false` |
| `broad_normal_sample` | `same-source public CFTC genuine-order counterparts` | `source-owned broad normal activity sample` | `false` |

Interpretation:
The cleanup corrects my own duplicate contribution and keeps the shared intake conservative. R6 remains schema-ready but confidence-blocked because support/Wilson95, broad normal controls, and direct-species breadth are still insufficient.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/r6-mohan-shak-duplicate-cleanup/r6_mohan_shak_duplicate_cleanup_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/r6-mohan-shak-duplicate-cleanup/r6_mohan_shak_duplicate_cleanup_v1_gates.csv`
- Removed rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/r6-mohan-shak-duplicate-cleanup/r6_mohan_shak_duplicate_cleanup_v1_removed_rows.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T212325-codex-r6-mohan-shak-duplicate-cleanup-v1/checks/r6_mohan_shak_duplicate_cleanup_v1_assertions.out`
