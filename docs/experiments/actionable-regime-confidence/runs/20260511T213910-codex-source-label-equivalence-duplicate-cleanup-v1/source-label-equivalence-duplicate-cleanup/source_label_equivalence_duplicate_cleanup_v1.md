# Source Label Equivalence Duplicate Cleanup v1

- Decision: `source_label_equivalence_duplicate_cleanup_v1=duplicates_or_malformed_rows_removed_schema_ready_unscored`.
- Rows before: `248441`.
- Duplicate rows removed: `1`.
- Rows after: `248440`.
- After label counts: `{'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`.
- Verifier status: `schema_ready_unscored`; return code `0`.
- Accepted confidence rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1/source-label-equivalence-duplicate-cleanup/source_label_equivalence_duplicate_cleanup_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1/source-label-equivalence-duplicate-cleanup/source_label_equivalence_duplicate_cleanup_v1.md`
- Removed rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1/source-label-equivalence-duplicate-cleanup/source_label_equivalence_duplicate_rows_removed_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T213910-codex-source-label-equivalence-duplicate-cleanup-v1/checks/source_label_equivalence_duplicate_cleanup_v1_assertions.out`
