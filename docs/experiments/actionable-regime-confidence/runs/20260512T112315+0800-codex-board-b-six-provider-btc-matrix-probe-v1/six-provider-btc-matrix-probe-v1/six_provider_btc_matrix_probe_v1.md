# Six-Provider BTC Matrix Probe v1

Run id: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

Mode: `same_root_provider_matrix_probe_only`

## Scope

This packet records the six required Board B provider rows in one run root for a BTC-comparable provider matrix. It does not run Auto-Quant training/backtesting, does not run selected-data promotion, does not advance Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, does not edit Current Cursor, and does not call `update_goal`.

Required fields:

- `aq_provider_invoked=false`
- `provider_requested=IBKR,TradingViewRemix/TVR,yfinance/YF,Kraken,Binance,Bybit`
- `provider_data_acquired=yfinance:BTC-USD 1h 983 rows; TradingViewRemix/TVR:BTC-USD 1d 29 rows via local stdio alias; IBKR:BTC PAXOS AGGTRADES 1d 30 rows; Kraken:XBTUSD 1h 721 rows; Binance:BTCUSDT 1h 985 rows; Bybit:BTCUSDT linear 1h 985 rows`
- `provider_unreachable_or_default_gate_caveats=TradingViewRemix remote/default BINANCE:BTCUSDT failed get_ohlcv; TradingViewRemix local stdio exchange-prefixed aliases BITSTAMP:BTCUSD, COINBASE:BTCUSD, BTCUSD failed HTTP 404; BTC-USD alias succeeded; IBKR default provider-status remains unhealthy due runtime dependency path, while direct ib_async BTC/PAXOS AGGTRADES succeeded; Kraken/Binance/Bybit default provider-status remains unhealthy due python3 provider dependencies, while uv direct fetches succeeded`
- `local_cache_replay=false`
- `aq_handoff_or_run_artifact=null`
- `regime_profit_branch_path=not_scored_provider_acquisition_only:BTC -> SixProviderBtcMatrixProbe -> ProviderAuthorityReadback -> SixProviderBtcMatrixProbeV1`

## Command Exits

- `00_provider_status_yfinance`: exit `0`
- `01_provider_status_tradingview_mcp`: exit `0`
- `02_provider_status_ibkr`: exit `0`
- `03_provider_status_ibkr_bridge`: exit `0`
- `04_provider_status_kraken_public`: exit `0`
- `05_provider_status_binance_public`: exit `0`
- `06_provider_status_bybit_public`: exit `0`
- `10_tvr_btcusdt_1d`: exit `1`
- `11_yfinance_btc_usd_1h`: exit `0`
- `12_kraken_xbtusd_1h`: exit `0`
- `13_binance_btcusdt_1h`: exit `0`
- `14_bybit_btcusdt_linear_1h`: exit `0`
- `15_ibkr_btc_paxos_1d`: exit `0`
- `16_tvr_btcusdt_1d_local_stdio`: exit `1`
- `17_ibkr_btc_paxos_aggtrades_1d`: exit `0`
- `18_tvr_alias_BITSTAMP_BTCUSD_1d_local_stdio`: exit `1`
- `18_tvr_alias_BTCUSD_1d_local_stdio`: exit `1`
- `18_tvr_alias_BTC_USD_1d_local_stdio`: exit `0`
- `18_tvr_alias_COINBASE_BTCUSD_1d_local_stdio`: exit `1`

## Readback

- YFinance/YF fetched BTC-USD 1h rows: `983` from `2026-04-01 00:00:00+00:00` through `2026-05-11 23:00:00+00:00`.
- TradingViewRemix/TVR default remote and exchange-prefixed crypto aliases failed, but local stdio alias `BTC-USD` fetched `29` daily rows from `2026-04-13T00:00:00Z` through `2026-05-12T00:00:00Z`.
- IBKR default provider status remains unhealthy, but direct read-only `ib_async` qualified `BTC.USD` on PAXOS and fetched `30` daily `AGGTRADES` bars from `2026-04-01` through `2026-05-12`.
- Kraken public direct fetch wrote `721` XBTUSD 1h rows.
- Binance public direct fetch wrote `985` BTCUSDT 1h rows.
- Bybit public direct fetch wrote `985` BTCUSDT linear 1h rows.
- This closes a provider-acquisition gap only. It is not an AQ run, not a strategy result, not mature branch evidence, and not downstream promotion evidence.

## Gate

- `count_once:112315_six_provider_btc_matrix_probe`.
- `pass:six_required_provider_rows_recorded_in_one_run_root`.
- `pass:yfinance_btc_usd_1h_rows_983`.
- `pass:tvr_btc_usd_1d_rows_29_via_local_stdio_alias`.
- `pass:ibkr_btc_paxos_aggtrades_1d_rows_30`.
- `pass:kraken_xbtusd_1h_rows_721`.
- `pass:binance_btcusdt_1h_rows_985`.
- `pass:bybit_btcusdt_linear_1h_rows_985`.
- `partial:default_provider_statuses_still_unhealthy_for_tvr_ibkr_public_crypto_adapters`.
- `fail_closed:provider_acquisition_only_no_auto_quant_training_run`.
- `fail_closed:no_mature_rooted_branch_observations`.
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_promotion_rerun`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Use this same-root provider matrix as input material for an isolated AQ/provider nursery run only if the next slice actually runs Auto-Quant/backtest and emits branch-rooted trades. Promotion remains blocked until a mature profitable rooted branch survives Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
