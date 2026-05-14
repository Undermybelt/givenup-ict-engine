# AutoQuant Threaded Resolver Run Settlement After 042222 v1

Run id: `20260512T042900-codex-autoquant-threaded-resolver-run-settlement-after-042222-v1`

Gate result: `autoquant_threaded_resolver_run_settlement_after_042222_v1=runtime_succeeded_strategy_quality_not_promoting_source_roots_absent`

## Result

- Source command-output root: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1`
- New command: `command-output/05_autoquant_run_threaded_resolver.cmd`
- New exit: `0`
- AutoQuant runtime status changed from the earlier `042222/042603` failed-run readback to a successful threaded-resolver run: `3` backtests succeeded and `0` failed.
- This is AutoQuant runtime evidence only. It is not accepted `>=95%` regime-confidence evidence, not source/control evidence, not canonical merge input, not downstream promotion evidence, and not trade evidence.

## Strategy Readback

| Strategy | Trades | Win rate % | Profit % | Sharpe | Profit factor | Gate |
|---|---:|---:|---:|---:|---:|---|
| `BTCLeaderBreakV4BTCOnly` | 116 | 35.3448 | 14.8100 | 0.2464 | 2.3460 | `profit_floor_fail` |
| `MTFTrendStackBTCOnly` | 150 | 22.0000 | -4.2700 | -0.0796 | 0.8513 | `profit_floor_fail` |
| `MomentumMTFConfluenceBTCOnly` | 169 | 30.7692 | 2.8600 | 0.0411 | 1.0709 | `profit_floor_fail` |

The run proves the local-cache AutoQuant workspace can execute with the threaded resolver and local data. It does not satisfy Board A because source/control gates remain absent and no accepted regime-confidence packet was produced.

## Promotion Status

- Accepted rows added: `0`
- Source/control evidence acquired: `false`
- New confidence gate: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- Command: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.cmd`
- Stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.stdout.txt`
- Stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.stderr.txt`
- Exit: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.exit`
- Settlement JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T042900-codex-autoquant-threaded-resolver-run-settlement-after-042222-v1/autoquant-threaded-resolver-run-settlement-after-042222-v1/autoquant_threaded_resolver_run_settlement_after_042222_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T042900-codex-autoquant-threaded-resolver-run-settlement-after-042222-v1/checks/autoquant_threaded_resolver_run_settlement_after_042222_v1_assertions.out`

## Next

Preserve the Current Cursor next action. Continue only after explicit approval, verifier-native R6 owner/export rows plus source-owned broad normal controls, source-owned R5 recency-extension rows, native sub-hour source-label rows, or genuinely source-owned cross-timeframe `MainRegimeV2` exports unlock the relevant target root. Then rerun direct verifier, split calibration, canonical merge, provider/AutoQuant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution-tree readback in order.
