# R3/R5 Public Source Live Search Rerun v2

Run id: `20260512T055829+0800-codex-r3-r5-public-source-live-search-rerun-v2`

Gate result: `r3_r5_public_source_live_search_rerun_v2=no_exact_r3_r5_rows_no_promotion`

Board hash before artifact: `b2f483d59d80b9129b0c70204ba6fde219d1f6ab8349ac0caeb6026a20194bd9`

## Scope

Durable restoration of the `055829` metadata/file-listing source search artifacts. This run checks Kaggle and Hugging Face metadata plus selected Kaggle file listings. It does not download row data, create labels, mutate target intake roots, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Readback

- Kaggle rows scanned: `2` across `7` queries.
- Hugging Face rows scanned: `0` across `7` queries.
- Kaggle file-list rows scanned: `33` across `3` candidate refs.
- R3 metadata/file hits: `0`.
- R5 metadata/file hits: `0`.
- Compatible source rows acquired: `false`.

## Required Roots

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: before `False`, after `False`
- `/tmp/ict-engine-native-subhour-source-label-intake`: before `False`, after `False`
- `/tmp/ict-engine-source-panel-recency-extension`: before `False`, after `False`

## Decision

No source-owned AAPL/IXIC/NQ native 15m/30m regime-label rows and no source-owned post-cutoff `MainRegimeV2` rows were acquired. The run is countable only as source-search evidence and remains non-promoting.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Continue only after explicit source/control approval, verifier-native R6 owner/export rows with valid controls, source-owned R5 recency rows, or source-owned R3 native sub-hour labels unlock a required target root. Then rerun direct verifier, split calibration, canonical merge, providers, Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
