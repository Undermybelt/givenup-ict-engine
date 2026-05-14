# Wash Trading Public API Raw Access

Run id: `20260511T021058+0800-codex-wash-trading-public-api-raw-access`

This probe found the Mendeley public API path that exposes raw row-level CSV download URLs. It retained only metadata and first-row samples in the repo; no full raw CSVs were committed.

Files verified:

- `Blur_ml_samples.csv`: 346004976 bytes, label-like columns ['filter_1234']
- `gox_ml_samples.csv`: 986063630 bytes, label-like columns ['wash']
- `LooksRare_ml_samples.csv`: 38651230 bytes, label-like columns ['filter_1234']
- `OpenSea_ml_samples.csv`: 2127010916 bytes, label-like columns ['filter_1234']

Decision: `raw_event_onchain_wash_labels_accessible_not_calibrated`. Qualifying direct/event input sets: `1`. Accepted 95: `False`. Blocker: Mendeley public API exposes row-level labeled wash-trading CSV downloads, but this slice only verified metadata and bounded samples. A chronological calibration/test gate has not been run.

Next action: Stream the Mendeley wash-trading CSVs into a run-local calibration job, confirm label polarity for `filter_1234`, and evaluate the unchanged 95% Manipulation gate without committing raw data.
