# AutoQuant Local Cache Tomac Settlement After 065613 v1

Run id: `20260512T070059+0800-codex-autoquant-local-cache-tomac-settlement-after-065613-v1`

Gate result: `autoquant_local_cache_tomac_settlement_after_065613_v1=tomac_backtest_succeeded_runtime_only_source_control_unlock_absent_no_promotion`

## Scope

This settlement reads the settled `065613` Auto-Quant local-cache command outputs after the local-cache data-ready run, the default seeded-strategy run, the threaded-resolver retry, and the Tomac-specific offline run. It does not mutate R3/R5/R6 target roots, approve source/control evidence, run canonical merge, run filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion, make a trade claim, or call `update_goal`.

## Readback

- Local-cache bootstrap/status/prepare exited `0`; Auto-Quant status was `dependency_ready_data_ready`, `healthy=true`, `data_ready=true`.
- Default local-cache run exited `1`: `12` attempted strategy/timerange backtests all returned `ERROR` because Freqtrade/CCXT could not load Binance markets.
- Threaded-resolver retry exited `1`: `12` attempted strategy/timerange backtests all returned `ERROR` with the same market-loading failure.
- Tomac-specific run exited `0` using `run_tomac.py`: `TomacNQ_KillzoneBreakout` on `QQQ/USD` `1h` produced `74` trades, `52.7027%` win rate, `6.98%` total profit, `Sharpe 0.2207`, `Profit factor 1.2501`, and max drawdown `-4.2049%`.

## Decision

The Tomac run proves the local-cache Auto-Quant runtime can execute one local Freqtrade backtest from the seeded isolated workspace. It is still not Board A promotion evidence: it is single-pair strategy output, not per-regime `MainRegimeV2` confidence calibration, not source-owned R5/R3 labels, not R6 owner/export controls, and not a post-unlock downstream chain run.

Accounting: accepted rows added `0`, valid required-root unlock false, source/control evidence acquired false, canonical merge false, provider/AutoQuant promotion false, filter / Pre-Bayes / BBN / CatBoost / execution-tree promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Artifacts

- Source command root: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/`
- Local-cache status: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/auto_quant_status_after_cache.stdout`
- Default run output: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/auto_quant_run_after_cache.stdout`
- Threaded-resolver run output: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/auto_quant_run_threaded_resolver_after_cache.stdout`
- Tomac run output: `docs/experiments/actionable-regime-confidence/runs/20260512T065613+0800-codex-autoquant-local-cache-data-ready-after-065116-v1/command-output/auto_quant_run_tomac_after_cache.stdout`
- Settlement JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T070059+0800-codex-autoquant-local-cache-tomac-settlement-after-065613-v1/autoquant-local-cache-tomac-settlement-after-065613-v1/autoquant_local_cache_tomac_settlement_after_065613_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T070059+0800-codex-autoquant-local-cache-tomac-settlement-after-065613-v1/checks/autoquant_local_cache_tomac_settlement_after_065613_v1_assertions.out`

## Next

Continue only from explicit source/control approval, verifier-native R6 owner-export rows with valid controls, source-owned R5 post-`2026-01-30` rows matching the source-panel schema, verifier-native Crisis-capable R3 `MainRegimeV2` labels, or a genuinely new accepted cross-timeframe `MainRegimeV2` source export before direct verifier, split calibration, canonical merge, provider/AutoQuant promotion, filter / Pre-Bayes, BBN, CatBoost/path-ranking, or execution-tree promotion.
