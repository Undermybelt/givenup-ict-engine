# AutoQuant Seeded Threaded Run Settlement After 033430 v1

Run id: `20260512T034423-codex-autoquant-seeded-threaded-run-settlement-after-033430-v1`

Gate result: `autoquant_seeded_threaded_run_settlement_after_033430_v1=seeded_threaded_backtests_succeeded_runtime_only_source_controls_absent_no_promotion`

Generated at UTC: `2026-05-11T19:44:23Z`

Board sha256 before artifact: `3d01441f635d2e17f848d55a969d6a2e9c5ff6954b0cc773f3b61546bea458dc`

## Scope

This packet classifies the settled seeded Auto-Quant run already captured in the `033430` command-output root. It reads command output only and does not rerun Auto-Quant, mutate source roots, edit ict-engine runtime code, edit the managed Auto-Quant checkout, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

Source command output:

- `docs/experiments/actionable-regime-confidence/runs/20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1/command-output/auto_quant_run_seeded_strategies_threaded_resolver.stdout.txt`
- `docs/experiments/actionable-regime-confidence/runs/20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1/command-output/auto_quant_run_seeded_strategies_threaded_resolver.stderr.txt`
- `docs/experiments/actionable-regime-confidence/runs/20260512T033430-codex-autoquant-threaded-resolver-workaround-run-v1/command-output/auto_quant_run_seeded_strategies_threaded_resolver.exit`

## Evidence Read

- Threaded-resolver seeded run exit: `0`.
- Completion line: `Done: 3 backtests succeeded, 0 failed.`
- Prepared workspace: `/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant/.deps/auto-quant`.
- Strategy set: `BTCLeaderBreakV4`, `MomentumMTFConfluence`, and `VolBreakoutSized`.
- Pair basket: `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, and `AVAX/USDT`.
- Timerange: `20210101-20251231`.
- Auto-Quant commit: `34ba6b6`.

## Strategy Readback

| Strategy | Robust Sharpe | Worst Profit % | Worst Drawdown % | Avg Position % | Trades | Win Rate % | Profit Floor | Min Position Size |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `BTCLeaderBreakV4` | `0.9415` | `42.4600` | `-5.7458` | `6.9583` | `600` | `31.8333` | `PASS` | `PASS` |
| `MomentumMTFConfluence` | `0.3993` | `53.2400` | `-23.1801` | `21.5841` | `854` | `34.8` | `PASS` | `PASS` |
| `VolBreakoutSized` | `1.3390` | `25.0200` | `-4.2529` | `3.6641` | `1221` | `32.8419` | `PASS` | `FAIL` |

## Decision

The seeded threaded Auto-Quant run is real runtime evidence: three active strategies executed over the prepared 2021-2025 crypto workspace and completed successfully under the threaded resolver shim.

It remains non-promoting for Board A:

- The run measures strategy/backtest performance, not calibrated `MainRegimeV2` regime confidence.
- The three required source/control roots remained absent before this settlement: `/tmp/ict-engine-board-a-r6-owner-export-v1`, `/tmp/ict-engine-native-subhour-source-label-intake`, and `/tmp/ict-engine-source-panel-recency-extension`.
- The approval package remains non-approving: `approval_present=false`, `flip_controls_accepted_under_current_contract=false`, `canonical_merge_allowed_now=false`, `downstream_rerun_allowed_now=false`, `strict_full_objective_achieved=false`, `trade_usable=false`, and `update_goal=false`.
- No direct verifier, canonical merge, split calibration, Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion rerun is allowed while source/control gates remain closed.

## Status

- Auto-Quant seeded threaded backtests succeeded: `true`.
- Source/control evidence acquired: `false`.
- Accepted rows added: `0`.
- New confidence gate: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Do not repeat the same Auto-Quant seeded run. Continue only from verifier-native owner/export rows, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before verifier rerun, canonical merge, and downstream promotion.
