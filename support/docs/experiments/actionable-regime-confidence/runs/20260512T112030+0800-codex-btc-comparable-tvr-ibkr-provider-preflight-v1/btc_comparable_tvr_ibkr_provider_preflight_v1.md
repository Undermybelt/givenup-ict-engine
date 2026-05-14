# BTC-Comparable TVR / IBKR Provider Preflight v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1`

Gate: `btc_comparable_tvr_ibkr_provider_preflight_v1=tvr_remote_btc_and_ibkr_paxos_btc_rows_present_stdio_tvr_failed_provider_layer_only_no_promotion`

## Result

This run improves the provider-layer blocker for BTC-comparable TradingViewRemix / TradingView MCP and IBKR coverage, but it is not a six-provider AQ packet and not downstream promotion evidence.

## Evidence

- `00_provider_status_tvr.exit=0`
- `01_tvr_btc_binance_1h.exit=0`
- `02_tvr_btc_coinbase_1h.exit=0`
- `03_tvr_btc_binance_1h_local_stdio.exit=1`
- `04_ibkr_btc_paxos_bulk.exit=0`

## Readback

- `provider-status --provider tradingview_mcp --agent` reported `ready=true`, status `ready`, reason `mcp_url_and_api_key_available`.
- Remote/configured `tradingview_mcp` fetched `BINANCE:BTCUSDT` `1h` OHLCV with `720` rows from `2026-04-12T04:00:00Z` through `2026-05-12T03:00:00Z`.
- Remote/configured `tradingview_mcp` fetched `COINBASE:BTCUSD` `1h` OHLCV with `715` rows from `2026-04-12T04:00:00Z` through `2026-05-12T03:00:00Z`.
- Local-stdio `tradingview_mcp` for `BINANCE:BTCUSDT` `1h` exited `1`: `get_ohlcv` failed with HTTP `404 Not Found`.
- Direct IBKR bulk fetch through the Auto-Quant Python runtime fetched `BTC` `PAXOS` `1 hour` `MIDPOINT` with `45` rows into `derived/ibkr_btc_paxos/BTC_1h_midpoint.csv`, spanning `2026-05-10T07:00:00+00:00` through `2026-05-12T03:00:00+00:00`.
- Repo `market-data-harness` provider summaries still report the default IBKR runtime as unhealthy because runtime dependencies are missing, even though the direct `ibkr-bulk` path returned BTC rows.

## Decision

Accepted rows added `0`. Mature rooted branch observations promoted `0`. Source/control evidence acquired `false`. Explicit selected-history `false`. Canonical merge `false`. Selected-data AutoQuant promotion `false`. Downstream promotion `false`. Strict full objective `false`. Trade usable `false`. Promotion allowed `false`. `update_goal=false`.

## Next

Use this provider-layer preflight as inputs for the next provider-matrix AQ attempt: remote TVR BTC symbols and direct IBKR PAXOS BTC are reachable, but the same-root AQ/provider packet still needs YF/Kraken/Binance/Bybit plus TVR and IBKR provenance, then Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree on the same rooted branch.
