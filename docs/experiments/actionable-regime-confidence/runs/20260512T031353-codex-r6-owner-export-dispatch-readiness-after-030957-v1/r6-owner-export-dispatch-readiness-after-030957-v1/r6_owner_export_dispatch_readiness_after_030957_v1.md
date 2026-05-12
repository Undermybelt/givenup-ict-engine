# R6 Owner-Export Dispatch Readiness After 030957 v1

Run id: `20260512T031353-codex-r6-owner-export-dispatch-readiness-after-030957-v1`

Gate result: `r6_owner_export_dispatch_readiness_after_030957_v1=requests_ready_dispatch_or_approval_required_rows_not_acquired`

## Scope

This packet converts the current R6 blocker into a dispatch checklist. It uses the existing `001636` request package, the `010127` route/entitlement readback, and the `030957` completion audit. It does not send external requests, mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Readback

| Input | Result |
|---|---|
| `001636` request package | request package ready, rows not acquired, external requests not sent |
| `010127` route entitlement | route fit improved, valid source-owned normal controls `0`, owner-export root absent |
| `030957` current objective audit | not complete; `030617` fail-closed, `030623` durable source-control poll, `030722` reference broken |

## Dispatch Checklist

| Step | Evidence Required Before Promotion |
|---|---|
| CME owner/export request | Licensed CME Market Depth / Market by Order or equivalent order-lifecycle export for the Oystacher CME/NYMEX/COMEX window, with ticket/export/license id and provenance |
| Cboe/CFE owner/export request | CFE VIX futures trades/quotes and, if needed, historical depth/order-lifecycle export confirmation with provenance |
| Control policy | Either source-owned normal controls are supplied, or same-exhibit `FLIP` rows are explicitly approved as matched controls |
| Verifier-native delivery | Populate `/tmp/ict-engine-board-a-r6-owner-export-v1` with the filenames required by the current direct verifier |
| Downstream rerun | Only after verifier and split calibration pass, rerun provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree |

## Filename Contract Warning

The `001636` request package names conceptual delivery files as `direct_manipulation_positive_rows.csv`, `direct_manipulation_matched_controls.csv`, and `direct_manipulation_provenance.json`.

The current `030617` verifier invocation expects verifier-native files named `positive_spoofing_layering_rows.csv`, `matched_negative_normal_activity_rows.csv`, and `provenance_manifest.json`.

Do not treat a delivered package as verifier-ready unless this filename contract is satisfied or an explicit verifier/mapping update is made and recorded. The safest current path is to deliver/copy verifier-native filenames under `/tmp/ict-engine-board-a-r6-owner-export-v1` before rerunning the direct verifier.

## Decision

- Dispatch readiness: `ready_to_dispatch_or_request_owner_approval`.
- Rows acquired: `false`.
- Owner-export root complete: `false`.
- Explicit `FLIP` approval present: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Send or satisfy the owner/export requests and preserve ticket/export/license identifiers in provenance. After real files or explicit approval arrive, use the verifier-native filename contract above, rerun the direct verifier, then rerun split calibration and the full provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree chain.
