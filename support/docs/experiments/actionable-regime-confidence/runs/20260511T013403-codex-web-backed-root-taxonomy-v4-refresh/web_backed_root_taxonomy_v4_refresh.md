# Web-Backed RootTaxonomyV4 Refresh

Run id: `20260511T013403+0800-codex-web-backed-root-taxonomy-v4-refresh`

Purpose: correct Board A's active root axis after the latest user correction. The prior plain `Bull` / `Bear` / `Sideways` axis is too coarse: those labels are parent descriptors, while the release gate needs main regimes that separate expansion, consolidation, crisis stress, and direct manipulation.

## Sources Read

- Hamilton 1989, "A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle" (`https://doi.org/10.2307/1912559`): supports persistent hidden-state modelling and transition probabilities. Engineering use: HMM/Markov-switching posterior, persistence, entropy, and state relabeling by realized return/volatility.
- Ang and Bekaert 2002, "International Asset Allocation With Regime Shifts" (`https://doi.org/10.1093/rfs/15.4.1137`): supports cross-market regime-dependent allocation and the need to validate across contexts, not a single instrument.
- Guidolin and Timmermann 2007, "Asset Allocation Under Multivariate Regime Switching" (`https://doi.org/10.1016/j.jedc.2006.12.004`, SSRN `https://ssrn.com/abstract=1083124`): supports separate `crash`, `slow growth`, `bull`, and `recovery` states, so `CrisisStress` and `TransitionRecovery` cannot be blindly folded into ordinary bear or sideways labels.
- Chen and Tsang 2018, directional-change work (`https://doi.org/10.1109/TETCI.2017.2775235`): supports event-based trend/range transition features when clock-time bars blur expansions and consolidations.
- Truong, Oudre, and Vayatis 2020, selective review of offline change-point detection (`https://doi.org/10.1016/j.sigpro.2019.107299`) plus `ruptures` (`https://github.com/deepcharles/ruptures`): useful for segment boundary evidence. It does not label the root by itself.
- `hmmlearn` (`https://github.com/hmmlearn/hmmlearn`): implementation reference for HMM posterior/state machinery, not domain ontology.
- `hidden-regime` (`https://github.com/hidden-regime/hidden-regime`): open-source reference that explicitly uses bear/sideways/bull HMM examples and event studies for crashes, bubbles, and rotations. Use as implementation inspiration, not acceptance evidence.
- CFTC spoofing interpretation (`https://www.cftc.gov/sites/default/files/idc/groups/public/%40newsroom/documents/file/dtpinterpretiveorder_qa.pdf`) and FINRA manipulative-trading guidance (`https://www.finra.org/rules-guidance/guidance/reports/2024-finra-annual-regulatory-oversight-report/manipulative-trading`): support a direct-input gate for spoofing/layering style manipulation.
- Spoofing/order-book papers: "Spoofing the Limit Order Book: A Strategic Agent-Based Analysis" (`https://www.mdpi.com/2073-4336/12/2/46`), Montgomery "Spoofing, Market Manipulation, and the Limit-Order Book" (`https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2780579`), and Fabre/Challet 2025 "Learning the Spoofability of Limit Order Books" (`https://arxiv.org/abs/2504.15908`). Engineering consequence: manipulation requires order book/order lifecycle/Level-3 style evidence, not OHLCV proxies.
- `orderbooktools/crobat` (`https://github.com/orderbooktools/crobat`): open-source clue for the needed direct fields: limit-order insertions, cancellations, and market orders.

## Active RootTaxonomyV4

Required root classes:

| Root | Meaning | Minimum evidence family |
|---|---|---|
| `BullExpansion` | Positive signed expansion: persistent upward drift with enough continuation/breadth or directional-change expansion evidence. | OHLCV plus cross-asset/breadth/vol-context features can qualify if calibrated chronologically and cross-context. |
| `BearExpansion` | Negative signed expansion: persistent downward drift that is not merely a crisis/liquidity panic. | OHLCV plus breadth/credit/vol-context features can qualify if ordinary bearish expansion is separated from `CrisisStress`. |
| `Consolidation` | Range-bound or compressed auction state: bounded movement, low directional persistence, balanced expansion pressure, or coiling before a break. | OHLCV/directional-change/change-point features can qualify if separated from low-vol bull drift and post-crisis compression. |
| `Manipulation` | Market state or overlay where price/flow is materially distorted by spoofing, layering, wash trading, pump/dump, oracle/mempool, or event/social manipulation. | Direct tick/order-flow/L2/L3/order-lifecycle/event/social/on-chain evidence only. OHLCV/liquidity proxies stay fail-closed. |
| `CrisisStress` | Disorderly stress/crash/liquidity-fragility state that breaks normal expansion/consolidation assumptions. | Cross-market volatility, drawdown, correlation, spread/credit/flight-to-quality, and liquidity stress evidence. |

Conditional/auxiliary root classes:

| Root | Handling |
|---|---|
| `TransitionRecovery` | Root only if a downstream contract needs recovery/reversal/rotation as a first-class gate. Otherwise an overlay/provenance class. |
| `UnknownOrMixed` | Residual bucket. It is required for abstention but cannot be promoted as confidence. |

## Demotions / Non-Promotions

- Plain `Bull`, `Bear`, and `Sideways` are no longer precise release-gate root labels. They map to `BullExpansion`, `BearExpansion`, and `Consolidation` only after the signed expansion/range definition is materialized.
- `TrendExpansion` is child evidence unless sign-specific and calibrated separately for `BullExpansion` and `BearExpansion`.
- `RangeConsolidation` is child evidence for `Consolidation`, not proof of the whole root unless it passes the root gate directly.
- `ThinLiquidity`, `SessionLiquidityCoreViable`, sweeps, and volume-ratio signatures are not `Manipulation`. They may be context features only.
- `CrisisStress` should not be hidden under `BearExpansion`; the literature supports a separate crash/stress state.

## Gate Consequence

No fresh calibration was run in this slice. Runtime code changed: false. Thresholds relaxed: false.

Board A remains blocked. Carry-forward evidence can be re-audited under RootTaxonomyV4, but the only already strong source-backed root candidate is `CrisisStress`; `BullExpansion`, `BearExpansion`, `Consolidation`, and direct-input `Manipulation` remain missing. `TransitionRecovery` remains optional unless downstream contracts activate it.

## Next Action

Materialize RootTaxonomyV4 target schema/crosswalk, then rerun unchanged chronological root gates for `BullExpansion`, `BearExpansion`, `Consolidation`, and `CrisisStress`; keep `Manipulation` fail-closed until calibration-grade direct order-flow/L2/L3/order-lifecycle/event data exists.
