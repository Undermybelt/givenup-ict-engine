# R6 Zhao/Skudder CFTC Row Uplift v1

Decision: `r6_zhao_skudder_cftc_row_uplift_v1=rows_added_schema_ready_calibration_still_blocked`.

Result:
- Positive rows added/materialized by this artifact: `7`; matched controls added/materialized: `7`.
- Rows newly appended during this rerun: positives `0`, matched controls `0`.
- Direct intake after run: positives `41`, matched negatives `41`, matched groups `40`.
- Unique positive dates/symbols/venues: `35` / `18` / `7`.
- Wilson95 LCB positive/negative/min: `0.914332` / `0.914332` / `0.914332`.
- Verifier status: `schema_ready_unscored`.
- Broad normal sample: `false`; direct species coverage still incomplete.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- External official CFTC PDF requests sent: `true`; raw data committed: `false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; trade usable: `false`.

Source Boundary:
- Raw PDFs/text stay under `/tmp/ict-engine-r6-zhao-skudder-cftc-row-uplift-v1`; repo artifacts record only URLs, hashes, summaries, and derived row assertions.
- Same-complaint genuine legs are matched schema/control seeds. They do not satisfy the broad normal-market calibration-control requirement.

Gates:

| Gate | Observed | Required | Pass |
|---|---|---|---:|
| `verifier_schema_ready` | `schema_ready_unscored` | `schema_ready_unscored` | `true` |
| `positive_rows_materialized` | `7` | `7` | `true` |
| `matched_negative_rows_materialized` | `7` | `7` | `true` |
| `positive_support` | `41` | `>=50` | `false` |
| `negative_support` | `41` | `>=50` | `false` |
| `orphan_groups` | `0` | `0` | `true` |
| `chronological_split` | `35` | `>=2 dates` | `true` |
| `heldout_symbol_or_venue` | `symbols=18;venues=7` | `symbol>=2 or venue>=2` | `true` |
| `wilson95_lcb` | `0.914332` | `>=0.95` | `false` |
| `broad_normal_sample` | `False` | `True` | `false` |
| `direct_species_coverage` | `False` | `True` | `false` |

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/r6-zhao-skudder-cftc-row-uplift/r6_zhao_skudder_cftc_row_uplift_v1.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/r6-zhao-skudder-cftc-row-uplift/r6_zhao_skudder_cftc_row_uplift_v1_gates.csv`
- Additions CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/r6-zhao-skudder-cftc-row-uplift/r6_zhao_skudder_cftc_row_uplift_v1_additions.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213113-codex-r6-zhao-skudder-cftc-row-uplift-v1/checks/r6_zhao_skudder_cftc_row_uplift_v1_assertions.out`
