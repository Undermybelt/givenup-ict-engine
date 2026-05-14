# TVR Local Stdio Alias Probe Summary v1

Run root: `20260512T160908+0800-codex-board-a-tvr-local-stdio-alias-probe-v1`

This is read-only TradingViewRemix / `tradingview_mcp` local-stdio route plumbing evidence. It does not use the remote HTTP API, does not persist secrets, does not run Auto-Quant, and does not promote Board A.

## Probe Results

| check | symbol | exit | ok | rows | first | last |
|---|---:|---:|---:|---:|---|---|
| `01_tvr_local_stdio_btc_usd_1h` | `BTC-USD` | 0 | true | 720 | `2026-04-12T09:00:00Z` | `2026-05-12T08:12:15Z` |
| `02_tvr_local_stdio_qqq_1h` | `NASDAQ:QQQ` | 0 | true | 148 | `2026-04-13T13:30:00Z` | `2026-05-11T20:00:00Z` |
| `03_tvr_local_stdio_es_f_1h` | `ES=F` | 0 | true | 487 | `2026-04-12T22:00:00Z` | `2026-05-12T08:02:23Z` |

Provider status for all three probes reported `tradingview_mcp` as ready with reason `local_stdio_ohlcv_available`, `credential_source=missing`, and local stdio command/args env set.

## Decision

The local-stdio TVR route can fetch OHLCV for BTC, QQQ, and ES sanity symbols without using the remote HTTP API path that previously returned HTTP 429.

This is still provider-route plumbing only. It is not same-root six-provider Auto-Quant authority, not a regime-confidence packet, not Pre-Bayes/BBN/CatBoost/path-ranker evidence, not execution-tree admission, not trade usable, and not a goal-completion basis.
