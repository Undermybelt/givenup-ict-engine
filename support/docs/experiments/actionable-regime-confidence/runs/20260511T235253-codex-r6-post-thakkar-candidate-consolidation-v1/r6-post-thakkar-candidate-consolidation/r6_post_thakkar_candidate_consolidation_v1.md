# R6 Post-Thakkar Candidate Consolidation v1

Run id: `20260511T235253-codex-r6-post-thakkar-candidate-consolidation-v1`
Generated at UTC: `2026-05-11T15:54:33.377988+00:00`

## Result

- Canonical live intake exists now: `False`.
- Direct verifier blocked on missing files: `True`.
- V54 durable baseline positives/controls: `57/57`.
- Unique proposed positives after de-duplication: `34`.
- Duplicate proposed candidate rows ignored: `0`.
- Proposed matched-control rows currently materialized in sidecar packets: `2`.
- What-if positives after all unique sidecars: `91`.
- What-if min Wilson95 LCB after all unique sidecars: `0.954180263735`.
- Pooled what-if Wilson95 pass: `True`.
- Gate result: `r6_post_thakkar_candidate_consolidation_v1=pooled_whatif_passes_but_live_intake_missing_and_split_gates_not_rerun`.
- Strict full objective achieved: `False`; `update_goal=False`.

## Fail-Closed Decision

- This run did not mutate the shared intake and did not accept any sidecar rows.
- The pooled what-if is above `0.95`, but the live intake is missing, candidate matched controls are incomplete, and chronological/symbol/venue split gates have not rerun.
- R5 source-panel recency and R3 native-subhour blockers remain outside this direct R6 sidecar consolidation.
