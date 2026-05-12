# R3 Target Cell Check Against Source-Label Root v1

Run id: `20260512T012000-codex-r3-target-cell-check-against-source-label-root-v1`
Gate result: `r3_target_cell_check_against_source_label_root_v1=source_label_root_has_no_native_subhour_target_rows`

This read-only check tests whether the live source-label equivalence root can satisfy the separate R3 native 15m/30m target cells.

| Symbol | Required Timeframe | Source Rows For Symbol | Source Timeframes Present | Exact Native Rows | Latest Source Date | Post-Cutoff Exact Native Rows | R3 Satisfied |
|---|---:|---:|---|---:|---|---:|---|
| AAPL | 15m | 6559 | 1d | 0 | 2026-01-30 | 0 | False |
| AAPL | 30m | 6559 | 1d | 0 | 2026-01-30 | 0 | False |
| ^IXIC | 15m | 6559 | 1d | 0 | 2026-01-30 | 0 | False |
| ^IXIC | 30m | 6559 | 1d | 0 | 2026-01-30 | 0 | False |

Result:
- Source-label root present: `True`.
- R3 native root present with required files: `False`.
- All R3 targets satisfied: `False`.
- The live source-label root contains daily source-panel labels for target symbols, not source-native 15m/30m labels.
- No rows were copied into the R3 root, no thresholds were relaxed, and no downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree promotion was run.

Next:
- Keep R3 fail-closed until exact native sub-hour source-label rows and provenance arrive under `/tmp/ict-engine-native-subhour-source-label-intake`.
