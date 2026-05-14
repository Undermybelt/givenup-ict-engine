# MainRegimeV2 Parent-Child Crosswalk

Run id: `20260511T020421+0800-codex-main-regime-v2-parent-child-crosswalk`

This artifact locks the Board A reporting boundary. The only emittable root targets are `Bull`, `Bear`, `Sideways`, `Crisis`, and direct-input-gated `Manipulation`; `UnknownOrMixed` is residual only.

Child, subtype, overlay, and signature packets can be features, guardrails, or provenance. They cannot be reported as root acceptance unless a calibrated packet emits the parent root itself.

Current mapping:

| Root target | Child / feature evidence allowed | Cannot count directly as root |
|---|---|---|
| `Bull` | `TrendExpansion`, `BullExpansion`, signed positive persistence/provider-agreement evidence | `TrendExpansion`, `BullExpansion` |
| `Bear` | `TrendExpansion`, `BearExpansion`, signed negative persistence/provider-agreement evidence | `TrendExpansion`, `BearExpansion`, `ExtremeStress`, `CrisisStress` |
| `Sideways` | `RangeConsolidation`, `Consolidation`, range/chop/compression features | `RangeConsolidation`, `Consolidation` |
| `Crisis` | `ExtremeStress`, `CrisisStress`, tail-volatility/liquidity-cliff evidence | `ExtremeStress`, `CrisisStress` |
| `Manipulation` | event-confirmed pump/dump labels, direct L2/L3/MBO/order-lifecycle fields, direct L2 signatures only when paired with labels | `ThinLiquidity`, `SessionLiquidityCoreViable`, unlabeled direct L2 signatures |
| `UnknownOrMixed` | residual only | `UnknownOrMixed` cannot be a release/trade regime |

Current gate state remains blocked. Accepted 95 root: `Crisis` only. Missing 95 roots: `Bull`, `Bear`, `Sideways`, and `Manipulation`. Runtime code changed: false. Thresholds relaxed: false. Fresh calibration rerun: false. Trade usable: false.

Next action: use a credentialed historical Tardis/Binance export for the nine exact-date available pump events, or provide another labeled direct L2/L3/order-lifecycle manipulation dataset before rerunning unchanged gates.
