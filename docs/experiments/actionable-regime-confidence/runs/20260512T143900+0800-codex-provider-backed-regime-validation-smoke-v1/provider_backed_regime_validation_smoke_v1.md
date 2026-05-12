# Provider-Backed Regime Validation Smoke v1

Run id: `20260512T143900+0800-codex-provider-backed-regime-validation-smoke-v1`

Purpose: verify that provider-backed normalized OHLCV data can be consumed by `ict-engine validate-market-state` before using the same provider lanes for Board B profitability-factor work.

This is a support-only regime-validation smoke. It is not an Auto-Quant profitability factor packet, does not run Pre-Bayes/BBN/CatBoost/execution-tree admission, does not mutate production state, does not promote a candidate, and does not call `update_goal`.

## Inputs

- Binance `BTCUSDT` 1h full listing: `data/binance_btcusdt_1h_20170817_20260512.normalized.csv`
- IBKR `SPY` 1h 5Y: `data/ibkr_spy_1h_5y.normalized.csv`
- Yahoo/YF `ES=F` 1h 2Y: `data/yahoo_es_1h_20240513_20260512.normalized.csv`
- Hashes: `data_sha256.txt`

## Commands

- `01_validate_binance_btc_1h`: `ict-engine validate-market-state --data ... --window-size 500 --step-size 500 --profile high_confidence --compact`
- `02_validate_ibkr_spy_1h`: `ict-engine validate-market-state --data ... --window-size 500 --step-size 250 --profile high_confidence --compact`
- `03_validate_yahoo_es_1h`: `ict-engine validate-market-state --data ... --window-size 500 --step-size 250 --profile high_confidence --compact`

## Results

- Binance BTCUSDT 1h exited `0`: `samples=153`, `avg_confidence=76.68%`, `high_confidence=55.56%`, `tradeable=100.00%`, `primary_top=TrendExpansion:76`, `secondary_top=WideRange:41`.
- IBKR SPY 1h exited `0`: `samples=80`, `avg_confidence=75.19%`, `high_confidence=50.00%`, `tradeable=100.00%`, `primary_top=RangeConsolidation:40`, `secondary_top=WideRange:27`.
- Yahoo/YF ES 1h exited `0`: `samples=45`, `avg_confidence=79.17%`, `high_confidence=68.89%`, `tradeable=100.00%`, `primary_top=TrendExpansion:27`, `secondary_top=BullTrendAcceleration:16`.

## Gate

- `support_once:143900_provider_backed_regime_validation_smoke_v1`
- `evidence_class:provider_backed_regime_validation_smoke_not_profitability_packet`
- `pass:binance_btcusdt_1h_validate_market_state_exit0`
- `pass:ibkr_spy_1h_validate_market_state_exit0`
- `pass:yahoo_es_1h_validate_market_state_exit0`
- `partial:provider_backed_data_consumable_by_validate_market_state`
- `fail_closed:not_auto_quant_profitability_factor_packet`
- `fail_closed:no_real_trade_outcome_rows`
- `fail_closed:no_pre_bayes_bbn_catboost_execution_tree_chain`
- `fail_closed:missing_tradingviewremix_tvr_for_this_smoke`
- `fail_closed:missing_kraken_for_this_smoke`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Use this only as provider-backed data-consumption support. The next Board B continuation must produce or select a profitability-factor packet with branch-path fields, explicit provider provenance, and ordered Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree readback.
