# 012425 Restoration Readback v1

Gate result: `012425_restoration_readback_v1=restored_reference_complete_no_promotion`.

Current board:
- board_state: `blocked`
- last_loop_id: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`
- board SHA-256 before artifact: `cc4ca34c9f5593d22c2fdfedff3f7a699a53dc2c36c0d832c8b20fd7a8d43c95`

Restored reference:
- Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T012425-codex-source-label-qualifying-condition-failclosed-v1`
- Expected files present: `8/8`
- Non-empty files: `8/8`
- Source packet gate: `source_label_qualifying_condition_failclosed_v1=conditions_present_but_no_acceptance`
- Source packet accepted labels: `[]`

Stale upstream note:
- `012616` artifact-presence row for `source_label_failclosed_conditions` recorded present=`False`.
- That row is now stale because the restored 012425 JSON exists and is hashed in this readback.

Promotion decision:
- Accepted rows added: `0`
- New confidence gate: false
- Canonical merge allowed: false
- Downstream provider/Auto-Quant/pre-Bayes/BBN/CatBoost/execution-tree rerun allowed: false
- Strict full objective achieved: false
- `update_goal=false`

Remaining blockers:
- R6 owner-export root is still absent.
- R3 native-subhour source-label root is still absent.
- R5 recency-extension source root is still absent.
- Bull/Sideways remain fail-closed condition leads only; Bear/Crisis remain blocked.

Artifacts:
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T013127-codex-012425-restoration-readback-v1/012425-restoration-readback-v1/012425_restoration_readback_v1.json`
- Restored file status CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013127-codex-012425-restoration-readback-v1/012425-restoration-readback-v1/012425_restored_file_status_v1.csv`
- Tmp root status CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013127-codex-012425-restoration-readback-v1/012425-restoration-readback-v1/tmp_root_status_after_012425_restoration_v1.csv`
- Stale 012616 row CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013127-codex-012425-restoration-readback-v1/012425-restoration-readback-v1/stale_012616_presence_row_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T013127-codex-012425-restoration-readback-v1/checks/012425_restoration_readback_v1_assertions.out`

Next:
- Preserve the Current Cursor next action for R6. Treat the 012425 reference as artifact-restored but still fail-closed; continue only from source-owned R6 controls or explicit `FLIP` approval plus exact R3/R5/source-native evidence.
