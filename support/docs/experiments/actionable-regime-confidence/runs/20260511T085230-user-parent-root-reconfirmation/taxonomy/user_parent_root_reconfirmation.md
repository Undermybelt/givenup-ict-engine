# User Parent-Root Reconfirmation

Run ID: `20260511T085230+0800-user-parent-root-reconfirmation`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Result

- User correction accepted: the surfaced labels read like subtypes under main regimes, not main-class regimes themselves.
- Active root taxonomy remains `MainRegimeV2`.
- Main price roots are exactly `Bull`, `Bear`, `Sideways`, and `Crisis`.
- `UnknownOrMixed` is residual only.
- `Manipulation` is a separate direct-event/order-flow/order-lifecycle overlay, not an OHLCV price root.
- `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, `CrisisCrash`, `TrendExpansion`, `ReversalBrewing`, `SessionLiquidityCoreViable`, `ThinLiquidity`, and event-shape signatures are child/provenance evidence only.
- Board A root emission is parent-first: emit the source-backed parent root first, then attach child subtype/evidence fields underneath it.

## Gate

- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Current blocker: `564` parent-root source-label slots remain missing/rejected, and direct `Manipulation` coverage is incomplete.
- Gate result: `parent_root_reconfirmed_no_subtype_promotion`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
