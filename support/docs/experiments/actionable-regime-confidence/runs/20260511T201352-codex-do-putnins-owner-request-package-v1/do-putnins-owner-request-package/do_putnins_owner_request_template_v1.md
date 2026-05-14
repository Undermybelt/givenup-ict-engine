# Do/Putnins Spoofing/Layering Owner Request Template v1

Source target: `Detecting Layering and Spoofing in Markets`.
Source URL: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036`.
Readback URL: `https://studylib.net/doc/28317823/ssrn-4525036`.

Request:

Please provide a research/export package for the prosecuted layering/spoofing sample that contains:

1. `positive_spoofing_layering_rows.csv` with row-level positive events.
2. `matched_negative_normal_activity_rows.csv` with same-venue/symbol/session normal controls.
3. `provenance_manifest.json` with source ownership, source sections, export date or hash ids, redaction policy, and matched-control policy.

Required CSV fields:

label, source_report, source_section, trade_date, symbol, venue_or_market_center, participant_type_code, participant_identifier, side, earliest_order_received_time, latest_order_received_time, order_count, total_order_quantity, activity_description, matched_negative_group_id, session_bucket, source_row_id

The package will be checked locally with:

`python3 docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py --intake-root /tmp/ict-engine-direct-manipulation-row-intake`

Rows cannot be accepted if they are synthetic, simulated, positive-only, or raw order-book panels without source-owned manipulation labels.
