# ActionableRegimeRootV7 Schema Crosswalk

Run ID: `20260511T102326+0800-codex-actionableregimerootv7-schema-crosswalk`

## Result

- Active candidate taxonomy: `ActionableRegimeRootV7`.
- Mandatory roots: `BullExpansion`, `BearExpansion`, `ConsolidationBalance`, `CrisisDislocation`, `ManipulationIntegrityEvent`.
- Watchlist root: `TransitionRotation`.
- Residual bucket: `UnknownOrMixed`.
- Accepted 95 roots added: `0`.
- Accepted direct manipulation rows added: `0`.

## Boundary

Old `MainRegimeV2` labels and V5/V6 labels are compatibility/provenance only. They can seed candidates, but they cannot complete V7 roots by wording alone.

`ManipulationIntegrityEvent` remains a top-level market-integrity class. It requires real direct timestamped positive and negative rows. OHLCV/session/liquidity proxies, synthetic rows, unlabeled order-book samples, and document indexes remain fail-closed.

## Gate

`blocked_actionableregimerootv7_schema_crosswalk_materialized_no_calibration`

Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.
