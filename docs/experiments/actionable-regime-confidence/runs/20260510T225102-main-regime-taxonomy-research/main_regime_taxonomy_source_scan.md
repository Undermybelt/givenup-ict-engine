# Main Regime Taxonomy Source Scan

Date: 2026-05-10

Purpose: correct Board A's regime ontology. The previous accepted packets are useful sub-regime/confidence packets, but they are not the root market-regime taxonomy.

## Source-Backed Correction

The root taxonomy should separate directional expansion, range behavior, stress/crisis, transition, and manipulation/liquidity-engineering behavior.

| Main Regime | Why It Is A Main Class | Evidence / Starting Sources | ict-engine Implication |
|---|---|---|---|
| `BullExpansion` | Persistent positive-direction expansion is a primary market state, not just generic `TrendExpansion`. | Bull/bear dating literature such as Pagan and Sossounov's bull/bear framework; Markov-switching/HMM regime work such as Hamilton; HMM tooling such as `hmmlearn`. | Split current `TrendExpansion` into signed expansion labels. Require positive drift/slope/breadth/persistence evidence and a separate payoff gate. |
| `BearExpansion` | Persistent negative-direction expansion has different risk, sizing, and execution rules from bull expansion. | Same bull/bear and Markov-switching sources; bear states need their own persistence, drawdown, and downside acceleration labels. | Do not collapse bull and bear into one `TrendExpansion`. Require bearish slope/return path, downside volatility, and short/hedge allowed-action semantics. |
| `ConsolidationRange` | Sideways/range regimes are a separate root state, not just low-stress transition evidence. | Bull/bear/sideways taxonomies in regime-detection repos and classical range/turning-point research; change-point tooling such as `ruptures` for boundaries. | Current `RangeConsolidation` packet can become a sub-class, but root class needs range persistence, compression, false-break, and mean-reversion feasibility labels. |
| `ManipulationLiquidityEngineering` | Spoofing, pump-dump, stop-run, quote/layering, and liquidity-raid behavior is neither bull nor bear expansion; it changes execution trust. | ArXiv market manipulation/order-book work: `1109.2631`, `1204.2736`, `2508.17086`, `2504.15908`; crypto pump-dump papers: `1811.10109`, `2005.06610`, `2105.00733`, `2309.06608`. | Treat as a root class or root overlay. Fail closed unless tick/order-flow/L2/order-lifecycle or crypto social/event inputs exist. OHLCV proxy only is `proxy_only_low_confidence`. |
| `CrisisStress` | Crash, liquidity cliff, volatility explosion, and stress regimes are not the same as ordinary bear expansion. | HMM/Markov switching, volatility-specialist routing, order-flow stress papers, and existing `ExtremeStress` evidence. | Current `ExtremeStress` is a sub-regime packet. Root class needs gap/tail/loss/liquidity-cliff labels and sizing/abstain action. |
| `TransitionAccumulationDistribution` | Boundary phases, accumulation/distribution, reversal brewing, and state transitions are distinct from stable regimes. | Directional-change/regime-change work including arXiv `2309.15383`; change-point detection survey/tooling including `ruptures`; HMM transition probability/persistence. | Current `ReversalBrewing` is a sub-regime. Root class needs transition hazard, boundary recency, directional-change event rate, and duration viability. |

## Source URLs

- Pagan and Sossounov, *A Simple Framework for Analysing Bull and Bear Markets*: https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html
- Hamilton regime-switching foundation: https://doi.org/10.2307/1912559
- `hmmlearn` HMM implementation: https://github.com/hmmlearn/hmmlearn
- `ruptures` change-point detection: https://github.com/deepcharles/ruptures
- Directional-change regime strategy: https://arxiv.org/abs/2309.15383
- Optimal execution and manipulation in order books: https://arxiv.org/abs/1109.2631 and https://arxiv.org/abs/1204.2736
- LOB manipulation / spoofability: https://arxiv.org/abs/2508.17086 and https://arxiv.org/abs/2504.15908
- Crypto pump-dump detection and impact: https://arxiv.org/abs/1811.10109, https://arxiv.org/abs/2005.06610, https://arxiv.org/abs/2105.00733, https://arxiv.org/abs/2309.06608
- Hidden-regime implementation reference: https://github.com/hidden-regime/hidden-regime

## Required Board A Reset

1. Preserve the six accepted 95% packets as `sub_regime_packets`.
2. Add `MainRegimeV2` as the root taxonomy.
3. Do not claim root-regime 6/6 completion from sub-regime packets.
4. Add new acceptance requirements:
   - each main regime has explicit qualifying condition;
   - bull and bear expansion are signed, not one generic trend;
   - manipulation requires L2/tick/order-lifecycle or crypto social/event evidence;
   - each root class must pass chronological calibration/test, cross-instrument validation, and cross-market-context validation;
   - Board B still controls profitability/trade-usable promotion.

## Current Sub-Regime Crosswalk

| Existing Accepted Packet | New Role |
|---|---|
| `TrendExpansion` | sub-regime evidence for future `BullExpansion` or `BearExpansion`; must be split by sign and allowed action |
| `RangeConsolidation` | sub-regime evidence under `ConsolidationRange` |
| `ExtremeStress` | sub-regime evidence under `CrisisStress` |
| `ReversalBrewing` | sub-regime evidence under `TransitionAccumulationDistribution` |
| `SessionLiquidityCoreViable` | liquidity/readiness context, not a root market regime |
| `ThinLiquidity` | liquidity guardrail / possible manipulation-risk context, not manipulation proof |
