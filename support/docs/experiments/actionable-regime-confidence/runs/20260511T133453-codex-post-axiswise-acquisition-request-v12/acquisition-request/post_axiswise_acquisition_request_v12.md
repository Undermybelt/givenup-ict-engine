# Post-Axiswise Acquisition Request v12

Run ID: `20260511T133453+0800-codex-post-axiswise-acquisition-request-v12`

## Result

- Rebased the stale v2 acquisition request from `564` rows to `556` active post-axiswise source-label requests.
- Superseded rows removed: `8`; all are same-source stock/index rows now covered by the `131922` axiswise gate.
- Accepted confidence added: `0`; this is a current-target acquisition request, not a confidence gate.
- Full objective achieved: `false`.

## Active Counts

- By provider: `{'kraken_public_lowpollution_http': 108, 'yfinance': 448}`.
- By timeframe: `{'15m': 68, '1d': 44, '1h': 68, '1m': 68, '1mo': 60, '1w': 44, '30m': 68, '4h': 68, '5m': 68}`.
- By root: `{'Bear': 139, 'Bull': 139, 'Crisis': 139, 'Sideways': 139}`.

## High-Yield Batches

| Batch | Rows | Required Evidence | Forbidden Shortcut |
|---|---:|---|---|
| `native_intraday_yfinance_index_etf_futures` | 336 | native intraday MainRegimeV2 labels or owner-approved source labels for all four roots | do not use OHLCV/HMM/future-return generated labels as acceptance evidence |
| `kraken_full_species_native_labels` | 108 | crypto exact-underlying source labels across roots/timeframes with chronological and heldout-symbol validation | do not promote raw Kraken bars or provider readiness to regime labels |
| `yfinance_non_same_source_daily_weekly_monthly_species` | 112 | exact-underlying labels for commodities, ETFs, futures, volatility, and non-same-source instruments | do not infer labels from the accepted US stock/index panel unless an explicit crosswalk is approved and calibrated |

## Guardrails

- Provider bars/catalog readiness is not source-label evidence.
- HMM, OHLCV, strategy prediction, or future-return labels cannot close these rows.
- Direct `Manipulation` matched negatives remain a separate direct-evidence lane.
- No runtime code changed; no thresholds relaxed; no raw data committed; not trade usable.
