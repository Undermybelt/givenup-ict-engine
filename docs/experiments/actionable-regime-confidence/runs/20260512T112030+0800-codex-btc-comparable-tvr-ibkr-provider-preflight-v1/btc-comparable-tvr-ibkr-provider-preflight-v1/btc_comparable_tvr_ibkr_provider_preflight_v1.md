# BTC-Comparable TVR/IBKR Provider Preflight v1

Run id: `20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1`

## Scope
BTC-comparable provider preflight for the Board A provider-matrix gap. This packet checks TradingViewRemix / `tradingview_mcp` BTC OHLCV and IBKR PAXOS BTC historical bars only. It does not run Auto-Quant, select history, mutate source/control roots, or promote downstream evidence.

## Results
- TVR provider-status exit `0`; ready `True`; status `ready`; reason `mcp_url_and_api_key_available`.
- TVR `BINANCE:BTCUSDT` 1h default fetch exit `0`; ok `True`; rows `720`; first `2026-04-12T04:00:00Z`; last `2026-05-12T03:00:00Z`.
- TVR `COINBASE:BTCUSD` 1h default fetch exit `0`; ok `True`; rows `715`; first `2026-04-12T04:00:00Z`; last `2026-05-12T03:00:00Z`.
- TVR local-stdio `BINANCE:BTCUSDT` 1h fetch exit `1`; ok `False`; error `tradingview MCP tool 'get_ohlcv' error: Failed to fetch OHLCV for 'BINANCE:BTCUSDT': Both direct and proxy connections failed: HTTP Error 404: Not Found`.
- IBKR PAXOS BTC 1h MIDPOINT bulk exit `0`; rows `45`; first `2026-05-10T07:00:00+00:00`; last `2026-05-12T03:00:00+00:00`; csv `docs/experiments/actionable-regime-confidence/runs/20260512T112030+0800-codex-btc-comparable-tvr-ibkr-provider-preflight-v1/derived/ibkr_btc_paxos/BTC_1h_midpoint.csv`.

## Decision
- Gate: `btc_comparable_tvr_ibkr_provider_preflight_v1=tvr_btc_and_ibkr_paxos_btc_rows_present_provider_layer_only_no_aq_no_promotion`.
- This repairs part of the provider-layer gap: TVR now has BTC OHLCV through the default credential path, and IBKR has BTC PAXOS historical bars through the low-pollution bulk path.
- It remains provider-layer evidence only. It is not same-root AQ/provider provenance, not selected-history approval, not source/control unlock, not canonical merge input, and not ordered Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree evidence.
- Accepted rows added: `0`.
- Mature rooted branch observations added: `0`.
- Promotion allowed: `false`.
- `update_goal=false`.
