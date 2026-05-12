# MainRegimeV3 Crosswalk Contract

Run id: `20260511T073820+0800-codex-mainregimev3-crosswalk-contract`

This materializes the active Board A taxonomy after the latest user correction and paper/GitHub refresh. It does not accept any new 95% root by itself.

## Active Roots

| MainRegimeV3 root | Old V2 alias/provenance | Current state | Evidence channel | Hard blocker |
|---|---|---|---|---|
| `BullExpansion` | `Bull` | blocked_remap_required | bar/panel state with positive-drift expansion behavior | old `Bull` evidence cannot count until expansion semantics and source labels are attached |
| `BearExpansion` | `Bear` | blocked_remap_required | bar/panel state with downside risk-off expansion behavior | old `Bear` evidence cannot count until downside-expansion semantics and source labels are attached |
| `SidewaysConsolidation` | `Sideways`, `Consolidation`, `Range` | blocked_remap_required | range/compression state that changes strategy selection | child `RangeConsolidation` or low-vol proxies cannot count by wording |
| `CrisisStress` | `Crisis`, `CrisisCrash`, `VolatilityDislocation` | blocked_remap_required | stress/drawdown/volatility/correlation/liquidity state | old `Crisis` evidence must be re-audited as stress/dislocation coverage |
| `Manipulation` | `Manipulation` | blocked_full_coverage_remap_required | direct event/social/order-flow/order-lifecycle/wash/spoof labels | OHLCV proxies fail closed; one direct event variety is not full coverage |
| `UnknownOrMixed` | residual | residual_only | abstain/default guardrail | not a completion root |

## Candidate Big Classes

These may become roots only after schema preflight and separate calibration: `TransitionRecovery`, `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `CrossAssetRotationOrRiskOnRiskOff`, `MacroPolicyRegime`.

## Child/Input-Only Evidence

`TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, `ThinLiquidity`, raw L2 wall/cancel/layering signatures, HMM state ids, and change-point boundaries can support a root, but cannot complete a root by wording alone.

## Acceptance Contract

- Each active root needs its own chronological calibration/test split and Wilson95 >= 0.95.
- Cross-market and cross-timeframe disposition remains required.
- Independent/source-backed labels are required for accepted confidence.
- OHLCV-derived proxy labels cannot be promoted into accepted source labels.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

Gate result: `blocked_mainregimev3_crosswalk_materialized_acceptance_not_rerun`.

Next action: rerun the attachability/full-coverage disposition matrix against the MainRegimeV3 roots and keep missing source-label cells blocked.
