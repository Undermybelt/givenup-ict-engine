# AutoQuant Run Readback After Data Ready v1

Run id: `20260512T070031+0800-codex-autoquant-run-readback-after-data-ready-v1`

Gate result: `autoquant_run_readback_after_data_ready_v1=data_ready_prepare_ok_run_market_load_blocked_no_source_control_unlock_no_downstream`

## Scope

Read-only consolidation of the recent Auto-Quant runtime roots after the local-cache/data-ready work:

- `docs/experiments/actionable-regime-confidence/runs/20260512T065652+0800-codex-autoquant-threaded-dns-prepare-after-065116-v1`
- `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1`
- `docs/experiments/actionable-regime-confidence/runs/20260512T065824+0800-codex-autoquant-local-run-readback-after-065116-v1`

This packet does not rerun Auto-Quant, mutate Auto-Quant code, mutate R3/R5/R6 target roots, run direct verifier, run canonical merge, run filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion, make a trade claim, or call `update_goal`.

## Runtime Readback

| Root | Command surface | Result | Decision |
|---|---|---|---|
| `065652` | `auto-quant-prepare --state-dir /tmp/ict-engine-board-a-064259-runtime-v1` with run-local aiohttp threaded resolver shim | Exit `0`; final status `dependency_ready_data_ready`, `healthy=true`, `data_ready=true` | Auto-Quant prepare/data readiness can be made healthy, but this is runtime-only. |
| `065613` | cache-seeded Auto-Quant run over three strategies and four timeranges | `auto_quant_run_after_cache.exit=1`; `auto_quant_run_threaded_resolver_after_cache.exit=1`; stdout ends `Done: 0 backtests succeeded, 12 failed` | Selected local run still fails at Binance/Freqtrade market loading. |
| `065824` | `/tmp/ict-engine-board-a-064259-runtime-v1` Auto-Quant run readback | status exits `0`; `04_autoquant_run_064259_state.exit=1`; stdout ends `Done: 0 backtests succeeded, 1 failed` | Managed state is data-ready, but the actual run fails market loading. |
| `065822` | `source-control-provider-refresh-after-065506-v1` placeholder directory | Directory exists with only `scripts/`, no report/JSON/assertions observed | Do not count as evidence. |

## Failure Shape

Visible Auto-Quant run failures are runtime/exchange-market-loading failures, not source/control unlocks:

- `065824` discovered `1` strategy: `TomacNQ_KillzoneBreakout`.
- `065613` discovered `3` strategies: `CrashRebound`, `PerPairMR`, `RegimeAdaptiveBNB`.
- Both run surfaces failed with Freqtrade `OperationalException: Could not load markets`.
- The stderr path remains `ExchangeNotAvailable` for `binance GET https://api.binance.com/api/v3/exchangeInfo` with DNS/market-load failures.
- No successful backtest rows were produced by these roots.

## Gate

- Auto-Quant data ready: `true` for `/tmp/ict-engine-board-a-064259-runtime-v1`
- Auto-Quant prepare healthy: `true` when using the run-local threaded resolver patch
- Auto-Quant selected run success: `false`
- Successful backtests: `0`
- R6 owner/export unlock: `false`
- R5 recency unlock: `false`
- R3 native-subhour unlock: `false`
- Valid required-root unlock: `false`
- Source/control evidence acquired: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Next

Keep Auto-Quant as runtime-ready but not promotion-ready. Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned post-`2026-01-30` R5 recency rows, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before running direct verifier, split calibration, canonical merge, provider/AutoQuant selected-data research, filter/Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
