# R6 Owner-Export Request Status After 032258 v1

Run id: `20260512T032417-codex-r6-owner-export-request-status-after-032258-v1`

Gate result: `r6_owner_export_request_status_after_032258_v1=requests_ready_not_sent_rows_not_acquired_no_promotion`

Board sha256 before packet: `d6f4fd63a06d888fdad0a70f2c47aebe6d5d5200382d575c883b42fa30317bfa`

## Scope

This packet consolidates the current R6 owner-export request/readback state after the latest durable `031655` current-objective audit and the later `032152`, `032155`, `032258`, and `032302` side packets. It does not send external requests, acquire licensed rows, mutate `/tmp/ict-engine-board-a-r6-owner-export-v1`, approve same-exhibit `FLIP` controls, run canonical merge, rerun provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree, or call `update_goal`.

## Request Status

| Item | Status | Evidence |
|---|---|---|
| CME request draft | ready by local artifact, not dispatched by local evidence | `005913` created `cme_group_owner_export_request_v3.md`; `031353` and `032258` record external requests not sent |
| Cboe/CFE request draft | ready by local artifact, not dispatched by local evidence | `005913` created `cboe_cfe_owner_export_request_v3.md`; `031353` and `032258` record external requests not sent |
| Official route refresh | current enough for next owner contact | `032258` refreshed CME Market Depth / Market by Order and Cboe/CFE DataShop routes |
| Deficit quantification | current requirements quantified, rows still absent | `032152` requires `73` rows per class per evaluated cell and records `0` acquired rows |
| Source unlock | not unlocked | `032155` reads R6/R3/R5 roots absent and approval package non-approving |
| Provider/Auto-Quant refresh | read-only readiness only, no promotion | `032302` gate remains source-controls-blocked |

## Required Dispatch Readback Fields

Every real dispatch or owner/export delivery must preserve these fields in provenance before any verifier rerun:

- `owner`: CME Group or Cboe/CFE.
- `route`: exact product/support route used.
- `ticket_id` or `support_case_id`.
- `order_id`, `export_id`, `dataset_id`, or equivalent licensed-delivery identifier.
- `license_id`, `subscription_id`, approval grant, or explicit permission reference.
- `request_sent_at` and `response_received_at`, with timezone.
- `product_scope`: exchange, venue, product, contract, expiry, and symbol mapping.
- `date_range` and market-session/timezone basis.
- `field_dictionary` and timestamp precision.
- `normal_control_policy`: source-owned normal controls or explicit same-exhibit `FLIP` approval.
- `raw_delivery_hashes`, row counts, and source filenames.
- `verifier_file_mapping` to the required verifier-native filenames.

## Verifier-Native Delivery Contract

Do not treat any delivered package as verifier-ready unless `/tmp/ict-engine-board-a-r6-owner-export-v1` contains:

- `positive_spoofing_layering_rows.csv`
- `matched_negative_normal_activity_rows.csv`
- `provenance_manifest.json`

The older conceptual names from request bundles must either be delivered under these verifier-native names or mapped by an explicit verifier/mapping update before rerun.

## Current Blocking Facts

- Source-owned normal controls acquired: `0`.
- Explicit `FLIP` approval present: `false`.
- R6 owner-export root complete: `false`.
- R3 native sub-hour root exists: `false`.
- R5 recency-extension root exists: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Decision

The next actionable step is still external owner/export dispatch or an explicit owner/user approval decision. The local repo has sendable drafts and route/requirement evidence, but no ticket/export/license identifiers, no licensed rows, no accepted controls, and no source/control unlock.

## Next

Send or otherwise satisfy the CME and Cboe/CFE owner-export requests. Preserve ticket/export/license identifiers and the provenance fields above. Only after source/control gates unlock should the direct verifier, split calibration, and provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree chain rerun.
