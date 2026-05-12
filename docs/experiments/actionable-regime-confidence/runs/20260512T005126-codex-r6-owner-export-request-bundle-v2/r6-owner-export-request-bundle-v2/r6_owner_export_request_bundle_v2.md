# R6 Owner Export Request Bundle v2

- Run id: `20260512T005126-codex-r6-owner-export-request-bundle-v2`.
- Gate result: `r6_owner_export_request_bundle_v2=request_ready_controls_not_acquired_no_merge`.
- Required Oystacher normal-control cells: `17`.
- Cells with owner route: `17`.
- CME Group cells: `13`; Cboe/CFE cells: `4`.
- Required support per cell: `73` valid source-owned normal controls.
- Delivery root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files: `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, `provenance_manifest.json`.
- Valid source-owned normal controls found now: `0`.
- Canonical merge allowed now: `false`; downstream rerun allowed now: `false`.
- Accepted rows added: `0`; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. Owner-export root mutated: false. Raw data committed: false. External requests sent: false.

## What To Request

- CME/NYMEX/COMEX/CME Globex cells: CME DataMine/FIX-FAST/Market by Order or licensed equivalent with 2011-2013 product/date coverage confirmation.
- VIX/CFE cell: Cboe/CFE DataShop or market-data support export that explicitly covers 2014 historical depth/order-lifecycle rows.
- Every delivered row must be a source-owned normal/non-manipulation control row and must not be same-exhibit `FLIP` unless the explicit exception is approved.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_owner_export_request_bundle_v2.json`
- Cell request CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_oystacher_required_cell_owner_export_request_v2.csv`
- Verifier-native schema CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_oystacher_verifier_native_control_schema_v2.csv`
- Provenance requirements CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_oystacher_provenance_manifest_requirements_v2.csv`
- Post-export chain CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/r6-owner-export-request-bundle-v2/r6_oystacher_post_export_chain_v2.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2/checks/r6_owner_export_request_bundle_v2_assertions.out`

## Next
Send the cell-level request to CME DataMine/FIX-FAST/Market by Order or licensed equivalent for CME/NYMEX/COMEX/CME Globex cells, and to Cboe/CFE DataShop or market-data support for the 2014 VIX/CFE depth/order-lifecycle cell. Only after verifier-native controls and provenance arrive should the owner-export root be populated and the full chain rerun.
