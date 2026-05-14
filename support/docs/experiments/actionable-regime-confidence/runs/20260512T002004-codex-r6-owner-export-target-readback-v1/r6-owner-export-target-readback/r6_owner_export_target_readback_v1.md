# R6 Owner Export Target Readback v1

- Run id: `20260512T002004-codex-r6-owner-export-target-readback-v1`.
- Target root: `/tmp/ict-engine-board-a-r6-owner-export-v1`.
- Target root exists: `false`.
- Missing required files: `direct_manipulation_positive_rows.csv, direct_manipulation_matched_controls.csv, direct_manipulation_provenance.json`.
- Missing unchanged-verifier files: `positive_spoofing_layering_rows.csv, matched_negative_normal_activity_rows.csv, provenance_manifest.json`.
- Request/verifier filename mismatch: `true`.
- Explicit approval file present: `false`.
- Direct verifier return code: `2`.
- Gate result: `r6_owner_export_target_readback_v1=target_root_missing_request_verifier_names_mismatch_no_chain_rerun`.
- Accepted rows added: `0`; new confidence gate: `false`; strict full objective achieved: `false`; `update_goal=false`.
- Downstream chain rerun: `false`, because no owner export files or explicit split-contract approval are present.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T002004-codex-r6-owner-export-target-readback-v1/r6-owner-export-target-readback/r6_owner_export_target_readback_v1.json`
- Direct verifier stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T002004-codex-r6-owner-export-target-readback-v1/command-output/direct_manipulation_row_intake_verifier_owner_export_target.stdout.txt`
- Direct verifier stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T002004-codex-r6-owner-export-target-readback-v1/command-output/direct_manipulation_row_intake_verifier_owner_export_target.stderr.txt`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002004-codex-r6-owner-export-target-readback-v1/checks/r6_owner_export_target_readback_v1_assertions.out`
