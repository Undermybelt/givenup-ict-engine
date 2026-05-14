# 125715 ETH Downstream CatBoost Runtime Closure v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1`

Source AQ packet: `20260512T125715+0800-codex-six-provider-eth-same-root-aq-v1`

Scope: close the missing CatBoost/path-ranker runtime step for the already ingested same-root ETH six-provider AQ momentum packet. This is isolated run evidence only; it does not mutate production priors, CPDs, runtime code, or live execution gates.

## Provider/AQ Provenance

- Source packet has same-root six-provider ETH AQ authority present.
- Required provider rows: yfinance `21`, Kraken `20`, Binance `34`, Bybit `34`, TradingViewRemix/TVR `21`, IBKR/PAXOS AGGTRADES `32` momentum trade rows consumed downstream.
- Derived downstream trade rows: `162`.
- `auto-quant-ingest-real-trades` applied `162/162` rows with `0` invalid rows in isolated state `state_ingest/B2R_ETH_SIX_PROVIDER_MOMENTUM_125715`.

## Runtime Closure

- CatBoost history training exited `0`.
- CatBoost current scoring exited `0`.
- External score application exited `0`.
- Trainer artifact registration exited `0`.
- Runtime enablement exited `0`.
- Post-runtime policy-training readback exited `0`.
- Post-runtime execution-candidate readback exited `0`.

Readback:

- `structural_path_ranking_runtime.enabled=true`
- `runtime_selection_status=enabled_candidate_set_ready`
- `runtime_matches=2`
- `score_model_family=catboost`
- `score_source_kind=external_model`
- `raw_scored_mature=163/30`
- `production_validation=162/30`
- `observation_validation=162/30`
- `calibration=evaluated`
- `trainer_artifact=runtime_eligible`

## Remaining Fail-Closed State

- Execution candidate remains `actionable=false`.
- Execution candidate remains `ready=false`.
- Review status remains `observe`.
- Pre-Bayes policy/gate is still absent from the execution-candidate readback.
- Path-ranker raw score is only `0.2934390186466203`.
- Selected path probability is `0.6632710958496916`, below Board A `>=95%` calibrated-confidence acceptance.
- Entry-model policy training still has `matched_rows=0` for the shipped entry models.

Gate:

- `pass:same_root_six_provider_eth_aq_authority_true`.
- `pass:six_provider_momentum_rows_162`.
- `pass:ingest_applied_162_invalid_0`.
- `pass:catboost_train_exit0`.
- `pass:catboost_apply_exit0`.
- `pass:external_scores_applied_exit0`.
- `pass:trainer_artifact_registered_exit0`.
- `pass:path_ranker_runtime_enabled_candidate_set_ready`.
- `pass:raw_scored_mature_163_of_30`.
- `pass:production_validation_162_of_30`.
- `pass:observation_validation_162_of_30`.
- `fail_closed:selected_path_probability_0p6632710958496916_below_0p95`.
- `fail_closed:path_ranker_raw_score_0p2934390186466203_low`.
- `fail_closed:pre_bayes_policy_absent`.
- `fail_closed:execution_candidate_observed_only`.
- `fail_closed:execution_ready_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

Next:

- Do not promote from `131500`. The six-provider AQ and CatBoost/path-ranker runtime contracts are now wired, but the remaining blocker is calibrated regime confidence and execution readiness: Pre-Bayes/BBN must produce a real policy/gate and the execution candidate must move beyond observe-only with calibrated `>=95%` support before Board A or Board B can accept it.
