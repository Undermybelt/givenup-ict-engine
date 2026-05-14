# Binance BTC Fullchain Provider AQ Downstream Fail-Closed v1

Run id: `20260512T151021+0800-codex-143900-binance-btc-fullchain-v1`
Source provider smoke: `docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1`
Source rows: `76429` from `docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/binance_btcusdt_1h_20170817_20260512.normalized.csv`

## Readback
- AQ metrics strategies: `['ProviderCryptoMomentumStateV1', 'ProviderCryptoPullbackRevertV1']`.
- Merged real-trade rows: `892` by `{'ProviderCryptoMomentumStateV1': 624, 'ProviderCryptoPullbackRevertV1': 268}`.
- Command exits: `{'00_provider_status': 0, '01_aq_compile': 0, '02_aq_run_tomac': 0, '03_ingest_real_trades': 0, '04_analyze': 124, '05_pre_bayes_status': 0, '06_policy_training_status_before_export': 0, '07_export_structural_path_target': 0, '08_policy_training_status_after_export': 0, '09_train_catboost': 1, '10_apply_catboost_scores': 1, '13_workflow_structural_bundle': 0, '14_workflow_execution_candidate': 0, '15_workflow_full': 0}`.
- Structural target rows: `3`.
- CatBoost artifact exists: `False`; scores exists: `False`.

## Provider Matrix
- Binance: requested=True acquired=True rows=76429 source=docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/binance_btcusdt_1h_20170817_20260512.normalized.csv
- IBKR: requested=True acquired=True rows=20034 source=docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/ibkr_spy_1h_5y.normalized.csv
- yfinance/YF: requested=True acquired=True rows=11383 source=docs/experiments/actionable-regime-confidence/runs/20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1/data/yahoo_es_1h_20240513_20260512.normalized.csv
- TradingViewRemix/TVR: requested=True acquired=False rows=0 source=20260512T141554 provider matrix
- Kraken: requested=True acquired=False rows=2000 source=20260512T141554 provider matrix
- Bybit: requested=True acquired=False rows=1000 source=20260512T141554 provider matrix

## Decision
- Gate: `binance_btc_fullchain_provider_aq_downstream_fail_closed_v1`.
- This is a provider-backed long-window AQ/downstream readback, not an accepted Board A regime packet.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.
