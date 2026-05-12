# MainRegimeV2 Lock After V6 Drift

Run ID: `20260511T095043+0800-codex-mainregimev2-lock-after-v6-drift`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Decision

- Active Board A taxonomy is restored to `MainRegimeV2`.
- Main price roots are exactly `Bull`, `Bear`, `Sideways`, and `Crisis`; `UnknownOrMixed` remains residual only.
- `Manipulation` remains a separate direct-event/order-flow/order-lifecycle class or overlay.
- The `20260511T094817+0800` `MainRegimeV6` writeback is superseded drift/provenance only.
- `BullExpansion`, `BearExpansion`, `ConsolidationRange`, `CrisisStress`, `TransitionAccumulationDistribution`, `ManipulationLiquidityEngineering`, `CrossAssetMacroRotation`, and the six older subtype packets remain child/provenance or direct-event overlay evidence only.

## Accounting

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `mainregimev2_locked_after_v6_drift_no_new_95`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Continue source acquisition against the v3 request CSV for exact-underlying MainRegimeV2 parent-root labels or authenticated direct `Manipulation` positive/negative rows.
