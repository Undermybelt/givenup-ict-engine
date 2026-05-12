# R6 Oystacher Exact-Date Candidate Extract v1

- Run id: `20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1`.
- Official CFTC complaint URL: `https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfigorcomplnt101915.pdf`.
- Exact source dates extracted: `51`.
- Source groups: `6`.
- Aggregate source totals: flip sequences `1316`, spoof orders `5207`, spoof contracts `359790`.
- Candidate status: `positive_date_candidate_only_controls_missing`.
- This does not solve the current R6 gate: the dates are pre-2020, order-time/order-id rows are absent, and matched normal controls are absent.
- Gate result: `r6_oystacher_exact_date_candidate_extract_v1=exact_dates_extracted_controls_and_order_times_missing_no_acceptance`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: false. `update_goal=false`.

## Artifacts

- Candidate rows: `docs/experiments/actionable-regime-confidence/runs/20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1/r6-oystacher-exact-date-candidate-extract/r6_oystacher_exact_date_positive_candidates_v1.csv`
- Source date ranges: `docs/experiments/actionable-regime-confidence/runs/20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1/r6-oystacher-exact-date-candidate-extract/r6_oystacher_exact_date_source_groups_v1.csv`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1/r6-oystacher-exact-date-candidate-extract/r6_oystacher_exact_date_candidate_extract_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001635-codex-r6-oystacher-exact-date-candidate-extract-v1/checks/r6_oystacher_exact_date_candidate_extract_v1_assertions.out`
