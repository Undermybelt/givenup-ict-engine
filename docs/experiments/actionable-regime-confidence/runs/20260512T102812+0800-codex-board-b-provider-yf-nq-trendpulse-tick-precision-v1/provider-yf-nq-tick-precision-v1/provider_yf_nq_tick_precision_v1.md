# Provider YF NQ Tick Precision Readback v1

Run id: `20260512T102812+0800-codex-board-b-provider-yf-nq-trendpulse-tick-precision-v1`

Source workspace: `docs/experiments/actionable-regime-confidence/runs/20260512T102332+0800-codex-board-b-provider-yf-nq-trendpulse-aq-v1`

## Summary

This run copied the `102332` provider-owned Yahoo NQ workspace and changed only the copied TOMAC/Freqtrade synthetic-market precision from `amount=8, price=8` to `amount=0.000001, price=0.01`.

The precision-only repair changed the NQ entry-wire result from zero executed trades to nonzero executed trades:

- `ProviderNqSampledPulse`: `18` trades, `0.9700%` total profit, Sharpe `0.1898`, win rate `33.3333%`, profit factor `5.3246`, max drawdown about `0.16%`.
- `ProviderNqTrendPulse`: `896` trades, `-38.1000%` total profit, Sharpe `-3.3038`, win rate `37.7232%`, profit factor `0.5912`, max drawdown about `40.97%`.

Interpretation:

- The NQ zero-trade symptom was not only signal absence. The copied synthetic-market precision can suppress Freqtrade fills.
- `ProviderNqSampledPulse` proves provider-owned NQ data can generate real executed trades after the precision repair, but `18` trades is still below a mature factor threshold and the branch path is diagnostic, not a Board A accepted branch contract.
- `ProviderNqTrendPulse` is retired for this shape because the precision-repaired dense strategy is strongly loss-making.

## Provider Fields

- `aq_provider_invoked=true`.
- `provider_requested=yfinance/YF Yahoo NQ=F 1h via source workspace 102332`.
- `provider_data_acquired=true via copied provider-owned NQ workspace`.
- `provider_unreachable=not_reprobed_this_slice`.
- `providers_not_invoked_this_slice=IBKR,TradingViewRemix/TVR,Kraken,Binance,Bybit`.
- `local_cache_replay=provider_workspace_replay_from_102332`.
- `aq_handoff_or_run_artifact=provider_yf_nq_tick_precision_strategy_library_v1.json`.
- `regime_profit_branch_path=Bull -> ProviderYfNq -> SampledPulseDiagnostic -> ProviderNqSampledPulse:provider_yf_nq_sampled_pulse_h48`.

## ict-engine Consumption

The repaired packet was materialized and consumed in an isolated state:

- Strategy library: `provider_yf_nq_tick_precision_strategy_library_v1.json`.
- Real trades JSONL: `provider_yf_nq_sampled_pulse_real_trades_v1.jsonl`.
- `auto-quant-results-import` exited `0`, with `n_ok=2`.
- `auto-quant-prior-init` exited `0` for `ProviderNqSampledPulse`, with `evidence_value_gate_passed=true` and final probabilities `[0.538448, 0.000006769230769230769, 0.46154523076923076]`.
- `auto-quant-ingest-real-trades` exited `0`, with `18/18` trades applied and `0` invalid rows.
- `pre-bayes-status` exited `0`, but there was no latest bridge, gate, policy, or structural context.
- `policy-training-status` exited `0`, but had `analyze_runs=0`, `update_runs=0`, and path-ranker runtime disabled.
- `export-structural-path-ranking-target` exited `0`, but exported only `1` unobserved row, with `mature_rows=0`.
- `workflow-status --phase execution-candidate` exited `0`, but stayed `ready=false`, `review_status=observe`, and `path_label=bootstrap_readiness`.

## Gate

- `count_once:102812_provider_yf_nq_tick_precision_repair`.
- `pass:provider_owned_nq_tick_precision_repair_created_nonzero_trades`.
- `pass:auto_quant_results_import_n_ok_2`.
- `pass:auto_quant_prior_init_evidence_value_gate_passed`.
- `pass:auto_quant_real_trade_ingest_18_of_18_invalid_0`.
- `fail_closed:sampled_pulse_only_18_trades_below_mature_threshold`.
- `fail_closed:sampled_pulse_branch_path_diagnostic_not_board_a_contract`.
- `fail_closed:trendpulse_precision_repaired_shape_negative_minus_38_10_pct`.
- `fail_closed:provider_matrix_incomplete_yf_only_this_slice`.
- `fail_closed:pre_bayes_no_latest_gate_or_bridge`.
- `fail_closed:path_ranker_target_mature_rows_0`.
- `fail_closed:execution_candidate_ready_false`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not rerun the pre-fix `102332` zero-trade shape as if it proved signal absence. The next non-duplicative NQ slice should use the copied-harness tick-size repair from the start, map any profitable strategy to a real Board A rooted branch path, and satisfy the full AQ/provider matrix before downstream promotion is considered.
