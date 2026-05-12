# Current Real Chain Readback v1

Run id: `20260512T100426+0800-codex-board-b-current-real-chain-readback-v1`

Mode: `incubation_only`, follow-on readback.

This packet is additive evidence after the nearby `100412` recorded-MTF chain refresh. It does not edit the Board B Current Cursor, does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

## Scope

State dir:
- `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

Symbol:
- `SRC_ROOT_CARRY_LONG_220646`

## Command Evidence

All command exit markers are under:
- `docs/experiments/actionable-regime-confidence/runs/20260512T100426+0800-codex-board-b-current-real-chain-readback-v1/command-output/`

Commands exited `0`:
- `cargo build --bin ict-engine`
- `provider-status --agent`
- `provider-status --provider yfinance --agent`
- `provider-status --provider tradingview_mcp --agent`
- `provider-status --provider ibkr --agent`
- `provider-status --provider kraken_cli --agent`
- `provider-status --provider kraken_public --agent`
- `pre-bayes-status --symbol SRC_ROOT_CARRY_LONG_220646 --refresh --output-format json`
- `policy-training-status --symbol SRC_ROOT_CARRY_LONG_220646 --output-format agent`
- `workflow-status --phase structural-recommended-path-bundle --agent`
- `workflow-status --phase structural-feedback --agent`
- `workflow-status --phase execution-candidate --agent`
- `workflow-status --hard-block-only --output-format json`
- `export-structural-path-ranking-target`

## Provider Readback

- Aggregate `provider-status --agent`: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `yfinance`: ready in live-runtime and market-data lanes.
- `tradingview_mcp`: provider-specific command reports `market_data:1/1 ready`.
- Aggregate provider-status still lists `tradingview_mcp@market_data:configured_runtime_unhealthy:tradingview_mcp_connectivity_probe_failed`.
- `kraken_cli`: ready.
- `ibkr`: market-data `0/1 ready`, `configured_runtime_unhealthy`, reason `ibkr_runtime_dependencies_missing_with_gateway_reachable`; local API on port `4002` is still detected.
- `kraken_public`: market-data `0/1 ready`, reason `python3_provider_dependencies_missing`.

Interpretation: provider-specific TradingViewRemix readiness and aggregate provider readiness disagree in this run. Do not treat TradingViewRemix as cleanly production-ready until that contradiction is resolved or a direct lightweight MCP health check confirms the usable lane.

## Downstream Readback

- Pre-Bayes latest gate: `pass_neutralized`.
- Pre-Bayes branch-path BBN bundle: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`; bundle application status `applied`.
- Structural path-ranking target export: `rows=6`, `history_rows=295`, `mature_rows=4`, `history_mature_rows=288`, `execution_gate_rows=3`.
- Policy-training entry models are still not ready for direct BBN/CatBoost entry-model training because matched rows are `0`.
- Path-ranker runtime is ready: `enabled_candidate_set_ready`, `prefer_history`, active match count `1`.
- Path-ranker validation is ready: raw-scored mature `288/30`, production validation `286/30`, observation validation `48/30`, trainer artifact `runtime_eligible`, model family `catboost`.
- Structural bundle exact path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution-candidate exact path is preserved.
- Execution-candidate state: `execution_observe_only`, `execution_readiness=0.4504361163104953`, `review_status=observe`, `ready=false`, reason `structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- Hard-block-only workflow output is `[]`.

## Decision

Gate:
- `incubation_only:build_backed_current_chain_readback`.
- `incubation_only:exact_branch_preserved_execution_observe_only`.
- `fail_closed:execution_candidate_ready_false`.
- `fail_closed:pre_bayes_pass_neutralized`.
- `fail_closed:provider_aggregate_tradingview_disagrees_with_provider_specific_readiness`.
- `fail_closed:ibkr_dependency_unhealthy_gateway_reachable`.
- `fail_closed:kraken_public_python_dependencies_missing`.
- `fail_closed:agent_selected_history_not_explicit_user_selected_history`.
- `fail_closed:source_control_evidence_acquired_false`.

Promotion: `false`.

`update_goal=false`.

## Next

Do not duplicate the `100412` readback as a new promotion claim. The useful next slice is either resolving the aggregate-vs-provider-specific TradingViewRemix readiness contradiction or adding branch-preserving recorded-history observations that can raise execution-candidate readiness above observe-only. Production promotion remains blocked until explicit selected-history approval and source/control unlock exist.
