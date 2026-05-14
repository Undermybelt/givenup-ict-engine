# R6 Owner Export v5 Dispatch Manifest v1

Run id: `20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1`

Gate result: `r6_owner_export_v5_dispatch_manifest_v1=v5_dispatch_drafts_ready_not_sent_controls_not_acquired`

Board sha256 before artifact: `bd4384a420ba31e431b180e8493231a562aac7807385049c2f750fed506ef572`

## Purpose

This packet reconciles the freshest `052231` v5 owner-export request text with the official dispatch contacts captured by the prior `052444` manifest. It creates v5 dispatch drafts only. It does not send external email, acquire controls, approve same-exhibit `FLIP` rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Inputs

- v4 current-route packet: `docs/experiments/actionable-regime-confidence/runs/20260512T015040-codex-r6-owner-export-sendable-requests-v4-current-routes-v1/r6-owner-export-sendable-requests-v4-current-routes-v1/r6_owner_export_sendable_requests_v4_current_routes_v1.md`
- v5 Bessembinder/CFTC request packet: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6_owner_export_sendable_requests_v5_with_bessembinder_addendum_v1.md`
- prior contact/dispatch evidence: `docs/experiments/actionable-regime-confidence/runs/20260512T052444-codex-r6-owner-export-dispatch-manifest-v1/r6-owner-export-dispatch-manifest-v1/r6_owner_export_dispatch_manifest_v1.json`

## Dispatch Drafts

| owner | primary route | fallback route | dispatch draft | status |
|---|---|---|---|---|
| CME Group | `CMEDataSales@cmegroup.com` | `marketdata@cmegroup.com` | `docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cme_group_owner_export_v5_dispatch_v1.eml` | draft_not_sent |
| Cboe/CFE | `marketdata@cboe.com` | `DataShop contact form or phone from 010506 contact-route check` | `docs/experiments/actionable-regime-confidence/runs/20260512T052650-codex-r6-owner-export-v5-dispatch-manifest-v1/r6-owner-export-v5-dispatch-manifest-v1/cboe_cfe_owner_export_v5_dispatch_v1.eml` | draft_not_sent |

## Required Delivery After Vendor/User Action

Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

The provenance manifest must preserve ticket/export/license/order/support identifiers. Same-exhibit `FLIP` rows remain rejected as controls unless the user or board explicitly approves that exception.

## Decision

Dispatch readiness is now aligned to the v5 request text. External requests sent by this artifact: `false`. Valid source-owned normal controls acquired now: `0`. Canonical merge allowed now: `false`. Downstream rerun allowed now: `false`.

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired `false`, new confidence gate `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Send or otherwise satisfy the v5 CME and Cboe/CFE owner-export requests. After verifier-native controls and provenance arrive under the approved target root, rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order. Keep R5/R3/source-label roots blocked until their exact source-owned inputs exist.
