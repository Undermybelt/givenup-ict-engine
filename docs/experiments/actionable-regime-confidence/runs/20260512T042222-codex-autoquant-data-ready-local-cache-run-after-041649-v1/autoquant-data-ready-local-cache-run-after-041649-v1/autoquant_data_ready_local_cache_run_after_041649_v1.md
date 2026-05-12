# AutoQuant Data-Ready Local Cache Run After 041649 v1

Run id: `20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1`

Gate result: `autoquant_data_ready_local_cache_run_after_041649_v1=threaded_resolver_run_succeeded_three_backtests_no_board_a_promotion`

## Result

- `auto-quant-status` before and after the run exited `0` with status `dependency_ready_data_ready`, dependency healthy `true`, and data ready `true`.
- Plain `run.py` exited `1` because the ambient interpreter lacked `pandas`.
- `uv --directory ... run --with ta-lib run.py` exited `1`; all three attempted backtests failed with `OperationalException` because Binance market loading could not reach `api.binance.com` DNS/market metadata.
- The bounded threaded-resolver retry loaded `sitecustomize.py`, exited `0`, and completed `3` backtests with `0` failed.
- Strategy readback:
  - `BTCLeaderBreakV4BTCOnly`: robust Sharpe `0.2464`, total profit `14.81%`, trades `116`, win rate `35.3448%`, profit factor `2.3460`, profit floor `FAIL`, minimum position size `PASS`.
  - `MTFTrendStackBTCOnly`: robust Sharpe `-0.0796`, total profit `-4.27%`, trades `150`, win rate `22.0%`, profit factor `0.8513`, profit floor `FAIL`, minimum position size `PASS`.
  - `MomentumMTFConfluenceBTCOnly`: robust Sharpe `0.0411`, total profit `2.86%`, trades `169`, win rate `30.7692%`, profit factor `1.0709`, profit floor `FAIL`, minimum position size `PASS`.
- Successful data-ready threaded execution is runtime-readiness evidence only. It is not accepted regime-confidence evidence, not source/control evidence, not canonical merge input, not downstream promotion evidence, and not trade evidence.

## Promotion Status

- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge: `false`
- Downstream promotion rerun: `false`
- Strict full objective: `false`
- Trade usable: `false`
- `update_goal=false`

## Artifacts

- Status before: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/00_status_before.stdout.json`
- Plain run stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/01_autoquant_run.stderr.txt`
- Status after plain run: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/02_status_after.stdout.json`
- UV-directory run stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/03_autoquant_run_uv_directory.stdout.txt`
- UV-directory run stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/03_autoquant_run_uv_directory.stderr.txt`
- Final status: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/04_status_after_uv_directory.stdout.json`
- Threaded-resolver run stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.stdout.txt`
- Threaded-resolver run stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/05_autoquant_run_threaded_resolver.stderr.txt`
- Status after threaded-resolver run: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/command-output/06_status_after_threaded_resolver.stdout.json`
- Metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/autoquant-data-ready-local-cache-run-after-041649-v1/autoquant_data_ready_local_cache_run_after_041649_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/autoquant-data-ready-local-cache-run-after-041649-v1/autoquant_data_ready_local_cache_run_after_041649_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T042222-codex-autoquant-data-ready-local-cache-run-after-041649-v1/checks/autoquant_data_ready_local_cache_run_after_041649_v1_assertions.out`

## Next

Preserve the Current Cursor next action. Do not promote AutoQuant runtime success without accepted source/control gates. Continue only after stronger source-confidence evidence, source-owned R3/R5 target rows, verifier-native R6 controls, or explicit approval unlocks the relevant target root before rerunning the full verifier -> split calibration -> canonical merge -> provider/AutoQuant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain.
