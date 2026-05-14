# Six-Provider BTC Same-Root AQ IBKR AGGTRADES Chain v1

Run id: `20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1`
Symbol: `B2R_SIX_PROVIDER_BTC_1H_AQ_115500`

## Scope
Consumes the fresh `115500` same-root six-provider 1h AQ outputs and runs the ordered downstream chain.
No provider refetch, no ict-engine runtime code edits, no selected-history approval, and no promotion.

## Chain Readback
- Provider AQ run success: `6/6`.
- Strategy/provider metric sets: `12`.
- Materialized rooted trades: `245`.
- Trades by provider: `{'yfinance': 22, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_binance': 37, 'ibkr_aggtrades': 51}`.
- Ordered command exits: `{'20_auto_quant_results_import_1h': 0, '21_auto_quant_prior_init_1h': 0, '22_ingest_real_trades_1h': 0, '23_analyze_provider_data_1h': 0, '24_pre_bayes_status_1h': 0, '25_policy_training_status_before_export_1h': 0, '26_export_structural_path_ranking_target_1h': 0, '27_train_catboost_1h': 1, '28_apply_catboost_history_1h': 1, '29_apply_external_scores_1h': 1, '30_register_trainer_artifact_1h': 0, '31_enable_runtime_1h': 0, '32_policy_training_status_final_1h': 0, '33_workflow_execution_candidate_1h': 0, '34_workflow_full_1h': 0}`.
- Pre-Bayes gate: `None`.
- Raw scored mature: `0/30`.
- Production validation: `0/30`.
- Observation validation: `245/30`.
- Trainer artifact ready: `True` status `present_validation_insufficient`.
- Runtime selection: `enabled_no_matching_scores` ready `False`.
- Execution ready/actionable: `False` / `False` review `observe`.

## Decision
- Gate result: `six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1=fresh_1h_six_provider_aq_to_downstream_ran_fail_closed_no_promotion`.
- This repairs the earlier TVR/IBKR daily-template mismatch by using fresh 1h TVR and IBKR AQ inputs, but it still does not create promotion authority.
- Promotion remains blocked unless selected-history/source-control approval, CatBoost/runtime scored mature rows, production validation, runtime matches, and non-observe execution admissibility all pass.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/six-provider-btc-same-root-aq-ibkr-aggtrades-chain-v1/six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/checks/six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/six-provider-btc-same-root-aq-ibkr-aggtrades-chain-v1/prompt_to_artifact_checklist_six_provider_btc_same_root_aq_ibkr_aggtrades_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/derived/six_provider_1h_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/derived/strategy_library_six_provider_1h_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1/state_six_provider_1h_chain_v1`
- CatBoost cleanup: `catboost_info_absent`
