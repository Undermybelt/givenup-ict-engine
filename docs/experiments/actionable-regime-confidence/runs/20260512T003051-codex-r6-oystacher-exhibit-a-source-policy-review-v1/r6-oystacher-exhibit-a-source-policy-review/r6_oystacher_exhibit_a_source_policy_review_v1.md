# R6 Oystacher Exhibit A Source Policy Review v1

- Run id: `20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1`.
- Source materialization: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1`.
- Positive rows: `5182`; matched controls: `1553`; matched groups: `1313`.
- Isolated verifier status: `schema_ready_unscored`.
- Isolated split axes pass: `True`.
- Promotion candidate: `true`, because the public court exhibit has row-level SPOOF/FLIP order-lifecycle data and isolated split axes pass.
- Source policy gate: `false`, because no explicit board/user approval exists yet for promoting the CourtListener RECAP/PACER mirror into canonical R6 intake.
- Gate result: `r6_oystacher_exhibit_a_source_policy_review_v1=row_evidence_strong_policy_approval_required_before_canonical_merge`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; shared intake mutated: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/r6-oystacher-exhibit-a-source-policy-review/r6_oystacher_exhibit_a_source_policy_review_v1.json`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/r6-oystacher-exhibit-a-source-policy-review/r6_oystacher_exhibit_a_source_policy_review_checklist_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003051-codex-r6-oystacher-exhibit-a-source-policy-review-v1/checks/r6_oystacher_exhibit_a_source_policy_review_v1_assertions.out`

## Next

Record explicit board/user approval for using the public RECAP/PACER Exhibit A rows, then copy the isolated intake into the owner-export target or canonical live root under a shared lock and rerun direct verifier, split calibration, provider, Auto-Quant, pre-Bayes/BBN, CatBoost/path-ranking, and execution-tree readback.
