# R6 Owner Export Sendable Requests v3

- Run id: `20260512T005913-codex-r6-owner-export-sendable-requests-v3`.
- Gate result: `r6_owner_export_sendable_requests_v3=sendable_requests_created_controls_not_acquired_no_merge`.
- Source matrix: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_oystacher_required_cell_owner_export_request_v2.csv`.
- Required Oystacher normal-control cells: `17`.
- CME Group cells: `13`.
- Cboe/CFE cells: `4`.
- Required support per cell: `73` valid source-owned normal controls.
- Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files: `positive_spoofing_layering_rows.csv, matched_negative_normal_activity_rows.csv, provenance_manifest.json`.
- Valid source-owned normal controls found now: `0`.
- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.
- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Raw data committed: false. External requests sent: false.

## Created Request Drafts

- CME Group request: `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/cme_group_owner_export_request_v3.md`
- Cboe/CFE request: `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/cboe_cfe_owner_export_request_v3.md`
- Official route sources: `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/official_route_sources_v3.csv`

## Decision

This packet makes the active V71 owner-export next action sendable. It does not satisfy the source/control gate by itself. Do not populate `/tmp/ict-engine-board-a-r6-owner-export-v1` or rerun the full chain until verifier-native controls and provenance arrive, or until explicit same-exhibit `FLIP` approval is recorded.
