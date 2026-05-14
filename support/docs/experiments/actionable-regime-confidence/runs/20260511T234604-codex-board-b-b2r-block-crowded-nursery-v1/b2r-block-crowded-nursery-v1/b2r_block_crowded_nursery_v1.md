# B2R Block-Crowded Nursery v1

Run id: `20260511T234604+0800-codex-board-b-b2r-block-crowded-nursery-v1`

## Decision

`block_crowded` is recorded as `incubation_only` negative execution-admissibility feedback for the exact Crisis branch. It is not a profitability rejection and not a promotion.

## Branch

- Accepted Board A context: `BoardA_regime_factor_consumer_map_MainRegimeV2_roots_plus_scoped_manipulation`
- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Runtime context: `RangeConsolidation/WideRange`
- Execution readiness: `0.4433 < 0.45`

## Runtime Probes

- Provider status exits: `{'yfinance': 0, 'tradingview_mcp': 0, 'ibkr': 0, 'kraken_public': 0, 'kraken_cli': 0}`
- Seeded baseline B5 feedback rows: `48/48`
- Auto-Quant seed ingested: `True`
- Pre-Bayes/filter probe: `pre_bayes_status_exit0`
- BBN/update feedback probe: `update_consumed_feedback_exit0`
- CatBoost trained: `True`
- CatBoost runtime enabled: `True`
- Execution-candidate payload present: `True`
- Promotion allowed: `False`

## Artifacts

- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234604-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/b2r_block_crowded_nursery_v1.json`
- Feedback JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234604-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/feedback/block_crowded_negative_execution_admissibility_feedback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234604-codex-board-b-b2r-block-crowded-nursery-v1/checks/b2r_block_crowded_nursery_v1_assertions.out`
- Command logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234604-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/command-output`
- Provider logs: `docs/experiments/actionable-regime-confidence/runs/20260511T234604-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/provider`

## Next

Accumulate more nursery observations for this exact branch under crowded and non-crowded contexts before promoting any Board A rule change. Rerun strict `220646` promotion only when execution readiness/context is compatible.
