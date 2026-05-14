# Completion Audit: Actionable Regime Confidence Full Chain

Objective audited:

```text
docs/plans/2026-05-10-actionable-regime-confidence-todo.md
亲自操控 Auto-Quant 和 ict-engine，经过 filter/pre-Bayes、BBN、CatBoost、execution tree；
使用 IBKR、TradingViewRemix、yfinance、Kraken；
结果放到 docs/experiments。
```

## Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Use the named board as authority | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` cursor points to `20260510T185358+0800-codex-accepted95-full-chain`; ledger has the full-chain row. | satisfied |
| Results under `docs/experiments` | Run root is `docs/experiments/actionable-regime-confidence/runs/20260510T185358-codex-accepted95-full-chain`. | satisfied |
| Accepted 95% regime packet exists | `regime-sidecar/accepted_session_liquidity_packet.json`; source packet reports `SessionLiquidityCoreViable`, cal/test `378/378`, test Wilson95 `0.9899396497369397`, ECE `0.010582010582010581`, coverage `0.3776223776223776`. | satisfied |
| Auto-Quant actually operated | `ict-engine/01_auto_quant_results_import_nq.json` reports `n_ok=1`, `n_error=0`; imported library is `autoquant/strategy_library_nq_scratch_no_rsi_2025.json`. | satisfied |
| yfinance used | `provider/yf_QQQ_1h_20240601_20260509.csv` has 3369 data rows; `analyze-live` artifacts use live yfinance NQ=F/QQQ context. | satisfied |
| IBKR considered | `provider/ibkr_QQQ_1h.csv` has 4007 data rows; provider status records IBKR runtime unhealthy but durable IBKR CSV kept. | satisfied-with-runtime-caveat |
| Kraken considered | `provider/kraken_PF_XBTUSD_1h_2024_2025.csv` has 2000 data rows; provider matrix marks Kraken public ready. | satisfied |
| TradingViewRemix considered | `provider/provider-tvremix-tools-list-health.json` records API key present but HTTP 429 rate limit. | satisfied-with-provider-caveat |
| Filter/pre-Bayes stage operated | `ict-engine/03_pre_bayes_status_nq.json` reports `latest_gate_status=pass_neutralized`; `ict-engine/18_analyze_live_after_catboost_nqf_qqq_agent.json` also reports `pre_bayes_gate=pass_neutralized`. | satisfied |
| BBN stage operated | `ict-engine/04_auto_quant_prior_init_nq_dry_run.json` reports `evidence_value_gate_passed=true`, `strategies_applied=1`, and `trade_count=1081`. | satisfied |
| CatBoost stage operated | `catboost/10_path_ranker_train_nq.out` shows CatBoost training and `catboost_model.cbm` emission; `catboost/11_path_ranker_apply_nq.out` shows 3 predictions; `ict-engine/12_apply_structural_path_ranker_scores_nq.json` applies 3 scored rows; `ict-engine/13_register_catboost_path_ranker_artifact_nq.json` registers `model_family=catboost`; `ict-engine/14_enable_structural_path_ranking_runtime_nq.json` enables runtime selection with `runtime_active_match_count=3`. | satisfied |
| Execution tree consumed CatBoost score | `ict-engine/19_execution_tree_trace_after_catboost_analyze_nq.json` reports `path_ranker_score_visible_to_execution_tree=true`, `path_ranker_score_used_by_execution_tree=true`, `path_ranker_model_family=catboost`, `path_ranker_runtime_source=candidate_set`. | satisfied |
| No tradable-strategy overclaim | `evidence_packet_full_chain.json` decision says `trade_usable=false`; execution tree remains `observe/transition_guardrail`; CatBoost validation is `0/30` mature rows. | satisfied |

## Residual Risk

- Board A confidence objective is satisfied at 95% for `SessionLiquidityCoreViable`.
- This is not a tradable strategy release. The packet is a liquidity/session guardrail, TradingViewRemix is rate-limited, and CatBoost/path-ranker validation has `0/30` mature rows.
- The next action remains: collect or replay at least 30 mature structural-path observations before treating the CatBoost path-ranker as validation-ready.

## Fresh Verification

Executed after writing this audit:

```text
json_checks_ok
accepted_packet=True
auto_quant_import_n_ok=True
yfinance_rows_3369=True
ibkr_rows_4007=True
kraken_rows_2000=True
tvremix_429_recorded=True
pre_bayes_pass=True
bbn_gate_passed=True
catboost_model_registered=True
catboost_runtime_enabled=True
execution_tree_used_catboost=True
no_trade_overclaim=True
all=True
```

Verification scope: JSON validity for the main evidence packet, final execution-tree trace, and provider readback summary; plus direct field checks over the accepted packet, Auto-Quant import, yfinance/IBKR/Kraken CSV summaries, TradingViewRemix health artifact, pre-Bayes status, BBN dry-run, CatBoost trainer/runtime registration, final execution-tree CatBoost consumption, and no-trade-overclaim decision.
