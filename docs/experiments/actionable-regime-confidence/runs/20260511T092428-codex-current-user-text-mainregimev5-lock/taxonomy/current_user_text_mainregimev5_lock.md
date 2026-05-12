# Current User Text MainRegimeV5 Lock

Date: 2026-05-11

Purpose: resolve repeated concurrent writeback drift that incorrectly restored `MainRegimeV2` after the current user instruction.

## Current User Instruction

The controlling current user text says: "这些都只能算是子分类的regime，主分类应该是牛市扩张、熊市扩张、操纵和盘整，甚至还有别的大类，你应该去上网搜搜丰富你的认知，论文或者github"

This is an explicit taxonomy reopening. It names `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation` as main classes and requests paper/GitHub research for additional main classes.

## Decision

Current Board A candidate taxonomy is `MainRegimeV5`.

Mandatory next-calibration roots:
- `BullExpansion`
- `BearExpansion`
- `ConsolidationRange`
- `CrisisStress`
- `ManipulationLiquidityEngineering`
- `TransitionAccumulationDistribution`

Optional overlay/watchlist:
- `CrossAssetMacroRotation`

Residual:
- `UnknownOrMixed`

## Superseded Conflict Writebacks

The following sections are retained as provenance/conflict records only:
- `20260511T091507+0800-codex-mainregimev2-reassert-after-v5-drift`
- `20260511T092259+0800-codex-mainregimev2-lock-after-false-v5-reopen`

They do not control the current cursor because they contradict the current user text.

## Acceptance Accounting

- Accepted 95 roots added: `0`.
- Accepted gate: `none_for_MainRegimeV5_taxonomy_reset_no_calibration`.
- No thresholds were relaxed.
- No runtime code changed.
- Existing V2/V3/V4 packets remain provenance until crosswalked into V5 and rerun through unchanged 95%-99% chronological calibration.
- `ManipulationLiquidityEngineering` still requires direct event/order-flow/order-lifecycle/L2/L3/MBO positive and negative rows.

## Next Action

Materialize the `MainRegimeV5` schema/crosswalk and rerun unchanged 95%-99% chronological calibration across full market/timeframe coverage.
