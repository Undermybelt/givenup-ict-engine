# 115500 Same-Root Six-Provider AQ Chain v1

Run id: `20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1`
Symbol: `B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_115500`
Provider/AQ root: `20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1`

## Scope
This run consumes the settled `115500` comparable 1h six-provider AQ packet and carries its rooted trade rows through ict-engine downstream readbacks.
It does not edit ict-engine runtime code and does not promote a live-trade candidate.

## Provider Rows
- `yfinance_btc_usd_1h`: rows `983`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_binance_btcusdt_1h`: rows `720`, exit `0`.
- `ibkr_btc_paxos_aggtrades_1h`: rows `783`, exit `0`.

## AQ Results
- `yfinance`: rows `983`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `14`, profit_pct `1.69`, win_rate_pct `50.0`, profit_factor `1.7314733582840918`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.21`, win_rate_pct `37.5`, profit_factor `0.8505535234732061`.
- `kraken_public`: rows `721`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_binance`: rows `720`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `25`, profit_pct `-1.03`, win_rate_pct `32.0`, profit_factor `0.765930096934388`.
  - `ProviderCryptoPullbackRevertV1`: trades `12`, profit_pct `-1.47`, win_rate_pct `16.666666666666664`, profit_factor `0.34369888998507653`.
- `ibkr_aggtrades`: rows `783`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `0.08`, win_rate_pct `38.23529411764706`, profit_factor `1.0144516414659697`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `1.31`, win_rate_pct `52.94117647058824`, profit_factor `1.6850347091222428`.

## Chain Readback
- Materialized rooted trades: `245`.
- Trades by provider: `{'yfinance': 22, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_binance': 37, 'ibkr_aggtrades': 51}`.
- Provider AQ run success: `6/6`.
- Ordered command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- Pre-Bayes gate: `None`.
- Raw scored mature: `0/30`.
- Production validation: `0/30`.
- Observation validation: `245/30`.
- Trainer artifact ready: `True` status `present_validation_insufficient`.
- Runtime selection: `enabled_no_matching_scores` ready `False`.
- Execution ready/actionable: `False` / `False` review `observe`.

## Decision
- Gate result: `115500_same_root_six_provider_aq_chain=full_1h_provider_authority_downstream_ran_but_execution_fail_closed`.
- Same-root comparable 1h provider authority is present, but promotion remains blocked until downstream execution is ready/actionable with non-observe review.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/115500-same-root-six-provider-aq-chain-v1/115500_same_root_six_provider_aq_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/checks/115500_same_root_six_provider_aq_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/115500-same-root-six-provider-aq-chain-v1/prompt_to_artifact_checklist_115500_same_root_six_provider_aq_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/derived/same_root_six_provider_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/derived/strategy_library_same_root_six_provider_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T120746+0800-codex-115500-same-root-six-provider-aq-chain-v1/state_six_provider_chain_v1`
- CatBoost cleanup: `catboost_info_absent`
