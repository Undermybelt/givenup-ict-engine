# Tomac GC/NQ MainRegimeV2 Root Gate

Run id: `20260511T012949+0800-codex-tomac-gc-nq-main-regime-v2-root-gate`

## Decision

- Gate: `partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved`
- Newly accepted roots from this run: `none`
- Prior accepted root preserved: `Crisis`
- Still missing: `Bull`, `Bear`, `Sideways`, and direct-input-gated `Manipulation`
- `Manipulation` remains `missing_required_inputs`; OHLCV is not direct manipulation evidence.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

## Contexts

- `GC 1h`: bars=94079, feature_rows=94051, split={'train': 47025, 'calibration': 23513, 'test': 23513}
- `GC 1d`: bars=4741, feature_rows=4716, split={'train': 2358, 'calibration': 1179, 'test': 1179}
- `NQ 1h`: bars=93845, feature_rows=93817, split={'train': 46908, 'calibration': 23454, 'test': 23455}
- `NQ 1d`: bars=4739, feature_rows=4714, split={'train': 2357, 'calibration': 1178, 'test': 1179}

## Root Summary

- GC 1h Bull: rule=`bar_range >= 0.0066040614769`, cal_lcb=0.357784, test_lcb=0.412732, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1h Bear: rule=`ret_20 >= 0.0137231783969`, cal_lcb=0.203960, test_lcb=0.191262, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1h Sideways: rule=`bar_range <= 0.000715910724503`, cal_lcb=0.435526, test_lcb=0.392151, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1h Crisis: rule=`vol_20 >= 0.00345581008166`, cal_lcb=0.191890, test_lcb=0.225251, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1d Bull: rule=`vol_20 >= 0.00893976005544`, cal_lcb=0.271076, test_lcb=0.340780, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1d Bear: rule=`range_20 <= 0.0337286165244`, cal_lcb=0.133151, test_lcb=0.090244, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1d Sideways: rule=`vol_20 <= 0.006184888013`, cal_lcb=0.392594, test_lcb=0.238279, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- GC 1d Crisis: rule=`vol_20 >= 0.0148644068788`, cal_lcb=0.103791, test_lcb=0.182382, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1h Bull: rule=`vol_20 >= 0.00368185284387`, cal_lcb=0.432712, test_lcb=0.426268, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1h Bear: rule=`bar_range_z20 >= 2.35206857291`, cal_lcb=0.194292, test_lcb=0.210048, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1h Sideways: rule=`bar_range <= 0.000484512557178`, cal_lcb=0.446525, test_lcb=0.505644, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1h Crisis: rule=`bar_range >= 0.00688215025405`, cal_lcb=0.261575, test_lcb=0.159549, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1d Bull: rule=`ret_8 <= -0.0366374272905`, cal_lcb=0.333213, test_lcb=0.350779, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1d Bear: rule=`range_20 <= 0.0294515071013`, cal_lcb=0.056682, test_lcb=0.206549, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1d Sideways: rule=`vol_20 <= 0.00385018167586`, cal_lcb=0.019891, test_lcb=0.000000, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30
- NQ 1d Crisis: rule=`vol_20 >= 0.0133497975083`, cal_lcb=0.200938, test_lcb=0.141433, accepted_95=False, blocker=calibration_or_test_wilson_below_95_or_support_below_30

Next: acquire calibration-grade direct L2/L3/MBO/order-lifecycle/event data for `Manipulation`, and add non-OHLCV signed-direction/sideways evidence before rerunning unchanged MainRegimeV2 gates.
