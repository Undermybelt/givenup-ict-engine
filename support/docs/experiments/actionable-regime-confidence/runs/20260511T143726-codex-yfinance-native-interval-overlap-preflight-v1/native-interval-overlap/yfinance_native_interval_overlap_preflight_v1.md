# YFinance Native Interval Overlap Preflight v1

Run ID: `20260511T143726+0800-codex-yfinance-native-interval-overlap-preflight-v1`

This run checks which native yfinance intervals actually overlap the stock-market-regimes source-label dates.
It does not add a confidence gate; it narrows the next viable timeframe route.

## Result

- Source panel after warmup: `39` tickers, `2001-01-02` to `2026-01-30`.
- Intervals checked: `1m, 5m, 15m, 30m, 60m, 90m, 1h`.
- Intervals with any source-date overlap: `60m, 1h`.
- Canonical interval with source-date overlap: `1h`.
- Alias interval with source-date overlap: `60m`.
- Blocked native intervals with no source-date overlap: `1m, 5m, 15m, 30m, 90m`.
- Accepted confidence rows added: `0`.
- Full objective achieved: `false`.
- Runtime code changed: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Trade usable: `false`.
- Gate result: `yfinance_native_interval_overlap_preflight_v1=no_new_confidence_gate_1h_only_native_overlap`.

## Interval Summary

| Interval | Period | Ready Tickers | Provider First Date | Provider Last Date | Source-Overlap Ticker-Days | Bull | Bear | Sideways | Crisis | Decision |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---|
| `1m` | `7d` | 39 | 2026-04-30 | 2026-05-08 | 0 | 0 | 0 | 0 | 0 | `blocked_no_source_date_overlap` |
| `5m` | `60d` | 39 | 2026-02-12 | 2026-05-08 | 0 | 0 | 0 | 0 | 0 | `blocked_no_source_date_overlap` |
| `15m` | `60d` | 39 | 2026-02-12 | 2026-05-08 | 0 | 0 | 0 | 0 | 0 | `blocked_no_source_date_overlap` |
| `30m` | `60d` | 39 | 2026-02-12 | 2026-05-08 | 0 | 0 | 0 | 0 | 0 | `blocked_no_source_date_overlap` |
| `60m` | `730d` | 36 | 2023-06-12 | 2026-05-08 | 23826 | 11483 | 5023 | 5170 | 2150 | `overlap_alias_of_1h` |
| `90m` | `60d` | 39 | 2026-02-12 | 2026-05-08 | 0 | 0 | 0 | 0 | 0 | `blocked_no_source_date_overlap` |
| `1h` | `730d` | 39 | 2023-06-12 | 2026-05-08 | 25812 | 12486 | 5430 | 5731 | 2165 | `overlap` |

## Decision

- Native yfinance sub-hour intervals do not overlap the current source panel because retained provider bars start after the panel's `2026-01-30` label cutoff.
- `60m` is treated as an alias of `1h`, not a new cycle.
- Additional native yfinance intraday work should wait for source-label extension or a different overlapping source-label panel.
- A separate derived `4h` artifact may be useful, but it must be labeled as derived from `1h`, not provider-native.
