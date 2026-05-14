# R6 Concurrency Readback v1

Run ID: `20260511T221713+0800-codex-r6-concurrency-readback-v1`

## Boundary

- Read-only coordination artifact.
- Did not edit `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`.
- Did not modify `/tmp/ict-engine-direct-manipulation-row-intake`.
- Did not edit, rename, reorder, or clean up any existing run directory.
- `update_goal=false`.

## Observed State

- Board hash after concurrent V51 writeback: `9ca41e6082e471418ded3b782d94cf5a47ea0ce3`.
- Current Cursor points at `20260511T221253+0800-codex-current-goal-completion-audit-v51-after-r6-support-extension`.
- Current Cursor records R6 direct as `60/60`, matched groups `59`, Wilson95 min LCB `0.939828`, support closed, broad-normal `false`, direct species `false`.
- The same plan tail also has a supplemental `20260511T221300-codex-r6-direct-calibration-gate-v1` section over the current live `57/57` intake.
- Live read-only verifier at this readback observed `/tmp/ict-engine-direct-manipulation-row-intake` as `57/57`, matched groups `56`.
- `/tmp/ict-engine-direct-manipulation-row-intake` files had mtime `May 11 22:16:13 2026`, after the V51 artifact timestamp.

## Interpretation

The Board A plan already carries the V51 cursor update, while the live shared R6 intake has moved to the later `57/57` cleanup/calibration state. Treat `60/60` as the V51 cursor snapshot, not the current mutable `/tmp` state.

The strict objective remains blocked:

- source-confidence accepted labels: `0/4`
- R5 recency verifier: `blocked/missing_required_files`
- R3 native-subhour root: missing
- R6 pooled Wilson95: below `0.95`
- R6 chronological and heldout splits: fail-closed per `221300`
- broad normal-market controls: absent
- direct species coverage: incomplete

## Next Safe Action

Avoid mutating the shared direct intake unless taking a fresh lock and re-reading the plan/hash first. The non-overlapping evidence path is independent broad normal-market order-lifecycle controls or owner-approved missing-species rows; more duplicate same-complaint CFTC rows should not be treated as broad normal controls.
