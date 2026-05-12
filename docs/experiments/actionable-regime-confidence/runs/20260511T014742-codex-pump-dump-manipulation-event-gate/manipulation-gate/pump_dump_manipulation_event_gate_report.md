# Pump-And-Dump Manipulation Event Gate

Run id: `20260511T014742+0800-codex-pump-dump-manipulation-event-gate`

## Source

- URL: `https://github.com/SystemsLab-Sapienza/pump-and-dump-dataset`
- Commit inspected in `/tmp`: `d71250d4cb055dde2d415c8cba38a0dcd6eb6e16`
- Dataset type: Telegram pump-and-dump event labels plus Binance trade-derived labeled feature windows.
- Pump event rows: 1110.
- Groups: 13.

## Gate Result

- Accepted 95 Manipulation root: false.
- State: `partial_crypto_event_social_manipulation_evidence`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

## Timeframe Results

- features_15S.csv.gz: rows=584104, positives=317, events=327, symbols=85, rule=`std_trades >= 0.009`, cal_lcb=0.063847, test_lcb=0.052392, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_50
- features_25S.csv.gz: rows=482157, positives=317, events=327, symbols=85, rule=`std_volume >= 0.008`, cal_lcb=0.068612, test_lcb=0.058929, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_50
- features_5S.csv.gz: rows=821307, positives=317, events=327, symbols=85, rule=`std_trades >= 0.012`, cal_lcb=0.047222, test_lcb=0.036087, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_50

## Decision

Dataset provides useful labeled crypto pump-and-dump event/social/trade-feature evidence, but strict chronological gates did not pass 95% Wilson lower bound across feature timeframes and it covers Binance crypto pumps only, not cross-market L2/L3/order-lifecycle manipulation.

Next: Acquire broader calibration-grade direct manipulation data: market-wide L2/L3/MBO/order-lifecycle datasets or multiple event/social/on-chain manipulation datasets across venues and periods, then rerun unchanged Manipulation gates.
