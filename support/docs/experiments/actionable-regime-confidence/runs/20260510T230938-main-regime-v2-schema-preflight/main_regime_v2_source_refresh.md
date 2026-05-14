# MainRegimeV2 Source Refresh

Date: 2026-05-10

Purpose: refresh the external basis for root/main market-regime classes before accepting or rejecting 95% MainRegimeV2 gates. This supplements the earlier source scan without changing thresholds.

## Source Matrix

| Source | What It Supports | Board A Implication |
|---|---|---|
| Pagan and Sossounov, *A simple framework for analysing bull and bear markets*, Journal of Applied Econometrics 2003, https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html | Bull/bear market dating is a root directional-market problem, not a generic trend subtype. | Split `TrendExpansion` into signed `BullExpansion` and `BearExpansion` root labels. |
| Hamilton, *A New Approach to the Economic Analysis of Nonstationary Time Series and the Business Cycle*, Econometrica 1989, https://doi.org/10.2307/1912559 | Hidden/Markov switching states are suitable for persistent regimes and transition probabilities. | Root classes should carry persistence, transition hazard, and posterior-style evidence rather than raw uncalibrated labels. |
| `hidden-regime`, https://github.com/hidden-regime/hidden-regime | The repo's public README presents market regimes as bull, bear, sideways, and crisis, and emphasizes temporal isolation and validation/backtesting. | This agrees with the need for root classes above the current subtype packets, plus time-ordered validation. |
| `hmmlearn`, https://github.com/hmmlearn/hmmlearn | Provides HMM algorithms for unsupervised hidden-state learning/inference. | Useful implementation reference for posterior regime probabilities, entropy, and state relabeling. |
| `ruptures`, https://github.com/deepcharles/ruptures | Offline change-point detection and segmentation of non-stationary signals. | Useful boundary evidence for `TransitionAccumulationDistribution`; a break alone is not tradability proof. |
| Wu and Han, *Intelligent trading strategy based on improved directional change and regime change detection*, arXiv:2309.15383, https://arxiv.org/abs/2309.15383 | Directional-change sampling plus HMM-style regime change detection uses event-based transitions instead of only clock bars. | Add directional-change / overshoot / boundary-recency features before accepting transition roots across timeframes. |
| Lin and Yang, *Detecting Multilevel Manipulation from Limit Order Book via Cascaded Contrastive Representation Learning*, arXiv:2508.17086, https://arxiv.org/abs/2508.17086 | LOB spoofing/manipulation evidence is multi-level order-book behavior. | `ManipulationLiquidityEngineering` cannot be accepted from OHLCV-only packets. |
| Fabre and Challet, *Learning the Spoofability of Limit Order Books With Interpretable Probabilistic Neural Networks*, arXiv:2504.15908, https://arxiv.org/abs/2504.15908 | Spoofability needs Level-3/order-flow variables, placement distance, and order-lifecycle style evidence. | Current Board A artifacts remain `missing_required_inputs` for manipulation. |
| Xu and Livshits, *The Anatomy of a Cryptocurrency Pump-and-Dump Scheme*, arXiv:1811.10109, https://arxiv.org/abs/1811.10109 | Crypto manipulation can be event/social-channel driven, not visible from OHLCV alone. | Crypto manipulation lane may use event/social evidence, but absent those inputs it must fail closed. |

## Taxonomy Consequence

MainRegimeV2 root labels used by this run:

- `BullExpansion`
- `BearExpansion`
- `ConsolidationRange`
- `ManipulationLiquidityEngineering`
- `CrisisStress`
- `TransitionAccumulationDistribution`
- `UnknownOrMixed`

The current six subtype/signature packets remain useful context, but they do not close MainRegimeV2 unless promoted by a root-class target, accepted gate, and residual bucket.
