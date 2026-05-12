# AutoQuant Local Cache Tomac Readback After 032835 v1

Run id: `20260512T033215-codex-autoquant-local-cache-tomac-readback-after-032835-v1`

Gate result: `autoquant_local_cache_tomac_readback_after_032835_v1=local_cache_backtest_succeeded_single_pair_no_regime_confidence_no_promotion`

## Scope

This packet records a local Auto-Quant/Freqtrade cache readback for `TomacNQ_KillzoneBreakout` after the `032835` current-objective audit. It is a strategy/runtime diagnostic only. It does not mutate source roots, acquire owner-export controls, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream provider/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion, or call `update_goal`.

## Command Readback

- Exit code: `0`.
- Strategy: `TomacNQ_KillzoneBreakout`.
- Auto-Quant commit shown by output: `34ba6b6`.
- Config shown by output: `config.tomac.json`.
- Pair: `QQQ/USD`.
- Timeframe shown by resolver/config: `1h`.
- Backtest window: `2024-06-13 23:00:00` to `2025-12-30 20:00:00`.
- Trades: `74`.
- Win rate: `52.7027%`.
- Total profit: `6.98%`.
- Sharpe: `0.2207`.
- Sortino: `0.3825`.
- Calmar: `5.6268`.
- Profit factor: `1.2501`.
- Max drawdown: `-4.2049%`.
- Data-quality warnings: missing-data fillup reported for `QQQ/USD` `1h` (`401.38%`) and `4h` (`278.62%`).

## Decision

- Runtime command succeeded: `true`.
- Local cache strategy diagnostic: `true`.
- Source/control evidence acquired: `false`.
- Owner/export rows acquired: `false`.
- `FLIP` approval acquired: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Preserve the Current Cursor next action. Treat this as Auto-Quant local-cache strategy diagnostics only. Do not promote it without source/control unlock, verifier rerun, split calibration, and the full downstream provider/Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain.
