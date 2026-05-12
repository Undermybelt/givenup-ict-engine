# Main Regime V4 Web Research Taxonomy

Run id: `20260511T082635+0800-codex-main-regime-v4-web-research-taxonomy`

Trigger: user explicitly reopened the taxonomy after the prior MainRegimeV2 lock, stating that the main classes should be closer to `BullExpansion`, `BearExpansion`, `Manipulation`, and `Consolidation`, with possible additional roots. This packet supersedes the active Board A taxonomy wording, but does not accept any confidence gate.

## Source Scan

| Source | Useful signal | Taxonomy implication |
|---|---|---|
| Pagan and Sossounov, 2003, `A Simple Framework for Analysing Bull and Bear Markets`, Journal of Applied Econometrics, DOI `10.1002/jae.664`, indexed at `https://www.econbiz.de/10001738239` and summarized at `https://www.researchgate.net/publication/5139690_A_Simple_Framework_for_Analyzing_Bull_and_Bear_Markets` | Bull and bear markets are parent-level equity-price cycle states, not small derived subtypes. | Preserve a directional parent axis, but user-facing roots should describe actionable expansion phases, not raw HMM ids. |
| Maheu, McCurdy, and Song, 2012, `Components of Bull and Bear Markets: Bull Corrections and Bear Rallies`, `https://ideas.repec.org/a/taf/jnlbes/v30y2012i3p391-403.html` | Bull corrections and bear rallies are components inside bull/bear markets. | `BullExpansion` and `BearExpansion` are main directional roots; correction/rally states are child or transition evidence. |
| `hidden-regime/hidden-regime`, `https://github.com/hidden-regime/hidden-regime` | The open-source implementation exposes Bull, Bear, Sideways, and Crisis as core market-regime concepts. | `Consolidation`/Sideways and `CrisisStress` deserve root-layer treatment rather than being buried under child packets. |
| `Sakeeb91/market-regime-detection`, `https://github.com/Sakeeb91/market-regime-detection` | Its README frames detected regimes as Bull/Calm, Bear/Crisis, and Transition. | A transition bucket is useful, but should be residual/preflight until separable labels and actions are proven. |
| Tampouris and Dritsaki, 2026, `Adaptive Hierarchical Hidden Markov Models for Structural Market Change`, `https://www.mdpi.com/1911-8074/19/1/15` | Separates fast states such as bull, bear, and turbulent from slower low/high-uncertainty meta-regimes. | `CrisisStress`/Turbulent can be an additional main class; macro/uncertainty is better treated as a meta-regime overlay. |
| `Market manipulation detection: A systematic literature review`, Expert Systems with Applications, 2022, `https://www.sciencedirect.com/science/article/pii/S0957417422014555` | Treats market manipulation detection as its own trade-based manipulation taxonomy and anomaly problem. | `Manipulation` is a direct-event/order-flow root-output class, not an OHLCV child of sideways or thin liquidity. |
| Siering, Clapham, Engel, and Gomber, 2017, `A Taxonomy of Financial Market Manipulations`, `https://journals.sagepub.com/doi/10.1057/s41265-016-0029-z` | Provides a manipulation taxonomy for automated fraud detection. | Manipulation evidence must come from direct surveillance-style labels or direct order/trade/event inputs. |
| Mirtaheri et al. / Hamrick et al. / crypto manipulation surveys, including `https://arxiv.org/abs/2105.00733`, `https://arxiv.org/abs/2005.06610`, and `https://www.mdpi.com/1999-5903/15/8/267` | Pump-and-dump, wash trading, spoofing/layering, social-event manipulation, and order-book manipulation are distinct event forms. | Manipulation subtypes are children of `Manipulation`, not substitutes for price-regime roots. |

## Decision

Board A should move from the prior `MainRegimeV2` root wording to `MainRegimeV4`:

| MainRegimeV4 root | Meaning | Accepted evidence requirement |
|---|---|---|
| `BullExpansion` | Sustained positive directional expansion / constructive risk regime. | Independent labels or calibrated rule with chronological split, cross-market/timeframe support, and no future-target leakage. |
| `BearExpansion` | Sustained negative directional expansion / risk-off decline that is not just a one-bar crash. | Independent labels or calibrated rule with chronological split, cross-market/timeframe support, and crisis-vs-bear separation. |
| `Consolidation` | Sideways/range/compression/neutral regime with weak directional edge. | Source labels or calibrated range/compression rule validated across instruments and timeframes. |
| `CrisisStress` | Turbulent/high-volatility/systemic-stress class distinct from ordinary bear expansion. | Stress/crisis labels, volatility-dislocation evidence, or cross-market drawdown/stress rule with high support. |
| `Manipulation` | Direct manipulation/event/order-flow/order-lifecycle class. | Direct positive/negative labels: pump/dump events, wash-trade rows, spoofing/layering order lifecycle, L2/L3/MBO evidence, social-event labels, or comparable provenance. OHLCV proxy alone remains fail-closed. |
| `UnknownOrMixed` | Residual abstain bucket. | Never counts as completion. |

Candidate future roots or overlays remain preflight-only until they pass separability, support, action difference, and per-root calibration:

- `TransitionRecovery`
- `AccumulationDistribution`
- `BubbleEuphoria`
- `LiquidityDrought`
- `CrossAssetRotationRiskOnRiskOff`
- `MacroPolicyRegime`
- `LowUncertainty` / `HighUncertainty` meta-regime overlay

## Crosswalk From Prior Board State

| Prior active wording | V4 handling |
|---|---|
| `Bull` | Re-audit as `BullExpansion`; do not count raw Bull labels until the V4 schema proves they represent directional expansion rather than weak recovery or transition. |
| `Bear` | Re-audit as `BearExpansion`; separate ordinary bear trend from `CrisisStress`. |
| `Sideways` | Rename/reframe to `Consolidation`; range/compression child packets can support but not complete without V4 calibration. |
| `Crisis` | Preserve as `CrisisStress`; not subordinate to `BearExpansion`. |
| `Manipulation` overlay | Promote to active root-output class with direct-input gate and override precedence when direct evidence exists. |
| `TrendExpansion`, `RangeConsolidation`, `ExtremeStress`, `ReversalBrewing`, `ThinLiquidity`, `SessionLiquidityCoreViable` | Child/provenance evidence only. They may support roots but cannot complete a root by wording. |

## Acceptance Accounting

- Existing MainRegimeV2 source-label attachability `48/612` is no longer directly accepted for the expanded user goal until re-run against V4 roots.
- Existing subtype packets remain useful guardrails only.
- Direct `Manipulation` accepted label slots remain `0`.
- No 95%-99% confidence gate is accepted by this web scan.
- Thresholds are unchanged.
- Runtime code changed: false.
- Raw web or market data committed: false.
- Trade usable: false.

## Next Action

Materialize the V4 target schema and source-label crosswalk, then rerun attachability/completion accounting for `BullExpansion`, `BearExpansion`, `Consolidation`, `CrisisStress`, and direct-input-gated `Manipulation`. After that, resume the Mendeley/Dune direct manipulation source path under the V4 schema.
