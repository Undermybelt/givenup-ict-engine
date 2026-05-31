# Workflow Status Marker Closure Repair

- Created: 2026-05-31T11:22:01+08:00
- Owner: codex-workflow-status-marker-closure-repair
- Repo: ict-engine checkout root
- Branch: main
- Workdoc: `/tmp/ict-engine-workflow-status-marker-closure-repair-20260531T112201+0800/workdoc.md`
- Claim: `/tmp/ict-engine-agent-claims/board-b-factor-refinement/20260531T112201+0800-codex-workflow-status-marker-closure-repair.claim`
- Status: terminalized verified source/test repair; no provider, IBKR historical, AutoQuant, Freqtrade/TOMAC, paper/sim/live, downstream lifecycle, or local backtest launch.

## Objective

Close the loophole where Rust workflow status can treat marker-only `same_tree_practical_closure_validated=true` or `evidence_packet_validated=true` fields as proof that a profitability factor is practical. Completion still requires canonical same-tree evidence from the validated packet path, not marker fields copied into arbitrary candidate/admission JSON.

## Debugging Record

- Symptom: workflow status can make `promotion_allowed`, `trade_usable`, and `update_goal` true when all live-plane fields are true and a bare closure marker is present.
- Root cause: `practical_closure_validated_for_value(...)` trusts marker booleans directly, including nested admission marker fields, without requiring a structured validated same-tree practical-closure packet.
- Canonical owner: `src/application/orchestration/workflow_status.rs` for Rust workflow-status normalization; Python packet validation remains owned by `support/scripts/research/same_tree_practical_closure.py` and `support/scripts/factor_claim_terminalization_audit.py`.
- Patch shape: edit owner, not wrapper or claim producer. Reject marker-only fields, accept only structured `same_tree_practical_closure` evidence with `status=pass`, practical flags true, `deploy_ready=true`, `funded_live_fill_required=false`, correct readiness contract, and evidence validation true.

## TDD Route

- Mode: auto
- Decision: strict
- Reason: shared workflow-status gate controls practical admission and live-trade usability readbacks.
- Verification: add a failing Rust unit test for marker-only closure, then patch and rerun focused tests.

## Pre-Edit Complexity Check

- Target edit file: `src/application/orchestration/workflow_status.rs`
- Existing pressure signal: large control chokepoint, but the relevant owner function already exists and localizes the closure-validity contract.
- Owner fit: edit in place, because this is the workflow-status normalization owner.
- Safer edit boundary: keep changes inside `practical_closure_validated_for_value(...)` and adjacent unit tests.
- Decision: edit-in-place.

## Evidence Log

- 2026-05-31T11:21:34+08:00: `factor_claim_terminalization_audit.py --compact` returned pass: no active claims, no live factor processes, no same-tree practical closure, no practical factors.
- 2026-05-31T11:36:26+08:00: fresh overlapping no-runtime code claim observed: `20260531T113047+0800-codex-balanced-factor-gates.claim`; no provider/AQ/IBKR/TOMAC launch was attempted.
- 2026-05-31T11:39:xx+08:00: RED confirmed with `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-marker-repair-20260531T112201 cargo test structural_branch_admission_rejects_marker_only_same_tree_closure -- --nocapture`; expected failure was `left: "admitted" right: "fail_closed"`.
- 2026-05-31T11:51:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-marker-repair-20260531T112201 cargo test structural_branch_admission -- --nocapture` passed `7 passed; 0 failed`.
- 2026-05-31T11:53:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-marker-repair-20260531T112201 cargo test workflow_factor_profitability_lifecycle -- --nocapture` passed `8 passed; 0 failed`.
- 2026-05-31T11:54:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-marker-repair-20260531T112201 cargo test same_root_trace_admission -- --nocapture` passed `3 passed; 0 failed`.
- 2026-05-31T11:56:xx+08:00: GREEN `CARGO_TARGET_DIR=/tmp/ict-engine-cargo-target-marker-repair-20260531T112201 cargo test execution_candidate_phase_lets -- --nocapture` passed `2 passed; 0 failed`, and `cargo test agent_current_regime_posterior_reconciles_ready_structural_candidate_gate -- --nocapture` passed `1 passed; 0 failed`.

## Terminal Readback

- Terminal status: `terminalized_verified_code_repair_no_runtime_launch`
- Decision: marker-only same-tree practical closure is rejected by Rust workflow-status; validated structured `same_tree_practical_closure` packets preserve the positive pass path.
- Balance result: `learning_admission_status=admitted` and `paper_feedback_collection_ready=true` may surface as flywheel-ready, while `deploy_ready`, `promotion_allowed`, `trade_usable`, and `update_goal` remain false unless the structured closure packet validates.
- promotion_allowed: false
- trade_usable: false
- update_goal: false
- same_tree_practical_closure: not produced by this slice
- Remaining full-goal status: not complete; this closes one fail-open loophole only.
