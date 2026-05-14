# UV Provider Readiness + Kraken Public Smoke

Run id: `20260511T072600+0800-codex-uv-provider-readiness-kraken-smoke`

Goal achieved: `false`

## Provider Status

- UV wrapper summary: `market_data:6/7 ready`
- Ready providers: `binance_public, bybit_public, ibkr, kraken_public, polymarket_public, yfinance`
- Pending providers: `tradingview_mcp@market_data:configured_runtime_unhealthy:tradingview_mcp_connectivity_probe_failed`

## Kraken Public Futures Matrix

- Cells attempted: `27`
- OK cells: `24`
- Failed cells: `0`
- Unsupported cells: `3`
- Raw OHLCV committed: `false`

## Accounting

- This opens a data-provider lane only; it does not attach independent root labels.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `uv_wrapper_opened_provider_lane_kraken_data_available_root_confidence_pending`
