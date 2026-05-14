# R6 Isolated Reconstruction Snapshot v56

- Run id: `20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56`
- Durable snapshot root: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake`
- Direct verifier: `schema_ready_unscored` returncode `0`.
- Rows: positives `73`, matched controls `73`, matched groups `70`, sidecar broad-normal controls `80`.
- Pooled Wilson95 min LCB: `0.950007992044`; pooled gate `true`.
- Chronological split gate: `false`; heldout symbol gate: `false`; heldout venue gate: `false`; direct species closed: `false`.
- Prior `234414` mixed-artifact readback: suffixed JSON `73/73`, legacy isolated folder `53/53`.
- Gate result: `r6_isolated_reconstruction_snapshot_v56=pooled_wilson95_passed_split_species_full_objective_still_blocked`.
- Accepted confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; external requests sent: `false`; trade usable: `false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/r6_isolated_reconstruction_snapshot_v56.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/r6_isolated_reconstruction_snapshot_v56.md`
- Positive rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake/positive_spoofing_layering_rows.csv`
- Matched controls: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake/matched_negative_normal_activity_rows.csv`
- Provenance: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake/provenance_manifest.json`
- Split metrics: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/r6_isolated_reconstruction_snapshot_v56_split_metrics.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/checks/r6_isolated_reconstruction_snapshot_v56_assertions.out`

## Next
Use this durable 73x73 snapshot as the reconstruction baseline for the next calibration rerun, but do not accept Board A: chronological/symbol/venue support and direct species coverage remain blocked, and R5/R3 blockers remain open.

