# 135722 Long-History ES/NQ AQ Downstream Readback v1

## Scope

This is a settled readback for `20260512T135722+0800-codex-long-history-es-nq-1m-aq-smoke-v1`.

The run is useful because TOMAC/Auto-Quant did execute on staged ES/NQ long-history futures data and its measured result was imported into ict-engine. It is not promotion evidence because the run lacks Auto-Quant-owned six-provider data authority and the downstream admission layers remain fail-closed.

## Evidence

- TOMAC/AQ command output: `command-output/03_tomac_backtest.out`
- Metrics CSV: `chain-artifacts/strategy_metrics.long_history_es_nq_1m_smoke_v1.csv`
- Strategy library: `chain-artifacts/strategy_library.long_history_es_nq_1m_smoke_v1.json`
- Provider matrix: `aq_provider_authority_matrix_135722.csv`
- Provider status readback: `command-output/13_provider_status_agent_readback.out`
- ict-engine state: `state_ict_chain_v1/`
- Checks: `checks/`

## Command Status

- `01_prepare_nq.exit=0`
- `02_prepare_es.exit=0`
- `03_tomac_backtest.exit=0`
- `04_auto_quant_results_import.exit=0`
- `05_auto_quant_prior_init.exit=0`
- `07_pre_bayes_status_after_incomplete_analyze.exit=0`
- `08_policy_training_status_after_aq_import.exit=0`
- `09_workflow_structural_bundle_after_aq_import.exit=0`
- `10_workflow_execution_candidate_after_aq_import.exit=0`
- `11_workflow_full_after_aq_import.exit=0`
- `12_export_structural_path_target_after_aq_import.exit=0`
- `13_provider_status_agent_readback.exit=0`

`06_analyze_nq_long_1m` left command files but no `.exit` check and no output, so it is not counted as a completed analyze/downstream evidence step.

## Auto-Quant Measurement

TOMAC/Freqtrade measured `TomacNQ_KillzoneBreakout` over staged ES/NQ long-history data:

- Aggregate: `153` trades, total profit `5.43%`, win rate `59.4771%`, Sharpe `0.0252`, profit factor `1.0984`, max drawdown `-6.8357%`.
- NQ/USD: `77` trades, total profit `9.50%`, win rate `72.7%`, Sharpe `0.0395`, profit factor `1.31`.
- ES/USD: `76` trades, total profit `-4.08%`, win rate `46.1%`, Sharpe `-0.0221`, profit factor `0.83`.

This is a real AQ/TOMAC measurement, but it is weak aggregate profitability and mixed cross-instrument evidence.

## Provider Authority Matrix

The six required provider rows are emitted in `aq_provider_authority_matrix_135722.csv`.

Important distinction:

- `provider-status --agent` was read back successfully.
- The AQ/TOMAC data path did not prove Auto-Quant-owned provider acquisition for IBKR, TradingViewRemix/TVR, yfinance/YF, Kraken, Binance, or Bybit.
- The backtest used staged local ES/NQ feather data, so `local_cache_replay=true` for every required row.

Therefore this packet fails the AQ/provider authority lock: `fail_closed:aq_provider_authority_missing`.

## Downstream Readback

Auto-Quant import and BBN prior initialization did run:

- `auto-quant-results-import`: `n_ok=1`, `n_total_strategies=1`.
- `auto-quant-prior-init`: `trade_count=153`, `n_win=91`, `n_loss=62`, `evidence_value_gate_passed=true`, final probabilities `[0.6149046459627329, 0.000001093167701863354, 0.3850942608695652]`.

But downstream admission stayed fail-closed:

- Pre-Bayes status had no policy, no gate, no canonical structural confidence, no soft evidence.
- Policy training had `analyze_runs=0`, entry model `matched_rows=0`, and path-ranker runtime disabled before export.
- Structural export produced `rows=1`, `mature_rows=0`, `rows_with_raw_path_score=0`, `rows_with_calibrated_path_prob=0`, `rows_with_path_prob_lower_bound=0`, and `rows_with_execution_gate_status=0`.
- Execution candidate was `ready=false`, `actionable=false`, `review_status=observe`, `path_label=bootstrap_readiness`, `pre_bayes_gate_status=""`, `path_ranker_calibrated_path_prob=null`, and `path_ranker_path_prob_lower_bound=null`.

## Decision

This run is support evidence for a long-history AQ measurement and a downstream fail-closed readback. It is not accepted Board A regime-confidence evidence and not accepted Board B profitability evidence.

Gate tags:

- `support_once:135722_long_history_es_nq_aq_downstream_readback_v1`
- `evidence_class:long_history_aq_measurement_chain_contract_negative_sample`
- `pass:tomac_auto_quant_backtest_exit0`
- `pass:auto_quant_import_exit0`
- `pass:auto_quant_prior_init_exit0`
- `pass:provider_status_readback_exit0`
- `fail_closed:aq_provider_authority_missing`
- `fail_closed:local_cache_replay_not_primary_authority`
- `fail_closed:analyze_step_missing_exit_check`
- `fail_closed:pre_bayes_policy_absent`
- `fail_closed:structural_path_ranker_mature_rows_0`
- `fail_closed:calibrated_path_prob_absent`
- `fail_closed:path_prob_lower_bound_absent`
- `fail_closed:execution_ready_false`
- `fail_closed:actionable_false`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Continue from this packet only by making the AQ/provider provenance matrix real at the data-acquisition layer, then rerun the ordered chain with a completed analyze step and regime/branch-keyed trade attribution. Do not promote from staged local ES/NQ replay, aggregate TOMAC metrics, or AQ prior initialization alone.
