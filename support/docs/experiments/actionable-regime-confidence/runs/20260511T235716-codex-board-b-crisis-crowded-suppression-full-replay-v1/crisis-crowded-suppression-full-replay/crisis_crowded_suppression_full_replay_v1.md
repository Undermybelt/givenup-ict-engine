# Crisis Crowded Suppression Full Replay v1

Run id: `20260511T235716+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1`

## Scope

This run encodes `CrisisCrowdedSuppressionSiblingV1` into full B2R nursery replay rows and reruns the cheap downstream chain on isolated state. It is not promotion evidence.

## Replay

- Source branch: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Sibling branch: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`
- Replay counted trade rows: `532`
- No-trade guard rows: `1`
- Test folds: `10`; min fold trades `15`
- Source Crisis RC-SPA: `83.0`
- Suppression rule: `if execution_tree_branch=block_crowded or execution_readiness<0.45 or live_context=RangeConsolidation/WideRange then no_trade`

## Downstream

- BBN update applied: `True`
- Pre-Bayes gate: `blocked`
- CatBoost score rows: `15`
- Sibling path in current target: `True`
- Sibling path in history target: `True`
- CatBoost trainer artifact ready: `True`
- Runtime ready: `True`
- Production validation rows: `293`
- Observation validation rows: `50`
- Workflow bundle path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Workflow selected sibling: `False`
- Execution candidate ready: `True`

## Decision

The sibling no-trade guard is encoded and visible to the downstream path-ranker target/history, but it remains `incubation_only`. Promotion stays blocked because a no-trade guard is not a profitability pass and the workflow still needs repeated context evidence before production logic changes.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_full_replay_v1.json`
- Replay rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_full_replay_rows_v1.csv`
- Replay summary: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_full_replay_summary_v1.csv`
- Feedback file: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_no_trade_feedback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/checks/crisis_crowded_suppression_full_replay_v1_assertions.out`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260511T235716-codex-board-b-crisis-crowded-suppression-full-replay-v1/command-output`
