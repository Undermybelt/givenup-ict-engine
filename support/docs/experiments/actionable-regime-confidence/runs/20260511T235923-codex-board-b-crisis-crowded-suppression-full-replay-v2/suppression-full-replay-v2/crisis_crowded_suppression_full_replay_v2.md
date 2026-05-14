# Crisis Crowded Suppression Full Replay v2

Run id: `20260511T235923+0800-codex-board-b-crisis-crowded-suppression-full-replay-v2`

## Decision

The sibling Crisis suppression leaf is encoded across the full selected-row replay as `incubation_only` nursery feedback.

This is not a profitability promotion. Under the current crowded / wide-range context it converts the exact Crisis carry branch into `no_trade`, so the effective Crisis trade count is `0` for this replay.

## Replay

- Source selected rows: `12329`
- Suppressed no-trade rows: `532`
- Effective trade rows: `11797`
- Crisis source rows: `532`
- Crisis effective trade rows: `0`
- Crisis source RC-SPA: `83.0`
- Sibling branch path: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`

## Downstream Probes

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance harness rows / exit: `21` / `0`
- TradingViewRemix harness errors / exit: `1` / `1`
- IBKR harness exit: `1`
- Kraken CLI OHLC rows / exit: `721` / `0`
- Pre-Bayes before: `pass_neutralized`
- BBN update exit: `0`
- Pre-Bayes after: `blocked`
- BBN soft evidence source readback: `applied`
- CatBoost/path-ranker validation ready: `True`
- CatBoost/path-ranker consumed in source readback: `True`
- Execution candidate ready: `True`
- Workflow blocker: `user_selected_historical_data_missing`
- Command failures: `0`

## Interpretation

The sibling leaf is encoded across the full 220646 selected-row replay. In the crowded/wide-range context it suppresses all exact Crisis carry rows, so it is execution-admissibility feedback and not a profitable Crisis branch.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2/suppression-full-replay-v2/crisis_crowded_suppression_full_replay_v2.json`
- Replay rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2/suppression-full-replay-v2/crisis_crowded_suppression_full_replay_rows_v2.csv`
- Summary rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2/suppression-full-replay-v2/crisis_crowded_suppression_full_replay_summary_v2.csv`
- Feedback file: `docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2/suppression-full-replay-v2/crisis_crowded_suppression_feedback_v2.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235923-codex-board-b-crisis-crowded-suppression-full-replay-v2/checks/crisis_crowded_suppression_full_replay_v2_assertions.out`
