# Concurrency Safe Intake Snapshot v1

- Gate result: `concurrency_safe_intake_snapshot_v1=local_snapshot_only_no_new_rows`.
- Board hash before snapshot: `0db82c211c87672d3121590c164b33d09a36e1613792ed908e73c5b94252c58a`.
- Current cursor last loop: `20260511T210744+0800-codex-r6-mohan-additional-row-uplift-v1`.
- Current board state: `blocked`.
- Ready intake roots by file presence: `1/4`.
- Active/empty latest run directories: `3`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Intake Roots

| Root | Present | Ready | Missing |
|---|---:|---:|---|
| `R2_R4_source_label_equivalence` | `False` | `False` | `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json` |
| `R3_native_subhour_source_label` | `False` | `False` | `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json` |
| `R5_source_panel_recency_extension` | `False` | `False` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |
| `R6_direct_manipulation_row_intake` | `True` | `True` | `` |

## Verifier Readbacks

| Verifier | Status | Return Code |
|---|---|---:|
| `R2_R4_source_label_equivalence` | `blocked` | `2` |
| `R5_source_panel_recency_extension` | `blocked` | `2` |
| `R6_direct_manipulation_row_intake` | `schema_ready_unscored` | `0` |

## Active Or Empty Run Directories

- `20260511T211030-codex-current-goal-completion-audit-v40-after-mohan-uplift`
- `20260511T211032-codex-r6-mohan-complaint-expansion-gate-v1`
- `20260511T211050-codex-r6-current-live-intake-calibration-readback-v1`

## Boundary

This is a local-only coordination snapshot. It does not register or rewrite another agent's run, does not update the Current Cursor, and does not perform source acquisition.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T210950-codex-concurrency-safe-intake-snapshot-v1/concurrency-safe-intake-snapshot/concurrency_safe_intake_snapshot_v1.json`
- Roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210950-codex-concurrency-safe-intake-snapshot-v1/concurrency-safe-intake-snapshot/concurrency_safe_intake_snapshot_v1_roots.csv`
- Run-dir CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210950-codex-concurrency-safe-intake-snapshot-v1/concurrency-safe-intake-snapshot/concurrency_safe_intake_snapshot_v1_run_dirs.csv`
- Verifier CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T210950-codex-concurrency-safe-intake-snapshot-v1/concurrency-safe-intake-snapshot/concurrency_safe_intake_snapshot_v1_verifiers.csv`
