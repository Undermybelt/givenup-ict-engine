# R6 Owner Export Outbound Request Messages v1

- Run id: `20260512T005842-codex-r6-owner-export-outbound-request-messages-v1`.
- Input bundle: `docs/experiments/actionable-regime-confidence/runs/20260512T005126-codex-r6-owner-export-request-bundle-v2`.
- Gate result: `r6_owner_export_outbound_request_messages_v1=outbound_messages_ready_not_sent_controls_not_acquired`.
- Required Oystacher normal-control cells represented: `17`.
- Required support per cell: `73` valid source-owned normal/non-manipulation controls.
- Delivery root after acquisition: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files after acquisition: `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.
- External requests sent by this artifact: false.
- Valid source-owned normal controls acquired now: `0`.
- Same-exhibit `FLIP` approval acquired now: false.
- Canonical merge allowed now: false.
- Downstream rerun allowed now: false.

## Messages

- CME Group request: `docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/r6-owner-export-outbound-request-messages-v1/cme_group_owner_export_request_message_v1.md`
- Cboe/CFE request: `docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/r6-owner-export-outbound-request-messages-v1/cboe_cfe_owner_export_request_message_v1.md`
- Request index CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/r6-owner-export-outbound-request-messages-v1/r6_owner_export_outbound_request_index_v1.csv`
- Summary JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/r6-owner-export-outbound-request-messages-v1/r6_owner_export_outbound_request_messages_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T005842-codex-r6-owner-export-outbound-request-messages-v1/checks/r6_owner_export_outbound_request_messages_v1_assertions.out`

## Guardrails

- These messages request source-owned normal/non-manipulation order-lifecycle controls only.
- Same-exhibit `FLIP` rows remain rejected as controls unless the user or board explicitly approves that exception.
- Raw market-depth data is not promoted to verifier-ready controls unless it arrives with source-owner provenance and enough schema detail to satisfy the verifier-native contract.
- No provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion rerun is allowed until controls and provenance arrive or the `FLIP` exception is approved.

## Next

Send or otherwise satisfy the two owner/export requests, then place verifier-native controls plus provenance under `/tmp/ict-engine-board-a-r6-owner-export-v1` under the shared lock. Only then rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
