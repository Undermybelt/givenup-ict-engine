# Native Sub-hour Source Label Intake Request Template v1

We need owner-approved or source-native sub-hour market-regime labels for an audit of regime-confidence transfer across markets and cycles.

Required scope:
- Active native intraday request rows: 336
- Immediate focus cells from the live blocker: 4
- Timeframes: 1m, 5m, 15m, 30m, 1h, and 4h only when the labels are source-native at that horizon.
- Root labels: Bull, Bear, Sideways, Crisis.

Required files:
- `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_rows.csv`
- `/tmp/ict-engine-native-subhour-source-label-intake/native_subhour_source_label_provenance.json`

Required boundary:
- Do not provide HMM/KMeans/classifier/future-return/generated/OHLCV-only labels.
- Do not provide daily or monthly labels projected into sub-hour windows.
- Include source version, license or permission, row ids, and per-row provenance.
