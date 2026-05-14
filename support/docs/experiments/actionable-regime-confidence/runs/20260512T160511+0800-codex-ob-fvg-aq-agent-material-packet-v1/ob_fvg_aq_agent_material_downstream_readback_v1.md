# OB/FVG AQ Agent-Material Downstream Readback v1

This is a post-terminal detail readback for already-counted root `20260512T160511+0800-codex-ob-fvg-aq-agent-material-packet-v1`. It must not add a second Board B support count.

## Objective Mapping

- Profitability factor branch: `TrendTransition -> LowVolatility -> up_momentum -> order_block_pullback_v1`.
- Provider matrix: six rows exist; TVR is recorded unreachable from `154536` without a new TVR call; five non-TVR provider material files were dispatched.
- Auto-Quant execution: real `auto-quant-agent-material-dispatch` ran for groups `0,1,2,3,4` with `max_parallel=1`.
- ict-engine handoff: `auto-quant-results-import`, `auto-quant-prior-init`, `pre-bayes-status`, `policy-training-status`, `workflow-status`, and `export-structural-path-ranking-target` were run against a run-local state dir.
- CatBoost/path-ranker: a real CatBoost trainer invocation was attempted and failed honestly because the target had only one non-mature row and constant/ignored features.

## Command Evidence

All paths are under this run root unless stated otherwise.

- `01_material_json_valid.exit=0`: all five non-TVR material JSON files parsed and contained required fields.
- `02_strategy_py_compile.exit=0`: `agent-material/ProviderObFvgPullbackV1.py` compiled.
- `03_agent_material_batch.exit=0`: `PROVIDER_OB_FVG_160511` batch created with five dispatch groups.
- `04_agent_material_dispatch_groups_0_4.exit=0`: five material groups dispatched through Auto-Quant.
- `05_agent_material_rank.exit=0`: rank artifact produced.
- `06_build_strategy_library.exit=0`: a local `provider_ob_fvg_160511_strategy_library_v1.json` was built from the dispatch output.
- `07_auto_quant_results_import.exit=0`: ict-engine imported the library with `n_total_strategies=5`, `n_ok=3`, `n_error=2`, `n_meta_invalid=2`.
- `08_auto_quant_prior_init.exit=0`: BBN prior init applied IBKR and YF rows, skipped Kraken/Bybit `status=error`, and skipped Binance `trade_count=0`.
- `09_pre_bayes_status_after_prior.exit=0`: Pre-Bayes status command ran, but no policy/gate/bridge snapshot was present.
- `12_export_structural_path_ranking_target.exit=0`: structural target export created one candidate row, with `mature_rows=0`.
- `13_policy_training_status_after_export.exit=0`: path-ranker validation stayed `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, trainer artifact missing, runtime disabled.
- `14_workflow_status_after_export.exit=0`: workflow stayed fail-closed with `review_status=observe`, `ready=false`, `actionable=false`, and `no workflow phase snapshots available`.
- `15_train_catboost_path_ranker.exit=1`: CatBoost failed with `All features are either constant or ignored` after loading `1` target row and `0` mature rows.

## AQ Results

| Provider material | Status | Trades | Win rate | Total profit | Profit factor |
|---|---:|---:|---:|---:|---:|
| IBKR SPY 1h | completed | 350 | 39.1429% | 9.65% | 1.1346 |
| yfinance/YF ES 1h | completed | 255 | 34.1176% | -2.02% | 0.9508 |
| Binance BTCUSDT 1h | completed | 0 | 0.0% | 0.0% | 0.0 |
| Kraken XBTUSD 1h | failed | n/a | n/a | n/a | n/a |
| Bybit BTCUSDT linear 1h | failed | n/a | n/a | n/a | n/a |
| TradingViewRemix/TVR | provider_unreachable | 0 | n/a | n/a | n/a |

## Gate

- `support_once_remains:160511_ob_fvg_aq_agent_material_packet_v1`.
- `duplicate_suppressed:160511_post_terminal_downstream_detail`.
- `pass:auto_quant_dispatch_groups_0_4_exit0`.
- `partial:ibkr_spy_completed_350_trades_pf_1_1346_total_profit_9_65_pct`.
- `partial:yfinance_es_completed_255_trades_pf_0_9508_total_profit_minus_2_02_pct`.
- `fail_closed:tvr_unreachable_from_154536`.
- `fail_closed:binance_zero_trades`.
- `fail_closed:kraken_run_tomac_failed`.
- `fail_closed:bybit_run_tomac_failed`.
- `fail_closed:not_same_root_current_provider_acquisition`.
- `fail_closed:pre_bayes_policy_gate_absent`.
- `fail_closed:path_ranker_target_rows_1_mature_rows_0`.
- `fail_closed:catboost_train_exit1_constant_or_ignored_features`.
- `fail_closed:workflow_ready_false_actionable_false_observe`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not count `160511` again. Treat this as post-terminal plumbing evidence only. The next promotable Board B packet still needs same-root current provider/AQ authority including TVR or an explicit TVR-unreachable fail-closed state, enough branch-keyed profitable observations, mature path-ranker rows, and non-observe execution admission.
