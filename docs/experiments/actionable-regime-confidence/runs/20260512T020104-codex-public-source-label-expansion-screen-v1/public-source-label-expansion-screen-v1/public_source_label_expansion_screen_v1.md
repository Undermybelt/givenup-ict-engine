# Public Source Label Expansion Screen v1

Run id: `20260512T020104-codex-public-source-label-expansion-screen-v1`
Gate result: `public_source_label_expansion_screen_v1=new_candidates_screened_no_source_owned_mainregime_export_no_promotion`

Purpose:
- Continue non-R6 source acquisition without repeating prior `sujinwo` / BTC HMM screens.
- Search the current Hugging Face public dataset API for new regime-label candidates.
- Keep this packet metadata-only: no raw dataset files are downloaded into the repo and no intake root is mutated.

Search summary:
- Query terms: `market regime, regime_label, bull bear sideways, trading regime`.
- Search result rows observed: `5`.
- New candidate datasets screened after excluding prior Board A candidates: `3`.

Candidate decisions:
- `AAdevloper/nifty50-market-regime`: `sidecar_only_fail_closed_daily_low_support_int_labels`.
  - URL: `https://huggingface.co/datasets/AAdevloper/nifty50-market-regime`
  - Observed label fields: `regime`.
  - Blocker: Has a regime field for NIFTY 50, but observed rows are daily, small support, and integer labels lack a source-owner MainRegimeV2/Bull-Bear-Sideways crosswalk.
- `ClarusC64/market-regime-coherence-mapping-v0.1`: `reject_fail_closed_text_mapping_not_verifier_native_market_rows`.
  - URL: `https://huggingface.co/datasets/ClarusC64/market-regime-coherence-mapping-v0.1`
  - Observed label fields: `regime_coherence_score, dominant_driver_label, regime_stability_band`.
  - Blocker: Observed fields are macro/cross-asset narrative mapping rows rather than verifier-native OHLCV/order-lifecycle rows with source-owned MainRegimeV2 labels.
- `ClarusC64/market-regime-transition-breakpoint-mapping-v0.1`: `reject_fail_closed_text_mapping_not_verifier_native_market_rows`.
  - URL: `https://huggingface.co/datasets/ClarusC64/market-regime-transition-breakpoint-mapping-v0.1`
  - Observed label fields: `current_regime_basin, adjacent_regime_targets`.
  - Blocker: Observed fields are macro/cross-asset narrative mapping rows rather than verifier-native OHLCV/order-lifecycle rows with source-owned MainRegimeV2 labels.

Source-root readback:
- `r6_owner_export`: present `false`, file_count `0`, root `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- `r3_native_subhour`: present `false`, file_count `0`, root `/tmp/ict-engine-native-subhour-source-label-intake`.
- `r5_recency_extension`: present `false`, file_count `0`, root `/tmp/ict-engine-source-panel-recency-extension`.
- `source_label_equivalence`: present `true`, file_count `2`, root `/tmp/ict-engine-source-label-equivalence-intake`.

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
- Raw dataset files downloaded: `false`.
- Raw data committed: `false`.
- External vendor/contact request sent: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6. Non-R6 public-source work should continue only with genuinely source-owned MainRegimeV2/cross-timeframe exports or an approved crosswalk; do not repeat prior sidecar/proxy dataset downloads.
