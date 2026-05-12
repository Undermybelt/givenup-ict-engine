# R6 Live Intake Rehydration v1

- Run id: `20260511T235910-codex-r6-live-intake-rehydration-v1`
- Live intake root: `/tmp/ict-engine-direct-manipulation-row-intake`
- Source snapshot: `docs/experiments/actionable-regime-confidence/runs/20260511T235726-codex-r6-isolated-reconstruction-snapshot-v56/r6-isolated-reconstruction-snapshot-v56/isolated-direct-intake`
- Mutation: `skipped_existing_live_schema_ready`.
- Live verifier status: `schema_ready_unscored` returncode `0`.
- Rows: positives `73`, matched controls `73`, matched groups `70`.
- Sidecar broad-normal controls: `80`.
- Pooled Wilson95 min LCB: `0.950006246616`; pooled gate `true`.
- Chronological split gate: `false`; heldout symbol gate: `false`; heldout venue gate: `false`.
- Direct species closed: `false`.
- Gate result: `r6_live_intake_rehydration_v1=live_schema_ready_pooled95_passed_split_species_full_objective_still_blocked`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/r6_live_intake_rehydration_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/r6_live_intake_rehydration_v1.md`
- Live positive rows snapshot: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/positive_spoofing_layering_rows.csv`
- Live matched controls snapshot: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/matched_negative_normal_activity_rows.csv`
- Live provenance snapshot: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/provenance_manifest.json`
- Split metrics: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/r6-live-intake-rehydration/r6_live_intake_rehydration_split_metrics_v1.csv`
- Live verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/command-output/live_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-live-intake-rehydration-v1/checks/r6_live_intake_rehydration_v1_assertions.out`

## Next
Keep R6 blocked for strict completion: live schema is restored and pooled Wilson95 passes, but chronological/symbol/venue split support and non-spoofing direct species coverage remain blocked; keep R5 source-owner recency blocked.
