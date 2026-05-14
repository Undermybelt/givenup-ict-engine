# 115700 CatBoost Feature Support v1

Run id: `20260512T121354+0800-codex-115700-layer-contract-downstream-v1`
Symbol: `B2R_SIX_PROVIDER_BTC_115700`

## Scope
Derive non-runtime trainer features from the existing 115700 structural target history so CatBoost is not trained on a constant-only feature surface.
This does not edit ict-engine runtime code or alter the original 115700 source rows.

## Readback
- Train/apply/register/enable exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Contract-complete rows after CatBoost support: `237`.
- Market/factor trainable rows: `237`.
- Raw scored mature: `237/30`.
- Production validation: `237/30`.
- Observation validation: `237/30`.
- Runtime selection: `enabled_candidate_set_ready` ready `True`.
- Execution ready/actionable: `False` / `False` review `observe`.
- CatBoost cleanup: `catboost_info_absent`.

## Decision
- Gate result: `115700_layer_contract_catboost_runtime_repaired_but_execution_fail_closed`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
