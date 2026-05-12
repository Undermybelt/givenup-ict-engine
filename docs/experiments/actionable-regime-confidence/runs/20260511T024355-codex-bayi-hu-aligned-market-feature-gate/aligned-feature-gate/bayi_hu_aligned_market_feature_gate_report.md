# Bayi-Hu Aligned Market-Feature Manipulation Gate

Run id: `20260511T024355+0800-codex-bayi-hu-aligned-market-feature-gate`

## Source
- URL: `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- Sample root in tmp: `/private/tmp/ict-regime-bayi-gdrive`
- Train archive SHA-256: `cbd0e54487b8d46f2f57dd5215120505af69f31469b4d339d4a9ed7374126a84`
- Test archive SHA-256: `88854280bc194a0dcb44974cba4d79a13d045402fb2a3fa906ea1213f5f747bc`
- Raw CSV extracted or committed to repo: false.

## Dataset
- Train rows: 132314 with 748 positives and 131566 negatives.
- Test rows: 64299 with 200 positives and 64099 negatives.
- Train timestamp range: 1546353004000 to 1620579611000.
- Test timestamp range: 1620579621000 to 1642518014000.
- Fit/calibration event split: 527 / 227 events.
- Fit rows: 82365; calibration rows: 49949; reservoir rows: 82365.
- Target features used: 139; sequence fields not used in this bounded target-feature gate.
- Axis note: this is a MainRegimeV3 `Manipulation` readback only; it does not reissue `BullExpansion`, `BearExpansion`, `SidewaysConsolidation`, or `CrisisStress`.

## Best Gate Rows

- rank=4 accepted_95=false rule=`pre_6h_return >= 1.95934015751` min_lcb=0.015287 fit_lcb=0.017359 cal_lcb=0.015287 test_lcb=0.033250 cal_support=2543 test_support=1329 cal_cov=0.050912 test_cov=0.020669
- rank=8 accepted_95=false rule=`pre_1h_return >= 2.2777635479` min_lcb=0.014645 fit_lcb=0.015310 cal_lcb=0.014645 test_lcb=0.025496 cal_support=1215 test_support=893 cal_cov=0.024325 test_cov=0.013888
- rank=9 accepted_95=false rule=`pre_1h_return >= 3.13196591377` min_lcb=0.013675 fit_lcb=0.014811 cal_lcb=0.013675 test_lcb=0.040684 cal_support=667 test_support=500 cal_cov=0.013354 test_cov=0.007776
- rank=14 accepted_95=false rule=`pre_3h_return >= 2.09631967545` min_lcb=0.013275 fit_lcb=0.013275 cal_lcb=0.015131 test_lcb=0.036330 cal_support=1890 test_support=1097 cal_cov=0.037839 test_cov=0.017061
- rank=17 accepted_95=false rule=`pre_3d_alexa_index >= 0.357165187597` min_lcb=0.013065 fit_lcb=0.013065 cal_lcb=0.014224 test_lcb=0.013209 cal_support=6234 test_support=4604 cal_cov=0.124807 test_cov=0.071603
- rank=2 accepted_95=false rule=`pre_6h_return >= 1.22798411846` min_lcb=0.013013 fit_lcb=0.020222 cal_lcb=0.013013 test_lcb=0.020886 cal_support=5153 test_support=3085 cal_cov=0.103165 test_cov=0.047979
- rank=23 accepted_95=false rule=`pre_36h_return >= 1.63023495197` min_lcb=0.012280 fit_lcb=0.012280 cal_lcb=0.014160 test_lcb=0.021385 cal_support=3484 test_support=1941 cal_cov=0.069751 test_cov=0.030187
- rank=33 accepted_95=false rule=`pre_1h_return >= 1.25885224342` min_lcb=0.011544 fit_lcb=0.011544 cal_lcb=0.013340 test_lcb=0.018029 cal_support=3304 test_support=2205 cal_cov=0.066147 test_cov=0.034293
- rank=34 accepted_95=false rule=`pre_24h_return >= 0.985964655876` min_lcb=0.011544 fit_lcb=0.011544 cal_lcb=0.011552 test_lcb=0.015055 cal_support=6502 test_support=4277 cal_cov=0.130173 test_cov=0.066517
- rank=38 accepted_95=false rule=`pre_6h_return >= 2.67220497131` min_lcb=0.011049 fit_lcb=0.011049 cal_lcb=0.021120 test_lcb=0.050883 cal_support=1476 test_support=819 cal_cov=0.029550 test_cov=0.012737

## Decision
- Accepted 95 MainRegimeV3 `Manipulation` root: false.
- Best min full-split LCB: `0.015287`.
- Best rule: `pre_6h_return >= 1.95934015751`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

Bayi-Hu aligned target-coin samples are direct event-aligned manipulation evidence, but the bounded streaming scalar target-feature gate did not pass unchanged 95% Wilson lower bounds with support and 3% coverage floors on calibration and official test.

Next: Materialize the full MainRegimeV3 schema/crosswalk and rerun unchanged 95% chronological root gates for BullExpansion, BearExpansion, SidewaysConsolidation, CrisisStress, and Manipulation; for Manipulation, the next non-proxy slice should use a sequence/ranking gate over coin_id_seq and feature_seq rather than only scalar target features.
