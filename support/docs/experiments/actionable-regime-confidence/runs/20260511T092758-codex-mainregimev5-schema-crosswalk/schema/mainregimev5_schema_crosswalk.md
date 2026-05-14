# MainRegimeV5 Schema Crosswalk

Run ID: `20260511T092758+0800-codex-mainregimev5-schema-crosswalk`

## Result

- Active taxonomy: `MainRegimeV5`.
- Schema materialized: `true`.
- Calibration rerun: `false`.
- Accepted 95 roots added: `0`.
- Accepted gate: `none_for_MainRegimeV5_schema_materialized_calibration_pending`.
- Gate result: `blocked_mainregimev5_schema_materialized_calibration_pending`.
- Runtime code changed: false. Thresholds relaxed: false. Raw data committed: false. Trade usable: false.

## Mandatory Roots

| Root | Definition | Legacy Inputs | Reuse Policy |
|---|---|---|---|
| `BullExpansion` | signed positive directional expansion | `Bull`, `TrendExpansion`, persistence features | provenance only until signed V5 calibration passes |
| `BearExpansion` | signed negative directional expansion | `Bear`, `TrendExpansion`, drawdown features | provenance only; crisis/stress cannot substitute |
| `ConsolidationRange` | range, compression, sideways persistence, false-break/mean-reversion feasibility | `Sideways`, `RangeConsolidation`, `SidewaysConsolidation` | child/provenance only until V5 root rerun passes |
| `CrisisStress` | tail-loss, volatility dislocation, liquidity cliff, crash/stress | `Crisis`, `ExtremeStress`, `CrisisStress`, `CrisisCrash` | provenance only until V5 crisis-stress rerun passes |
| `ManipulationLiquidityEngineering` | spoofing, layering, wash trading, pump/dump, quote stuffing, stop-run, liquidity raid | `Manipulation`, direct event/order-flow rows, social/event packets, L2/order-book signatures | OHLCV/session/liquidity proxies are inputs only; direct positive/negative labels required |
| `TransitionAccumulationDistribution` | accumulation, distribution, reversal, or boundary transition phase | `ReversalBrewing`, change-point and directional-change features | child/provenance only until transition-specific validation passes |

Optional overlay/watchlist: `CrossAssetMacroRotation`.

Residual: `UnknownOrMixed`, fail closed.

## Hard Rejections

- Do not promote subtype/signature packets by wording.
- Do not accept HMM/GMM/cluster IDs without external labels or unchanged chronological calibration.
- Do not accept OHLCV/session/liquidity proxies as `ManipulationLiquidityEngineering`.
- Do not count document indexes, search surfaces, or methodology papers as source-label panels.

## Next Calibration Matrix

- Market scope: expanded full-species/full-universe requirement remains open.
- Timeframes: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`, `1mo`.
- Providers/sources: yfinance, Kraken, local cache, Auto-Quant cache, IBKR if operator runtime is available, TradingViewRemix if connectivity is restored, and direct manipulation row sources.
- Current blocker: source labels/direct positive-negative rows are still insufficient for a full V5 calibration matrix.

## Next Action

Run a V5 attachability/calibration preflight that maps existing source-backed packets and missing slots to the six mandatory V5 roots without relaxing thresholds.
