# 150352 Trend Pullback AQ Route Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T150352+0800-codex-145809-trend-pullback-aq-route-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T145809+0800-codex-provider-backed-high-density-factor-screen-v1`

## Readback

- Selected branch: `trend_expansion->normal_volatility->down_or_flat_momentum->trend_pullback_resume`.
- Screen summary: `384` trades, win rate `0.6041666666666666`, average return `0.0015056034211132481`, profit factor `1.3558460293603907`, first entry `2017-08-26 08:00:00+00:00`, last entry `2026-05-10 20:00:00+00:00`.
- Provider provenance matrix has six rows, but same-root AQ authority remains false: IBKR/SPY, yfinance/ES, and Binance/BTCUSDT have provider-backed source files from `143900`; TradingViewRemix/TVR, Kraken, and Bybit have no current data file for this seed; all rows have `aq_provider_invoked=false`.
- Chronological fold readback is positive but still only a screen: aggregate folds had `128` trades each with win rates `0.578125`, `0.625`, and `0.609375`, and profit factors `1.245406386486888`, `1.6303047649651041`, and `1.2908032972201895`.
- Auto-Quant material batch, dispatch, and rank exited `0`, but ranked AQ outputs were weaker than the screen: IBKR SPY `212` trades, win rate `40.0943%`, Sharpe `0.1225`, total profit `3.99%`; yfinance ES `164` trades, win rate `34.1463%`, Sharpe `0.0397`, total profit `0.56%`; Binance BTCUSDT produced `0` ranked trades.
- Real-trade ingest attempts exited `0` but applied `0` trades: BTCUSDT `254/254` invalid, SPY `81/81` invalid, ES `49/49` invalid.

## Gate

- `support_once:150352_trend_pullback_aq_route_v1`.
- `evidence_class:provider_backed_branch_screen_to_aq_route_fail_closed`.
- `pass:selected_branch_screen_trades_384_pf_1_3558`.
- `pass:walk_forward_aggregate_folds_positive`.
- `pass:agent_material_batch_dispatch_rank_exit0`.
- `partial:six_provider_rows_emitted`.
- `partial:provider_backed_source_files_ibkr_yfinance_binance`.
- `fail_closed:tvr_kraken_bybit_data_missing`.
- `fail_closed:aq_provider_invoked_false_all_rows`.
- `fail_closed:ranked_aq_outputs_weaker_than_screen`.
- `fail_closed:binance_ranked_trade_count_0`.
- `fail_closed:real_trade_ingest_applied_0`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_admission`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision

This root is useful branch-selection and AQ-routing evidence, but not accepted Board A evidence. It converts the `145809` top screen into agent-material dispatch and real-trade ingest attempts, yet fails the same-root six-provider AQ authority lock, fails to produce valid ingested trade feedback, and does not run Pre-Bayes/filter, BBN, CatBoost/path-ranker, or execution-tree admission.
