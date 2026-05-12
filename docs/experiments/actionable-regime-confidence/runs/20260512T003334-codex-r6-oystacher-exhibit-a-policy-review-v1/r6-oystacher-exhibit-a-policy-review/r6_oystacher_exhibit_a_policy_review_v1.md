# R6 Oystacher Exhibit A Policy Review v1

- Run id: `20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1`.
- Source materialization: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/r6_oystacher_exhibit_a_row_materialization_v1.json`.
- Parsed order rows: `6735`; side counts: `{'SPOOF': 5182, 'FLIP': 1553}`.
- Positive SPOOF candidates: `5182`.
- FLIP same-exhibit control candidates: `1553`.
- Isolated split axes pass: `true`; minimum split Wilson95 LCB: `0.95771100465`.
- Gate result: `r6_oystacher_exhibit_a_policy_review_v1=positive_source_passed_flip_controls_rejected_no_canonical_merge`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

- Public RECAP/CourtListener Exhibit A is sufficient to preserve Oystacher `SPOOF` rows as positive candidates for policy review.
- The same exhibit's `FLIP` rows are not accepted as `matched_negative_normal_activity` under the current R6 contract because they are sequence counterpart legs, not source-owned normal/non-manipulation controls.
- Canonical intake merge and downstream rerun remain blocked unless the user/owner explicitly approves the FLIP-control contract or supplies source-owned normal controls.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json`
- Policy checks CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_checks_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003334-codex-r6-oystacher-exhibit-a-policy-review-v1/checks/r6_oystacher_exhibit_a_policy_review_v1_assertions.out`

## Next

Keep Oystacher Exhibit A rows isolated unless the user/owner explicitly approves same-exhibit FLIP rows as controls or supplies source-owned normal controls; after approval or new controls, merge through the verifier-native contract and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback while keeping R5 and R3 blocked.
