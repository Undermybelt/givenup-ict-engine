# 20260510T192649 Hermes Full-Chain Score Match

Purpose: latest Board A closure folder for the accepted 95% regime guardrail and the NQ CatBoost score-match readback.

Primary packet:
- `evidence_packet_score_match_catboost_runtime_closure.json`

Lineage:
- Accepted regime packet: `../20260510T185358-codex-accepted95-full-chain/evidence_packet_full_chain.json`
- Strict BBN/CatBoost replay closure: `../20260510T191350-codex-nq-structural-replay36/evidence_packet_structural_replay36_catboost_closure.json`

Current re-audit artifacts:
- `provider/provider-status-agent-current-reaudit.json`
- `ict-engine/16_policy_training_status_current_reaudit.json`
- `ict-engine/17_pre_bayes_status_current_reaudit.json`
- `ict-engine/18_workflow_phase_structural_recommended_path_bundle_current_reaudit.json`
- `completion_audit_prompt_to_artifact.json`

Current bounded conclusion:
- Board A regime confidence is `accepted_95` for `SessionLiquidityCoreViable`.
- CatBoost external-model score match is ready as downstream context.
- Trade/use promotion remains blocked: Pre-Bayes is `observe_only`; structural path gate is `observe`; execution tree remains `observe/transition_guardrail/guarded`.
- Current default provider-status re-audit is weaker than the earlier saved provider artifact: yfinance is ready, Kraken CLI is ready, but IBKR/ibkr_bridge and Kraken public are blocked in this default runtime by missing Python/runtime deps; TradingView MCP remains not ready. Durable IBKR/Kraken/yfinance CSV artifacts remain available in the upstream full-chain run.
