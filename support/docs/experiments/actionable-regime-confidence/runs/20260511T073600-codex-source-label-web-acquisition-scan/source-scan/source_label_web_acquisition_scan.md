# Source Label Web Acquisition Scan

Run id: `20260511T073600+0800-codex-source-label-web-acquisition-scan`

Goal achieved: `false`

## Summary

- Candidate public/source-label references checked: `5`
- Full yfinance/Kraken MainRegimeV2 root-label panels found: `0`
- Root panel cells added: `0`
- Gate result: `blocked_no_public_full_matrix_source_label_panel_found`

## Source Dispositions

| Source | Useful Signal | Blocking Gap | Disposition |
|---|---|---|---|
| Kaggle `stock-market-regimes-2000-2026` | possible stock/index daily root-label evidence | not all ready-provider symbols/timeframes/cycles; prior packet coverage remains sampled | `partial_source_candidate_not_full_panel` |
| Hugging Face `sujinwo/tsie-market-regime-dataset` | large time-series table with `regime_label` | narrow IDX-style panel, label encoding not proven equivalent to MainRegimeV2 roots, not attachable to ready matrix | `method_or_narrow_panel_not_full_source_panel` |
| FRED `USREC` / NBER recession indicator | official U.S. recession/expansion timing | macro Crisis context only; no Bull/Bear/Sideways, crypto, futures, ETFs, or intraday cycles | `official_crisis_macro_context_only` |
| Mirtaheri et al. crypto manipulation source | direct event/social manipulation evidence | direct `Manipulation` overlay only; not a price-root label panel | `accepted_overlay_source_only` |
| Xu and Livshits pump-and-dump source | direct pump-and-dump event context | event overlay/research context only; not root labels or full coverage | `overlay_or_research_context_only` |

## Accounting

- No public source in this scan supplies independent source-backed `Bull` / `Bear` / `Sideways` / `Crisis` labels for every ready yfinance/Kraken symbol/timeframe cell.
- Official FRED/NBER recession data can support U.S. macro Crisis context, but it cannot complete all four MainRegimeV2 roots or all species/cycles.
- Direct manipulation papers/sources remain overlay evidence only and cannot be counted as OHLCV bar-root labels.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Gate result: `blocked_no_public_full_matrix_source_label_panel_found`
