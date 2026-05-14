# AutoQuant Prepared Seeded Run After 033625 v1

Run id: `20260512T034031-codex-autoquant-prepared-seeded-run-after-033625-v1`

Gate result: `autoquant_prepared_seeded_run_after_033625_v1=threaded_run_succeeded_three_strategies_runtime_only_no_source_control_no_promotion`

## Scope

This packet executes the prepared Auto-Quant oracle in the isolated managed workspace after the `033430` threaded-resolver prepare and `033625` readback. It records runtime evidence only. It does not mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Command Readback

- Status before run exited `0`: `dependency_ready_data_ready`, `healthy=true`, `data_ready=true`.
- Active strategy files existed: `BTCLeaderBreakV4.py`, `MomentumMTFConfluence.py`, `VolBreakoutSized.py`.
- Unpatched `uv run --with ta-lib run.py` exited `1`; all three strategies failed at Binance market loading through the `aiodns` loopback path.
- Patched `PYTHONPATH=<threaded-resolver-shim> uv run --with ta-lib run.py` exited `0`; all three strategies backtested successfully.
- Status after patched run exited `0`: `dependency_ready_data_ready`, `healthy=true`, `data_ready=true`.

## Strategy Readback

| Strategy | Robust Sharpe | Total Profit % | Max DD % | Trades | Win Rate % | Profit Factor | Gates |
|---|---:|---:|---:|---:|---:|---:|---|
| `BTCLeaderBreakV4` | `0.9415` | `42.46` | `-5.7458` | `600` | `31.8333` | `1.7469` | profit floor pass; min position pass; non-dominated |
| `MomentumMTFConfluence` | `0.3993` | `53.24` | `-23.1801` | `854` | `34.7775` | `1.1682` | profit floor pass; min position pass; non-dominated |
| `VolBreakoutSized` | `1.3390` | `25.02` | `-4.2529` | `1221` | `32.8419` | `1.4751` | profit floor pass; min position fail; non-dominated |

## Decision

This is real Auto-Quant runtime evidence: data is prepared, strategies are seeded, and the oracle can run through the threaded-resolver shim. It is not Board A completion evidence:

- It is strategy/backtest performance, not calibrated regime confidence `>=95%`.
- It does not provide per-regime qualifying conditions.
- It does not validate every active regime across other markets, cycles, and timeframes.
- It does not provide R6 owner/export controls, R3 native sub-hour labels, or R5 recency-extension rows.
- It does not unlock filter/Pre-Bayes/BBN, CatBoost/path-ranking, or execution-tree promotion because source/control gates and canonical merge remain false.

Promotion status: accepted rows added `0`, new confidence gate false, canonical merge false, downstream promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only from verifier-native owner/export rows, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before verifier rerun, canonical merge, and downstream promotion.
