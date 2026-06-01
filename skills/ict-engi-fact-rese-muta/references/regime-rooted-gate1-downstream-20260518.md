# Regime-rooted Gate 1 and downstream continuation notes — 2026-05-18

## Context
User goal: train practical profit factors with branch identity rooted by market/product/symbol/base timeframe/main regime/sub regime/profit factor, starting from `1m` where feasible and covering `5m/15m/30m/1h/4h/1d` where real provider data exists. Downstream work must preserve the same rooted path through Auto-Quant, Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution tree.

## Durable lessons

### 1. Gate 1 failure must stop downstream even when provider and AQ succeeded
A fully successful provider fetch plus `auto-quant-agent-material-batch`, `dispatch`, and `rank` is not enough. If `1m` origin has zero or sparse trades and the dense/cost gate fails, stop before Pre-Bayes/BBN/CatBoost/execution-tree and classify the branch as a Gate 1 practical failure.

Observed examples:
- `yf_environmental_services_orb_rvol_expansion_1m_mtf_1d_v1`: YF `WM/RSG/CLH`, real rows for `1m/5m/15m/30m/1h/1d` where available, `rank_rows=17`, `rank_total_trade_count=10`, `one_minute_trades=0`, `dense_positive_gate=false`, downstream disallowed.
- `kraken_comp_zec_vwap_compression_expansion_density_1m_full_ladder_v1`: Kraken `COMPUSD/ZECUSD`, `1m/5m/15m/30m/1h/4h/1d`, AQ rank succeeded, but `positive_origin_1m=[]`, `cost_gate_survives=false`, downstream skipped.
- `kraken_tia_sei_rsi_vwap_scalp_density_1m_full_ladder_v1`: Kraken `TIAUSD/SEIUSD`, full ladder, AQ rank succeeded, but no positive 1m origin; downstream skipped.

Rule: do not spend downstream budget on zero/sparse `1m` roots. Keep subclass evidence or drop the branch.

### 2. Missing timeframe coverage must be explicit, not synthesized
If provider path lacks `4h` (Yahoo/YF common case), record `actual_4h_coverage=false` and do not fabricate or resample it into a claimed provider lane. `1d` can be included as real daily context when available.

Useful summary fields:
- `covered_timeframes`
- `actual_4h_coverage`
- `actual_1d_coverage`
- `max_practical_provider_window_attempted`
- `local_cache_replay`

### 3. Direct fallback path-ranker apply pitfall
Some downstream helpers train a direct fallback model with `--allow-direct-fallback` but omit that flag during `--apply`. If apply fails with `No trained model found ... pass --allow-direct-fallback`, rerun apply with `--allow-direct-fallback`, then register the artifact with its true family `weighted_feature_sum_v1`, not `catboost`.

Safe sequence:
1. `analyze`
2. `export-structural-path-ranking-target`
3. train/apply path ranker; use `--allow-direct-fallback` on apply if model family is direct fallback
4. `apply-structural-path-ranking-external-scores`
5. `register-structural-path-ranking-trainer-artifact --model-family weighted_feature_sum_v1`
6. `enable-structural-path-ranking-runtime --reuse-mode prefer_history`
7. rerun `analyze`, `workflow-status`, `pre-bayes-status`, `policy-training-status`
8. inspect execution-tree readback

### 4. Ranker visibility is parity evidence, not promotion
Observed TVR ARKK downstream after the fallback fix:
- exact branch survived
- execution tree saw and used ranker score
- `path_ranker_score_visible_to_execution_tree=true`
- `path_ranker_score_used_by_execution_tree=true`
- `ranker_validation_ready=false`
- `raw_scored_mature=1/30`, `production_validation=0/30`, `observation_validation=0/30`
- `closed_loop_branch_admission.status=fail_closed`
- `candidate_status=execution_observe_only`

Rule: even exact-branch ranker visibility/usage stays observe-only until validation rows mature and `closed_loop_branch_admission.actionable=true`.

### 5. Multi-agent hygiene
Before launching a factor lane, check active processes and claims. If another agent is running same-class AQ/downstream/autoresearch lanes, do not kill or modify their artifacts. Use `/tmp/ict-engine-agent-claims/...` for claim files; keep shared repo docs for terminal decisions only.

## Classification terms
- `keep_subclass_evidence_or_drop_gate1_no_downstream`: provider+AQ ran, but dense 1m/cost gates failed.
- `gate1_pass_downstream_fail_closed`: Gate 1 justified downstream parity test, but BBN/CatBoost/execution tree refused promotion.
- `execution_observe_only`: exact branch may survive, but execution/admission is not actionable.
- `weighted_feature_sum_v1`: direct fallback ranker artifact; never report as CatBoost-trained model.
