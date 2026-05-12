# R6 Optiver Marking-Close Positive Row Candidate Screen v1

- Run id: `20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1`
- Source owner: CFTC public press release and complaint packet.
- Candidate direct species: `painting_tape_marking_close`.
- Proposed positive rows: `19`.
- Matched normal controls acquired: `false`.
- Shared intake mutated: `false`.
- Gate result: `r6_optiver_marking_close_positive_row_candidate_screen_v1=proposed_rows_only_missing_matched_controls_split_species_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.

## Sources
- `cftc_press_5521_08`: https://www.cftc.gov/PressRoom/PressReleases/5521-08 status `http_200`, sha256 `56eb273880fb1a8fa5e4a539f221ea6d1272cc26c7566dd558b9532a089b96c7`
- `cftc_optiver_complaint_pdf`: https://www.cftc.gov/sites/default/files/idc/groups/public/%40lrenforcementactions/documents/legalpleading/enfoptiveruscomplaint072408.pdf status `http_200`, sha256 `3ce2407ab94fcb5f93cce6dfbbc13a74cad200d84dde4f33faafbd655ea0e07d`
- `cftc_optiver_chart_pdf`: https://www.cftc.gov/sites/default/files/idc/groups/public/%40newsroom/documents/file/enfoptiverchart.pdf status `http_200`, sha256 `6538dbd7cf4f747bc8ababa5115898cde2182d71ccbafbfca8144213f8dff18e`

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/r6-optiver-marking-close-positive-row-candidate-screen/r6_optiver_marking_close_positive_row_candidate_screen_v1.json`
- Proposed rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/r6-optiver-marking-close-positive-row-candidate-screen/r6_optiver_marking_close_positive_row_candidates_v1.csv`
- Source screen CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/r6-optiver-marking-close-positive-row-candidate-screen/r6_optiver_marking_close_source_screen_v1_sources.csv`
- Live direct verifier stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/checks/r6_optiver_marking_close_positive_row_candidate_screen_v1_assertions.out`

## Runtime Chain Readback
- `provider_status` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/provider_status.stdout.txt`
- `auto_quant_status` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/auto_quant_status.stdout.txt`
- `analyze_demo` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/analyze_demo.stdout.txt`
- `pre_bayes_status` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/pre_bayes_status.stdout.txt`
- `policy_training_status` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/policy_training_status.stdout.txt`
- `workflow_status_execution_candidate` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/workflow_status_execution_candidate.stdout.txt`
- `structural_path_ranking_target` returned `0`; stdout `docs/experiments/actionable-regime-confidence/runs/20260512T001100-codex-r6-optiver-marking-close-positive-row-candidate-screen-v1/command-output/structural_path_ranking_target.stdout.txt`

## Decision
The official CFTC complaint exposes a concrete 19-instance date/product table for a non-spoofing marking-close species. It still cannot be accepted into the canonical direct intake because the public packet does not expose same-schema matched normal controls, instance-level quantities, or a control provenance manifest.
