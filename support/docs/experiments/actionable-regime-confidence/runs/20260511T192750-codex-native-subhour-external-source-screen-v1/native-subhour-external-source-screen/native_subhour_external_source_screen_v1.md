# Native Subhour External Source Screen v1

Run ID: `20260511T192750+0800-codex-native-subhour-external-source-screen-v1`

Targeted screen for public native sub-hour source-owned market-regime labels. This is narrower than the broad external source-label screens and does not download raw rows.

## Decision

`native_subhour_external_source_screen_v1=no_ready_native_subhour_source_labels`

- Kaggle targeted queries: `3`.
- Hugging Face targeted queries: `5`.
- Candidate records dispositioned: `3`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Native sub-hour source overlap closed: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Candidate Disposition

| Source | Candidate | Decision | Reason |
|---|---|---|---|
| `huggingface` | [`akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`](https://huggingface.co/datasets/akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD) | `blocked_hmm_generated_labels_not_source_owned` | Only HF native-subhour regime hit from targeted API search; labels are HMM-6 inferred from 5m/15m OHLCV and technical indicators, so they remain generated/proxy labels rather than source-owned MainRegimeV2 rows. |
| `kaggle` | [`thisathdamiru/bybit-multi-crypto-historical-data-2020-2026`](https://www.kaggle.com/datasets/thisathdamiru/bybit-multi-crypto-historical-data-2020-2026) | `blocked_raw_provider_panel_no_regime_labels` | Kaggle targeted searches surface this raw Bybit historical data set, but search metadata indicates historical crypto data rather than source-owned regime labels or owner-approved MainRegimeV2 equivalence. |
| `kaggle` | [`toocool69/synthetic-stock-price-data-1m-instances`](https://www.kaggle.com/datasets/toocool69/synthetic-stock-price-data-1m-instances) | `blocked_synthetic_price_data_not_source_labels` | Synthetic 1m-instance price data cannot satisfy source-owned market-regime labels, other-market validation, or source provenance. |

## Search Readback

- Kaggle `intraday market regime`, `intraday regime label`, and `5m market regime` searches surfaced raw daily/crypto/provider panels or synthetic price data, not source-owned regime labels.
- Hugging Face targeted searches only returned the BTCUSD HMM-6 candidate for sub-hour market-regime wording; that remains proxy/generated evidence.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1.json`
- Candidate CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/native-subhour-external-source-screen/native_subhour_external_source_screen_v1_candidates.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T192750-codex-native-subhour-external-source-screen-v1/checks/native_subhour_external_source_screen_v1_assertions.out`
