# User-Reopened MainRegimeV5 After V2 Reassertion

Date: 2026-05-11

Purpose: resolve the immediate taxonomy conflict created after `20260511T091507+0800-codex-mainregimev2-reassert-after-v5-drift`.

## Decision

The user explicitly reopened the taxonomy in the current instruction: `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation` are main categories, not just child regimes, and the agent should search papers/GitHub to enrich the taxonomy. Therefore the `091507` V2 reassertion is retained as conflict/provenance only and does not control the current cursor.

## Active Candidate Taxonomy

The current Board A candidate taxonomy remains `MainRegimeV5`:

- `BullExpansion`
- `BearExpansion`
- `ConsolidationRange`
- `CrisisStress`
- `ManipulationLiquidityEngineering`
- `TransitionAccumulationDistribution`
- optional overlay/watchlist: `CrossAssetMacroRotation`
- residual: `UnknownOrMixed`

## Acceptance Accounting

- Accepted 95 roots added by this writeback: `0`.
- Accepted gate: `none_for_MainRegimeV5_taxonomy_reset_no_calibration`.
- The prior `MainRegimeV2` missing-slot audit and `091507` reassertion remain evidence that old accounting was not complete, but they do not override the user's explicit V5 reopening.
- Existing V2/V3/V4 and subtype packets remain provenance until crosswalked and rerun through unchanged 95%-99% gates.
- `ManipulationLiquidityEngineering` still requires direct event/order-flow/order-lifecycle/L2/L3/MBO positive and negative rows; OHLCV proxy labels remain fail-closed.

## Next Action

Materialize the `MainRegimeV5` schema/crosswalk and rerun unchanged 95%-99% chronological calibration across full market/timeframe coverage.
