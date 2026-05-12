# Direct Manipulation Local Intake Probe v1

Run ID: `20260511T181211+0800-codex-direct-manipulation-local-intake-probe-v1`

Read-only local probe for spoofing/layering direct Manipulation intake rows.

## Result

- Candidate files found: `0`.
- Required files missing: `3/3`.
- Verifier status: `blocked` / `missing_required_files`.
- Accepted direct rows added: `0`; new confidence gate: `false`.
- Gate result: `direct_manipulation_local_intake_probe_v1=missing_required_files`.
- Full objective achieved: `false`; `update_goal=false`.

## Missing Required Files

- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

## Next

Place source-owned positive spoofing/layering rows, matched normal controls, and provenance under /tmp/ict-engine-direct-manipulation-row-intake, then rerun the verifier.
