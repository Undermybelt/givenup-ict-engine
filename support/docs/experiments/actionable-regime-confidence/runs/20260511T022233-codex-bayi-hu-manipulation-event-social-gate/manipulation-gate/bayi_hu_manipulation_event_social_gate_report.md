# Bayi-Hu Manipulation Event/Social Gate

Run id: `20260511T022233+0800-codex-bayi-hu-manipulation-event-social-gate`

## Source

- URL: `https://github.com/Bayi-Hu/Pump-and-Dump-Detection-on-Cryptocurrency`
- Commit inspected in `/tmp`: `17e398f99558c52a472728d4a5856f15313be079`
- Dataset type: Telegram P&D event log, manual message labels, predicted pump-message/session artifacts.
- Raw data committed to repo: false.

## Dataset

- P&D event rows: 1335 across 14 exchanges and 277 coins.
- Largest exchange: binance with 1003 rows.
- Manual message rows mapped: 3884 with 1468 positive and 2416 negative controls.
- Candidate event sessions: 4377 with 1168 cleaned-log positives and 3209 weaker absent-from-log controls.
- GitHub-shipped aligned market feature train/test samples: false.

## Gate Results

- manual_message_multinomial_nb: accepted_95=False, rule_or_threshold=`9.494898003833766`, cal_lcb=0.882541, test_lcb=0.730180, cal_support=83, test_support=17, blocker=calibration_or_test_wilson_below_95_or_support_below_floor
- manual_message_regex_rule: accepted_95=False, rule_or_threshold=`has_coin & has_countdown`, cal_lcb=0.899041, test_lcb=0.433602, cal_support=83, test_support=104, blocker=calibration_or_test_wilson_below_95_or_support_below_floor
- cleaned_event_session_candidate_rule: accepted_95=False, rule_or_threshold=`has_vip`, cal_lcb=0.324882, test_lcb=0.329374, cal_support=561, test_support=391, blocker=calibration_or_test_wilson_below_95_or_support_below_floor

## Decision

- Accepted 95 `Manipulation` root: false.
- State: `partial_crypto_event_social_dataset_below_95`.
- Runtime code changed: false.
- Thresholds relaxed: false.
- Trade usable: false.

Bayi-Hu provides direct crypto P&D event/social evidence and manual negative message controls, but the unchanged chronological gates failed held-out 95% Wilson lower bounds; no aligned market-feature samples were acquired in this bounded run.

Next: Acquire or regenerate Bayi-Hu aligned market-feature samples with explicit positive/negative controls, then rerun the unchanged Manipulation gate before trying another source.
