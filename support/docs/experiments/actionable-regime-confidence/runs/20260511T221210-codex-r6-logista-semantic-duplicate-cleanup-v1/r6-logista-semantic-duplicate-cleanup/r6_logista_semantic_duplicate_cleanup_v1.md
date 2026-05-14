# R6 Logista Semantic Duplicate Cleanup v1

- Decision: `r6_logista_semantic_duplicate_cleanup_v1=duplicates_removed_support_ok_confidence_still_blocked`.
- Removed duplicate Logista rows: positives `3`, matched controls `3`.
- Direct intake after cleanup: positives `57`, matched negatives `57`, matched groups `56`.
- Wilson95 LCB positive/negative/min: `0.936861` / `0.936861` / `0.936861`.
- `50/50` support gate: `true`.
- Broad normal sample: `false`; controls remain same-complaint genuine-order schema seeds.
- Direct species coverage closed: `false`.
- Gate result: `r6_logista_semantic_duplicate_cleanup_v1=duplicates_removed_support_ok_confidence_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Boundary

This run removes only semantic duplicates of Logista/Serotta examples. It keeps the canonical repaired Logista rows, the Roman/Banoczay rows, and the active Vorley/Franko rows. It does not promote same-event genuine-order controls into broad normal-market controls.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/r6-logista-semantic-duplicate-cleanup/r6_logista_semantic_duplicate_cleanup_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/r6-logista-semantic-duplicate-cleanup/r6_logista_semantic_duplicate_cleanup_v1.md`
- Removed rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/r6-logista-semantic-duplicate-cleanup/r6_logista_semantic_duplicate_cleanup_removed_rows_v1.csv`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/r6-logista-semantic-duplicate-cleanup/r6_logista_semantic_duplicate_cleanup_gates_v1.csv`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T221210-codex-r6-logista-semantic-duplicate-cleanup-v1/checks/r6_logista_semantic_duplicate_cleanup_v1_assertions.out`
