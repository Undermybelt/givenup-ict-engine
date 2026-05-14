# Provider Universe Manifest

Run id: `20260511T070103+0800-codex-provider-universe-manifest`

This manifest defines the first concrete `full species / full cycles` coverage contract for Board A. It is not a passing completion gate.

## Provider Status

`ict-engine provider-status --agent` returned:

- `entry_model:2/2 ready`
- `live_runtime:1/3 ready`
- `local_runtime:1/2 ready`
- `market_data:1/7 ready`

Ready for market data now:

- `yfinance`

Pending market-data providers:

| Provider | Status |
|---|---|
| `binance_public` | `configured_runtime_unhealthy: python3_provider_dependencies_missing` |
| `bybit_public` | `configured_runtime_unhealthy: python3_provider_dependencies_missing` |
| `ibkr` | `configured_runtime_unhealthy: ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `kraken_public` | `configured_runtime_unhealthy: python3_provider_dependencies_missing` |
| `polymarket_public` | `configured_runtime_unhealthy: python3_provider_dependencies_missing` |
| `tradingview_mcp` | `configured_runtime_unhealthy: tradingview_mcp_connectivity_probe_failed` |

## Repo Market Catalog Universe

Market keys: `NQ`, `ES`, `YM`, `GC`, `CL`.

YFinance symbols to try first:

`CL=F`, `DIA`, `ES=F`, `GC=F`, `GLD`, `NQ=F`, `QQQ`, `SPY`, `USO`, `YM=F`, `^DJI`, `^GSPC`, `^NDX`, `^VIX`.

TradingViewRemix symbols are present in config but currently blocked by provider health:

`AMEX:DIA`, `AMEX:GLD`, `AMEX:SPY`, `AMEX:USO`, `CBOE:VIX`, `DJ:DJI`, `NASDAQ:NDX`, `NASDAQ:QQQ`, `OANDA:XAUUSD`, `SP:SPX`, `TVC:USOIL`.

IBKR symbols are present in config but currently blocked by local runtime dependencies:

`DIA`, `DJI`, `GLD`, `NDX`, `QQQ`, `SPX`, `SPY`, `USO`, `VIX`, `XAUUSD`.

Relationship universe adds: futures `BZ`, `ES`, `NQ`, `SI`, `YM`; ETFs/options `BNO`, `DIA`, `QQQ`, `SLV`, `SPY`; CFD/crypto companions `BTCUSD`, `ETHUSD`, `NAS100`, `SOLUSD`, `UKOIL`, `US30`, `US500`, `USOIL`, `XAGUSD`, `XAUUSD`, plus `BTC`, `ETH`, `SOL`; volatility proxies `^GVZ`, `^OVX`, `^VIX`, `^VXN`.

## Cycle Ladder

Try first for bar roots where provider-supported:

`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`.

Event and snapshot roots use separate lanes:

- `Manipulation`: chronological event train/calibration/test plus coin/channel breadth.
- Options enrichment: `options_snapshot`.

## Next Matrix Contract

1. For bar roots, attempt every ready-provider symbol in the repo catalog across the cycle ladder where supported.
2. For pending providers, record blocked cells with exact provider-status reason.
3. For `Manipulation`, keep OHLCV proxy blocked and enumerate direct event sources by coin/channel/time window.
4. Do not lower Wilson/support/coverage/ECE gates.

Gate result: `provider_universe_manifest_built_full_matrix_pending`.
