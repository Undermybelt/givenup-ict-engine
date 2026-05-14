# Public Source Candidate Prior History Correction v1

Run id: `20260512T015909-codex-public-source-candidate-prior-history-correction-v1`
Gate result: `public_source_candidate_prior_history_correction_v1=known_candidates_do_not_redownload_no_acceptance`
Board hash before artifact: `968acaf8c749ed01a0fb14330562408afe12757b173452862ffdf0f9b7af39a8`

Correction:
- The `015639` public-source candidate readback refreshed current Hugging Face API metadata, but the board already had older evidence for both candidates.
- Existing board history marks `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` as `proxy_only` because its labels are HMM-generated BTC 5m/15m regimes, not independent source-backed MainRegimeV2 roots.
- Existing board history marks `sujinwo/tsie-market-regime-dataset` as `sidecar_only`; it was already downloaded to `/private/tmp/ict-regime-hf-tsie`, had `7,193,996` train rows and 7 rule-based IDX signal classes, and still lacked a source-owner approved MainRegimeV2 crosswalk.

Decision:
- Treat the `015639` packet as current API freshness only, not as a new intake instruction.
- Do not redownload `sujinwo/tsie-market-regime-dataset` unless a new source-owner approved MainRegimeV2 crosswalk or acceptance contract is opened.
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
- Raw dataset files downloaded by this correction: `false`.
- External vendor/contact request sent: `false`.
- Trade usable: `false`.

Next:
- Preserve the Current Cursor next action for R6. Search only for genuinely new source-owned MainRegimeV2/cross-timeframe labels, or proceed through owner/operator R6 export/explicit `FLIP` approval before canonical merge and downstream rerun.
