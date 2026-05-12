# Databento GC Metadata Disposition After 075426 v1

Run id: `20260512T075909+0800-codex-databento-gc-metadata-disposition-after-075426-v1`

Gate result: `databento_gc_metadata_disposition_after_075426_v1=batch_metadata_no_source_label_or_control_unlock`

## Scope

Read-only disposition of the Databento batch companion metadata under `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025` after the `075426` local-download arrival sweep. This packet checks whether `condition.json`, `manifest.json`, `metadata.json`, or `symbology.json` contain source-owned `MainRegimeV2`, source-confidence, matched-control, owner/export, direct-label, or order-lifecycle fields that could unlock Board A. It does not mutate target roots, derive labels from OHLCV, approve controls, run direct verifier, split calibration, canonical merge, selected-data AutoQuant, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Local root: `/Users/thrill3r/Downloads/Tomac/gc future 2021-2025`.
- `metadata.json` identifies Databento dataset `GLBX.MDP3`, schema `ohlcv-1m`, symbol `GC.FUT`, `stype_in=parent`, `stype_out=instrument_id`, CSV encoding, and download delivery.
- `manifest.json` contains five batch files: `condition.json`, `metadata.json`, `symbology.json`, `symbology.csv`, and `glbx-mdp3-20210106-20260105.ohlcv-1m.csv`, with Databento batch download URLs and SHA-256 hashes.
- `condition.json` is an availability calendar with fields `date`, `condition`, and `last_modified_date`.
- `symbology.json` maps futures symbols to Databento instrument ids with date ranges.
- Recursive key scan across the four JSON files found no `MainRegimeV2`, `main_regime_v2`, `source_confidence`, `matched_negative`, `matched_control`, `owner_export`, `direct_label`, `order_lifecycle`, `SPOOF`, or `FLIP` keys.

## Decision

The Databento companion metadata is real package provenance for raw OHLCV/symbology, but it is not source-owned `MainRegimeV2` label evidence and not R6 owner-export control evidence. It cannot fill `/tmp/ict-engine-source-panel-recency-extension`, `/tmp/ict-engine-native-subhour-source-label-intake`, or `/tmp/ict-engine-board-a-r6-owner-export-v1` under the current Board A contract.

Accepted rows added `0`; R6 owner/export unlock false; R5 recency unlock false; R3 native-subhour unlock false; valid required-root unlock false; source/control evidence acquired false; canonical merge false; downstream promotion rerun false; strict full objective false; trade usable false; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T075909+0800-codex-databento-gc-metadata-disposition-after-075426-v1/databento-gc-metadata-disposition-after-075426-v1/databento_gc_metadata_disposition_after_075426_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T075909+0800-codex-databento-gc-metadata-disposition-after-075426-v1/databento-gc-metadata-disposition-after-075426-v1/databento_gc_metadata_files_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T075909+0800-codex-databento-gc-metadata-disposition-after-075426-v1/checks/databento_gc_metadata_disposition_after_075426_v1_assertions.out`

## Next

Continue source/control acquisition only. Do not promote Databento batch metadata, symbology, or raw OHLCV as source-owned labels or matched controls.
