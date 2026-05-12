# Execution-Tree Block-Crowded Diagnosis v1

Run id: `20260511T231800+0800-codex-board-b-220646-exact-branch-closed-loop-readback-v4`

## Decision

`block_crowded` is a legitimate execution-tree fail-closed admissibility result for this readback, not a branch-path preservation or CatBoost routing gap.

Promotion remains blocked.

## Evidence

- Exact branch path reached the structural bundle:
  - `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
  - `path_ranker_runtime_source=history_path`
  - `path_ranker_runtime.status=using_history_scores`
- Pre-Bayes emitted a live gate:
  - `latest_gate_status=pass_neutralized`
  - `latest_policy_version=318900600c5e8cf2`
  - `latest_uses_soft_evidence=true`
- Execution-candidate emitted a live payload:
  - `candidate_status=ready`
  - `actionable=true`
  - `review_status=promote_latest`
- Execution tree consumed the path-ranker signal:
  - `path_ranker_score_visible_to_execution_tree=true`
  - `path_ranker_score_used_by_execution_tree=true`
  - trace line includes the exact Crisis path with `runtime_source=history_path`
- Execution tree blocked on readiness and current market state:
  - `execution_readiness=0.4433 -> gate_status=blocked`
  - `branch=block_crowded`
  - `readiness 0.4433 < 0.45`
  - `market_state=RangeConsolidation/WideRange`
  - decision hint: `execution_blocked_regardless_of_prediction`

## Code Readback

- `src/application/orchestration/execution_tree.rs:393-420` maps `gate_status == "blocked"` to `branch=block_crowded` before prediction can override it.
- `src/application/orchestration/execution_tree.rs:636-638` treats `gate_status=blocked` or `branch=block_crowded` as not actionable.
- `tests/hard_gate_execution_first.rs:77-86` confirms the execution-first contract: strong prediction with weak execution still blocks as `block_crowded`.
- `src/application/orchestration/execution_tree.rs:966-999` confirms path-ranker score visibility/use does not bypass weak execution readiness.

## Interpretation

The Board B branch identity is now preserved through Pre-Bayes, BBN-soft-evidence analyze-live, CatBoost/path-ranker, and execution-candidate. The remaining blocker is execution-tree admissibility under the current live market state.

The selected exact path is a Crisis branch, while the live runtime market state is `RangeConsolidation/WideRange`. That mismatch is not enough by itself to mark a routing bug because the trace proves the exact Crisis path was visible and used. It is fail-closed market-state evidence: do not promote this candidate from RC-SPA, Pre-Bayes, or CatBoost alone.

## Next

Keep Board B blocked. Either:

- rerun the same exact branch path when live execution readiness is not crowded and the market context is compatible, or
- feed `block_crowded` as nursery / Board A context feedback for the Crisis branch rather than promoting it.

