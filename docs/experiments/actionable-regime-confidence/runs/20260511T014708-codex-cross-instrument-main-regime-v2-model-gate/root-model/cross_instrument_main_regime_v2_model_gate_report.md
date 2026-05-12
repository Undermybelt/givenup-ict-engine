# Cross-Instrument MainRegimeV2 Model Gate

Run id: `20260511T014708+0800-codex-cross-instrument-main-regime-v2-model-gate`

## Decision

- Gate: `partial_for_MainRegimeV2_Crisis_only_prior_evidence_preserved`
- Accepted 95 roots from this run: `none`
- Missing roots after this run: `Bull, Bear, Sideways, Manipulation`
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

## Root Summary

- Bull: state=`blocked`, rule=`train_only_logistic_score_Bull >= 0.553877407165`, cal_lcb=0.251198, test_lcb=0.289717, test_support=1756, blockers=`calibration_wilson95_below_0_95, test_wilson95_below_0_95`
- Bear: state=`blocked`, rule=`train_only_logistic_score_Bear >= 0.587199577116`, cal_lcb=0.165388, test_lcb=0.190052, test_support=379, blockers=`calibration_wilson95_below_0_95, test_wilson95_below_0_95, test_coverage_below_0_03`
- Sideways: state=`blocked`, rule=`train_only_logistic_score_Sideways >= 0.876481829552`, cal_lcb=0.602956, test_lcb=0.613420, test_support=593, blockers=`calibration_wilson95_below_0_95, test_wilson95_below_0_95`
- Crisis: state=`blocked`, rule=`train_only_logistic_score_Crisis >= 0.91278613174`, cal_lcb=0.865396, test_lcb=0.794018, test_support=541, blockers=`calibration_wilson95_below_0_95, test_wilson95_below_0_95, ece_above_0_05, validation_timeframes_below_2`
- Manipulation: state=`missing_required_inputs`, rule=`calibration_grade_direct_L2_L3_MBO_order_lifecycle_event_inputs_present == true`, cal_lcb=0.000000, test_lcb=0.000000, test_support=0, blockers=`missing_required_inputs, proxy_only_low_confidence`
