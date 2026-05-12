# AutoQuant Threaded Resolver Strategy Run After 033625 v1

Run id: `20260511T194321-codex-autoquant-threaded-resolver-strategy-run-after-033625-v1`

Gate result: `autoquant_threaded_resolver_strategy_run_after_033625_v1=threaded_resolver_backtest_succeeded_three_strategies_diagnostic_no_source_control_no_promotion`

## Scope

This packet continues the isolated AutoQuant runtime lane after the `033625` resolver readback. It used the existing prepared workspace under `/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant/.deps/auto-quant` and the already-recorded threaded-resolver probe path. It does not mutate source/control roots, approve `FLIP` controls, accept Board A labels, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Contrast

- Default `uv run --with ta-lib run.py` failed first in `20260511T194206-codex-autoquant-prepared-strategy-run-after-033625-v1`: all 3 strategy attempts failed before backtesting because Freqtrade could not load Binance markets through the default `aiodns` path.
- Threaded run command used `PYTHONPATH=docs/experiments/actionable-regime-confidence/runs/20260512T022552-codex-autoquant-threaded-dns-prepare-probe-v1/scripts`.
- Threaded run exited `0` and reported `Done: 3 backtests succeeded, 0 failed`.

## Results

| strategy | trades | win_rate_pct | profit_pct | sharpe | sortino | max_drawdown_pct | profit_floor | min_position_size |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `BTCLeaderBreakV4` | 600 | 31.8333 | 42.4600 | 0.9415 | 4.9623 | -5.7458 | PASS | PASS |
| `MomentumMTFConfluence` | 854 | 34.7775 | 53.2400 | 0.3993 | 1.0760 | -23.1801 | PASS | PASS |
| `VolBreakoutSized` | 1221 | 32.8419 | 25.0200 | 1.3390 | 7.3012 | -4.2529 | PASS | FAIL |

## Decision

AutoQuant operation is now proven beyond prepare in this isolated runtime: seeded strategies executed and produced backtest metrics over the 5-pair 2021-2025 regime-mix dataset. This is still not Board A acceptance evidence because it is strategy diagnostics, not per-regime calibrated `>=95%` confidence, not source-owned R6/R3/R5 controls, not cross-market/cycle/timeframe label validation, and not a post-unlock downstream provider/AutoQuant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion packet.

## Next

Preserve the Current Cursor next action. Continue Board A only from verifier-native owner/export rows, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before verifier rerun, canonical merge, and downstream promotion.
