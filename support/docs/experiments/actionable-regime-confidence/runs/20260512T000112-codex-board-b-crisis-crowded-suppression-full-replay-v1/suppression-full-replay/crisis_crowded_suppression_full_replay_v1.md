# Crisis Crowded Suppression Full Replay v1

Run id: `20260512T000112+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1`

## Decision

The sibling Crisis suppression leaf was encoded across the full selected-row replay as `incubation_only` nursery feedback.

This is not a profitability promotion. The exact Crisis branch is preserved through the downstream stack, but the current execution tree blocks it as `block_crowded`, so the sibling leaf emits `no_trade`.

## Branch Path

- Source branch: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Sibling branch: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`
- Shape: `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`
- Action leaf: `no_trade_when_block_crowded_or_low_readiness`

## Replay

- Source selected rows: `12329`
- Crisis source rows: `532`
- Crisis suppressed no-trade rows: `532`
- Crisis effective trade rows: `0`
- Crisis source RC-SPA: `83.0`
- Crisis source edge LCB: `0.002745066872817171`
- Source Crisis net sum before suppression: `2.906877183291`

## Downstream Probes

- Pre-Bayes gate: `pass_neutralized`
- BBN soft evidence: `applied` weight `0.650`
- CatBoost/path-ranker runtime ready: `True`
- CatBoost/path-ranker validation ready: `True`
- Path-ranker score consumed by execution tree: `True`
- Execution candidate ready: `True`
- Execution tree branch: `block_crowded`
- Execution readiness: `0.4495`
- Workflow blocker: `user_selected_historical_data_missing`

## Provider Readback

- Provider status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance QQQ 1d harness: exit `0`, rows `21`
- TradingViewRemix QQQ 1d harness: exit `1`, errors `1`
- IBKR QQQ 1d harness: exit `1`
- Kraken CLI XBTUSD 1h OHLC: exit `0`, rows `721`

## Interpretation

The sibling leaf is encoded across the full selected-row replay and the rooted Crisis branch path is preserved through Pre-Bayes, BBN soft evidence, CatBoost/path-ranker, and execution tree. The current runtime is blocked by block_crowded/readiness, so the sibling emits no_trade. This is execution admissibility feedback, not a profitability pass.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000112-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_v1.json`
- Replay rows: `docs/experiments/actionable-regime-confidence/runs/20260512T000112-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_rows_v1.csv`
- Summary rows: `docs/experiments/actionable-regime-confidence/runs/20260512T000112-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000112-codex-board-b-crisis-crowded-suppression-full-replay-v1/checks/crisis_crowded_suppression_full_replay_v1_assertions.out`

