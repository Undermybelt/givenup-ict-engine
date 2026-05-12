# YFinance Root Gate Score Matrix

Run id: `20260511T072000+0800-codex-yfinance-root-gate-score-matrix`

Goal achieved: `false`

## Summary

| Root | Scored Cells | Hit Cells | Candidate Rows | Timeframes With Hits | Symbols With Hits |
|---|---:|---:|---:|---|---:|
| `Bull` | 126 | 112 | 129834 | `1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo` | 14 |
| `Bear` | 126 | 52 | 7685 | `5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo` | 14 |
| `Sideways` | 126 | 95 | 268486 | `1m, 5m, 15m, 30m, 1h, 4h, 1d` | 14 |
| `Crisis` | 126 | 2 | 29 | `1d, 1w` | 2 |

## Accounting

- This is close-only rule/gate scoring over the yfinance full matrix.
- It does not claim accepted 95% confidence because source labels are absent for every symbol/timeframe cell.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `yfinance_full_matrix_root_gate_scored_confidence_pending`
