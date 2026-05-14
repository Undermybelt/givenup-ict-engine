# R6 Direct Intake Reconstruction Preflight v1

- Run id: `20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1`
- Generated at UTC: `2026-05-11T16:01:11.695390+00:00`
- Canonical live intake exists: `true`.
- Direct verifier blocked on missing required files: `false`.
- Durable row snapshot files found: `12`.
- Durable row-generation / sidecar scripts found: `94`.
- Unique proposed sidecar positives from consolidation: `34`.
- What-if positives after sidecars: `91`.
- What-if min Wilson95 LCB after sidecars: `0.954180263735`.
- Pooled what-if Wilson95 pass: `true`.
- Provider/downstream commands all returned zero: `true`.
- Gate result: `r6_direct_intake_reconstruction_preflight_v1=active_cursor_root_missing_live_intake_missing_rehydrate_required`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This preflight does not rebuild the intake yet. It establishes the current blocker and the durable inputs available for the next locked rehydration slice.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1/r6-direct-intake-reconstruction-preflight/r6_direct_intake_reconstruction_preflight_v1.json`
- Snapshot inventory CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1/r6-direct-intake-reconstruction-preflight/r6_direct_intake_reconstruction_preflight_snapshot_files_v1.csv`
- Script inventory CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1/r6-direct-intake-reconstruction-preflight/r6_direct_intake_reconstruction_preflight_scripts_v1.csv`
- Command summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1/r6-direct-intake-reconstruction-preflight/r6_direct_intake_reconstruction_preflight_commands_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235303-codex-r6-direct-intake-reconstruction-preflight-v1/checks/r6_direct_intake_reconstruction_preflight_v1_assertions.out`
