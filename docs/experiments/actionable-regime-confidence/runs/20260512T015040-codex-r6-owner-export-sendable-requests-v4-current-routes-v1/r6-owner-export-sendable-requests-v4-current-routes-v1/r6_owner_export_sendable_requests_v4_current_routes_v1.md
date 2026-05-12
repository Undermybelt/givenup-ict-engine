# R6 Owner Export Sendable Requests v4 Current Routes v1

- Run id: `20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1`.
- Gate result: `r6_owner_export_sendable_requests_v4_current_routes_v1=requests_refreshed_current_routes_controls_not_acquired_no_merge`.
- Inputs: v3 sendable request packet `20260512T005913-codex-r6-owner-export-sendable-requests-v3`, required-cell matrix `20260512T005126-codex-r6-owner-export-request-bundle-v2`, and restored current-route recheck `20260512T014314-codex-r6-owner-route-current-web-recheck-v1`.
- Purpose: refresh only the sendable request drafts so the Cboe/CFE request matches the current route evidence. This is not approval, not submitted contact, not acquired data, not an owner-export root, and not a canonical merge.

## Required Delivery Contract

- Delivery root after approval/export: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files:
  - `positive_spoofing_layering_rows.csv`
  - `matched_negative_normal_activity_rows.csv`
  - `provenance_manifest.json`
- Valid controls must be source-owned normal/non-manipulation rows.
- Same-exhibit `FLIP` rows remain invalid unless the user/board explicitly approves that exception.

## Request Coverage

- Required Oystacher normal-control cells: `17`.
- CME Group cells: `13`.
- Cboe/CFE cells: `4`.
- Required valid source-owned normal controls per cell: `73`.
- Valid source-owned normal controls found now: `0`.
- Owner/vendor request submitted by this packet: `false`.
- Ticket/export identifier received: `false`.
- Canonical merge allowed now: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun allowed now: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Current Route Alignment

- CME Group request stays aligned with the current route evidence: CME DataMine historical data plus CME Market Depth Files FAQ. It asks Data Sales to confirm product/date coverage for Market Depth/FIX-FAST, Market by Order, or licensed equivalent rows for the 2011-2013 CME/NYMEX/COMEX cells.
- Cboe/CFE request is refreshed from the older generic/public historical-data route toward the current route evidence: Cboe DataShop CFE VIX futures trades/quotes plus Cboe U.S. Futures Market Data Services for Top-of-Book/Depth-of-Book/custom historical support.
- Public history pages and route evidence remain routing/support evidence only. They do not prove source-owned normal controls were acquired.

## Created Request Drafts

- CME Group request v4: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/cme_group_owner_export_request_v4.md`
- Cboe/CFE request v4: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/cboe_cfe_owner_export_request_v4.md`
- Official route sources v4: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/official_route_sources_v4.csv`
- Cell summary v4: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/r6_owner_export_request_v4_cell_summary.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/r6_owner_export_sendable_requests_v4_current_routes_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/checks/r6_owner_export_sendable_requests_v4_current_routes_v1_assertions.out`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/scripts/r6_owner_export_sendable_requests_v4_current_routes_v1.py`

## Decision

This packet replaces v3 as the freshest sendable request packet because it incorporates the restored `014314` current-route evidence. It still does not satisfy the source/control gate. Do not populate `/tmp/ict-engine-board-a-r6-owner-export-v1` or rerun the full chain until verifier-native controls and provenance arrive, or until explicit same-exhibit `FLIP` approval is recorded.
