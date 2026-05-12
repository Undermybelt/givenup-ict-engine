# Auto-Quant Seeded Strategy Readback Settlement v1

## Gate

`autoquant_seeded_strategy_readback_settlement_v1=connector_patch_backtests_succeeded_profit_floor_failed_non_promoting_source_control_blocked`

## Source

- Runtime root: `/tmp/ict-engine-board-a-autoquant-seeded-strategy-readback-20260512T024111`
- Prepared Auto-Quant workspace: `/private/tmp/ict-engine-board-a-autoquant-threaded-dns-20260512T022552/auto-quant/.deps/auto-quant`
- Connector patch source: `docs/experiments/actionable-regime-confidence/runs/20260512T022552-codex-autoquant-threaded-dns-prepare-probe-v1/scripts`
- Unpatched command exit: `uv_run_run_py.exit=1`
- Connector-patch command exit: `uv_run_run_py_connector_patch.exit=0`
- Status-after exit: `auto_quant_status_after_seeded_run.exit=0`
- Settled stdout: `Done: 12 backtests succeeded, 0 failed.`

## Strategy Summary

| strategy | robust_sharpe | worst_profit_pct | profit_floor | full_5y_profit_pct | full_5y_trades | full_5y_win_rate_pct |
|---|---:|---:|---|---:|---:|---:|
| CrashRebound | 0.0847 | 2.9900 | FAIL | 55.6900 | 207 | 68.5990 |
| PerPairMR | 0.0520 | 0.8400 | FAIL | 35.7800 | 519 | 58.1888 |
| RegimeAdaptiveBNB | 0.0967 | 3.7100 | FAIL | 16.4100 | 115 | 69.5652 |

## Decision

This settlement records that the existing seeded Auto-Quant workspace can complete all 12 declared backtests when the connector patch is supplied through `PYTHONPATH`. The unpatched run still failed on exchange market loading, and every seeded strategy failed the Auto-Quant per-timerange profit-floor gate.

Promotion remains blocked. This packet does not provide source-owned `MainRegimeV2` labels, per-regime qualifying-condition packets, R6 owner/control rows, explicit `FLIP` approval, canonical source/control merge inputs, Pre-Bayes/BBN confidence `>=95%`, CatBoost/path-ranking promotion, or execution-tree actionable acceptance.

## Non-Mutations

- Runtime code changed: false
- Auto-Quant `run.py` changed: false
- Auto-Quant `config.json` changed: false
- Shared intake mutated: false
- R3/R5/R6 roots mutated: false
- Thresholds relaxed: false
- Raw data committed: false
- Trade usable: false
- `update_goal`: false
