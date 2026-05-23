# Board A Workflow Child-Root Readback Packet - 2026-05-23

## Scope

- Board: A, aggregate rooted-feedback readback only.
- Problem: `workflow-status` was still reading the weak top-level state for the
  `BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523` bucket while the stronger
  `state/ict-engine-feedback/BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523/`
  branch held the mature feedback and structural path evidence.
- Repair surface: `src/application/orchestration/command_entry.rs`
  plus the shared read-root helper in
  `src/application/entry_models/training_export.rs`.

## Fix

- Reused the existing child-root resolver from the policy/export lane.
- `workflow-status`, `pre-bayes-status`, and `pre-bayes-diff` now resolve the
  stronger child feedback root before loading snapshot / learning state.
- Added a regression test that forces `workflow_status_command` to read from
  the child root when the child summary is stronger than the top-level summary.

## Evidence

- Focused Rust tests:
  - `workflow_status_command_refreshes_from_mature_feedback_child_root`
  - `policy_training_status_uses_mature_feedback_child_root_for_ranker_when_primary_root_only_has_assets`
- Python ingress test:
  - `support/docs/experiments/actionable-regime-confidence/scripts/test_board_a_positive_negative_feedback_ingress.py`
- Real CLI readback:
  - command: `cargo run --quiet -- workflow-status --symbol BOARD_A_AGGREGATED_ROOTED_FEEDBACK_20260523 --state-dir support/docs/experiments/actionable-regime-confidence/runs/20260523T064708Z-codex-board-a-positive-negative-feedback-ingress-v1/state --output-format json`
  - exit: `0`
  - `/tmp/ict-engine-board-a-workflow-child-root-readback-20260523/workflow_status.out`

## Readback

- `latest_structural_execution_candidate.path_id` resolved to the rooted
  feedback branch:
  `RangeConsolidation -> InsuranceDefensivePremiumCycle -> rsi_vwap_reclaim -> yf_insurance_defensive_range_reclaim_1m_mtf_board_a_v1`
- `latest_update.structural_feedback.path_id` matched the same rooted branch.
- `closed_loop_branch_admission.status=fail_closed`
- `closed_loop_branch_admission.reason=exact_structural_branch_visible_but_not_ready_or_actionable`

## Decision

- This is readback plumbing only.
- It preserves the rooted branch evidence surface and does not claim Board A
  completion, root-regime registration, `95%` confidence, trade usability, or
  Board B promotion.
- `update_goal=false`
