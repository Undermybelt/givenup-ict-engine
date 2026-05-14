# AutoQuant Prepared Strategy Run After 033430 v1

Run id: `20260512T034000-codex-autoquant-prepared-strategy-run-after-033430-v1`

Gate result: `autoquant_prepared_strategy_run_after_033430_v1=unshimmed_run_failed_aiodns_no_promotion`

## Scope

This packet records the first AutoQuant oracle run after the `033430` prepare-after root made the isolated workspace data-ready. It intentionally ran `uv run --with ta-lib run.py` directly from the prepared workspace. It does not mutate source roots, accept labels, approve `FLIP` rows, run canonical merge, rerun downstream promotion, or call `update_goal`.

## Readback

- Workspace: `/tmp/ict-engine-board-a-readonly-refresh-20260512T032145/auto-quant/auto-quant/.deps/auto-quant`.
- Command: `uv run --with ta-lib run.py`.
- Exit code: `1`.
- Strategies discovered: `3`.
- Backtests succeeded: `0`.
- Backtests failed: `3`.
- Failed strategies: `BTCLeaderBreakV4`, `MomentumMTFConfluence`, `VolBreakoutSized`.
- Failure class: `OperationalException` while loading Binance markets through the default `aiohttp` / `aiodns` path.

## Decision

The prepared workspace was not enough by itself for `run.py`; the same async DNS path that previously blocked prepare still blocks unshimmed backtests. This packet is useful only as contrast evidence for the later shimmed run.

Promotion status remains unchanged: accepted rows added `0`, new confidence gate false, canonical merge false, downstream provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree promotion rerun false, strict full objective false, trade usable false, and `update_goal=false`.

## Next

Use the threaded-resolver shim for AutoQuant runtime commands in this isolated state. Keep any AutoQuant runtime evidence non-promoting until source/control gates unlock and the full downstream ict-engine chain reruns.
