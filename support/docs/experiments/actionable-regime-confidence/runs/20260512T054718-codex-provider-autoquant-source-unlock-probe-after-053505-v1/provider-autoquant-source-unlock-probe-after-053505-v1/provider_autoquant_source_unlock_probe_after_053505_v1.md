# Provider Auto-Quant Source Unlock Probe After 053505 v1

Run id: `20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1`

Gate result: `provider_autoquant_source_unlock_probe_after_053505_v1=provider_surfaces_refreshed_no_source_root_unlock_no_promotion`

## Scope

Read-only refresh of the user-named provider surfaces and local Auto-Quant state after the `053505` R5 Kaggle recency screen. Raw provider bars, if fetched, stay under `/tmp`; this artifact records only row counts and hashes.

## Provider / Auto-Quant Readback

- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Auto-Quant status: `dependency_ready_seed_required`; healthy `true`; data_ready `true`; next blocker `auto_quant_seed_strategies_required`.

Selected provider states:

| Provider | Ready | Status | Reason |
|---|---:|---|---|
| `ibkr@market_data` | `False` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `ibkr_bridge@local_runtime` | `False` | `configured_runtime_unhealthy` | `ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable` |
| `kraken_cli@local_runtime` | `True` | `ready` | `kraken_cli_config_detected` |
| `kraken_public@market_data` | `False` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `tradingview_mcp@market_data` | `False` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance@live_runtime` | `True` | `ready` | `native_yfinance_runtime_available` |
| `yfinance@market_data` | `True` | `ready` | `public_yahoo_http_endpoints` |

Provider bar probes:

| Output | Rows | SHA-256 |
|---|---:|---|
| `/tmp/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/provider-bars/AAPL_ibkr_1h_2w.csv` | `158` | `56c2c12f6cc9ac22e15262aec2f7dc72d72b85dde5fdb9109371fe8fe9aa17ec` |
| `/tmp/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/provider-bars/PF_XBTUSD_kraken_futures_1h_20260131_20260510.csv` | `2000` | `4ce6974a63eda68f268f81e6e56e2f6933f0d160a15d5d1933c5d466bc24880d` |
| `/tmp/20260512T054718-codex-provider-autoquant-source-unlock-probe-after-053505-v1/provider-bars/QQQ_yfinance_1h_20260131_20260510.csv` | `473` | `f85640f440e27b7aae8af9ffaf39816643e52027d1a44c1571aa4b0a4ecefad2` |

## Decision

- Provider surfaces were refreshed, but no source/control target root was unlocked.
- Provider bars are not source-owned `MainRegimeV2` labels, not R6 matched normal controls, and not native sub-hour source-label rows.
- Target root mutated: `false`.
- Accepted rows added `0`; source/control evidence acquired `false`; canonical merge `false`; downstream promotion rerun `false`; strict full objective `false`; trade usable `false`; `update_goal=false`.

## Next

Do not promote from provider bars. Continue only after explicit source/control approval, verifier-native R6 owner/export rows with normal controls, source-owned R5 recency rows, or source-owned R3 native subhour labels unlock a target root.
