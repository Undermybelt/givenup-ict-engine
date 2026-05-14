# Board B 220646 Branch Path Closure Readback v1 Strict Audit

Run id: `20260512T002020+0800-codex-board-b-220646-branch-path-closure-readback-v1`.

Decision: `not_promoted:pre_bayes_and_execution_candidate_blocked`.

## Confirmed

- Source candidate remains the `220646` strict RC-SPA pass: stable score `85.7407`, price roots `4/4`, scoped Manipulation component retained.
- Replay selected `80` feedback rows, `20` per root (`Bull`, `Bear`, `Sideways`, `Crisis`).
- The four required rooted branch paths were observed in structural feedback history.
- CatBoost path-ranker train/apply/register/enable ran with command exits `0`.
- Policy/path-ranker validation is ready: production validation `794/30`, observation validation `80/30`.
- Runtime structural path is now one of the required Board B branch paths: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`.

## Strict Fail-Closed Finding

The generated calibration summary says `promotion_allowed=True`, but that field is not accepted as the Board B promotion gate because the final execution-candidate readback is still blocked:

- `actionable=false`
- `candidate_status=execution_blocked`
- `execution_gate_status=execution_blocked`
- `pre_bayes_gate_status=blocked`
- `ready=false`
- `review_reason=structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`

Pre-Bayes also reports `latest_gate_status=blocked` with `pre_bayes_branch_path_gate=blocked_missing_consumed_pre_bayes_filter` on the exact branch path.

## Provider / Auto-Quant Readback

- Provider status captured: yfinance ready, Kraken CLI ready, IBKR gateway reachable but runtime dependencies missing, TradingViewRemix unhealthy.
- Fresh Auto-Quant status readback in the provider-state root is `missing_dependency`; this does not invalidate the measured `220646` replay input, but it blocks claiming the fresh state is Auto-Quant prepared.

## Artifact Pointers

- Replay summary: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1.md`
- Replay assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/source_root_stop_carry_longhorizon_b5_calibration_v1_assertions.out`
- Final policy status: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/command-output/13_policy_training_status_final.out`
- Final execution candidate: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/b5-branch-feedback-calibration-v2/command-output/15_workflow_execution_candidate_final.out`
- Provider status: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/provider/provider_status_agent.out`
- Auto-Quant status: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1/provider/auto_quant_status.json`

## Next

Repair the Pre-Bayes branch-path filter so the exact consumed branch path exits `blocked_missing_consumed_pre_bayes_filter`, then rerun execution-candidate. Do not promote from CatBoost/path-ranker readiness alone.
