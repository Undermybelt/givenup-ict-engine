# 150346 Binance BTCUSDT Provider Downstream Readback Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T150346+0800-codex-143900-binance-btcusdt-provider-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Use provider-backed input, not local-only replay | Binance `BTCUSDT` 1h source from `143900`; materialized 1h/4h/1d JSON in `provider-data-json/`; `01_materialize_provider_json.exit=0` | Partial |
| Run Auto-Quant route | `02_factor_research_auto_quant_handoff.exit=0`, `03_auto_quant_prepare.exit=0`, `04_factor_research_after_prepare.exit=0`; state has `auto_quant_handoff.factor_research.json` and workspace profile | Partial |
| Run ict-engine analyze/filter/Pre-Bayes | `05_analyze_provider_slice.exit=0`, `06_pre_bayes_status.exit=0`; Pre-Bayes latest canonical regime `range`, confidence `0.5345590139527494`, gate `pass_neutralized` | Fail-closed |
| Run BBN-facing readback | Pre-Bayes soft evidence and policy emitted in `06_pre_bayes_status.out`; probabilities: `range=0.7503448811920331`, `stress=0.1746206306887635`, `transition=0.07503448811920331`, `trend=0.0` | Fail-closed |
| Run CatBoost/path-ranker | `09_catboost_path_ranker_train_attempt.exit=0`; external CatBoost artifact exists under `path-ranker/catboost_model/` | Fail-closed |
| Prove CatBoost/path-ranker calibration/adoption | Trainer used only 3 pseudo-labeled rows, no mature samples, fallback `structural_baseline_score`; runtime readback stayed disabled with raw-scored mature `0/30` and production validation `0/30` | Missing |
| Run execution-tree/workflow readback | `11_workflow_structural_bundle.exit=0`, `12_workflow_execution_candidate.exit=0`, `13_workflow_full.exit=0` | Pass-readback |
| Prove execution readiness/actionability | Execution candidate `ready=false`, `actionable=false`, `execution_gate_status=execution_blocked`, `review_status=observe`, selected path probability `0.3663153553254684` | Fail-closed |
| Meet Board A 95% calibrated regime-confidence/lower-bound gate | Latest canonical structural confidence `0.5345590139527494`; no calibrated path probability or lower bound | Missing |
| Cross-market/timeframe/provider validation | Same-root chain used Binance BTCUSDT slices only; no same-root IBKR/TVR/YF/Kraken/Bybit rows | Missing |

## Evidence

- All command checks `01-13` exited `0`.
- Provider materialization produced Binance BTCUSDT rows: full 1h `76429`, full 4h `19124`, full 1d `3191`, sliced to 1h `4000`, 4h `1000`, 1d `168`.
- Auto-Quant prepare completed, but this does not satisfy the hard-lock six-provider AQ authority contract.
- Pre-Bayes emitted a live canonical regime readback, but confidence was only `0.5345590139527494`.
- Structural path target export had `rows=3`, `history_rows=3`, `mature_rows=0`, `history_mature_rows=0`, `rows_with_calibrated_path_prob=0`, `rows_with_path_prob_lower_bound=0`, and `rows_with_execution_gate_status=0`.
- CatBoost trainer wrote an external model artifact, but it trained on only `3` rows, no mature samples, pseudo-labels derived from `structural_baseline_score`, and one fallback feature.
- Runtime policy readback still reported path-ranker runtime `disabled`, trainer artifact `missing` from state/runtime perspective, raw-scored mature rows `0/30`, production validation `0/30`, and observation validation `0/30`.
- Full workflow readback had `actionable_artifact_count=5`, but closed-loop branch admission stayed `status=fail_closed`, `ready=false`, and `actionable=false`.

## Gate

- `support_once:150346_binance_btcusdt_provider_downstream_readback_v1`.
- `evidence_class:provider_backed_single_provider_aq_downstream_chain_fail_closed`.
- `pass:provider_materialization_binance_btcusdt_1h4h1d_exit0`.
- `pass:auto_quant_prepare_exit0`.
- `pass:analyze_pre_bayes_policy_export_catboost_workflow_exit0`.
- `partial:pre_bayes_range_confidence_0_5346`.
- `partial:external_catboost_artifact_written`.
- `fail_closed:confidence_0_5346_below_0_95`.
- `fail_closed:single_provider_binance_only`.
- `fail_closed:missing_required_provider_rows_ibkr_tvr_yf_kraken_bybit`.
- `fail_closed:path_ranker_mature_rows_0`.
- `fail_closed:raw_scored_mature_0_of_30`.
- `fail_closed:production_validation_0_of_30`.
- `fail_closed:calibrated_path_prob_absent`.
- `fail_closed:path_prob_lower_bound_absent`.
- `fail_closed:runtime_path_ranker_disabled`.
- `fail_closed:execution_blocked`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Decision

This run is valuable because it proves the local chain can carry a provider-backed Binance BTCUSDT packet through Auto-Quant prepare, Pre-Bayes/BBN-facing readback, external CatBoost training attempt, and execution-tree workflow readback. It is not accepted Board A or Board B evidence: confidence is far below `0.95`, provider authority is single-provider only, CatBoost/path-ranker calibration is not mature or runtime-adopted, and execution remains blocked/observe.
