# AutoQuant Local Cache Run Readback After 042222 v1

Run id: `20260512T042603-codex-autoquant-local-cache-run-readback-after-042222-v1`

Gate result: `autoquant_local_cache_run_readback_after_042222_v1=data_ready_but_backtests_failed_market_loading_no_promotion`

## Scope

Readback over `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1` without editing that source root. This packet only records AutoQuant readiness and execution failure status after the latest source-confidence and source-target scans.

## Evidence

- AutoQuant status before and after the run was `dependency_ready_data_ready`; dependency health `true`, data readiness `true`, bootstrap needed `false`.
- Managed workspace: `/tmp/ict-engine-board-a-autoquant-local-cache-20260512T022826/auto-quant/.deps/auto-quant`.
- Direct `run.py` invocation exited `1` with `ModuleNotFoundError: No module named 'pandas'`.
- `uv --directory` run exited `1`, discovered `3` strategies (`BTCLeaderBreakV4BTCOnly`, `MTFTrendStackBTCOnly`, `MomentumMTFConfluenceBTCOnly`), and completed `0` successful backtests / `3` failed backtests.
- The decisive `uv --directory` blocker was Freqtrade/Binance market loading: `Could not load markets`, with DNS failure contacting `api.binance.com`.
- Required target roots were still absent at the fresh board readback: `/tmp/ict-engine-board-a-r6-owner-export-v1`, `/tmp/ict-engine-native-subhour-source-label-intake`, and `/tmp/ict-engine-source-panel-recency-extension`.

## Decision

AutoQuant local-cache data readiness is real readiness evidence, but not a successful AutoQuant backtest and not Board A promotion evidence. The run does not create accepted regime confidence, source/control evidence, canonical merge input, downstream promotion evidence, trade evidence, or `update_goal` authorization.

Promotion status remains unchanged: accepted rows added `0`, new confidence gate `false`, source/control evidence acquired `false`, canonical merge `false`, downstream promotion rerun `false`, strict full objective `false`, trade usable `false`, and `update_goal=false`.

## Next

Preserve the Current Cursor next action. Continue only after source/control unlock or explicit approval; if AutoQuant is retried before that, use an offline/reachable market metadata path or exchange config that does not require live Binance DNS, and keep the result non-promoting until the source/control gates pass.
