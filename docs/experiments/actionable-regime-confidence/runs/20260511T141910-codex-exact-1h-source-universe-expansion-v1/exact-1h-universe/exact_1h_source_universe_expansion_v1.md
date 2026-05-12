# Exact 1h Source Universe Expansion v1

Run ID: `20260511T141910+0800-codex-exact-1h-source-universe-expansion-v1`

This run expands the exact same-source direction from the AMD/CVX slice to every ticker in the stock-market-regimes source panel.
It accepts only strict ticker/root rows where that same ticker and root pass both 2024 calibration and 2025 heldout-time gates.

## Result

- Source-panel tickers checked: `39`.
- Yfinance `1h` ready tickers: `39`.
- Scoped ticker/root slots: `156`.
- Strict accepted ticker/root rows: `41`.
- Strict blocked ticker/root rows: `115`.
- Accepted by root: `{'Bear': 4, 'Bull': 27, 'Crisis': 3, 'Sideways': 7}`.
- Accepted ticker count: `35`.
- Gate result: `exact_1h_source_universe_expansion_v1=accepted41_strict_ticker_root_rows_full_goal_still_blocked`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.

## Policy

- Attach only the same ticker's source-panel daily `MainRegimeV2` root to `1h` bars whose exchange-local session date matches the source date.
- Strict row acceptance requires that ticker/root itself pass 2024 calibration and 2025 heldout-time support/Wilson gates.
- Pooled panel context is reported separately and is not used to accept ticker/root rows.
- No ETF/futures/index crosswalk, OHLCV-derived label, HMM state, generated label, strategy prediction, or future-return label is used.

## Accepted By Ticker

| Ticker | Accepted Roots |
|---|---|
| `AAPL` | `Bull` |
| `ABBV` | `Bull` |
| `AMD` | `Crisis` |
| `AMZN` | `Bull` |
| `BAC` | `Bull` |
| `CAT` | `Bull` |
| `COP` | `Bear` |
| `CSCO` | `Bull` |
| `CVX` | `Bull,Sideways` |
| `DIS` | `Sideways` |
| `GE` | `Bull` |
| `GOOGL` | `Bull` |
| `GS` | `Bull` |
| `INTC` | `Crisis` |
| `JNJ` | `Bull` |
| `JPM` | `Bull` |
| `MCD` | `Bull,Sideways` |
| `META` | `Bull` |
| `MS` | `Bull` |
| `MSFT` | `Bull,Sideways` |
| `NFLX` | `Bull` |
| `NKE` | `Bear` |
| `NVDA` | `Bull` |
| `PFE` | `Bear,Sideways` |
| `SBUX` | `Bear` |
| `T` | `Bull` |
| `TSLA` | `Crisis` |
| `VZ` | `Bull,Sideways` |
| `WFC` | `Bull` |
| `WMT` | `Bull` |
| `XOM` | `Bull` |
| `^DJI` | `Bull` |
| `^GSPC` | `Bull` |
| `^IXIC` | `Bull` |
| `^RUT` | `Bull,Sideways` |

## Pooled Panel Context

| Root | 2024 Support | 2024 Wilson95 | 2025 Support | 2025 Wilson95 | Panel Context Accepted |
|---|---:|---:|---:|---:|---|
| `Bull` | 5262 | 0.999270 | 4538 | 0.999154 | `true` |
| `Bear` | 1846 | 0.997923 | 2053 | 0.998132 | `true` |
| `Sideways` | 2158 | 0.998223 | 2134 | 0.998203 | `true` |
| `Crisis` | 562 | 0.993211 | 1025 | 0.996266 | `true` |

## Next

- Use the strict accepted ticker/root rows as positive exact-source 1h supply.
- Expand to additional provider-native timeframes only after checking actual source-date overlap.
- Do not promote pooled panel context as per-ticker support.
