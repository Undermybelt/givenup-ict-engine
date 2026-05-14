# Market Data Vendor Native Sub-hour Label Availability Request v2

Subject: Availability request for source-native 15m/30m regime-label rows for AAPL and IXIC

We are looking for source-native or owner-approved sub-hour market-regime labels, not a derived label set produced from bars. The immediate cells are `AAPL` and `^IXIC` at 15m and 30m.

Focus cells:

| symbol | timeframe | provider_date_min | provider_date_max | source_date_max | source_overlap_sessions | blocker |
| --- | --- | --- | --- | --- | --- | --- |
| AAPL | 15m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| AAPL | 30m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| ^IXIC | 15m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |
| ^IXIC | 30m | 2026-02-12 | 2026-05-08 | 2026-01-30 | 0 | no_provider_session_overlap_with_source_panel_tail |

Request:
- Please confirm whether a licensed dataset or custom export can provide native 15m/30m regime-label intervals for these cells.
- If the available product is raw trades/quotes/bars only, please state that explicitly; raw market data by itself does not satisfy the source-label intake.
- If a source-native label export is available, please include date coverage, root-label vocabulary, version/export id, license/permission terms, and row-level provenance.

Required delivery root after approval/export: `/tmp/ict-engine-native-subhour-source-label-intake`

Required files:
- `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
- `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`

Accepted root labels: `Bull, Bear, Sideways, Crisis`.

Fail-closed boundary:
- Do not provide HMM/KMeans/classifier/future-return/generated/OHLCV-only labels.
- Do not provide daily or monthly labels projected into sub-hour windows.
- Include owner/licensor permission, source version/hash, row ids, per-row provenance, and per-root qualifying conditions.
- This request is not an external send record and does not authorize a downstream rerun by itself.


Required row fields:

- `source_row_id`: Stable row identifier from the owner/source package.
- `source_name`: Dataset, licensor, venue, or owner-approved source name.
- `owner_or_licensor`: Entity approving the label export or source-native label policy.
- `license_or_permission`: License, written permission, or export approval reference.
- `instrument`: Board A target instrument, for example QQQ, NQ=F, SPY, ES=F.
- `timeframe`: Native sub-hour timeframe: 1m, 5m, 15m, 30m, or exact 1h/4h if source-native.
- `timestamp_start_utc`: Start timestamp for the source-labeled interval in UTC.
- `timestamp_end_utc`: End timestamp for the source-labeled interval in UTC.
- `root_label`: One of Bull, Bear, Sideways, Crisis using the accepted MainRegimeV2 root vocabulary.
- `source_label`: Original owner/source label before normalization.
- `qualifying_condition`: Per-root condition that makes this row eligible for Board A, not borrowed from another regime.
- `confidence_or_quality_flag`: Source confidence, adjudication flag, or source quality marker; may be categorical.
- `validation_instrument_group`: Instrument/species group used for cross-market validation.
- `validation_period`: Chronological period bucket used for train/calibration/test separation.
- `validation_market_context`: Market context or provider/source context for the row.
- `provenance_url_or_path`: Owner-approved URL, local intake path, or manifest reference.
- `source_version_hash`: Dataset hash, source package version, or signed export id.
- `forbidden_proxy_flag`: Must be false. True means HMM/KMeans/classifier/future-return/generated/OHLCV-only proxy.
