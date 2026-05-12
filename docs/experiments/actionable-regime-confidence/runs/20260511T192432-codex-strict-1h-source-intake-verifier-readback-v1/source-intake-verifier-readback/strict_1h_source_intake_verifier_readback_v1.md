# Strict 1h Source Intake Verifier Readback v1

Run ID: `20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1`

This readback executes the verifier named by `strict_1h_next_source_intake_contract_v1` against the live intake root. It does not create intake rows or alter Current Cursor.

## Decision

`strict_1h_source_intake_verifier_readback_v1=blocked_missing_source_label_equivalence_files`

- Verifier return code: `2`.
- Verifier status: `blocked`; reason: `missing_required_files`.
- Missing required files: `2`.
- Live intake root exists: `false`; file count `0`.
- Contract target rows: `4`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Missing Files

- `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_rows.csv`
- `/tmp/ict-engine-source-label-equivalence-intake/source_label_equivalence_provenance.json`

## Contract Targets

- `XOM/Sideways` heldout_time requires `5` source-owned sessions.
- `UNH/Bear` calibration requires `7` source-owned sessions.
- `^DJI/Sideways` calibration requires `7` source-owned sessions.
- `AMD/Bear` calibration requires `10` source-owned sessions.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/source-intake-verifier-readback/strict_1h_source_intake_verifier_readback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T192432-codex-strict-1h-source-intake-verifier-readback-v1/checks/strict_1h_source_intake_verifier_readback_v1_assertions.out`
