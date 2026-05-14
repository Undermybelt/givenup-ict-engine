# Provider-Native Timeframe Retry Readback v1

- Retry exits zero: `3/3`.
- Native timeframe fetches with rows: `3/3`.
- Long-span native candidates: `3/3`.
- Accepted 95 contexts added: `0`.
- Promotion allowed: `false`.
- Trade usable: `false`.

| Provider | Symbol | Timeframe | Rows | Actual Start | Actual End | Span Days | Native | Board A Support |
|---|---|---:|---:|---|---|---:|---|---|
| `yfinance/YF` | `SPY` | `1d` | 1597 | `2020-01-02T14:30:00Z` | `2026-05-11T13:30:00Z` | 2320.958 | True | False |
| `Binance` | `BTCUSDT` | `4h` | 13938 | `2020-01-01T00:00:00Z` | `2026-05-12T00:00:00Z` | 2323.0 | True | False |
| `Binance` | `BTCUSDT` | `1d` | 2324 | `2020-01-01T00:00:00Z` | `2026-05-12T00:00:00Z` | 2323.0 | True | False |

Gate:
- `preflight_only=true`
- `active_claim_closed:195307_provider_native_timeframe_acquisition_preflight_v1` only after Board append
- `accepted_95_contexts_added_0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
