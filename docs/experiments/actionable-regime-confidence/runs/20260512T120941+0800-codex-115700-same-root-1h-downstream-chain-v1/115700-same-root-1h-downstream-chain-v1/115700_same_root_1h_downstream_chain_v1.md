# 115700 Same-Root 1h Downstream Chain v1

Run id: `20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
Symbol: `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700`

## Scope
This run consumes the settled `115700` six-provider 1h AQ packet and pushes it through the ordered downstream stack.
It does not rerun Auto-Quant, edit ict-engine runtime code, approve selected history, or claim live trade use.

## Source AQ Readback
- Provider fetch success: `6`.
- AQ provider runs: `6/6`.
- Strategies with metrics: `12`.
- Total AQ trades: `237`.
- Materialized rooted trades for ingestion: `237`.
- Trades by provider: `{'yfinance': 21, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_default_binance': 37, 'ibkr_paxos_long_midpoint': 44}`.

## Ordered Chain Readback
- Command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0, '40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Pre-Bayes gate: `pass_neutralized`.
- Raw scored mature: `237/30`.
- Production validation: `237/30`.
- Observation validation: `237/30`.
- Trainer artifact ready: `True` status `runtime_eligible`.
- Runtime selection: `enabled_candidate_set_ready` ready `True`.
- Execution ready/actionable: `False` / `False` review `observe`.
- CatBoost cleanup: `catboost_info_absent`.

## Decision
- Gate result: `115700_same_root_1h_downstream_chain_v1=ordered_chain_ran_from_six_provider_1h_aq_packet_but_requires_board_gate_readback_no_completion`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/115700-same-root-1h-downstream-chain-v1/115700_same_root_1h_downstream_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/checks/115700_same_root_1h_downstream_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/115700-same-root-1h-downstream-chain-v1/prompt_to_artifact_checklist_115700_same_root_1h_downstream_chain_v1.csv`
- Trades: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/derived/same_root_1h_six_provider_aq_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/derived/strategy_library_115700_same_root_1h_aq_v1.json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T120941+0800-codex-115700-same-root-1h-downstream-chain-v1/state_115700_downstream_chain_v1`
