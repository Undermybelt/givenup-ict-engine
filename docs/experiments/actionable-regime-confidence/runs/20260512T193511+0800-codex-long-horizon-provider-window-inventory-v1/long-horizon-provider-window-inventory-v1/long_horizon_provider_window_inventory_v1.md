# Long-Horizon Provider Window Inventory v1

- Providers present: `6/6`.
- Long-span candidates by span/rows: `2/6`.
- Native provider cross-timeframe fetches: `0/6`.
- Board A training-adequate rows: `0/6`.
- Accepted 95 contexts added: `0`.
- Promotion allowed: `false`.

## Provider Rows

| Provider | Market | Span Days | 1h Rows | 4h Rows | 1d Rows | Long Span | Native XTF | Training Adequate | Blockers |
|---|---|---:|---:|---:|---:|---|---|---|---|
| `yfinance/YF` | `equity` | 494.2 | 2355 | 588 | 98 | True | False | False | `no_provider_native_cross_timeframe_fetch` |
| `Binance` | `crypto` | 496.0 | 2400 | 600 | 100 | True | False | False | `no_provider_native_cross_timeframe_fetch` |
| `Bybit` | `crypto` | 41.6 | 1000 | 250 | 41 | False | False | False | `short_provider_span_or_low_1h_rows;no_provider_native_cross_timeframe_fetch;daily_rows_below_90;provider_window_under_180_days` |
| `Kraken` | `crypto` | 83.3 | 2000 | 500 | 83 | False | False | False | `short_provider_span_or_low_1h_rows;no_provider_native_cross_timeframe_fetch;daily_rows_below_90` |
| `IBKR` | `equity` | 130.0 | 1427 | 356 | 59 | False | False | False | `short_provider_span_or_low_1h_rows;no_provider_native_cross_timeframe_fetch;daily_rows_below_90;provider_window_under_180_days` |
| `TradingViewRemix/TVR` | `crypto` | 30.0 | 719 | 179 | 29 | False | False | False | `short_provider_span_or_low_1h_rows;no_provider_native_cross_timeframe_fetch;daily_rows_below_90;provider_window_under_180_days` |

## Interpretation

- This is inventory only, not a confidence packet.
- Existing artifacts contain six provider-backed rows, but 4h/1d are derived from 1h artifacts rather than provider-native cross-timeframe fetches.
- Only yfinance/YF and Binance look long-span enough by current rows/span heuristics; the rest remain short-window or low-row evidence.
- No full provider/AQ -> Pre-Bayes/BBN -> CatBoost/path-ranker -> execution-tree rerun was performed in this slice.
- Board A remains fail-closed.
