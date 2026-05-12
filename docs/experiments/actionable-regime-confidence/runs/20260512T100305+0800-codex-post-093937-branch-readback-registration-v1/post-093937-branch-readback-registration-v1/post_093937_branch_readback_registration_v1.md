# Post-093937 Branch Readback Registration v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T100305+0800-codex-post-093937-branch-readback-registration-v1`

Purpose: register the existing post-`093937` readback so the branch-preservation and provider/AQ status are not missed or rerun blindly. This is an append-only evidence packet. It does not edit the Board B Current Cursor, select historical data, approve source/control evidence, promote a candidate, or authorize `update_goal`.

## Evidence Files

- Structural bundle: `command-output/00_workflow_structural_bundle_agent.out`
- Execution candidate: `command-output/01_workflow_execution_candidate_agent.out`
- Provider status: `command-output/02_provider_status_agent.out`
- HTF Auto-Quant status: `command-output/03_auto_quant_status_htf_agent.out`
- Exit markers: `checks/00_workflow_structural_bundle_agent.exit`, `checks/01_workflow_execution_candidate_agent.exit`, `checks/02_provider_status_agent.exit`, `checks/03_auto_quant_status_htf_agent.exit`

## Readback

- Structural bundle preserved exact branch path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution candidate preserved the same exact branch path.
- Path-ranker runtime source was `history_path`, raw score `0.65`.
- Pre-Bayes gate was `pass_neutralized`.
- Execution stayed non-promotional: `execution_gate_status=execution_observe_only`, `review_status=observe`, `ready=false`, `execution_readiness=0.4504361163104953`.
- Provider matrix was refreshed: yfinance was ready as live runtime and market data; TradingView MCP was ready; Kraken CLI was ready; IBKR gateway was reachable but dependency-unhealthy; IBKR market data, kraken_public, binance_public, and bybit_public were not ready due dependency/runtime blockers.
- The HTF nursery Auto-Quant workspace stayed `dependency_ready_data_missing`: dependency healthy, data not ready, recommended next command still `ict-engine auto-quant-prepare --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T093854+0800-codex-board-b-htf-nursery-v1/state_htf_nursery_v1`.

## Decision

- Gate: `incubation_only:post_093937_branch_path_preserved_observe_only`.
- Provider visibility improved versus older TradingView-unhealthy rows, but this is not provider-complete profitability evidence.
- The AQ/provider blocker remains data acquisition for the HTF nursery workspace; the prior Binance prepare path failed on DNS and this readback does not replace it with provider-acquired data.
- Promotion allowed `false`; `update_goal=false`.

## Next

- Do not rerun the closed LTF/TOMAC sidecars.
- Continue from recorded-history or HTF nursery only if the next slice either acquires AQ/provider data through a healthy provider path or adds non-synthetic mature branch observations, then reruns the ordered Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree chain on that same rooted path.
