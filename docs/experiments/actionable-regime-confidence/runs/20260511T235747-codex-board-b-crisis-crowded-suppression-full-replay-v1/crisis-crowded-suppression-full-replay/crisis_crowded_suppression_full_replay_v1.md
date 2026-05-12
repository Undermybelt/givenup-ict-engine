# Crisis Crowded Suppression Full Replay v1

Run id: `20260511T235747+0800-codex-board-b-crisis-crowded-suppression-full-replay-v1`

## Decision

`CrisisCrowdedSuppressionSiblingV1` was encoded as a full `incubation_only` nursery replay for the source Crisis branch. The sibling emits `no_trade` for crowded `RangeConsolidation/WideRange` context and remains non-promotional.

## Replay / Backtest

- Source branch: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Sibling branch: `Crisis -> CrisisReliefCarry -> BlockCrowdedSuppression -> SourceRootStopCarryLongHorizonV1:crisis_carry_no_trade_when_block_crowded_v1`
- Source Crisis rows: `532`
- Full replay rows: `532`
- Suppressed no-trade rows: `532`
- Trade-taken rows: `0`
- Markets covered: `17`
- Year folds covered: `10`

## Downstream Probes

- Auto-Quant source-wire dry run: `True`
- Pre-Bayes/filter: `pass_neutralized`
- BBN soft evidence: `skipped`
- CatBoost/path-ranker: `enabled_candidate_set_ready`; `Ranker validation: calibration=true quality_ready=true raw_scored_mature=291/30 production_validation=290/30 observation_validation=49/30 ready=true`
- Execution tree: `block_crowded` / `blocked` / `skip`
- Ranker consumed by execution tree: `True`
- Promotion allowed: `False`

## Provider Readback

- yfinance: ready `True`; reason `native_yfinance_runtime_available;public_yahoo_http_endpoints`
- TradingViewRemix/tradingview_mcp: ready `False`; reason `tradingview_mcp_connectivity_probe_failed`
- IBKR: ready `False`; reason `ibkr_runtime_dependencies_missing_with_gateway_reachable`
- Kraken CLI: ready `True`; reason `kraken_cli_config_detected`
- Kraken public: ready `False`; reason `python3_provider_dependencies_missing`

## Artifacts

- Replay CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T235747-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_full_replay_rows_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235747-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/crisis_crowded_suppression_full_replay_summary_v1.json`
- Feedback JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235747-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/feedback/crisis_crowded_suppression_not_followed_feedback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235747-codex-board-b-crisis-crowded-suppression-full-replay-v1/checks/crisis_crowded_suppression_full_replay_v1_assertions.out`
- Command logs: `docs/experiments/actionable-regime-confidence/runs/20260511T235747-codex-board-b-crisis-crowded-suppression-full-replay-v1/crisis-crowded-suppression-full-replay/command-output`

## Next

Accumulate repeated crowded and compatible-context nursery observations before sending the suppression rule to Board A or reopening production promotion.
