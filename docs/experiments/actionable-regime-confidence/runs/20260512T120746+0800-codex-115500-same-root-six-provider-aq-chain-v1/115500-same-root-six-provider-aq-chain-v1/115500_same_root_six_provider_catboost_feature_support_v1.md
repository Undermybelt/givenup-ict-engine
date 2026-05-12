# 115500 Same-Root Six-Provider CatBoost Feature Support v1

Run id: `20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1`
Symbol: `B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_115500`

## Scope
This support packet derives non-runtime trainer features from the existing structural target history so CatBoost is not trained on a constant-only feature surface.
It does not edit ict-engine runtime code or alter the source trade rows.

## Readback
- Train/apply/register/enable exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Raw scored mature: `245/30`.
- Production validation: `245/30`.
- Observation validation: `245/30`.
- Trainer artifact ready: `True` status `runtime_eligible`.
- Runtime selection: `enabled_candidate_set_ready` ready `True`.
- Execution ready/actionable: `False` / `False` review `observe`.
- CatBoost cleanup: `catboost_info_absent`.

## Decision
- Gate result: `115500_same_root_six_provider_catboost_feature_support=catboost_runtime_repaired_but_execution_fail_closed`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
