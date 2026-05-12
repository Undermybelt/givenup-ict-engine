# Local Cache Source Label Audit

Run id: `20260511T073800+0800-codex-local-cache-source-label-audit`

Goal achieved: `false`

## Summary

- Rows/files scanned: `347`
- Auto-Quant OHLCV cache cells: `52`
- Auto-Quant symbols represented: `AAPL, AAPL_USD, AVAX_USDT, BNB_USDT, BTC-USD, BTCY_USD, BTC_USDT, DIA_USD, ES_F, ES_USD, ETH_USDT, EURUSD_X, EUR_USD, GLD_USD, IWM_USD, NQ_USD, QQQ_USD, SOL_USDT, SPY, SPY_USD, binance_BTCUSDT, bybit_BTCUSDT_linear, kraken_AAPLx, kraken_EURUSD, kraken_PF_SPX, kraken_SPYx, kraken_XBTUSD`
- Auto-Quant timeframes represented: `15m, 1d, 1h, 4h, 5m`
- Independent source-backed MainRegimeV2 label sources found: `0`
- Full-root label panel cells available: `0`

## Counts By Status

| Status | Count |
|---|---:|
| `generated_or_runtime_labelish_json_not_independent_source` | 170 |
| `labelish_or_generated_columns_not_independent_source` | 6 |
| `no_root_label_columns` | 2 |
| `no_root_label_keys` | 117 |
| `ohlcv_only` | 52 |

## Accounting

- Local and Auto-Quant caches are useful for replay/data breadth, but they do not contain source-backed `Bull` / `Bear` / `Sideways` / `Crisis` labels.
- HMM states, future targets, strategy predictions, and repo runtime artifacts remain generated/proxy evidence and are not counted as accepted labels.
- Runtime code changed: false. Thresholds relaxed: false. Raw OHLCV committed: false. Trade usable: false.

Gate result: `blocked_local_and_autoquant_cache_have_no_independent_root_label_panel`
