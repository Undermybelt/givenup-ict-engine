# 115700 Six-Provider 1h Downstream Chain v1

Run id: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
Symbol: `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Scope
This run consumes the completed `115700` six-provider 1h provider/AQ packet and does not launch new provider fetches or AQ/TOMAC jobs.
It runs the ordered downstream chain from the materialized AQ trade observations through Pre-Bayes/filter, BBN state surfaces, CatBoost/path-ranker, and workflow/execution-tree readback.
It does not edit ict-engine runtime code, approve selected history/source-control intake, or promote a live-trade candidate.

## Source Authority
- Source gate: `same_root_six_provider_1h_aq_v1=six_provider_1h_provider_aq_packet_ready_for_downstream_no_promotion`.
- Source provider fetch success: `6/6` listed providers; source report `provider_fetch_success=6`.
- Source AQ provider runs: `6/6`.
- Source metric sets/trades: `12` / `237`.
- Materialized rooted trades: `237`.
- Trades by provider: `{'yfinance': 21, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_default_binance': 37, 'ibkr_paxos_long_midpoint': 44}`.
- Trades by path: `{'Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1': 164, 'Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1': 73}`.

## Ordered Chain Readback
- Command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- Pre-Bayes gate: `pass_neutralized`.
- Standard ranker raw scored mature: `0/30`.
- Standard ranker production validation: `0/30`.
- Standard ranker observation validation: `237/30`.
- Standard trainer artifact ready: `True` status `present_validation_insufficient`.
- Standard runtime selection: `enabled_no_matching_scores` ready `False`.
- Standard execution ready/actionable: `False` / `False` review `observe`.

## CatBoost Feature-Support Readback
- Augmented command exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Augmented raw scored mature: `237/30`.
- Augmented production validation: `237/30`.
- Augmented observation validation: `237/30`.
- Augmented runtime selection: `enabled_candidate_set_ready` ready `True`.
- Augmented execution ready/actionable: `False` / `False` review `observe`.

## Decision
- Gate result: `115700_six_provider_1h_downstream_chain_v1=six_provider_1h_aq_consumed_by_prebayes_bbn_catboost_pathranker_but_execution_observe_no_promotion`.
- The six-provider 1h packet is now carried through the downstream chain, and augmented CatBoost/path-ranker support is attempted from the same run state.
- Promotion remains blocked unless execution-tree readiness/actionability becomes non-observe and the strict Board A per-regime/cross-axis acceptance contract is satisfied.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/115700-enriched-downstream-chain-v1/base-downstream-support/115700_six_provider_1h_downstream_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/checks/115700_six_provider_1h_downstream_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/115700-enriched-downstream-chain-v1/base-downstream-support/prompt_to_artifact_checklist_115700_six_provider_1h_downstream_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.repaired.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/strategy_library_same_root_six_provider_1h_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/state_115700_enriched_downstream_chain_v1`
- Augmented history scores: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/path-ranker/catboost_feature_support_v1/history_scores_augmented.csv`
- CatBoost cleanup: `catboost_info_absent`
