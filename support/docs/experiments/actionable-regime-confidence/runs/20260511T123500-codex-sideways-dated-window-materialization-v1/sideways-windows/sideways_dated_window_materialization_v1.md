# Sideways Dated Window Materialization v1

Run ID: `20260511T123500+0800-codex-sideways-dated-window-materialization-v1`

## Result

- Materialized Sideways dated windows: `608`.
- Selected rows: `4049`.
- Scope: `scoped_existing_yahoo_gate_crypto_and_equity_etf_1d_1w_only`.
- Existing Sideways gate Wilson95 calibration/test LCB: `0.988647` / `0.995568`.
- Full objective gate: `none_for_MainRegimeV2_expanded_full_universe_full_cycle_goal`.

## What Changed

The Sideways lane no longer has to say only `no dated source window` for the existing accepted Yahoo scope. It now has concrete dated windows derived from the already accepted `sideways_sourcebacked_abs_return_range_v1` gate.

## Guardrails

- Existing local cache only; no fresh download.
- No threshold relaxation.
- No runtime code change.
- No raw Yahoo close matrix committed.
- Sideways is not inferred as complement of Bull/Bear/Crisis.
- This does not cover expanded intraday/monthly/full-species Sideways slots.

## Artifacts

- `sideways_dated_window_materialization_v1.json`
- `sideways_dated_windows_v1.csv`
- `../checks/sideways_dated_window_materialization_v1_assertions.out`
