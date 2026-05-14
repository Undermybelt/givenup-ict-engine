# Source Root Presence Readback v1

Run id: `20260512T010855-codex-source-root-presence-readback-v1`

## Result

- Decision: `blocked_source_label_schema_ready_unscored_no_r6_r3_r5`
- R6 source-owned controls acquired now: `false`
- Source-label equivalence schema ready: `true`
- Source-label confidence gate now: `false`
- R3 native sub-hour rows acquired now: `false`
- R5 panel-recency extension rows acquired now: `false`
- Same-exhibit FLIP approval acquired now: `false`
- Canonical merge allowed now: `false`
- Downstream rerun allowed now: `false`
- Strict full objective achieved: `false`

## Roots

### r6_owner_export

- Root: `/tmp/ict-engine-board-a-r6-owner-export-v1`
- Root exists: `false`
- File count: `0`
- Required files complete: `false`
- Missing required files: `positive_spoofing_layering_rows.csv, matched_negative_normal_activity_rows.csv, provenance_manifest.json`

### source_label_equivalence

- Root: `/tmp/ict-engine-source-label-equivalence-intake`
- Root exists: `true`
- File count: `2`
- Required files complete: `true`
- Missing required files: ``

### r3_native_subhour

- Root: `/tmp/ict-engine-native-subhour-source-label-intake`
- Root exists: `false`
- File count: `0`
- Required files complete: `false`
- Missing required files: `native_subhour_source_label_rows.csv, native_subhour_source_label_provenance.json`

### r5_panel_recency_extension

- Root: `/tmp/ict-engine-source-panel-recency-extension`
- Root exists: `false`
- File count: `0`
- Required files complete: `false`
- Missing required files: `stock_market_regimes_2026_extension.csv, source_panel_recency_provenance.json`

