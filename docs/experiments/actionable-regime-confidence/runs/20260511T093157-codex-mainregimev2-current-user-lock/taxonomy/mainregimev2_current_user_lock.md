# MainRegimeV2 Current User Lock

Run ID: `20260511T093157+0800-codex-mainregimev2-current-user-lock`

Board: `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Decision

- Active Board A taxonomy is `MainRegimeV2`.
- Main price-root axis is exactly `Bull`, `Bear`, `Sideways`, and `Crisis`; `UnknownOrMixed` remains residual only.
- `Manipulation` is separate direct-event/order-flow/order-lifecycle class or overlay evidence.
- `Manipulation` cannot be accepted from OHLCV proxy subfactors such as liquidity thinness, session-liquidity windows, sweep-like ranges, or volume-ratio filters.
- Existing six accepted packets are demoted to `sub_regime_evidence_only`: `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity`.
- The six packets may remain explanation, guardrail, routing, or subtype evidence only after the parent root is independently proven.

## Accounting

- Accepted parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Gate result: `mainregimev2_current_user_lock_no_subtype_or_ohlcv_manipulation_promotion`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Acquire or verify independent exact-underlying parent-root label panels for `Bull`, `Bear`, `Sideways`, and `Crisis`, or authenticated timestamped direct `Manipulation` positive/negative rows. Attach subtype packets only underneath a proven parent-root packet.
