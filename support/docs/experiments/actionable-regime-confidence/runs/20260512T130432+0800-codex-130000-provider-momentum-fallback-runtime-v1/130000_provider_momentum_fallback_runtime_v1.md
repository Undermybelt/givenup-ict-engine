# 130000 Provider Momentum Fallback Runtime v1

Run id: `20260512T130432+0800-codex-130000-provider-momentum-fallback-runtime-v1`

## Scope

- Child closure over settled source root `20260512T130000+0800-codex-113833-provider-momentum-downstream-v1`.
- Source state copied before modification; source state was not mutated.
- Purpose: test whether the path-ranker direct fallback can carry the provider-momentum branch through runtime/workflow after CatBoost training failed on constant/ignored features.
- This is not a CatBoost success and not promotion evidence.

## Commands

- `01_apply_direct_fallback`: exit `0`.
- `02_apply_scores_to_ict`: exit `0`.
- `03_register_fallback_artifact`: exit `0`.
- `04_enable_runtime`: exit `0`.
- `05_policy_training_status`: exit `0`.
- `06_pre_bayes_refresh`: exit `0`.
- `07_workflow_execution_candidate`: exit `0`.
- `08_workflow_full`: exit `0`.

## Readback

- Direct fallback emitted `4` score rows using `weighted_feature_sum_v1` / `direct_fallback`.
- ict-engine accepted the score rows into the copied state.
- Policy-training readback improved validation coverage: `raw_scored_mature=133/30`, `production_validation=133/30`, and `observation_validation=133/30`.
- Trainer artifact registered as `weighted_feature_sum_v1`, but runtime selection stayed invalid: `enabled_registered_model_invalid`, `runtime_active_match_count=0`.
- Workflow execution-candidate stayed fail-closed: `execution_blocked`, `ready=false`, `actionable=false`, execution readiness `0.3363756308524155`, Pre-Bayes `pass_neutralized`, review `observe`.
- Execution candidate reported `path_ranker_raw_score=null`, `path_ranker_calibrated_path_prob=null`, and runtime status `enabled_no_matching_scores`.

## Decision

- Gate: `provider_momentum_fallback_runtime_fail_closed_no_promotion`.
- This is useful chain-contract evidence: provider-rooted mature rows exist, but direct fallback is not an accepted runtime substitute for a trained CatBoost/path-ranker artifact.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
