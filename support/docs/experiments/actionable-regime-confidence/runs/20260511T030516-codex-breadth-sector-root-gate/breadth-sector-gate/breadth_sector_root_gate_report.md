# Breadth/Sector Root Gate

Run id: `20260511T030516+0800-codex-breadth-sector-root-gate`

## Data

- Requested yfinance symbols: DIA, GLD, HYG, IWM, LQD, QQQ, RSP, SPY, TLT, UUP, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY, ^VIX.
- Available symbols: DIA, GLD, HYG, IWM, LQD, QQQ, RSP, SPY, TLT, UUP, XLB, XLC, XLE, XLF, XLI, XLK, XLP, XLRE, XLU, XLV, XLY, ^VIX.
- Derived feature rows: 9111.
- Raw provider CSV committed: false; only derived feature/report artifacts are retained.

## Gate Results

- Bull: accepted_95=False, rule=`breadth_above_ma200 <= 0.318181818182`, cal_lcb=0.279430, test_lcb=0.014178, cal_support=462, test_support=39, blockers=test_support_below_60|calibration_wilson95_below_0_95|test_wilson95_below_0_95|coverage_below_0_03|ece_above_0_05|validation_timeframes_below_2
- Bear: accepted_95=False, rule=`panel_range20_mean <= 0.0127445794453`, cal_lcb=0.559965, test_lcb=0.171886, cal_support=63, test_support=588, blockers=calibration_support_below_120|calibration_wilson95_below_0_95|test_wilson95_below_0_95|ece_above_0_05|validation_timeframes_below_2
- Sideways: accepted_95=False, rule=`vol20 <= 0.00465418081575`, cal_lcb=0.621180, test_lcb=0.504391, cal_support=15, test_support=48, blockers=calibration_support_below_120|test_support_below_60|calibration_wilson95_below_0_95|test_wilson95_below_0_95|coverage_below_0_03|ece_above_0_05|validation_timeframes_below_2

## Decision

- Newly accepted active roots: none.
- Gate: `blocked_breadth_sector_roots_below_95`.
- Thresholds relaxed: false.
- Runtime code changed: false.
- Trade usable: false.

Breadth/sector/credit/volatility features did not close all missing MainRegimeV2 roots at the unchanged 95% held-out gate.

Next: If no roots pass, acquire a labeled macro/bull-bear-sideways regime dataset or options/dealer-positioning history before rerunning unchanged gates.
