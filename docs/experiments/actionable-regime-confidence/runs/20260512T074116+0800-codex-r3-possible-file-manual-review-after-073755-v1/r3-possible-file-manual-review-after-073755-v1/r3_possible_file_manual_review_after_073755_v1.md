# R3 Possible File Manual Review After 073755 v1

Run id: `20260512T074116+0800-codex-r3-possible-file-manual-review-after-073755-v1`

Gate result: `r3_possible_file_manual_review_after_073755_v1=tsie_existing_native_subhour_root_non_promoting_no_unlock`

## Scope

Manual settlement of the `073755` local sweep gate `possible_r3_files_present_requires_manual_review`.
This packet reviews the two unlock-like local hits and does not mutate R3/R5/R6 target roots, run direct verifier, run split calibration, run canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- `073755` reported `recent_required_filename_count=2` and `recent_unlock_like_count=2`.
- The two paths are the same filesystem-backed candidate observed through `/tmp` and `/private/tmp`:
  - `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
  - `/private/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
- The target root contains:
  - `native_subhour_source_label_rows.csv`
  - `native_subhour_source_label_provenance.json`
- Provenance dataset: `sujinwo/tsie-market-regime-dataset`.
- Provenance run id: `20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1`.
- Provenance row count: `5032903`.
- Provenance label scope: accepted mapping labels are `Bear`, `Bull`, and `Sideways`.
- Provenance limitations include: `Crisis has no direct TSIE source taxonomy class`, trap labels are fail-closed abstain, canonical merge was not run, and downstream provider/AutoQuant/Pre-Bayes/BBN/CatBoost/execution-tree was not rerun.

## Decision

The `073755` possible R3 file is not a new verifier-native Crisis-capable `MainRegimeV2` source export. It is the already-known TSIE-derived native-subhour root and remains quarantined / non-promoting under the current Board A contract.

Accepted rows added `0`; R3 native-subhour unlock false; R5 recency unlock false; R6 owner/export unlock false; valid required-root unlock false; source/control evidence acquired false; direct verifier run false; split calibration run false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Next

Continue source/control acquisition only. Do not run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion until explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export exists.
