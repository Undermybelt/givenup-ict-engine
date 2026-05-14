# 111403 Path-Ranker Direct Fallback Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112303+0800-codex-111403-path-ranker-direct-fallback-v1`
Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T111403+0800-codex-105014-ingest-bridge-fix-v1`
Symbol: `B2R_YAHOO_CRYPTO_BTC_PULLBACK_104610`

## Exits

{
  "01_path_ranker_integration_direct_fallback": 0,
  "02_apply_structural_path_ranking_external_scores": 0,
  "03_policy_training_status_after_direct_fallback": 0,
  "04_workflow_execution_candidate_after_direct_fallback": 0,
  "05_workflow_full_after_direct_fallback": 0
}

## Decision

- Direct fallback path-ranker integration and explicit score application were run on a copied 111403 state.
- Trainer/runtime status after readback: `Ranker runtime: structural_path_ranking_target rows=2 history_rows=2 mature_rows=1 history_mature_rows=1 raw_scored_mature=1/30 production_validation=0/30 observation_validation=146/30 calibration=not_fitted trainer_artifact=ready trainer_status=present_validation_insufficient runtime_selection=enabled_registered_model_invalid runtime_mode=candidate_set_only runtime_source=registered_model_artifact score_model_family=weighted_feature_sum_v1 score_source=direct_model runtime_matches=0`.
- Target rows: `2`; mature rows: `1`; raw scored mature: `1/30`; production validation: `0/30`; observation validation: `146/30`.
- Execution remains ready=`False`, actionable=`False`, review_status=`observe`, closed_loop_branch_admission=`fail_closed`.
- Promotion remains false; this is not Board A completion evidence.
