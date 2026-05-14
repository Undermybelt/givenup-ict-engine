# Public Source Candidate Sweep After 062842 v1

Run id: `20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1`

Gate result: `public_source_candidate_sweep_after_062842_v1=no_candidate_selected_no_required_root_no_downstream`

Board sha256 before artifact: `1d6e0879fa2b8d20ad173b23c10cdca98a587e2f37bacb94254e675e83868278`

## Scope

Read-only acquisition sweep after the unregistered `062842` unlock refresh. This checks public Kaggle/HuggingFace/GitHub candidates and local artifact presence. It does not mutate required roots, send vendor mail, approve controls, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Required Roots

| Root ID | Root | Exists | All Required Present | Missing Files |
|---|---|---:|---:|---|
| `r6_owner_export` | `/tmp/ict-engine-board-a-r6-owner-export-v1` | `False` | `False` | `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json` |
| `r3_native_subhour` | `/tmp/ict-engine-native-subhour-source-label-intake` | `True` | `True` | `` |
| `r5_recency_extension` | `/tmp/ict-engine-source-panel-recency-extension` | `False` | `False` | `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json` |

## Local Artifact Readback

| Artifact | Exists | File Count | Expected Report | Role |
|---|---:|---:|---:|---|
| `062842_source_control_unlock_refresh` | `True` | `7` | `True` | unregistered read-only unlock refresh |
| `062854_readonly_runtime_refresh` | `True` | `20` | `False` | unregistered read-only runtime outputs |
| `062902_r3_hf_tsie_native_intraday_intake` | `True` | `6` | `False` | empty/incomplete root observed, not evidence |

## Candidate Decisions

| Candidate | Surface | Source | Observed Rows | Date Span | Decision | Unlock | Reason |
|---|---|---|---:|---|---|---:|---|
| `kaggle_macro_stress_liquidity` | `kaggle` | `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes` | `4150` | Date:2014-10-17..2026-02-25 | `rejected_feature_panel_no_mainregimev2_labels` | `False` | Daily cross-asset feature/stress panel reaches 2026-02-25 but has no discrete Bull/Bear/Sideways/Crisis source labels and no native sub-hour rows. |
| `kaggle_stock_market_regimes_20002026` | `kaggle` | `mafaqbhatti/stock-market-regimes-20002026` | `245021` | date:2000-01-03..2026-01-30 | `rejected_known_daily_no_post_cutoff_rows` | `False` | Known 39-ticker daily MainRegimeV2-like panel still ends at 2026-01-30, so it does not unlock the R5 post-cutoff recency root. |
| `kaggle_nifty500_behavior_regime` | `kaggle` | `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | `10810` | Date:2010-09-20..2026-03-20; Date:2012-02-02..2026-03-20; Date:2012-02-02..2026-03-20; run_date:2012-02-02..2026-03-20; feature_date:2012-02-02..2026-03-20 | `rejected_behavior_hmm_not_mainregimev2_not_existing_panel` | `False` | Daily NIFTY behavior/macro states reach 2026-03-20 but labels are Durable/Fragile/Calm/Stress/Trending/Noisy style states, not the existing R5 panel or accepted MainRegimeV2 source labels. |
| `hf_clarus_coherence_mapping` | `huggingface` | `ClarusC64/market-regime-coherence-mapping-v0.1` | `7` | date_window:2025-09-01_to_2025-09-04..2025-09-01_to_2025-09-04; date_window:2025-01-10_to_2025-01-14..2025-06-10_to_2025-06-13 | `rejected_tiny_benchmark_no_market_matrix` | `False` | Tiny 6-train/1-test relationship benchmark with 2025 windows and no instrument/timeframe matrix; not R3 native sub-hour or R5 recency evidence. |
| `hf_clarus_transition_breakpoint` | `huggingface` | `ClarusC64/market-regime-transition-breakpoint-mapping-v0.1` | `7` | date_window:2025-09-01_to_2025-09-03..2025-09-01_to_2025-09-03; date_window:2025-01-15_to_2025-01-18..2025-06-11_to_2025-06-13 | `rejected_tiny_transition_benchmark_no_mainregimev2` | `False` | Tiny transition benchmark with narrative basins/targets, not source-owned Bull/Bear/Sideways/Crisis rows and not native sub-hour. |
| `hf_tsie_idx` | `huggingface` | `sujinwo/tsie-market-regime-dataset` | `0` | n/a | `rejected_known_sidecar_no_crisis_single_idx_rule_labels` | `False` | Full TSIE parquet is already counted as non-promoting: rule/OHLCV IDX labels, no direct Crisis semantic, no accepted MainRegimeV2 equivalence. |
| `hf_btc_hmm6` | `huggingface` | `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | `315311` | timestamp:2025-05-25 13:10:00+00:00..2025-11-05 18:30:00+00:00; timestamp:2022-11-06 21:20:00+00:00..2024-12-12 07:40:00+00:00; timestamp:2024-12-12 07:45:00+00:00..2025-05-25 13:05:00+00:00 | `rejected_hmm_proxy_single_crypto_no_mainregimev2` | `False` | 5m/15m BTC HMM labels are proxy model states, not source-owned MainRegimeV2 labels across required markets. |
| `hf_nifty50_binary` | `huggingface` | `AAdevloper/nifty50-market-regime` | `0` | n/a | `rejected_binary_risk_on_off_small_single_market` | `False` | Binary risk-on/off NIFTY50 labels cannot cover Bull/Bear/Sideways/Crisis roots or the required R3/R5 target roots. |
| `github_repo_search` | `github` | `gh search repos market-regime/source-label queries` | `0` | n/a | `rejected_no_repo_candidate_returned` | `False` | Authenticated gh repo searches returned no candidate repositories for MainRegimeV2 R3/R5/R6 unlock contracts in this slice. |

## Decision

No public candidate is selected for target-root materialization. The Kaggle `stock-market-regimes-20002026` file still ends on `2026-01-30`, the newer Kaggle/NIFTY/HF candidates are feature, behavior, benchmark, proxy-HMM, or rule/OHLCV sidecars rather than accepted source-owned `MainRegimeV2` rows, and GitHub repo search returned no unlock candidate in this slice.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Use the approved operator/vendor route for R6 owner-export rows or explicit source/control approval, or acquire true R5 post-cutoff source-panel rows or R3 native-subhour `MainRegimeV2` labels before rerunning direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/public-source-candidate-sweep-after-062842-v1/public_source_candidate_sweep_after_062842_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/public-source-candidate-sweep-after-062842-v1/public_source_candidate_sweep_candidates_v1.csv`
- Required roots CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/public-source-candidate-sweep-after-062842-v1/public_source_candidate_sweep_required_roots_v1.csv`
- Local artifacts CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/public-source-candidate-sweep-after-062842-v1/public_source_candidate_sweep_local_artifacts_v1.csv`
- HF search CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/public-source-candidate-sweep-after-062842-v1/hf_search_results_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T063217+0800-codex-public-source-candidate-sweep-after-062842-v1/checks/public_source_candidate_sweep_after_062842_v1_assertions.out`
