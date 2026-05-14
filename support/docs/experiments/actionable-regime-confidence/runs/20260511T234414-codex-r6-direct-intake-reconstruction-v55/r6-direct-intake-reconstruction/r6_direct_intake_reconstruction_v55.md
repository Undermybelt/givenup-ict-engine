# R6 Direct Intake Reconstruction v55

Run ID: `20260511T234414+0800-codex-r6-direct-intake-reconstruction-v55`

## Result

- Isolated verifier status: `schema_ready_unscored`.
- Isolated reconstructed rows: positives `53`, matched negatives `53`, matched groups `52`.
- V54 durable baseline rows: positives `57`, matched negatives `57`.
- Reconstruction gap vs V54: positives `4`, matched negatives `4`.
- Reconstructed Wilson95 min LCB: `0.932415695547`.
- Sarao plus Nowak/Smith proposed positives: `12`; V54 what-if rows `69`; V54 what-if Wilson95 LCB `0.947260905856`.
- Additional all-correct positives still needed after both sidecars on the V54 baseline: `4`.
- Gate result: `r6_direct_intake_reconstruction_v55=isolated_schema_ready_reconstruction_incomplete_confidence_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Interpretation

The isolated CSVs are schema-ready, but the durable reconstruction does not reproduce the saved V54 `57/57` state. This confirms the live `/tmp` root was carrying mutable state that was not fully snapshotted as versioned row CSVs. Sarao and Nowak/Smith remain proposed positives only until matched controls are materialized and the base intake is rehydrated.

## Artifacts

- Reconstruction JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/r6_direct_intake_reconstruction_v55.json`
- Isolated positive rows: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/isolated-direct-intake/positive_spoofing_layering_rows.csv`
- Isolated matched controls: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/isolated-direct-intake/matched_negative_normal_activity_rows.csv`
- Isolated provenance: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/isolated-direct-intake/provenance_manifest.json`
- Gates CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/r6_direct_intake_reconstruction_v55_gates.csv`
- Source steps CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/r6_direct_intake_reconstruction_v55_source_steps.csv`
- Verifier stdout/stderr: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/direct_manipulation_row_intake_verifier.stdout.txt`, `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/r6-direct-intake-reconstruction/direct_manipulation_row_intake_verifier.stderr.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234414-codex-r6-direct-intake-reconstruction-v55/checks/r6_direct_intake_reconstruction_v55_assertions.out`
