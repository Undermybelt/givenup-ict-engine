# Read-only Runtime Surface Refresh After 012425 v1

- Decision: `readonly_runtime_surface_refresh_after_012425_v1=readiness_refreshed_no_promotion_source_control_blocked`.
- Current cursor observed: `20260512T010127+0800-codex-r6-owner-route-entitlement-readback-v1`.
- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant status: `missing_dependency`; healthy `false`; next command `ict-engine auto-quant-bootstrap --state-dir /tmp/ict-engine-board-a-readonly-runtime-20260512T013050/auto-quant`.
- Pre-Bayes ready: `false`.
- Policy training ready: `false`; matched rows `0`.
- Structural path ranking export ready: `false`; runtime ready `false`.
- Workflow path: `bootstrap_readiness`; stop `No trade until preconditions are satisfied.`.
- Downstream chain rerun allowed: `false`; strict full objective achieved: `false`; `update_goal=false`.

## Provider Readiness

| Provider | Ready | Status | Reason |
|---|---|---|---|
| `yfinance` | `true` | `ready` | `public_yahoo_http_endpoints` |
| `ibkr` | `false` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `ibkr_bridge` | `false` | `configured_runtime_unhealthy` | `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable` |
| `kraken_cli` | `true` | `ready` | `kraken_cli_config_detected` |
| `kraken_public` | `false` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `tradingview_mcp` | `false` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |

## Boundary

This packet summarizes existing read-only command outputs only. It does not bootstrap Auto-Quant, fetch provider data, train BBN/CatBoost, export a structural target, mutate intake roots, or authorize provider/Auto-Quant/filter/Pre-Bayes/BBN/CatBoost/path-ranking/execution-tree promotion.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T013050-codex-readonly-runtime-surface-refresh-after-012425-v1/readonly-runtime-surface-refresh-after-012425-v1/readonly_runtime_surface_refresh_after_012425_v1.json`
- Provider CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T013050-codex-readonly-runtime-surface-refresh-after-012425-v1/readonly-runtime-surface-refresh-after-012425-v1/provider_readiness_after_012425_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T013050-codex-readonly-runtime-surface-refresh-after-012425-v1/checks/readonly_runtime_surface_refresh_after_012425_v1_assertions.out`
