# Direct Manipulation Source Scan v2

Run ID: `20260511T182601+0800-codex-direct-manipulation-source-scan-v2`

This scan targets the remaining direct `Manipulation` species gap: spoofing/layering, quote stuffing, pinging, bear raid, painting tape, and social/text pump-dump variants. It records public metadata only and does not download raw row files.

## Decision

`direct_manipulation_source_scan_v2=no_ready_matched_negative_source`

- Kaggle searches: `4`.
- Hugging Face searches: `5`.
- Candidate records summarized: `5`.
- Ready row-schema candidates: `0`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full direct species coverage: `false`.
- `update_goal`: `false`.

## Candidate Disposition

- `adamatractor/institutional-crypto-l2-orderbook-30lvl-1m-5m`: `blocked_positive_or_topic_only_no_matched_negatives`. Metadata has manipulation-like topic or positive labels, but no matched negative/control-row evidence.
- `praanj/limit-orderbook-data`: `control_only_not_direct_positive_source`. Metadata has L2/order-lifecycle or orderbook rows but no direct positive manipulation labels.
- `a53e93e57a1/maker-order-dataset-osaka-20210301`: `control_only_not_direct_positive_source`. Metadata has L2/order-lifecycle or orderbook rows but no direct positive manipulation labels.
- `Go3x3/pump_and_dump_dataset`: `blocked_positive_or_topic_only_no_matched_negatives`. HF metadata exposes pump/dump package files, but README has no schema detail and metadata does not show matched negative/control rows.
- `18667008`: `blocked_preprint_only_no_rows`. Zenodo record is a preprint/PDF record, not a row dataset with positive and matched negative controls.

## Why It Blocks

Board A needs direct positive rows plus matched normal controls and provenance. L2/orderbook data without positive labels is control-only. A pump/dump or spoofing topic hit without matched negatives remains positive-only or publication-only. None of the scanned candidates can be promoted into a direct `Manipulation` confidence gate.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2/direct-source-scan/direct_manipulation_source_scan_v2.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2/direct-source-scan/direct_manipulation_source_scan_v2_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T182601-codex-direct-manipulation-source-scan-v2/checks/direct_manipulation_source_scan_v2_assertions.out`

## Next

Acquire row-level positive plus matched-negative exports for at least one missing direct species, then run a direct calibration gate without lowering thresholds.
