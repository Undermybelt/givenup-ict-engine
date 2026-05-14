# Root Label Source Acquisition Probe

Run id: `20260511T084131+0800-codex-root-label-source-acquisition-probe`

## Result

- Missing/rejected source-label slots inspected: `564`.
- New accepted MainRegimeV2 root-label slots: `0`.
- New accepted direct `Manipulation` label sources: `0`.
- Existing Kaggle exact-label cache can newly attach missing slots: `0`.
- Re-seen rejected near-proxy Nasdaq slots: `24`.
- Gate result: `blocked_no_new_unauthenticated_source_labels_for_564_slots`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Missing Slot Shape

| Dimension | Counts |
|---|---|
| Reason | `{'missing_intraday_or_monthly_source_label': 392, 'missing_instrument_source_label': 40, 'rejected_near_underlying_proxy_not_accepted': 24, 'missing_non_yfinance_source_label': 108}` |
| Provider | `{'yfinance': 456, 'kraken_public_lowpollution_http': 108}` |
| Timeframe | `{'1m': 68, '5m': 68, '15m': 68, '30m': 68, '1h': 68, '1d': 44, '1w': 44, '1mo': 68, '4h': 68}` |
| Root | `{'Bull': 141, 'Bear': 141, 'Sideways': 141, 'Crisis': 141}` |

## Candidate Sources

| Source | Class | Decision | Reason |
|---|---|---|---|
| `kaggle_stock_market_regimes_2000_2026_existing_cache` | `independent_root_labels_partial` | `partial_existing_only_no_new_missing_slots` | Exact-source daily/weekly labels already attached where allowed; remaining gaps are intraday/monthly, non-yfinance, missing exact instruments, or rejected Nasdaq near-proxies. |
| `kaggle_us_market_regimes_1995_2024_hmm_gmm_existing_cache` | `model_inferred_hmm_gmm` | `rejected_proxy_only` | Labels are HMM/GMM state labels such as Calm/Stressful/Transitional, not independent Bull/Bear/Sideways/Crisis source labels for target instruments/timeframes. |
| `hf_nifty50_market_regime_existing_cache` | `off_universe_unlabeled_integer_regime` | `rejected_off_universe_or_proxy_only` | Nifty50 daily integer regimes are not target instruments and do not expose independent MainRegimeV2 root semantics. |
| `hf_btc_hmm6_existing_cache` | `model_inferred_hmm` | `rejected_proxy_only` | BTC HMM6 labels are model-inferred HMM states, not independent source-backed roots. |
| `dune_nft_wash_trades` | `direct_manipulation_candidate` | `blocked_missing_api_key_no_rows` | Dune schema is promising for Manipulation, but no replayable rows were exported because DUNE_API_KEY is absent and public endpoint returned 401. |

## Bounded Web Queries

- `"QQQ" "market regime" "Bull" "Bear" "Sideways" dataset`
- `"NQ" "market regime" "Bull" "Bear" "Sideways" dataset`
- `"VIX" "market regime" "Bull" "Bear" "Sideways" dataset`
- `"crude oil" "market regime" "bull" "bear" "sideways" dataset`

## Next Action

Search for non-Kaggle exact-underlying label panels or obtain authenticated/exported direct manipulation rows. Do not promote HMM/GMM/strategy/future-return labels or near-underlying proxies.
