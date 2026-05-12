# AutoQuant Local Cache Tomac Resolver Readback After 033216 v1

Run id: `20260512T033334-codex-autoquant-local-cache-tomac-resolver-readback-after-033216-v1`

Gate result: `autoquant_local_cache_tomac_resolver_readback_after_033216_v1=local_cache_backtest_succeeded_resolver_diagnosed_no_board_a_promotion`

Board sha256 before artifact: `0d57e17c4c9b86ac515aa39c7c2857a8657e687e8d7771ce5236ee8bf6cb8bc5`

## Scope

This packet classifies the new post-`032835` Auto-Quant evidence without editing the source run roots. It reads the raw local-cache Tomac run under `033215` and the resolver diagnostic under `033216`. It does not mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Evidence Read

- `033215` raw command output: `run_tomac.exitcode=0`; strategy `TomacNQ_KillzoneBreakout`; pair `QQQ/USD`; timeframe `1h`; informative data includes `4h`; backtest window `2024-06-13 23:00:00` to `2025-12-30 20:00:00`.
- `033215` metrics: trades `74`, win rate `52.7027%`, total profit `6.98%`, Sharpe `0.2207`, Sortino `0.3825`, Calmar `5.6268`, max drawdown `-4.2049%`, profit factor `1.2501`.
- `033216` resolver diagnostic: socket and curl reached Binance; default `aiodns` used loopback `127.0.0.1` and failed; `aiohttp` with `ThreadedResolver` reached Binance; `auto-quant-prepare` still failed without a workaround.

## Decision

`033215` proves a local Auto-Quant strategy/backtest can run from existing cache. It is not Board A acceptance evidence:

- It is one pair (`QQQ/USD`) and one primary timeframe (`1h`) with `4h` informative data, not every active regime across markets/cycles/timeframes.
- It reports strategy PnL/win-rate metrics, not calibrated regime confidence `>=95%`.
- It does not provide per-regime qualifying conditions, source-owned cross-timeframe `MainRegimeV2` exports, R6 owner/operator rows, R3 native sub-hour labels, or R5 source-panel recency extension.
- It does not run the promoted provider/Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain after source/control unlock.

`033216` narrows the Auto-Quant prepare blocker to the `aiodns` loopback resolver path and identifies a no-runtime-code workaround candidate (`ThreadedResolver` or remove/disable `aiodns` in an isolated prepare environment). This remains runtime diagnostics only while source/control gates are closed.

## Status

- Local Auto-Quant cached backtest succeeded: `true`.
- Auto-Quant prepare DNS root cause narrowed: `true`.
- Board A accepted regime confidence added: `false`.
- Source-owned normal controls acquired: `0`.
- R6 owner-export root complete: `false`.
- R3 native sub-hour source-label root complete: `false`.
- R5 source-panel recency-extension root complete: `false`.
- Canonical merge allowed: `false`.
- Downstream promotion rerun allowed: `false`.
- Strict full objective achieved: `false`.
- Trade usable: `false`.
- `update_goal=false`.

## Next

Do not promote this Auto-Quant run. Continue from source/control unlock, owner/operator verifier-native export delivery, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports. If the Auto-Quant runtime lane is reopened, test the threaded-resolver/no-`aiodns` workaround in an isolated `/tmp` state, then still require verifier/source-control unlock and the full downstream chain before Board A acceptance.
