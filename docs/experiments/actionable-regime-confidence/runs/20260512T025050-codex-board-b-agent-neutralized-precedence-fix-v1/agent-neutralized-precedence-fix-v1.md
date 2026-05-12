# Board B Agent Neutralized Precedence Fix v1

Scope: corrective code/test readback only. No RC-SPA, Auto-Quant, provider, or runtime replay was rerun in this slice.

Root cause:
- The human workflow-status hard-block list already treated `pass_neutralized` as a blocking status.
- The agent workflow-status hard-block list did not, so a structural branch-admission `fail_closed` value could override the more specific `blocking_truth.status=pass_neutralized`.

Fix:
- Add `pass_neutralized` to the agent workflow-status hard-block list in `src/application/orchestration/workflow_status.rs`.

Verification:
- `CARGO_BUILD_JOBS=1 cargo test agent_status_treats_pre_bayes_neutralized_as_blocking -- --nocapture` exited `0`.
- `CARGO_BUILD_JOBS=1 cargo test branch_admission -- --nocapture` exited `0`.

Interpretation:
- The exact Sideways branch remains fail-closed in workflow/execution-tree artifacts from the existing `022415` readback.
- Agent status now preserves the upstream Pre-Bayes blocker when `blocking_truth.status=pass_neutralized`.
- Promotion remains false.
