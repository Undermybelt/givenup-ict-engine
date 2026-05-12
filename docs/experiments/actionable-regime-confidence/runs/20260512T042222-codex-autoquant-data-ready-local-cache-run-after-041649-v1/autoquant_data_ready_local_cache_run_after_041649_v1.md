# Auto-Quant Data-Ready Local Cache Run After 041649 v1

Scope: readback for the completed `042222` local Auto-Quant cache run plus the
bounded threaded-resolver retry. This artifact does not edit the Current Cursor,
does not create source/control evidence, and does not promote a profitability or
regime-confidence candidate.

## Evidence

- `command-output/00_status_before.stdout.json`
- `command-output/01_autoquant_run.exit`
- `command-output/01_autoquant_run.stderr.txt`
- `command-output/03_autoquant_run_uv_directory.exit`
- `command-output/03_autoquant_run_uv_directory.stdout.txt`
- `command-output/03_autoquant_run_uv_directory.stderr.txt`
- `command-output/04_status_after_uv_directory.stdout.json`
- `command-output/05_autoquant_run_threaded_resolver.exit`
- `command-output/05_autoquant_run_threaded_resolver.stdout.txt`
- `command-output/05_autoquant_run_threaded_resolver.stderr.txt`
- `command-output/06_status_after_threaded_resolver.stdout.json`
- `autoquant-data-ready-local-cache-run-after-041649-v1/autoquant_data_ready_local_cache_run_after_041649_v1.csv`

## Readback

- `00_status_before.exit=0`; ict-engine reported `status=dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, and `data_ready=true`.
- `01_autoquant_run.exit=1`; direct `uv run --with ta-lib <run.py>` failed before strategy execution with `ModuleNotFoundError: No module named 'pandas'`.
- `03_autoquant_run_uv_directory.exit=1`; `uv --directory <auto-quant> run --with ta-lib run.py` reached Freqtrade and discovered `3` BTC-only strategies.
- All `3/3` discovered strategies failed with `OperationalException: Could not load markets` because Freqtrade could not contact `api.binance.com/api/v3/exchangeInfo`.
- `05_autoquant_run_threaded_resolver.exit=0`; the bounded `sitecustomize.py` shim switched aiohttp to `ThreadedResolver` and the same local-cache workspace completed `3` backtests with `0` failures.
- The successful threaded run is runtime-only evidence. The results were not source/control-backed and were not promoted.
- `06_status_after_threaded_resolver.exit=0`; ict-engine still reported `dependency_ready_data_ready`.

## Gate

- `runtime_readback:auto_quant_local_cache_threaded_resolver_run_succeeded`
- `not_promoted:missing_source_control_evidence`
- `not_promoted:accepted_rows_added_0`
- `not_started:canonical_merge_downstream_rerun`
- `promotion_allowed=false`

## Next

Do not promote from this local-cache Auto-Quant run. Continue only after stronger
source-confidence evidence, source-owned R3/R5 target rows, verifier-native R6
controls, or explicit approval unlocks the relevant target root before rerunning
the full verifier -> split calibration -> canonical merge -> provider/AutoQuant
-> filter/Pre-Bayes -> BBN -> CatBoost/path-ranking -> execution-tree chain.
