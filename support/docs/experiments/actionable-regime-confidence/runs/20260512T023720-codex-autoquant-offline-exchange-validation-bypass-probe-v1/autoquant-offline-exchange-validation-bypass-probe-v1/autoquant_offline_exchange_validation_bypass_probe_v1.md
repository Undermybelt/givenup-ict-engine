# Auto-Quant Offline Exchange Validation Bypass Probe v1

Run id: `20260512T023720-codex-autoquant-offline-exchange-validation-bypass-probe-v1`

Gate result: `autoquant_offline_exchange_validation_bypass_probe_v1=validation_bypass_still_markets_not_loaded_no_promotion`

Board sha256 before artifact: `b23942d664ded202243f52823ce7dca4d5ba2164e6986da32de65a60d16c7149`

## Scope

- Reused the isolated local-crypto-cache Auto-Quant state from `20260512T023351-codex-autoquant-local-crypto-cache-backtest-smoke-v1`.
- Added a diagnostic `sitecustomize.py` shim only through `PYTHONPATH`; Auto-Quant `run.py` and `config.json` were not edited.
- The shim forced Freqtrade `ExchangeResolver.load_exchange(..., validate=False, load_leverage_tiers=False)` to test whether removing startup exchange validation was enough for offline local-data backtests.

## Command

Command:

`env PYTHONUNBUFFERED=1 PYTHONPATH=docs/experiments/actionable-regime-confidence/runs/20260512T023720-codex-autoquant-offline-exchange-validation-bypass-probe-v1/scripts uv --directory /tmp/ict-engine-board-a-autoquant-local-crypto-cache-20260512T023351/auto-quant/.deps/auto-quant run --with ta-lib python run.py`

Exits:

- `00_auto_quant_status_before.exit=0`
- `01_auto_quant_run_offline_exchange_validation_bypass.exit=1`
- `02_auto_quant_status_after.exit=0`

## Result

- Status after the run remained `dependency_ready_data_ready`, with `healthy=true`, `dependency_healthy=true`, `data_ready=true`, and `bootstrap_needed=false`.
- The bypass did not unlock local backtests. Auto-Quant stdout reported `0` successful backtests and `12` failed backtests.
- The repeated failure changed from startup validation to pairlist/market access: `OperationalException: Markets were not loaded.`
- Stderr still traced the underlying market metadata path to Binance `exchangeInfo` DNS failure ending in `Could not contact DNS servers`.
- This is a negative diagnostic probe only. It does not supersede the successful `023312` seeded run, and it does not create accepted Board A evidence.

## Decision

- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- `update_goal=false`.

Runtime code changed: `false`.
Shared intake mutated: `false`.
R3/R5/R6 roots mutated: `false`.
Thresholds relaxed: `false`.
Raw data committed: `false`.
Trade usable: `false`.

## Next

Preserve the Current Cursor next action for R6. Continue from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion.
