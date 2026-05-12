# Auto-Quant Local Crypto Cache Backtest Smoke v1

Run id: `20260512T023351-codex-autoquant-local-crypto-cache-backtest-smoke-v1`

Gate result: `autoquant_local_crypto_cache_backtest_smoke_v1=strategies_and_data_ready_run_blocked_by_market_metadata_dns_no_promotion`

## Inputs

- State dir: `/tmp/ict-engine-board-a-autoquant-local-crypto-cache-20260512T023351`
- Managed Auto-Quant dir: `/tmp/ict-engine-board-a-autoquant-local-crypto-cache-20260512T023351/auto-quant/.deps/auto-quant`
- Local Auto-Quant source: `/Users/thrill3r/Auto-Quant`
- Managed commit: `34ba6b6ee6aa69813a50a72158d4c089d97afb96`
- Data copied into the isolated managed workspace: `15` crypto feather files for `BTC`, `ETH`, `SOL`, `BNB`, and `AVAX` across `1h`, `4h`, and `1d`
- Active strategy files present in the isolated managed workspace: `CrashRebound.py`, `PerPairMR.py`, `RegimeAdaptiveBNB.py`

## Command Results

- `00_auto_quant_status_before`: exit `0`
- `01_auto_quant_bootstrap_local`: exit `0`
- `02_auto_quant_status_after_seed`: exit `0`
- `03_auto_quant_run`: exit `1`
- `04_auto_quant_status_after_run`: exit `0`

Status after seeding was `dependency_ready_data_ready`, with `healthy=true`, `dependency_healthy=true`, `data_ready=true`, and `bootstrap_needed=false`.

`run.py` discovered `3` strategies and attempted the fixed crypto whitelist `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, and `AVAX/USDT`. It reported `0` successful backtests and `12` failed backtests.

The repeated failure was `OperationalException: Could not load markets`. The stderr trace resolves the blocker to Binance market metadata loading through `api.binance.com/api/v3/exchangeInfo`, ending in `Could not contact DNS servers`.

## Decision

This proves the isolated managed Auto-Quant workspace can be bootstrapped, can receive active strategies, and can be made data-ready from local crypto cache files. It does not prove a successful Auto-Quant backtest or Board A promotion path.

Accepted rows added: `0`.
New confidence gate: `false`.
Canonical merge allowed: `false`.
Downstream provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion rerun allowed: `false`.
Strict full objective achieved: `false`.
`update_goal=false`.

Runtime code changed: `false`.
Shared intake mutated: `false`.
R3/R5/R6 roots mutated: `false`.
Thresholds relaxed: `false`.
Raw data committed: `false`.
Trade usable: `false`.

## Next

Preserve the Current Cursor next action for R6. Auto-Quant is no longer blocked by missing local strategy/data files in this isolated smoke root, but the run still fails closed on exchange metadata DNS and remains non-promoting until source-owned controls, explicit `FLIP` approval or accepted cross-timeframe `MainRegimeV2` exports are canonically merged.
