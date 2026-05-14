# Research-Backed Root Taxonomy Reset

Run id: `20260511T043824+0800-codex-research-backed-root-taxonomy-reset`

Purpose: respond to the latest user correction that prior labels were mostly sub-regimes, and that the main axis should start from `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation`, with room for other large classes.

This is a source-refresh and board-contract reset only. It does not lower the 95% gate, does not claim a tradable strategy, and does not add fresh runtime code.

## Source Readback

| Source | Useful Signal | Board A Decision |
|---|---|---|
| Zakamulin, `Not all bull and bear markets are alike`, `https://doi.org/10.1057/s41283-022-00112-y` | Bull and bear markets can be decomposed into child states such as low-volatility bull, high-volatility bull, bubble, regular bear, crash, and correction. | Supports `BullExpansion` and `BearExpansion` as main roots, with low-vol/high-vol/bubble/correction/crash as child labels unless separately promoted. |
| Oelschlager and Adam, hierarchical HMM, `https://arxiv.org/abs/2007.14874` | Hierarchical hidden-state modeling separates long-term bull/bear regimes from shorter sub-states. | Supports a root/sub-root hierarchy instead of flattening every HMM state into a main class. |
| Hamilton regime switching, `https://doi.org/10.2307/1912559`; Ang and Bekaert regime switching, `https://doi.org/10.1093/rfs/15.4.1137`; `hmmlearn`, `https://github.com/hmmlearn/hmmlearn` | Hidden Markov / regime-switching priors are useful for persistent root probabilities. | Use posterior, entropy, persistence, and relabeled realized behavior as evidence fields, not as root names by themselves. |
| Truong, Oudre, and Vayatis change-point review, `https://doi.org/10.1016/j.sigpro.2019.107299`; `ruptures`, `https://github.com/deepcharles/ruptures` | Change-point tools identify boundary timing and structural breaks. | Boundary/break evidence can support `TransitionRecovery`, `CrisisStress`, or root switches, but a break alone is not a main root. |
| Chen and Tsang directional-change features, `https://doi.org/10.3390/a11120202` | Event-time features reduce clock-time blur in transitions. | Directional-change event rate and overshoot are root evidence features for expansion/consolidation/dislocation, not root labels. |
| Hidden Regime GitHub, `https://github.com/hidden-regime/hidden-regime` | Public implementation prior includes broad `Bull`, `Bear`, `Sideways`, and `Crisis` style reporting. | Confirms that broad roots are the right layer; Board A uses clearer action names `BullExpansion`, `BearExpansion`, `Consolidation`, and `CrisisStress/VolatilityDislocation`. |
| Siering, Clapham, Engel, and Gomber manipulation taxonomy, `https://doi.org/10.1057/s41265-016-0029-z`; Do and Putnins spoofing/layering, `https://ssrn.com/abstract=4525036`; Fabre and Challet order-level manipulation, `https://arxiv.org/abs/2504.15908` | Manipulation detection depends on manipulation type and direct order/event evidence such as imbalance, cancellations, order activity, and order-level lifecycle. | `Manipulation` is a main root-or-overlay gated by direct evidence. OHLCV/session/liquidity proxies remain subordinate and fail closed. |
| SystemsLab/Sapienza pump-and-dump dataset, `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`; Bayi-Hu pump-and-dump repo, `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency` | Public event/social/market-feature sources can supply direct pump/dump positives and controls. | They are candidate direct sources for `Manipulation`; prior Board A gates remain below 95 and do not pass. |

## Active Layer Decision

| Layer | Labels | Decision |
|---|---|---|
| Active main roots | `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress/VolatilityDislocation` | Require per-root calibrated packets. Existing accepted `Bull`, `Bear`, `Sideways`, and `Crisis` packets can be read as source-backed evidence for these roots where the target semantics match, but this reset itself does not rerun calibration. |
| Direct-input-gated main root or overlay | `Manipulation` | Still missing. Needs event/order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives. |
| Residual | `UnknownOrMixed` | Abstain bucket only. Never promote weak evidence into a root. |
| Candidate large roots | `TransitionRecovery`, `LiquidityDrought`, `CrossAssetRotation/RiskOnRiskOff`, `MacroPolicyRegime`, `BubbleEuphoria` | Preflight only until separability, support, action difference, and 95% calibration are proven. `BubbleEuphoria` may stay a `BullExpansion` child unless it has distinct downstream handling. |
| Sub-regime/evidence signatures | low-vol bull, high-vol bull, regular bear, correction, crash, range persistence, accumulation/distribution display labels, HMM state id, change-point break, directional-change event, spoofing/layering, pump event, wash burst, wall imbalance, thin liquidity | These support roots but cannot complete roots by name alone. |

## Accounting Impact

- Previous generic roots `Bull`, `Bear`, `Sideways`, and `Crisis` are source labels or legacy parent names, not the preferred active root names.
- `Sideways` / `RangeConsolidation` / `SidewaysConsolidation` map upward to `Consolidation`.
- `Crisis` remains a plausible large class because volatility/correlation/liquidity dislocation can require different downstream suppression than ordinary `BearExpansion`.
- `Manipulation` remains the only missing active root-or-overlay after this source refresh.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Fresh calibration rerun: false.
- Trade usable: false.

Gate result: `taxonomy_reset_no_new_accepted_root`.
