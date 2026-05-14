# Source-Backed Root Ontology Reset

Date: 2026-05-11

Purpose: respond to the user correction that the current accepted packets are only sub-regime/signature evidence, and that the main taxonomy should start from larger market states such as bull expansion, bear expansion, manipulation, and consolidation.

## Sources Checked

Papers and source pages:
- Pagan and Sossounov, 2003, "A Simple Framework for Analysing Bull and Bear Markets", Journal of Applied Econometrics, DOI `10.1002/jae.664` (`https://doi.org/10.1002/jae.664`): bull/bear markets are treated as the primary market-cycle partition.
- Lunde and Timmermann, 2004, "Duration Dependence in Stock Prices: An Analysis of Bull and Bear Markets", DOI `10.1198/073500104000000136` (`https://doi.org/10.1198/073500104000000136`): bull/bear states are modeled with state duration and hazard dynamics.
- Werge, 2021, arXiv `2107.05535` (`https://arxiv.org/abs/2107.05535`): asset-independent HMM regime model reports bull, bear, and high-volatility periods across commodities, currencies, equities, and fixed income.
- Shu, Yu, and Mulvey, 2024, arXiv `2402.05272` (`https://arxiv.org/abs/2402.05272`): statistical jump model emphasizes persistent regime switching, downside-risk regimes, transaction costs, and trading delays.
- Shu and Mulvey, 2024, arXiv `2410.14841` (`https://arxiv.org/abs/2410.14841`): dynamic factor allocation uses sparse jump models to identify bull and bear market regimes for factors.
- Li, Polukarova, and Ventre, 2023, arXiv `2308.08683` (`https://arxiv.org/abs/2308.08683`): manipulation detection is based on order-book dynamics and identifies spoofing/layering, including LUNA flash-crash behavior.
- Fabre and Challet, 2025, arXiv `2504.15908` (`https://arxiv.org/abs/2504.15908`): spoofability detection uses Level-3 order data, order-flow variables, Hawkes-style placement/size features, and posting distance from best prices.
- Qin et al., 2025, arXiv `2508.17086` (`https://arxiv.org/abs/2508.17086`): multilevel limit-order-book manipulation detection treats spoofing as a hierarchical LOB anomaly, not as an OHLCV proxy.

GitHub/source implementations:
- `hidden-regime/hidden-regime` (`https://github.com/hidden-regime/hidden-regime`): HMM finance package with market-regime concepts for bull, bear, sideways, and crisis states plus event studies.
- `hmmlearn/hmmlearn` (`https://github.com/hmmlearn/hmmlearn`): generic HMM implementation; useful for posterior state probabilities, but not a taxonomy by itself.
- `Yizhan-Oliver-Shu/jump-models` (`https://github.com/Yizhan-Oliver-Shu/jump-models`): statistical jump model implementation with scikit-learn-style APIs, sparse jump model, online prediction, and finance examples.
- `deepcharles/ruptures` (`https://github.com/deepcharles/ruptures`): change-point detection library; useful for boundary timing and transition evidence, not root labels by itself.
- `abides-sim/abides` (`https://github.com/abides-sim/abides`): market microstructure simulation using message-based exchange/agent interactions modeled after ITCH/OUCH-style protocols; useful for manipulation/order-lifecycle probes.

## Reset Decision

The current plain `Bull` / `Bear` / `Sideways` / `Crisis` axis is too coarse and also conflicts with the user's correction. The next MainRegimeV2 root schema should be rebuilt around source-backed large states:

| Root / Main Class | Chinese Label | Why It Belongs At Root Level | Evidence Needed Before 95% Acceptance |
|---|---|---|---|
| `BullExpansion` | 牛市扩张 | Bull market literature treats sustained positive market-cycle phases as primary states; expansion adds execution relevance beyond generic positive drift. | signed positive forward return, breadth/participation, persistence, volatility not in crisis, cross-context support |
| `BearExpansion` | 熊市扩张 | Bear market literature treats sustained negative market-cycle phases as primary states; expansion separates ordinary downside trend from crash stress. | signed negative forward return, downside breadth, persistence, non-crisis separation, cross-context support |
| `Consolidation` | 盘整 | Sideways/range/chop is a distinct root execution environment, but the current `RangeConsolidation` packet is only one narrow child rule. | low signed drift, bounded range, mean-reversion/chop evidence, enough horizon duration, cross-timeframe support |
| `CrisisStress` | 危机/压力 | HMM/jump-model and open-source regime packages commonly separate high-volatility/crisis periods from ordinary bear states. | extreme range/vol/correlation/liquidity stress, broad validation, tail-risk semantics |
| `Manipulation` | 操纵 | Manipulation is not a price-bar shape; recent papers require LOB/order-flow/order-lifecycle features for spoofing/layering. | tick/order-flow/L2/Level-3/order-lifecycle, posting distance, cancel/replace behavior, venue/event evidence |
| `TransitionRecovery` | 转换/修复 | Literature and prior probes show recovery/transition/accumulation-distribution may be a large class, but it can also be residual boundary handling. | change-point recency, posterior entropy, reversal/accumulation evidence, duration and hazard controls |
| `UnknownOrMixed` | 未知/混合 | Required residual bucket for MECE coverage; never a release gate. | explicit not-covered routing and abstain behavior |

## Consequences For Existing Evidence

- `SessionLiquidityCoreViable`, `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, and `ThinLiquidity` remain sub-regime/signature packets.
- The old `Bull` root probes are now provenance for `BullExpansion`, but they did not pass 95%.
- The old `Bear` root probes are now provenance for `BearExpansion`, but they did not pass 95%.
- The old `Sideways` root probes are now provenance for `Consolidation`, but they did not pass 95%.
- The accepted old `Crisis` root packet can be carried as partial evidence for `CrisisStress` only. It does not close the whole root ontology.
- `Manipulation` remains `missing_required_inputs`; OHLCV thin-liquidity/session/sweep-like patterns are context only.

## Required Next Run

Rebuild the target schema and crosswalk under the new root labels:

```text
BullExpansion
BearExpansion
Consolidation
CrisisStress
Manipulation
TransitionRecovery
UnknownOrMixed
```

The unchanged gates still apply:
- no `future_*` / `target_*` predictor leakage;
- chronological train/calibration/test split;
- Wilson LCB 95 >= 0.95;
- support/ECE/coverage/context/timeframe gates unchanged;
- no OHLCV proxy acceptance for `Manipulation`.

This source scan changes the taxonomy contract only. It does not add a new accepted 95% root packet.
