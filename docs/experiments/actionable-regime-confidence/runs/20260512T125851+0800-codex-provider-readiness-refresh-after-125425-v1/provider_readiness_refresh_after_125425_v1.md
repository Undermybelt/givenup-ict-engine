# Provider Readiness Refresh After 125425 v1

Run id: `20260512T125851+0800-codex-provider-readiness-refresh-after-125425-v1`

## Scope

Read-only provider-status refresh after the `125425` ETH path-ranker runtime closure. This artifact records current provider/readiness gates only; it is not market/factor evidence and does not fetch new candles.

## Commands

All commands exited `0`:

- `provider-status --agent`
- `provider-status --provider yfinance --compact`
- `provider-status --provider ibkr --compact`
- `provider-status --provider tradingview_mcp --compact`
- `provider-status --provider kraken_public --compact`
- `provider-status --provider kraken_cli --compact`
- `provider-status --provider binance_public --compact`
- `provider-status --provider bybit_public --compact`

## Readback

- Overall: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `yfinance`: ready as live/runtime and market-data path.
- `ibkr`: market-data pending, `configured_runtime_unhealthy:ibkr_runtime_dependencies_missing_with_gateway_reachable`; local IBKR API is reachable on port `4002`, but the runtime still needs `redis` and `ib_async`.
- `tradingview_mcp`: market-data pending, `configured_runtime_unhealthy:tradingview_mcp_connectivity_probe_failed`; TVRemix credentials/endpoint health need refresh before treating it as usable.
- `kraken_public`: market-data pending because system Python is missing provider modules including `ccxt`, `ib_async`, `redis`, `sklearn`, `pyarrow`, and `xgboost`.
- `kraken_cli`: local runtime ready, but this is not the public market-data provider row.
- `binance_public` and `bybit_public`: market-data pending with the same Python provider dependency gap as `kraken_public`.

## Gate

- `evidence_class=infrastructure_negative_sample`.
- `quality_weight=0.0_for_market_factor_learning`.
- `pass:yfinance_ready`.
- `pass:kraken_cli_local_runtime_ready`.
- `fail_closed:ibkr_market_data_dependency_unhealthy_gateway_reachable`.
- `fail_closed:tradingview_mcp_connectivity_probe_failed`.
- `fail_closed:kraken_public_python_provider_dependencies_missing`.
- `fail_closed:binance_public_python_provider_dependencies_missing`.
- `fail_closed:bybit_public_python_provider_dependencies_missing`.
- `fail_closed:provider_matrix_not_data_acquisition`.

## Decision

This provider refresh explains why local-cache and selected-history results cannot be upgraded into provider-authoritative profitability evidence. Provider failures here may update provider reliability, evidence quality, data authority, workflow readiness, and human-next prompts. They must not update BBN market likelihood, regime-conditioned win rate, CatBoost production labels, or execution-tree branch weights as if a market/factor branch failed.
