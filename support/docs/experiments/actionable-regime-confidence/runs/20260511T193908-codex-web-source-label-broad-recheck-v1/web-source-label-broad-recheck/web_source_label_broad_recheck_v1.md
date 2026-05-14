# Web Source Label Broad Recheck v1

Run ID: `20260511T193908+0800-codex-web-source-label-broad-recheck-v1`

This is a narrow live-web recheck for the remaining other-market/source-label equivalence blocker. It does not download raw rows, edit Current Cursor, relax thresholds, or promote proxy/generated labels.

## Decision

`web_source_label_broad_recheck_v1=no_new_promotable_source_label_equivalence`

- Web queries screened: `4`.
- New promotable source-owned `MainRegimeV2` or owner-approved equivalence sources found: `0`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Full other-market/source-label equivalence: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Queries

- `site:kaggle.com/datasets "market regime" "label" "2026" Bull Bear Sideways`
- `site:huggingface.co/datasets "market regime" "regime_label" finance`
- `"market regime" "bull" "bear" "sideways" dataset`
- `"regime_label" stock bull bear sideways dataset`

## Result Disposition

| Source | Candidate | Decision | Reason |
|---|---|---|---|
| Kaggle | [`mafaqbhatti/stock-market-regimes-20002026`](https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026) | `known_source_no_new_strict_or_transfer_closure` | Already screened and live-recency-checked; still no XOM/Sideways tail repair rows and no new strict `1h` source-owned sessions beyond already-counted support. |
| Hugging Face | [`sujinwo/tsie-market-regime-dataset`](https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset) | `known_rule_or_generated_label_surface_no_mainregimev2_crosswalk` | Already screened; has `regime_label`-style fields but no source-owner approved `MainRegimeV2` crosswalk and remains proxy/rule-generated evidence. |
| Web | general web results | `method_or_article_not_row_level_source_labels` | Method pages, model descriptions, and papers about regimes are not row-level source-owned labels with provenance and `MainRegimeV2` equivalence. |

## Why It Still Blocks

The live web recheck did not produce a new row-level external source that can satisfy the active Board A acceptance contract. The known Kaggle stock-regime source remains useful but cannot add the missing strict `1h` sessions. The known Hugging Face IDX/TSIE surface remains useful as a request target only because the labels are not owner-approved `MainRegimeV2` equivalents.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T193908-codex-web-source-label-broad-recheck-v1/web-source-label-broad-recheck/web_source_label_broad_recheck_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T193908-codex-web-source-label-broad-recheck-v1/web-source-label-broad-recheck/web_source_label_broad_recheck_v1_candidates.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T193908-codex-web-source-label-broad-recheck-v1/checks/web_source_label_broad_recheck_v1_assertions.out`
