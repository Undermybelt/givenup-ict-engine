# MainRegimeV3 Reassertion After V2 Drift

Run id: `20260511T074100+0800-codex-mainregimev3-reassert-after-v2-drift`

This corrects the board after `20260511T074000+0800-codex-mainregimev2-reassert-after-v3-drift` reasserted the old price-root-only axis. That `074000` section conflicts with the latest user correction in this turn and is now historical provenance only.

## Active Taxonomy

Active taxonomy: `MainRegimeV3`.

Active completion roots:
- `BullExpansion`
- `BearExpansion`
- `SidewaysConsolidation`
- `CrisisStress`
- `Manipulation`

Residual: `UnknownOrMixed`.

Candidate big classes to preflight before activation: `TransitionRecovery`, `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `CrossAssetRotationOrRiskOnRiskOff`, and `MacroPolicyRegime`.

## Boundary

- Old `Bull`, `Bear`, `Sideways`, and `Crisis` packets are not deleted, but they are provenance until mapped to `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, and `CrisisStress`.
- `Manipulation` is a top-level decision root, not an OHLCV child. It still requires direct event, social/event, order-flow, order-lifecycle, wash-trade, spoofing/layering, or comparable labels.
- `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, `ThinLiquidity`, HMM state ids, change-point boundaries, and raw L2 signatures are inputs/children unless a parent-root packet passes the unchanged gate.

Gate result: `blocked_mainregimev3_reasserted_after_v2_drift_acceptance_not_rerun`.

Accepted 95 roots from this reassertion: none.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.

Next action: rerun the attachability/full-coverage disposition matrix against MainRegimeV3 and keep missing source-label cells blocked.
