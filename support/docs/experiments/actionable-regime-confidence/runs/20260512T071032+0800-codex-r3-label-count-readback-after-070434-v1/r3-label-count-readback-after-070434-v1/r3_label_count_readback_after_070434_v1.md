# R3 Label Count Readback After 070434 v1

Run id: `20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1`

Gate result: `r3_label_count_readback_after_070434_v1=header_aware_counts_no_crisis_tsie_quarantined_no_unlock`

## Scope

This packet materializes the header-aware label count for `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv` after the `070434` arrival poll. It reads the existing R3 TSIE-derived target root only. It does not mutate required roots, approve TSIE labels, run direct verifier, run split calibration, run canonical merge, run provider / Auto-Quant selected-data promotion, run filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Rows path: `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
- Rows SHA-256: `72406e48b000f91ed2b3c3e132651537339afb2a8ed2e3ce43b5007abf38f62f`
- File lines including header: `5,032,904`
- Data rows: `5,032,903`
- Header includes `main_regime_v2_label`.
- Header-aware label counts:
  - `Bear`: `1,435,764`
  - `Bull`: `1,435,055`
  - `Sideways`: `2,162,084`
  - `Crisis`: `0`
- Provenance source run: `20260512T063155+0800-codex-r3-tsie-native-subhour-intake-materialization-v1`
- Provenance limitations still include: `Crisis has no direct TSIE source taxonomy class`, trap labels are fail-closed abstain, canonical merge not run, and downstream chain not rerun.

## Decision

The R3 native-subhour root remains non-promoting. It supplies a large TSIE-derived Bear/Bull/Sideways row set, but no `Crisis` rows, no verifier-native accepted `MainRegimeV2` source export, and no valid required-root unlock.

Accepted rows added `0`; R3 native-subhour unlock false; R5 recency unlock false; R6 owner/export unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1/r3-label-count-readback-after-070434-v1/r3_label_count_readback_after_070434_v1.json`
- Decision CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1/r3-label-count-readback-after-070434-v1/r3_label_count_readback_after_070434_v1.csv`
- Raw label count TSV: `docs/experiments/actionable-regime-confidence/runs/20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1/command-output/r3_main_regime_v2_label_counts_header_aware.tsv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T071032+0800-codex-r3-label-count-readback-after-070434-v1/checks/r3_label_count_readback_after_070434_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider / Auto-Quant selected-data research, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
