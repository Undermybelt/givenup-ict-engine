# MainRegimeV2 Relock After Taxonomy Drift v10

Run ID: `20260511T130916+0800-codex-mainregimev2-relock-after-taxonomy-drift-v10`

This is a taxonomy correction packet, not a confidence gate.

## Decision

- Active denominator is relocked to `MainRegimeV2`.
- Main price roots are exactly `Bull`, `Bear`, `Sideways`, and `Crisis`.
- `Manipulation` remains separate direct-event/order-flow/order-lifecycle/social/on-chain evidence.
- `130633` is retained as provenance only, not the active denominator.
- `BullExpansion`, `BearExpansion`, `ConsolidationBalance`, and `CrisisDislocation` are not accepted as the active parent axis in this lane because they risk recreating the user-rejected child/sub-regime framing.

## Retained Evidence

- `130600` same-source `1w`/`1mo` rollup remains useful seed evidence for `MainRegimeV2`.
- `130655` derived timeframe probe remains useful partial evidence: accepted `1w:Bull` and `1w:Sideways`; rejected `1w:Bear`, `1w:Crisis`, and all `1mo` roots.
- `130102` remains the scoped cross-context audit.
- `125122` remains the daily parent-root stock-market-regimes gate.

## Guardrails

- Do not call `update_goal`.
- Do not promote child/sub-regime labels to parent roots.
- Do not treat OHLCV proxies as direct `Manipulation`.
- Full objective remains blocked until exact/direct labels or approved crosswalks close unsupported cells.

Gate result: `mainregimev2_relocked_after_taxonomy_drift_full_matrix_still_blocked`.

