# MainRegimeV3 Reopened Source Refresh

Run id: `20260511T073701+0800-codex-main-regime-v3-reopened-source-refresh`

Scope: paper/GitHub/source-backed taxonomy correction only. No raw market data was committed, no runtime code changed, no thresholds were relaxed, and no 95% acceptance gate is completed by this source scan alone.

## User Correction Applied

The latest user correction reopens the V3 schema: `BullExpansion`, `BearExpansion`, `Manipulation`, and `SidewaysConsolidation` / `Consolidation` are top-level decision classes for Board A, not merely child/provenance labels. The prior wording that forced `BullExpansion`, `BearExpansion`, and `Consolidation` under naked `Bull` / `Bear` / `Sideways` is superseded for current Board A planning.

## Source Takeaways

1. Bull and bear regimes are primary market-state objects in classic market-cycle dating and HMM literature, but for this project the actionable root should include the behavioral phase: `BullExpansion` and `BearExpansion`.
2. Consolidation/sideways/range is a primary action regime when it changes downstream strategy selection from directional continuation to suppression, mean reversion, or abstain.
3. Crisis/stress remains a separate major class because volatility/correlation/liquidity shocks can dominate sign and sizing; it should not be hidden inside ordinary `BearExpansion`.
4. Manipulation is a top-level decision class for the downstream chain, but its evidence channel is not ordinary OHLCV regime detection. It requires direct event, social/event, order-flow, order-lifecycle, wash-trade, spoofing/layering, or equivalent labeled evidence. OHLCV proxy-only evidence remains fail-closed.
5. Other large classes are plausible but should enter through preflight first: `TransitionRecovery`, `BubbleEuphoria`, `LiquidityDrought`, `VolatilityDislocation`, `CrossAssetRotationOrRiskOnRiskOff`, and `MacroPolicyRegime`.

## Active MainRegimeV3 Root Set

| Root key | Meaning | Child / provenance examples | Required evidence style |
|---|---|---|---|
| `BullExpansion` | Persistent upward/risk-on expansion state | trend expansion, buy-dip persistence, breadth expansion, low-vol bull | chronological calibration for positive drift/persistence plus cross-context validation |
| `BearExpansion` | Persistent downside/risk-off expansion state | downside trend, sell-rally failure, deleveraging, negative breadth | chronological calibration for negative drift/persistence plus cross-context validation |
| `SidewaysConsolidation` | Range/chop/compression state where directional systems should be suppressed, resized, or replaced | range consolidation, low trend strength, compression, mean-reversion window | range-bound target, low directional drift, support across instruments/timeframes |
| `CrisisStress` | Crash/stress/high-volatility/correlation or liquidity shock state | crisis crash, volatility dislocation, liquidity shock, correlation spike | direct stress/covariance/volatility/drawdown/liquidity evidence |
| `Manipulation` | Direct market-abuse or engineered price/action lifecycle | pump/dump, wash trading, spoofing, layering, quote-stuffing-like bursts | labeled/direct event/order-flow/order-lifecycle evidence; OHLCV proxies fail closed |
| `UnknownOrMixed` | Residual abstain state | mixed posterior, conflicting evidence, low support | not a completion root; abstain/default guardrail |

## Source Inventory

- Pagan and Sossounov, "A Simple Framework for Analysing Bull and Bear Markets": bull/bear cycle dating as a market-state problem. `https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html`
- Oelschlager and Adam, "Detecting bearish and bullish markets in financial time series using hierarchical hidden Markov models": bullish/bearish state detection at multiple temporal scales. `https://arxiv.org/abs/2007.14874`
- Guidolin and Timmermann, NBER "Regime Changes and Financial Markets": multiple asset-allocation regimes beyond a simple two-state split. `https://www.nber.org/papers/w17182`
- `hidden-regime/hidden-regime`: executable HMM and event-study implementation surface for regimes, crashes, bubbles, and rotations. `https://github.com/hidden-regime/hidden-regime`
- `hmmlearn/hmmlearn`: implementation primitive for posterior hidden-state probabilities. `https://github.com/hmmlearn/hmmlearn`
- `deepcharles/ruptures`: implementation primitive for change-point boundary evidence. `https://github.com/deepcharles/ruptures`
- Xu and Livshits, "The Anatomy of a Cryptocurrency Pump-and-Dump Scheme": direct crypto manipulation event modeling. `https://arxiv.org/abs/1811.10109`
- Kamps and Kleinberg, "To the moon: defining and detecting cryptocurrency pump-and-dumps": criteria for pump-and-dump detection. `https://doi.org/10.1186/s40163-018-0093-5`
- `Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`: public executable source for crypto pump-and-dump event/social data. `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- Mendeley wash-trading dataset: candidate direct manipulation row source. `https://data.mendeley.com/datasets/4hyxfwzpgg/3`

## Accounting Impact

- Active taxonomy is now `MainRegimeV3`, not the prior MainRegimeV2 price-root-only axis.
- Completion roots are `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisStress`, and `Manipulation`.
- Prior accepted packets remain useful evidence, but must be remapped and re-audited under V3 before claiming full-universe/full-cycle completion.
- `Manipulation` is promoted back into the top-level Board A decision set, while still requiring direct/event/order-flow evidence.
- This source refresh accepts zero new 95% roots. It only corrects the target schema.

## Gate Result

Result: `blocked_taxonomy_reopened_mainregimev3_source_refresh_only`.

Accepted 95 roots from this scan: none.

Next action: materialize a MainRegimeV3 crosswalk and rerun attachability/full-coverage disposition against `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, `CrisisStress`, and `Manipulation`, without promoting OHLCV proxies or weakening 95% gates.
