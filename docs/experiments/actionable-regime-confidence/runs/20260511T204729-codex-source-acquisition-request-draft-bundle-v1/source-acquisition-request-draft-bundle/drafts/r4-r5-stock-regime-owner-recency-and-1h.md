# No-Send Request Draft: R4-R5-stock-regime-owner-recency-and-1h

Status: `draft_only_not_sent`

Subject: Board A source-owned evidence request: R4-R5-stock-regime-owner-recency-and-1h

Target contact surface:
Kaggle stock-regime owner discussion/profile and collaborator profile

Request:
We are preparing a reproducible source-owned/owner-approved validation package for a regime-confidence audit. Please advise whether you can provide or approve the following row-level files with provenance for offline verification:

- Requirements: `R4;R5`
- Required intake root: `/tmp/ict-engine-source-panel-recency-extension`
- Required files: `stock_market_regimes_2026_extension.csv;source_panel_recency_provenance.json`
- Requested payload: post-2026-01-30 source-owned extension rows for XOM/Sideways, UNH/Bear, ^DJI/Sideways, AMD/Bear and strict 1h source/provenance if available

Verification after receipt:
rerun source_panel_recency_extension_verifier_v1.py and strict 1h source gates

Boundaries:
- This draft has not been sent.
- No private data has been downloaded.
- No proxy, generated, synthetic, future-return, or OHLCV-only labels will be accepted.
- Rows must be source-owned or owner-approved and include provenance sufficient to rerun the fail-closed Board A verifier.

