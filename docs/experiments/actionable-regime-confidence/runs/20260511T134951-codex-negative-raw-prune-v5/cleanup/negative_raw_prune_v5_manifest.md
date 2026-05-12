# Negative Raw Prune Manifest v5

Run ID: `20260511T134951+0800-codex-negative-raw-prune-v5`

## Scope

- Purpose: act on the disk-footprint warning by pruning old negative, blocked, and context-only raw intermediates before additional source-label loops add more artifacts.
- Preserved: board cursor fields were not edited by this cleanup; selected deletion paths excluded the pre-cleanup active `134237` yfinance intraday attack-map artifacts, the concurrently advanced `134756` daily-to-intraday source attachment artifacts, current `133453` post-axiswise acquisition request artifacts, board-referenced full paths, JSON/Markdown reports, checks/assertions, scripts, and compact evidence packets.
- Removed: exact-path-unreferenced repo-local raw feature matrices, state-copy replay logs, duplicated provider-agreement feature tables, provider download CSVs, and a stale Auto-Quant artifact index from old negative/blocked/context-only loops.
- Runtime code changed: false.
- Thresholds changed: false.
- Board cursor changed: false.

## Safety Checks

- Board cursor read before cleanup: `20260511T134237+0800-codex-yfinance-intraday-source-label-attack-map-v1`.
- Board cursor read after cleanup/writeback: `20260511T134756+0800-codex-daily-to-intraday-source-attachment-v1` from another agent; this cleanup did not overwrite it.
- Exact candidate paths found in the board before deletion: `0`.
- `lsof` result before deletion: no open handles for selected paths.
- Candidate paths: `45`.
- Bytes selected for deletion: `155262784`.

## Removed Repo-Local Raw/Intermediate Artifacts

| Path | Size Before | Bytes Before | SHA-256 Before |
|---|---:|---:|---|
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/state_native_control/QQQ/learning_state.json` | `1.2M` | `1218002` | `8b5139f20ce660ed0e05be5449ca29c00059c0c84f660484b0531b58c04c053d` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/structural-replay-qqq-36/state/QQQ/update_runs.json` | `1.6M` | `1659655` | `3fc65a19b27bbb33b1c86b79a59aa07f100de4d940b592e76c59b942c92e0197` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/structural-replay-qqq-36/state/QQQ/policy_training/structural_path_ranking_target_history.jsonl` | `1.9M` | `2028430` | `8885482127cb0e418e0e9a82209042facb19c23d64f19662e22877bb84eb5b5e` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/branch-chain/qqq-regime-branch-iteration/structural-replay-qqq-36/state/QQQ/analyze_runs.json` | `3.2M` | `3326051` | `97284cf7582d82d0c43397b6b57aa0eb316535a99c6bc02261feb05a45afa340` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/autoquant/autoquant-entry-windows-512-selected-trades.csv` | `4.3M` | `4497690` | `d5847ba3aa49146f9b9a36a7b561016808de4722c617f56d74e55a2b2f32c3a3` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/catboost/autoquant_entry_release_leaksafe_features_512.csv` | `4.1M` | `4325073` | `14b7a96e68bfc042f8351dd481dc42c914bf298f5e0e7711b13f7c69aa036ab0` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/catboost/autoquant_entry_aqonly_features_512.csv` | `4.1M` | `4266990` | `cf4954b4f648688051985eceddd04df33738a96a1b75f03dce6df52d2be1c7c9` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T174651/provider-agreement-v2/qqq_nq_related_provider_agreement_1h/provider_agreement_v2_features.csv` | `8.1M` | `8491840` | `cd011ca441bf160bcd34ee45d1d06802102e6cffc27230336b653d84f0e5e020` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T183017/calibration/provider_agreement_v2_features_512.csv` | `3.9M` | `4045366` | `41985defc812841fd7918e610fc7e71a36ce0cad5dc4197f75af57f5703f3316` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T183454/calibration/nq_forward_payoff_truth_20k.jsonl` | `3.5M` | `3708576` | `8b1a80327751d4b2922f0b881f7112352abf3f0b6ff4b70bd0700d97fe4e8a2d` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T183512/provider-agreement-v2/qqq_nq_related_provider_agreement_1h/provider_agreement_v2_features.csv` | `8.1M` | `8491840` | `cd011ca441bf160bcd34ee45d1d06802102e6cffc27230336b653d84f0e5e020` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T183942-codex-same-market-qqq/provider-agreement-v2/qqq_yf_ibkr_same_market_provider_agreement_1h/provider_agreement_v2_features.csv` | `2.9M` | `3019288` | `0eff1bfba917723d2772ba2c02f092ad34e88ad1a8a63d54475042b08c6facfe` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T184129-codex-qqq-nq-cross/provider-agreement-v2/qqq_yf_ibkr_nq_cache_cross_provider_agreement_1h/provider_agreement_v2_features.csv` | `4.7M` | `4947685` | `d73a770b9affb74ca0a3f4a356fc043335aebf84892c4b1f73fc09e5cc482f87` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T184411-a-v2-2-integrated-review/provider-agreement-v2/qqq_yf_ibkr_same_market_provider_agreement_1h_integrated/provider_agreement_v2_features.csv` | `2.9M` | `3019288` | `0eff1bfba917723d2772ba2c02f092ad34e88ad1a8a63d54475042b08c6facfe` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T184411-a-v2-2-integrated-review/provider-agreement-v2/qqq_yf_ibkr_nq_cache_cross_provider_agreement_1h_integrated/provider_agreement_v2_features.csv` | `4.7M` | `4947685` | `d73a770b9affb74ca0a3f4a356fc043335aebf84892c4b1f73fc09e5cc482f87` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T184538/autoquant/fresh_tomac_scratch_no_rsi_nq_binding_2025.json` | `1.7M` | `1823858` | `894f960edfa3d32ed778806c63c01661c06034aa5c8ff9542d3eb323e8fac99a` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T184555/autoquant/fresh_tomac_scratch_no_rsi_nq_2025.json` | `1.7M` | `1823935` | `a2aeba78f2add0126bba955a19ecbdc6ef5850be3849090269ae9548eb3f152c` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T185034-a7-covariance-eigenstructure/covariance-eigenstructure/covariance_eigenstructure_features.csv` | `2.0M` | `2140379` | `3706f5c369d57c53b897b760ec2344904b0a69aa6b5922e551f75c1cc692ba84` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/analyze_live_20260510T105601_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/analyze_live_20260510T110505_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/policy_training/structural_path_ranking_target_history.csv` | `1.1M` | `1110444` | `2e33762405fcb92c564486bc91d049f8cb75ea86ccd2b0a4b6298990d9abb4eb` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/update_runs.json` | `1.8M` | `1887583` | `292197b115d6afd581a6ff50a7924b57160b795d88e7cee6bce2ce5a71d1c795` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/policy_training/structural_path_ranking_target_history.jsonl` | `2.1M` | `2217602` | `b11f1ffe96c1ee4c39172e3efee79a91a6bf043a1285745356b6169e9fb7d23a` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T191350-codex-nq-structural-replay36/structural-replay-nq-36/state/NQ/analyze_runs.json` | `3.6M` | `3795392` | `72594fd409112c874b35c7ead6139934de54c8ca7ee4f9b89a79205b05878496` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/analyze_live_20260510T105601_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/analyze_live_20260510T110505_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/policy_training/structural_path_ranking_target_history.csv` | `1.1M` | `1106312` | `af7adf8680175db95f058194d443447934c2fd1014e0ccf21783852111df2df7` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/update_runs.json` | `1.8M` | `1887583` | `292197b115d6afd581a6ff50a7924b57160b795d88e7cee6bce2ce5a71d1c795` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/policy_training/structural_path_ranking_target_history.jsonl` | `2.1M` | `2211256` | `f3d93b0dbe12e0c9a1ab21ac936e937c7de6140343a01248a4f5eb715ff643c1` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200154-hermes-loop-full-chain-reaudit/state-copy/NQ/analyze_runs.json` | `3.6M` | `3795392` | `72594fd409112c874b35c7ead6139934de54c8ca7ee4f9b89a79205b05878496` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T200229-hermes-multi-regime-expansion/multi-regime/multi_regime_features_and_labels.csv` | `2.2M` | `2271444` | `08db46438651da0a60872073492918c5c22aa3d03341a62233ba83f78b866780` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T201931-hermes-loop-real-chain/autoquant/02_auto_quant_artifact_index.txt` | `5.8M` | `6107485` | `80f97c8e95b05107ec9320497188828685d6b41d82cdce3dae2ef98e0bf70fa0` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T202359-hermes-cross-market-regime-validation/cross-market/cross_market_regime_features_and_labels.csv` | `4.5M` | `4687611` | `7ce895a304078fcfb29f897b6b46d2aa82fc3b5b622781a804d595914b2cac38` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/analyze_live_20260510T105601_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/analyze_live_20260510T110505_m1.json` | `1.1M` | `1110157` | `92be9db66d475f4116aec46897183d8ba4985e124c64a70b594b24f3331ee436` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/policy_training/structural_path_ranking_target_history.csv` | `1.1M` | `1106312` | `af7adf8680175db95f058194d443447934c2fd1014e0ccf21783852111df2df7` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/update_runs.json` | `1.8M` | `1887583` | `292197b115d6afd581a6ff50a7924b57160b795d88e7cee6bce2ce5a71d1c795` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/policy_training/structural_path_ranking_target_history.jsonl` | `2.1M` | `2211256` | `f3d93b0dbe12e0c9a1ab21ac936e937c7de6140343a01248a4f5eb715ff643c1` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T203010-hermes-per-regime-candidate-search/ict-engine/state-copy/NQ/analyze_runs.json` | `3.6M` | `3795392` | `72594fd409112c874b35c7ead6139934de54c8ca7ee4f9b89a79205b05878496` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T205856-codex-sticky-hazard-per-regime/cross-context/cross_context_sticky_hazard_features.csv` | `15M` | `15373647` | `9768b27a84b9483d70dec4feef29fb0f153305a7a4d85f363cc1dc1644ff4d41` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T212828-codex-legacy-regime-contract-reissue/legacy-reissue/legacy_regime_contract_reissue_features.csv` | `14M` | `15146189` | `d24119c144d12272b6ce091f5493d5b26f94dbcb843d47359ecd8e3fb47f86e2` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T214429-codex-legacy-regime-contract-reissue/legacy-contract/legacy_regime_contract_features.csv` | `5.4M` | `5654928` | `3df3bcbbdd1df7f53e01f14f01751480c60f52c99d17a954757f80847ae137ca` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/provider/ESF_1h_yfinance.csv` | `1.2M` | `1238085` | `aeaa9d77f889127abc04c5884cd9e78d41503ba2abb111ed8efed33f26872450` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/provider/NQF_1h_yfinance.csv` | `1.2M` | `1285986` | `92e42c61904ab03f9c8e84fd1bbb11d25c824649dbd269397001d3797674daa9` |
| `docs/experiments/actionable-regime-confidence/runs/20260510T224014-codex-cross-timeframe-regime-validation/provider/BTC_USD_1h_yfinance.csv` | `1.9M` | `2042729` | `a313f1a88858e1f8cbf6e2495dc3ad57b867f6e9da7990ab3747eb2d97fa36d1` |

## Verification

- Post-delete selected path existence check: `0` selected paths remain.
- `docs/experiments/actionable-regime-confidence/runs` size dropped from `264M` to `116M`.
- Repo-local run file count dropped from `2593` to `2549`.
- Remaining `>1M` files are limited to nine preserved artifacts: three old state/readback files, one FRED sample, one local filesystem label-panel audit JSON, one accepted root-window inventory CSV, the CFTC feature table, the stock-regime same-source rollup CSV, and the persistent-HMM score table.

## Follow-Up Guardrail

Negative, blocked, sub-regime-only, or context-only loops must write replay-sized matrices, provider downloads, and state-copy logs to `/tmp` or `/private/tmp`, then preserve only compact JSON/MD/check/script evidence in the repo. If a heavy artifact is needed as current evidence, it must be named explicitly on the board; otherwise prune it after assertions exist.
