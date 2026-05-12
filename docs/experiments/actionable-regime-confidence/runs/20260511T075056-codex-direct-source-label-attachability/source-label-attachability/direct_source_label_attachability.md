# Direct Source Label Attachability

Run id: `20260511T075056+0800-codex-direct-source-label-attachability`

## Result

- Root-label slots audited: `612`
- Direct source-label candidate slots: `16`
- Missing source-label slots: `596`
- Full four-root cells: `4`
- Attached slots by root: `{'Bull': 4, 'Bear': 4, 'Sideways': 4, 'Crisis': 4}`

The attachable cells are limited to yfinance index daily/weekly rows from the Kaggle stock/index source panel.
This is source-label availability only; it is not accepted full-universe/full-cycle confidence.

## Blocker

Only 16 of 612 current MainRegimeV2 root-label slots have direct source-label candidates from this public stock/index panel; only 4 provider/instrument/timeframe cells have all four price roots, all on yfinance 1d/1w indices. Kraken, most yfinance symbols, intraday/monthly timeframes, and Manipulation direct-event coverage remain outside this source.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
