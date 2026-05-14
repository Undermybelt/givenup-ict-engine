# Non-Promoting Multicadence Run Tomac Readback v1

Run id: `20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1`

Packet: `non-promoting-multicadence-run-tomac-readback-v1`

Gate result: `non_promoting_multicadence_run_tomac_readback_v1=incubation_only_zero_trade_and_startup_candle_failure`

## Scope

This packet records a non-promoting Auto-Quant nursery replay against the `092558` multicadence workspace. It does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not run selected-data AutoQuant promotion, direct verifier, split calibration, canonical merge, filter / Pre-Bayes, BBN, CatBoost/path-ranking, execution-tree promotion, trade claims, or `update_goal`.

## Command

The first attempted command used the parent repo `uv run` context and failed before import with `ModuleNotFoundError: No module named 'freqtrade'`. The corrected command used the Auto-Quant workspace venv:

```bash
cd docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/state_non_promoting_multicadence_v1/.deps/auto-quant
./.venv/bin/python run_tomac.py
```

## Readback

- Exit code: `1`.
- Strategies discovered: `5`.
- Backtests succeeded: `3`.
- Backtests failed: `2`.
- Successful zero-trade strategies:
  - `NQMeanRevertFeedback`: Sharpe `0.0000`, total profit `0.0000%`, trade count `0`, win rate `0.0000%`, profit factor `0.0000`.
  - `NQTrendCarryFeedback`: Sharpe `0.0000`, total profit `0.0000%`, trade count `0`, win rate `0.0000%`, profit factor `0.0000`.
  - `TomacNQ_KillzoneBreakout`: Sharpe `0.0000`, total profit `0.0000%`, trade count `0`, win rate `0.0000%`, profit factor `0.0000`.
- Failed startup-candle strategies:
  - `TomacNQ_CompressionMeanRevert`: `OperationalException: No data left after adjusting for startup candles.`
  - `TomacNQ_MulticadenceTrendPullback`: `OperationalException: No data left after adjusting for startup candles.`
- Pairlist/data gate was no longer the terminal blocker in the captured run: `NQ/USD` data loaded and three strategies completed.
- Nursery signal added: zero qualifying trades and two startup-window failures. No mature observations were produced.

## Artifacts

- Raw output: `docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-run-tomac-readback-v1/raw/run_tomac.stdout_stderr.txt`
- Exit marker: `docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-run-tomac-readback-v1/raw/run_tomac.exit`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-run-tomac-readback-v1/non_promoting_multicadence_run_tomac_readback_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T092558+0800-codex-board-b-032157-non-promoting-multicadence-feedback-v1/non-promoting-multicadence-run-tomac-readback-v1/checks/non_promoting_multicadence_run_tomac_readback_v1_assertions.out`

## Decision

This is `incubation_only` / `non_promoting_aq_feedback`. It is useful negative feedback for the nursery lane: the current multicadence NQ seed set is either too restrictive for the available replay window or requires a longer prepared history before startup-heavy MTF strategies are meaningful.

Production promotion remains fail-closed.

