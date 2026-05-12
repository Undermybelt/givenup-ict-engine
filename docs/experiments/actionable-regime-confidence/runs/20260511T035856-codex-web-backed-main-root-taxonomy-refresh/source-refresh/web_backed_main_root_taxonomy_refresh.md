# Web-Backed Main Root Taxonomy Refresh

Run id: `20260511T035856+0800-codex-web-backed-main-root-taxonomy-refresh`

Purpose: answer the latest user correction that the active regime taxonomy was too low-level. This is a source refresh only. It does not claim any new 95%-99% calibrated root.

## Source Readback

1. Zakamulin 2023, `Not all bull and bear markets are alike`, supports splitting the broad bull/bear axis into multiple behaviorally different states: low-volatility bull, high-volatility bull, stock-market bubble, regular bear, and crash/correction. This supports keeping `BullExpansion`, `BearExpansion`, and `CrisisCrash` as main operational roots rather than treating them as mere child labels.
   - Source: `https://ideas.repec.org/a/pal/risman/v25y2023i1d10.1057_s41283-022-00112-y.html`

2. Oelschlager and Adam 2020, hierarchical HMMs, supports modeling short-term and long-term bull/bear structure separately so that short fluctuations do not overwrite the long-term root state. This argues for root plus transition/context fields, not one flat child-only ontology.
   - Source: `https://arxiv.org/abs/2007.14874`

3. Chen and Tsang 2018, directional-change normal/abnormal regimes, supports event-based regime features and normal/abnormal separation across markets. This supports `SidewaysConsolidation` and `CrisisCrash/VolatilityDislocation` as structural roots or root candidates, with DC/event features as evidence.
   - Source: `https://www.mdpi.com/1999-4893/11/12/202`

4. Werge 2021, asset-independent regime-switching, supports cross-asset bull, bear, and high-volatility periods. This keeps the root contract cross-market rather than equity-only.
   - Source: `https://arxiv.org/abs/2107.05535`

5. Hidden Regime GitHub exposes an HMM pipeline with Bull, Bear, Sideways, and Crisis examples plus event studies. This is not calibration evidence, but it is useful implementation prior art for temporal isolation, report/export artifacts, and crisis/event studies.
   - Source: `https://github.com/hidden-regime/hidden-regime`

6. Do and Putnins 2023 plus Fabre and Challet 2025 support `Manipulation` as a direct microstructure/order-lifecycle root-or-overlay, not an OHLCV trend state. Useful inputs are order-book imbalance, high order activity, abnormal cancellations, cyclic depth/cancellation patterns, L3 order placement distance, and order-level expected manipulation gain.
   - Sources: `https://ssrn.com/abstract=4525036`, `https://arxiv.org/abs/2504.15908`

7. SystemsLab Sapienza and Bayi-Hu GitHub repositories provide public pump-and-dump event/social datasets. These are candidate direct-event sources for `Manipulation`, but they still need chronological positive/negative calibration and cross-context validation before acceptance.
   - Sources: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`, `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`

## Active Root Reset

Current Board A root taxonomy should be `MainRegimeV3SourceBacked`:

| Root | Status After This Refresh | Evidence Requirement |
|---|---|---|
| `BullExpansion` | active root; accepted 95 via existing Kaggle coverage-buffer crosswalk | source-labeled bull/expansion target plus observed-feature rule, chronological calibration/test, cross-context support |
| `BearExpansion` | active root; missing | direct bear/negative-expansion target or robust source crosswalk, unchanged 95 gate |
| `SidewaysConsolidation` | active root; missing | direct flat/range/consolidation target or robust source crosswalk, unchanged 95 gate |
| `CrisisCrash` | active root; accepted 95 via prior `CrisisStress` crosswalk | high-volatility/crash/stress source-backed rule, chronological calibration/test |
| `Manipulation` | active root-or-overlay; missing required inputs | direct event/order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives |
| `UnknownOrMixed` | residual only | abstain bucket, not a completion root |

Preflight-only additional roots: `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `TransitionRecovery`, and `CrossAssetRotation/RiskOnRiskOff`. They should not weaken the active completion contract until a separate schema preflight proves support, separability, and downstream action difference.

## Decision

The previous Board A wording that demoted `BullExpansion`, `BearExpansion`, and `SidewaysConsolidation` to child-only labels is superseded by the latest user correction and this source refresh. Those labels now belong on the active root axis. Existing child signatures such as `TrendExpansion`, `RangeConsolidation`, `ThinLiquidity`, wall cancel bursts, and layering-stack imbalance remain evidence features unless they are reissued through a source-backed root gate.

Accepted accounting after this refresh: `BullExpansion` and `CrisisCrash` are accepted 95 from prior calibrated packets. Missing roots remain `BearExpansion`, `SidewaysConsolidation`, and `Manipulation`.

Runtime code changed: false. Thresholds relaxed: false. Fresh calibration rerun: false. Trade usable: false.
