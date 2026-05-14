# Auto-Quant Synthetic Market Map Backtest Probe v1

Run id: `20260512T023920-codex-autoquant-synthetic-market-map-backtest-probe-v1`
Gate result: `autoquant_synthetic_market_map_backtest_probe_v1=synthetic_market_map_backtest_passed_noncanonical_no_promotion`
Board sha256 before readback registration: `85f13c62a42d509a3c0bbef781545fe460352e7b9f654aec46a3497d96c133c6`

## Inputs

- State dir: `/tmp/ict-engine-board-a-autoquant-local-crypto-cache-20260512T023351`
- Managed Auto-Quant dir: `/tmp/ict-engine-board-a-autoquant-local-crypto-cache-20260512T023351/auto-quant/.deps/auto-quant`
- Synthetic market shim: `scripts/sitecustomize.py`
- Command output: `command-output/01_auto_quant_run_synthetic_market_map.stdout.txt`

The shim is diagnostic only. It does not edit Auto-Quant runtime files or source roots; it supplies minimal spot market metadata for the five configured crypto pairs so the local cached OHLCV strategy path can be tested while Binance market metadata DNS is unavailable.

## Command Result

- `00_auto_quant_status_before.exit=0`
- `01_auto_quant_run_synthetic_market_map.exit=0`
- `02_auto_quant_status_after.exit=0`
- `run.py` completed `12` backtests with `0` failures.
- Final Auto-Quant status remained `dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, and `data_ready=true`.

## Strategy Readback

| strategy | robust_sharpe | full_profit_pct | full_trades | full_win_rate_pct | worst_timerange_profit_pct | profit_floor | min_position_size | pareto |
|---|---:|---:|---:|---:|---:|---|---|---|
| CrashRebound | 0.1516 | 40.58 | 176 | 65.3409 | 8.63 | FAIL | PASS | none |
| PerPairMR | -0.2159 | 23.97 | 287 | 64.1115 | -2.48 | FAIL | PASS | none |
| RegimeAdaptiveBNB | -0.0390 | 15.96 | 30 | 60.0000 | -0.76 | FAIL | PASS | none |

## Decision

This is useful Auto-Quant runtime evidence: the local cache plus synthetic market metadata can run the configured strategy oracle end to end. It is noncanonical and not Board A acceptance evidence because every strategy fails Auto-Quant's per-timerange profit floor, and because no source-owned `MainRegimeV2` labels, per-regime qualifying conditions, cross-market/cycle acceptance packets, R6 controls, canonical source/control merge, Pre-Bayes/BBN confidence above `95%`, CatBoost/path-ranking promotion, or execution-tree actionable acceptance were produced.

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

Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and downstream promotion. Treat this synthetic-market probe as diagnostic Auto-Quant runtime evidence only.
