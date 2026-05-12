# MainRegimeV2 Reassertion After V5 Drift

Run ID: `20260511T091507+0800-codex-mainregimev2-reassert-after-v5-drift`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Result

- Active taxonomy is restored to `MainRegimeV2`.
- Active main price roots are `Bull`, `Bear`, `Sideways`, and `Crisis`.
- `Manipulation` remains a separate direct-event/order-flow/order-lifecycle class or overlay.
- `UnknownOrMixed` remains residual only.
- The `20260511T091142+0800` `MainRegimeV5` writeback is retained as drift/provenance only.
- `BullExpansion`, `BearExpansion`, `ConsolidationRange`, `CrisisStress`, `ManipulationLiquidityEngineering`, `TransitionAccumulationDistribution`, and `CrossAssetMacroRotation` are not active Board A roots unless the user explicitly reopens taxonomy.
- Existing subtype/signature packets remain `sub_regime_evidence_only`.
- Accepted gate remains `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `mainregimev2_reasserted_after_v5_drift_full_universe_still_blocked`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Next Action

Continue source acquisition for exact-underlying non-Kaggle MainRegimeV2 parent-root label panels and direct `Manipulation` positive/negative rows. Do not run a V5 schema/crosswalk unless the user explicitly reopens taxonomy.
