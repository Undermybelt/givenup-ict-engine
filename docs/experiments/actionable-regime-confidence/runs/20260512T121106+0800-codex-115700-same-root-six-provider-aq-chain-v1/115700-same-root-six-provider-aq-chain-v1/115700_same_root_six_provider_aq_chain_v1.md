# 115700 Same-Root Six-Provider AQ Chain v1

Run id: `20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1`
Symbol: `B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_115700`
Provider/AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Scope
This run consumes the settled `115700` comparable 1h six-provider AQ packet and carries its rooted trade rows through ict-engine downstream readbacks.
It does not edit ict-engine runtime code and does not promote a live-trade candidate.

## Provider Rows
- `yfinance_btc_usd_1h`: rows `971`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_default_binance_btcusdt_1h`: rows `720`, exit `0`.
- `ibkr_btc_paxos_30d_1h_midpoint`: rows `783`, exit `0`.

## AQ Results
- `yfinance`: rows `971`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `13`, profit_pct `1.83`, win_rate_pct `53.84615384615385`, profit_factor `1.837494864219173`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.18`, win_rate_pct `37.5`, profit_factor `0.8671168003674068`.
- `kraken_public`: rows `721`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_default_binance`: rows `720`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `25`, profit_pct `-1.03`, win_rate_pct `32.0`, profit_factor `0.765930096934388`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-1.47`, win_rate_pct `16.666666666666664`, profit_factor `0.34369888998507653`.
- `ibkr_paxos_long_midpoint`: rows `783`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `32`, profit_pct `0.98`, win_rate_pct `37.5`, profit_factor `1.1923059186034541`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-0.27`, win_rate_pct `25.0`, profit_factor `0.8524420093984961`.

## Chain Readback
- Materialized rooted trades: `237`.
- Trades by provider: `{'yfinance': 21, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_default_binance': 37, 'ibkr_paxos_long_midpoint': 44}`.
- Provider AQ run success: `6/6`.
- Ordered command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- CatBoost feature-support exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Pre-Bayes gate: `None`.
- Raw scored mature: `237/30`.
- Production validation: `237/30`.
- Observation validation: `237/30`.
- Trainer artifact ready: `True` status `runtime_eligible`.
- Runtime selection: `enabled_candidate_set_ready` ready `True`.
- Execution ready/actionable: `False` / `False` review `observe`.

## Decision
- Gate result: `115700_same_root_six_provider_aq_chain=full_1h_provider_authority_downstream_ran_but_execution_fail_closed`.
- Same-root comparable 1h provider authority is present, but promotion remains blocked until downstream execution is ready/actionable with non-observe review.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/115700-same-root-six-provider-aq-chain-v1/115700_same_root_six_provider_aq_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/checks/115700_same_root_six_provider_aq_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/115700-same-root-six-provider-aq-chain-v1/prompt_to_artifact_checklist_115700_same_root_six_provider_aq_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/derived/same_root_six_provider_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/derived/strategy_library_same_root_six_provider_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T121106+0800-codex-115700-same-root-six-provider-aq-chain-v1/state_six_provider_chain_v1`
- CatBoost cleanup: `catboost_info_absent`
