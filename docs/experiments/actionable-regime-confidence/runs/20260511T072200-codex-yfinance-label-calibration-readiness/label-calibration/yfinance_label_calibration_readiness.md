# YFinance Label Calibration Readiness

Run id: `20260511T072200+0800-codex-yfinance-label-calibration-readiness`

Goal achieved: `false`

## Summary

- Cells audited: `126`
- Data OK cells: `126`
- Close-only scored cells: `126`
- Independent-label-ready cells: `0`
- Unsupported label cells: `126`

## Main Price Root Readiness

| Root | Data OK Cells | Scored Cells | Label Ready Cells | Unsupported Label Cells | Close-Only Candidate Rows | Gate |
|---|---:|---:|---:|---:|---:|---|
| `Bull` | 126 | 126 | 0 | 126 | 129834 | `blocked_missing_independent_source_labels` |
| `Bear` | 126 | 126 | 0 | 126 | 7685 | `blocked_missing_independent_source_labels` |
| `Sideways` | 126 | 126 | 0 | 126 | 268486 | `blocked_missing_independent_source_labels` |
| `Crisis` | 126 | 126 | 0 | 126 | 29 | `blocked_missing_independent_source_labels` |

## Manipulation Overlay

- Yfinance OHLCV/bar cells accepted for direct `Manipulation`: `0`.
- Reason: the overlay requires direct event, order-lifecycle, L2/L3/MBO, social, or on-chain evidence; bar proxies fail closed.
- Accepted direct variety preserved: `classified_telegram_coin_pump_event_present` from the Mehrnoom/Mirtaheri Telegram event packet.

## Pending Provider Cells

- `ibkr: ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `tradingview_mcp: tradingview_mcp_connectivity_probe_failed`
- `binance_public/bybit_public/kraken_public/polymarket_public: python3_provider_dependencies_missing`

## Accounting

- This run converts the yfinance label blocker into an explicit 126-cell readiness matrix.
- It does not derive labels from the same close-only features.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `blocked_yfinance_full_matrix_missing_independent_root_labels`
