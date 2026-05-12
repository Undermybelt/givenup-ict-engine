# Auto-Quant Local Tomac Readback v1

Run id: `20260512T022923-codex-autoquant-local-tomac-readback-v1`

Gate result: `autoquant_local_tomac_readback_v1=local_freqtrade_backtest_succeeded_non_promoting_single_pair_single_strategy`

## Command

`cd /Users/thrill3r/Auto-Quant && uv run python run_tomac.py`

Exit: `0`

## Result

- Strategy: `TomacNQ_KillzoneBreakout`
- Config: `config.tomac.json`
- Pair: `QQQ/USD`
- Trades: `74`
- Total profit %: `6.98`
- Win rate %: `52.7027`
- Sharpe: `0.2207`
- Sortino: `0.3825`
- Calmar: `5.6268`
- Max drawdown %: `-4.2049`
- Profit factor: `1.2501`
- Backtest window: `2024-06-13 23:00:00` to `2025-12-30 20:00:00`

## Interpretation

This proves the local/offline Auto-Quant Tomac harness can run through FreqTrade without repeating the Binance DNS-dependent prepare path.

It is non-promoting Board A evidence because it is one strategy, one configured pair, and FreqTrade reported large missing-data fillups. It is not connected to source-owned `MainRegimeV2` labels, R6 owner/control rows, canonical merge, or the full downstream promotion chain.

## Data Warnings

- `2026-05-12 02:28:06,263 - freqtrade.data.history.datahandlers.idatahandler - WARNING - QQQ/USD, spot, 1h, data starts at 2024-06-03 13:00:00`
- `2026-05-12 02:28:06,753 - freqtrade.data.converter.converter - INFO - Missing data fillup for QQQ/USD, 1h: before: 2754 - after: 13808 - 401.38%`
- `2026-05-12 02:28:10,042 - freqtrade.data.history.datahandlers.idatahandler - WARNING - QQQ/USD, spot, 4h, data starts at 2024-06-03 12:00:00`
- `2026-05-12 02:28:10,147 - freqtrade.data.converter.converter - INFO - Missing data fillup for QQQ/USD, 4h: before: 912 - after: 3453 - 278.62%`

## Non-Mutation

Runtime code changed: false. Shared intake mutated: false. R3/R5/R6 roots mutated: false. Raw data committed: false. `update_goal=false`.
