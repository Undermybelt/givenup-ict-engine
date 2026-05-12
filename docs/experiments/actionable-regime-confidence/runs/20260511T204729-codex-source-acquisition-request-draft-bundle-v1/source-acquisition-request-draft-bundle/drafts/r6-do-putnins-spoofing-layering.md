# No-Send Request Draft: R6-do-putnins-spoofing-layering

Status: `draft_only_not_sent`

Subject: Board A source-owned evidence request: R6-do-putnins-spoofing-layering

Target contact surface:
SSRN author email links, SSRN contact-author, UTS profile, RePEc fallback

Request:
We are preparing a reproducible source-owned/owner-approved validation package for a regime-confidence audit. Please advise whether you can provide or approve the following row-level files with provenance for offline verification:

- Requirements: `R6`
- Required intake root: `/tmp/ict-engine-direct-manipulation-row-intake`
- Required files: `positive_spoofing_layering_rows.csv;matched_negative_normal_activity_rows.csv;provenance_manifest.json`
- Requested payload: owner-approved prosecuted-case spoofing/layering positives, matched same-schema controls, and provenance manifest

Verification after receipt:
rerun direct_manipulation_row_intake_verifier_v1.py then chronological/heldout calibration

Boundaries:
- This draft has not been sent.
- No private data has been downloaded.
- No proxy, generated, synthetic, future-return, or OHLCV-only labels will be accepted.
- Rows must be source-owned or owner-approved and include provenance sufficient to rerun the fail-closed Board A verifier.

