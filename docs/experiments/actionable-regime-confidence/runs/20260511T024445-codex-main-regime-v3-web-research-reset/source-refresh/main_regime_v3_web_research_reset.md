# MainRegimeV3 Web/Paper/GitHub Research Reset

Run id: `20260511T024445+0800-codex-main-regime-v3-web-research-reset`

Supersession note: this source scan is now retained as provenance only. The active Board A root axis is MainRegimeV2 (`Bull`, `Bear`, `Sideways`, `Crisis`, direct-input-gated `Manipulation`, and residual `UnknownOrMixed`) unless the user explicitly reopens the V3 schema.

Scope: source-backed taxonomy reset only. No provider readiness is newly claimed, no raw market dataset is committed, and no 95% acceptance gate is completed by this scan.

## Source Takeaways

1. Bull and bear should not be treated only as low-level features. Classical bull/bear market dating work and HMM regime work make persistent rising/falling market phases a natural top-level state axis.
2. Sideways/range/consolidation should not be buried under generic `Sideways` if the downstream action differs. Modern three-state and four-state examples explicitly separate bullish, bearish, sideways, volatile/crisis states.
3. Manipulation is not an OHLCV regime. It is a direct-event/order-lifecycle class or overlay requiring pump/dump, wash, spoofing/layering, quote-stuffing, or equivalent labeled/direct evidence.
4. Crisis/stress remains a top-level risk state because covariance/correlation/volatility regimes can dominate direction and sizing.
5. Other large classes are plausible, but should enter as candidate roots only after a schema preflight: transition/recovery, bubble/euphoria, volatility-dislocation, liquidity-drought, and cross-asset/sector-rotation.

## MainRegimeV3 Proposed Root Set

| Root key | Meaning | Child / provenance examples | Required evidence style |
|---|---|---|---|
| `BullExpansion` | Persistent upward/risk-on expansion state | trend expansion, buy-dip persistence, low-vol bull, breadth expansion | chronological calibration for positive drift/persistence plus cross-context validation |
| `BearExpansion` | Persistent downward/risk-off downside expansion state | downside trend, sell-rally, deleveraging, negative breadth | chronological calibration for negative drift/persistence plus cross-context validation |
| `SidewaysConsolidation` | Range/chop/compression state where directional systems should be suppressed or resized | range consolidation, low trend strength, compression, mean-reversion window | range-bound target, low directional drift, support across instruments/timeframes |
| `CrisisStress` | Crash/stress/high-volatility/correlation-break state | extreme stress, volatility spike, correlation spike, liquidity stress | direct stress/covariance/volatility/drawdown features; not just a display label |
| `Manipulation` | Direct market abuse or engineered price/action lifecycle | pump/dump, wash trading, spoofing, layering, quote-stuffing-like bursts | labeled/direct event/order-flow/order-lifecycle evidence; OHLCV proxies fail closed |
| `UnknownOrMixed` | Residual abstain state | mixed posterior, conflicting evidence, low support | not a release gate; abstain/default guardrail |

Candidate add-on roots to test before final lock: `TransitionRecovery`, `BubbleEuphoria`, `VolatilityDislocation`, `LiquidityDrought`, `Rotation`. These are source-supported ideas, not accepted gates.

## Implementation Implications

- Do not report `Bull`, `Bear`, and `Sideways` as the final root keys if the operational target is expansion/consolidation behavior. Use `BullExpansion`, `BearExpansion`, and `SidewaysConsolidation`.
- Keep `TrendExpansion`, `RangeConsolidation`, `ThinLiquidity`, `SessionLiquidityCoreViable`, L2 wall/cancel/layering signatures, and similar fields as children, predictors, or overlay evidence.
- `Manipulation` remains special: it can be emitted as a main class or overlay only when direct labels/events/order-lifecycle evidence is present.
- HMM, change-point detection, covariance regimes, directional-change indicators, and event studies are methods/evidence channels, not root classes by themselves.
- Superseded next-step correction: do not materialize this MainRegimeV3 schema unless explicitly reopened. Continue from the active MainRegimeV2 blockers in the board.

## Source Inventory

- Pagan and Sossounov, "A Simple Framework for Analysing Bull and Bear Markets", Journal of Applied Econometrics: bull/bear market dating as a primary market-state problem. `https://ideas.repec.org/a/jae/japmet/v18y2003i1p23-46.html`
- Oelschlager and Adam, "Detecting bearish and bullish markets in financial time series using hierarchical hidden Markov models": bullish/bearish switches and multi-scale trend interpretation. `https://arxiv.org/abs/2007.14874`
- "Identifying Risk Regimes in a Sectoral Stock Index Through a Multivariate Hidden Markov Framework": a three-state bullish/sideways/bearish HMM example with distinct return/volume/OI behavior. `https://www.mdpi.com/2227-9091/13/7/135`
- "Market Regime Detection via Realized Covariances": calm/high-volatility covariance regimes support stress/volatility as a major axis. `https://arxiv.org/abs/2104.03667`
- Guidolin and Timmermann, regime-switching stock/bond allocation work: multiple economic regimes beyond simple bull/bear, including crash/recovery-style states in asset-allocation context. `https://www.nber.org/papers/w17182`
- `hidden-regime/hidden-regime`: executable HMM pipeline with event studies for crashes, bubbles, and sector rotations. `https://github.com/hidden-regime/hidden-regime`
- `hmmlearn/hmmlearn`: implementation reference for HMM posterior-state features. `https://github.com/hmmlearn/hmmlearn`
- `deepcharles/ruptures`: implementation reference for change-point/boundary evidence. `https://github.com/deepcharles/ruptures`
- Xu and Livshits, "The Anatomy of a Cryptocurrency Pump-and-Dump Scheme": direct manipulation event modeling. `https://arxiv.org/abs/1811.10109`
- Kamps and Kleinberg, "To the moon: defining and detecting cryptocurrency pump-and-dumps": criteria for crypto pump-and-dump detection. `https://doi.org/10.1186/s40163-018-0093-5`
- `Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`: executable GitHub source for cryptocurrency pump-and-dump target-coin/event data. `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- Mendeley wash-trading dataset: row-level NFT/Mt. Gox wash-trading data source already used in the current lane. `https://data.mendeley.com/datasets/4hyxfwzpgg/1`

## Gate Result

Result: `blocked_taxonomy_reset_only`.

Accepted 95 roots from this source scan: none. Prior `Crisis` evidence remains accepted only under the active MainRegimeV2 accounting in the board; this V3 scan does not change completion accounting.

Thresholds relaxed: false. Runtime code changed: false. Fresh calibration rerun: false. Trade usable: false.
