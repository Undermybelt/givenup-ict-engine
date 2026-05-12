# Branch Path Closure Runtime Audit v1

Run id: `20260512T002020+0800-codex-board-b-220646-branch-path-closure-readback-v1`

## Decision

`pass:branch_feedback_calibrated`

`fail_closed:workflow_blocking_truth_user_selected_historical_data_missing`

Do not promote from the `promotion_allowed=True` flag in the B5 calibration summary alone. The calibration artifact proves branch feedback coverage, CatBoost training, runtime score availability, and an execution-candidate surface. The full workflow readback still reports a blocking truth requiring user-selected historical data, and the live execution triage is observe/guarded rather than an unblocked execution admission.

## Evidence

- Exact required branch paths were covered in feedback history: `Bull`, `Bear`, `Sideways`, and `Crisis` all have `20` selected feedback rows in `b5-branch-feedback-calibration-v2`.
- CatBoost/path-ranker was trained and enabled from branch history: `raw_scored_mature=794/30`, `production_validation=794/30`, `observation_validation=80/30`, runtime status `enabled_candidate_set_ready`.
- Structural bundle selected a required Board B branch path after feedback: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`.
- Execution-candidate surface returned `candidate_status=ready`, `review_status=promote_latest`, and `actionable=true`.
- Pre-Bayes remained `pass_neutralized`; latest soft evidence was present, with canonical structural active regime `trend` and confidence `0.558445370096112`.
- Live execution triage stayed guarded: `branch=transition_guardrail`, `gate_status=observe`, and reason includes `block_crowded` readiness `0.4486 < 0.45`.
- Full workflow status still reports `blocking_truth.status=blocked`, reason `user_selected_historical_data_missing`, with an `ask_user_choose_historical_data` next command.
- Provider status was refreshed: yfinance ready, Kraken CLI ready, IBKR bridge dependency-unhealthy but gateway reachable, TradingView MCP unhealthy, Kraken public dependency-unhealthy.
- Auto-Quant status in the post-feedback isolated state is `missing_dependency` / `auto_quant_not_bootstrapped`; this run consumes the existing `220646` Auto-Quant/RC-SPA source rather than producing a fresh Auto-Quant recipe.

## Primary Artifacts

- B5 calibration summary: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1.md`
- B5 calibration assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1_assertions.out`
- Post-feedback runtime readback logs: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/post-feedback-runtime-readback-v1`
- This audit assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/branch-path-closure-readback-v1/branch_path_closure_runtime_audit_v1_assertions.out`

## Next

Resolve the runtime blocking truth before any promotion claim: choose or obtain the historical dataset explicitly requested by workflow-status, then rerun factor-research and the ordered downstream path with the same rooted branch path.
