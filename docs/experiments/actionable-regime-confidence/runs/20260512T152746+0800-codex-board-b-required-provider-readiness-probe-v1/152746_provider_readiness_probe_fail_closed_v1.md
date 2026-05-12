# 152746 Provider Readiness Probe Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T152746+0800-codex-board-b-required-provider-readiness-probe-v1/`

## Scope

This is a lightweight `provider-status --agent` readiness probe. It is not provider acquisition, not Auto-Quant evidence, and not Board A acceptance.

## Evidence

All provider-status commands exited `0`:

- `00_provider_status_market_data_agent.exit=0`
- `01_provider_status_ibkr_agent.exit=0`
- `02_provider_status_tradingview_mcp_agent.exit=0`
- `03_provider_status_yfinance_agent.exit=0`
- `04_provider_status_kraken_public_agent.exit=0`
- `05_provider_status_binance_public_agent.exit=0`
- `06_provider_status_bybit_public_agent.exit=0`

## Results

The aggregate market-data readback reported `market_data:1/7 ready`.

Ready:

- `yfinance`: `ready`, reason `public_yahoo_http_endpoints`

Fail-closed / pending:

- `ibkr`: `configured_runtime_unhealthy`, reason `ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `tradingview_mcp`: `configured_runtime_unhealthy`, reason `tradingview_mcp_connectivity_probe_failed`
- `kraken_public`: `configured_runtime_unhealthy`, reason `python3_provider_dependencies_missing`
- `binance_public`: `configured_runtime_unhealthy`, reason `python3_provider_dependencies_missing`
- `bybit_public`: `configured_runtime_unhealthy`, reason `python3_provider_dependencies_missing`
- aggregate market-data surface: only `1/7` ready under the probed runtime

The commands succeeded as status readbacks, but the status content blocks provider-authority claims for this runtime.

## Gate

- `support_once:152746_provider_readiness_probe_v1`
- `evidence_class:provider_status_readback_not_acceptance`
- `pass:provider_status_commands_exit0`
- `partial:yfinance_ready`
- `fail_closed:market_data_ready_1_of_7`
- `fail_closed:ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `fail_closed:tradingview_mcp_connectivity_probe_failed`
- `fail_closed:kraken_public_python3_provider_dependencies_missing`
- `fail_closed:binance_public_python3_provider_dependencies_missing`
- `fail_closed:bybit_public_python3_provider_dependencies_missing`
- `fail_closed:no_provider_data_acquisition`
- `fail_closed:no_auto_quant_pre_bayes_bbn_catboost_execution_tree_chain`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`

## Next

Do not treat this root as provider evidence for Board A. Use it only as current readiness feedback; the next valid provider packet must acquire data and carry candidates through Auto-Quant -> filter/Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution tree.
