# Kaggle Bull Coverage-Buffer Gate

Run id: `20260511T035045+0800-codex-kaggle-bull-coverage-buffer-gate`.

## Decision

- Gate result: `accepted_bull_95`
- Accepted 95 `Bull`: `true`
- Rule: `close_drawdown60 >= -0.0032047199531 AND volatility <= 0.152179344579`
- Calibration Wilson95 LCB / coverage: `0.952516` / `0.037214`
- Test Wilson95 LCB / coverage: `0.961931` / `0.052777`
- Blockers: none

## Policy

- Thresholds were selected on the train split only.
- The train selector required a coverage buffer of at least 0.045 before held-out calibration/test checks.
- Source `regime_label` was used only as the target label; source confidence and future/target/next predictors stayed blocked.
- Raw provider data and the full feature table stayed under `/private/tmp`.
