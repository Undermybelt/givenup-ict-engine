# TSIE Source-Label Intake Dry Run v1

Run id: `20260512T022005-codex-tsie-source-label-intake-dryrun-v1`

Gate result: `tsie_source_label_intake_dryrun_v1=full_parquet_support_screen_passed_acceptance_blocked_no_intake_mutation`

## Objective Mapping

This is a non-R6 `/tmp`-only source-label dry run following the public-source candidate readback. It tests whether `sujinwo/tsie-market-regime-dataset` has enough full-parquet support to be worth a later canonical source-label intake path.

It does not accept regimes, mutate shared intake roots, relax thresholds, submit owner/export requests, approve `FLIP` rows, rerun downstream promotion, or call `update_goal`.

## Source

- Dataset: `sujinwo/tsie-market-regime-dataset`
- URL: <https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset>
- License: `mit`
- Dataset sha: `75e7e2f86c37f8f28204651dcccf8338ca50aa6b`
- Last modified: `2026-04-13T13:27:46.000Z`
- Parquet URL: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet`
- Parquet sha256: `8b6f25f8b2aba162af2eac30b1a8a9df662fc5dd04878e933f42c8df4eaa6158`
- Raw parquet location: `/tmp/ict-engine-board-a-tsie-market-regime-dryrun-20260512T0200/0000.parquet`

## Full-Parquet Support

- Rows read: `7193996` / API rows `7193996`
- Feature count from API: `32`
- Time span: `1990-06-07T02:00:00` to `2026-04-07T02:00:00`
- Year span: `1990` to `2026`
- Unique group ids: `1150`
- Unique hours: `[2, 3, 4, 5, 6, 7, 8, 9]`
- Group ids with Bear, Bull, and Sideways support after abstaining traps: `1150` / `1150`

## Label Mapping

- `0 STRONG_SELL` -> `Bear`
- `1 WEAK_SELL` -> `Bear`
- `2 BEAR_TRAP` -> `ABSTAIN_TRAP`
- `3 FLAT_NOISE` -> `Sideways`
- `4 BULL_TRAP` -> `ABSTAIN_TRAP`
- `5 WEAK_BUY` -> `Bull`
- `6 STRONG_BUY` -> `Bull`

Mapped counts:

- Bear: `1435764`
- Bull: `1435055`
- Sideways: `2162084`
- ABSTAIN_TRAP: `2161093`

## Decision

Candidate support is large enough for a future source-label intake experiment, but acceptance remains blocked.

Blockers:

- R6 owner-export/control gate remains the current board blocker.
- Dataset labels are public/rule-based IDX labels, not source-owned MainRegimeV2 acceptance labels.
- Trap labels must abstain; they cannot be forced into Bear/Bull.
- No canonical intake mutation or downstream promotion rerun happened.
- Chronological split calibration, cross-market transfer, and board approval are still required before any acceptance.

## Artifacts

- JSON summary: `tsie_source_label_intake_dryrun_v1.json`
- Label counts: `label_counts.csv`
- Mapped regime counts: `mapped_regime_counts.csv`
- Year counts: `year_counts.csv`
- Hour counts: `hour_counts.csv`
- Top group support: `group_mapped_support_top100.csv`
- Sample mapped rows: `sample_rows_mapped.csv`
