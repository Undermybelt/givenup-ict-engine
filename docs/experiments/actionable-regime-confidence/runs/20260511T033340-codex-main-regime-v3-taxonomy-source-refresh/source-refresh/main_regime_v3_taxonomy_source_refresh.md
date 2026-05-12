# Main Regime V3 Taxonomy Source Refresh

Run root: `docs/experiments/actionable-regime-confidence/runs/20260511T033340-codex-main-regime-v3-taxonomy-source-refresh`

Purpose: refresh the parent regime taxonomy after the user correction that expansion/consolidation/manipulation should not be treated as ordinary child labels.

## Source Scan

- Zakamulin, "Not all bull and bear markets are alike: insights from a five-state hidden semi-Markov model", Risk Management / SSRN. The model separates multiple bull states and multiple bear states, including low-vol bull, high-vol bull, bubble, regular bear, and crash/correction. Source: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3678004`, DOI `10.1057/s41283-022-00112-y`.
- Hidden Regime GitHub package. It exposes HMM market regimes and event studies for crashes, bubbles, and sector rotations, and its README uses parent market conditions such as bull, bear, sideways, and crisis. Source: `https://github.com/hidden-regime/hidden-regime`.
- Montgomery, "Spoofing, Market Manipulation, and the Limit-Order Book", SSRN. It treats spoofing/layering through limit-order-book behavior and cancellation intent, so manipulation must be a direct microstructure/event evidence lane rather than an OHLCV child of bull/bear/sideways. Source: `https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2780579`, DOI `10.2139/ssrn.2780579`.
- SystemsLab-Sapienza pump-and-dump dataset GitHub. It provides labeled crypto manipulation events tied to Telegram pump groups and exchange/timestamp fields; this is direct event-labeled manipulation evidence. Source: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`, paper DOI `10.1109/ICCCN49398.2020.9209660`.
- Bayi-Hu pump-and-dump work. The paper/repo frame pump prediction as a target-coin/event task and release code/data, reinforcing that manipulation needs its own labeled-event gate. Sources: `https://arxiv.org/abs/2204.12929`, `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`.

## Taxonomy Decision

Active parent axis should move from flat MainRegimeV2 to MainRegimeV3Candidate:

| Parent root | Role | Minimal evidence shape |
|---|---|---|
| `BullExpansion` | Positive directional expansion / risk-on trend state. | Directional persistence, positive realized drift, acceptable drawdown, breadth or cross-asset confirmation, chronological calibration/test gate. |
| `BearExpansion` | Negative directional expansion / risk-off trend state. | Downside persistence, negative realized drift, rising stress or drawdown, defensive/risk-off confirmation, chronological calibration/test gate. |
| `SidewaysConsolidation` | Non-directional consolidation / balanced auction / low-drift range state. | Low absolute drift, bounded realized range, low trend efficiency, rotation or mean-reversion evidence, chronological calibration/test gate. |
| `CrisisCrash` | Extreme stress, crash, dislocation, or correction state. | Very negative return or drawdown, volatility/liquidity stress, cross-context stress confirmation, chronological calibration/test gate. |
| `Manipulation` | Direct microstructure/event-driven manipulation state or overlay. | Labeled event/order-lifecycle/L2/L3/MBO/social/on-chain evidence; OHLCV proxies remain fail-closed. |
| `TransitionRecovery` | Optional parent only if separability and action difference pass preflight. | Break recency, posterior entropy fall, reversal/recovery confirmation, separate allowed_action from bull/bear/sideways. |
| `BubbleEuphoria` | Optional parent or bull child depending on downstream action difference. | Extreme positive drift, valuation/sentiment/crowding or acceleration evidence, crash-risk guardrail. |
| `LiquidityDrought` / `VolatilityDislocation` | Optional parent or crisis/liquidity overlay depending on action difference. | Spread/depth/liquidity/volatility direct evidence, not just ATR proxy. |
| `CrossAssetRotation` | Optional parent or context overlay depending on action difference. | Sector/factor/asset-flow rotation evidence with downstream action difference. |
| `UnknownOrMixed` | Residual abstain bucket. | Used when no parent root reaches calibrated confidence. |

## Gate Implication

- `Bull`, `Bear`, and `Sideways` should become coarse display aliases, not completion roots.
- Prior `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, and `CrisisStress/Crash` runs are no longer merely child evidence; they should be reissued through MainRegimeV3Candidate root gates.
- No 95%-99% completion is claimed by this source refresh. It only resets the active taxonomy contract.
- The next executable step is a MainRegimeV3Candidate schema preflight and root gate that reuses existing source-backed feature tables before any fresh raw data pull.

