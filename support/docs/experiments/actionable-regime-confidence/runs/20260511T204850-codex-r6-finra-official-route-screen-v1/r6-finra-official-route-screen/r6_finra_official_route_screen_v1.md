# R6 FINRA Official Route Screen v1

Decision: `r6_finra_official_route_screen_v1=official_route_identified_rows_not_acquired`.

Result:
- Official FINRA route identified for spoofing/layering report-card detail data.
- Public/source-owned positive rows acquired: `false`.
- Same-schema matched controls acquired: `false`.
- Intake files created: `false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

Required intake files remain:
- `/tmp/ict-engine-direct-manipulation-row-intake/positive_spoofing_layering_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/matched_negative_normal_activity_rows.csv`
- `/tmp/ict-engine-direct-manipulation-row-intake/provenance_manifest.json`

Candidate routes:
- `finra_potential_manipulation_report`: `blocked_permissioned_report_center_export_required`; rows acquired `false`; https://www.finra.org/compliance-tools/report-center/cross-market-equities-supervision/potential-manipulation-report
- `finra_report_center_technical_assistance`: `blocked_entitled_user_download_required`; rows acquired `false`; https://www.finra.org/compliance-tools/report-center/technical-assistance
- `aimm_gt_public_research_candidate`: `rejected_until_source_owned_spoofing_layering_rows_and_controls_are_exported`; rows acquired `false`; https://arxiv.org/abs/2512.16103
