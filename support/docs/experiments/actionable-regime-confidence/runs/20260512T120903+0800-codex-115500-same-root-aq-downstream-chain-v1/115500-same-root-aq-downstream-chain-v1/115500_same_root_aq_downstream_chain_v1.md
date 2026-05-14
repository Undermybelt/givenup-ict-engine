# 115500 Same-Root AQ Downstream Chain v1

Run id: `20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1`
Source AQ root: `20260512T115500+0800-codex-six-provider-btc-same-root-aq-ibkr-aggtrades-probe-v1`
Symbol: `B2R_SIX_PROVIDER_BTC_AQ_115500`

## Scope
This run consumes the settled 115500 six-provider 1h AQ packet and pushes it through ict-engine Pre-Bayes/filter, BBN, CatBoost/path-ranker, and execution-tree surfaces.
It does not edit ict-engine runtime code, approve selected history, mutate canonical source/control roots, promote a candidate, or call `update_goal`.

## Source AQ Readback
- Provider AQ success: `6/6`.
- Strategies with metrics: `12`.
- Total AQ trades: `245`.
- Materialized rooted trades for downstream ingestion: `245`.
- Trades by provider: `{'yfinance': 22, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_binance': 37, 'ibkr_aggtrades': 51}`.

## Chain Readback
- Ordered command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- Augmented CatBoost exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Pre-Bayes gate: `None`.
- Raw scored mature: `245/30`.
- Production validation: `245/30`.
- Observation validation: `245/30`.
- Trainer artifact ready: `True` status `runtime_eligible`.
- Runtime selection: `enabled_candidate_set_ready` ready `True`.
- Execution ready/actionable: `False` / `False` review `observe`.
- CatBoost cleanup: `catboost_info_absent`.

## Decision
- Gate result: `115500_same_root_aq_downstream_chain_v1=six_provider_1h_aq_to_downstream_ran_execution_fail_closed_no_promotion`.
- The six-provider AQ root is first-class and comparable 1h, but Board A promotion still requires non-observe execution admissibility and the strict acceptance axes.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/115500-same-root-aq-downstream-chain-v1/115500_same_root_aq_downstream_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/checks/115500_same_root_aq_downstream_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/115500-same-root-aq-downstream-chain-v1/prompt_to_artifact_checklist_115500_same_root_aq_downstream_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/derived/115500_same_root_six_provider_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/derived/strategy_library_115500_same_root_six_provider_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T120903+0800-codex-115500-same-root-aq-downstream-chain-v1/state_115500_downstream_chain_v1`
