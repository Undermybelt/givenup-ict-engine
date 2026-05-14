# US Panel Source Label Duplicate Cleanup v1

- Decision: `us_panel_source_label_duplicate_cleanup_v1=duplicate_extension_removed_schema_ready_unscored`.
- Rows before cleanup: `493445`.
- Rows after cleanup: `248440`.
- Rows removed: `245005`.
- Labels after cleanup: `{'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`.
- Source owners after cleanup: `{'ahaanverma00': 3435, 'source-owned-stock-market-regimes-2000-2026': 245005}`.
- Shared rows hash after cleanup: `915d8148a468798600d4357a60f6c322bd19f421ad7ed01632a5e1c00be2937f`.
- Verifier status: `schema_ready_unscored`; return code `0`.
- Removed the oversized generated repo snapshot and left a small `.removed.txt` marker.
- Accepted confidence rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Interpretation:
The source-label equivalence root keeps the first US source-panel extension plus NIFTY rows, so all four MainRegimeV2 price labels remain present. The duplicate rerun block is removed. This cleanup does not score confidence and does not close native sub-hour, recency, or R6 direct gates.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1/us-panel-source-label-duplicate-cleanup/us_panel_source_label_duplicate_cleanup_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1/us-panel-source-label-duplicate-cleanup/us_panel_source_label_duplicate_cleanup_v1.md`
- Counts CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1/us-panel-source-label-duplicate-cleanup/us_panel_source_label_duplicate_cleanup_counts_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213906-codex-us-panel-source-label-duplicate-cleanup-v1/checks/us_panel_source_label_duplicate_cleanup_v1_assertions.out`
