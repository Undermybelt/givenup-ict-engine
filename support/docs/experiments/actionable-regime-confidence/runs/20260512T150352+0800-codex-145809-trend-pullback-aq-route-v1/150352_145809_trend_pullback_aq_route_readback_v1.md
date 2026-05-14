# 150352 145809 Trend-Pullback AQ Route v1 Readback

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T150352+0800-codex-145809-trend-pullback-aq-route-v1/`

## Scope

This run converts the settled `145809` branch-local provider-backed seed into an AQ-routed packet. It does not continue `141000`, `142321`, or `145809`, does not edit runtime code, and does not mutate production state. All BBN/path-ranker state is isolated under `/tmp/ict-engine-150352-*` and copied back as evidence.

Selected branch path:

`trend_expansion->normal_volatility->down_or_flat_momentum->trend_pullback_resume`

## Evidence

- Recipe source: `aq-material/ProviderBackedTrendPullbackResume1h.py`
- Material packages: `aq-material/material_binance_btcusdt.json`, `aq-material/material_ibkr_spy.json`, `aq-material/material_yahoo_es.json`
- Selected branch trades: `derived/selected_branch_seed_trades.csv`
- Six-provider provenance: `derived/six_provider_provenance_matrix.csv`
- Walk-forward summary: `derived/walk_forward_summary.csv`
- AQ batch/dispatch/rank snapshots: `state-snapshots/`
- SPY CatBoost/path-ranker model: `downstream/catboost_spy_path_ranker_model/`
- SPY downstream policy-training snapshot: `downstream/state_spy_policy_training/`

## Readback

Selected `145809` branch seed has `384` rows, win rate `0.604167`, total return units `0.578152`, and profit factor `1.355846`.

Provider provenance:
- IBKR: requested=true acquired=true aq_invoked=false status=provider_backed_source_file_available_from_143900
- TradingViewRemix/TVR: requested=true acquired=false aq_invoked=false status=fail_closed_no_current_tvr_data_file_for_this_seed
- yfinance/YF: requested=true acquired=true aq_invoked=false status=provider_backed_source_file_available_from_143900
- Kraken: requested=true acquired=false aq_invoked=false status=fail_closed_no_current_kraken_ohlcv_file_for_this_seed
- Binance: requested=true acquired=true aq_invoked=false status=provider_backed_source_file_available_from_143900
- Bybit: requested=true acquired=false aq_invoked=false status=fail_closed_no_current_bybit_data_file_for_this_seed

AQ public-surface dispatch:

- Batch exit `0`; dispatch exit `0`; rank exit `0`.
- Dispatch completed `3/3` jobs with `0` failures and `0` blocked jobs.
- ibkr SPY 1h trend-expansion normal-vol pullback-resume: status `completed`, trades `212`, win_rate `40.0943`, total_profit_pct `3.99`, sharpe `0.1225`
- yfinance ES 1h trend-expansion normal-vol pullback-resume: status `completed`, trades `164`, win_rate `34.1463`, total_profit_pct `0.56`, sharpe `0.0397`
- binance BTCUSDT 1h trend-expansion normal-vol pullback-resume: status `completed`, trades `0`, win_rate `0.0`, total_profit_pct `0.0`, sharpe `0.0`

BBN ingest / structural feedback:

- BTCUSDT applied `254` rows, invalid `0`.
- SPY applied `81` rows, invalid `0`.
- ES applied `49` rows, invalid `0`.

SPY CatBoost/path-ranker:

- CatBoost train exit `0`; apply scores exit `0`; register exit `0`; enable runtime exit `0`.
- Runtime enabled `True`, ready `True`, status `enabled_candidate_set_ready`, score model `catboost`, active matches `2`.
- Validation ready: calibration `True`, production `True`, observation `True`, raw scored mature `82/30`.
- Workflow preserved exact path `trend_expansion->normal_volatility->down_or_flat_momentum->trend_pullback_resume` with raw score `0.7127935008151997` and selected path probability `0.6965143886549179`.
- Execution admission stayed fail-closed: ready `False`, actionable `False`, gate `execution_candidate_observed`, review `observe`, reason `structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.

## Gate

- `support_once:150352_145809_trend_pullback_aq_route_v1`.
- `pass:selected_branch_rows_384`.
- `pass:six_provider_rows_present`.
- `pass:aq_agent_material_batch_exit0`.
- `pass:aq_agent_material_dispatch_completed_3_of_3`.
- `partial:aq_dispatch_spy_212_trades_pf_1_0948_total_profit_3_99`.
- `partial:aq_dispatch_es_164_trades_pf_1_023_total_profit_0_56`.
- `fail_closed:aq_dispatch_binance_0_trades`.
- `fail_closed:missing_tvr_kraken_bybit_data_acquisition_for_this_seed`.
- `pass:bbn_ingest_applied_btcusdt_254_spy_81_es_49_in_isolated_state`.
- `pass:spy_catboost_trained_and_runtime_enabled_candidate_set_ready`.
- `pass:spy_exact_branch_path_preserved_in_workflow`.
- `fail_closed:pre_bayes_gate_status_absent`.
- `fail_closed:execution_readiness_null`.
- `fail_closed:execution_gate_status_execution_candidate_observed`.
- `fail_closed:workflow_ready_false_actionable_false_observe`.
- `caveat:catboost_training_features_one_structural_baseline_score_only`.
- `caveat:catboost_label_distribution_one_negative_eighty_one_positive_pseudo_labels`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

The next unowned step should either acquire missing TVR/Kraken/Bybit provider-backed data for this same branch recipe, or run a narrower SPY-only admission repair that creates a real Pre-Bayes/analyze snapshot so execution readiness is no longer null. Do not promote `150352` as-is: it proves the branch path can survive BBN ingestion plus CatBoost/path-ranker runtime, but execution admission remains observe-only.
