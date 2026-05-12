# R3 Native Sub-hour Live Source Recheck v3

Run id: `20260512T044947-codex-r3-native-subhour-live-source-recheck-v3`

Decision: `r3_native_subhour_live_source_recheck_v3=no_ready_source_owned_native_subhour_rows_no_promotion`

## Scope

- Target blocker: R3 native sub-hour source-label rows.
- Required intake root: `/tmp/ict-engine-native-subhour-source-label-intake`.
- Required files:
  - `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
  - `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`
- Focus cells preserved from the prior request package: `AAPL 15m`, `AAPL 30m`, `^IXIC 15m`, and `^IXIC 30m`, after `2026-01-30`.

## Readback

- Prior R3 packets read before this recheck: `192750`, `194400`, `201713`, `010401`, and `012139`.
- The required R3 intake root was absent during the pre-write readback.
- Kaggle CLI exact searches for `AAPL 15m regime label` and `IXIC 15m regime label` returned no datasets.
- Kaggle CLI broad search for `intraday market regime labels` returned `thisathdamiru/bybit-multi-crypto-historical-data-2020-2026`, which is a raw Bybit historical data panel, not source-owned `MainRegimeV2` labels for AAPL or IXIC.
- Hugging Face API searches for `AAPL 15m regime label`, `IXIC 15m regime label`, and `intraday market regime labels` returned HTTP `200` but no dataset rows.
- The previously known Hugging Face `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` first-row schema exposes 5m/15m OHLCV and related generated HMM-style fields for BTCUSD, so it remains proxy/model-derived evidence rather than source-owned AAPL/IXIC native sub-hour labels.

## Gate

- Ready source-owned native sub-hour exports found: `0`.
- Accepted rows added: `0`.
- Source/control evidence acquired: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Boundary

This packet records a fresh public/API/source-gate readback only. It does not download raw rows, create or mutate the R3 intake root, copy local OHLCV/proxy files, approve generated HMM labels, run canonical merge, rerun calibration, or rerun downstream promotion.
