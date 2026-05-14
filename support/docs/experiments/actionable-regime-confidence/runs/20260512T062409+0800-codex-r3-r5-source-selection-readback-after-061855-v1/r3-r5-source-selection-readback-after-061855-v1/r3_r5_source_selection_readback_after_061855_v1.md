# R3/R5 Source Selection Readback After 061855 v1

Run id: `20260512T062409+0800-codex-r3-r5-source-selection-readback-after-061855-v1`

Gate result: `r3_r5_source_selection_readback_after_061855_v1=no_candidate_selected_no_required_root_no_promotion`

Board sha256 before artifact: `b286771cfbc8c5ffbae3e3d2b0d4974267f6810b9607ef8669fd322a73a18dde`

## Scope

This readback decides whether the newly resurfaced TSIE branch or nearby public R3/R5 candidates should be selected for target-root materialization. It does not copy files into `/tmp/ict-engine-native-subhour-source-label-intake`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-board-a-r6-owner-export-v1`; it does not run canonical merge or downstream promotion.

## Required Roots

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `false`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `false`
- `/tmp/ict-engine-source-panel-recency-extension`: `false`

## TSIE Readback

- Existing full parquet present: `true`
- Parquet SHA-256: `8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158`
- Rows read in prior dry run: `7193996`
- Time span: `1990-06-07T02:00:00` to `2026-04-07T02:00:00`
- Mapped counts: `{'ABSTAIN_TRAP': 2161093, 'Bear': 1435764, 'Bull': 1435055, 'Sideways': 2162084}`
- Selection decision: `false`; no `Crisis` semantic, single IDX context, rule/OHLCV-derived labels, and prior full-parquet Board A gates accepted `0` roots.

## Candidate Decisions

| Candidate | Source | Decision | Unlock | Reason |
|---|---|---|---:|---|
| `tsie_idx` | `sujinwo/tsie-market-regime-dataset` | `rejected_known_sidecar_no_crisis_single_idx_rule_labels` | `false` | TSIE has full parquet support and native subhour timestamps but no Crisis semantic, single IDX market context, rule/OHLCV-derived labels, and prior full-parquet Board A gates accepted 0 roots. |
| `btc_hmm6` | `akashkumar5/Multi_Timeframe_Market_Regimes_HMM6_BTCUSD` | `rejected_hmm_proxy_single_crypto_no_mainregimev2` | `false` | Multi-timeframe BTC rows are HMM-inferred labels, not source-owned MainRegimeV2 labels, and do not cover equity/index cross-market roots or Crisis/Sideways/Bull/Bear as accepted source labels. |
| `nifty50_binary` | `AAdevloper/nifty50-market-regime` | `rejected_binary_risk_on_off_small_single_market` | `false` | Binary RISK_ON/RISK_OFF NIFTY50 labels cannot cover Bull/Bear/Sideways/Crisis roots and are a small single-market technical-indicator label panel. |
| `nifty500_behavior` | `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` | `rejected_daily_hmm_labels_not_r5_existing_panel` | `false` | Known daily NIFTY behavior labels reach 2026-03-20 but are HMM/behavior labels such as Calm/Stress, not the existing 39-ticker R5 panel recency extension or accepted MainRegimeV2 source labels. |
| `us_market_regimes` | `nickdatak/us-market-regimes-dataset-1995-2024` | `rejected_stale_weekly_unsupervised` | `false` | Known US market-regimes files are weekly HMM/GMM/feature tables stale to 2023/2024, not post-cutoff MainRegimeV2 rows or native subhour source labels. |
| `stock_market_regimes` | `mafaqbhatti/stock-market-regimes-20002026` | `rejected_known_daily_no_post_cutoff_rows` | `false` | Known source panel remains daily and already counted; latest local/live checks show no rows after 2026-01-30 for the R5 recency tail. |

## Decision

No R3 or R5 candidate is selected for target-root materialization in this slice. The TSIE branch is closed as non-promoting despite full parquet availability; the nearby HMM/NIFTY/US/Kaggle candidates are proxy, stale, daily-only, or not MainRegimeV2-equivalent.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 recency rows for the existing source panel, source-owned R3 native sub-hour labels with accepted MainRegimeV2 equivalence, or a genuinely new cross-timeframe MainRegimeV2 export. Do not rerun provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion until a required target root unlocks.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T062409+0800-codex-r3-r5-source-selection-readback-after-061855-v1/r3-r5-source-selection-readback-after-061855-v1/r3_r5_source_selection_readback_after_061855_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T062409+0800-codex-r3-r5-source-selection-readback-after-061855-v1/r3-r5-source-selection-readback-after-061855-v1/r3_r5_source_selection_candidates_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T062409+0800-codex-r3-r5-source-selection-readback-after-061855-v1/checks/r3_r5_source_selection_readback_after_061855_v1_assertions.out`
