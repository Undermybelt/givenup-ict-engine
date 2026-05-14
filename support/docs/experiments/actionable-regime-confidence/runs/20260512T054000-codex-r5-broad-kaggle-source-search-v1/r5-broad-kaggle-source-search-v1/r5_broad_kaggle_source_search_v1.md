# R5 Broad Kaggle Source Search v1

Run id: `20260512T054000-codex-r5-broad-kaggle-source-search-v1`

Gate result: `r5_broad_kaggle_source_search_v1=current_nifty_candidate_found_not_schema_compatible_no_promotion`

## Scope

Read-only broad Kaggle source search for the R5 recency/source-panel blocker after the exact `mafaqbhatti/stock-market-regimes-20002026` screen found no post-cutoff target rows. This run writes command outputs under this run root and downloads candidate files to `/tmp`; it does not copy rows into `/tmp/ict-engine-source-panel-recency-extension`, mutate target roots, generate accepted labels, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Search Commands

All four Kaggle search commands exited `0`:
- `stock market regime`
- `market regime labels`
- `financial market regimes`
- `regime classification stock`

The broad search surfaced one current regime-like candidate not covered by the exact previous screen:
- `ahaanverma00/nifty-500-market-and-behavior-regime-dataset`, last updated `2026-04-15 15:25:28.867000`

## Candidate Inspection

Downloaded to `/tmp/ict-engine-kaggle-nifty500-behavior-regime-20260512T054000`.

Files:
- `behavior_regime_predictions.csv`, SHA-256 `a3d89910596bd8f953218e5bfe3d57eab4f5c9c76f9b0ef1d38c9c9dca079c77`, rows `3846`, date range `2010-09-20` to `2026-03-20`, post-cutoff rows after `2026-01-30`: `35`
- `regime_timeline_history.csv`, SHA-256 `4bfb78601e36557e177701bf8ee6a0c9b8e243206e0f9eafe8ee6c7115f0b732`, rows `3464`, date range `2012-02-02` to `2026-03-20`, post-cutoff rows after `2026-01-30`: `34`
- `final_features_matrix.csv`, SHA-256 `f7e44a4f73505b2e733f33262262e9756bb974f717afdbfbfaa29a83cfeecc28`, rows `3500`, date range `2012-02-02` to `2026-03-20`

Observed regime-like fields:
- `behavior_fast_state`, `behavior_slow_state`: `Trending`, `Mean-Reverting`, `Noisy`
- `macro_state`, `fast_state`, `combined_state`, `adaptive_*_state`: examples include `Durable-Calm`, `Fragile-Choppy`, `Fragile-Stress`
- probability columns: `p_fragile_*`, `p_calm_*`, `p_choppy_*`, `p_stress_*`

## Decision

This is useful source-discovery context but not an R5 unlock.

Reasons:
- It is NIFTY/market-behavior oriented, not a source-owned `MainRegimeV2` stock-panel extension with `Bull`, `Bear`, `Sideways`, and `Crisis` labels.
- It has current post-cutoff rows, but no direct Board A target rows and no target provenance manifest.
- Mapping `Fragile/Calm/Choppy/Stress` or `Trending/Mean-Reverting/Noisy` into `MainRegimeV2` would be a derived ontology transform, not a source-owned root-label export.
- `/tmp/ict-engine-source-panel-recency-extension` was not mutated.

Promotion status remains unchanged: accepted rows added `0`, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Keep R5 blocked unless a source-owned, schema-compatible `MainRegimeV2` extension with provenance arrives. Continue with R6 owner export / explicit approval, R3 native sub-hour source labels, or another source-owned cross-timeframe `MainRegimeV2` export before rerunning the downstream chain.
