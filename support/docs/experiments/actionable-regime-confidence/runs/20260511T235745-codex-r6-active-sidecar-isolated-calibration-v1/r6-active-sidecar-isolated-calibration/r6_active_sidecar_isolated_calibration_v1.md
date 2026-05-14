# R6 Active Sidecar Isolated Calibration v1

- Run id: `20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1`
- Verifier status: `schema_ready_unscored`; return code `0`.
- Baseline reconstructed from durable V55 rows after excluding prior sidecars: `57/57`.
- Active sidecar positives materialized only in this isolated preflight: Sarao `6`, Nowak/Smith `6`, Thakkar `4`.
- Final isolated direct rows: positives `73`, matched controls `73`, broad-normal sidecar controls `80`.
- Pooled Wilson95 min LCB: `0.950007992044`; pooled gate `true`.
- Chronological split gate: `false`; heldout symbol gate: `false`; heldout venue gate: `false`.
- Direct species closed: `false`.
- Canonical shared intake mutated: `false`.
- Gate result: `r6_active_sidecar_isolated_calibration_v1=pooled_wilson95_passed_split_species_canonical_intake_still_blocked`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

## Interpretation

This run converts the active Thakkar what-if into a durable isolated verifier packet with canonical filenames. It still does not accept a Board A confidence gate because the shared canonical intake is absent, matched controls are policy-preflight only, and chronological/symbol/venue plus species gates fail.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/r6-active-sidecar-isolated-calibration/r6_active_sidecar_isolated_calibration_v1.json`
- Isolated intake root: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/r6-active-sidecar-isolated-calibration/isolated-direct-intake`
- Split metrics: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/r6-active-sidecar-isolated-calibration/r6_active_sidecar_isolated_calibration_v1_split_metrics.csv`
- Gates: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/r6-active-sidecar-isolated-calibration/r6_active_sidecar_isolated_calibration_v1_gates.csv`
- Source steps: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/r6-active-sidecar-isolated-calibration/r6_active_sidecar_isolated_calibration_v1_source_steps.csv`
- Verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/command-output/direct_manipulation_row_intake_verifier.stdout.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T235745-codex-r6-active-sidecar-isolated-calibration-v1/checks/r6_active_sidecar_isolated_calibration_v1_assertions.out`
