# CatBoost single-label ranker fallback for regime-rooted branches

Use when a regime-rooted Auto-Quant branch passes Gate 1 and is pushed through filtering / BBN / CatBoost / execution tree, but the structural path-ranker training set is too small or one-class.

Observed pattern

- Gate 1 can be positive and branch fields can be preserved, but CatBoost training may fail with:
  - `Target contains only one unique value`
  - `All train targets are equal`
- This means there are not enough mature positive/negative labels for supervised CatBoost, not that the branch is automatically dead.
- Do not fabricate labels or promote the branch.

Fallback sequence

1. Run the normal downstream sequence first:
   - `auto-quant-results-import`
   - `auto-quant-prior-init`
   - `analyze`
   - `workflow-status`
   - `pre-bayes-status`
   - `export-structural-path-ranking-target`
   - `policy-training-status`
   - CatBoost trainer attempt
2. If CatBoost fails due one-class target, run the trainer in `--apply --allow-direct-fallback` mode against the current target CSV to emit direct fallback scores.
3. Register the resulting `path_ranker_direct_model.json` with the model family recorded by the artifact, usually `weighted_feature_sum_v1`. Do not register it as `catboost_direct_fallback`; ict-engine rejects mismatched family/source.
4. Apply scores, enable runtime, then re-run:
   - `analyze`
   - `workflow-status`
   - `pre-bayes-status`
   - `policy-training-status`
5. Verify execution tree fields, not just command success:
   - `path_ranker_score_visible_to_execution_tree=true`
   - `path_ranker_score_used_by_execution_tree=true`
   - `path_ranker_model_family=weighted_feature_sum_v1`
   - `ranker_validation_ready`
   - `execution_tree.gate_status`
   - `closed_loop_branch_admission.status`

Promotion rule

- If ranker validation remains insufficient, e.g. `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=0/30`, keep the branch observation-only even when the fallback score is visible and used.
- If execution tree returns `observe`, `transition_guardrail`, or `execution_observe_only`, set `promotion_allowed=false`, `trade_usable=false`, and keep collecting mature rows or seek provider parity.

Durable lesson

A direct fallback ranker is useful as telemetry and as a path-ranker plumbing check, not as live-readiness proof. The decisive gate remains execution-tree admission plus ranker validation sufficiency.
