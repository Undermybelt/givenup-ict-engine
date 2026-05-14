# Provider-LTF Timerange Repair v1

Run id: `20260512T100817+0800-codex-board-b-provider-ltf-timerange-repair-v1`

Mode: `incubation_only`

## Scope

This is a run-local diagnostic continuation of `093820`. It does not edit Current Cursor, does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not promote selected-data AutoQuant, does not run downstream promotion, and does not call `update_goal`.

## Root Cause

Fact: `093820` had `NQ_USD-{1h,4h,1d}.feather` files in the run-local `user_data/data` directory.

Fact: the failed `093820` backtest logged `NQ/USD, spot, 1h, data starts at 2026-03-27 15:00:00`, then raised `OperationalException: No data found. Terminating.`

Fact: `093820` used `timerange=20230101-20251231`.

Root cause: the run-local TOMAC config requested a historical window ending before the available provider-LTF data started. Freqtrade correctly filtered the data to an empty backtest window.

Canonical owner: this is run-local Auto-Quant/TOMAC config ownership, not ict-engine runtime code and not Board A regime vocabulary.

## Minimal Test

Only the copied sidecar config changed:

```text
timerange: 20230101-20251231 -> 20260327-20260512
```

Command:

```text
uv --directory /Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T092800+0800-codex-board-b-aq-first-nursery-provider-ltf-v1/state/.deps/auto-quant run python /Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260512T100817+0800-codex-board-b-provider-ltf-timerange-repair-v1/workspace/auto-quant-pair-repair/run_tomac.py
```

Artifacts:

- `command-output/00_run_tomac_timerange_repair.cmd`
- `command-output/00_run_tomac_timerange_repair.out`
- `command-output/00_run_tomac_timerange_repair.err`
- `command-output/00_run_tomac_timerange_repair.exit`

## Readback

- Command exit: `0`.
- Freqtrade loaded `NQ/USD` 1h data from `2026-03-27 15:00:00` to `2026-05-11 15:00:00`.
- Backtest effective window after startup: `2026-04-07 01:00:00 -> 2026-05-11 15:00:00`.
- Strategy: `TomacNQ_KillzoneBreakout`.
- Trades: `0`.
- Sharpe: `0.0000`.
- Total profit: `0.0000%`.
- Win rate: `0.0000%`.
- Profit factor: `0.0000`.

## Decision

Gate: `incubation_only:timerange_repaired_but_zero_trades`.

The timerange bug is retired for this sidecar, but this did not create mature rooted branch observations or profitability evidence. Do not promote. Do not rerun the same short-window provider-LTF TOMAC shape unless the next slice changes the factor/strategy signal or supplies a longer provider-provenanced history.

Promotion: `false`.

`update_goal=false`.
