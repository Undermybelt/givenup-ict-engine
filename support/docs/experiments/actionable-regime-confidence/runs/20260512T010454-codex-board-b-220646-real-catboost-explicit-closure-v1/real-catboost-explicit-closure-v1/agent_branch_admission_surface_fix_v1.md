# Agent Branch Admission Surface Fix v1

Run id: `20260512T010454+0800-codex-board-b-220646-real-catboost-explicit-closure-v1`

Scope: downstream workflow-status surface repair for the exact `220646` Sideways branch. No RC-SPA, Auto-Quant scorer, or branch replay rerun was performed in this packet.

## Root Cause

The phase-specific execution-candidate surface and full JSON workflow-status surface already exposed the exact structural branch after the earlier precedence fix. The remaining mismatch was `workflow-status --output-format agent`: it still routed from the generic recommended command and reported `blocking_status=unblocked`, so an agent could treat a `pass_neutralized` / `execution_observe_only` structural branch as open even though full JSON had `closed_loop_branch_admission.status=fail_closed`.

## Fix

The agent workflow-status view now reuses the structural execution-candidate / closed-loop branch-admission helper used by full JSON. If the structural candidate is visible but not ready/actionable, the agent surface emits:

- `blocking_status=fail_closed`
- `blocking_reason=exact_structural_branch_visible_but_not_ready_or_actionable`
- `hard_block_active=true`
- `next_command_source=closed_loop_branch_admission`
- the same `latest_structural_execution_candidate` and `closed_loop_branch_admission` objects as the full JSON branch-admission surface

## Evidence

- `35_cargo_test_structural_branch_admission_agent_surface.exit = 0`
- `36_cargo_test_execution_candidate_phase_lib.exit = 0`
- `37_cargo_build_agent_branch_admission.exit = 0`
- `38_workflow_json_after_agent_branch_admission_fix.exit = 0`
- `39_workflow_agent_after_agent_branch_admission_fix.exit = 0`

Full JSON readback:

- `phase_detail.source_phase=structural-recommended-path-bundle`
- `latest_structural_execution_candidate.path_id=Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- `closed_loop_branch_admission.status=fail_closed`
- `pre_bayes_gate_status=pass_neutralized`
- `execution_gate_status=execution_observe_only`
- `review_status=observe`

Agent readback:

- `blocking_status=fail_closed`
- `blocking_reason=exact_structural_branch_visible_but_not_ready_or_actionable`
- `next_command_source=closed_loop_branch_admission`
- `latest_structural_execution_candidate.path_id=Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- `closed_loop_branch_admission.status=fail_closed`

## Decision

Promotion remains blocked. This packet closes the agent-surface routing gap only. It does not supersede the newer execution-tree trace parity blocker: the execution tree still needs to emit or consume the same exact Sideways branch-level admission/fail-closed reason before any promotion claim.
