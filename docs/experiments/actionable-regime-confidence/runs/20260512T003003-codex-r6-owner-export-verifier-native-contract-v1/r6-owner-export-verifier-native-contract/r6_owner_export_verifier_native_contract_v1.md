# R6 Owner Export Verifier-Native Contract v1

- Run id: `20260512T003003-codex-r6-owner-export-verifier-native-contract-v1`.
- Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- This is a contract/mapping artifact only: no adapter was created and runtime verifier behavior was not changed.
- Verifier-native required files:
  - `positive_spoofing_layering_rows.csv`
  - `matched_negative_normal_activity_rows.csv`
  - `provenance_manifest.json`
- V62 owner-facing filenames are treated as aliases only; they are not accepted by the unchanged verifier unless copied/adapted under explicit approval.
- Gate result: `r6_owner_export_verifier_native_contract_v1=contract_ready_no_rows_or_adapter_created`.
- Accepted rows added: `0`; strict full objective achieved: `false`; `update_goal=false`.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/r6-owner-export-verifier-native-contract/r6_owner_export_verifier_native_contract_v1.json`
- File matrix: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/r6-owner-export-verifier-native-contract/r6_owner_export_verifier_native_files_v1.csv`
- Field mapping: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/r6-owner-export-verifier-native-contract/r6_owner_export_to_verifier_mapping_v1.csv`
- Positive header template: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/r6-owner-export-verifier-native-contract/positive_spoofing_layering_rows.header.csv`
- Matched-control header template: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/r6-owner-export-verifier-native-contract/matched_negative_normal_activity_rows.header.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T003003-codex-r6-owner-export-verifier-native-contract-v1/checks/r6_owner_export_verifier_native_contract_v1_assertions.out`

## Next

Drop verifier-native files under the target root, or provide explicit approval for an adapter/contract change, then rerun direct verifier and the provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree chain.
