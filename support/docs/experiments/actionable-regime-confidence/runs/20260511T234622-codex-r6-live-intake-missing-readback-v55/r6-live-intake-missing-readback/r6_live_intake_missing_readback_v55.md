# R6 Live Intake Missing Readback v55

- Run id: `20260511T234622-codex-r6-live-intake-missing-readback-v55`
- Generated at UTC: `2026-05-11T15:47:20.785007+00:00`
- Live intake root: `/tmp/ict-engine-direct-manipulation-row-intake`
- Live intake exists: `false`
- Verifier status: `blocked`
- Verifier reason: `missing_required_files`
- Sarao proposed positives preserved: `6`
- Nowak/Smith proposed positives preserved: `6`
- What-if positives after both sidecars: `69`
- What-if min Wilson95 LCB after both sidecars: `0.947260905856`
- Additional positives still needed after both sidecars: `4`
- Gate result: `current_goal_completion_audit_v55=shared_r6_intake_missing_sidecar_candidates_preserved`
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234622-codex-r6-live-intake-missing-readback-v55/r6-live-intake-missing-readback/r6_live_intake_missing_readback_v55.json`
- Gate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234622-codex-r6-live-intake-missing-readback-v55/r6-live-intake-missing-readback/r6_live_intake_missing_readback_v55_gates.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T234622-codex-r6-live-intake-missing-readback-v55/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234622-codex-r6-live-intake-missing-readback-v55/checks/r6_live_intake_missing_readback_v55_assertions.out`

## Next

Under a fresh shared-intake lock, restore or reconstruct the R6 intake from durable row-uplift scripts/provenance, then decide whether to append Sarao and Nowak/Smith positives with matched controls; even if all current sidecars are accepted, source at least four more all-correct positive direct rows and rerun sidecar calibration plus chronological/symbol/venue split gates.
