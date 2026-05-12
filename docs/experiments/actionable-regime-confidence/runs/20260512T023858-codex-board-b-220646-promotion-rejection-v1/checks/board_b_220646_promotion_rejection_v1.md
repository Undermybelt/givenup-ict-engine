# Board B 220646 Promotion Rejection v1

Scope: board-level decision after exact `220646` branch trace/admission parity was repaired and fail-closed causes were diagnosed.

Authoritative board: `docs/plans/2026-05-10-regime-conditional-auto-quant-profitability-todo.md`

## Evidence

- Verified current-binary evidence remains `20260512T022415-codex-board-b-220646-execution-tree-admission-current-bin-v1`.
- The `023559` copied-state diagnosis ran provider-status, Auto-Quant status, Pre-Bayes, policy/CatBoost path-ranker, structural bundle, execution-candidate, full workflow, and execution-tree trace readbacks with exit `0`.
- Exact branch identity remains preserved:
  `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`.
- CatBoost/path-ranker is not the current blocker: `score_model_family=catboost`, `score_source_kind=external_model`, `runtime_active_match_count=4`, `production_validation=869/30`, and `observation_validation=82/30`.
- Pre-Bayes remains `pass_neutralized`, not `pass_hard`; the diagnosed long/short probability gap is `0.007747` versus `min_directional_support_gap=0.08`.
- Execution remains fail-closed: `execution_readiness=0.4421` is below the `0.45` threshold, the branch hits `block_crowded`, and the trace stays `observe / transition_guardrail / guarded` with `hybrid_transition_hazard=0.600`.
- The workflow `user_selected_historical_data_missing` state is an intentional data-selection gate when multiple historical paths exist, not a trace-parity or CatBoost-readiness bug.

## Decision

Reject exact `220646` for promotion in the current Board B context.

This does not invalidate the upstream RC-SPA pass (`85.7407`, price roots `4/4`, scoped Manipulation component pass). It closes this exact promotion attempt as fail-closed after the ordered chain reached execution tree and still could not produce an admitted/actionable branch.

## Next

Move to `B2R-repeat-next`: synthesize or select a materially different root-aware Bull/Bear/Sideways/Crisis family/provider panel. Preserve the rooted branch contract, run real provider/Auto-Quant/Pre-Bayes/BBN/CatBoost/execution-tree probes, and combine the `205047` scoped Manipulation component only if all price roots pass unchanged RC-SPA.

Do not rerun RC-SPA or trace/admission parity for `220646` unless the user supplies an explicit selected historical data path and the same branch is re-evaluated once under compatible regime/execution context evidence.
