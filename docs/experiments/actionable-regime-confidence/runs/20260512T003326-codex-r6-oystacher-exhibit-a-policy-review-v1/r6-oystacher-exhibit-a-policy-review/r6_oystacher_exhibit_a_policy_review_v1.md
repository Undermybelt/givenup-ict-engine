# R6 Oystacher Exhibit A Policy Review v1

- Run id: `20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1`.
- Materialization run: `20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1`.
- Parsed order rows: `6735`; SPOOF rows: `5182`; FLIP rows: `1553`.
- Positive source decision: `usable_as_positive_candidate_only`.
- Matched control decision: `rejected_flip_rows_not_normal_controls`.
- Canonical live intake merge allowed: `false`.
- Downstream chain rerun allowed: `false`.
- Gate result: `r6_oystacher_exhibit_a_policy_review_v1=positive_source_candidate_controls_rejected_no_canonical_merge`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Rationale

Court-filed Exhibit A is useful as a positive source candidate because it directly marks SPOOF rows. The FLIP rows are not accepted as normal controls because they are from the same alleged flip sequences and same defendant activity, so treating them as `matched_negative_normal_activity` would mislabel the control side.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json`
- Decision matrix: `docs/experiments/actionable-regime-confidence/runs/20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_decision_matrix_v1.csv`
- Control-label risk CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_control_label_risk_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003326-codex-r6-oystacher-exhibit-a-policy-review-v1/checks/r6_oystacher_exhibit_a_policy_review_v1_assertions.out`
