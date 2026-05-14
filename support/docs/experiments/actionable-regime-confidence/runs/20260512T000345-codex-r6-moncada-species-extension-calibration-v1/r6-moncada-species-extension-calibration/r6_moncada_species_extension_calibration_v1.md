# R6 Moncada Species Extension Calibration v1

- Run id: `20260512T000345-codex-r6-moncada-species-extension-calibration-v1`
- Baseline source: `docs/experiments/actionable-regime-confidence/runs/20260511T235910-codex-r6-canonical-intake-v57-materialization-v1/r6-canonical-intake-v57-materialization/r6_canonical_intake_v57_materialization.json`
- Moncada candidate source: `docs/experiments/actionable-regime-confidence/runs/20260511T235000-codex-r6-moncada-large-lot-positive-row-candidate-screen-v1/r6-moncada-large-lot-positive-row-candidate-screen/r6_moncada_large_lot_positive_row_candidates_v1.csv`
- Isolated verifier status: `schema_ready_unscored`; return code `0`.
- Rows after isolated extension: positives `79`, matched controls `79`, matched groups `76`.
- Added isolated Moncada large-lot quote-pressure rows: `6` positives and `6` generated same-source controls.
- Pooled Wilson95 min LCB: `0.953627163164`; pooled gate `true`.
- Chronological split gate: `false`; heldout symbol gate `false`; heldout venue gate `false`.
- Moncada non-spoofing species present: `true`; direct species closed: `false`.
- Provider/Auto-Quant/Pre-Bayes/CatBoost/execution-tree command exit codes: `{'provider_status_compact': 0, 'auto_quant_status_agent': 0, 'pre_bayes_status_nq': 0, 'policy_training_status_nq': 0, 'workflow_status_execution_candidate': 0, 'workflow_status_structural_feedback': 0, 'export_structural_path_ranking_target': 0}`.
- Runtime readback: provider `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`; workflow `observe/observe`; policy matched rows `[0, 0]`.
- Gate result: `r6_moncada_species_extension_calibration_v1=pooled_wilson95_passed_nonspoofing_species_added_split_species_full_objective_still_blocked`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/r6_moncada_species_extension_calibration_v1.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/r6_moncada_species_extension_calibration_v1.md`
- Positive rows CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/positive_spoofing_layering_rows_moncada_species_v1.csv`
- Matched controls CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/matched_negative_normal_activity_rows_moncada_species_v1.csv`
- Provenance: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/isolated-direct-intake/provenance_manifest.json`
- Split metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/r6_moncada_species_extension_split_metrics_v1.csv`
- Species metrics: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/r6-moncada-species-extension-calibration/r6_moncada_species_extension_species_metrics_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000345-codex-r6-moncada-species-extension-calibration-v1/checks/r6_moncada_species_extension_calibration_v1_assertions.out`

## Next
Do not accept R6 yet: source and materialize enough direct rows for chronological, heldout-symbol, heldout-venue, and missing direct species coverage; separately keep R5 recency and R3 native-subhour acquisition open.
