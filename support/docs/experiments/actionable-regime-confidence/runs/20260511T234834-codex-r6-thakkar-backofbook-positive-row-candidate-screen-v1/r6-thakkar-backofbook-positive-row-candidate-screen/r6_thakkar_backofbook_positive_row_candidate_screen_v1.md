# R6 Thakkar Back-of-Book Positive Row Candidate Screen v1

- Run id: `20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1`
- Generated at UTC: `2026-05-11T15:53:33.057160+00:00`
- Official source: https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfthakkarcomplaint012818.pdf
- Live shared intake status: `blocked`
- Shared intake mutated: `false`
- Proposed positive rows: `4`
- Proposed matched-control rows: `2`
- Latest verified baseline positives: `57`
- Sarao sidecar positives: `6`
- Nowak/Smith sidecar positives: `6`
- What-if positives after Sarao + Nowak/Smith + Thakkar: `73`
- What-if min Wilson95 LCB after all three sidecars: `0.950006246616`
- Additional positive rows needed after all three sidecars: `0`
- Gate result: `r6_thakkar_backofbook_positive_row_candidate_screen_v1=sidecar_candidates_enough_for_pooled_wilson_but_live_intake_missing`
- Next action: Restore or re-materialize the shared R6 direct intake under a fresh lock, then decide whether to accept Sarao, Nowak/Smith, and Thakkar candidates with matched controls and rerun direct plus sidecar calibration; do not claim acceptance from sidecar what-if evidence while the live intake is missing.

## Boundary

This run does not mutate `/tmp/ict-engine-direct-manipulation-row-intake`. Because that live root is currently missing, this is candidate evidence only; acceptance still requires a fresh locked intake restoration, matched-control policy application, and full direct plus sidecar calibration rerun.

## Artifacts

- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_positive_row_candidate_screen_v1.json`
- Proposed positives CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_positive_row_candidates_v1.csv`
- Proposed controls CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_matched_control_candidates_v1.csv`
- Source screen CSV: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/r6-thakkar-backofbook-positive-row-candidate-screen/r6_thakkar_backofbook_positive_row_source_screen_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T234834-codex-r6-thakkar-backofbook-positive-row-candidate-screen-v1/checks/r6_thakkar_backofbook_positive_row_candidate_screen_v1_assertions.out`
