# R5/R3 Public Source Targeted Search After 065134 v1

Run id: `20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1`

Gate result: `r5_r3_public_source_targeted_search_after_065134_v1=post_cutoff_candidates_found_no_mainregimev2_unlock_no_downstream`

## Scope

Bounded live source search after `065134` kept R5 blocked. This packet searched Kaggle and Hugging Face for post-`2026-01-30` regime-label recency candidates and Crisis-capable `MainRegimeV2` source exports, then directly downloaded the two most plausible small Kaggle candidates for CSV profiling. It does not mutate R3/R5/R6 target roots, approve proxy labels, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Search Commands

- `kaggle datasets list -s "market regime 2026" --csv`
- `kaggle datasets list -s "stock market regimes" --csv`
- `kaggle datasets list -s "financial crisis dataset" --csv`
- `curl https://huggingface.co/api/datasets?search=market%20regime&limit=20`
- `curl https://huggingface.co/api/datasets?search=financial%20crisis&limit=20`

All search commands exited `0`.

## Downloaded Candidate Readback

| Candidate | Rows | Date Max | Post-2026-01-30 Rows | Label Readback | Decision |
|---|---:|---|---:|---|---|
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` / `behavior_regime_predictions.csv` | `3846` | `2026-03-20` | `35` | `Trending`, `Mean-Reverting`, `Noisy` behavior states | Post-cutoff rows exist, but not `MainRegimeV2` Bull/Bear/Sideways/Crisis and not R3 native-subhour. |
| `ahaanverma00/nifty-500-market-and-behavior-regime-dataset` / `regime_timeline_history.csv` | `3464` | `2026-03-20` | `34` | `Durable`, `Fragile`, `Calm`, `Choppy`, `Stress` states | Source regime context only; no accepted root taxonomy and no direct Crisis mapping. |
| `kanchana1990/algorithmic-trading-macro-stress-and-asset-regimes` / `Global_Market_Stress_and_Liquidity_Regimes.csv` | `4150` | `2026-02-25` | `26` | `Financial_Stress_Index` numeric column only | Stress context only; no source-owned Bull/Bear/Sideways/Crisis labels. |

## Decision

The search found real post-cutoff daily regime/context candidates, but none unlocks Board A under the current contract:

- no source-owned post-`2026-01-30` `MainRegimeV2` root rows suitable for `/tmp/ict-engine-source-panel-recency-extension`;
- no verifier-native R3 native-subhour labels;
- no R6 owner/export controls;
- no accepted `Crisis` root packet;
- no canonical merge or downstream promotion rerun.

Promotion remains blocked: accepted rows added `0`, valid required-root unlock false, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- Kaggle/HuggingFace search outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1/command-output/`
- Candidate profile JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1/command-output/candidate_csv_profile.json`
- Candidate profile summary CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1/r5-r3-public-source-targeted-search-after-065134-v1/candidate_profile_summary_v1.csv`
- JSON summary: `docs/experiments/actionable-regime-confidence/runs/20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1/r5-r3-public-source-targeted-search-after-065134-v1/r5_r3_public_source_targeted_search_after_065134_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T065449+0800-codex-r5-r3-public-source-targeted-search-after-065134-v1/checks/r5_r3_public_source_targeted_search_after_065134_v1_assertions.out`

## Next

Continue from a stricter source search: source-owned post-`2026-01-30` rows with accepted Bull/Bear/Sideways/Crisis-style roots, verifier-native Crisis-capable R3 `MainRegimeV2` labels, R6 owner/export controls, explicit source/control approval, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
