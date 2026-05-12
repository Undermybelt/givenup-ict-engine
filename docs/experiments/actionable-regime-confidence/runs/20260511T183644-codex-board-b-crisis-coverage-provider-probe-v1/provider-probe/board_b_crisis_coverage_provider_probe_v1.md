# Board B Crisis Coverage Provider Probe v1

Run ID: `20260511T183644+0800-codex-board-b-crisis-coverage-provider-probe-v1`

## Decision

- Gate result: `provider_probe_only_source_label_gap_remains`.
- Source-label coverage added: `0`.
- This probe refreshes provider readiness only; it does not solve the Crisis root support gap or authorize downstream branch promotion.

## Provider Readiness

| Provider | Ready | Status | Reason |
|---|---:|---|---|
| `yfinance` | `True` | `ready` | `native_yfinance_runtime_available` |
| `tradingview_mcp` | `True` | `ready` | `mcp_url_and_api_key_available` |
| `kraken_cli` | `True` | `ready` | `kraken_cli_config_detected` |
| `kraken_public` | `False` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `ibkr` | `False` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |

## Next

Acquire source-owned crisis-capable labels or an owner-approved broader label/equivalence panel before another root-aware profitability recipe claim.
