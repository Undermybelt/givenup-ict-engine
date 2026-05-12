# 104703 Pre-Bayes Exact Branch Closure v1

Run id: `20260512T114439+0800-codex-104703-prebayes-exact-branch-closure-v1`

## Scope

This isolated run copied the `113152` exact-branch CatBoost-ready state, emitted one exact structural-feedback probe for `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`, consumed it through `ict-engine update`, retrained/applied CatBoost, enabled runtime selection, and reran Pre-Bayes, policy-training, structural bundle, execution-candidate, and full workflow readbacks.

## Readback

- All ordered commands `00` through `14` exited `0`.
- Pre-Bayes gate surface is present: `latest_gate_status=pass_neutralized`.
- Pre-Bayes branch assignment is present: `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`.
- Durable latest Pre-Bayes policy remains absent: `latest_policy_present=False`.
- CatBoost/path-ranker validation remains ready: `Ranker validation: calibration=true quality_ready=true raw_scored_mature=87/30 production_validation=87/30 observation_validation=43/30 ready=true`.
- Runtime selection remains ready: `Ranker runtime: structural_path_ranking_target rows=3 history_rows=90 mature_rows=1 history_mature_rows=87 raw_scored_mature=87/30 production_validation=87/30 observation_validation=43/30 calibration=evaluated trainer_artifact=ready trainer_status=runtime_eligible runtime_selection=enabled_candidate_set_ready runtime_mode=prefer_history runtime_source=candidate_set score_model_family=catboost score_source=external_model runtime_matches=3`.
- Closed-loop branch admission remains `fail_closed` with `execution_gate_status=execution_observe_only`, `pre_bayes_gate_status=pass_neutralized`, and `review_status=observe`.

## Decision

This closes the narrow exact-branch Pre-Bayes gate/assignment surfacing gap for 104703 and keeps CatBoost/path-ranker validation above floor. It is not promotion evidence: Pre-Bayes is `pass_neutralized`, durable policy/bridge is absent, the path-ranker execution gate is observe, closed-loop admission is fail-closed, and the same-root six-provider AQ authority gate is still missing.
