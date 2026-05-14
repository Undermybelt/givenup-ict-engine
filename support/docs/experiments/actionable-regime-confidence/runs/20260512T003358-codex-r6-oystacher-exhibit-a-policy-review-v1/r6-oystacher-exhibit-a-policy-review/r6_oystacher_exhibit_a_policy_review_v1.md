# R6 Oystacher Exhibit A Policy Review v1

- Run id: `20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1`.
- Materialization reviewed: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/r6_oystacher_exhibit_a_row_materialization_v1.json`.
- Positive candidate rows: `5182`.
- FLIP control candidate rows: `1553`.
- Isolated split axes pass: `true`.
- Source provenance policy: `conditional_candidate_not_canonical_without_owner_user_approval`.
- Control policy: `flip_rows_rejected_as_matched_normal_controls_without_explicit_approval`.
- Canonical merge approved: `false`; downstream chain rerun: `false`.
- Gate result: `r6_oystacher_exhibit_a_policy_review_v1=positive_rows_candidate_controls_rejected_no_canonical_merge`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; external requests sent: `false`; trade usable: `false`.

## Decision

The Oystacher Exhibit A materialization is valuable positive evidence, but it is not enough to mutate the canonical R6 intake under the current Board A contract.

The `SPOOF` rows are source-labeled direct positive candidates. The `FLIP` rows remain blocked as matched normal controls: they are same-defendant, same-exhibit sequence rows, not source-owned normal/non-manipulation labels or report-negative matched controls. Therefore the isolated split pass is not accepted as a strict Board A confidence gate.

## Next

If the user approves RECAP/PACER provenance and explicitly approves `FLIP` rows as matched controls, merge through the shared lock and rerun the direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree chain. Otherwise source independent owner-approved normal controls for the Oystacher `SPOOF` positives.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_review_v1.json`
- Policy decisions CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/r6_oystacher_exhibit_a_policy_decisions_v1.csv`
- Prompt-to-artifact checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/r6-oystacher-exhibit-a-policy-review/prompt_to_artifact_checklist_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003358-codex-r6-oystacher-exhibit-a-policy-review-v1/checks/r6_oystacher_exhibit_a_policy_review_v1_assertions.out`
