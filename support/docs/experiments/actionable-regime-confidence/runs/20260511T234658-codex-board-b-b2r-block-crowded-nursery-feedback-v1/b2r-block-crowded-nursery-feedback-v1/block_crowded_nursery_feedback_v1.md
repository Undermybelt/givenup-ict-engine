# B2R Block-Crowded Nursery Feedback v1

Run id: `20260511T234658+0800-codex-board-b-b2r-block-crowded-nursery-feedback-v1`

## Scope

This is nursery feedback only. It consumes the verified exact Crisis branch `block_crowded` execution-tree block and records it as a not-followed execution-admissibility observation, not as a profitability rejection.

## Branch

- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Nursery status: `incubation_only`
- Feedback outcome: `not_followed`
- Exit reason: `execution_tree_block_crowded`

## Runtime Readback

- Structural feedback rows: `49` / total `49`
- Observation outcomes: `{'loss': 25, 'not_followed': 1, 'win': 23}`
- Ranker runtime ready: `True`
- Production validation ready: `True`
- Observation validation ready: `True`
- Pre-Bayes gate readback: `blocked`
- Pre-Bayes branch-path gate: `blocked_missing_consumed_pre_bayes_filter`

## Board A Feedback

Candidate feedback only: require non-crowded execution readiness or compatible context before replaying the exact Crisis carry branch for promotion. Do not treat this single row as an accepted Board A replacement rule.

## Artifacts

- `docs/experiments/actionable-regime-confidence/runs/20260511T234658-codex-board-b-b2r-block-crowded-nursery-feedback-v1/b2r-block-crowded-nursery-feedback-v1/block_crowded_nursery_structural_feedback_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T234658-codex-board-b-b2r-block-crowded-nursery-feedback-v1/b2r-block-crowded-nursery-feedback-v1/block_crowded_nursery_feedback_v1.json`
- `docs/experiments/actionable-regime-confidence/runs/20260511T234658-codex-board-b-b2r-block-crowded-nursery-feedback-v1/checks/block_crowded_nursery_feedback_v1_assertions.out`

## Next

Run a compatible-context replay or live readback only when execution readiness is not crowded; keep promotion blocked.
