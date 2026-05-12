# BTC Binance Full Provider AQ Chain Bounded-2Y Continuation v1

Run id: `20260512T150515+0800-codex-btc-binance-full-provider-aq-chain-v1`

## Readback

- Full-listing `ict-engine analyze` timed out after `900` seconds and is recorded as `04_analyze_binance_full.exit=124`.
- Auto-Quant full-listing Momentum metrics: trades `2758`, profit_pct `-89.97`, win_rate_pct `26.68600435097897`, profit_factor `0.6725106376079354`.
- Auto-Quant full-listing Pullback metrics: trades `1353`, profit_pct `-74.31`, win_rate_pct `39.689578713968956`, profit_factor `0.6077654391592684`.
- Selected Momentum wire rows ingested for downstream: `2758`.
- Bounded 2Y command exits: `{'04b_analyze_binance_2y': 124, '05b_pre_bayes_status': 0, '06b_policy_training_status_before_export': 0, '07b_export_structural_path_ranking_target': 0, '08b_policy_training_status_after_export': 0, '09b_train_catboost_path_ranker': 0, '11b_register_trainer_artifact': 0, '12b_enable_runtime': 0, '13b_policy_training_status_after_ranker': 0, '14b_workflow_structural_bundle': 0, '15b_workflow_execution_candidate': 0, '16b_workflow_full': 0}`.
- Structural target rows `2`, history rows `2760`, CatBoost artifact exists `True`, scores exist `False`.
- Execution ready `False`, actionable `False`.

## Gate

- `support_once:150515_btc_binance_full_provider_aq_chain_v1`.
- `evidence_class:provider_backed_profitability_chain_negative_sample`.
- `fail_closed:full_listing_analyze_timeout_900s`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
