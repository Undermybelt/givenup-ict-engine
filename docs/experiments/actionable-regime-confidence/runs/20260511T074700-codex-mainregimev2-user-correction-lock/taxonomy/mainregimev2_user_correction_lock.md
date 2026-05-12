# MainRegimeV2 User-Correction Lock

Run id: `20260511T074700+0800-codex-mainregimev2-user-correction-lock`

## Decision

The latest user correction states that labels such as `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisStress`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity` look like subtypes under a main-class regime rather than main-class regimes themselves.

The controlling taxonomy is restored to `MainRegimeV2`:

- Main price roots: `Bull`, `Bear`, `Sideways`, `Crisis`
- Separate direct-event class / overlay: `Manipulation`
- Residual: `UnknownOrMixed`

The `20260511T074600+0800-codex-mainregimev3-user-correction-lock` writeback is superseded drift because it promoted subtype-like labels into the root layer.

## Accounting

- Goal achieved: `false`
- Gate result: `mainregimev2_user_correction_locked_full_universe_still_blocked`
- Runtime code changed: false
- Thresholds relaxed: false
- Trade usable: false

## Next Action

Attach or acquire an independent MainRegimeV2 four-root label panel for ready yfinance/Kraken/local cells. Keep HF/HMM/OHLCV candidates sidecar-only until that panel exists.
