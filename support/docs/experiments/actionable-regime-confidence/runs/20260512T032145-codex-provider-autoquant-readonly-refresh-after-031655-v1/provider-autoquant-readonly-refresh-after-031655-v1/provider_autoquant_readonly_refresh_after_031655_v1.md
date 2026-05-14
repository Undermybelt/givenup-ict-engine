# Provider Auto-Quant Readonly Refresh After 031655 v1

Run id: `20260512T032145-codex-provider-autoquant-readonly-refresh-after-031655-v1`

Gate result: `provider_autoquant_readonly_refresh_after_031655_v1=runtime_readiness_refreshed_no_source_control_unlock_no_promotion`

## Commands

- provider-status exit: `0`
- auto-quant-status exit: `0`
- pre-bayes-status exit: `0`
- workflow-status exit: `0`

## Provider Readiness

- Summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- yfinance market data: `ready` / `public_yahoo_http_endpoints`
- yfinance live runtime: `ready` / `native_yfinance_runtime_available`
- IBKR market data: `configured_runtime_unhealthy` / `ibkr_runtime_dependencies_missing_with_gateway_reachable`
- IBKR bridge: `configured_runtime_unhealthy` / `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`
- Kraken CLI: `ready` / `kraken_cli_config_detected`
- Kraken public market data: `configured_runtime_unhealthy` / `python3_provider_dependencies_missing`
- TradingView MCP / Remix: `configured_runtime_unhealthy` / `tradingview_mcp_connectivity_probe_failed`

## Runtime Chain Readiness

- Auto-Quant status: `missing_dependency`; healthy `False`; bootstrap needed `True`; data ready `False`.
- Pre-Bayes latest policy version: `None`; latest gate status `None`.
- Workflow blocking status: `insufficient_state` / `no workflow phase snapshots available`.
- Workflow branch admission: `fail_closed`; actionable `False`.

## Decision

This is readiness evidence only. It does not unlock Board A because R6 owner-export, R3 native-subhour source-label, and R5 recency-extension roots remain absent. No canonical merge or downstream promotion rerun is allowed from this packet.

Accepted rows added `0`; new confidence gate `false`; canonical merge `false`; downstream rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.
