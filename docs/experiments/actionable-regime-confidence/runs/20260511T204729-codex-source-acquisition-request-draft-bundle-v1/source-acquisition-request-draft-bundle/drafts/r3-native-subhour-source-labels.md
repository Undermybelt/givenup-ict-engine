# No-Send Request Draft: R3-native-subhour-source-labels

Status: `draft_only_not_sent`

Subject: Board A source-owned evidence request: R3-native-subhour-source-labels

Target contact surface:
Kaggle stock-regime owner, Yahoo/Yahoo terms, Nasdaq, CME, Cboe, Polygon

Request:
We are preparing a reproducible source-owned/owner-approved validation package for a regime-confidence audit. Please advise whether you can provide or approve the following row-level files with provenance for offline verification:

- Requirements: `R3`
- Required intake root: `/tmp/ict-engine-native-subhour-source-label-intake`
- Required files: `native_subhour_source_label_rows.csv;native_subhour_source_label_provenance.json`
- Requested payload: source-native 1m/5m/15m/30m/1h/4h Bull/Bear/Sideways/Crisis labels with per-row provenance

Verification after receipt:
rerun native-subhour intake package check and source-label verifier if crosswalk rows are also supplied

Boundaries:
- This draft has not been sent.
- No private data has been downloaded.
- No proxy, generated, synthetic, future-return, or OHLCV-only labels will be accepted.
- Rows must be source-owned or owner-approved and include provenance sufficient to rerun the fail-closed Board A verifier.

