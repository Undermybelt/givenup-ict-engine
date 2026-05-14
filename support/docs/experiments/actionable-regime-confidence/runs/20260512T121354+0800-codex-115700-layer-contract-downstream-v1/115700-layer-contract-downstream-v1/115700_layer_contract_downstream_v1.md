# 115700 Layer Contract Downstream v1

Run id: `20260512T121354+0800-codex-115700-layer-contract-downstream-v1`
Source root: `20260512T115700+0800-codex-same-root-six-provider-1h-aq-v1`

## Result
- Enriched rows: `237`.
- Contract-complete rows: `237`.
- Market/factor trainable rows: `0`.
- Gate: `fail_closed:schema_complete_but_no_trainable_market_factor_rows`.
- Promotion allowed: `False`.

## Ordered Chain Exits
- `20_auto_quant_results_import`: `0`
- `21_auto_quant_prior_init`: `0`
- `22_ingest_real_trades`: `0`
- `23_analyze_provider_data`: `0`
- `24_pre_bayes_status`: `0`
- `25_policy_training_status_before_export`: `0`
- `26_export_structural_path_ranking_target`: `0`
- `27_train_catboost`: `1`
- `28_apply_catboost_history`: `1`
- `29_apply_external_scores`: `1`
- `30_register_trainer_artifact`: `0`
- `31_enable_runtime`: `0`
- `32_policy_training_status_final`: `0`
- `33_workflow_execution_candidate`: `0`
- `34_workflow_full`: `0`

## Provider Row Counts
- `binance_public`: `52`
- `bybit_public`: `51`
- `ibkr_paxos_long_midpoint`: `44`
- `kraken_public`: `32`
- `tvr_default_binance`: `37`
- `yfinance`: `21`

## Artifacts
- Pre-chain enriched JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/derived/115700_prechain_layer_contract_real_trades.jsonl`
- Final enriched JSONL: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/derived/115700_postchain_layer_contract_real_trades.jsonl`
- Strategy library: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/derived/strategy_library_115700_layer_contract_v1.json`
- Provider JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/provider-data-json`
- State dir: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/state_115700_layer_contract_downstream_v1`
- Command output: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/command-output`
- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/115700-layer-contract-downstream-v1/115700_layer_contract_downstream_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T121354+0800-codex-115700-layer-contract-downstream-v1/checks/115700_layer_contract_downstream_v1_assertions.out`
