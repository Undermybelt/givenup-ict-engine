# Main Regime Taxonomy Enrichment

Run id: `20260511T042050+0800-codex-main-regime-taxonomy-enrichment`

Purpose: answer the user correction that several proposed regimes were only subclasses or feature signatures. This is a paper/GitHub source refresh only. It does not claim a new 95%-99% calibrated root.

## Layer Decision

Active Board A roots remain `MainRegimeV3SourceBacked`:

| Layer | Labels | Decision |
|---|---|---|
| Active root | `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisCrash` | Main market-state roots that need per-root calibrated evidence packets. |
| Direct-input root or overlay | `Manipulation` | Main root-or-overlay only when direct event/order-lifecycle/L2/L3/MBO/social/on-chain evidence exists. |
| Residual | `UnknownOrMixed` | Abstain bucket, not a promotion target. |
| Preflight-only possible roots | `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `TransitionRecovery`, `CrossAssetRotation/RiskOnRiskOff`, `MacroPolicyRegime` | Plausible large axes, but not active completion roots until schema, support, separability, and downstream action difference are proven. |
| Sub-regime / evidence signatures | low-volatility bull, high-volatility bull, regular bear, correction, wall imbalance, spoofing/layering stack, pump event, wash burst, thin liquidity, change-point break, HMM posterior state | These can support roots but cannot complete root acceptance by themselves unless reissued through a source-backed root gate. |

## Source Readback

| Source | Useful Signal | Board A Decision |
|---|---|---|
| Zakamulin, `Not all bull and bear markets are alike`, `https://doi.org/10.1057/s41283-022-00112-y` | Bull and bear periods split into behaviorally different states such as low-vol bull, high-vol bull, stock-market bubble, regular bear, and crash/correction. | Supports bull/bear as main axes with child states below them, and supports `CrisisCrash` / `BubbleEuphoria` as large separable candidates. |
| Oelschlager and Adam, hierarchical HMM, `https://arxiv.org/abs/2007.14874` | Long-term and short-term bull/bear structure can be modeled hierarchically. | Supports root state plus sub-state/context separation instead of flattening every child signal into a root. |
| Chen and Tsang, directional-change regime features, `https://doi.org/10.3390/a11120202` | Event-based features separate normal/abnormal price behavior and can reduce clock-time blur. | Directional-change events are evidence features for roots such as expansion, consolidation, and dislocation, not standalone accepted roots. |
| Werge, asset-independent regime switching, `https://arxiv.org/abs/2107.05535` | Cross-asset regime switching can identify bull, bear, and high-volatility states without staying equity-only. | Supports keeping the root contract cross-market and treating high-volatility/dislocation as a candidate root family. |
| Kaggle `mafaqbhatti/stock-market-regimes-20002026`, `https://www.kaggle.com/datasets/mafaqbhatti/stock-market-regimes-20002026` | Public labels include broad `Bull`, `Bear`, `Sideways`, `Crisis`, and high-volatility-style regimes. | Useful for root-label preflight and prior accepted `BullExpansion`; already failed to complete `BearExpansion`. |
| Hidden Regime GitHub, `https://github.com/hidden-regime/hidden-regime` | HMM/report pipeline examples include Bull, Bear, Sideways, and Crisis/event-study surfaces. | Useful implementation prior art, not acceptance evidence by itself. |
| `hmmlearn`, `https://github.com/hmmlearn/hmmlearn` | General HMM tooling for hidden-state posteriors and persistence. | Implementation prior only; accepted roots still require source relabeling plus chronological calibration/test. |
| `ruptures`, `https://github.com/deepcharles/ruptures` | Change-point detection tooling for structural breaks. | Boundary evidence only; a break does not define the post-break root by itself. |
| Siering, Clapham, Engel, and Gomber, automated market-manipulation detection taxonomy, `https://doi.org/10.1057/s41265-016-0029-z` | Manipulation detection should be categorized by manipulation type and input evidence, not reduced to generic OHLCV stress. | Supports `Manipulation` as a direct-input-gated root-or-overlay with subtype signatures below it. |
| Do and Putnins, spoofing/layering detection, `https://ssrn.com/abstract=4525036` | Direct order-book evidence includes imbalance, high order activity, abnormal cancellations, and patterns around prosecuted cases. | Supports accepting only direct microstructure/order-lifecycle evidence for `Manipulation`. |
| Fabre and Challet, order-level manipulation analysis, `https://arxiv.org/abs/2504.15908` | Manipulation detection can depend on L3/order-level placement, cancellations, and expected gain. | Reinforces fail-closed handling for OHLCV-only manipulation proxies. |
| SystemsLab Sapienza pump-and-dump dataset, `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset` | Public pump event/social evidence for crypto manipulation research. | Candidate direct-event source for `Manipulation`; still needs chronological positives/negatives and cross-context calibration. |
| Bayi-Hu pump-and-dump GitHub, `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency` | Public event/social/market feature lane for pump-and-dump detection. | Candidate direct-event source; prior Board A probes did not pass 95. |

## Implications

- `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, and `CrisisCrash` should stay on the active root axis. Child states such as low-vol bull, high-vol bull, regular bear, correction, and range persistence should be recorded as sub-regime/context evidence.
- `Manipulation` is not a normal trend/volatility state. It is a direct-input root-or-overlay requiring direct labeled event/order-lifecycle evidence. OHLCV stress, sweep-like ranges, session liquidity, thin liquidity, and wall-like proxies remain fail-closed.
- `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `TransitionRecovery`, `CrossAssetRotation/RiskOnRiskOff`, and `MacroPolicyRegime` are plausible next major classes, but adding them to the completion contract now would expand scope without 95% evidence.
- The immediate missing-root search should split cleanly:
  - `BearExpansion`: find or build a directional, source-backed negative-expansion label with multi-context chronological calibration.
  - `Manipulation`: acquire direct event/order-lifecycle positives and negatives before any model gate.

Gate result: `taxonomy_enriched_no_new_accepted_root`.

Accepted active roots after this refresh remain `BullExpansion`, `SidewaysConsolidation`, and prior `CrisisCrash`. Missing active roots remain `BearExpansion` and direct-input-gated `Manipulation`.

Runtime code changed: false. Thresholds relaxed: false. Fresh calibration rerun: false. Trade usable: false.
