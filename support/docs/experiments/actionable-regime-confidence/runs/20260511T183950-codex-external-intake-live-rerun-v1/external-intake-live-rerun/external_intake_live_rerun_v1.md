# External Intake Live Rerun v1

Run ID: `20260511T183950+0800-codex-external-intake-live-rerun-v1`

## Decision

- Gate result: `external_intake_live_rerun_v1=missing_required_files_still_blocked`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Verifier return code: `2`.
- Required files: `7`; missing files: `7`.
- Missing packages: `direct_manipulation_species, price_root_equivalence, source_panel_recency_extension`.

## Missing Files

- `/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_rows.csv`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/price-root/source_label_equivalence_provenance.json`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_rows.csv`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/recency/source_panel_recency_extension_provenance.json`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_positive_rows.csv`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_matched_controls.csv`
- `/tmp/ict-engine-board-a-external-intake-bundle-v1/direct-manipulation/direct_manipulation_provenance.json`

## Guardrail

No downstream calibration or goal-completion audit should treat this bundle as satisfied until every required source-owned/owner-approved file is present and the verifier returns a non-blocked status.
