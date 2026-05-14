# S&P 500 Breadth Root Gate

Run id: `20260511T030530+0800-codex-sp500-breadth-root-gate`

## Source

- Constituents source: `https://en.wikipedia.org/wiki/List_of_S%26P_500_companies`
- Constituents parsed: 503; downloaded close columns retained: 494.
- Raw price cache: `/private/tmp/ict-regime-sp500-breadth-root/sp500_breadth_prices.csv`
- Raw data committed to repo: false.
- Predictors used: daily breadth, credit/rates/USD/volatility proxies; future label columns blocked as predictors.

## Split

- Train: {'rows': 1211, 'date_min': '2018-03-29', 'date_max': '2023-01-19', 'label_counts': {'UnknownOrMixed': 554, 'Bull': 256, 'Sideways': 192, 'Bear': 106, 'Crisis': 103}}
- Calibration: {'rows': 404, 'date_min': '2023-01-20', 'date_max': '2024-08-28', 'label_counts': {'UnknownOrMixed': 206, 'Bull': 102, 'Sideways': 72, 'Bear': 24}}
- Test: {'rows': 404, 'date_min': '2024-08-29', 'date_max': '2026-04-10', 'label_counts': {'UnknownOrMixed': 194, 'Sideways': 107, 'Bull': 58, 'Crisis': 24, 'Bear': 21}}

## Gate Results

### Bull

- Selected train-only rule: `spy_ret_60d <= -0.137051311203`.
- Train Wilson95 LCB: `0.340129` with support 61.
- Calibration Wilson95 LCB: `0.000000` with support 0.
- Test Wilson95 LCB: `0.000000` with support 4.
- Accepted 95: False.

### Bear

- Selected train-only rule: `tlt_ret_20d <= -0.0332470331193`.
- Train Wilson95 LCB: `0.145027` with support 243.
- Calibration Wilson95 LCB: `0.010573` with support 97.
- Test Wilson95 LCB: `0.000000` with support 58.
- Accepted 95: False.

### Sideways

- Selected train-only rule: `pct_above_200d >= 0.917695473251`.
- Train Wilson95 LCB: `0.294569` with support 64.
- Calibration Wilson95 LCB: `0.000000` with support 0.
- Test Wilson95 LCB: `0.000000` with support 0.
- Accepted 95: False.

## Decision

- Accepted 95 roots from this run: `[]`.
- Gate: `blocked_sp500_breadth_root_gate_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.
