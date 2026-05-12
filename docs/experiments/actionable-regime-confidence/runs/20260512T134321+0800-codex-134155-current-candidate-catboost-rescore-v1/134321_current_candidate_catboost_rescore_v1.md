# 134321 Current-Candidate CatBoost Rescore v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T134321+0800-codex-134155-current-candidate-catboost-rescore-v1`

Source state: `docs/experiments/actionable-regime-confidence/runs/20260512T134155+0800-codex-130814-plus-bbn-analyze-chain-v1/state_catboost_plus_bbn_v1`

Source model: `docs/experiments/actionable-regime-confidence/runs/20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1/path-ranker/catboost_history_runtime_v1/catboost_model`

## Command Status

All commands exited `0`:

- `01_apply_catboost_current`
- `02_apply_scores_to_ict`
- `03_enable_runtime`
- `04_policy_training_status`
- `05_workflow_structural_bundle`
- `06_workflow_execution_candidate`
- `07_workflow_full`
- `08_pre_bayes_status`
- `09_workflow_structural_bundle_refresh`
- `10_workflow_execution_candidate_refresh`
- `11_workflow_full_second_refresh`

## Readback

- CatBoost scored the refreshed current candidate set `structural-candidates:B2R_ETH_SIX_PROVIDER_MOMENTUM_125715:b7d77aa214e58a0a`.
- The three current `range` candidate rows received raw score `0.2934390186466203`; the inherited matured feedback row for `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` received raw score `0.9920352279003659`.
- Applying the scores into ict-engine succeeded: target rows `4`, rows with raw path score `4`, rows with calibrated path probability `1`, rows with lower bound `1`, and rows with execution gate status `1`.
- Policy-training status became score-aligned for the refreshed candidate set: `runtime_selection_status=enabled_candidate_set_ready`, `runtime_active_match_count=3`, `raw_scored_mature=325/30`, `production_validation=324/30`, and `observation_validation=162/30`.
- The only calibrated/lower-bound row is the matured inherited provider-momentum feedback row; the three current `range` candidate rows still have `calibrated_path_prob=null`, `path_prob_lower_bound=null`, and `execution_gate_status=null`.
- Workflow/execution surfaces did not consume the repaired policy-training target. Even after targeted refresh, structural bundle and execution-candidate readbacks still report `enabled_no_matching_scores`, `candidate_set_match_count=0`, `path_ranker_raw_score=null`, `path_ranker_calibrated_path_prob=null`, and `path_ranker_path_prob_lower_bound=null`.
- Pre-Bayes/BBN remains non-admitting: gate `observe_only`, active canonical regime `range`, confidence `0.367008438103555`, and soft evidence present.
- Execution remains fail-closed: selected path `range_mean_reversion`, selected path probability `0.33333333333333337`, `execution_gate_status=execution_blocked`, `execution_readiness=0.3046756738194877`, `ready=false`, `actionable=false`, and `review_status=observe`.

## Classification

`evidence_class=chain_contract_negative_sample`

This is not market/factor negative evidence. It proves that the current candidate-set scores can be applied to the policy-training target, but workflow/execution readbacks still do not consume the repaired scored rows.

## Gate

- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Do not rerun the same same-root ETH provider/AQ, Pre-Bayes/BBN, or CatBoost raw-score application. The next valid transition is to repair the workflow/execution consumption boundary so it reloads the refreshed policy-training target, and separately to produce calibrated probability/lower-bound evidence for the current unobserved `range` candidate rows. No promotion is allowed while Pre-Bayes remains `observe_only` and workflow execution still reports null score fields.
