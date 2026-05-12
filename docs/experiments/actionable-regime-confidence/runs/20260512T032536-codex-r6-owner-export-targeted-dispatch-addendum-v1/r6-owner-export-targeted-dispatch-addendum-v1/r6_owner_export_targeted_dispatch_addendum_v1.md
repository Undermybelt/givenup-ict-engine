# R6 Owner Export Targeted Dispatch Addendum v1

Run id: `20260512T032536-codex-r6-owner-export-targeted-dispatch-addendum-v1`

Gate result: `r6_owner_export_targeted_dispatch_addendum_v1=dispatch_addendum_ready_rows_not_acquired_no_promotion`

## Scope

This packet converts the `032152` augmentation requirements into targeted owner/export request text and a verifier-native delivery checklist. It does not send external requests, acquire rows, mutate source roots, accept labels, approve `FLIP` rows, relax thresholds, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Inputs

- Latest durable current-objective audit: `20260512T031655-codex-current-objective-completion-audit-after-031435-v1`.
- Existing dispatch readiness: `20260512T031353-codex-r6-owner-export-dispatch-readiness-after-030957-v1`.
- Source-unlock readback: `20260512T032155-codex-source-unlock-readback-after-031655-v1`, gate `no_new_source_unlock_roots_sidecars_and_approval_still_nonpromoting`.
- Augmentation requirements: `20260512T032152-codex-r6-owner-export-augmentation-requirements-after-031655-v1`, gate `requirements_quantified_no_source_rows_acquired_no_promotion`.
- Official route refresh: `20260512T032258-codex-r6-owner-route-refresh-after-031655-v1`, gate `official_routes_current_controls_not_acquired_no_merge`.

## Minimum Delivery Contract

- Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Required verifier-native files:
  - `positive_spoofing_layering_rows.csv`
  - `matched_negative_normal_activity_rows.csv`
  - `provenance_manifest.json`
- Per failed cell, request at least `73` source-owned positive rows and `73` source-owned matched normal-control rows, or an explicitly approved family-level split/control contract.
- Current deficits from `032152`:
  - Chronological split: `3` failed cells, `142` positive rows plus `142` matched controls still needed.
  - Heldout exact-symbol split: `40` failed cells, `2843` positive rows plus `2843` matched controls still needed.
  - Heldout exact-venue split: `11` failed cells, `726` positive rows plus `726` matched controls still needed.

## Dispatch Addendum Text

### CME / CME DataMine / Market Depth

Request licensed CME Market Depth, Market by Order, or equivalent order-lifecycle rows for the CME/CBOT/NYMEX/COMEX Oystacher-related cells in the `032152` deficit table. The export must preserve ticket/export/license identifiers in provenance and include enough source-owned normal-control rows to satisfy the exact chronological, symbol, and venue deficits. Deliver or map the result into the verifier-native filenames above.

Minimum useful fields: timestamp, venue, product, contract, expiry, order or message identifier, side, price, quantity, action/message type, source label or policy-backed class, matched group id where applicable, and export/license provenance.

### Cboe / CFE / DataShop

Request historical CFE VIX futures trades/quotes plus, if available, depth/order-lifecycle rows for the Oystacher-era VIX cells. The legacy VIX trades/quotes product fits the 2013/2014 date window but is not by itself proven sufficient for matched normal controls; ask support to confirm whether historical order-lifecycle/depth fields can be exported for the relevant window. If only the current CFE Futures Trades schema is available, record the date mismatch because it starts after the Oystacher VIX window.

### Explicit Approval Alternative

If owner/export rows cannot be delivered, record an explicit board/user decision for both:

- public RECAP/PACER Exhibit A provenance use, and
- same-exhibit `FLIP` rows as matched controls under the current contract.

Without that explicit decision, `FLIP` rows remain non-promoting sidecar evidence.

## Decision

- Dispatch addendum ready: `true`.
- External requests sent: `false`.
- Rows acquired: `false`.
- Source-owned normal controls acquired: `0`.
- Explicit `FLIP` approval present: `false`.
- R6 owner-export root complete: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Send or satisfy the targeted owner/export request addendum, preserve export/ticket/license identifiers in `provenance_manifest.json`, then populate the verifier-native target root under a shared lock. Only after direct verifier and split calibration pass should provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree rerun.
