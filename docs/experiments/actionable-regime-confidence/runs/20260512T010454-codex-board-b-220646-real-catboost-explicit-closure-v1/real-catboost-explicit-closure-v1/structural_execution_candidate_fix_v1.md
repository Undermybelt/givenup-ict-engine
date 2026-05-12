# Structural Execution Candidate Fix v1

Run id: `20260512T010454+0800-codex-board-b-220646-real-catboost-explicit-closure-v1`

Scope: downstream-only repair/readback for the exact `220646` Sideways branch. No RC-SPA or Auto-Quant scorer rerun was performed in this packet.

## Root Cause

The command-shape issues were already repaired in corrected steps `16-23`: export runs without unsupported `--output-dir`, trainer registration uses `trainer_artifact.json` instead of the binary `.cbm`, and runtime enable uses `prefer_history`.

The remaining execution-candidate issue was a workflow-status precedence bug. `workflow-status --phase execution-candidate` returned the persisted `analyze-live` execution candidate whenever it existed, so the stale Bull candidate masked the structural recommended path even when the exact Sideways branch was available.

## Fix

`workflow-status --phase execution-candidate` now builds the structural recommended path candidate first and falls back to the persisted execution candidate only when no structural candidate can be built. The virtual structural candidate is intentionally not promotable unless both execution and Pre-Bayes gates are ready.

## Evidence

- `24_cargo_build_structural_execution_candidate_fix.exit = 0`
- `28_cargo_test_structural_candidate_fallback.exit = 0`
- `29_cargo_test_pre_bayes_structural_feedback_assignments.exit = 0`
- `30_cargo_test_structural_candidate_prefers_over_stale_analyze.exit = 0`
- `25_workflow_structural_bundle_after_execution_candidate_fix.exit = 0`
- `26_workflow_execution_candidate_after_execution_candidate_fix.exit = 0`
- `27_workflow_full_after_execution_candidate_fix.exit = 0`

The corrected structural bundle still selects:

`Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

The corrected execution-candidate phase now emits:

- `source_phase=structural-recommended-path-bundle`
- `candidate_set_size=4`
- `path_ranker_raw_score=0.857407`
- `path_ranker_calibrated_path_prob=0.42857142857142855`
- `pre_bayes_gate_status=pass_neutralized`
- `execution_gate_status=execution_observe_only`
- `execution_readiness=0.57`
- `actionable=false`
- `review_status=observe`

## Decision

Promotion remains blocked. The stale analyze-live masking bug is repaired, but the exact structural branch is still only visible as an observe-only candidate. Closed-loop promotion still requires the same branch to be admitted through Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution tree with explicit branch-level confidence.

## Next

Keep the current `010454` cursor. Next work should make the full workflow/execution-tree closed-loop surface consume or persist the same exact Sideways structural branch, then prove a branch-level admission or explicit fail-closed reason. Do not rerun RC-SPA for this candidate.
