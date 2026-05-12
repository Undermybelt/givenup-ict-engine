# Provider Acquisition Reroute v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T101138+0800-codex-board-b-provider-acquisition-reroute-v1`

Purpose: test provider acquisition paths before another AQ-first Board B nursery run. This is provider/data evidence only. It does not edit the Board B Current Cursor, select `HTF`/`MTF`/`LTF`, approve source/control evidence, run Auto-Quant training, run downstream promotion, or authorize `update_goal`.

## Commands

- `./target/debug/ict-engine provider-status --agent`
- `./target/debug/ict-engine market-data-harness --action fetch --request-json provider-acquisition-reroute-v1/harness_request_qqq_provider_matrix_v1.json`
- `uv run --with pandas --with requests python scripts/auto_quant_external/fetch_external.py kraken-kline --market spot --pair XBTUSD --interval 1h ...`
- `uv run --with pandas --with requests python scripts/auto_quant_external/fetch_external.py bybit-kline --category linear --symbol BTCUSDT --interval 1h ...`
- `uv run --with pandas --with requests python scripts/auto_quant_external/fetch_external.py binance-kline --symbol BTCUSDT --interval 1h ...`
- `uv run --with pandas --with requests --with redis --with ib_async python scripts/auto_quant_external/fetch_external.py ibkr-historical --symbol QQQ --sec-type STK --exchange SMART --primary-exchange NASDAQ --bar-size "1 day" --duration "1 M" --what-to-show TRADES --port 4002 --client-id 88 ...`

## Provider Results

| Provider path | Result | Artifact |
|---|---:|---|
| yfinance harness `QQQ` 1d | `21` rows acquired | `provider-data/yfinance_QQQ_1d.csv` |
| TradingView MCP harness `NASDAQ:QQQ` 1d | fetch failed | `command-output/01_market_data_harness_fetch.err` |
| IBKR default harness `QQQ` 1d | fetch failed due missing default-runtime deps | `command-output/01_market_data_harness_fetch.err` |
| IBKR low-pollution `uv --with redis --with ib_async` `QQQ` 1d | `21` rows acquired | `provider-data/ibkr_QQQ_1d.csv` |
| Kraken public `XBTUSD` 1h | `721` rows acquired | `provider-data/kraken_XBTUSD_1h.csv` |
| Bybit public linear `BTCUSDT` 1h | `985` rows acquired | `provider-data/bybit_BTCUSDT_linear_1h.csv` |
| Binance public spot `BTCUSDT` 1h | `985` rows acquired | `provider-data/binance_BTCUSDT_1h.csv` |

Provider-status readback remained conservative: yfinance and Kraken CLI were ready; IBKR and IBKR bridge were dependency-unhealthy despite gateway reachability; TradingView MCP was connectivity-unhealthy; kraken_public/binance_public/bybit_public were dependency-unhealthy in the default runtime. The successful direct fetches used explicit `uv --with ...` runtime envelopes and should be treated as provider acquisition artifacts, not proof that the default repo provider gates are fully healthy.

## Board B Fields

- `aq_provider_invoked`: `false_provider_acquisition_slice`.
- `provider_requested`: `yfinance`, `TradingViewMCP`, `IBKR`, `Kraken`, `Bybit`, `Binance`.
- `provider_data_acquired`: `yfinance:QQQ_1d_21_rows`, `ibkr:QQQ_1d_21_rows`, `kraken:XBTUSD_1h_721_rows`, `bybit:BTCUSDT_linear_1h_985_rows`, `binance:BTCUSDT_1h_985_rows`.
- `provider_unreachable`: `tradingview_mcp:get_ohlcv_failed`; `ibkr_default_harness:missing_redis_runtime` but `ibkr_uv_fetch_succeeded`.
- `local_cache_replay`: `false`.

## Decision

- Gate: `provider_acquisition_only:not_profitability_evidence`.
- This repairs the narrow "only local cache / Binance DNS" blocker for the next nursery setup: fresh provider rows now exist for tradfi and crypto sidecars.
- It does not create a rooted Auto-Quant profitability candidate, mature branch observations, Pre-Bayes/BBN posterior, CatBoost/path-ranker calibration, execution-tree pass, selected-history approval, or Board A source/control unlock.
- Promotion allowed `false`; `update_goal=false`.

## Next

Use these provider artifacts only as input material for a new isolated AQ/provider nursery workspace. The next non-duplicative slice is to pre-seed that workspace from acquired provider rows, run Auto-Quant/backtest, then rerun Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree on the same rooted branch path if and only if the AQ run adds nonzero mature branch observations.
