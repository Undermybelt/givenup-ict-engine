# R2/R3/R5 Source Intake Gap Readback v1

- Gate result: `r2_r3_r5_source_intake_gap_readback_v1=no_required_source_label_or_recency_rows_found`.
- Board hash before run: `d2e9e4b958414175046c68c981eb778dce365b6d5b701730143d52a90a493971`.
- Exact required filenames searched under `/tmp` and `Downloads`: `6`.
- Exact required file hits: `0`.
- Source-label equivalence verifier blocked: `true`.
- Native sub-hour intake root ready: `false`.
- Source-panel recency verifier blocked: `true`.
- Direct R6 root schema-ready/unscored: `true`.
- Ready intake roots: `1/4` (`direct_manipulation_row_intake`).
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Boundary

This is a readback-only slice for R2/R3/R5. It does not promote the local stock-regime dataset, VantMacro page text, OHLCV provider output, or any generated labels into source-owned MainRegimeV2 rows.

## Local Inventory

- Source-label equivalence root ready: `false`; missing `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json`.
- Native sub-hour root ready: `false`; missing `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json`.
- Recency-extension root ready: `false`; missing `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json`.
- The local stock-market-regimes panel is still the known `2000-01-03..2026-01-30` source panel, not a post-cutoff R5 extension.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_readback_v1.json`
- Required-file hits CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_required_file_hits_v1.csv`
- Candidate inventory CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_candidate_inventory_v1.csv`
- Intake roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/r2-r3-r5-source-intake-gap-readback/r2_r3_r5_source_intake_gap_roots_v1.csv`
- Verifier command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T211112-codex-r2-r3-r5-source-intake-gap-readback-v1/checks/r2_r3_r5_source_intake_gap_readback_v1_assertions.out`

## Next

Acquire source-owned or owner-approved R2/R3/R5 row exports and provenance, populate the exact fail-closed intake roots, then rerun source-label and recency verifiers before another completion audit.
