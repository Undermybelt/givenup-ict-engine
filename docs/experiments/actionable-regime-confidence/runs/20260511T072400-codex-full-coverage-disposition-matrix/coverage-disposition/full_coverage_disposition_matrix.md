# Full Coverage Disposition Matrix

Run id: `20260511T072400+0800-codex-full-coverage-disposition-matrix`

Goal achieved: `false`

## Summary

- Bar provider/symbol/timeframe cells dispositioned: `397`
- Direct `Manipulation` varieties dispositioned: `9`
- Accepted full-cycle/full-universe gate: `false`

## Disposition Counts

| Disposition | Count |
|---|---:|
| `accepted_overlay` | 1 |
| `blocked_or_diagnostic` | 8 |
| `blocked_provider_unavailable` | 271 |
| `unsupported_for_accepted_confidence` | 126 |

## Provider Counts

| Provider | Cells |
|---|---:|
| `binance_public` | 27 |
| `bybit_public` | 27 |
| `direct_event_source` | 9 |
| `ibkr` | 90 |
| `kraken_public` | 27 |
| `polymarket_public` | 1 |
| `tradingview_mcp` | 99 |
| `yfinance` | 126 |

## Accounting

- All current manifest cells are now represented with an explicit disposition.
- Yfinance remains blocked for acceptance by missing independent root labels, despite usable/scored close cells.
- Pending provider cells are blocked by their provider-status reasons, not silently skipped.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `full_coverage_dispositioned_but_acceptance_blocked`
