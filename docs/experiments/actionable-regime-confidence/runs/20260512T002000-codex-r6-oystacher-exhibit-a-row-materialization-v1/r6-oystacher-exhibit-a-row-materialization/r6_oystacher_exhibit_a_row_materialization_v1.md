# R6 Oystacher Exhibit A Row Materialization v1

- Run id: `20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1`.
- Public Exhibit A PDF: `https://storage.courtlistener.com/recap/gov.uscourts.ilnd.316889/gov.uscourts.ilnd.316889.1.1.pdf`.
- Pages: `116`; parsed order rows: `6735`; unparsed candidate lines: `8`.
- Parsed side counts: `{'SPOOF': 5182, 'FLIP': 1553}`.
- Isolated candidate intake verifier status: `schema_ready_unscored`; positives `5182`; controls `1553`; matched groups `1313`.
- Split axes pass in isolated materialization: `true`.
- Canonical live intake mutated: `false`; accepted rows added: `0`; source policy review required before promotion.
- Gate result: `r6_oystacher_exhibit_a_row_materialization_v1=public_court_exhibit_rows_isolated_schema_ready_policy_review_required`.
- Strict full objective achieved: `false`; `update_goal=false`.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/r6_oystacher_exhibit_a_row_materialization_v1.json`
- Parsed rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/oystacher_exhibit_a_parsed_order_rows_v1.csv`
- Candidate positive CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/isolated-oystacher-exhibit-a-intake/positive_spoofing_layering_rows.csv`
- Candidate matched-control CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/isolated-oystacher-exhibit-a-intake/matched_negative_normal_activity_rows.csv`
- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/oystacher_exhibit_a_split_metrics_v1.csv`
- Unparsed candidate lines CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/r6-oystacher-exhibit-a-row-materialization/oystacher_exhibit_a_unparsed_candidate_lines_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002000-codex-r6-oystacher-exhibit-a-row-materialization-v1/checks/r6_oystacher_exhibit_a_row_materialization_v1_assertions.out`
