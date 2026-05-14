# R6 Owner Export Dispatch Manifest v1

Run id: `20260512T052444-codex-r6-owner-export-dispatch-manifest-v1`

Gate result: `r6_owner_export_dispatch_manifest_v1=dispatch_manifest_ready_not_sent_controls_not_acquired`

Board sha256 before artifact: `6f7e2dcbe697b7e4a3255a5500c68066807f2b1a19b21a422ea2d43532cbd802`

## Purpose

This packet binds the existing R6 sendable request drafts to the verified official contact routes. It is a dispatch-readiness artifact only. It does not send external email, acquire controls, approve same-exhibit `FLIP` rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Inputs

- Sendable request drafts: `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3`
- Official contact route check: `docs/experiments/actionable-regime-confidence/runs/20260512T010506-codex-r6-owner-export-official-contact-route-check-v1`

## Dispatch Items

| owner | primary route | fallback route | request draft | dispatch draft |
|---|---|---|---|---|
| CME Group | `CMEDataSales@cmegroup.com` | `marketdata@cmegroup.com` | `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/cme_group_owner_export_request_v3.md` | `cme_group_owner_export_dispatch_v1.eml` |
| Cboe/CFE | `marketdata@cboe.com` | DataShop contact form / phone from `010506` | `docs/experiments/actionable-regime-confidence/runs/20260512T005913-codex-r6-owner-export-sendable-requests-v3/r6-owner-export-sendable-requests-v3/cboe_cfe_owner_export_request_v3.md` | `cboe_cfe_owner_export_dispatch_v1.eml` |

## Required Delivery After Vendor/User Action

Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

The provenance manifest must preserve ticket/export/license/order/support identifiers. Same-exhibit `FLIP` rows remain rejected as controls unless the user or board explicitly approves that exception.

## Decision

Dispatch readiness is improved, but the source/control gate is unchanged. External requests sent by this artifact: `false`. Valid source-owned normal controls acquired now: `0`. Canonical merge allowed now: `false`. Downstream rerun allowed now: `false`.

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired `false`, new confidence gate `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Send or otherwise satisfy the CME and Cboe/CFE owner-export requests. After verifier-native controls and provenance arrive under the approved target root, rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
