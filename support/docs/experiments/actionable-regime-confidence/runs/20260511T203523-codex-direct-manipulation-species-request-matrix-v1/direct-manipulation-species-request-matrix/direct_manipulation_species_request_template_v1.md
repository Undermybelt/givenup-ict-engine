# Direct Manipulation Species Row Request Template v1

We need source-owned or owner-approved direct market-manipulation rows for strict regime-confidence validation.

Required species:
- spoofing_layering
- quote_spoofing
- quote_stuffing
- pinging
- bear_raid
- painting_tape

Required row package:
- Positive manipulation rows for each species.
- Matched same-schema normal-activity controls.
- Provenance manifest with source owner, license or permission, source version, venue, symbol, date/session, and row ids.

Current direct-intake verifier still requires:
- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

Forbidden:
- Generated, simulated, synthetic, future-return, classifier, or OHLCV-only labels.
- Raw order-book data without source-owned positive labels.
- Paper/method/library evidence without replayable positive and matched-control rows.
