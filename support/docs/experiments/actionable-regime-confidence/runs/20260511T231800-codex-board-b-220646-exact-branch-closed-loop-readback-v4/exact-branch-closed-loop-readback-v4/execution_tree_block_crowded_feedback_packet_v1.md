# Execution-Tree Block-Crowded Feedback Packet v1

Run id: `20260511T233358+0800-codex-board-b-220646-block-crowded-feedback-packet-v1`

Source readback: `20260511T231800+0800-codex-board-b-220646-exact-branch-closed-loop-readback-v4`

## Classification

`block_crowded` is downstream execution-admissibility feedback for the exact Crisis branch, not a profitability rejection and not a branch-routing failure.

Promotion remains blocked.

## Feedback Scope

- Accepted Board A context: `BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation`
- Recipe: `SourceRootStopCarryLongHorizonV1`
- Exact branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- RC-SPA upstream state: `85.7407`; price roots `4/4`; scoped Manipulation component pass
- Pre-Bayes state: `pass_neutralized`; policy `318900600c5e8cf2`
- Execution-candidate state: `ready`; review status `promote_latest`
- CatBoost/path-ranker state: score visible and used by execution tree; validation ready
- Execution tree state: `blocked`; branch `block_crowded`; readiness `0.4433 < 0.45`
- Runtime market state: `RangeConsolidation/WideRange`

## Signal Meaning

Use this as negative execution-admissibility evidence for the exact Crisis carry branch under crowded or wide-range runtime context.

Do not use it as evidence that:

- the branch path was lost;
- the CatBoost/path-ranker score was not consumed;
- the RC-SPA profitability pass was invalidated;
- the Board A root map should be changed by this single observation.

## Board A / Nursery Feedback

Candidate feedback only:

`Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12` should require non-crowded execution readiness or a compatible live context before promotion replay.

This is `nursery_feedback` / context feedback until repeated across instruments, periods, and market contexts. It is not an accepted Board A replacement rule.

## Next

Keep `220646` blocked. The next Board B loop should either:

- rerun this exact branch only when execution readiness is not crowded and context is compatible; or
- start B2R-nursery with `block_crowded` as a negative execution-admissibility feature.
