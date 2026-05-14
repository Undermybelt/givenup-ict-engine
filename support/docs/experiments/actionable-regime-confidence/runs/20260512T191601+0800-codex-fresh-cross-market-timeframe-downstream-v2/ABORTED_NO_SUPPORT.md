# Aborted No Support

This root is not Board A support.

The fresh `191601` run was stopped after a duplicate continuation process reran the same state root and produced duplicate-state failures in the first yfinance window:

- `01_yfinance_w1_auto_quant_prior_init.exit=1`
- `01_yfinance_w1_auto_quant_ingest_real_trades.exit=1`

The root did not produce a terminal summary, aggregate CatBoost/path-ranker readback, independent cross-market/timeframe acceptance, execution-tree admission, or per-regime calibrated `>=95%` evidence.

Gate:
- `aborted_no_support:191601_fresh_cross_market_timeframe_downstream_v2`
- `no_support_count:191601`
- `accepted_95_contexts_added_0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
