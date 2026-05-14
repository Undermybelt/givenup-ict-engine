# Main Regime Taxonomy Correction

Run id: `20260511T070241+0800-codex-main-regime-taxonomy-correction`

## Decision

- The user's correction is accepted: several labels discussed earlier are child regimes under a main regime, not main-class regimes.
- Main price-regime roots are now fixed to `Bull`, `Bear`, `Sideways`, and `Crisis`.
- `Manipulation` is moved out of the main price-regime root ledger. It remains a direct-event overlay gate for suppress/abstain/cooldown.
- `UnknownOrMixed` remains residual only.
- The expanded `all species / all cycles` objective remains open until a provider-universe and timeframe-ladder coverage matrix exists.

## Current Accounting

| Accounting Class | Labels | Status |
|---|---|---|
| Main price-regime roots | `Bull`, `Bear`, `Sideways`, `Crisis` | prior >=95 baseline evidence preserved |
| Direct-event overlay gate | `Manipulation` | accepted only as event-confirmed overlay evidence |
| Child/provenance labels | `BullExpansion`, `BearExpansion`, `RangeConsolidation`, `SidewaysConsolidation`, `CrisisStress`, `CrisisCrash`, `VolatilityDislocation`, `TrendExpansion`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, `ThinLiquidity` | not counted as roots |
| Preflight-only labels | `BubbleEuphoria`, `LiquidityDrought`, `TransitionRecovery`, `CrossAssetRotation`, `MacroPolicyRegime` | not counted as roots |
| Residual | `UnknownOrMixed` | abstain bucket only |

## Preserved Baseline Evidence

| Main Root | Accepted Packet | Test Wilson95 | Baseline Breadth |
|---|---|---:|---|
| `Bull` | `20260511T035045+0800-codex-kaggle-bull-coverage-buffer-gate` | `0.961931` | `index` + `single_stock`, `1d` + `1w` |
| `Bear` | `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate` | `0.992722` | `crypto` + `equity_etf`, `1d` + `1w` |
| `Sideways` | `20260511T041923+0800-codex-yahoo-sourcebacked-parent-root-gate` | `0.995568` | `crypto` + `equity_etf`, `1d` + `1w` |
| `Crisis` | `20260510T235220+0800-codex-broader-root-v2-probe` | `0.995981` | 7 contexts, `15m` + `1h` |

## Overlay Evidence

| Overlay | Accepted Packet | Test Wilson95 | Boundary |
|---|---|---:|---|
| `Manipulation` | `20260511T045102+0800-codex-mehrnoom-telegram-direct-manipulation-gate` | `0.999701` | overlay only; not a main price-regime root |

## Next

Build the provider-universe and timeframe-ladder coverage matrix for the four main price roots. Keep `Manipulation` in a separate overlay coverage lane.

Runtime code changed: false. Thresholds relaxed: false. Trade usable: false.
