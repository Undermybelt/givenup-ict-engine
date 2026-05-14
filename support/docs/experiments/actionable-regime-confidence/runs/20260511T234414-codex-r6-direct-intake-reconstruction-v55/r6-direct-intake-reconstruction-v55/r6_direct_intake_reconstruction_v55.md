# R6 Direct Intake Reconstruction v55

- Run id: `20260511T234414-codex-r6-direct-intake-reconstruction-v55`
- Isolated intake root: `/tmp/ict-engine-r6-direct-intake-reconstruction-v55/intake`
- V54 baseline reconstructed: `57/57`.
- Accepted candidate positives in isolated reconstruction: Sarao `6`, Nowak/Smith `6`, JPM CFTC `4`.
- Final direct rows: positives `73`, same-event controls `73`, sidecar broad-normal controls `80`.
- Pooled Wilson95 min LCB: `0.950006246616`; pooled gate `true`.
- Chronological split gate: `false`; heldout symbol gate `false`; heldout venue gate `false`.
- Direct species closed: `false`.
- Gate result: `r6_direct_intake_reconstruction_v55=pooled_wilson95_passed_split_species_full_objective_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/r6_direct_intake_reconstruction_v55.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/r6_direct_intake_reconstruction_v55.md`
- Positive rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/positive_spoofing_layering_rows_v55.csv`
- Matched control CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/matched_negative_normal_activity_rows_v55.csv`
- Split metrics CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/r6_direct_intake_reconstruction_v55_split_metrics.csv`
- Reconstruction steps CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction-v55/r6_direct_intake_reconstruction_v55_steps.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/checks/r6_direct_intake_reconstruction_v55_assertions.out`

## Next
Do not call update_goal. R6 pooled Wilson95 now passes in isolated reconstruction, but chronological/symbol/venue split support and direct species coverage remain blocked; continue sourcing non-spoofing direct Manipulation species and restore R5 source-owner recency.
