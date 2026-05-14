# 112315 Same-Root Six-Provider AQ Chain v1

Run id: `20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1`
Symbol: `B2R_PROVIDER_MATRIX_SIX_PROVIDER_AQ_112315`
Provider root: `20260512T112315+0800-codex-board-b-six-provider-btc-matrix-probe-v1`

## Scope
This run consumes only the `112315` provider matrix root for all six required provider names.
TVR and IBKR are routed through their same-root daily bars instead of the mixed-source 1h precheck rows used by `113833`.
It does not edit ict-engine runtime code and keeps all AQ workspaces under this run root.

## Provider Rows
- `yfinance_btc_usd_1h`: rows `983`, exit `0`.
- `kraken_xbtusd_1h`: rows `721`, exit `0`.
- `binance_btcusdt_1h`: rows `985`, exit `0`.
- `bybit_btcusdt_linear_1h`: rows `985`, exit `0`.
- `tvr_btc_usd_1d`: rows `29`, exit `1`.
- `ibkr_btc_paxos_aggtrades_1d`: rows `30`, exit `0`.

## AQ Results
- `yfinance`: rows `983`, source_tf `None`, aq_tf `None`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `14`, profit_pct `1.69`, win_rate_pct `50.0`, profit_factor `1.7314733582840918`.
  - `ProviderCryptoPullbackRevertV1`: trades `8`, profit_pct `-0.21`, win_rate_pct `37.5`, profit_factor `0.8505535234732061`.
- `kraken_public`: rows `721`, source_tf `None`, aq_tf `None`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `23`, profit_pct `-0.55`, win_rate_pct `34.78260869565217`, profit_factor `0.8609310567518771`.
  - `ProviderCryptoPullbackRevertV1`: trades `9`, profit_pct `-0.71`, win_rate_pct `22.22222222222222`, profit_factor `0.5831340534022595`.
- `binance_public`: rows `985`, source_tf `None`, aq_tf `None`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `37`, profit_pct `0.77`, win_rate_pct `37.83783783783784`, profit_factor `1.1326410355009617`.
  - `ProviderCryptoPullbackRevertV1`: trades `15`, profit_pct `-0.98`, win_rate_pct `26.666666666666668`, profit_factor `0.5850842589000907`.
- `bybit_public`: rows `985`, source_tf `None`, aq_tf `None`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `34`, profit_pct `1.48`, win_rate_pct `41.17647058823529`, profit_factor `1.288511226299377`.
  - `ProviderCryptoPullbackRevertV1`: trades `17`, profit_pct `-1.71`, win_rate_pct `23.52941176470588`, profit_factor `0.45016637432495576`.
- `tvr_btc_usd_daily`: rows `29`, source_tf `1d`, aq_tf `1d`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `4`, profit_pct `1.1`, win_rate_pct `75.0`, profit_factor `2.2857542696728324`.
  - `ProviderCryptoPullbackRevertV1`: trades `1`, profit_pct `0.4`, win_rate_pct `100.0`, profit_factor `0.0`.
- `ibkr_btc_paxos_aggtrades_daily`: rows `30`, source_tf `1d`, aq_tf `1d`, compile `0`, TOMAC `0`.
  - `ProviderCryptoMomentumStateV1`: trades `7`, profit_pct `5.21`, win_rate_pct `85.71428571428571`, profit_factor `5.485935691745877`.
  - `ProviderCryptoPullbackRevertV1`: trades `1`, profit_pct `0.4`, win_rate_pct `100.0`, profit_factor `0.0`.

## Chain Readback
- Materialized rooted trades: `170`.
- Trades by provider: `{'yfinance': 22, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_btc_usd_daily': 5, 'ibkr_btc_paxos_aggtrades_daily': 8}`.
- Provider AQ run success: `6/6`.
- Ordered command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- Pre-Bayes gate: `None`.
- Raw scored mature: `0/30`.
- Production validation: `0/30`.
- Observation validation: `170/30`.
- Trainer artifact ready: `True` status `present_validation_insufficient`.
- Runtime selection: `enabled_no_matching_scores` ready `False`.
- Execution ready/actionable: `False` / `False` review `observe`.

## Decision
- Gate result: `112315_same_root_six_provider_aq_chain=same_root_provider_authority_repaired_but_execution_fail_closed`.
- This is stronger than `112904` and `113833` on provider authority because all six source CSVs come from `112315`, and TVR/IBKR have successful same-root AQ runs on daily bars.
- Promotion still requires execution readiness/actionability and a non-observe release decision; this report does not override fail-closed workflow status.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/112315-same-root-six-provider-aq-chain-v1/112315_same_root_six_provider_aq_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/checks/112315_same_root_six_provider_aq_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/112315-same-root-six-provider-aq-chain-v1/prompt_to_artifact_checklist_112315_same_root_six_provider_aq_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/derived/same_root_six_provider_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/derived/strategy_library_same_root_six_provider_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T115204+0800-codex-112315-same-root-six-provider-aq-chain-v1/state_six_provider_chain_v1`
- CatBoost cleanup: `catboost_info_absent`
