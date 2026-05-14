# 104703 Exact-Branch CatBoost UV Final Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T112900+0800-codex-104703-exact-branch-structural-feedback-closure-v1`

## Readback

- The proper dependency wrapper retired the earlier local CatBoost import failure: `14_catboost_path_ranker_train_uv.exit=0`, `15_catboost_path_ranker_apply_uv.exit=0`, and `16_apply_external_scores_catboost.exit=0`.
- `17_register_catboost_trainer_artifact.exit=1` with `stream did not contain valid UTF-8` when pointed at the binary CatBoost model. Despite that explicit register command failure, final policy status reports `trainer_artifact_ready=true`, `trainer_artifact_status=runtime_eligible`, `score_model_family=catboost`, `score_source_kind=external_model`, `runtime_selection_ready=true`, and `runtime_active_match_count=3`.
- Validation floors pass in the final status: `raw_scored_mature=86/30`, `production_validation=85/30`, `observation_validation=43/30`, calibration evaluated.
- The rooted path remains `Bull -> ProviderTrend -> EmaRsiContinuation -> ProviderBtcEmaRsiHold12`.
- Pre-Bayes is `pass_neutralized` with no policy. Full workflow keeps `closed_loop_branch_admission.status=fail_closed`, `execution_gate_status=execution_observe_only`, `ready=false`, and `actionable=false`.

## Decision

This materially advances the branch-preserved CatBoost/path-ranker blocker, but it is still not a production promotion. The remaining blockers are execution-tree observe/fail-closed behavior, missing non-neutral policy/BBN promotion evidence, and missing same-root six-provider AQ authority.
