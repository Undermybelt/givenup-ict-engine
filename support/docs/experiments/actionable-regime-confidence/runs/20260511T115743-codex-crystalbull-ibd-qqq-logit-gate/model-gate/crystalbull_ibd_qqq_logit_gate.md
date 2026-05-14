# CrystalBull IBD QQQ Logit Gate

Run ID: `20260511T115743+0800-codex-crystalbull-ibd-qqq-logit-gate`

## Scope

- Active taxonomy: `MainRegimeV2`.
- Source candidate: CrystalBull IBD Market Pulse Review.
- Instrument/timeframe: yfinance `QQQ` `1d`.
- Prior simple-rule gate: `20260511T113603+0800-codex-crystalbull-ibd-qqq-source-gate`.
- This run tests a stronger probability model without installing new packages.

Source: https://www.crystalbull.com/IBD-market-pulse-review/

## Method

- Parsed `4957` embedded IBD Current Outlook points from the public page.
- Fetched yfinance `QQQ` daily OHLCV at run time.
- Built current/past-only OHLCV rolling features: returns, volatility, moving-average ratios, drawdown, range position, volume z-score, RSI.
- Used pure NumPy one-vs-rest L2 logistic regression with standardized, `tanh`, and squared feature transforms.
- Fit used train split only.
- Probability thresholds were selected on calibration split only.
- Test split was held out until final evaluation.
- No `future_*` or `target_*` predictors used.
- No package installation. Runtime code changed: false.

Rows after warmup: `4706`.

Chronological split:
- train `2823`
- calibration `941`
- test `942`

## Results

| Root | Calibration Wilson95 | Test Wilson95 | Calibration Support | Test Support | Accepted 95 |
|---|---:|---:|---:|---:|---:|
| Bull | `0.954754` | `0.924919` | `254` | `307` | false |
| Bear | `0.845442` | `0.850023` | `43` | `64` | false |
| Sideways | `0.523624` | `0.137130` | `60` | `115` | false |
| Crisis | `0.000000` | `0.000000` | `0` | `0` | false |

The stricter Bull threshold with perfect calibration precision still failed test Wilson95: calibration `0.972916`, test `0.915883`.

## Decision

- Accepted MainRegimeV2 parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_crystalbull_ibd_qqq_logit_gate_below_95_and_incomplete_source_axis`.

The model improves Bull calibration but does not pass held-out 95% confidence. Bear and Sideways remain below gate, and the source axis lacks Crisis. This should stop additional CrystalBull/IBD QQQ daily OHLCV model recycling unless a materially different external label export is supplied.
