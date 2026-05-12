# CrystalBull IBD QQQ Source Gate

Run ID: `20260511T113603+0800-codex-crystalbull-ibd-qqq-source-gate`

## Scope

- Active taxonomy: `MainRegimeV2`.
- Candidate source: CrystalBull IBD Market Pulse Review.
- Candidate instrument/timeframe: yfinance `QQQ` `1d`.
- Tested mapping: `Confirmed Uptrend -> Bull`, `Uptrend Under Pressure -> Sideways`, `Correction -> Bear`.
- `Crisis` is not present in the source state axis.

Source: https://www.crystalbull.com/IBD-market-pulse-review/

## Source Extraction

- Embedded IBD Current Outlook points parsed from the public page: `4957`.
- Embedded source date range: `2002-12-31` to `2022-09-16` UTC.
- Raw source page committed: false.
- Value counts: `Confirmed Uptrend/Bull=-1.0:3046`, `Uptrend Under Pressure/Sideways=0.5:846`, `Correction/Bear=1.0:1065`.

## Calibration

- yfinance `QQQ` daily OHLCV fetched at run time.
- Feature rows after rolling warmup: `4706`.
- Feature date range: `2003-12-30` to `2022-09-16`.
- Chronological split: train `2823`, calibration `941`, test `942`.
- Selection used train-only one- and two-condition OHLCV feature rules. Calibration/test were held out.
- No `future_*` or `target_*` predictors used. Thresholds relaxed: false.

| Root | Best Rule | Train Wilson95 | Calibration Wilson95 | Test Wilson95 | Accepted 95 |
|---|---|---:|---:|---:|---:|
| Bull | `ma_ratio_20 >= 0.0339732954359 AND ret_20 >= 0.0535997879283` | `0.983065` | `0.797578` | `0.910274` | false |
| Bear | `ret_20 <= -0.063102622668 AND rsi14 <= 33.5610627494` | `0.934347` | `0.686054` | `0.597406` | false |
| Sideways | `ret_120 >= 0.217526352355 AND ret_10 <= 0.00338053039555` | `0.506909` | `0.000000` | `0.287556` | false |
| Crisis | N/A | `0.000000` | `0.000000` | `0.000000` | false |

## Decision

- Accepted MainRegimeV2 parent-root slots added: `0`.
- Accepted direct `Manipulation` rows/windows added: `0`.
- Gate result: `blocked_crystalbull_ibd_qqq_daily_source_gate_below_95_and_incomplete_roots`.

The source is useful daily QQQ provenance for broad market state labels, but it does not pass the unchanged held-out 95% Wilson LCB gate, lacks `Crisis`, and does not close QQQ intraday/weekly/monthly or cross-instrument missing slots.

Runtime code changed: false. Raw data committed: false. Trade usable: false.
