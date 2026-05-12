# Live Provider Intake Recheck v37

Decision: `live_provider_intake_recheck_v37=providers_rechecked_r6_schema_ready_remaining_intakes_blocked`.

Result:
- Provider/status paths rechecked: `IBKR`, `TradingViewRemix/MCP`, `yfinance`, `Kraken`, and local Auto-Quant.
- Ready intake roots: `1/4`.
- Kraken public low-pollution fetch rows: `721`.
- IBKR low-pollution fetch rows: `21`; return code `0`.
- Auto-Quant local feather files: `40`; strategy files found: `1`.
- Direct Manipulation verifier status: `schema_ready_unscored`; schema-ready rows do not pass Wilson95/heldout calibration.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.

Provider readback:
- `yfinance`: ready=`True`, status=`ready`, reason=`native_yfinance_runtime_available`.
- `tradingview_mcp`: ready=`True`, status=`ready`, reason=`mcp_url_and_api_key_available`.
- `ibkr`: ready=`False`, status=`configured_runtime_unhealthy`, reason=`ibkr_runtime_dependencies_missing_with_gateway_reachable`.
- `kraken_public`: ready=`False`, status=`configured_runtime_unhealthy`, reason=`python3_provider_dependencies_missing`.
- `kraken_cli`: ready=`True`, status=`ready`, reason=`kraken_cli_config_detected`.
- `ibkr_bridge`: ready=`False`, status=`configured_runtime_unhealthy`, reason=`ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`.

Blocked intake roots:
- `/tmp/ict-engine-source-label-equivalence-intake`
- `/tmp/ict-engine-native-subhour-source-label-intake`
- `/tmp/ict-engine-source-panel-recency-extension`
- `/tmp/ict-engine-direct-manipulation-row-intake` is schema-ready only and remains calibration-blocked.

Next:
- Populate the exact source-owned or owner-approved intake files, then rerun these verifiers before another completion audit.
