# Bayi-Hu Sequence/Ranking Manipulation Gate

Run id: `20260511T043519+0800-codex-bayi-sequence-manipulation-gate`

## Source
- URL: `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- Sample root in tmp: `/private/tmp/ict-regime-bayi-gdrive`
- Train archive SHA-256: `cbd0e54487b8d46f2f57dd5215120505af69f31469b4d339d4a9ed7374126a84`
- Test archive SHA-256: `88854280bc194a0dcb44974cba4d79a13d045402fb2a3fa906ea1213f5f747bc`
- Raw CSV extracted or committed to repo: false.
- External source-review posture: public repo/data schema inspected; no external repo code executed; generated archives parsed as untrusted input.

## Dataset
- Train rows: 132314 with 748 positives and 131566 negatives across 754 events.
- Test rows: 64299 with 200 positives and 64099 negatives across 227 events.
- Train timestamp range: 1546353004000 to 1620579611000.
- Test timestamp range: 1620579621000 to 1642518014000.
- Fit/calibration event split: 527 / 227 events.
- Fit rows: 82365; calibration rows: 49949.
- Sequence fields used: `coin_id_seq` plus the recent 10 entries of `feature_seq`; each sequence entry uses the source model's last 9 market/social dimensions.
- Blocked predictors: source label, raw channel id, raw channel embedding id, raw coin string/id, raw timestamp, future/next fields.

## Best Row Gates

- model=sequence_tail_logodds accepted_95=false rule=`calibrated_probability >= 0.0294950966776` min_lcb=0.028636 fit_lcb=0.028636 cal_lcb=0.028683 test_lcb=0.040038 cal_support=2498 test_support=2311 cal_cov=0.050011 test_cov=0.035941
- model=combined_target_sequence_logodds accepted_95=false rule=`calibrated_probability >= 0.0226907095905` min_lcb=0.023915 fit_lcb=0.041149 cal_lcb=0.024734 test_lcb=0.023915 cal_support=2498 test_support=4473 cal_cov=0.050011 test_cov=0.069566

## Best Event Top-1 Gates

- model=sequence_tail_logodds accepted_95=false rule=`event_top1_score >= 0.013 AND event_top1_margin >= 0` min_lcb=0.024102 cal_lcb=0.040450 test_lcb=0.024102 cal_hit=0.066079 test_hit=0.044053 cal_events=227 test_events=227
- model=combined_target_sequence_logodds accepted_95=false rule=`event_top1_score >= 0.031012404962 AND event_top1_margin >= 0` min_lcb=0.002420 cal_lcb=0.024102 test_lcb=0.002420 cal_hit=0.044053 test_hit=0.008811 cal_events=227 test_events=227

## Diagnostic Hit Rates

- split=test model=sequence_tail_logodds gate=event_hit_at_1_diagnostic hit_rate=0.044053 wilson95_lcb=0.024102 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_3_diagnostic hit_rate=0.136564 wilson95_lcb=0.097904 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_5_diagnostic hit_rate=0.246696 wilson95_lcb=0.195141 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_10_diagnostic hit_rate=0.444934 wilson95_lcb=0.381736 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_20_diagnostic hit_rate=0.647577 wilson95_lcb=0.583446 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_30_diagnostic hit_rate=0.735683 wilson95_lcb=0.674741 support=227
- split=test model=sequence_tail_logodds gate=event_hit_at_50_diagnostic hit_rate=0.801762 wilson95_lcb=0.745067 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_1_diagnostic hit_rate=0.008811 wilson95_lcb=0.002420 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_3_diagnostic hit_rate=0.088106 wilson95_lcb=0.057758 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_5_diagnostic hit_rate=0.127753 wilson95_lcb=0.090442 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_10_diagnostic hit_rate=0.255507 wilson95_lcb=0.203165 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_20_diagnostic hit_rate=0.533040 wilson95_lcb=0.468128 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_30_diagnostic hit_rate=0.660793 wilson95_lcb=0.596985 support=227
- split=test model=combined_target_sequence_logodds gate=event_hit_at_50_diagnostic hit_rate=0.744493 wilson95_lcb=0.684015 support=227

## Decision
- Accepted 95 MainRegimeV2 direct-input-gated `Manipulation`: false.
- Best row rule: `calibrated_probability >= 0.0294950966776`.
- Best row min LCB: `0.028636`.
- Best event top-1 rule: `event_top1_score >= 0.013 AND event_top1_margin >= 0`.
- Best event top-1 min LCB: `0.024102`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

Bayi-Hu supplies explicit positive pump-target rows, explicit negative candidate rows, and sequence fields (`coin_id_seq`, `feature_seq`), but the chronological sequence/ranking gates did not pass unchanged 95% Wilson lower bounds with support and coverage floors on calibration and official test.

Next: Do not repeat scalar or Bayi-Hu sequence thresholding; acquire a stronger direct manipulation source with richer order-lifecycle/L2/L3/MBO/social/on-chain positives and negatives, or train a full sequence model only if it can preserve chronological calibration and the same 95 Wilson gate.
