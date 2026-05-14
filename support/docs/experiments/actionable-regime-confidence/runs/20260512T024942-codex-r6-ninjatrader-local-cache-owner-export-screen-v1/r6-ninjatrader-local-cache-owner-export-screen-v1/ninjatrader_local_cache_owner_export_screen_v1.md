# R6 NinjaTrader Local Cache Owner-Export Screen v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1`

Gate result: `r6_ninjatrader_local_cache_owner_export_screen_v1=non_promoting_local_last_cache_no_owner_export_no_order_lifecycle_no_depth_controls`

## Screened Source

- Local NinjaTrader DB root: `/Users/thrill3r/Documents/NinjaTrader 8/db`
- SQLite file: `/Users/thrill3r/Documents/NinjaTrader 8/db/NinjaTrader.sqlite`
- Owner/export root required by the current cursor: `/tmp/ict-engine-board-a-r6-owner-export-v1`
- Owner/export root present: `False`
- Board SHA-256 before artifact write: `7e45c103115a05f165bd4e878a0099f54740c87e026837db2ab8ca39f665b85d`

## Findings

- `Orders`, `OrderUpdates`, `Executions`, `Positions`, and `User2MarketDataEntitlement` all have `0` rows.
- Local market cache has `2440` `.ncd` files and `13` `.ntb` descriptors.
- `.ncd` cache type summary: `Last`.
- No `.ncd` filename indicates MarketDepth, depth, bid, ask, MBO, book, or order-lifecycle payloads.
- `.ntb` descriptors extract as `MarketDataType=Last`; `BidAsk` appears only as a volumetric build setting in descriptor XML, not as source-owned depth/order-lifecycle rows.

## Decision

This is local chart/bar/tick cache evidence only. It is not a source-owned R6 owner export, does not provide matched normal controls, does not create source-owned `MainRegimeV2` labels, and cannot be merged into canonical intake.

Promotion status remains unchanged: accepted rows added `0`, new confidence gate false, canonical merge false, downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun false, strict full objective false, and `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/r6-ninjatrader-local-cache-owner-export-screen-v1/ninjatrader_local_cache_owner_export_screen_v1.json`
- Table counts: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/r6-ninjatrader-local-cache-owner-export-screen-v1/ninjatrader_sqlite_table_counts_v1.csv`
- Order-lifecycle schema: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/r6-ninjatrader-local-cache-owner-export-screen-v1/ninjatrader_order_lifecycle_schema_v1.csv`
- Cache inventory: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/r6-ninjatrader-local-cache-owner-export-screen-v1/ninjatrader_cache_inventory_v1.csv`
- NTB descriptor summary: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/r6-ninjatrader-local-cache-owner-export-screen-v1/ninjatrader_ntb_descriptor_summary_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T024942-codex-r6-ninjatrader-local-cache-owner-export-screen-v1/checks/ninjatrader_local_cache_owner_export_screen_v1_assertions.out`

## Next

Preserve the Current Cursor next action for R6. Continue only from owner/operator CME/Cboe/CFE export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
