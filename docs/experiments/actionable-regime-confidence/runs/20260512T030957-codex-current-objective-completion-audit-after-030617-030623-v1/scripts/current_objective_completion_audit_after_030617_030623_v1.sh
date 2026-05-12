#!/usr/bin/env bash
set -euo pipefail

RUN_ROOT="docs/experiments/actionable-regime-confidence/runs/20260512T030957-codex-current-objective-completion-audit-after-030617-030623-v1"
SUMMARY="$RUN_ROOT/current-objective-completion-audit-after-030617-030623-v1/current_objective_completion_audit_after_030617_030623_v1.json"

jq -e '
  .gate_result == "current_objective_completion_audit_after_030617_030623_v1=not_complete_source_controls_missing_030722_reference_broken_downstream_blocked"
  and .verifier_030617.status == "blocked"
  and .verifier_030617.command_exit == 2
  and .reference_integrity.artifact_root_030722_exists == false
  and .promotion.accepted_rows_added == 0
  and .promotion.new_confidence_gate == false
  and .promotion.canonical_merge_allowed == false
  and .promotion.downstream_promotion_rerun_allowed == false
  and .promotion.update_goal == false
' "$SUMMARY"
