# B2R Block-Crowded Nursery v1

Run id: `20260511T234513+0800-codex-board-b-b2r-block-crowded-nursery-v1`

## Decision

`block_crowded` is installed as an `incubation_only` negative execution-admissibility feature for the exact Crisis branch. This does not promote `220646`.

## Branch

- Branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Nursery status: `incubation_only`
- Trade count from source RC-SPA branch: `532`
- Crisis branch RC-SPA: `83.0`
- Filter probe: `pass_neutralized`
- CatBoost/path-ranker probe: `ranker_runtime_ready=True; status=enabled_candidate_set_ready`
- Execution-tree probe: `blocked:block_crowded; readiness=0.4433; market_state=RangeConsolidation/WideRange`

## Provider Readback

- Provider command: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/command-output/provider_status_agent.out`
- yfinance ready: `True`
- TradingView MCP ready: `False`
- IBKR recorded: `True`
- Kraken CLI ready: `True`
- Kraken public ready: `False`

## Interpretation

The branch path reached the ordered chain: Auto-Quant/RC-SPA, Pre-Bayes, BBN-soft-evidence, CatBoost/path-ranker, and execution tree. The execution tree blocked on weak execution readiness under `RangeConsolidation/WideRange`; this is context feedback, not a profitability or routing rejection.

## Next

Run B2R nursery repeat only when a compatible live context appears, or test a sibling Crisis leaf that explicitly suppresses crowded RangeConsolidation/WideRange states; do not promote 220646 from this packet.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery/b2r_block_crowded_nursery_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery/b2r_block_crowded_nursery_row_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/checks/b2r_block_crowded_nursery_v1_assertions.out`
