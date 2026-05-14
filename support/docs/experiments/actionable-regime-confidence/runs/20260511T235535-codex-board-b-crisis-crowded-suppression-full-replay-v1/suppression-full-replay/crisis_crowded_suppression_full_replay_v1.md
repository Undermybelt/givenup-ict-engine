# Crisis Crowded Suppression Full Replay v1

Run id: `20260511T235535+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1`

## Decision

The sibling Crisis suppression leaf was encoded across the full selected-row replay as `incubation_only` nursery feedback.

It is not a profitability promotion: under the current crowded / wide-range context it converts the exact Crisis carry branch into `no_trade`, so the effective Crisis trade count becomes `0` for this replay.

## Replay

- Source selected rows: `12329`
- Suppressed no-trade rows: `532`
- Effective trade rows: `11797`
- Crisis source rows: `532`
- Crisis effective trade rows: `0`
- Crisis source RC-SPA: `83.0`
- Sibling branch path: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`

## Downstream Probes

- Provider-status exit: `0`
- Provider readback: `{'summary_line': 'entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready', 'yfinance_live_ready': True, 'ibkr_bridge_ready': False, 'ibkr_bridge_reason': 'ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable', 'tradingview_mcp_ready': False, 'tradingview_mcp_reason': 'tradingview_mcp_connectivity_probe_failed', 'kraken_cli_ready': True, 'kraken_public_ready': False, 'kraken_public_reason': 'python3_provider_dependencies_missing'}`
- Auto-Quant status exit: `0`
- Auto-Quant readback: `{'status': 'missing_dependency', 'healthy': False, 'bootstrap_needed': True, 'notes': ['auto_quant_not_bootstrapped']}`
- Pre-Bayes gate: `pass_neutralized`
- BBN soft evidence: `applied`
- CatBoost/path-ranker validation ready: `True`
- CatBoost/path-ranker consumed: `True`
- Runtime probe branch path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Sibling branch downstream-consumed: `False`
- Execution candidate ready: `True`
- Workflow blocker: `user_selected_historical_data_missing`
- Agent-selected recorded data path: `docs/experiments/actionable-regime-confidence/runs/20260511T233426-codex-board-b-220646-crisis-branch-live-replay-v1/state_crisis_branch_live_replay_v1/SRC_ROOT_CARRY_LONG_220646/analyze_live_20260511T154641_mtf.json`

## Interpretation

The sibling leaf is now encoded across the full selected-row replay. It suppresses all exact Crisis carry rows under the crowded/wide-range context, so it is useful as execution-admissibility feedback but cannot count as a profitable Crisis branch.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_v1.json`
- Replay rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_rows_v1.csv`
- Summary rows: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/suppression-full-replay/crisis_crowded_suppression_full_replay_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235535-codex-board-b-crisis-crowded-suppression-full-replay-v1/checks/crisis_crowded_suppression_full_replay_v1_assertions.out`
