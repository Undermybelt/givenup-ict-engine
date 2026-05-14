# No-Send Request Draft: VantMacro Source-Label Equivalence Rows

Purpose: Board A needs source-owned or owner-approved rows for R2/R5 source-label equivalence and recency extension.

Requested deliverables:
1. `source_label_equivalence_rows.csv` using the Board A required schema.
2. `source_label_equivalence_provenance.json` with source owner, approval/export date, export identity, hashes, redaction notes, and a non-proxy attestation.

Required schema fields:
- `source_owner`
- `source_report_or_dataset`
- `source_pull_date`
- `market_family`
- `symbol`
- `source_symbol`
- `equivalence_policy`
- `event_species`
- `timestamp_or_date`
- `timeframe`
- `main_regime_v2_label`
- `direct_label`
- `matched_negative_group_id`
- `split_role`
- `source_row_id`
- `provenance_hash`

Requested source-specific content:
- Row-level VantMacro regime labels or owner-approved export/crosswalk.
- Historical and current rows covering 2026 recency where available.
- Explicit mapping to `MainRegimeV2` labels (`Bull`, `Bear`, `Sideways`, `Crisis`) or an owner-approved equivalence policy.
- Split-role support for train/calibration/heldout_time/heldout_market/test.
- Stable row ids and provenance hashes.

Boundary: this draft was not sent. No rows were acquired, no account was used, and no source-label equivalence intake file was created.
