# Accepted 95 Full-Chain Evidence

Date: 2026-05-10

Purpose: durable follow-through for Board A after the `SessionLiquidityCoreViable` 95% packet. This run keeps the accepted packet, provider artifacts, Auto-Quant import, ict-engine filter/BBN/CatBoost/execution-tree outputs, and state snapshots in one named repo folder.

## Result

- Board A confidence gate: `accepted_95`
- Accepted packet: `regime-sidecar/accepted_session_liquidity_packet.json`
- Full-chain packet: `evidence_packet_full_chain.json`
- Trade usability: `false`
- Reason: the accepted regime is a liquidity guardrail, not a directional/path-specific edge; CatBoost scores are visible to execution tree, but path-ranker validation is still `0/30` mature rows; execution tree remains `observe / transition_guardrail`.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Follow `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | Board cursor and ledger updated in that file | done |
| Do not hallucinate a confidence factor | `regime-sidecar/accepted_session_liquidity_packet.json` records cal/test support, Wilson LCB, ECE, coverage | done |
| Use yfinance | `provider/yf_QQQ_1h_20240601_20260509.csv`; `ict-engine/18_analyze_live_after_catboost_nqf_qqq_agent.json` used `NQ=F` and QQQ via yfinance | done |
| Use IBKR | `provider/ibkr_QQQ_1h.csv`; accepted target uses future IBKR count/volume | done |
| Use Kraken | `provider/kraken_PF_XBTUSD_1h_2024_2025.csv`; provider status also marks Kraken ready | probe-only |
| Use TradingViewRemix | `provider/provider-tvremix-tools-list-health.json`; provider status says `configured_runtime_unhealthy` / connectivity or rate-limit failure | blocked |
| Operate Auto-Quant | `ict-engine/01_auto_quant_results_import_nq.json` imports `autoquant/strategy_library_nq_scratch_no_rsi_2025.json`, `n_ok=1` | done |
| Operate ict-engine live chain | `ict-engine/18_analyze_live_after_catboost_nqf_qqq_agent.json` | done |
| Pass through filter / Pre-Bayes | `ict-engine/03_pre_bayes_status_nq.json`; gate `pass_neutralized`, soft evidence true | done |
| Pass through BBN | `ict-engine/04_auto_quant_prior_init_nq_dry_run.json`; dry-run, evidence gate passed, 1081 trades consumed | done |
| Pass through CatBoost/path-ranker | `catboost/10_path_ranker_train_nq.out`, `catboost/11_path_ranker_apply_nq.out`, `ict-engine/12_apply_structural_path_ranker_scores_nq.json`, `ict-engine/14_enable_structural_path_ranking_runtime_nq.json` | done with validation blocker |
| Pass through execution tree | `ict-engine/19_execution_tree_trace_after_catboost_analyze_nq.json` shows CatBoost score visible and used, final branch `transition_guardrail`, gate `observe` | done |
| Keep useful tmp/state artifacts durable | `state/` contains live analyze, workflow, execution tree, Auto-Quant prior-init, and policy-training artifacts | done |
| Keep future outputs in one named place | this run root is `docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain/` | done |

## Operational Notes

- Regime bundle loaded into analyze-live, but BBN soft evidence skipped as `no_supported_label` because `SessionLiquidityCoreViable` is a liquidity guardrail, not a supported directional market-regime label.
- CatBoost model trained on only 3 target rows using fallback pseudo-labels; runtime is enabled and execution tree uses the score, but validation remains blocked at `raw_scored_mature=0/30`.
- Execution tree final state is intentionally not promoted to trade: `gate_status=observe`, `branch=transition_guardrail`, `decision_hint=execution_guarded_due_to_high_transition_hazard`.
