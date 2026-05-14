# Readonly Runtime Refresh After 062604 v1

Run id: `20260512T062854+0800-codex-readonly-runtime-refresh-after-062604-v1`

## Decision

`readonly_runtime_refresh_after_062604_v1=runtime_surfaces_called_no_required_root_no_promotion`

Runtime surfaces were called, but this is non-promoting because the required source/control roots remain absent.

## Surface Readback

- Provider status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- yfinance ready: `true`; Kraken CLI ready: `true`; IBKR market-data ready: `false`.
- Auto-Quant checked state: `missing_dependency`; fresh state: `missing_dependency`.
- analyze-live: `Observe only`, direction `Bull`, pre-Bayes `pass_neutralized`, execution gate `observe`.
- Pre-Bayes post-analyze: `pass_neutralized`, structural regime `range`, confidence `0.573271485537414`.
- Workflow post-analyze: `blocked` / `user_selected_historical_data_missing`.
- Policy/CatBoost rows: `cisd=0`, `breaker=0`.
- Path-ranking export: rows `3`, mature rows `0`, calibrated rows `0`.

## Required Roots

- `/tmp/ict-engine-board-a-r6-owner-export-v1`: `false`
- `/tmp/ict-engine-native-subhour-source-label-intake`: `false`
- `/tmp/ict-engine-source-panel-recency-extension`: `false`

## Accounting

- Canonical merge: `false`.
- Downstream promotion rerun: `false`.
- Strict full objective: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Keep this as read-only runtime evidence. Do not promote until one required source/control root unlocks; then rerun direct verifier, split calibration, canonical merge, providers, AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
