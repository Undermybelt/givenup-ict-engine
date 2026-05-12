# CBOE Options/Vol Root Gate

Run id: `20260511T030759+0800-codex-cboe-options-vol-root-gate`

## Data

- CBOE public volatility series requested: vix, vvix, vix9d, vix3m, vix6m, vix1y, skew, ovx, gvz, vxeem.
- CBOE public volatility series available: vix, vvix, vix9d, vix3m, vix6m, vix1y, skew, ovx, gvz, vxeem.
- yfinance target symbols available: IWM, QQQ, SPY.
- Derived feature rows: 13577.
- Raw provider CSV committed: false; CBOE raw CSV cache path `/private/tmp/ict-regime-cboe-options-vol-root`.

## Gate Results

- Bull: accepted_95=False, rule=`vvix_vix_ratio >= 7.99066874028`, cal_lcb=0.438503, test_lcb=0.000000, cal_support=3, test_support=0, blockers=calibration_support_below_120|test_support_below_60|calibration_wilson95_below_0_95|test_wilson95_below_0_95|coverage_below_0_03|ece_above_0_05|validation_instruments_below_2|validation_market_contexts_below_2|validation_timeframes_below_2
- Bear: accepted_95=False, rule=`crossasset_vol_dispersion <= 6.25399339089`, cal_lcb=0.470852, test_lcb=0.156123, cal_support=51, test_support=171, blockers=calibration_support_below_120|calibration_wilson95_below_0_95|test_wilson95_below_0_95|ece_above_0_05
- Sideways: accepted_95=False, rule=`target_vol_60 <= 0.0049663998606`, cal_lcb=0.386190, test_lcb=0.000000, cal_support=18, test_support=0, blockers=calibration_support_below_120|test_support_below_60|calibration_wilson95_below_0_95|test_wilson95_below_0_95|coverage_below_0_03|ece_above_0_05|validation_instruments_below_2|validation_market_contexts_below_2|validation_timeframes_below_2

## Decision

- Newly accepted active roots: none.
- Gate: `blocked_cboe_options_vol_roots_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.

CBOE public volatility and options-implied context did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate.

Next: If this gate fails, stop repeating proxy-only threshold scans; acquire labeled bull/bear/sideways regime-cycle data or options/dealer-positioning history, and direct order-flow/event labels for Manipulation.
