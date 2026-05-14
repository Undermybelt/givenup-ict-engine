# R6 Owner Export Operator Handoff v2

- Run id: `20260512T015055-codex-r6-owner-export-operator-handoff-v2`.
- Gate result: `r6_owner_export_operator_handoff_v2=operator_packet_ready_no_request_submitted_no_controls_acquired`.
- Current Cursor preserved: `true`.
- Board hash before artifact refresh: `87c088095b63318a9eebfc8a8012496d4ab915e887c8df96abc382cdb15a142f`.

## Purpose

This packet turns the current R6 next action into an operator handoff. It does not submit vendor requests, acquire controls, mutate intake roots, approve `FLIP`, or authorize downstream promotion.

## Operator Packet

| Owner | Request draft | Cells | Required support per cell | Current status |
|---|---|---:|---:|---|
| CME Group | `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/cme_group_owner_export_request_v4.md` | `13` | `73` | ready, not submitted by this packet |
| Cboe/CFE | `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/cboe_cfe_owner_export_request_v4.md` | `4` | `73` | ready, not submitted by this packet |

The `015040` v4 request packet supersedes the earlier v3 request drafts as the freshest sendable request set.

Current send/support route evidence:
- CME DataMine historical data: `https://www.cmegroup.com/market-data/datamine-historical-data/index.html`
- CME Market Depth Files FAQ: `https://www.cmegroup.com/market-data/files/cme-group-market-depth-faq.pdf`
- Cboe DataShop CFE VIX futures trades and quotes: `https://datashop.cboe.com/cfe-vix-volatility-index-futures-trades-quotes`
- Cboe U.S. Futures Market Data Services: `https://ww2.cboe.com/market_data_services/us/futures/`

## Required Delivery

After owner/operator submission, the response must preserve:
- `licensed_export_reference`: invoice, order, ticket, export id, or owner approval reference.
- `raw_file_sha256`: hash of raw export kept outside repo.
- `field_mapping`: owner columns mapped to verifier-native fields.
- `normal_control_basis`: why rows are normal/non-manipulation controls and not same-exhibit `FLIP`.
- `license_constraints`: raw data commit policy, default false.

Only after evidence arrives and the shared lock is available should the root `/tmp/ict-engine-board-a-r6-owner-export-v1` contain:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

## Post-Arrival Chain

1. Place owner-export files under `/tmp/ict-engine-board-a-r6-owner-export-v1` only after owner export or explicit `FLIP` approval plus shared lock.
2. Run direct verifier: `python3 docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py --intake-root /tmp/ict-engine-board-a-r6-owner-export-v1`.
3. Only after verifier pass and canonical merge permission: split calibration -> provider status -> Auto-Quant -> Pre-Bayes/BBN -> CatBoost/path-ranking -> execution-tree readback.

## Result

- Owner/vendor request submitted: `false`.
- Ticket/export identifier received: `false`.
- Source-owned normal controls acquired: `0`.
- Explicit `FLIP` approval acquired: `false`.
- Accepted rows added: `0`; new confidence gate: false; canonical merge allowed: false; downstream promotion rerun allowed: false; strict full objective achieved: false. `update_goal=false`.
- Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Thresholds relaxed: false. Raw data committed: false. External contact submitted: false. Trade usable: false.

## Boundary

The empty staging root `docs/experiments/actionable-regime-confidence/runs/20260512T014941-codex-r6-owner-export-operator-handoff-v1` was observed and left untouched to avoid interfering with concurrent work.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T015055-codex-r6-owner-export-operator-handoff-v2/r6-owner-export-operator-handoff-v2/r6_owner_export_operator_handoff_v2.json`
- Channel CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T015055-codex-r6-owner-export-operator-handoff-v2/r6-owner-export-operator-handoff-v2/r6_owner_export_operator_handoff_channels_v2.csv`
- Delivery checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T015055-codex-r6-owner-export-operator-handoff-v2/r6-owner-export-operator-handoff-v2/r6_owner_export_operator_delivery_checklist_v2.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T015055-codex-r6-owner-export-operator-handoff-v2/checks/r6_owner_export_operator_handoff_v2_assertions.out`
- Reproduction script: `docs/experiments/actionable-regime-confidence/runs/20260512T015055-codex-r6-owner-export-operator-handoff-v2/scripts/r6_owner_export_operator_handoff_v2.py`
