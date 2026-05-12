# No-Send Request Draft: R2-source-label-equivalence-crossmarket

Status: `draft_only_not_sent`

Subject: Board A source-owned evidence request: R2-source-label-equivalence-crossmarket

Target contact surface:
Kaggle owner, Nasdaq indexes/licensing, CME, Kraken public data/contact surfaces

Request:
We are preparing a reproducible source-owned/owner-approved validation package for a regime-confidence audit. Please advise whether you can provide or approve the following row-level files with provenance for offline verification:

- Requirements: `R2`
- Required intake root: `/tmp/ict-engine-source-label-equivalence-intake`
- Required files: `source_label_equivalence_rows.csv;source_label_equivalence_provenance.json`
- Requested payload: owner-approved or source-owned cross-market/species equivalence rows and provenance

Verification after receipt:
rerun source_label_equivalence_intake_verifier_v1.py

Boundaries:
- This draft has not been sent.
- No private data has been downloaded.
- No proxy, generated, synthetic, future-return, or OHLCV-only labels will be accepted.
- Rows must be source-owned or owner-approved and include provenance sufficient to rerun the fail-closed Board A verifier.

