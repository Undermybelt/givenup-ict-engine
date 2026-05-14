# R6 Owner Export Target Verifier After 030300 v1

Run id: `20260512T030617-codex-r6-owner-export-target-verifier-after-030300-v1`

Gate result: `r6_owner_export_target_verifier_after_030300_v1=owner_export_target_missing_required_files_no_promotion`

## Objective Mapping

This packet reruns the live direct verifier against the active R6 owner-export target after the `030300` provider/Auto-Quant read-only refresh. It checks the current next-action blocker directly instead of inferring from provider readiness or source-discovery screens.

## Command

`python3 docs/experiments/actionable-regime-confidence/runs/20260511T151950-codex-direct-manipulation-row-intake-manifest-v1/direct-manipulation-intake/direct_manipulation_row_intake_verifier_v1.py --intake-root /tmp/ict-engine-board-a-r6-owner-export-v1`

## Readback

- Exit code: `2`
- Verifier status: `blocked`
- Verifier reason: `missing_required_files`
- Missing files:
  - `/tmp/ict-engine-board-a-r6-owner-export-v1/positive_spoofing_layering_rows.csv`
  - `/tmp/ict-engine-board-a-r6-owner-export-v1/matched_negative_normal_activity_rows.csv`
  - `/tmp/ict-engine-board-a-r6-owner-export-v1/provenance_manifest.json`
- Approval package still present only as a non-approving decision package: `/private/tmp/r6_oystacher_approval_decision_package_v1.json.valid`

## Decision

The owner-export target is not verifier-ready. No source-owned normal controls, explicit `FLIP` approval, canonical merge input, or downstream promotion input is present. The downstream chain remains disallowed.

## Promotion Guards

- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion rerun allowed: `false`
- Strict full objective achieved: `false`
- Trade usable: `false`
- `update_goal=false`
- Runtime code changed: `false`
- Shared intake mutated: `false`
- R3/R5/R6 roots mutated: `false`
- Thresholds relaxed: `false`
- Raw data committed: `false`

## Artifacts

- Command stdout: `docs/experiments/actionable-regime-confidence/runs/20260512T030617-codex-r6-owner-export-target-verifier-after-030300-v1/command-output/owner_export_direct_verifier.stdout.txt`
- Command stderr: `docs/experiments/actionable-regime-confidence/runs/20260512T030617-codex-r6-owner-export-target-verifier-after-030300-v1/command-output/owner_export_direct_verifier.stderr.txt`
- Command exit: `docs/experiments/actionable-regime-confidence/runs/20260512T030617-codex-r6-owner-export-target-verifier-after-030300-v1/command-output/owner_export_direct_verifier.exit`
- Command text: `docs/experiments/actionable-regime-confidence/runs/20260512T030617-codex-r6-owner-export-target-verifier-after-030300-v1/command-output/owner_export_direct_verifier.cmd`

## Next

Preserve the Current Cursor next action for R6. Continue only from owner/operator R6 export delivery, explicit `FLIP` approval, or genuinely source-owned cross-timeframe `MainRegimeV2` labels before canonical merge and downstream promotion.
