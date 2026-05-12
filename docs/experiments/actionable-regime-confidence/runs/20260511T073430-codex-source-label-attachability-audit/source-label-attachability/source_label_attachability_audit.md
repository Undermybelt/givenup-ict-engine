# Source Label Attachability Audit

Run id: `20260511T073430+0800-codex-source-label-attachability-audit`

Goal achieved: `false`

## Summary

- Yfinance matrix cells audited: `126`
- Cells with any existing accepted root-packet overlap: `14`
- Cells with all four MainRegimeV2 roots attached: `0`
- Unsupported full-root label cells: `126`
- Previous readiness label-ready cells: `0`

## Root Overlap

| Root | Existing Packet Overlap Cells | Source Packet | Test Wilson95 | Granularity |
|---|---:|---|---:|---|
| `Bull` | 4 | `20260511T035045+0800-codex-kaggle-bull-coverage-buffer-gate` | 0.961931 | `reported_symbol_timeframe_contexts` |
| `Bear` | 4 | `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate` | 0.992722 | `instrument_timeframe_cross_product_from_report_summary` |
| `Sideways` | 6 | `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate` | 0.995568 | `instrument_timeframe_cross_product_from_report_summary` |
| `Crisis` | 4 | `20260510T235220+0800-codex-broader-root-v2-probe` | 0.995981 | `reported_symbol_timeframe_contexts` |

## Manipulation Overlay

- Existing accepted `Manipulation` packet is direct social/event-confirmed.
- Yfinance OHLCV/bar attachable cells: `0`.
- It remains suppress/abstain/cooldown evidence, not a main price-root label and not a bar proxy.

## Unsupported Coverage

- Timeframes without complete four-root labels: `15m, 1d, 1h, 1m, 1mo, 1w, 30m, 4h, 5m`
- Symbols without complete four-root labels: `CL=F, DIA, ES=F, GC=F, GLD, NQ=F, QQQ, SPY, USO, YM=F, ^DJI, ^GSPC, ^NDX, ^VIX`

## Pending Provider Cells

- `ibkr: ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `tradingview_mcp: tradingview_mcp_connectivity_probe_failed`
- `binance_public/bybit_public/kraken_public/polymarket_public: python3_provider_dependencies_missing`

## Accounting

- This run does not create new labels, fetch raw data, or relax thresholds.
- Sparse overlap from accepted packets is provenance only; it is not enough for the expanded all-species/all-cycle gate.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `blocked_existing_packets_do_not_form_full_yfinance_label_panel`
