# Strict Objective Acquisition Contract v1

Decision: `strict_objective_acquisition_contract_v1=contracts_ready_objective_still_blocked`

- Contract rows: `5`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; raw data committed: `false`.

## Contract Rows

| Requirement | Package | Required files | Acceptance check |
|---|---|---|---|
| R2 | `other_market_source_label_equivalence` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` | source_label_equivalence verifier accepts rows and a completion audit shows other-market/source-label equivalence is true with accepted_rows_added > 0 |
| R3 | `native_subhour_source_labels` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` | native sub-hour verifier reports ready_native_subhour_source_owned_label_sources > 0 and native_subhour_source_overlap_closed=true |
| R4 | `strict_1h_exact_target_source_rows` | `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv;/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json` | strict_1h_source_intake_verifier reports live intake files present and strict_1h_target_exact_source_search finds ready exact-target source-owned rows |
| R5 | `strict_1h_recency_tail_repair` | `source_panel_recency_tail_rows.csv;source_panel_recency_tail_provenance.json` | local target counts show rows_after_2026_01_30 > 0 for each strict target and completion audit clears the recency-tail row |
| R6 | `direct_manipulation_full_species_rows` | `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv;/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv;/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json` | direct_manipulation_intake verifier finds all required files, missing_files=0, and full_direct_manipulation_species_coverage=true |

## Fail-Closed Rules

- Do not promote HMM, KMeans, classifier, future-return, generated, synthetic, or OHLCV-only labels.
- Do not duplicate existing source-panel rows as new strict `1h` support.
- Do not use daily/monthly labels projected into sub-hour windows.
- Do not use pump/dump-only rows to close spoofing/layering or full direct `Manipulation` species coverage.

## Next Exact Acquisition Targets

1. Fill `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv` plus provenance for the four strict `1h` target cells.
2. Obtain a native sub-hour source-owned label package, not a projection from daily/monthly regimes.
3. Obtain direct spoofing/layering positives plus matched normal controls and provenance.
4. Add recency-tail source rows after `2026-01-30` for XOM/Sideways, UNH/Bear, ^DJI/Sideways, and AMD/Bear.
