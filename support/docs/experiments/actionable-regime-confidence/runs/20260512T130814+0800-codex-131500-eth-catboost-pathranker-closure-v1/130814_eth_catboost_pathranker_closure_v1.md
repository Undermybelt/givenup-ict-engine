# 130814 ETH CatBoost Path-Ranker Closure v1

Generated: 2026-05-12T13:10:58+0800

## Scope

This child run reuses the isolated `131500` state derived from the same-root six-provider ETH AQ authority packet `125715`. It attempts to close the specific blocker recorded by Board A `131500`: convert same-root ETH observations into production-scored mature target rows with a fitted CatBoost/path-ranker artifact and runtime readback.

This does not count `125715` or `131500` again, does not mutate production BBN priors/CPDs, does not make a live-trade claim, does not promote execution, and does not call `update_goal`.

## Evidence

- All commands exited `0`: CatBoost history train, CatBoost current apply, external score apply, trainer registration, runtime enablement, policy-training status, runtime workflow status, structural-bundle workflow, full workflow, and Pre-Bayes refresh.
- CatBoost/path-ranker artifact exists at `path-ranker/catboost_model/trainer_artifact.json` with `model_family=catboost`, `trained_rows=163`, and `calibration_rows=163`.
- Path scores exist at `path-ranker/eth_momentum_path_scores.csv` with `2` scored candidate rows.
- Policy-training readback reported runtime `enabled_candidate_set_ready`, `score_model_family=catboost`, `score_source_kind=external_model`, `runtime_active_match_count=2`, `raw_scored_mature=163/30`, `production_validation=162/30`, and `observation_validation=162/30`.
- The structural bundle used candidate-set CatBoost scores and selected `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` with `path_ranker_raw_score=0.2934390186466203` and `selected_path_probability=0.6632710958496916`.
- The full workflow remained fail-closed: closed-loop branch admission status was `fail_closed`, `actionable=false`, `ready=false`, `execution_gate_status=execution_candidate_observed`, and `review_status=observe`.
- Entry-model policy training remained not ready: both `cisd_rb_long_v1` and `breaker_rb_long_v1` had `matched_rows=0`.
- Pre-Bayes policy readback had no latest policy/bridge/soft-evidence state for this symbol after runtime; no calibrated `>=95%` regime-confidence packet was produced.

## Decision

This root closes the local CatBoost/path-ranker maturity/runtime blocker for the `125715` ETH same-root provider/AQ chain. It is stronger than `131500` because CatBoost is now trained, applied, registered, and selected by the runtime with enough mature raw-scored and production-validation rows.

It still does not satisfy Board A acceptance. The best structural path probability observed was `0.6632710958496916`, the selected branch posterior was `0.345679012345679`, the execution candidate stayed observe/fail-closed, entry-model training stayed not ready, and no every-regime `>=95%` calibrated confidence or cross-market/timeframe validation packet exists.

Net Board A effect remains fail-closed: accepted `>=95%` contexts `0`; strict full objective false; trade usable false; promotion allowed false; and `update_goal=false`.

## Next

The next useful slice should not repeat CatBoost runtime closure for this exact packet. It should add calibrated Pre-Bayes/BBN regime confidence and cross-market/timeframe validation that can lift a regime packet toward `>=95%`, while preserving the same provider/AQ provenance and non-observe execution-readiness gate.

