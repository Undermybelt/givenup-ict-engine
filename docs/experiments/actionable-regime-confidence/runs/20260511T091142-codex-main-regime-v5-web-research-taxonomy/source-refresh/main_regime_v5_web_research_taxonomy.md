# Main Regime V5 Web Research Taxonomy Reset

Date: 2026-05-11

Purpose: reopen Board A's main-class regime taxonomy after the user correction that `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation` are not merely child regimes. This artifact is a source-refresh and taxonomy reset only. It does not claim a 95%-99% calibrated gate.

## External Sources Checked

| Source | Type | Relevant Takeaway | Board A Use |
|---|---|---|---|
| Pagan and Sossounov, "A Simple Framework for Analysing Bull and Bear Markets" | paper | Bull/bear regimes are first-class cycle states, not only post-hoc child labels. | Split directional roots into signed expansion classes instead of a coarse `Bull`/`Bear` parent with `Expansion` treated as a child-only modifier. |
| Hamilton 1989 and Ang/Bekaert 2002 | papers | Persistent Markov-switching states and transition probabilities are valid regime primitives, but state IDs must be economically relabeled. | Use HMM/Markov posterior features as evidence, not as accepted labels by themselves. |
| `hmmlearn` | GitHub | Practical HMM implementation reference. | Implementation reference for state persistence/posterior features. |
| `ruptures` | GitHub | Change-point detection library for structural breaks. | Boundary evidence for transitions and consolidation/expansion segment starts; not a class label by itself. |
| Directional-change regime work | paper | Event-based market sampling can expose transition/overshoot behavior hidden by clock bars. | Candidate features for expansion, consolidation, and transition roots. |
| `jump-models` | GitHub/paper implementation | Jump-model family explicitly targets interpretable regime identification with temporal regularization. | Candidate methodology for stable, non-HMM regime posterior features. |
| Crypto pump-and-dump / spoofing / order-book manipulation papers and datasets | papers/GitHub/data provenance | Manipulation is an event/order-flow/order-lifecycle phenomenon, not a price-root subtype. | Keep `Manipulation` as a main class or main overlay requiring direct positive/negative labels; reject OHLCV proxy acceptance. |

## Corrected Candidate Main Classes

The active candidate root taxonomy for the next Board A calibration run is `MainRegimeV5`:

| Candidate Main Class | Why It Is Main-Class | Existing Evidence Reuse | Acceptance Requirement |
|---|---|---|---|
| `BullExpansion` | Signed positive directional expansion has distinct allowed actions, sizing, and failure modes. | Existing unsigned `TrendExpansion` can only become child evidence until split by sign and rerun. | Source-backed or chronologically calibrated positive expansion labels across markets/timeframes. |
| `BearExpansion` | Signed negative directional expansion is not interchangeable with bullish expansion or generic stress. | Existing unsigned `TrendExpansion` and some crisis/stress features are evidence only. | Separate downside persistence/acceleration labels and short/hedge/abstain semantics. |
| `ConsolidationRange` | Range/compression/sideways behavior is a primary action state, not merely "absence of trend." | Existing `RangeConsolidation` packet remains useful provenance. | Range persistence, compression, false-break/mean-reversion feasibility, and cross-context calibration. |
| `CrisisStress` | Crash/liquidity cliff/volatility dislocation differs from ordinary bear expansion. | Existing `ExtremeStress` and prior partial `Crisis` evidence are provenance. | Tail/loss/liquidity-cliff labels with enough support and chronological validation. |
| `ManipulationLiquidityEngineering` | Spoofing, layering, wash trading, pump/dump, quote stuffing, stop-run/liquidity raid, and similar behavior changes execution trust regardless of trend direction. | `ThinLiquidity` and session/liquidity packets are risk context only, not proof. | Direct timestamped positive/negative labels from event, order-flow, L2/L3/MBO, order-lifecycle, wash-trade, or social/event sources. |
| `TransitionAccumulationDistribution` | Accumulation/distribution/reversal/boundary phases can be stable enough to gate trading differently from expansion or consolidation. | Existing `ReversalBrewing` can be child evidence. | Transition hazard, break recency, directional-change event rate, duration viability, and post-boundary validation. |
| `CrossAssetMacroRotation` | Risk-on/risk-off, policy/liquidity cycle, and cross-asset rotation can dominate single-instrument behavior. | Macro/breadth/sector probes are provenance only. | Must prove separability and downstream action difference before becoming mandatory; otherwise remains optional overlay. |
| `UnknownOrMixed` | Residual state for overlapping or insufficient evidence. | N/A | Fail closed; no trade-usable claim. |

## Accounting Impact

- The older `MainRegimeV2` denominator (`Bull`, `Bear`, `Sideways`, `Crisis` plus separate `Manipulation`) is now frozen as superseded accounting until a V5 schema/crosswalk is materialized.
- The prior `564` missing/rejected V2 parent-root slots remain evidence that the previous goal was not complete, but they are not the final V5 denominator.
- No existing subtype packet is promoted automatically. `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, and `ThinLiquidity` remain provenance/child evidence until the new root-specific calibration passes.
- `ManipulationLiquidityEngineering` can be a main class or a main overlay, but it cannot be filled from OHLCV proxy logic.
- Accepted gate remains `none`: this run changed taxonomy only and added `0` calibrated roots.

## Source URLs

- https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html
- https://doi.org/10.2307/1912559
- https://doi.org/10.1093/rfs/15.4.1137
- https://github.com/hmmlearn/hmmlearn
- https://github.com/deepcharles/ruptures
- https://arxiv.org/abs/2309.15383
- https://github.com/Yizhan-Oliver-Shu/jump-models
- https://arxiv.org/abs/1811.10109
- https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset
- https://arxiv.org/abs/2508.17086

## Next Action

Materialize a `MainRegimeV5` schema/crosswalk and rerun unchanged 95%-99% chronological calibration across full market/timeframe coverage for `BullExpansion`, `BearExpansion`, `ConsolidationRange`, `CrisisStress`, `ManipulationLiquidityEngineering`, and `TransitionAccumulationDistribution`, with `CrossAssetMacroRotation` as optional overlay until separability is proven.
