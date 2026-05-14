# R6 Athena Marking-Close Non-Spoofing Candidate Screen v1

- Run id: `20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1`.
- Official source fetched: `true`; content type `application/pdf`; PDF bytes `71622`.
- Candidate species: `marking_close_gravy`.
- Candidate rows: `10` across symbols `EBAY` and venues `BATS, NASDAQ, NASDAQ / lit market, NASDAQ / lit markets, NASDAQ closing cross`.
- What-if positive support if future policy accepts these rows: `83`; positive-only Wilson95 LCB `0.955763136561`.
- Accepted rows added: `0`; matched controls materialized: `false`; live intake mutated: `false`.
- Gate result: `r6_athena_marking_close_nonspoofing_candidate_screen_v1=nonspoofing_marking_close_candidate_rows_found_controls_and_splits_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1/r6-athena-marking-close-nonspoofing-candidate-screen/r6_athena_marking_close_nonspoofing_candidate_screen_v1.json`
- Candidate CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1/r6-athena-marking-close-nonspoofing-candidate-screen/r6_athena_marking_close_nonspoofing_candidates_v1.csv`
- Source extraction stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001226-codex-r6-athena-marking-close-nonspoofing-candidate-screen-v1/checks/r6_athena_marking_close_nonspoofing_candidate_screen_v1_assertions.out`

## Source Check

- Source URL: `https://www.sec.gov/files/litigation/admin/2014/34-73369.pdf`
- Verified markers include `EBAY`, `3:50:00.578`, `15:59:58.355`, `15:59:59.950`, and `4:00:03.348`.
