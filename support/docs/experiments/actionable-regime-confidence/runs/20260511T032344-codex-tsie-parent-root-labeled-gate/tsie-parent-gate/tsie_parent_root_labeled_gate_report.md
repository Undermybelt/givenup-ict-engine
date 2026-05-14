# TSIE Parent Root Labeled Gate

Run id: `20260511T032344+0800-codex-tsie-parent-root-labeled-gate`

## Source

- Dataset page: `https://huggingface.co/datasets/sujinwo/tsie-market-regime-dataset`
- Raw parquet cache: `/private/tmp/ict-regime-tsie-parent-root/tft_dataset_labeled.parquet`
- Raw data committed to repo: false.
- Source labels mapped: `0/1 -> Bear`, `3 -> Sideways`, `5/6 -> Bull`, `2/4 -> UnknownOrMixed`.
- Blocked from predictors: `future_volatility`, `target_return`, `regime_label`, and metadata columns.

## Split

- Train: {'rows': 4316854, 'date_min': '1990-06-07T02:00:00', 'date_max': '2022-04-21T02:00:00', 'label_counts': {'UnknownOrMixed': 1301009, 'Sideways': 1237259, 'Bull': 902610, 'Bear': 875976}}
- Calibration: {'rows': 1438543, 'date_min': '2022-04-21T03:00:00', 'date_max': '2024-05-28T08:00:00', 'label_counts': {'Sideways': 485035, 'UnknownOrMixed': 433323, 'Bear': 282176, 'Bull': 238009}}
- Test: {'rows': 1438599, 'date_min': '2024-05-28T09:00:00', 'date_max': '2026-04-07T02:00:00', 'label_counts': {'Sideways': 439790, 'UnknownOrMixed': 426761, 'Bull': 294436, 'Bear': 277612}}

## Gate Results

### Bull

- Rule: `p_model(Bull) >= 0.554942296743`.
- Calibration Wilson95 LCB: `0.374575` with support 1439.
- Test Wilson95 LCB: `0.563979` with support 3501.
- Test coverage: `0.002434`.
- Test instruments: `422`; market contexts: `['IDX']`; timeframes: `['intraday_hourly']`.
- Accepted 95: False.
- Blockers: `['calibration_wilson95_below_0_95', 'test_wilson95_below_0_95', 'calibration_coverage_below_0_03', 'test_coverage_below_0_03', 'validation_market_contexts_below_2', 'validation_timeframes_below_2']`.

### Bear

- Rule: `p_model(Bear) >= 0.604139246464`.
- Calibration Wilson95 LCB: `0.640954` with support 1439.
- Test Wilson95 LCB: `0.587442` with support 1898.
- Test coverage: `0.001319`.
- Test instruments: `453`; market contexts: `['IDX']`; timeframes: `['intraday_hourly']`.
- Accepted 95: False.
- Blockers: `['calibration_wilson95_below_0_95', 'test_wilson95_below_0_95', 'calibration_coverage_below_0_03', 'test_coverage_below_0_03', 'validation_market_contexts_below_2', 'validation_timeframes_below_2']`.

### Sideways

- Rule: `p_model(Sideways) >= 0.981051445007`.
- Calibration Wilson95 LCB: `0.972876` with support 1441.
- Test Wilson95 LCB: `0.864895` with support 177.
- Test coverage: `0.000123`.
- Test instruments: `14`; market contexts: `['IDX']`; timeframes: `['intraday_hourly']`.
- Accepted 95: False.
- Blockers: `['test_wilson95_below_0_95', 'calibration_coverage_below_0_03', 'test_coverage_below_0_03', 'validation_market_contexts_below_2', 'validation_timeframes_below_2']`.

## Decision

- Accepted 95 roots from this run: `[]`.
- Gate: `blocked_tsie_parent_root_labeled_gate_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.
