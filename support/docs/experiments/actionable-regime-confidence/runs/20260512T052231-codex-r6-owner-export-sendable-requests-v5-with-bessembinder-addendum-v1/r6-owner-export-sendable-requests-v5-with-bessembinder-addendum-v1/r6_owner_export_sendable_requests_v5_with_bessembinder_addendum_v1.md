# R6 Owner Export Sendable Requests v5 With Bessembinder Addendum v1

- Run id: `20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1`.
- Gate result: `r6_owner_export_sendable_requests_v5_with_bessembinder_addendum_v1=request_packet_refreshed_addendum_integrated_controls_not_acquired_no_merge`.
- Inputs:
  - v4 current-route request packet: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/r6_owner_export_sendable_requests_v4_current_routes_v1.md`
  - Bessembinder/CFTC comparison-cohort addendum: `docs/experiments/actionable-regime-confidence/runs/20260512T051015-codex-r6-bessembinder-control-cohort-source-delta-v1/r6-bessembinder-control-cohort-source-delta-v1/r6_bessembinder_control_cohort_request_addendum_v1.md`
- Purpose: register the current sendable owner-export packet as v4 route text plus the Bessembinder/CFTC comparison-cohort addendum. This is request text only; it is not submitted contact, ticket confirmation, acquired data, source/control evidence, canonical merge input, or downstream promotion authorization.

## Current Sendable Packet

- CME Group request v5 wrapper: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/cme_group_owner_export_request_v5_with_bessembinder_addendum.md`
- Cboe/CFE request v5 wrapper: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/cboe_cfe_owner_export_request_v5_with_bessembinder_addendum.md`
- Bundle manifest: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6_owner_export_request_v5_bundle_manifest.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6_owner_export_sendable_requests_v5_with_bessembinder_addendum_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/checks/r6_owner_export_sendable_requests_v5_with_bessembinder_addendum_v1_assertions.out`

## Required Delivery Contract

- Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files:
  - `positive_spoofing_layering_rows.csv`
  - `matched_negative_normal_activity_rows.csv`
  - `provenance_manifest.json`
- Valid controls must be source-owned normal/non-manipulation rows or explicitly source-approved comparison-cohort rows.
- Same-exhibit `FLIP` rows remain invalid controls unless the user/board explicitly approves that exception.

## Added v5 Request Clause

When sending the v4 CME/Cboe request text, include the Bessembinder/CFTC comparison-cohort addendum. Ask the source owner or licensed data route to include verifier-native rows for:

- Oystacher flip/spoof rows used in the analysis.
- Other flipping market participants in the same products, dates, sessions, and market contexts.
- Broader market-participant activity rows for the same products and windows.
- Non-flip order rows suitable for normal/non-manipulation controls.

The requested rows need source/export provenance, product/date/session scope, source-stable participant or account keys when available, order event fields, and a source-owner or documented CFTC/Bessembinder cohort marker.

## Decision

This v5 packet supersedes v4 only as the freshest sendable request wrapper. It does not supersede the v4 route evidence or requested-cell tables, and it does not satisfy the source/control gate. Do not populate `/tmp/ict-engine-board-a-r6-owner-export-v1` or rerun verifier/calibration/downstream promotion until verifier-native controls and provenance arrive, or until explicit same-exhibit `FLIP` approval is recorded.

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.
