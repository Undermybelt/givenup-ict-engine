# Prompt-to-Artifact Completion Audit

Date: 2026-05-10

Objective restated:

- Follow `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`.
- Do not reason hypothetically; use real Auto-Quant and `ict-engine` artifacts.
- Preserve the chain order: Auto-Quant -> filter / Pre-Bayes -> BBN -> CatBoost -> execution tree.
- Include provider paths: IBKR, TradingViewRemix, yfinance, and Kraken.
- Put results under `docs/experiments`.

## Completion Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Plan file followed and updated | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` has `board_state=accepted_95`, current run root `docs/experiments/actionable-regime-confidence/runs/20260510T192649-hermes-full-chain-score-match`, and Evidence Ledger rows through `20260510T192649+0800-hermes-full-chain-score-match-catboost-readback`. | covered |
| Results stored under `docs/experiments` | Latest run root: `docs/experiments/actionable-regime-confidence/runs/20260510T192649-hermes-full-chain-score-match`; upstream full-chain run root: `docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain`; BBN/CatBoost closure run root: `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36`. | covered |
| Auto-Quant operated or imported through `ict-engine` | `20260510T185358.../ict-engine/01_auto_quant_results_import_nq.json`: `command=auto-quant-results-import`, `n_ok=1`, `n_total_strategies=1`, source `autoquant/strategy_library_nq_scratch_no_rsi_2025.json`. `20260510T191350.../ict-engine/16_auto_quant_prior_init_nq_apply.json`: Auto-Quant prior apply consumed 1 strategy / 1081 trades. | covered |
| Filter / Pre-Bayes readback exists | Fresh readback `completion-audit/fresh_pre_bayes_status_nq.json`: `latest_gate_status=observe_only`, `latest_uses_soft_evidence=true`, canonical structural regime `range`, confidence `0.6195059211153686`. | covered |
| BBN apply was real, not dry-run | `20260510T191350.../ict-engine/16_auto_quant_prior_init_nq_apply.json`: `dry_run=false`, `evidence_value_gate_passed=true`, 1 strategy applied, 1081 trades, `bbn_log_loss_delta=6.7286527442285795`. | covered |
| CatBoost trained/applied and read back | `20260510T191350.../evidence_packet_structural_replay36_catboost_closure.json`: CatBoost model trained on 1397 rows. `20260510T192649.../evidence_packet_score_match_catboost_runtime_closure.json`: CatBoost scores applied to 3/3 current NQ candidate rows. Fresh `completion-audit/fresh_policy_training_status_nq.json`: `score_model_family=catboost`, `score_source_kind=external_model`, `raw_scored_mature=1397/30`, `production_validation=1395/30`, `observation_validation=40/30`, runtime matches 3. | covered |
| Execution tree consumed the CatBoost ranker | `20260510T192649.../ict-engine/15_execution_tree_trace_after_score_match_nq.json`: `gate_status=observe`, `branch=transition_guardrail`, `execution_bias=guarded`, path ranker score visible and used, ranker validation ready. | covered |
| yfinance provider path included | `20260510T185358.../provider/yf_QQQ_1h_20240601_20260509.csv`: 3369 data rows by readback summary, 3370 CSV lines including header. Fresh provider-status still reports yfinance ready. | covered |
| IBKR provider path included | `20260510T185358.../provider/ibkr_QQQ_1h.csv`: 4007 data rows by readback summary, 4008 CSV lines including header. | covered, with current-readiness drift |
| Kraken provider path included | `20260510T185358.../provider/kraken_PF_XBTUSD_1h_2024_2025.csv`: 2000 data rows by readback summary, 2001 CSV lines including header. Fresh provider-status reports `kraken_cli` ready, but `kraken_public` no longer ready in the current readback. | covered, with current-readiness drift |
| TradingViewRemix provider path included | `20260510T185358.../provider/provider-tvremix-tools-list-health.json`: API key present, endpoint probed, result `ok=false`, HTTP 429 rate limit. Plan ledger also preserves earlier `TradingViewRemix unhealthy` / `MCP not ready` state. | attempted and fail-closed |
| No false trade promotion | Latest evidence packet decision: `trade_usable=false`; fresh Pre-Bayes is `observe_only`; execution tree is `observe/transition_guardrail/guarded`; board Next says to use CatBoost-ready ranker only as downstream context. | covered |

## Fresh Verification Commands

Generated in this audit folder:

- `cargo run --quiet -- provider-status --agent > completion-audit/fresh_provider_status_agent.json`
- `cargo run --quiet -- policy-training-status --symbol NQ --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state --output-format json > completion-audit/fresh_policy_training_status_nq.json`
- `cargo run --quiet -- pre-bayes-status --symbol NQ --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state --refresh --output-format json > completion-audit/fresh_pre_bayes_status_nq.json`
- `cargo run --quiet -- workflow-status --symbol NQ --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state --refresh --phase structural-path-ranking --agent > completion-audit/fresh_workflow_phase_structural_path_ranking_nq_agent.json`
- `cargo run --quiet -- workflow-status --symbol NQ --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state --refresh --phase structural-recommended-path-bundle --agent > completion-audit/fresh_workflow_phase_structural_recommended_path_bundle_nq_agent.json`
- `cargo run --quiet -- workflow-status --symbol NQ --state-dir docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state --refresh --agent > completion-audit/fresh_workflow_status_nq_agent.json`

Additional file checks run:

- `wc -l` over durable yfinance, IBKR, and Kraken CSV artifacts returned 3370, 4008, and 2001 lines.
- `jq` readbacks checked provider health, Auto-Quant import, BBN apply, Pre-Bayes, policy training, CatBoost score match, and execution-tree trace artifacts.

## Drift / Residual Risk

- Current fresh `provider-status --agent` no longer reproduces the stored run-time provider status. It now reports `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`, with yfinance ready, Kraken CLI ready, IBKR not currently ready, Kraken public not currently ready, and TradingViewRemix still unhealthy.
- This does not erase the durable yfinance, IBKR, and Kraken data artifacts used by the run, but it means no final answer should claim those provider paths are currently live-ready.
- TradingViewRemix was probed and failed closed with HTTP 429. No TradingViewRemix market data should be treated as usable in the final accepted packet.
- The accepted `SessionLiquidityCoreViable` packet is a 95% guardrail context, not a standalone edge or tradable strategy. Execution remains observe/guarded.

## Audit Decision

The objective is covered as an evidence-producing run: real artifacts exist for the requested Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost -> execution-tree chain, provider paths were either used or fail-closed, and all results are under `docs/experiments`.

The objective is not a trade-promotion success. The final operational state remains context-only: use the CatBoost-ready ranker downstream, but do not execute until a non-observe release candidate passes edge and execution gates.
