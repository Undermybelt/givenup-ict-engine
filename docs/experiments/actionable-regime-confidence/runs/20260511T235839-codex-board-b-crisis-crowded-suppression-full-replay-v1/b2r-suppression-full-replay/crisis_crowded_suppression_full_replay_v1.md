# Crisis Crowded Suppression Full Replay v1

Run id: `20260511T235839+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1`

## Decision

- Nursery status: `incubation_only`
- Promotion allowed: `false`
- Sibling branch path: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`
- Suppression rule: `if execution_tree_branch=block_crowded or execution_readiness<0.45 or live_context=RangeConsolidation/WideRange then no_trade`
- Result: full replay encoded the Crisis branch as `no_trade`; this is execution-admissibility feedback, not a profitability promotion.

## Full Replay Backtest

- Input selected rows: `12329`
- Executed replay trades: `11797`
- No-trade rows: `532`
- Crisis decisions suppressed: `532/532`
- Source total net: `40.251986`
- Replay total net after suppression: `37.345109`
- Prevented Crisis source net: `2.906877`
- Rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1/b2r-suppression-full-replay/crisis_crowded_suppression_full_replay_rows_v1.csv`
- Branch summary: `docs/experiments/actionable-regime-confidence/runs/20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1/b2r-suppression-full-replay/crisis_crowded_suppression_full_replay_branch_summary_v1.csv`
- Fold summary: `docs/experiments/actionable-regime-confidence/runs/20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1/b2r-suppression-full-replay/crisis_crowded_suppression_full_replay_fold_summary_v1.csv`

## Downstream Probes

- Pre-Bayes/filter: `pass_neutralized`
- BBN soft evidence: `skipped` / `None`
- CatBoost/path-ranker: `enabled_candidate_set_ready`; export rows `5` history `321`
- Execution tree source runtime path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Execution tree branch/gate: `block_crowded` / `blocked`
- Sibling overlay action: `no_trade`
- Execution reason: `market_state=TrendExpansion/BullTrendExhaustion | execution=blocked/block_crowded/skip | ranker=history_path/unknown/ready`

## Provider / Auto-Quant

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance ready: `True`
- TradingViewRemix ready: `False`
- IBKR ready: `False`
- Kraken CLI ready: `True`
- Auto-Quant status: `missing_dependency`; source library import exit `0`

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1/b2r-suppression-full-replay/crisis_crowded_suppression_full_replay_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235839-codex-board-b-crisis-crowded-suppression-full-replay-v1/checks/crisis_crowded_suppression_full_replay_v1_assertions.out`

## Next

Keep the sibling leaf as incubation feedback and collect repeated compatible/non-compatible execution-context observations; do not promote from this no-trade overlay.
