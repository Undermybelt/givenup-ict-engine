# Main Regime V6 Web Research Taxonomy Refresh

Date: 2026-05-11

Purpose: respond to the latest user correction that the previous labels were still too child-like, and refresh Board A's parent regime taxonomy using external papers and GitHub repositories. This is a taxonomy/source-refresh artifact only. It does not claim a 95%-99% calibrated gate.

## External Sources Checked

| Source | Type | Relevant Takeaway | Board A Use |
|---|---|---|---|
| Pagan and Sossounov, "A Simple Framework for Analysing Bull and Bear Markets" | paper | Bull and bear markets are cycle-level regimes, not just labels under a generic trend bucket. | Keep signed directional expansion as parent-action candidates, not as a generic `TrendExpansion` child only. |
| Hamilton 1989 and Ang/Bekaert 2002 | papers | Persistent switching states and transition probabilities are valid regime primitives, but state IDs need economic relabeling. | HMM/Markov posterior features are evidence/probability inputs, not labels accepted by themselves. |
| `hmmlearn` | GitHub | Practical HMM implementation reference. | Implementation reference for posterior, entropy, and persistence features. |
| Truong/Oudre/Vayatis 2020 and `ruptures` | paper/GitHub | Change-point detection identifies structural boundaries, not the economic name of the state. | Use break recency/intensity for expansion, consolidation, crisis, and transition evidence. |
| Directional-change regime work | paper | Event-time sampling and overshoot behavior can expose trend/range/transition structure missed by clock bars. | Candidate features for expansion, consolidation, and transition roots across FX/crypto/futures. |
| `jump-models` | GitHub/paper implementation | Jump-model style regimes provide interpretable, temporally regularized regime identification. | Candidate method for stable non-HMM posterior features and white-box state explanations. |
| Pump-and-dump and spoofing/order-book manipulation papers/datasets | papers/GitHub/data provenance | Manipulation is an event, social, order-flow, order-lifecycle, or microstructure phenomenon rather than an OHLCV price root. | Treat manipulation as a mandatory direct-event/order-flow class or overlay with its own evidence gate. |
| Cross-asset/risk-on-risk-off regime literature | papers | Macro/risk rotation can dominate single-instrument behavior and may cut across price roots. | Keep cross-asset rotation as an overlay/watchlist until separability and action difference are proven. |

## Source-Backed Candidate Parent Layer

The latest candidate parent taxonomy is `MainRegimeV6`. It is intentionally hierarchical: price/action roots are separated from direct manipulation and macro overlays so the downstream chain can fail closed instead of forcing weak labels.

| Candidate Class | Accounting Role | Why It Belongs Above Child Labels | Acceptance Requirement |
|---|---|---|---|
| `BullExpansion` | mandatory parent-action root | Positive signed expansion has different allowed actions, sizing, invalidation, and downstream strategy selection from generic trend. | Source-backed or chronologically calibrated positive expansion labels across instruments, timeframes, and periods. |
| `BearExpansion` | mandatory parent-action root | Negative signed expansion is not interchangeable with bullish expansion or crisis; it changes hedge/short/abstain semantics. | Separate downside persistence/acceleration labels with cross-context validation. |
| `ConsolidationRange` | mandatory parent-action root | Range/compression/sideways behavior is a primary action state, not merely "not trend". | Range persistence, compression, false-break handling, mean-reversion feasibility, and held-out validation. |
| `CrisisStress` | mandatory parent-action root | Tail stress, crash, volatility dislocation, and liquidity cliff behavior differ from ordinary bear expansion. | Tail/loss/liquidity-cliff labels with enough support and chronological validation. |
| `TransitionAccumulationDistribution` | mandatory transition root | Accumulation/distribution/reversal-boundary states can require different gating from expansion or range. | Transition hazard, break recency, directional-change rate, duration viability, and post-boundary validation. |
| `ManipulationLiquidityEngineering` | mandatory direct-event/order-flow class or overlay | Spoofing, layering, wash trading, quote stuffing, pump/dump, stop-run, and liquidity raids change execution trust regardless of trend direction. | Direct timestamped positive/negative rows from event, order-flow, L2/L3/MBO, order-lifecycle, wash-trade, social/event, or comparable sources. |
| `CrossAssetMacroRotation` | optional overlay until proven mandatory | Risk-on/risk-off and macro liquidity rotation may dominate single-instrument regimes but can also be context rather than a root. | Prove separability plus downstream action difference before adding it to mandatory denominator. |
| `UnknownOrMixed` | residual/abstain | Overlapping or insufficient evidence should not be forced into a false parent class. | Fail closed; no accepted_95 promotion target. |

## Accounting Impact

- `MainRegimeV6` supersedes the previous active `MainRegimeV2` lock for taxonomy discovery because the latest user correction explicitly asked to broaden the parent layer with paper/GitHub research.
- The earlier `MainRegimeV2` evidence and missing-slot audits remain valuable baseline/provenance. They are not deleted, and they still prove the old denominator was not complete.
- No existing subtype packet is promoted automatically. Existing `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `SessionLiquidityCoreViable`, `ThinLiquidity`, and raw L2 signature packets remain provenance until a V6 class-specific calibration passes.
- `ManipulationLiquidityEngineering` is main-class-important for gating, but it is not accepted from OHLCV proxies. It still needs direct event/order-flow/order-lifecycle evidence.
- Accepted gate remains `none`: this run changed taxonomy only and added `0` calibrated roots.

## Source URLs

- https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html
- https://doi.org/10.2307/1912559
- https://doi.org/10.1093/rfs/15.4.1137
- https://github.com/hmmlearn/hmmlearn
- https://doi.org/10.1016/j.sigpro.2019.107299
- https://github.com/deepcharles/ruptures
- https://doi.org/10.1109/tetci.2017.2775235
- https://arxiv.org/abs/2309.15383
- https://github.com/Yizhan-Oliver-Shu/jump-models
- https://arxiv.org/abs/1811.10109
- https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset
- https://arxiv.org/abs/2508.17086

## Next Action

Materialize a `MainRegimeV6` schema/crosswalk, then rerun unchanged 95%-99% chronological calibration across the full market/timeframe requirement for `BullExpansion`, `BearExpansion`, `ConsolidationRange`, `CrisisStress`, and `TransitionAccumulationDistribution`, plus a direct-event/order-flow gate for `ManipulationLiquidityEngineering`. Keep `CrossAssetMacroRotation` as an overlay until separability is proven.
