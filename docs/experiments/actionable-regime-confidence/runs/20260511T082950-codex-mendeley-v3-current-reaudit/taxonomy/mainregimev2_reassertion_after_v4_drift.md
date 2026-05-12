# MainRegimeV2 Reassertion After V4 Drift

Run id: `20260511T082950+0800-codex-mendeley-v3-current-reaudit`

## Result

- Active Board A taxonomy: `MainRegimeV2`.
- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`.
- Separate direct-event class / overlay: `Manipulation`.
- Superseded drift run: `20260511T082635+0800-codex-main-regime-v4-web-research-taxonomy`.
- Reason: the latest explicit user correction says `Bull` / `Bear` / `Sideways` / `Crisis` are the main axis, and `Manipulation` cannot be represented by OHLCV subtype factors.

## Accounting

- Existing accepted packets `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity` are `sub_regime_evidence_only`.
- `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisStress`, `CrisisCrash`, and raw L2 wall/cancel/layering signatures are child/provenance/input evidence only.
- `Manipulation` remains fail-closed unless the source has direct event, social/event, order-flow, order-lifecycle, wash-trade, spoofing/layering, L2/L3/MBO, or comparable positive/negative labels.
- Current accepted gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.
- Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
