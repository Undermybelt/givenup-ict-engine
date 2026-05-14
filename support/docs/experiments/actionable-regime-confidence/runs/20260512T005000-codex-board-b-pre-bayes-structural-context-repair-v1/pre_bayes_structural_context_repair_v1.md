# Board B Pre-Bayes Structural Context Repair v1

Run id: `20260512T005000+0800-codex-board-b-pre-bayes-structural-context-repair-v1`.

Decision: `not_promoted:structural_context_repaired_but_execution_tree_not_closed`.

## Confirmed

- Replayed one exact `220646` Sideways structural-feedback update against a copied isolated state.
- All six real ict-engine commands exited `0`: update, Pre-Bayes status, policy-training status, structural bundle, execution-candidate, and workflow-status.
- The latest update now records a consumed Pre-Bayes branch-path filter instead of `blocked_missing_consumed_pre_bayes_filter`:
  - `pre_bayes_gate_status=pass_neutralized`
  - `pre_bayes_branch_path_gate=pass_neutralized`
  - `parent_regime_root=Sideways`
  - `regime_profit_branch_path=Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- Policy/path-ranker runtime remains ready: production validation `893/30`, observation validation `83/30`, runtime source `candidate_set`.
- The structural bundle still selects the required exact Sideways branch path, with candidate-set matches `4`.

## Fail-Closed Finding

This repairs the structural-feedback Pre-Bayes context handoff only. It does not promote the candidate:

- Structural bundle path-ranker gate remains `observe`.
- Latest execution-candidate output is the persisted `analyze-live` candidate, not an exact structural-branch promotion packet.
- Workflow remains in an update/analyze fail-closed state and still needs exact branch execution-tree admissibility plus closed-loop confidence before promotion.

## Artifact Pointers

- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/pre_bayes_structural_context_repair_v1_assertions.json`
- Update output: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/01_update_sideways_structural_feedback.out`
- Pre-Bayes status: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/02_pre_bayes_status_after_repair.out`
- Policy-training status: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/03_policy_training_status_after_repair.out`
- Structural bundle: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/04_workflow_structural_bundle_after_repair.out`
- Execution-candidate: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/05_workflow_execution_candidate_after_repair.out`
- Workflow status: `docs/experiments/actionable-regime-confidence/runs/20260512T005000-codex-board-b-pre-bayes-structural-context-repair-v1/command-output/06_workflow_status_after_repair.out`

## Next

Do not promote from this repair. Continue the active explicit-historical rerun cursor and require exact structural branch execution-tree admission plus closed-loop confidence before any Board B promotion claim.
