# R6 FINRA Authenticated Export Route v1

- Run id: `20260512T002732-codex-r6-finra-auth-export-route-v1`.
- Board cursor observed: `20260512T001636+0800-codex-r6-owner-export-request-package-v1`.
- Target intake root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Gate result: `r6_finra_auth_export_route_v1=official_access_path_identified_rows_not_acquired`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Official FINRA Route

Source-backed route for the owner/user-approved export branch:

1. Use FINRA Report Center access for the relevant firm/MPID through the firm's Super Account Administrator.
2. Open the Cross-Market Equities Supervision Potential Manipulation Report.
3. Request/export the detail data for layering and quote-spoofing exceptions as CSV.
4. Transform the export into the Board A intake contract:
   - `direct_manipulation_positive_rows.csv`
   - `direct_manipulation_matched_controls.csv`
   - `direct_manipulation_provenance.json`
5. Also provide verifier-native filenames, or an explicit approved adapter/copy step, because the unchanged direct verifier currently expects:
   - `positive_spoofing_layering_rows.csv`
   - `matched_negative_normal_activity_rows.csv`
   - `provenance_manifest.json`
6. Put the owner-approved files under `/tmp/ict-engine-board-a-r6-owner-export-v1`.
7. Rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.

## Source Readback

- FINRA Potential Manipulation Report is a monthly Cross-Market Equities Supervision report for firm order-entry/trading-activity exceptions and includes layering plus cross-market quote-spoofing analyses.
- FINRA documents detail-data fields that map to Board A positive-row needs, including trade date, symbol, participant identifier, side, earliest/latest order-received times, order count, total quantity, market center code, and activity description.
- FINRA Report Center access is controlled through the firm's SAA, and the user must have the relevant firm/identifier privileges.
- FINRA Report Center supports CSV export for report contents and detail-data request/retrieval for report cards.

## Blocker

No authenticated FINRA export, matched normal controls, owner approval artifact, or approved filename adapter was available in this environment. This artifact identifies the official acquisition path only; it does not create accepted rows or approve a different split contract.

## Next

Place owner/user-approved FINRA or equivalent venue/CAT/exchange export files under `/tmp/ict-engine-board-a-r6-owner-export-v1`, with verifier-native filenames or an approved adapter step, or record explicit approval for a different split contract; then rerun the full Board A chain while keeping R5 and R3 blocked.
