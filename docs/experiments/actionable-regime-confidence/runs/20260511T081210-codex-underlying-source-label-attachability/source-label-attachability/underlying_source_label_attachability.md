# Underlying Source Label Attachability

Run id: `20260511T081210+0800-codex-underlying-source-label-attachability`

## Result

- Root-label slots audited: `612`
- Direct or exact-underlying source-label candidate slots: `48`
- Missing or rejected source-label slots: `564`
- Full four-root cells: `12`
- Attached slots by root: `{'Bear': 12, 'Bull': 12, 'Crisis': 12, 'Sideways': 12}`
- Attached slots by relation: `{'exact_source_instrument': 16, 'exact_underlying_index': 32}`

Exact-underlying source labels are accepted only for same-underlying market exposures:

- `^DJI` source labels can attach to `DIA` daily/weekly slots.
- `^GSPC` source labels can attach to `ES=F` daily/weekly slots.
- `^GSPC` source labels can attach to `SPY` daily/weekly slots.
- `^DJI` source labels can attach to `YM=F` daily/weekly slots.

Near-proxy mappings are rejected rather than promoted:

- `^IXIC` is not accepted as an exact source label for `NQ=F`.
- `^IXIC` is not accepted as an exact source label for `QQQ`.
- `^IXIC` is not accepted as an exact source label for `^NDX`.

This is source-label availability only; it is not accepted full-universe/full-cycle confidence.

## Blocker

Only 48 of 612 current MainRegimeV2 root-label slots have direct or exact-underlying source-label candidates; 564 slots remain missing or rejected. Intraday/monthly, Kraken/non-yfinance, non-index commodities/crypto, near-proxy Nasdaq mappings, and full direct Manipulation coverage remain outside accepted source-label coverage.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
