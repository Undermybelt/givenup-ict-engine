# Source Label Intake Race Repair v1

- Decision: `source_label_intake_race_repair_v1=malformed_row_removed_schema_ready_unscored_strict_blocked`.
- Rows before repair: `248440`.
- Invalid/truncated rows removed: `0`.
- Rows after repair: `248440`.
- Repaired label counts: `{'Bear': 54939, 'Bull': 104979, 'Crisis': 30623, 'Sideways': 57899}`.
- Repaired split counts: `{'calibration': 148976, 'heldout_market': 26236, 'heldout_time': 45384, 'test': 27844}`.
- Source-label verifier: `schema_ready_unscored`; return code `0`.
- Source-panel recency verifier: `blocked` / `missing_required_files`.
- Native sub-hour root exists: `False`.
- Direct R6 verifier: `schema_ready_unscored` with positives `41`, matched negatives `41`, matched groups `40`, Wilson95 min LCB `0.914332`.
- R6 support/Wilson/broad-normal/direct-species gates remain blocked.
- Accepted confidence rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/source-label-intake-race-repair/source_label_intake_race_repair_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/source-label-intake-race-repair/source_label_intake_race_repair_v1.md`
- Invalid rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/source-label-intake-race-repair/source_label_equivalence_invalid_rows_removed_v1.csv`
- Repaired provenance copy: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/source-label-intake-race-repair/source_label_equivalence_provenance_repaired.json`
- Previous provenance copy: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/source-label-intake-race-repair/source_label_equivalence_previous_provenance_v1.json`
- Source-label verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/command-output/source_label_equivalence_verifier.stdout.txt`
- Source-panel verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/command-output/source_panel_recency_verifier.stdout.txt`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/command-output/direct_manipulation_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T214406-codex-source-label-intake-race-repair-v1/checks/source_label_intake_race_repair_v1_assertions.out`
