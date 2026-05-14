# Parent Regime Taxonomy Pivot v3

Run ID: `20260511T130633+0800-codex-parent-regime-taxonomy-pivot-v3`

This is a direction-reset packet, not a confidence gate.

## Why This Exists

The `130600` same-source weekly/monthly rollup is useful positive seed material, but it still follows the old `MainRegimeV2` denominator. The user's latest correction says the parent layer itself is the blocker: many current labels are sub-regimes or input signatures, while the parent layer should be closer to bull expansion, bear expansion, consolidation, crisis/dislocation, and direct manipulation/integrity events.

## Candidate Parent Axis

| Parent Candidate | Use of Existing Evidence | Child/Substate Examples |
|---|---|---|
| `BullExpansion` | map existing `Bull` daily/weekly/monthly labels only after explicit crosswalk approval | low-vol bull, high-vol bull, bubble, bull correction |
| `BearExpansion` | map existing `Bear` daily/weekly/monthly labels only after explicit crosswalk approval | regular bear, bear rally, distribution, downtrend acceleration |
| `ConsolidationBalance` | map existing `Sideways` labels only when source confidence or adjudicated range labels are present | quiet sideways, choppy sideways, range compression, accumulation/distribution candidate |
| `CrisisDislocation` | map existing `Crisis` labels as tail-stress seed evidence, not manipulation evidence | crash, liquidity drought, correlation breakdown, gap/jump stress |
| `ManipulationIntegrityEvent` | map existing direct manipulation evidence only by variety/support | pump/dump, bear raid, painting tape, spoofing, layering, pinging, quote stuffing, wash/self-trade |

Watchlist only until preflight: `TransitionRotation`, `CrossAssetMacroRotation`, `PolicyLiquidityRegime`, and residual `UnknownOrMixed`.

## External Refresh

- Bull/bear literature supports parent regimes with child components such as corrections, rallies, bubbles, regular bear markets, and crash/correction states.
- Open-source regime examples and the stock-market-regimes panel support Bull/Bear/Sideways/Crisis labels as seed material.
- Manipulation literature supports a separate direct-event/order-flow/order-lifecycle/on-chain/social family rather than OHLCV-only proxies.

## Local Consequence

- Preserve `130600` as useful same-source timeframe seed data.
- Do not train the next gate until the parent taxonomy and crosswalk are locked.
- Existing child packets stay child/input evidence.
- Broad negative scans should stop as the default action.

Safety:
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.
- Goal complete: false.
