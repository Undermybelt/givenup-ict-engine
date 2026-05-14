# R3 HF TSIE Provenance Decision v1

Run id: `20260512T062201+0800-codex-r3-hf-tsie-provenance-decision-v1`

Gate result: `r3_hf_tsie_provenance_decision_v1=rejected_rule_based_proxy_labels_no_intake_no_promotion`

## Scope

This run resolves the provenance question left open by `061855` for `sujinwo/tsie-market-regime-dataset`. It fetches the Hugging Face README, API metadata, dataset-server first rows, and a parquet HEAD probe. It does not download the 591 MB parquet payload, does not create or mutate `/tmp/ict-engine-native-subhour-source-label-intake`, does not run canonical merge, does not rerun downstream promotion, does not make a trade claim, and does not call `update_goal`.

## Evidence

- README fetch exited `0`: `raw/README.md`
- Hugging Face API fetch exited `0`: `raw/api.json`
- Dataset-server first rows fetch exited `0`: `raw/first_rows.json`
- Parquet HEAD probe exited `35` with a TLS error against the Xet bridge; the full parquet was not downloaded.
- Board hash before artifact: `checks/board_hash_before.txt`

## Readback

- The dataset is public and MIT-tagged.
- First rows confirm native sub-hour timestamps and a `regime_label` column.
- The README describes the dataset as including OHLCV, engineered technical indicators, session-aware features, and multi-class regime labels.
- The README labels are explicitly generated from rule-based signal classification using price action, volatility, RSI, and volume logic.
- First-row schema includes generated or target-adjacent fields such as `future_volatility`, `trend_return`, `target_return`, technical indicators, and `regime_label`.
- This confirms the older rejection basis: TSIE is useful research metadata, but it is not an independent source-owned `MainRegimeV2` label export and should not be copied into the required R3 target root.

## Decision

`061855` remains a candidate-screen artifact only. TSIE is rejected for Board A/B promotion because its labels are generated/proxy labels derived from OHLCV and technical logic. It cannot unlock R3 native sub-hour source-label evidence, source/control approval, canonical merge, selected-data AutoQuant training, or downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Continue source/control search from required roots or owner/source-native exports only: verifier-native R6 owner/export rows with controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels. Do not promote generated TSIE labels or materialize them under `/tmp/ict-engine-native-subhour-source-label-intake`.
