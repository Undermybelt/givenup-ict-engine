# Public Source Label Candidate Sweep

Run id: `20260511T081200+0800-codex-public-source-label-candidate-sweep`

## Purpose

Search for public labeled market-regime sources that could fill the `596` missing current MainRegimeV2 root-label slots without promoting proxy labels.

## Current Blocker

- Root-label slots: `612`
- Direct source-label attached slots: `16`
- Missing slots: `596`
- Full four-root cells: `4`
- Required price roots: `Bull`, `Bear`, `Sideways`, `Crisis`
- Separate direct class: `Manipulation`

## Candidate Sources

| Source | Decision | Reason |
|---|---|---|
| Kaggle stock-market-regimes-2000-2026 | partial_only | Already used; attaches only `16/612` slots, limited to yfinance `^DJI` / `^GSPC` at `1d` / `1w` |
| Hugging Face `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | rejected_proxy_only | Labels are HMM-derived/model-inferred BTCUSD `5m`/`15m` regimes with arbitrary state ids/post-hoc interpretation; not independent source-backed root labels |
| Hugging Face `sujinwo/tsie-market-regime-dataset` | rejected_sidecar_only | Prior metadata audit found `0` accepted/manual full-root panel candidates; `Crisis` and direct `Manipulation` labels are missing |

## Result

New accepted source-label slots: `0`.

Goal achieved: false.

Accepted full panel: false.

Proxy promoted: false.

Next action: acquire non-public/proprietary or explicitly labeled multi-asset multi-timeframe source labels for the missing `596` slots; public HMM/HF/OHLCV-derived regime labels remain sidecar-only.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
