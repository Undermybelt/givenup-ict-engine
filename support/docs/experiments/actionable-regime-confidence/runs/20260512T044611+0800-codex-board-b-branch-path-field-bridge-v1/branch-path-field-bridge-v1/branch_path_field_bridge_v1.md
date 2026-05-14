# Branch Path Field Bridge v1

Run id: `20260512T044611+0800-codex-board-b-branch-path-field-bridge-v1`

Gate result: `branch_path_field_bridge_v1=enriched_wire_schema_bridge_ready_no_promotion`

Purpose: build an isolated enriched Auto-Quant trade wire that carries the full `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` string at trade time. This does not select historical data, does not promote any candidate, and does not call `update_goal`.

## Result

- Input trade rows: `15415`.
- Rows enriched with full branch path fields: `15415`.
- Missing strategy mappings: `0`.
- Branch path row counts:
  - `Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72`: `10663`
  - `Sideways -> RangeConsolidation -> NQCalmVixZReversion -> NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72`: `3406`
  - `Bear -> BearMarketDrawdown -> NQHighVixOversoldRebound -> NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72`: `762`
  - `Crisis -> ExtremeStress -> NQFlushRebound -> NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72`: `584`
- CatBoost target paths absent from enriched wire: `['Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72']`.

## Layer Readback

- Pre-Bayes already contains all exact target paths: `False`.
- BBN already contains all exact target paths: `False`.
- Execution tree already contains all exact target paths: `False`.
- Workflow snapshot already contains all exact target paths: `True`.

## Decision

The Auto-Quant trade wire can be deterministically enriched from the strategy manifest for the four price-root branches that actually have trades. This repairs the wire-field shape only. It does not create Manipulation(scoped) trades, does not make Pre-Bayes or BBN consume exact branch paths, does not satisfy selected historical data, and is not promotion evidence.

## Next

Run `auto-quant-ingest-real-trades --dry-run` against this enriched wire, then apply only to an isolated copied state if the schema accepts it. Continue to Pre-Bayes/filter, BBN/analyze, CatBoost/path-ranker, and execution-tree readbacks only as a diagnostic branch-path preservation test.
