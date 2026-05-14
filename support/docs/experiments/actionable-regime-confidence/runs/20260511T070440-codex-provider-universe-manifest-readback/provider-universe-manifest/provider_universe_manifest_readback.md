# Provider Universe Manifest Readback

Run id: `20260511T070440+0800-codex-provider-universe-manifest-readback`

This readback preserves the later taxonomy correction: main price roots are `Bull`, `Bear`, `Sideways`, and `Crisis`; `Manipulation` is a direct-event overlay gate.

Provider status from `ict-engine provider-status --agent`:

- `market_data:1/7 ready`
- Ready market-data provider: `yfinance`
- Pending provider cells must be recorded, not silently skipped:
  - `ibkr`: `ibkr_runtime_dependencies_missing_with_gateway_reachable`
  - `tradingview_mcp`: `tradingview_mcp_connectivity_probe_failed`
  - `binance_public` / `bybit_public` / `kraken_public` / `polymarket_public`: `python3_provider_dependencies_missing`

YFinance-first matrix inputs:

- Symbols: `CL=F`, `DIA`, `ES=F`, `GC=F`, `GLD`, `NQ=F`, `QQQ`, `SPY`, `USO`, `YM=F`, `^DJI`, `^GSPC`, `^NDX`, `^VIX`
- Timeframe ladder: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`

Gate result: `provider_universe_manifest_readback_yfinance_matrix_next`.

Goal achieved under `full species / full cycles`: `false`.
