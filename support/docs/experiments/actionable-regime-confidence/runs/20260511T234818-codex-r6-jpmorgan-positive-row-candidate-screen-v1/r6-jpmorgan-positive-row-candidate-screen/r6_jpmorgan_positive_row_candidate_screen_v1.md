# R6 JPMorgan Positive Row Candidate Screen v1

- Run id: `20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1`
- Generated at UTC: `2026-05-11T15:50:57.069301+00:00`
- Official source: https://www.cftc.gov/media/4826/enfjpmorganchaseorder092920/download
- Shared intake mutated: `false`
- Live verifier status: `blocked`
- Baseline positive rows used for what-if: `57` from `v54_verifier_artifact_live_intake_missing_or_blocked`
- Proposed positive rows: `8`
- What-if positives after Sarao + Nowak/Smith + JPMorgan sidecars: `77`
- What-if min Wilson95 LCB after all sidecars: `0.952479911333`
- Additional rows still needed after all sidecars if all accepted: `0`
- Gate result: `r6_jpmorgan_positive_row_candidate_screen_v1=proposed_rows_reach_pooled_whatif_but_live_intake_missing`
- Next action: Reconstruct or lock the shared direct intake, accept Sarao/Nowak/JPMorgan positives only with matched same-source controls, then rerun the direct verifier and sidecar broad-normal calibration; do not claim a new confidence gate until live intake and split/species gates pass.

## Artifacts
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidate_screen_v1.json`
- Proposed rows CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_candidates_v1.csv`
- Source screen CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/r6-jpmorgan-positive-row-candidate-screen/r6_jpmorgan_positive_row_source_screen_v1_cases.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234818-codex-r6-jpmorgan-positive-row-candidate-screen-v1/checks/r6_jpmorgan_positive_row_candidate_screen_v1_assertions.out`
