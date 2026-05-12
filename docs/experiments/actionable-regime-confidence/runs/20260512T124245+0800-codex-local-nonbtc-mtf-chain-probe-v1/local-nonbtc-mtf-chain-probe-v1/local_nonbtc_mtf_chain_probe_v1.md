# Local Non-BTC MTF Chain Probe v1

Run id: `20260512T124245+0800-codex-local-nonbtc-mtf-chain-probe-v1`

## Scope
- Source: local Auto-Quant feathers, no provider fetch.
- Panels: `ETH_USDT` crypto non-BTC `1h/4h/1d`; `SPY_USD` equity ETF `15m/4h/1d` with `1h` side context.
- Chain: feather -> cleaned JSON -> ict-engine analyze -> factor-research auto-quant handoff -> Pre-Bayes/BBN status -> path-ranker export/CatBoost attempt -> workflow/execution readback.

## Result
- `eth_usdt_crypto_nonbtc_1h_4h_1d`: exits `{'eth_usdt_crypto_nonbtc_1h_4h_1d_01_analyze': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_02_factor_research_auto_quant': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_03_pre_bayes_status': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_04_policy_training_status': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_05_export_structural_path_ranking_target': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_06_train_catboost': 0, 'eth_usdt_crypto_nonbtc_1h_4h_1d_07_workflow_status': 0}`, handoff data_ready `False`, target rows `3`, max confidence-like value `0.92`, accepted95 `False`.
- `spy_usd_equity_etf_15m_4h_1d`: exits `{'spy_usd_equity_etf_15m_4h_1d_01_analyze': 1, 'spy_usd_equity_etf_15m_4h_1d_02_factor_research_auto_quant': 0, 'spy_usd_equity_etf_15m_4h_1d_03_pre_bayes_status': 0, 'spy_usd_equity_etf_15m_4h_1d_04_policy_training_status': 0, 'spy_usd_equity_etf_15m_4h_1d_05_export_structural_path_ranking_target': 0, 'spy_usd_equity_etf_15m_4h_1d_06_train_catboost': 1, 'spy_usd_equity_etf_15m_4h_1d_07_workflow_status': 0}`, handoff data_ready `False`, target rows `1`, max confidence-like value `None`, accepted95 `False`.

## Decision
- Gate: `local_nonbtc_mtf_chain_probe_v1=nonbtc_mtf_chain_exercised_no_95_confidence_no_promotion`.
- This is non-BTC / non-1h coverage evidence only.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
