# R6 Logista/Serotta CFTC Row Uplift v1

Run ID: `20260511T220727+0800-codex-r6-logista-serotta-cftc-row-uplift-v1`

## Result

- Added positive rows: `3`.
- Added matched same-complaint genuine-control rows: `3`.
- Duplicate/already-present readback: `False`.
- Direct verifier after uplift: `schema_ready_unscored` with positives `60`, matched negatives `60`, matched groups `59`.
- Examples 4 and 5 were screened but not materialized because they are aggregate/supervision-oriented rather than clean row-level Count I spoof rows.
- Same-complaint controls remain schema/control seeds only; broad normal sample is still `false`.
- Gate result: `r6_logista_serotta_cftc_row_uplift_v1=three_complaint_examples_added_calibration_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
