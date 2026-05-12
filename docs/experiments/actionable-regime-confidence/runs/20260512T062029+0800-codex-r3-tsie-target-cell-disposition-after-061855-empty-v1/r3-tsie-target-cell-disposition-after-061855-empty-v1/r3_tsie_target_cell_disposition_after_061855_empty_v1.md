# R3 TSIE Target Cell Disposition After 061855 Empty v1

Run id: `20260512T062029+0800-codex-r3-tsie-target-cell-disposition-after-061855-empty-v1`

Gate result: `r3_tsie_target_cell_disposition_after_061855_empty_v1=tsie_large_support_not_exact_r3_native_subhour_target_no_promotion`

## Scope

Bounded readback after the empty `061855` R3/HF/TSIE root. This does not mutate the empty root, does not copy files into `/tmp/ict-engine-native-subhour-source-label-intake`, does not create labels, does not run canonical merge or downstream promotion, does not make a trade claim, and does not call `update_goal`.

## Evidence Readback

- Prior TSIE dry run: `docs/experiments/actionable-regime-confidence/runs/20260512T022005-codex-tsie-source-label-intake-dryrun-v1`
- Dataset: `sujinwo/tsie-market-regime-dataset`
- License: `mit`
- Rows read from the existing local parquet: `7193996`
- Unique group ids: `1150`
- Time span: `1990-06-07 02:00:00` through `2026-04-07 02:00:00`
- Minute values: `[0]`
- Target-like rows for `AAPL|IXIC|NASDAQ|COMP`: `0`
- Target-like groups: `[]`
- Sample groups: `IDX_DLY_AALI_60`, `IDX_DLY_ACES_60`, `IDX_DLY_ADES_60`, `IDX_DLY_ADHI_240`, `IDX_DLY_ADHI_60`

## R3 Target Cells

| Symbol | Required Timeframe | Required After | TSIE Exact Rows | Decision |
|---|---:|---:|---:|---|
| `AAPL` | `15m` | `2026-01-30` | `0` | `missing_exact_target_cell` |
| `AAPL` | `30m` | `2026-01-30` | `0` | `missing_exact_target_cell` |
| `^IXIC` | `15m` | `2026-01-30` | `0` | `missing_exact_target_cell` |
| `^IXIC` | `30m` | `2026-01-30` | `0` | `missing_exact_target_cell` |

## Decision

TSIE remains useful as a large public regime-label candidate, but it does not unlock R3. It has no exact AAPL/IXIC target rows, no 15m/30m target-cell rows for the active R3 request, and no source-owned `MainRegimeV2` native sub-hour intake package. Required root `/tmp/ict-engine-native-subhour-source-label-intake` remains absent.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired `false`, target root mutated `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Use the existing R3 native sub-hour request package/contact routes, or supply source-owned AAPL/IXIC 15m/30m labels plus provenance in the required intake root. Only after a required root unlocks should direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback rerun in order.
