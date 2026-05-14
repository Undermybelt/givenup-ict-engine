# R3 native sub-hour cross-timeframe validation Request

Target root: `/tmp/ict-engine-native-subhour-source-label-intake`

Please provide source-owned or owner-approved rows for:

Source-native or owner-approved 1m/5m/15m/30m/1h/4h labels, especially AAPL and ^IXIC 15m/30m focus cells, with per-row source provenance.

Required delivery files:
- `native_subhour_source_label_rows.csv`
- `native_subhour_source_label_provenance.json`

Required row schema:
`source_row_id`, `source_name`, `owner_or_licensor`, `license_or_permission`, `instrument`, `timeframe`, `timestamp_start_utc`, `timestamp_end_utc`, `root_label`, `source_label`, `qualifying_condition`, `confidence_or_quality_flag`, `validation_instrument_group`, `validation_period`, `validation_market_context`, `provenance_url_or_path`, `source_version_hash`, `forbidden_proxy_flag`

Provenance requirements:
- identify the source owner/licensor
- include source dataset, export, ticket, or written approval reference
- include source version/hash or raw export hash
- state license constraints and whether raw rows can be committed
- state why rows are source-native labels rather than generated/HMM/KMeans/future-return/OHLCV proxy labels

Route:
Kaggle stock-regime owner, Yahoo/Nasdaq/CME/Cboe/Polygon source or licensing contacts

After delivery:
Place files under `/tmp/ict-engine-native-subhour-source-label-intake` and rerun `native-subhour package readback plus unchanged completion audit`. Schema readiness is not a confidence gate by itself; after verifier readiness, rerun the unchanged chronological/heldout-market/timeframe calibration and completion audit.

Current blocker:
R3 native-subhour root is absent; daily/monthly projections remain rejected.
