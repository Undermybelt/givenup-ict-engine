# 124245 ETH Path-Ranker Runtime Closure v1

Run id: `20260512T125425+0800-codex-124245-eth-path-ranker-runtime-closure-v1`

## Scope

- Parent evidence: `20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1`.
- Panel: `B2R_LOCAL_NONBTC_ETH_USDT_MTF_124245`, copied from the parent ETH state.
- Source data: local Auto-Quant feather replay only; no new provider fetch.
- Purpose: test whether the already-trained ETH CatBoost path-ranker artifact can be applied, registered, enabled, and consumed by ict-engine runtime without mutating the original `124245` run state.

## Commands

All child-run commands exited `0`:

- `01_apply_catboost_scores`
- `02_apply_scores_to_ict`
- `03_register_trainer`
- `04_enable_runtime`
- `05_policy_training_status`
- `06_workflow_status_runtime`
- `07_workflow_status_refresh`
- `08_pre_bayes_refresh`

## Readback

- CatBoost apply emitted `3` candidate-set scores into `path-ranker/eth_runtime_scores.csv`.
- `apply-structural-path-ranking-external-scores` wrote `rows_with_raw_path_score=3` over `rows=3`.
- `register-structural-path-ranking-trainer-artifact` recorded `model_family=catboost`, `trained_rows=3`, and `calibration_rows=3`.
- `enable-structural-path-ranking-runtime` reached `runtime_selection_status=enabled_candidate_set_ready`, `runtime_matches=3`, `score_model_family=catboost`, and `score_source=external_model`.
- Pre-Bayes remained `pass_neutralized`; the latest canonical structural active regime was `range`, with `range=0.7560034090474984`.
- Workflow runtime reported `status=using_candidate_set_scores`, `raw_path_score=0.7506586567765241`, and `runtime_enabled=true`.

## Gate

- `evidence_class=chain_contract_negative_sample`.
- `quality_weight=0.0_for_market_factor_learning`.
- `pass:catboost_scores_applied_3`.
- `pass:ict_engine_apply_scores_exit0`.
- `pass:trainer_artifact_registered_catboost`.
- `pass:runtime_enabled_candidate_set_ready_matches3`.
- `fail_closed:local_feather_replay_no_new_provider_authority`.
- `fail_closed:auto_quant_handoff_data_ready_false_in_parent`.
- `fail_closed:raw_scored_mature_0_of_30`.
- `fail_closed:production_validation_0_of_30`.
- `fail_closed:observation_validation_0_of_30`.
- `fail_closed:calibration_not_fitted`.
- `fail_closed:no_calibrated_path_probability`.
- `fail_closed:no_execution_gate_status`.
- `fail_closed:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision

This child run repairs the local `124245` ETH path-ranker runtime handoff from `runtime_selection=disabled` to `enabled_candidate_set_ready`, but it still produces no mature rooted observations, no calibrated path probability, no execution gate, no provider-provenanced profitability packet, and no non-observe execution-tree release. It must not update BBN likelihood tables, regime-conditioned factor win rates, CatBoost production labels, or execution-tree branch weights as market/factor evidence.
