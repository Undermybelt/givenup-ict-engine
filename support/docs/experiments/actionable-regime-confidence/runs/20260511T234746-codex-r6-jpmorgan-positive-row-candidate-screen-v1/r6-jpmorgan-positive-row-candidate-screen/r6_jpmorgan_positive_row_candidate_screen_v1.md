# R6 JPMorgan Positive Row Candidate Screen v1

- Run id: `20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1`
- Generated at UTC: `2026-05-11T15:53:21.422531+00:00`
- Official source: https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download
- Shared intake mutated: `false`
- Live direct verifier status: `blocked` from return code `2`.
- Base count source: `v54_artifact_fallback_because_live_shared_intake_not_ready`; base positives `57`.
- Proposed JPMorgan positives: `7`; proposed JPMorgan matched controls: `7`.
- Existing proposed sidecars: Sarao `6`, Nowak/Smith `6`.
- Current/base Wilson95 LCB: `0.936858991217`.
- What-if positives after Sarao + Nowak/Smith + JPMorgan: `76`.
- What-if min Wilson95 LCB after all three sidecars: `0.951884731769`.
- Additional positive rows still needed after all three sidecars: `0`.
- Gate result: `r6_jpmorgan_positive_row_candidate_screen_v1=proposed_rows_only_pooled_whatif_pass_live_split_still_blocked`.
- Live acceptance remains blocked because this run did not mutate or rebuild the shared intake, and chronological/symbol/venue split plus direct-species gates still need a live calibration rerun.

## Artifacts
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidate_screen_v1.json`
- Proposed positives CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidates_v1.csv`
- Proposed controls CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_matched_control_candidates_v1.csv`
- Source screen CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_source_screen_v1_cases.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234746-codex-r6-jpmorgan-positive-row-candidate-screen-v1/checks/r6_jpmorgan_positive_row_candidate_screen_v1_assertions.out`
