# R6 Order Lifecycle Local Scan Readback After 070820 v1

Run id: `20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1`

Gate result: `r6_order_lifecycle_local_scan_readback_after_070820_v1=no_required_r6_owner_export_files_no_unlock_no_downstream`

## Scope

This packet settles the partial local R6 order-lifecycle file scan at `20260512T070820+0800-codex-r6-order-lifecycle-local-file-scan-after-070737-v1`. It profiles the existing candidate file list only. It does not mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, copy local files into a target root, approve public same-exhibit controls, run direct verifier, run split calibration, run canonical merge, run provider / Auto-Quant promotion, run filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Source candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T070820+0800-codex-r6-order-lifecycle-local-file-scan-after-070737-v1/command-output/local_r6_order_lifecycle_candidate_files.csv`
- Candidate rows: `280`
- Unique paths: `270`
- Required R6 file names found: `0`

Classification counts:

| Classification | Count | Disposition |
|---|---:|---|
| `source_code_false_positive` | 200 | Code paths only; not source-owned data |
| `other_false_positive` | 58 | Not a required root unlock |
| `tomac_symbology_context` | 20 | Symbology context only; not order-lifecycle rows |
| `historical_regime_context` | 1 | Historical regime context only; not R6 controls |
| `indicator_or_script_context` | 1 | Indicator/script context only; not verifier-native owner export |

## Decision

The local scan does not produce verifier-native R6 owner-export files. It finds Tomac symbology, old regime context, an ICT script/context file, and many source-code false positives from local repos and package directories. No `direct_manipulation_positive_rows.csv`, `direct_manipulation_matched_controls.csv`, or `direct_manipulation_provenance.json` file was found, and no source-owned normal-control rows were acquired.

Accounting: accepted rows added `0`, R6 owner/export unlock false, R5 recency unlock false, R3 native-subhour unlock false, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1/r6-order-lifecycle-local-scan-readback-after-070820-v1/r6_order_lifecycle_local_scan_readback_after_070820_v1.json`
- Classified candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1/r6-order-lifecycle-local-scan-readback-after-070820-v1/r6_order_lifecycle_local_scan_readback_after_070820_v1.csv`
- Profile stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1/command-output/profile_070820_local_r6_scan.stdout`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T071107+0800-codex-r6-order-lifecycle-local-scan-readback-after-070820-v1/checks/r6_order_lifecycle_local_scan_readback_after_070820_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider / Auto-Quant selected-data research, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
