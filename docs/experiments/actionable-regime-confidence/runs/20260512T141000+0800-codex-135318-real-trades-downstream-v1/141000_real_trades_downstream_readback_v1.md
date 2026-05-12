# 141000 Real-Trade Downstream Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T141000+0800-codex-135318-real-trades-downstream-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T135318+0800-codex-long-history-es-nq-aq-staging-v1`

Status: `fail_closed`.

This root is support-only downstream plumbing evidence. It proves import/prior/real-trade ingest and workflow readbacks can be driven for the `135318` TOMAC family, but it does not prove Board A acceptance or Board B profitability promotion.

## Provider Authority

Required provider authority sidecar: `aq_provider_authority_matrix_141000.csv`.

All six required rows are present as a fail-closed classification:

- `IBKR`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.
- `TradingViewRemix/TVR`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.
- `yfinance/YF`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.
- `Kraken`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.
- `Binance`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.
- `Bybit`: `aq_provider_invoked=false`, `provider_requested=false`, `provider_data_acquired=false`, `local_cache_replay=true`.

Gate: `fail_closed:aq_provider_authority_missing`.

## Readback

- Real-trade export produced `192` records from the `135318` long-history TOMAC family.
- Aggregate metrics: `192` trades, profit `11.64%`, win rate `59.8958%`, profit factor `1.1615`, Sharpe `0.0449`.
- NQ metrics: `77` trades, profit `9.5%`, win rate `72.7273%`, profit factor `1.3086`, Sharpe `0.0336`.
- ES metrics: `115` trades, profit `2.14%`, win rate `51.3043%`, profit factor `1.0518`, Sharpe `0.0088`.
- NQ import/prior/ingest exited `0`; ingest applied `77/77` trades with `0` invalid.
- ES import/prior/ingest exited `0`; ingest applied `115/115` trades with `0` invalid.
- NQ analyze exited `130` after watchdog interruption: `nq_analyze_15m_1h_1d_exceeded_20m_no_output_no_new_state`.
- ES analyze exited `130` after watchdog interruption: `es_analyze_15m_1h_1d_aborted_after_nq_same_path_exceeded_20m`.
- NQ and ES Pre-Bayes status readbacks exited `0`, but latest bridge, canonical structural regime, confidence, filtered assignments, gate status, policy, and soft evidence were all absent.
- NQ and ES policy-training readbacks exited `0`, but both entry models had `matched_rows=0`, BBN/CatBoost not ready, and structural path-ranking runtime disabled.
- NQ and ES structural path target exports each produced `2` rows, `1` mature row, `0` raw path score rows, `0` calibrated path probability rows, `0` path lower-bound rows, and `0` execution gate rows.
- NQ execution candidate: `execution_candidate_observed`, posterior `0.7273`, selected path probability `0.8290`, `ready=false`, `actionable=false`, review `observe`.
- ES execution candidate: `execution_candidate_observed`, posterior `0.5130`, selected path probability `0.7738`, `ready=false`, `actionable=false`, review `observe`.
- Both workflow full readbacks reported closed-loop branch admission `status=fail_closed`, reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Gate

- `support_once:141000_es_nq_real_trade_downstream_readback_v1`.
- `evidence_class:local_replay_downstream_chain_contract_sample`.
- `partial:auto_quant_results_import_prior_init_real_trade_ingest`.
- `partial:structural_path_visible`.
- `fail_closed:aq_provider_authority_missing`.
- `fail_closed:local_tomac_replay_not_provider_acquisition`.
- `fail_closed:nq_analyze_interrupted_130`.
- `fail_closed:es_analyze_interrupted_130`.
- `fail_closed:pre_bayes_latest_canonical_missing`.
- `fail_closed:policy_training_matched_rows_0`.
- `fail_closed:path_ranker_runtime_disabled`.
- `fail_closed:calibrated_path_prob_absent`.
- `fail_closed:path_prob_lower_bound_absent`.
- `fail_closed:execution_gate_rows_0`.
- `fail_closed:ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Count this root exactly once as support-only downstream plumbing evidence. Do not promote the TOMAC family from this local replay. The next material packet must start from AQ-owned or AQ-routed provider acquisition across `IBKR`, `TradingViewRemix/TVR`, `yfinance/YF`, `Kraken`, `Binance`, and `Bybit`, then run provider-backed data through Auto-Quant, filter/Pre-Bayes, BBN, CatBoost/path-ranker, and execution-tree admission.

## Bounded 1h/4h/1d Follow-Up

Concurrent follow-up commands added bounded `1h/4h/1d` readbacks in the same root after the initial `01..22` classification. These do not change the promotion decision.

- NQ bounded analyze `23_nq_analyze_1h_4h_1d` exited `142` under the `240s` alarm; stdout/stderr remained empty.
- ES bounded analyze `30_es_analyze_1h_4h_1d` exited `142` under the `240s` alarm; stdout/stderr remained empty.
- NQ follow-up readbacks `24..29` exited `0`.
- ES follow-up readbacks `31..36` exited `0`; `35_es_workflow_execution_candidate_after_1h.out` and `36_es_workflow_full_after_1h.out` provide the final ES workflow state.
- NQ and ES Pre-Bayes status still had no latest canonical structural regime, confidence, probabilities, filtered assignments, gate status, policy, bridge, or soft evidence.
- NQ and ES policy-training still had `analyze_runs=0`, `matched_rows=0`, entry models not ready, and BBN/CatBoost not ready.
- NQ ranker observation validation became visible at `77/30`, but raw scored mature rows and production validation stayed `0/30`; calibration remained not fitted, trainer artifact missing, and runtime selection disabled.
- ES ranker observation validation became visible at `115/30`, but raw scored mature rows and production validation stayed `0/30`; calibration remained not fitted, trainer artifact missing, and runtime selection disabled.
- NQ and ES structural targets remained `rows=2`, `mature_rows=1`, `rows_with_calibrated_path_prob=0`, `rows_with_path_prob_lower_bound=0`, and `rows_with_execution_gate_status=0`.
- NQ and ES workflow full readbacks still reported closed-loop branch admission `status=fail_closed`, `ready=false`, `actionable=false`, reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

Additional gates:

- `partial:bounded_1h_4h_1d_readbacks_completed`.
- `partial:nq_observation_validation_77_of_30`.
- `partial:es_observation_validation_115_of_30`.
- `fail_closed:nq_bounded_analyze_exit142`.
- `fail_closed:es_bounded_analyze_exit142`.
- `fail_closed:raw_scored_mature_0_of_30`.
- `fail_closed:production_validation_0_of_30`.
- `fail_closed:trainer_artifact_missing`.
- `fail_closed:calibration_not_fitted`.
- `fail_closed:runtime_selection_disabled`.
- `fail_closed:aq_provider_authority_missing`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
