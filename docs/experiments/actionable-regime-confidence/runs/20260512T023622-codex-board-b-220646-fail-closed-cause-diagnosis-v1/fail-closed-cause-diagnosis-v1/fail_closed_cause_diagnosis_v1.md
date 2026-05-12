# Board B 220646 Regime-Root Fail-Closed Addendum v1

This is an append-only addendum to the existing fail-closed diagnosis. It does not supersede the current cursor and does not promote `220646`.

## Branch Under Review

- Branch path: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- Source score: `85.7407`
- Latest verified full-chain evidence used: `20260512T022415-codex-board-b-220646-execution-tree-admission-current-bin-v1`
- Artifact-integrity correction respected: `20260512T023723-codex-board-b-022732-artifact-integrity-correction-v1`
- Existing fail-closed diagnosis respected: `20260512T023559-codex-board-b-220646-fail-closed-cause-diagnosis-v1`
- Prior trace parity evidence used: `20260512T022335-codex-board-b-220646-execution-tree-branch-admission-readback-shared-target-v1`

## Facts

- Provider coverage is explicit in `022415`: `yfinance` ready, `kraken_cli` ready, IBKR gateway reachable but runtime deps unhealthy, and TradingViewRemix MCP probe failed.
- Auto-Quant status in `022415` is `dependency_ready_data_ready`.
- CatBoost/path-ranker is not the current blocker: runtime is ready, score source is `external_model`, production validation is `869/30`, observation validation is `82/30`, and the exact Sideways path score is visible.
- The exact Sideways branch path is preserved through structural bundle, workflow, execution-tree trace, and artifact ledger.
- Admission remains fail-closed: `closed_loop_branch_admission.status=fail_closed`, `ready=false`, `actionable=false`, `promote_candidate=false`.

## Root Cause

The blocker is a real branch rejection, not a missing trace surface.

1. Pre-Bayes is neutralized, not hard-pass.
   - `gating_status=pass_neutralized`
   - `evidence_quality_score=0.5458617984369726`
   - hard-pass threshold is `0.75`
   - conflict flag is `low_directional_separation`
   - support gap is `0.032`, below the `0.08` policy floor

2. The current regime evidence does not support promoting the Sideways-root branch.
   - branch root is `Sideways`
   - current market state is `TrendExpansion/BullTrendAcceleration`
   - canonical structural active regime is `trend`
   - branch transition prior from the exact Sideways path has `weighted_transition_mass=0.000`

3. Execution is below the admission floor.
   - workflow execution gate is `execution_blocked`
   - execution readiness is `0.4420748337394927`
   - observe threshold is `0.45`
   - ready threshold is `0.65`
   - execution-tree post-guardrail state is `observe / transition_guardrail / guarded`
   - `hybrid_transition_hazard=0.600`

4. Workflow blocking truth still requires explicit data selection.
   - `blocking_truth.status=blocked`
   - `blocking_truth.reason=user_selected_historical_data_missing`
   - dataset comparison class is `different_data_fingerprint`

## Decision

Do not promote `220646`.

The correct next action is to reject this candidate for promotion and feed the fail-closed tags into `B2R-repeat-next`, unless a single explicit user-selected historical-data retry is required by a concurrent agent. That retry still needs all of:

- Pre-Bayes `pass_hard`
- no Pre-Bayes conflict flags
- execution readiness at least `0.65`
- execution tree `ready / fill_viable`
- no transition guardrail
- exact same rooted branch identity preserved

## Nursery Feedback Tags

- `pre_bayes_low_directional_separation`
- `regime_root_context_mismatch`
- `execution_readiness_below_observe_threshold`
- `transition_guardrail_high_hazard`
- `user_selected_historical_data_missing`

Successor work should mine a materially different root-aware family/provider panel where the selected root agrees with current regime evidence and passes hard Pre-Bayes plus execution-tree ready/fill_viable admission.
