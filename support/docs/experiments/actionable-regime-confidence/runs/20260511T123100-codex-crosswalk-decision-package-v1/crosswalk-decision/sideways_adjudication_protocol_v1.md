# Sideways Adjudication Protocol v1

Purpose: convert the existing accepted Sideways source-backed gate into a targeted dated-window adjudication rerun, without pretending a dated external Sideways source already exists.

## Inputs

- Existing gate artifact: `docs/experiments/actionable-regime-confidence/runs/20260511T041923-codex-yahoo-sourcebacked-parent-root-gate/yahoo-parent-root-gate/yahoo_sourcebacked_parent_root_gate_report.json`
- Existing rule: `sideways_abs_return_ratio <= 0.505204858191 AND sideways_range_ratio <= 0.357222193236`
- Required target: per provider/instrument/timeframe Sideways windows from observed/trailing data only.

## Acceptance

- Held-out Wilson95 LCB must be `>= 0.95`.
- Support must be `>= 250` per accepted cell or explicitly scoped aggregate.
- Threshold selection must happen on train split only.
- Calibration/test splits must remain time-separated.
- Unsupported cells remain abstained.

## Forbidden Shortcuts

- Do not label Sideways as non-Bull/non-Bear/non-Crisis.
- Do not use future returns or target labels as predictors.
- Do not generalize a passed daily/weekly ETF/crypto scope to intraday/monthly or other species without rerun evidence.
- Do not count this protocol as a dated source window until rerun artifacts materialize dated windows.
