# Structural Feedback Branch Preservation Fix v1

Run id: `20260512T103057+0800-codex-structural-feedback-branch-preservation-fix-v1`

Mode: `runtime_surface_fix_non_promoting`

## Scope

This packet follows the `101314` diagnostic. It fixes only the `workflow-status --phase structural-feedback` surface so it preserves the same exact structural recommended path already visible in:

- `workflow-status --phase structural-recommended-path-bundle`
- `workflow-status --phase execution-candidate`
- full `workflow-status --agent` `latest_structural_execution_candidate`

It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not mutate canonical intake, does not promote Auto-Quant, BBN/CatBoost/path-ranking, structural feedback, or execution-tree output, does not make a trade claim, does not mark the objective complete, and does not call `update_goal`.

## Code Change

- `src/application/orchestration/workflow_status.rs`
  - Added `structural_feedback_template_value_from_recommended_path_bundle(...)`.
  - Kept `structural-feedback-template` and `structural-feedback-template-generic` as the generic template surface.
  - Routed `structural-feedback` through the exact `structural-recommended-path-bundle` when that bundle exists.
  - Added regression test `workflow_status_phase_structural_feedback_preserves_recommended_branch_path`.

## Runtime Evidence

State replayed:

```text
/tmp/ict-engine-20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1-state
```

Symbol:

```text
SRC_ROOT_CARRY_LONG_220646
```

Exact branch path:

```text
Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12
```

Command exits:

- `00_structural_recommended_path_bundle.exit=0`
- `01_structural_feedback.exit=0`
- `02_execution_candidate.exit=0`
- `03_workflow_full.exit=0`

Observed branch preservation after the fix:

- `structural-recommended-path-bundle.path_id` equals the exact branch path.
- `structural-feedback.path_id` equals the exact branch path.
- `structural-feedback.source_phase=structural-recommended-path-bundle`.
- `structural-feedback.generic_template_path_id=path:scenario:SRC_ROOT_CARRY_LONG_220646:belief_regime_node:range:range_mean_reversion:primary`, preserving the old generic path only as diagnostic context.
- `execution-candidate.path_id` equals the exact branch path.
- Full workflow `latest_structural_execution_candidate.path_id` equals the exact branch path.

## Verification

- `rustfmt --check src/application/orchestration/workflow_status.rs`
- `cargo test workflow_status_phase_structural_feedback_preserves_recommended_branch_path --lib`
- `cargo test workflow_status_phase_structural_feedback --lib`
- `cargo test execution_candidate_phase_ --lib`
- `cargo test workflow_status_structural_detail_phases_share_recommended_next_step_contract --lib`
- `cargo build`
- `checks/structural_feedback_branch_preservation_fix_v1_assertions.out`

## Decision

Gate:

- `structural_feedback_branch_preservation_fix_v1=branch_identity_preserved_across_feedback_bundle_execution_full_status_non_promoting`
- `structural_feedback_path_owner_mismatch_resolved=true`
- `selected_history_missing=true`
- `source_control_evidence_acquired=false`
- `promotion_allowed=false`
- `update_goal=false`

This closes the `101314` structural-feedback owner mismatch, but it does not unlock Board A production acceptance. The chain remains fail-closed because the branch is still `execution_observe_only`, `ready=false`, `actionable=false`, and full workflow still reports `closed_loop_branch_admission.status=fail_closed`.

## Next

Do not repeat the same branch-preservation diagnostic. The next non-duplicative move remains explicit selected-history approval for the recorded branch lane, or a real R6/R5/R3 source/control unlock before any promotion rerun can count.
