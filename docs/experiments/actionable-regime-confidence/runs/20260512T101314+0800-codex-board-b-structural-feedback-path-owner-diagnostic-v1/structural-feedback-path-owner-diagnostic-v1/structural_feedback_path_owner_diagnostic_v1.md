# Structural Feedback Path Owner Diagnostic v1

Run id: `20260512T101314+0800-codex-board-b-structural-feedback-path-owner-diagnostic-v1`

Mode: `incubation_only`

## Scope

Diagnostic follow-up after `20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1`.
This packet does not edit runtime code, does not edit the Current Cursor, does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

## Symptom

The current recorded-MTF chain preserves the exact Board B branch path through:

- `workflow-status --phase structural-recommended-path-bundle`
- `workflow-status --phase execution-candidate`

Exact path:

```text
Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12
```

But `workflow-status --phase structural-feedback` still emits the generic BBN/canonical structural path:

```text
path:scenario:SRC_ROOT_CARRY_LONG_220646:belief_regime_node:range:range_mean_reversion:primary
```

## Evidence Read

- `docs/experiments/actionable-regime-confidence/runs/20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1/command-output/05_workflow_structural_bundle_agent.stdout.txt`
- `docs/experiments/actionable-regime-confidence/runs/20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1/command-output/06_workflow_structural_feedback_agent.stdout.txt`
- `docs/experiments/actionable-regime-confidence/runs/20260512T100412+0800-codex-board-b-recorded-mtf-current-chain-refresh-v1/command-output/07_workflow_execution_candidate_agent.stdout.txt`
- `src/application/orchestration/workflow_status.rs`
- `src/application/orchestration/structural_playbook.rs`
- `src/workflow_snapshot_runtime.rs`

## Root Cause

This is an owner mismatch, not an Auto-Quant scoring failure:

- The `structural-recommended-path-bundle` phase calls `build_structural_recommended_path_bundle_artifact_with_runtime_context_and_prior_state(...)`, which can consume the CatBoost/path-ranker runtime context and select the exact Board B branch path.
- The `execution-candidate` phase can virtualize the structural recommended path bundle and preserve the same exact branch path.
- The `structural-feedback` phase is still routed through `build_structural_playbook_bundle_with_runtime_context_and_prior_state(...).feedback_template`.
- The feedback template builder selects from `branch_set -> scenario_playbook -> path_plan`, whose anchor remains the canonical structural prior / BBN range node for this state.
- Therefore the structural-feedback phase can expose a valid generic feedback contract while still failing the Board B requirement that the same `regime_profit_branch_path` survive every downstream surface.

## Decision

Gate:

- `incubation_only:structural_feedback_path_owner_diagnostic`
- `fail_closed:structural_feedback_phase_uses_playbook_feedback_template_owner`
- `fail_closed:exact_board_b_branch_not_preserved_by_structural_feedback_phase`
- `promotion_allowed=false`
- `update_goal=false`

No Rust patch was made in this slice because the canonical runtime files are already dirty in the shared worktree and this diagnostic is enough to narrow the next owner.

## Next

If the next agent edits code, the likely minimal target is the `structural-feedback` phase routing in `src/application/orchestration/workflow_status.rs`: when a structural recommended path bundle exists for the current state, the feedback template should either be generated from that exact recommended path or explicitly expose a separate `structural-feedback-template-generic` phase. Add a targeted test that the same exact Board B `regime_profit_branch_path` appears in `structural-recommended-path-bundle`, `structural-feedback`, and `execution-candidate` for the recorded-MTF state shape.
