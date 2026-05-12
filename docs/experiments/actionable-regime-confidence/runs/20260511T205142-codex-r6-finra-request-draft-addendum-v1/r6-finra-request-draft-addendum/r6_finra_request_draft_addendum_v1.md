# No-Send FINRA Request Draft Addendum

Status: `draft_only_not_sent`

Subject: Board A R6 FINRA PMR source-owned detail row export request

Target official routes:
- `finra_potential_manipulation_report`: https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report (layering;quote_spoofing)
- `finra_report_center_technical_assistance`: https://www.finra.org/compliance-tools/report-center/technical-assistance (report_center_detail_data_export_mechanics)

Request:
We are preparing an offline reproducibility package for a direct market-manipulation regime-confidence audit. Please advise whether an entitled user or FINRA-approved export can provide redacted row-level Potential Manipulation Report detail data suitable for offline validation.

Required offline intake files:
- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

Minimum row/provenance needs:
- source-owned or FINRA-approved positive spoofing/layering or quote-spoofing rows
- same-schema matched normal activity controls
- venue/symbol/time fields sufficient for chronological split
- provenance manifest with source route, approval/license, export timestamp, and field definitions

Boundaries:
- This draft has not been sent.
- No authenticated account has been used.
- No private rows have been downloaded.
- No positive-only export is accepted as completion without matched same-schema controls.
