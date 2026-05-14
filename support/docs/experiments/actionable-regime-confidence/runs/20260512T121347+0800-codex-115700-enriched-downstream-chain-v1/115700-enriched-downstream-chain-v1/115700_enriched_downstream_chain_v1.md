# 115700 Enriched Downstream Chain v1

Run id: `20260512T121347+0800-codex-115700-enriched-downstream-chain-v1`
Source AQ root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`
Symbol: `B2R_SAME_ROOT_SIX_PROVIDER_1H_AQ_115700`

## Scope
This slice consumes the already-counted `115700` six-provider 1h provider/AQ packet, repairs row-level run id/symbol/provider provenance in an isolated derived JSONL, runs the ordered downstream chain, then emits a final layer-contract JSONL with actual Pre-Bayes/BBN/CatBoost/execution-tree readback fields.
It does not edit ict-engine runtime code, recount the source provider/AQ root, approve selected history/source-control intake, promote a candidate, or call `update_goal`.

## Row Repair
- Raw materialized trades: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.raw.jsonl`.
- Repaired trades used for ingest: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.repaired.jsonl`.
- Enriched layer-contract trades: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/derived/same_root_six_provider_1h_aq_real_trades.enriched_layer_contract.jsonl`.
- Repaired/enriched rows: `237` / `237`.
- Provider counts: `{'yfinance': 21, 'kraken_public': 32, 'binance_public': 52, 'bybit_public': 51, 'tvr_default_binance': 37, 'ibkr_paxos_long_midpoint': 44}`.
- Branch counts: `{'Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1': 164, 'Range -> ProviderCryptoPullback -> MeanRevertBounce -> ProviderCryptoPullbackRevertV1': 73}`.

## Ordered Chain
- Command exits: `{'20_auto_quant_results_import': 0, '21_auto_quant_prior_init': 0, '22_ingest_real_trades': 0, '23_analyze_provider_data': 0, '24_pre_bayes_status': 0, '25_policy_training_status_before_export': 0, '26_export_structural_path_ranking_target': 0, '27_train_catboost': 1, '28_apply_catboost_history': 1, '29_apply_external_scores': 1, '30_register_trainer_artifact': 0, '31_enable_runtime': 0, '32_policy_training_status_final': 0, '33_workflow_execution_candidate': 0, '34_workflow_full': 0}`.
- Augmented CatBoost exits: `{'40_train_catboost_augmented': 0, '41_apply_catboost_augmented_history': 0, '42_apply_external_scores_augmented': 0, '43_register_trainer_artifact_augmented': 0, '44_enable_runtime_augmented': 0, '45_policy_training_status_augmented': 0, '46_workflow_execution_candidate_augmented': 0, '47_workflow_full_augmented': 0}`.
- Pre-Bayes gate: `pass_neutralized`.
- Ranker runtime status: `enabled_candidate_set_ready` ready `True`.
- Ranker rows raw/production/observation: `237/237/237`.
- Execution ready/actionable/review: `False` / `False` / `observe`.

## Layer Contract Gate
- Checked rows: `237`.
- Valid layer-contract rows: `237`.
- Rejected rows: `0`.
- Gate: `pass:layer_contract_schema_valid`.
- Failure reason carried by rows: `downstream_command_fail_closed:27_train_catboost,28_apply_catboost_history,29_apply_external_scores`.

## Decision
- `115700` now has an exact-root downstream readback with repaired/enriched row-level layer contract evidence.
- Promotion remains fail-closed because execution-tree readiness/actionability is still not proven and selected-history/source-control acceptance is still absent.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Artifacts
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/115700-enriched-downstream-chain-v1/115700_enriched_downstream_chain_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/checks/115700_enriched_downstream_chain_v1_assertions.out`
- Checklist: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/115700-enriched-downstream-chain-v1/prompt_to_artifact_checklist_115700_enriched_downstream_chain_v1.csv`
- Base downstream support report: `docs/experiments/actionable-regime-confidence/runs/20260512T121347+0800-codex-115700-enriched-downstream-chain-v1/115700-enriched-downstream-chain-v1/base-downstream-support/115700_six_provider_1h_downstream_chain_v1.md`
