# R6 Oystacher Public Appendix Trace v1

- Run id: `20260512T001700-codex-r6-oystacher-public-appendix-trace-v1`.
- Direct verifier status: `schema_ready_unscored`; positives `73`; matched negatives `73`; matched groups `70`.
- Prior Oystacher screen found aggregate source totals: trading days `51`, flip sequences `1316`, spoof orders `5207`, spoof contracts `359790`.
- V59 debt reference still requires chronological additional rows `219` before exact symbol/venue gates; exact-symbol debt `2559`; exact-venue debt `732`.
- Public appendix materialized: `false`.
- Gate result: `r6_oystacher_public_appendix_trace_v1=public_sources_confirm_large_aggregate_but_no_row_appendix_materialized`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Source Trace

| Source | Row Appendix Visible | Board A Utility | Blocker |
|---|---:|---|---|
| `cftc_oystacher_complaint_public_pdf` | `false` | confirms source-owned large aggregate row universe and Exhibit A reference | public PDF artifact does not expose the row appendix needed for timestamp/order-leg ingestion |
| `cftc_oystacher_press_release` | `false` | confirms official enforcement context and source identity | summary page is not a row-level order-lifecycle export |
| `secondary_oystacher_aggregate_table` | `false` | corroborates that public discourse preserves aggregate counts, not Board A rows | secondary summary cannot source-own positive labels or matched controls |

## Interpretation

- The Oystacher source remains the most promising public lead because its aggregate counts exceed the current chronological and pairwise debt scale.
- The public materials reviewed here still stop at aggregate counts or source-description level; they do not materialize the row appendix with timestamps/order legs needed for Board A ingestion.
- No sidecar row is accepted by this trace. The next acceptance attempt still needs the actual Exhibit A appendix, an owner-approved equivalent export, or explicit approval for a different heldout contract.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001700-codex-r6-oystacher-public-appendix-trace-v1/r6-oystacher-public-appendix-trace/r6_oystacher_public_appendix_trace_v1.json`
- Source CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001700-codex-r6-oystacher-public-appendix-trace-v1/r6-oystacher-public-appendix-trace/r6_oystacher_public_appendix_sources_v1.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T001700-codex-r6-oystacher-public-appendix-trace-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001700-codex-r6-oystacher-public-appendix-trace-v1/checks/r6_oystacher_public_appendix_trace_v1_assertions.out`
