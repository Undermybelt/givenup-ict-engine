# R3 HF TSIE Native Subhour Source Screen v1

Run id: `20260512T061855+0800-codex-r3-hf-tsie-native-subhour-source-screen-v1`

Gate result: `r3_hf_tsie_native_subhour_source_screen_v1=candidate_found_not_intaked_no_acceptance`

## Scope

Bounded public-source screen for an R3 native sub-hour source-label candidate after the required native-subhour root remained absent. This run records compact metadata only. It does not download the raw 591 MB parquet payload, copy files into `/tmp/ict-engine-native-subhour-source-label-intake`, mutate R3/R5/R6 target roots, approve source/control evidence, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Candidate

- Dataset: `sujinwo/tsie-market-regime-dataset`
- Page: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset`
- API source: `https://huggingface.co/api/datasets/sujinwo/tsie-market-regime-dataset`
- Dataset-server size endpoint: `https://datasets-server.huggingface.co/size?dataset=sujinwo/tsie-market-regime-dataset`
- Dataset-server first rows endpoint: `https://datasets-server.huggingface.co/first-rows?dataset=sujinwo/tsie-market-regime-dataset&config=default&split=train`
- Author: `sujinwo`
- License tag/card: `mit`
- Public/gated status: public, not gated, not disabled
- Last modified: `2026-04-13T13:27:46.000Z`
- Commit SHA: `75e7e2f86c37f8f28204651dcccf8338ca50aa6b`
- File: `tft_dataset_labeled.parquet`
- Rows: `7193996`
- Columns: `32`
- Parquet bytes: `591890794`

## Schema Signals

Fields observed through the Hugging Face dataset server include:

- Native timestamp field: `time` with type `timestamp[ns]`
- Session/hour fields: `hour`, `is_opening`, `is_closing`, `is_session_1`, `is_session_2`
- OHLCV fields: `open`, `high`, `low`, `close`, `volume`
- Source label field: `regime_label` with type `int8`

First-row samples are timestamped intra-day rows such as `2013-01-07T02:00:00`, `2013-01-07T03:00:00`, `2013-01-07T04:00:00`, `2013-01-07T06:00:00`, and `2013-01-07T07:00:00` for `group_id=IDX_DLY_AALI_60`.

The README describes a 7-class market regime label set:

- `0` STRONG SELL
- `1` WEAK SELL
- `2` BEAR TRAP
- `3` FLAT / NOISE
- `4` BULL TRAP
- `5` WEAK BUY
- `6` STRONG BUY

## Decision

This is a material R3 candidate because it is public, MIT-licensed, timestamped, session-aware, and includes a source `regime_label` column at sub-day timestamps. It is not accepted evidence yet.

Blockers before any Board A promotion:

- Raw parquet was not downloaded or verified locally.
- `/tmp/ict-engine-native-subhour-source-label-intake` remains absent and unmutated.
- The 7-class source labels are not yet mapped into `MainRegimeV2::{Bull,Bear,Sideways,Crisis}`.
- `Crisis` is not directly obvious from the README label taxonomy.
- Chronological, heldout-market, heldout-timeframe, and cross-market confidence calibration have not run.
- Provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion rerun remains disallowed until a required root is actually unlocked.

Promotion remains blocked: accepted rows added `0`, source/control evidence acquired false, target root mutated false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

If this candidate is selected, download the parquet into `/tmp`, compute SHA-256, map source labels fail-closed into `MainRegimeV2`, materialize a verifier-native R3 intake under `/tmp/ict-engine-native-subhour-source-label-intake`, then run native-subhour verifier, chronological and heldout splits, and only afterward consider canonical merge and downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree readback.
