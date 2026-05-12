# Crisis Crowded Suppression Sibling v1

Run id: `20260511T234938+0800-codex-board-b-crisis-crowded-suppression-sibling-v1`

## Decision

A sibling Crisis leaf was tested as `incubation_only`: it emits `no_trade` when the live execution tree reports `block_crowded` or `RangeConsolidation/WideRange` context.

This is not a profitability promotion. It is a nursery guard that prevents the exact Crisis carry branch from being replayed into the same crowded context that already blocked execution.

## Sibling Branch

- Source branch: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Sibling branch: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`
- Action leaf: `no_trade_when_block_crowded_or_wide_range`
- Suppression rule: `execution_tree_branch=block_crowded` or `execution_readiness<0.45` or `live_context=RangeConsolidation/WideRange`

## Source Metrics

- Crisis source trades: `532`
- Crisis source RC-SPA: `83.0`
- Crisis source edge LCB: `0.002745066872817171`
- Crisis source PBO: `0.1`
- Crisis source DSR: `3.2177242727776023`

## Current Runtime Test

- Pre-Bayes gate: `pass_neutralized`
- Execution candidate ready: `True`
- Ranker consumed by execution tree: `True`
- Execution tree branch: `block_crowded`
- Execution tree gate: `blocked`
- Consumer reason: `market_state=RangeConsolidation/WideRange | execution=blocked/block_crowded/skip | ranker=history_path/unknown/ready`
- Sibling action result: `no_trade`

## Next

Use this sibling leaf in B2R nursery replay logic; it should explicitly emit no_trade under block_crowded / RangeConsolidation-WideRange contexts and only allow Crisis carry promotion replay when execution readiness is >=0.45 and context is compatible.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/crisis-crowded-suppression-sibling/crisis_crowded_suppression_sibling_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234938-codex-board-b-crisis-crowded-suppression-sibling-v1/checks/crisis_crowded_suppression_sibling_v1_assertions.out`
