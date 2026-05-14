# Exact Branch Closed-Loop Readback v4

- Analyze-live exit zero: `True`; timed out `False`.
- Workflow bundle path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Workflow bundle path is required Board B branch path: `True`.
- Execution candidate observed: `True`; ready `True`; status `ready`.
- Pre-Bayes gate: `pass_neutralized`.
- Execution triage: branch `block_crowded`, gate `blocked`, reason `market_state=RangeConsolidation/WideRange | execution=blocked/block_crowded/skip | ranker=history_path/unknown/ready`.
- Ranker runtime ready: `True`; status `enabled_candidate_set_ready`.
- Ranker validation: production `274` ready `True`, observation `48` ready `True`.
- Promotion allowed: `False`.
- Promotion status: `not_promoted:execution_tree_blocked`.

Artifacts:
- `docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4/exact_branch_closed_loop_readback_v4.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4/exact_branch_closed_loop_readback_v4_assertions.out`
- logs under `docs/experiments/actionable-regime-confidence/runs/20260511T231800-codex-board-b-220646-exact-branch-closed-loop-readback-v4/exact-branch-closed-loop-readback-v4/logs`
