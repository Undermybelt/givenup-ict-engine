# MainRegimeV5 Schema Crosswalk

Run ID: `20260511T092356+0800-mainregimev5-schema-crosswalk`

Board: Board A, `docs/plans/2026-05-10-actionable-regime-confidence-todo.md`

## Objective

Materialize the active `MainRegimeV5` schema/crosswalk after the user reopened taxonomy, without promoting any prior subtype/proxy/model packet as accepted 95%-99% completion.

## Active Roots

Mandatory roots for calibration:

- `BullExpansion`
- `BearExpansion`
- `ConsolidationRange`
- `CrisisStress`
- `ManipulationLiquidityEngineering`
- `TransitionAccumulationDistribution`

Optional overlay/watchlist until separability and downstream action difference are proven:

- `CrossAssetMacroRotation`

Residual:

- `UnknownOrMixed`

## Required Label Panel Fields

- `provider`
- `instrument`
- `timeframe`
- `v5_root`
- `start_ts`
- `end_ts`
- `source_label`
- `source_label_confidence`
- `source_name`
- `source_license_or_access_contract`
- `labeling_method`
- `label_timestamp_or_publication_time`
- `raw_source_reference`
- `crosswalk_status`
- `chronological_split`
- `validation_market_context`

Additional required fields for `ManipulationLiquidityEngineering`:

- `direct_evidence_channel`
- `positive_or_negative_label`
- `venue_or_source`
- `event_type`

## Crosswalk

| V5 root | Prior provenance only | Required re-audit | Forbidden shortcut |
|---|---|---|---|
| `BullExpansion` | prior `Bull`, unsigned `TrendExpansion` | signed positive expansion source labels or calibrated parent-root gate across markets/timeframes | generic trend, future return target, or HMM state id |
| `BearExpansion` | prior `Bear`, unsigned `TrendExpansion`, stress sidecars | signed negative expansion labels separated from crisis/stress | generic drawdown proxy, future return target, or crisis bucket reuse |
| `ConsolidationRange` | prior `Sideways`, `RangeConsolidation` | range/compression persistence with false-break/mean-reversion context and cross-context calibration | absence-of-trend proxy alone |
| `CrisisStress` | prior `Crisis`, `ExtremeStress`, `CrisisStress`, `CrisisCrash` | tail/loss/liquidity-cliff labels with chronological support and enough non-crisis controls | ordinary bear expansion or volatility-only proxy |
| `ManipulationLiquidityEngineering` | prior `Manipulation` overlay, `ThinLiquidity`, session/liquidity packets | direct event/order-flow/order-lifecycle/L2/L3/MBO/wash-trade/social positive and negative rows | OHLCV sweeps, thin-liquidity, volume-ratio, or indicator proxy |
| `TransitionAccumulationDistribution` | `ReversalBrewing`, transition hazard, accumulation/distribution clues | boundary/transition labels with post-boundary validation and duration viability | any reversal-looking candle pattern without source labels or calibration |
| `CrossAssetMacroRotation` | macro/rotation/breadth sidecars | separability and downstream action difference before mandatory use | treating macro context as a substitute for price-root labels |

## Accounting

- Accepted 95 roots added by this schema/crosswalk: `0`.
- Accepted gate remains: `none_for_MainRegimeV5_schema_crosswalk_no_calibration`.
- Prior V2/V3/V4 labels and six accepted subtype/signature packets are provenance only.
- Prior 48 exact-underlying V2 source-label slots are not automatically accepted for V5 because each V5 root requires root-specific semantics and rerun calibration.
- `ManipulationLiquidityEngineering` remains fail-closed until direct timestamped positive/negative rows are available.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Raw data committed: false.
- Trade usable: false.

## Next Action

Run a V5 attachability/calibration readiness audit that maps available prior evidence into V5 provenance rows, counts which V5 roots have source-label/calibration inputs, and fails closed where labels are missing.
