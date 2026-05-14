# R6 Live Intake Rehydrate Calibration v1

Run id: `20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1`
Generated at UTC: `2026-05-11T16:00:48.419023+00:00`

## Result

- Live root status: `existing_live_root_not_overwritten` at `/tmp/ict-engine-direct-manipulation-row-intake`.
- Direct verifier status: `schema_ready_unscored` with return code `0`.
- Durable snapshots written: positives `73`, matched controls `73`.
- Direct pooled Wilson95 LCB: `0.950006246616`; pooled gate `true`.
- Sidecar broad-normal axis rows: `80`; sidecar axis gate `true`.
- Chronological split gate: `false`; heldout symbol gate: `false`; heldout venue gate: `false`.
- New confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Boundary

This run rehydrates the live tmp intake from versioned R6 snapshots and records durable copies in the run directory. It does not promote unmatched later sidecars, does not relax thresholds, and does not make a trade claim.
