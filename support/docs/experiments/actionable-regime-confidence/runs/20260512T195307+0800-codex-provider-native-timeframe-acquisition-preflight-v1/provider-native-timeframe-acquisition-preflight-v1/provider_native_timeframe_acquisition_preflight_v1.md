# Provider-Native Timeframe Acquisition Preflight v1

- Requested span: `2025-01-01T00:00:00Z_to_2026-05-12T00:00:00Z`.
- Provider-native timeframe fetches: `3/3`.
- Long-span native candidates: `3/3`.
- Accepted 95 contexts added: `0`.
- Promotion allowed: `false`.
- Trade usable: `false`.

## Rows

| Provider | Symbol | Native TF | Actual First | Actual Last | Rows | Span Days | Native Fetch | Long Span |
|---|---|---:|---|---|---:|---:|---|---|
| `yfinance/YF` | `SPY` | `1d` | `2025-01-02T14:30:00Z` | `2026-05-11T13:30:00Z` | 339 | 493.958 | True | True |
| `Binance` | `BTCUSDT` | `4h` | `2025-01-01T00:00:00Z` | `2026-05-12T00:00:00Z` | 2977 | 496.0 | True | True |
| `Binance` | `BTCUSDT` | `1d` | `2025-01-01T00:00:00Z` | `2026-05-12T00:00:00Z` | 497 | 496.0 | True | True |

## Interpretation

- This root is data preflight only. It does not run Auto-Quant, Pre-Bayes, BBN, CatBoost/path-ranker, or execution-tree admission.
- Native timeframe coverage can remove one blocker from `193417`, but it does not prove per-regime calibrated `>=95%` confidence.
- Board A remains fail-closed until the full chain has enough mature feedback/target rows and execution candidates leave observe/no-trade.
