# Public Source Candidate Readback v1

Run id: `20260512T015639-codex-public-source-candidate-readback-v1`
Gate result: `public_source_candidate_readback_v1=candidates_found_no_acceptance_no_intake_mutation`
Board hash before artifact: `e9d69fcc5dd1e91c94d4ef6450df549d36897d54801645b8b5a11d3fdef0d5a1`

Purpose:
- Continue the non-R6 source-label branch while R6 remains externally gated by owner/operator export.
- Screen public source-label datasets that could address Bull/Sideways cross-timeframe evidence or Bear/Crisis support without using generated proxy labels.

External readback:
- Hugging Face dataset API and first-row APIs were queried for two public datasets.
- No dataset file was downloaded into the repo.
- No intake root was mutated.
- No raw data was committed.

Candidate 1: `sujinwo/tsie-market-regime-dataset`
- URL: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset`
- API URL: `https://huggingface.co/api/datasets/sujinwo/tsie-market-regime-dataset`
- License tag: `mit`.
- Format: Parquet; sibling file `tft_dataset_labeled.parquet`.
- Dataset card says this is an Indonesian stock market (IDX) multi-class market-regime dataset with 7 classes: strong sell, weak sell, bear trap, flat/noise, bull trap, weak buy, strong buy.
- First-row API showed hourly/session-aware rows such as `group_id=IDX_DLY_AALI_60`, timestamp `2013-01-07T02:00:00`, OHLCV fields, session/time features, and `regime_label`.
- Candidate status: current API still shows a potentially useful schema, but prior board history already screened this dataset and kept it sidecar/proxy-only.
- Fail-closed blockers: earlier board entries record that this dataset was already downloaded to `/private/tmp/ict-regime-hf-tsie`, that it had `7,193,996` train rows and 7 rule-based IDX signal classes, and that it still lacked a source-owner approved MainRegimeV2 crosswalk. Do not repeat the download unless a new mapping/approval contract is opened.

Candidate 2: `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`
- URL: `https://huggingface.co/datasets/akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`
- API URL: `https://huggingface.co/api/datasets/akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD`
- License tag: `cc-by-4.0`.
- Format: CSV and Parquet train/validation/test splits.
- Dataset card says it contains BTCUSD/BTCUSDT 5m and 15m OHLCV/indicator rows with 6 HMM-derived regime labels: Choppy High-Vol, Range, Squeeze, Strong Trend, Volatility Spike, Weak Trend.
- First-row API showed 5m and 15m fields plus `state` and human-readable `regime`.
- Candidate status: current API still shows a crypto 5m/15m multi-timeframe schema, but prior board history already rejected this dataset as proxy-only.
- Fail-closed blockers: labels are HMM-derived and post-hoc/model-dependent, Strong/Weak Trend has no source-owned direction sign for Bull/Bear mapping, it is single-asset crypto only, and no source-owned MainRegimeV2 mapping/calibration/canonical merge exists.

Decision:
- Ready source-owned cross-timeframe MainRegimeV2 exports found: `0`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

No mutation claims:
- Runtime code changed: `false`.
- Shared intake mutated: `false`.
- R3/R5/R6 roots mutated: `false`.
- Thresholds relaxed: `false`.
- Raw data committed: `false`.
- Raw dataset files downloaded: `false`.
- External vendor/contact request sent: `false`.
- Trade usable: `false`.

Prior-history correction:
- Do not use this readback as a new instruction to redownload `sujinwo/tsie-market-regime-dataset`. It is a current API refresh only.
- Relevant prior board lines mark `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` as `proxy_only`, `sujinwo/tsie-market-regime-dataset` as `sidecar_only`, and `sujinwo` as previously downloaded to `/private/tmp/ict-regime-hf-tsie` with no accepted root.

Next:
- Preserve the Current Cursor next action for R6. For non-R6 source acquisition, search for genuinely new source-owned MainRegimeV2/cross-timeframe labels or reopen `sujinwo` only if a new source-owner approved crosswalk is available; do not repeat the existing `/private/tmp` download path.
