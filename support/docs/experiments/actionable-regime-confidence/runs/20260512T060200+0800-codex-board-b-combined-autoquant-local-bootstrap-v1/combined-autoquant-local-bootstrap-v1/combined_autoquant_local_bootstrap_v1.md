# Board B Combined Auto-Quant Local Bootstrap v1

Gate result: `board_b_combined_autoquant_local_bootstrap_v1=dependency_bootstrap_attempted_no_selected_data_no_promotion`

State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1`

Repo url: `/Users/thrill3r/Auto-Quant`

Command exits:
- command_exit_summary
- 00_board_hash_before.exit=0
- 01_auto_quant_status_before.exit=0
- 02_auto_quant_bootstrap_local.exit=0
- 03_auto_quant_status_after.exit=0

Status summary:
- before: bootstrap_needed=True, data_ready=False, dependency_healthy=False, healthy=False, managed_dir=docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/auto-quant/.deps/auto-quant, pinned_ref=None, repo_url=None, status=missing_dependency
- after: bootstrap_needed=False, data_ready=False, dependency_healthy=True, healthy=False, managed_dir=docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/auto-quant/.deps/auto-quant, pinned_ref=None, repo_url=None, status=dependency_ready_data_missing

Decision: dependency bootstrap evidence only; selected-data Auto-Quant training was not run; promotion remains blocked by user_selected_historical_data_missing and downstream validation gates. update_goal=false.
