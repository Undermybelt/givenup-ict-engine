# 150515 BTC Binance Full Provider AQ Chain Abort Fail-Closed v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260512T150515+0800-codex-btc-binance-full-provider-aq-chain-v1`

Scope:
- This root attempted a Binance BTCUSDT full-listing Auto-Quant -> ict-engine downstream chain for `B2R_BTC_BINANCE_FULL_MOMENTUM_150515`.
- It copied a run-local Auto-Quant workspace, ran AQ strategies on Binance BTCUSDT 1h full history, normalized selected real trades, ingested those trades, and then attempted `ict-engine analyze`.
- It did not complete the full ordered chain because `04_analyze_binance_full` produced no `.exit`, `.out`, or `.err` file and the root process was no longer active at readback.

Command/readback evidence:
- `01_auto_quant_compile.exit=0`.
- `02_auto_quant_run_tomac_binance_full.exit=0`.
- `03_ingest_real_trades.exit=0`.
- `04_analyze_binance_full.cmd` exists, but `04_analyze_binance_full.exit`, `.out`, and `.err` are absent.
- Downstream outputs for `05_pre_bayes_status`, `06_policy_training_status_before_export`, `07_export_structural_path_ranking_target`, `08_policy_training_status_after_export`, `09_train_catboost_path_ranker`, and `16_workflow_full` are absent.

AQ/provider evidence:
- AQ metrics for `ProviderCryptoMomentumStateV1`: `2758` trades, win rate `26.68600435097897%`, total profit `-89.97%`, Sharpe `-1.985151974351755`, profit factor `0.6725106376079354`, max drawdown `-90.38528160930034%`.
- AQ metrics for `ProviderCryptoPullbackRevertV1`: `1353` trades, win rate `39.689578713968956%`, total profit `-74.31%`, Sharpe `-1.336904605244201`, profit factor `0.6077654391592684`, max drawdown `-74.44338463335295%`.
- Selected real-trade ingest applied `2758` trades from `ProviderCryptoMomentumStateV1.real_trades.normalized.jsonl` with `trades_invalid=0`.
- The provider provenance matrix contains rows for `IBKR`, `TradingViewRemix/TVR`, `yfinance/YF`, `Kraken`, `Binance`, and `Bybit`, but only the `Binance` row has `used_for_current_aq=True`.
- Non-Binance provider rows are provenance/context rows from prior roots or capped provider files, not same-root provider inputs used by the AQ run.

Acceptance decision:
- This is useful negative AQ/trade-density evidence for a Binance BTCUSDT full-listing candidate, not Board A acceptance.
- It fails same-root six-provider AQ authority because only Binance was used for the current AQ run.
- It fails strategy quality because both AQ strategies were deeply negative after cost/backtest metrics.
- It fails the required downstream chain because analyze did not complete and Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree readbacks did not run.
- It provides no calibrated regime confidence, no path probability lower bound, no mature CatBoost/path-ranker validation, and no execution-tree actionable candidate.
- Board A remains fail-closed: accepted `>=95%` contexts `0`, same-root six-provider authority false, promotion allowed false, trade usable false, and `update_goal=false`.
