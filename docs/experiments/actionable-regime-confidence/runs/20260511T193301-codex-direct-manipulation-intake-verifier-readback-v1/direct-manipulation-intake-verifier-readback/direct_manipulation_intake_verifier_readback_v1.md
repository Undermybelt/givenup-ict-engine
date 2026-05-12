# Direct Manipulation Intake Verifier Readback v1

Run ID: `20260511T193301+0800-codex-direct-manipulation-intake-verifier-readback-v1`

This executes the existing `151950` direct Manipulation row-intake verifier against the live `/tmp` intake root. It does not create source rows or matched controls.

## Decision

`direct_manipulation_intake_verifier_readback_v1=blocked_missing_direct_intake_files`

- Intake root: `/tmp/ict-engine-direct-manipulation-row-intake`.
- Intake root exists: `false`.
- Verifier return code: `2`.
- Verifier status: `blocked`.
- Verifier reason: `missing_required_files`.
- Missing required files: `3`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Direct species coverage closed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Missing Files

- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/direct-manipulation-intake-verifier-readback/direct_manipulation_intake_verifier_readback_v1.json`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T193301-codex-direct-manipulation-intake-verifier-readback-v1/checks/direct_manipulation_intake_verifier_readback_v1_assertions.out`
