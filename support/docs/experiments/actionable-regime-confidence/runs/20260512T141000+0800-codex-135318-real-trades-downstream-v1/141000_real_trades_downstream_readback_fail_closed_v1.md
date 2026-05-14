# 141000 Real-Trades Downstream Readback Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T135318+0800-codex-long-history-es-nq-aq-staging-v1`

## Scope

This packet classifies the settled full NQ/ES downstream root that exported TOMAC real trades from the `135318` long-history ES/NQ Auto-Quant family, imported the split strategy manifests into ict-engine, initialized Auto-Quant priors, ingested real-trade feedback, and ran Pre-Bayes, policy-training, structural target, structural bundle, execution-candidate, and workflow readbacks for NQ and ES.

This is support-only downstream plumbing evidence. It is not Board A accepted regime-confidence evidence, not provider-owned acquisition, not production BBN/CPD mutation authority, not CatBoost/path-ranker promotion, not execution-tree promotion, and not trade-usable evidence.

## Evidence

- Real-trade export summary: `derived/tomac_real_trades_summary.json`
- Split trade files: `derived/tomac_real_trades_nq.jsonl`, `derived/tomac_real_trades_es.jsonl`
- Strategy manifests: `manifests/strategy_library_135318_nq_v1.json`, `manifests/strategy_library_135318_es_v1.json`
- Command outputs/checks: `command-output/`, `checks/`
- NQ state: `state_nq_v1/`
- ES state: `state_es_v1/`

## Command Status

- `01_export_tomac_real_trades.exit=0`
- `02_build_symbol_manifests.exit=0`
- `03_nq_results_import.exit=0`
- `04_nq_prior_init.exit=0`
- `05_nq_ingest_real_trades.exit=0`
- `06_nq_analyze_15m_1h_1d.exit=130`
- `06_nq_analyze_15m_1h_1d.interrupted=interrupted_at=2026-05-12T14:33:36+0800reason=nq_analyze_15m_1h_1d_exceeded_20m_no_output_no_new_state`
- `07_nq_pre_bayes_status.exit=0`
- `08_nq_policy_training_status.exit=0`
- `09_nq_export_structural_path_target.exit=0`
- `10_nq_workflow_structural_bundle.exit=0`
- `11_nq_workflow_execution_candidate.exit=0`
- `12_nq_workflow_full.exit=0`
- `13_es_results_import.exit=0`
- `14_es_prior_init.exit=0`
- `15_es_ingest_real_trades.exit=0`
- `16_es_analyze_15m_1h_1d.exit=130`
- `16_es_analyze_15m_1h_1d.interrupted=interrupted_at=2026-05-12T14:36:32+0800reason=es_analyze_15m_1h_1d_aborted_after_nq_same_path_exceeded_20m`
- `17_es_pre_bayes_status.exit=0`
- `18_es_policy_training_status.exit=0`
- `19_es_export_structural_path_target.exit=0`
- `20_es_workflow_structural_bundle.exit=0`
- `21_es_workflow_execution_candidate.exit=0`
- `22_es_workflow_full.exit=0`

## Real-Trade Export Metrics

- Aggregate: `192` records, total profit `11.64%`, win rate `59.8958%`, Sharpe `0.0449`, profit factor `1.1615`, max drawdown `-7.4751%`.
- NQ/USD: `77` trades, total profit `9.50%`, win rate `72.7273%`, profit factor `1.3086`, max drawdown `-7.0379%`.
- ES/USD: `115` trades, total profit `2.14%`, win rate `51.3043%`, profit factor `1.0518`, max drawdown `-11.2812%`.
- Backtest span: `2012-05-03 23:00:00` to `2025-08-04 12:00:00`.

## NQ Readback

- Auto-Quant results import succeeded: `n_ok=1`, `n_error=0`.
- Auto-Quant prior init succeeded with `evidence_value_gate_passed=true`, `trade_count=77`, `n_win=56`, `n_loss=21`.
- Real-trade ingest applied `77/77` rows with `0` invalid rows.
- Full analyze was interrupted before producing output, so no fresh analyze-run evidence was recorded.
- Pre-Bayes returned no policy, no gate, no canonical structural active regime, no structural confidence, and no structural probabilities.
- Policy training reported `analyze_runs=0`, entry models not ready, `matched_rows=0`, and structural path ranking runtime `disabled` with `active_match_count=0`.
- Structural target export produced `2` rows, `1` mature row, `0` rows with calibrated path probability, `0` rows with path lower bound, and `0` rows with execution gate status.
- Structural bundle exposed the TOMAC branch with `selected_path_probability=0.8290155440414507`, but this was not calibrated path-ranker probability.
- Execution candidate stayed `review_status=observe`, `ready=false`, `actionable=false`, and no calibrated path probability or lower bound.
- Workflow refresh had `actionable_artifacts=0` and `consumed_trend_status=no_consumed_validation`.

## ES Readback

- Auto-Quant results import succeeded: `n_ok=1`, `n_error=0`.
- Auto-Quant prior init succeeded with `evidence_value_gate_passed=true`, `trade_count=115`, `n_win=59`, `n_loss=56`.
- Real-trade ingest applied `115/115` rows with `0` invalid rows.
- Full analyze was interrupted before producing output, so no fresh analyze-run evidence was recorded.
- Pre-Bayes returned no policy, no gate, no canonical structural active regime, no structural confidence, and no structural probabilities.
- Policy training reported `analyze_runs=0`, entry models not ready, `matched_rows=0`, and structural path ranking runtime `disabled` with `active_match_count=0`.
- Structural target export produced `2` rows, `1` mature row, `0` rows with calibrated path probability, `0` rows with path lower bound, and `0` rows with execution gate status.
- Structural bundle exposed the TOMAC branch with `selected_path_probability=0.7737704918032787`, but this was not calibrated path-ranker probability.
- Execution candidate stayed `review_status=observe`, `ready=false`, `actionable=false`, and no calibrated path probability or lower bound.
- Workflow refresh had `actionable_artifacts=0` and `consumed_trend_status=no_consumed_validation`.

## Gate

- `support_once:141000_real_trades_downstream_readback_v1`
- `evidence_class:long_history_real_trade_downstream_fail_closed`
- `pass:real_trade_export_192_records`
- `pass:nq_auto_quant_import_prior_ingest_exit0`
- `pass:es_auto_quant_import_prior_ingest_exit0`
- `pass:nq_real_trades_ingest_77_of_77_invalid0`
- `pass:es_real_trades_ingest_115_of_115_invalid0`
- `partial:nq_structural_branch_visible_selected_path_probability_0_8290`
- `partial:es_structural_branch_visible_selected_path_probability_0_7738`
- `fail_closed:nq_analyze_interrupted_exit130`
- `fail_closed:es_analyze_interrupted_exit130`
- `fail_closed:local_tomac_replay_not_provider_owned_acquisition`
- `fail_closed:not_cross_market_provider_matrix_validation`
- `fail_closed:pre_bayes_policy_absent`
- `fail_closed:canonical_structural_confidence_absent`
- `fail_closed:no_regime_probability_ge_0_95`
- `fail_closed:path_ranker_runtime_disabled`
- `fail_closed:entry_models_matched_rows_0`
- `fail_closed:calibrated_path_prob_absent`
- `fail_closed:path_prob_lower_bound_absent`
- `fail_closed:execution_ready_false`
- `fail_closed:actionable_false`
- `fail_closed:no_consumed_validation`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Do not promote from `141000`. Count it exactly once as support-only downstream evidence for the long-history TOMAC family. The next useful fresh packet should use provider-backed or portable local-trained input with enough sample size, then complete the ordered Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree chain with calibrated per-regime confidence/lower-bound and cross-market/timeframe/provider validation.
