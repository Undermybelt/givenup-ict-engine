# AutoQuant Prepared Strategy Run Threaded After 034000 v1

Run id: `20260512T034100-codex-autoquant-prepared-strategy-run-threaded-after-034000-v1`

Gate result: `autoquant_prepared_strategy_run_threaded_after_034000_v1=shimmed_run_succeeded_three_backtests_no_board_a_promotion`

## Scope

This packet reruns the AutoQuant oracle from the prepared isolated workspace with the same threaded-resolver `sitecustomize.py` shim used by the successful `033430` prepare-after root. It records runtime strategy evidence only. It does not mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Command Readback

- Workspace: `/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant/.deps/auto-quant`.
- Shim: `docs/experiments/actionable-regime-confidence/runs/20260512T022552-codex-autoquant-threaded-dns-prepare-probe-v1/scripts/sitecustomize.py`.
- Command: `PYTHONPATH=<shim-dir> uv run --with ta-lib run.py`.
- Exit code: `0`.
- Strategies discovered: `3`.
- Backtests succeeded: `3`.
- Backtests failed: `0`.

## Strategy Results

| strategy | robust_sharpe | profit % | trades | win % | profit factor | profit floor | min position | decision |
|---|---:|---:|---:|---:|---:|---|---|---|
| BTCLeaderBreakV4 | 0.9415 | 42.46 | 600 | 31.8333 | 1.7469 | PASS | PASS | runtime_only_non_promoting |
| MomentumMTFConfluence | 0.3993 | 53.24 | 854 | 34.7775 | 1.1682 | PASS | PASS | runtime_only_non_promoting |
| VolBreakoutSized | 1.3390 | 25.02 | 1221 | 32.8419 | 1.4751 | PASS | FAIL | runtime_only_non_promoting |

## Decision

This proves the prepared AutoQuant runtime can execute a seeded 5-pair crypto strategy batch when the threaded-resolver shim is applied. It still does not satisfy Board A acceptance:

- It is strategy/backtest evidence, not calibrated per-regime `>=95%` confidence.
- It does not add per-regime qualifying conditions or cross-market/cycle/timeframe source validation.
- It does not supply verifier-native R6 owner/export rows, R3 native sub-hour source labels, R5 recency-extension rows, or `FLIP` approval.
- It does not rerun filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree after source/control unlock.

Promotion status remains unchanged: accepted rows added `0`, new confidence gate false, canonical merge false, downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Keep this as AutoQuant runtime evidence. Continue only from verifier-native owner/export rows, explicit `FLIP` approval/source-owned controls, or genuinely source-owned cross-timeframe `MainRegimeV2` exports before canonical merge and full downstream promotion.
