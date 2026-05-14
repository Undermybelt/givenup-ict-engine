# 034121 AutoQuant Seeded Threaded Run After 033625

Generated: 2026-05-11T19:48:32Z

Gate result: `autoquant_seeded_threaded_run_after_033625_v1=seeded_threaded_backtests_succeeded_duplicate_runtime_only_source_controls_absent_no_promotion`

This packet artifactizes the already captured `034121` raw command output. It is AutoQuant runtime evidence only. It does not add source/control evidence, regime-confidence labels, accepted rows, canonical merge input, downstream promotion evidence, or trade-usable Board A evidence.

## Command Evidence

- Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T034121-codex-autoquant-seeded-threaded-run-after-033625-v1`
- Stdout: `command-output/auto_quant_seeded_threaded_run.stdout.txt`
- Stderr: `command-output/auto_quant_seeded_threaded_run.stderr.txt`
- Exit code: `command-output/auto_quant_seeded_threaded_run.exitcode`
- Exit code observed: `0`
- Completion line: `Done: 3 backtests succeeded, 0 failed.`
- Prepared workspace: `/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant/.deps/auto-quant`
- Workspace commit reported by AutoQuant output: `34ba6b6`
- Timerange: `20210101-20251231`
- Basket: `BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT,AVAX/USDT`

## Strategy Readback

| Strategy | Robust Sharpe | Total Profit % | Worst DD % | Trades | Win Rate % | Profit Factor | Profit Floor | Min Position Size |
|---|---:|---:|---:|---:|---:|---:|---|---|
| BTCLeaderBreakV4 | 0.9415 | 42.46 | -5.7458 | 600 | 31.8333 | 1.7469 | PASS | PASS |
| MomentumMTFConfluence | 0.3993 | 53.24 | -23.1801 | 854 | 34.7775 | 1.1682 | PASS | PASS |
| VolBreakoutSized | 1.3390 | 25.02 | -4.2529 | 1221 | 32.8419 | 1.4751 | PASS | FAIL |

## Stderr Readback

The command stderr includes Freqtrade/CCXT lifecycle cleanup warnings after data loading and backtests:

- `Exchange.__del__` attempted `self.close()` after the event loop was closed.
- `RuntimeWarning: coroutine 'Exchange.close' was never awaited`.
- Binance/CCXT warned that async exchange resources should be explicitly closed.
- `asyncio` reported unclosed connectors.

These warnings do not change the captured command exit (`0`) or stdout completion line, but they keep this packet diagnostic-only.

## Board A Promotion Audit

- Source/control evidence acquired: `false`
- R6 owner-export root present: `false`
- R3 native-subhour source-label root present: `false`
- R5 recency-extension root present: `false`
- Approval present: `false`
- `FLIP` controls accepted under current contract: `false`
- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- Trade usable: `false`
- `update_goal`: `false`

## Counting Rule

Count this `034121` packet once as duplicate/runtime readback against the same prepared `/tmp` AutoQuant workspace already summarized by the `034423` settlement. Do not count it as a separate source/control packet, accepted regime-confidence packet, canonical merge input, downstream promotion rerun, or trade evidence.

Next action remains unchanged: continue only from verifier-native owner/export rows, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before verifier rerun, canonical merge, and downstream promotion.
