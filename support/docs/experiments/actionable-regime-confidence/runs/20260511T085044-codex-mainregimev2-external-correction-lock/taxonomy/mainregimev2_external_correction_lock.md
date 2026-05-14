# MainRegimeV2 External Correction Lock

Run ID: `20260511T085044+0800-codex-mainregimev2-external-correction-lock`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Result

- Active taxonomy is `MainRegimeV2`.
- Main price roots are exactly `Bull`, `Bear`, `Sideways`, and `Crisis`.
- `UnknownOrMixed` is residual only.
- `Manipulation` is a separate direct-event/order-lifecycle class or overlay, not an OHLCV price root.
- `Manipulation` cannot be accepted from `ThinLiquidity`, `SessionLiquidityCoreViable`, sweep-like ranges, volume-ratio filters, or other OHLCV proxy subfactors.
- Existing six subtype/signature packets are demoted to `sub_regime_evidence_only`: `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity`.
- Those six packets may remain explanation, routing, predictor, or guardrail evidence after the parent root is independently identified, but they cannot complete `Bull`, `Bear`, `Sideways`, `Crisis`, or `Manipulation`.
- `MainRegimeV3` and `MainRegimeV4` sections remain provenance only unless the user explicitly reopens taxonomy.

## Gate

- Accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Current blocker: `564` MainRegimeV2 price-root label slots remain missing/rejected, and direct `Manipulation` coverage is incomplete.
- Gate result: `board_a_repointed_to_mainregimev2_external_correction_subregime_packets_demoted_full_universe_blocked`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
