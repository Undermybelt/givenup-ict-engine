# Recorded MTF Chain Readback v1

Run id: `20260512T100402+0800-codex-board-a-recorded-mtf-chain-readback-v1`

Mode: `incubation_only_readback`.

## Provider Readback

- yfinance ready: `True`.
- TradingViewRemix/MCP ready: `False`.
- Kraken CLI ready: `True`.
- IBKR market-data ready: `False`.
- yfinance QQQ 1d harness fetch exit: `0`.
- TradingViewRemix QQQ 1d harness fetch exit: `1`.
- TradingViewRemix fetch error: `Error: market-data-harness fetch encountered failures: role=etf_reference provider=tradingview_mcp symbol=NASDAQ:QQQ fetch_failed:tradingview MCP call 'get_ohlcv' returned error | install_prompt=Consumer agent follow-up:`.
- Provider matrix CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T100402+0800-codex-board-a-recorded-mtf-chain-readback-v1/recorded-mtf-chain-readback-v1/provider_matrix_v1.csv`.

## Downstream Readback

- Commands captured: `18`.
- Provider/AQ/downstream core exits all zero: `True`.
- Key fields: `{"30_pre_bayes_status_json": {}, "40_policy_training_status_json": {"ready": false}, "50_workflow_structural_bundle_json": {"path_ranker_raw_score": 0.65, "path_ranker_runtime_source": "history_path"}, "51_workflow_execution_candidate_json": {"actionable": false, "candidate_status": "execution_observe_only", "execution_readiness": 0.4504361163104953, "path_ranker_raw_score": 0.65, "path_ranker_runtime_source": "history_path", "pre_bayes_gate_status": "pass_neutralized", "ready": false, "review_status": "observe"}, "52_workflow_full_json": {"actionable": true, "candidate_status": "execution_observe_only", "closed_loop_branch_admission": {"actionable": false, "candidate_status": "execution_observe_only", "evidence": ["pre_bayes_gate_status=pass_neutralized", "execution_gate_status=execution_observe_only", "review_status=observe"], "execution_gate_status": "execution_observe_only", "path_id": "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12", "path_label": "Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12", "pre_bayes_gate_status": "pass_neutrali`.

## Decision

- Gate: `incubation_only_recorded_mtf_chain_readback_no_promotion`.
- Promotion allowed: `false`.
- `update_goal=false`.
- This packet does not select `HTF`, `MTF`, or `LTF`; it does not approve source/control evidence; it does not mutate canonical intake.

## Next

Keep production gates fail-closed. The next qualifying move still needs explicit selected-history approval plus real Board A source/control unlock, or a new non-promoting recorded-history slice that improves execution readiness without reusing closed LTF/TOMAC dead ends.
