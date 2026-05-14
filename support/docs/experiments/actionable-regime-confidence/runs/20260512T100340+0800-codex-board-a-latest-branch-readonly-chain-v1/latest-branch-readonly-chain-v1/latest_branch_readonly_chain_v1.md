# Latest Branch Readonly Chain v1

Run id: `20260512T100340+0800-codex-board-a-latest-branch-readonly-chain-v1`

Mode: `incubation_only_non_promoting_readonly_chain`

State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

## Commands

All captured commands exited `0`: provider status, Auto-Quant status, Pre-Bayes/BBN status, policy/CatBoost status, structural bundle, structural feedback, and execution-candidate workflow status.

## Readback

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`.
- Provider usable paths in this readback: yfinance live/runtime data ready, TradingView MCP market data ready, Kraken CLI ready. IBKR/IBKR bridge remain dependency-unhealthy even though the gateway is reachable; Kraken public market-data remains dependency-unhealthy.
- Auto-Quant status: `dependency_ready_data_missing`; dependency healthy `True`; data ready `False`.
- Pre-Bayes gate: `pass_neutralized`.
- BBN application: `applied`; label `primary::ExtremeStress`; label set `primary::ExtremeStress,Crisis_->_CrisisReliefCarry_->_StopManagedPanicRecovery_->_SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- CatBoost/path-ranking: trainer artifact ready `True`, model family `catboost`, trained rows `12329`, production validation `286` rows, observation validation `48` rows.
- Structural bundle path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution-candidate path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Execution status: `execution_observe_only` / `observe`; ready `False`; readiness `0.4504361163104953`.

## Decision

Gate: `latest_branch_readonly_chain_v1=branch_path_preserved_bbn_applied_catboost_ready_execution_observe_only_non_promoting`.

The exact branch path is preserved through the downstream runtime readback, BBN evidence is applied, and CatBoost/path-ranking is runtime-ready in this isolated state. This remains non-promoting: no source/control unlock, no explicit selected-history approval, no canonical merge, no selected-data Auto-Quant promotion, no downstream promotion, no trade claim, and `update_goal=false`.

## Next

Keep production gates fail-closed. Ask for exactly one explicit selected-history lane (HTF, MTF, or LTF) or wait for real R6/R5/R3 source-control unlock evidence before any verifier, canonical merge, selected-data AutoQuant, BBN/CatBoost/execution promotion, trade claim, or update_goal.
