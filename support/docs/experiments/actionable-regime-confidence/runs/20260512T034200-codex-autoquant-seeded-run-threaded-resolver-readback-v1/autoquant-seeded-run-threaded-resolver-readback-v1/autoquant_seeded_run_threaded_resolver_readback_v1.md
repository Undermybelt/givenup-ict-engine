# AutoQuant Seeded Run Threaded Resolver Readback v1

Run id: `20260512T034200-codex-autoquant-seeded-run-threaded-resolver-readback-v1`

Gate result: `autoquant_seeded_run_threaded_resolver_readback_v1=seeded_strategies_backtested_local_cache_no_source_control_no_promotion`

## Runtime Evidence

- Command exit code: `0`.
- Run success marker: `True`.
- Auto-Quant status after run: `dependency_ready_data_ready`; healthy `True`; data_ready `True`.
- Active strategies: `BTCLeaderBreakV4, MomentumMTFConfluence, VolBreakoutSized`.
- Threaded resolver shim was loaded through `PYTHONPATH`; no repo runtime code or managed Auto-Quant code was modified.

## Strategy Diagnostics

| Strategy | Sharpe | Profit % | Max DD % | Trades | Win % | PF | Robust Sharpe | Profit Floor | Position Size Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| BTCLeaderBreakV4 | 0.9415 | 42.4600 | -5.7458 | 600 | 31.8333 | 1.7469 | 0.9415 | PASS | PASS |
| MomentumMTFConfluence | 0.3993 | 53.2400 | -23.1801 | 854 | 34.7775 | 1.1682 | 0.3993 | PASS | PASS |
| VolBreakoutSized | 1.3390 | 25.0200 | -4.2529 | 1221 | 32.8419 | 1.4751 | 1.3390 | PASS | FAIL |

## Board A Decision

- This removes the immediate Auto-Quant `seed strategies` runtime blocker in the isolated cache and proves the seeded local run path can execute under the threaded resolver shim.
- It does not satisfy Board A promotion: R6 owner/export root, R3 native-subhour source-label root, and R5 source-panel recency-extension root are still absent.
- It is not per-regime calibrated `>=95%` confidence, not per-regime qualifying-condition evidence, and not cross-market/cycle/timeframe validation for the current source/control objective.
- Accepted rows added `0`; new confidence gate `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Next

Preserve the Current Cursor next action: obtain verifier-native R6 owner/export rows or explicit `FLIP` control approval, then rerun verifier, split calibration, provider/Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranking, and execution tree. Keep R5 and R3 blocked until their source roots arrive.
