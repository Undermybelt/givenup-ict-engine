# No-Send Request Draft: R6 CME Normal Controls

Purpose: acquire same-schema normal activity rows for Board A R6 direct Manipulation controls.

Requested file: `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`.

Positive group to match: `cftc_mohan_20131202_nq_example` from the public CFTC Krishna Mohan order.

Required matching axes:
- Source owner or owner-approved export: CME Group or other explicitly licensed CME historical order-book export.
- Venue: CME.
- Instrument family: E-mini NASDAQ / NQ futures.
- Session bucket: overnight Central Time.
- Normal activity: no spoofing/layering/manipulation finding for the control rows.
- Same Board A intake schema as `positive_spoofing_layering_rows.csv`.

Boundary: this draft was not sent. It does not grant permission, download private rows, or create accepted evidence.
