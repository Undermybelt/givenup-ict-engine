# HF NIFTY50 Regime Candidate After 070506 v1

Run id: `20260512T070820+0800-codex-hf-nifty50-regime-candidate-after-070506-v1`

Gate result: `hf_nifty50_regime_candidate_after_070506_v1=binary_risk_on_off_no_r3_r5_r6_unlock_no_downstream`

## Scope

Bounded read-only profile of `AAdevloper/nifty50-market-regime`, a newly surfaced Hugging Face public dataset candidate after the `070506` GitHub code-source probe. This packet downloads the small CSV to `/tmp` for profiling only. It does not copy rows into `/tmp/ict-engine-source-panel-recency-extension`, mutate R3/R5/R6 target roots, approve proxy labels, run direct verifier, run split calibration, run canonical merge, run provider/AutoQuant promotion, run filter/Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree readback, make a trade claim, or call `update_goal`.

## Source Readback

- Dataset: `AAdevloper/nifty50-market-regime`
- Hugging Face dataset SHA: `51f6a4fb6b500627f5a7779d8e78d9d1fc567a10`
- License tag: `mit`
- File profiled: `market_regime_data_nifty50.csv`
- Local temporary SHA-256: `3cdea0310911bbfba4217b8a0c9ab24d38fcd69fb7ebbcd24fdf09aa7c49ac4f`
- Rows: `2,235`
- Columns: `Date`, `india_vix`, `rsi_14`, `ma_50`, `ma_200`, `regime`
- Date range: `2015-10-23` to `2024-11-14`
- Rows after `2026-01-30`: `0`
- Label column: `regime`
- Label counts: `0=1216`, `1=1019`
- README labels: `RISK_OFF (0)` and `RISK_ON (1)`

## Decision

This candidate does not unlock Board A:

- It is binary `RISK_ON/RISK_OFF`, not source-owned `MainRegimeV2` `Bull/Bear/Sideways/Crisis`.
- It has `0` rows after `2026-01-30`, so it cannot satisfy R5 recency.
- It is daily NIFTY50 context, not verifier-native R3 native-subhour labels.
- It has no R6 owner/export controls.
- It is feature/label context only, not canonical merge input or downstream promotion evidence.

Accepted rows added `0`; R6 owner/export unlock `false`; R5 recency unlock `false`; R3 native-subhour unlock `false`; valid required-root unlock `false`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Artifacts

- Hugging Face API JSON: `command-output/hf_dataset_api.json`
- Hugging Face README: `command-output/hf_readme.md`
- CSV head/profile/hash: `command-output/hf_market_regime_data_nifty50_head.csv`, `command-output/hf_nifty50_profile.json`, `command-output/hf_market_regime_data_nifty50.sha256`
- JSON summary: `hf-nifty50-regime-candidate-after-070506-v1/hf_nifty50_regime_candidate_after_070506_v1.json`
- Decision CSV: `hf-nifty50-regime-candidate-after-070506-v1/hf_nifty50_regime_candidate_after_070506_v1.csv`
- Assertions: `checks/hf_nifty50_regime_candidate_after_070506_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
