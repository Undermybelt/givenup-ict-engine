# Web-Backed Root Taxonomy Refresh

Run id: `20260511T005646-codex-web-backed-root-taxonomy-refresh`

Purpose: refresh Board A's root-regime ontology after the user corrected that the prior packets were only child/subtype regimes. This artifact is taxonomy evidence only. It does not add a new calibrated 95% packet.

## User Correction Applied

The active root taxonomy should not be inferred from already-accepted subtype packets. The next root-axis work should treat the following as main/root candidates:

| Root Candidate | Operational Meaning | Source Support | Current Board State |
|---|---|---|---|
| `BullExpansion` | persistent positive drift / risk-on expansion, not merely generic trend | bull-market turning-point and Markov-switching literature | missing accepted 95 packet |
| `BearExpansion` | persistent negative drift / risk-off decline, separated from crash/stress | bull/bear regime literature and HMM regime models | missing accepted 95 packet |
| `Consolidation` | sideways/range/choppy regime with low directional conviction | market-regime practice and change-point/segmentation tooling | missing accepted 95 packet |
| `Manipulation` | liquidity-engineering / spoofing / layering / quote-order anomaly state or overlay | market manipulation and limit-order-book literature | `missing_required_inputs` until direct LOB/order-flow/order-lifecycle data exists |
| `CrisisStress` | turbulent/high-volatility/liquidity-break state that is not identical to ordinary `BearExpansion` | HMM/stress/turbulent-regime literature | prior source-backed gate accepted this only |
| `TransitionRecovery` | turning-point, recovery, accumulation/distribution, or post-crisis transition state | regime-switching and structural-change literature | optional root candidate; missing accepted 95 packet |
| `UnknownOrMixed` | residual bucket for overlap, weak confidence, or mixed signals | required calibration hygiene | residual only; never release confidence |

## Source Scan

Primary paper / methodology sources:

- Hamilton 1989 Markov-switching model: `https://doi.org/10.2307/1912559`
- Ang and Bekaert 2002 international asset allocation with regime switches: `https://doi.org/10.1093/rfs/15.4.1137`
- Maheu and McCurdy, "Identifying Bull and Bear Markets in Stock Returns": `https://doi.org/10.2307/1392140`
- Pagan and Sossounov 2003, "A Simple Framework for Analysing Bull and Bear Markets": `https://doi.org/10.1002/jae.664`
- Guidolin and Timmermann 2005, persistent bull and bear regimes in UK stock and bond returns: `https://doi.org/10.1111/j.1468-0297.2004.00962.x`
- Adaptive Hierarchical HMM paper: models bull, bear, turbulent states and higher-order structural change: `https://www.mdpi.com/1911-8074/19/1/15`
- `ruptures` change-point detection package and review paper: `https://github.com/deepcharles/ruptures`, `https://doi.org/10.1016/j.sigpro.2019.107299`
- `hmmlearn`: HMM implementation useful for hidden-state probabilities and persistence: `https://github.com/hmmlearn/hmmlearn`
- `hidden-regime`: open-source HMM market-regime package: `https://github.com/hidden-regime/hidden-regime`

Manipulation / direct-input sources:

- Do and Putnins, "Detecting Layering and Spoofing in Markets": `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4525036`
- Montgomery, "Spoofing, Market Manipulation, and the Limit-Order Book": `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2780579`
- "Spoofing and pinging in foreign exchange markets": `https://doi.org/10.1016/j.intfin.2020.101278`
- "Detecting Financial Market Manipulation with Statistical Physics Tools": `https://arxiv.org/abs/2308.08683`
- "Learning the Spoofability of Limit Order Books With Interpretable Probabilistic Neural Networks": `https://arxiv.org/abs/2504.15908`

## Board Interpretation

The prior `Bull` / `Bear` / `Sideways` / `Crisis` axis should now be treated as a coarse alias layer, not the final active root taxonomy. The user-corrected source-backed main classes are more specific:

- `Bull` maps to `BullExpansion` only when expansion/persistence is directly materialized.
- `Bear` maps to `BearExpansion` only when ordinary bearish expansion is separated from `CrisisStress`.
- `Sideways` maps to `Consolidation` / range-bound behavior.
- `Crisis` maps to `CrisisStress` / turbulent high-volatility stress.
- `Manipulation` remains a direct-input root or overlay, never an OHLCV-only inference.

The previous source-backed gate `20260511T003739-source-backed-root-gate-mtf` is therefore no longer "wrong axis" under the latest correction. It is still not a completion packet: it accepted only `CrisisStress` and left `BullExpansion`, `BearExpansion`, `Consolidation`, `TransitionRecovery`, and `Manipulation` blocked.

## Next Evidence Requirement

Do not run another broad OHLCV-only threshold search and call it progress. The next useful root packet needs one of:

1. richer signed-direction inputs for `BullExpansion` and `BearExpansion`, such as breadth, cross-asset risk-on/risk-off confirmation, rates/credit/vol term structure, futures basis/carry, or validated HMM posterior persistence;
2. stronger range/chop evidence for `Consolidation`, separated from low-vol bull drift and post-crisis compression;
3. direct manipulation inputs: tick tape, best bid/ask, Level 2/Level 3 order book snapshots/updates, order add-cancel-replace lifecycle, venue event data, or crypto social/on-chain/mempool evidence where applicable;
4. an explicit decision whether `TransitionRecovery` is a root class or an overlay before it can be calibrated.

Current gate state remains blocked. No threshold was relaxed. No runtime code changed.
