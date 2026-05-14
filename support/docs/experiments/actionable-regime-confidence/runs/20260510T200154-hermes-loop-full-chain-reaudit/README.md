# 20260510T200154 Hermes Loop Full-Chain Reaudit

Purpose: latest Board A run root for re-auditing the accepted 95% regime packet against real provider probes and the persisted ict-engine chain.

Primary artifacts:
- `evidence_packet_full_chain_reaudit.json`
- `completion_audit_prompt_to_artifact.json`

Lineage:
- Accepted regime packet: `../20260510T185358-codex-accepted95-full-chain/evidence_packet_full_chain.json`
- Strict BBN/CatBoost closure: `../20260510T191350-codex-nq-structural-replay36/evidence_packet_structural_replay36_catboost_closure.json`
- CatBoost current score-match closure: `../20260510T192649-hermes-full-chain-score-match/evidence_packet_score_match_catboost_runtime_closure.json`

Current bounded conclusion:
- Board A remains `accepted_95` for `SessionLiquidityCoreViable`.
- BBN strict apply and CatBoost structural path-ranker validation remain covered by lineage artifacts.
- Current provider probe: yfinance, IBKR, Kraken CLI/public are ready; TradingView MCP remains not ready.
- Current Pre-Bayes is `pass_neutralized`; structural path bundle still uses CatBoost external-model scores with gate `observe`.
- Trade/execution promotion remains blocked by workflow `user_selected_historical_data_missing` and execution-tree `observe/transition_guardrail/guarded`.
