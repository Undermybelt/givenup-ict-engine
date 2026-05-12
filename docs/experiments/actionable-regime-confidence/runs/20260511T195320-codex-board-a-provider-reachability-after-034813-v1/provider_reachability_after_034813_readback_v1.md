# Provider Reachability After 034813 Readback v1

Run root:
`docs/experiments/actionable-regime-confidence/runs/20260511T195320-codex-board-a-provider-reachability-after-034813-v1`

This readback registers the provider evidence as visibility evidence for Board B. It is not accepted regime evidence, not a profitability packet, and not a downstream promotion rerun.

## Command Results

| Command | Exit | Readback |
|---|---:|---|
| `00_provider_status_agent` | 0 | Summary `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready` |
| `01_provider_status_yfinance` | 0 | yfinance status command completed |
| `02_provider_status_tradingview_mcp` | 0 | status command completed but provider remained unhealthy |
| `03_provider_status_ibkr` | 0 | status command completed but runtime remained unhealthy |
| `04_provider_status_kraken_cli` | 0 | Kraken CLI status command completed |
| `05_provider_status_kraken_public` | 0 | status command completed but provider remained unhealthy |
| `06_harness_yfinance_qqq_1d` | 0 | yfinance harness succeeded |
| `07_harness_tradingview_qqq_1d` | 1 | TradingViewRemix/MCP fetch failed |
| `08_harness_ibkr_qqq_1d` | 1 | ict-engine IBKR harness failed |
| `09_fetch_external_ibkr_qqq_1m` | 0 | external IBKR fetch wrote 21 QQQ rows |
| `10_kraken_cli_xbtusd_1h` | 0 | Kraken CLI returned XBT/USD 1h OHLC |
| `11_fetch_external_kraken_xbtusd_1h` | 2 | original command shape failed |
| `11b_fetch_external_kraken_xbtusd_1h_corrected` | 2 | corrected pair attempt was blocked by `uv` fetching `pandas` |
| `11c_fetch_external_kraken_xbtusd_1h_python3_corrected` | 1 | intermediate python3 correction failed |
| `11d_fetch_external_kraken_xbtusd_1h_python3_corrected` | 0 | corrected python3 command wrote 721 XBTUSD 1h rows |

## Provider Decision

- yfinance: usable in this run; harness passed.
- Kraken: CLI usable; corrected external python3 fetch also produced `721` 1h rows.
- IBKR: direct external fetch succeeded with `21` rows, but ict-engine provider/harness still remains unhealthy and non-promoting.
- TradingViewRemix/MCP: still blocked; harness failed with MCP `get_ohlcv` error.

## Promotion Decision

Gate: `diagnostic_only:provider_visibility_not_profitability`.

Promotion: `false`.

Next: use the working provider paths as inputs only after a rooted Board B branch has a measured backtest packet; do not treat provider reachability as profitability or regime-confidence evidence.
