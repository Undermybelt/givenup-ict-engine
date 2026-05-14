# 104902 Exact Downstream Readback v1

## Scope

Exact-root downstream readback for source root `20260512T104902+0800-codex-board-b-yahoo-btc-pullback-precision-aq-v1`.

Source branch:
`Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1`.

This packet does not promote a candidate, does not satisfy the six-provider authority gate, does not approve selected history, does not approve source/control evidence, and does not call `update_goal`.

## Source Readback

- Strategy: `ProviderCryptoPullbackRevertV1`.
- Symbol/pair/timeframe: BTC/USDT `1h`.
- Trades: `146`.
- Total profit: `+2.83%`.
- Sharpe: `0.1875`.
- Profit factor: `1.1186`.
- Win rate: `45.2055%`.
- Max drawdown: `-4.2915%`.

The source library preserves the required branch fields:

- `main_regime=Range`
- `sub_regime=ProviderCryptoPullback`
- `sub_sub_regime_or_profit_factor=MeanRevertBounce`
- `profit_factor=ProviderCryptoPullbackRevertV1`

## Ordered Chain Readback

All ordered command exits were `0`:

- `auto-quant-results-import`: imported `n_ok=1`.
- `auto-quant-prior-init`: applied `ProviderCryptoPullbackRevertV1`, `trade_count=146`, `evidence_value_gate_passed=true`.
- `auto-quant-ingest-real-trades`: applied `146/146` trades, `0` invalid, inserted `146` feedback records.
- `pre-bayes-status`: no latest bridge, policy, soft evidence, filtered assignments, canonical structural regime, or gate status.
- `policy-training-status`: entry models not ready, `matched_rows=0`; structural path-ranking runtime disabled.
- `export-structural-path-ranking-target`: exported `rows=1`, `history_rows=1`, `mature_rows=0`.
- `workflow-status` structural bundle: selected `bootstrap_readiness`, direction `observe`.
- `workflow-status` execution candidate: `ready=false`, `actionable=false`.
- full `workflow-status`: `closed_loop_branch_admission.status=fail_closed`.

The BBN network file was written under the run-local state directory, but Pre-Bayes/policy and CatBoost/path-ranker readiness did not materialize.

## Branch Parity

Source-side parity is present in the strategy library and learning state.

Downstream parity is broken for promotion purposes:

- The structural path-ranking target row has an empty `regime_profit_branch_path`.
- The execution path is `bootstrap_readiness`, not the source branch path.
- The execution candidate is `observe`, `ready=false`, and `actionable=false`.

## Gate

- `count_once:110224_104902_exact_downstream_readback`.
- `pass:all_ordered_downstream_commands_exit0`.
- `pass:strategy_library_imported_n_ok_1`.
- `pass:prior_init_evidence_value_gate_passed`.
- `pass:real_trades_ingested_146_invalid_0`.
- `pass:bbn_network_written`.
- `fail_closed:pre_bayes_policy_absent`.
- `fail_closed:entry_model_matched_rows_0`.
- `fail_closed:structural_target_mature_rows_0`.
- `fail_closed:catboost_path_ranker_runtime_disabled`.
- `fail_closed:path_ranker_trainer_artifact_not_ready`.
- `fail_closed:execution_candidate_ready_false_actionable_false`.
- `fail_closed:workflow_bootstrap_readiness_observe_only`.
- `fail_closed:exact_source_branch_not_preserved_into_structural_target_or_execution_tree`.
- `fail_closed:six_provider_authority_gate_not_satisfied`.
- `fail_closed:no_selected_history_or_source_control_unlock`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not promote `104902`. The useful next slice is a fresh provider-matrix-backed AQ packet or a source-root that produces non-bootstrap mature observations and preserves the exact rooted branch through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
