# FINRA Manipulation Acquisition Schema v1

Run ID: `20260511T133337+0800-codex-finra-manipulation-acquisition-schema-v1`

## Result

- Accepted direct `Manipulation` rows added: `0`.
- New calibration gate claimed: `false`.
- Concrete acquisition target: row-level spoofing/layering positives plus matched normal-activity controls using the FINRA Potential Manipulation Report field shape.
- Gate result: `finra_spoofing_layering_schema_package_ready_rows_not_acquired`.
- Full objective achieved: `false`.

## Why This Exists

The current direct `Manipulation` blocker is not another source-search problem. The missing piece is row-level data: spoofing/layering positives and matched negatives with the same venue, symbol, date/session, timestamps, side, order-count, quantity, market-center, and activity-description fields.

The public FINRA page is useful because it describes the report and detail-data field family, but it does not provide exportable rows. This artifact turns that into an acquisition contract instead of another negative sweep.

## Required Row Files

- Positive rows: timestamped spoofing/layering rows matching `finra_manipulation_acquisition_schema_v1.csv`.
- Matched negatives: same schema, same venue/instrument/date/session/liquidity bucket, but normal activity.
- Provenance manifest: source export identity, pull date, source owner, and row redaction notes.

## Acceptance Contract

- Taxonomy: direct `Manipulation` variety only.
- Target variety: `spoofing_layering`.
- Calibration: chronological calibration/test split plus heldout symbol or venue split.
- Acceptance: Wilson95 lower bound `>= 0.95` on calibration, heldout-time, and heldout-symbol/venue splits.
- Abstain: missing matched-negative group, missing timestamps, missing venue/symbol, or source rows not from direct order-lifecycle/report export.

## Guardrails

- Does not promote OHLCV/session/liquidity/sweep proxies.
- Does not use synthetic detector rows as direct evidence.
- Does not alter `MainRegimeV2` price-root accounting.
- No runtime code changed.
- No thresholds relaxed.
- No raw data committed.
- Not trade usable.

## Artifacts

- Schema CSV: `finra_manipulation_acquisition_schema_v1.csv`
- Schema JSON: `finra_manipulation_acquisition_schema_v1.json`
