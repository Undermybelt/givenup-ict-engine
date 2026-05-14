#!/usr/bin/env bash
set -euo pipefail

jq -e \
  '.promotion.update_goal == false
   and .promotion.strict_full_objective_achieved == false
   and .latest_staging_evidence.canonical_owner_root_mutated == false
   and .latest_staging_evidence.chronological_split_gate == false
   and .latest_staging_evidence.heldout_symbol_gate == false
   and .latest_staging_evidence.heldout_venue_gate == false
   and .latest_triplet_sweep.canonical_r6_owner_export_root_exists == false
   and .latest_triplet_sweep.legacy_sidecars_are_owner_export == false' \
  docs/experiments/actionable-regime-confidence/runs/20260512T031539-codex-current-objective-completion-audit-after-031316-v1/current-objective-completion-audit-after-031316-v1/current_objective_completion_audit_after_031316_v1.json
