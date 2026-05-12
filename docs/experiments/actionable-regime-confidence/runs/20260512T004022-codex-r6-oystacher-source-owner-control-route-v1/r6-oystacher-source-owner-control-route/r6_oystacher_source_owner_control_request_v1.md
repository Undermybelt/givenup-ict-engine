# R6 Oystacher Source-Owned Normal Control Request v1

Target root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

Required coverage:
- At least `73` valid source-owned normal-control rows for each of the 17 Oystacher cells.
- CME/CME Globex/COMEX/NYMEX cells require CME owner-approved order-lifecycle exports.
- CFE/VIX cells require Cboe/CFE owner-approved order-lifecycle exports.

Boundary:
- Public market data, OHLCV bars, aggregate settlements, modern samples, and same-exhibit `FLIP` rows are not accepted controls unless an explicit exception approves FLIP-as-control.
