# R6 Owner Export Dispatch Manifest v2 v5 Addendum v1

Run id: `20260512T052711-codex-r6-owner-export-dispatch-manifest-v2-v5-addendum-v1`

Gate result: `r6_owner_export_dispatch_manifest_v2_v5_addendum_v1=dispatch_manifest_refreshed_to_v5_not_sent_controls_not_acquired`

Board sha256 before artifact: `bd4384a420ba31e431b180e8493231a562aac7807385049c2f750fed506ef572`

## Purpose

This packet refreshes the R6 owner-export dispatch-readiness manifest so it points at the current v5 request wrapper, not the older v3 request drafts. It is a dispatch-readiness artifact only. It does not send external email, acquire controls, approve same-exhibit `FLIP` rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, run canonical merge, rerun downstream promotion, make a trade claim, or call `update_goal`.

## Inputs

- v5 sendable request wrapper: `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1`
- Bessembinder/CFTC comparison-cohort addendum: `docs/experiments/actionable-regime-confidence/runs/20260512T051015-codex-r6-bessembinder-control-cohort-source-delta-v1/r6-bessembinder-control-cohort-source-delta-v1/r6_bessembinder_control_cohort_request_addendum_v1.md`
- Prior v1 dispatch manifest and contact routes: `docs/experiments/actionable-regime-confidence/runs/20260512T052444-codex-r6-owner-export-dispatch-manifest-v1`

## Dispatch Items

| owner | primary route | fallback route | current request wrapper | dispatch draft |
|---|---|---|---|---|
| CME Group | `CMEDataSales@cmegroup.com` | `marketdata@cmegroup.com` | `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/cme_group_owner_export_request_v5_with_bessembinder_addendum.md` | `cme_group_owner_export_dispatch_v2.eml` |
| Cboe/CFE | `marketdata@cboe.com` | DataShop contact form / phone from `010506` | `docs/experiments/actionable-regime-confidence/runs/20260512T052231-codex-r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/r6-owner-export-sendable-requests-v5-with-bessembinder-addendum-v1/cboe_cfe_owner_export_request_v5_with_bessembinder_addendum.md` | `cboe_cfe_owner_export_dispatch_v2.eml` |

## Required Delivery After Vendor/User Action

Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`

Required verifier-native files:
- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

The provenance manifest must preserve ticket/export/license/order/support identifiers and source-owner cohort labels. Same-exhibit `FLIP` rows remain rejected as controls unless the user or board explicitly approves that exception.

## Decision

Dispatch readiness is now aligned to the freshest request packet. External requests sent by this artifact: `false`. Valid source-owned normal controls acquired now: `0`. Canonical merge allowed now: `false`. Downstream rerun allowed now: `false`.

Promotion status remains unchanged: accepted rows added `0`, accepted regime-confidence labels `0`, source/control evidence acquired `false`, new confidence gate `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Send or otherwise satisfy the v2 CME/Cboe/CFE dispatch drafts, preserving ticket/export/license identifiers in provenance. After verifier-native controls and provenance arrive under the approved target root, rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
