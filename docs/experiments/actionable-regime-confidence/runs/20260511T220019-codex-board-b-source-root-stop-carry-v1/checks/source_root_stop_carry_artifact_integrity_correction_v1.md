# SourceRootStopCarryV1 Artifact Integrity Correction v1

Readback time: `2026-05-11T22:10:53+0800`

Run id: `20260511T220019+0800-codex-board-b-source-root-stop-carry-v1`

## Decision

- Current primary report: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/branch-rc-spa/source_root_stop_carry_rc_spa_report_v1.md`
- Current assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/checks/source_root_stop_carry_v1_assertions.out`
- Current fail-closed summary: `docs/experiments/actionable-regime-confidence/runs/20260511T220019-codex-board-b-source-root-stop-carry-v1/ict-engine-fail-closed/source_root_stop_carry_fail_closed_summary_v1.md`

The primary `220019` artifacts currently on disk supersede the stale `3/4` near-miss interpretation for this run root.

## Verified Values

- Stable profit score: `78.7013`
- Variant rows: `6,839`
- Selected price-root rows: `4,083`
- Selected roots: `Bull=2388`, `Bear=376`, `Sideways=1271`, `Crisis=48`, `Manipulation(scoped)=13535`
- Price-root paths passed: `0/4`
- Scoped Manipulation component pass consumed: `true`
- Hard gate: `fail:required_root_branch_hard_gates_failed`
- Downstream: `not_started:blocked_by_branch_rc_spa_hard_gates`

## Integrity Result

Use the current primary report/assertions as the final `220019` state unless a clean isolated rerun intentionally recreates the stronger packet.

Do not start Pre-Bayes, BBN, CatBoost/path-ranker, or execution tree consumption from this run, because Bull, Bear, Sideways, and Crisis did not all pass unchanged RC-SPA gates.
