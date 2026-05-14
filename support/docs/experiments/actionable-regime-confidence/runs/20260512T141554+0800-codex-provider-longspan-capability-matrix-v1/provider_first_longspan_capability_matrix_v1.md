# 141554 Provider-First Long-Span Capability Matrix v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T141554+0800-codex-provider-longspan-capability-matrix-v1/`

Raw provider CSV root: `/tmp/ict-provider-longspan-20260512T141554+0800`

## Scope

This is a provider-first capability probe for the Board A long-history direction. It is not Board A acceptance, not a trade-usable signal, and not a completed Auto-Quant downstream chain. Local TOMAC data remains support/development data; this packet records which provider-backed long-span slices were reachable before any promotion claim.

Active root `20260512T141000+0800-codex-135318-real-trades-downstream-v1` was still in `06_nq_analyze_15m_1h_1d` when this report was written and is not counted here.

## Matrix

| provider | symbol | interval | requested window | exit | rows | first -> last | classification |
|---|---:|---:|---:|---:|---:|---|---|
| yfinance | ES=F | 1h | 2024-05-13 to 2026-05-12 | 0 | 11383 | 2024-05-13 00:00:00+00:00 -> 2026-05-11 23:00:00+00:00 | usable near-server-max intraday tradfi/futures slice |
| yfinance | ES=F | 1d | 2010-01-01 to 2026-05-12 | 0 | 4114 | 2010-01-04 05:00:00+00:00 -> 2026-05-11 04:00:00+00:00 | long daily fallback only |
| yfinance | ES=F | 1m | 2024-01-01 to 2026-05-12 | 1 | 0 | n/a | expected long-1m ceiling; Yahoo reported only 8 days of 1m granularity available |
| binance_public | BTCUSDT | 1m | 2017-08-17 to 2018-08-17 | 0 | 521470 | 2017-08-17 04:00:00+00:00 -> 2018-08-17 00:00:00+00:00 | provider-backed old-listing 1m crypto slice |
| binance_public | BTCUSDT | 1h | 2017-08-17 to 2026-05-12 | 0 | 76429 | 2017-08-17 04:00:00+00:00 -> 2026-05-12 00:00:00+00:00 | provider-backed full-listing 1h crypto slice |
| bybit_public | BTCUSDT linear | 1m | 2020-01-01 to 2021-01-01 | 0 | 1000 | 2020-12-31 07:21:00+00:00 -> 2021-01-01 00:00:00+00:00 | fetcher/window capped; support only |
| bybit_public | BTCUSDT linear | 1h | 2020-01-01 to 2026-05-12 | 0 | 1000 | 2026-03-31 09:00:00+00:00 -> 2026-05-12 00:00:00+00:00 | fetcher/window capped; support only |
| kraken_public | XBTUSD spot | 1m | server-window | 0 | 721 | 2026-05-11 18:21:00+00:00 -> 2026-05-12 06:21:00+00:00 | server-window only |
| kraken_public | PF_XBTUSD futures | 1h | 2020-01-01 to 2026-05-12 | 0 | 2000 | 2022-03-23 10:00:00+00:00 -> 2022-06-14 17:00:00+00:00 | fetcher/window capped; support only |
| kraken_public | PF_SPXUSD futures | 1h | 2020-01-01 to 2026-05-12 | 0 | 2000 | 2024-12-20 17:00:00+00:00 -> 2025-03-14 00:00:00+00:00 | fetcher/window capped; support only |
| ibkr | SPY STK SMART/ARCA | 1h | duration=5 Y to now | 0 | 20034 | 2021-05-13T08:00:00+00:00 -> 2026-05-11T23:00:00+00:00 | local gateway reachable through isolated uv deps |
| tradingview_mcp | NASDAQ:QQQ | 1h | 2024-05-13 to 2026-05-12 | 1 | 0 | n/a | TradingViewRemix MCP fetch failed on `get_ohlcv` |

## Decision

- Evidence direction is `provider_first_long_span_maximize`, not `local_tomac_primary` and not `15y_1m_or_stop`.
- Strongest reachable provider-backed intraday slices in this packet are IBKR SPY 5Y/1h, Binance BTCUSDT listing-span 1h, Binance BTCUSDT 1Y/1m, and yfinance ES=F near-server-max 1h.
- Daily-only data and short/server-window intraday data remain diagnostics. They cannot establish Board A regime confidence.
- TradingViewRemix/TVR remains a provider-context gap for this packet because the harness fetch exited `1` with a live `get_ohlcv` error.
- Provider capability does not equal AQ/downstream authority. No row here has been pushed through Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree admission.
- Net Board A effect remains fail-closed: accepted `>=95%` contexts `0`; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.

## Gate

- `support_once:141554_provider_first_longspan_capability_matrix_v1`
- `evidence_class:provider_capability_probe_not_board_a_acceptance`
- `pass:yfinance_es_1h_rows_11383`
- `pass:yfinance_es_1d_rows_4114`
- `pass:binance_btcusdt_1m_rows_521470`
- `pass:binance_btcusdt_1h_rows_76429`
- `pass:ibkr_spy_1h_5y_rows_20034`
- `fail_closed:yfinance_long_1m_unavailable`
- `fail_closed:tradingview_mcp_fetch_failed`
- `fail_closed:bybit_rows_window_capped`
- `fail_closed:kraken_rows_window_capped`
- `fail_closed:not_auto_quant_chain`
- `fail_closed:not_pre_bayes_bbn_catboost_execution_tree`
- `fail_closed:no_calibrated_path_lower_bound_0_95`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Evidence

- Summary JSON: `summaries/provider_longspan_capability_matrix_v1.json`
- Summary CSV: `summaries/provider_longspan_capability_matrix_v1.csv`
- Commands and exit files: `command-output/`, `checks/`
- TradingView harness request: `requests/tradingview_qqq_2y_1h_request.json`
