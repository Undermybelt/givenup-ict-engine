# Provider Runtime Source-label Readback v1

Decision: `provider_runtime_source_label_readback_v1=providers_checked_no_source_owned_labels_acquired`.

Result:
- Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- Wanted provider states: `{"ibkr": "configured_runtime_unhealthy:ibkr_runtime_dependencies_missing_with_gateway_reachable", "kraken_cli": "ready:kraken_cli_config_detected", "kraken_public": "configured_runtime_unhealthy:python3_provider_dependencies_missing", "tradingview_mcp": "configured_runtime_unhealthy:tradingview_mcp_connectivity_probe_failed", "yfinance": "ready:public_yahoo_http_endpoints"}`.
- TradingViewRemix status: `configured_runtime_unhealthy`; reason `tradingview_mcp_connectivity_probe_failed`.
- Auto-Quant status: `missing_dependency`; healthy `False`.
- yfinance rows: `88`; source-label-ready: `false`.
- Kraken rows: `721`; source-label-ready: `false`.
- IBKR fetch returncode: `0`; rows: `5`; source-label-ready: `false`.
- Ready intake roots added: `0`.
- Accepted rows added: `0`; new confidence gate: `false`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; trade usable: `false`.

Interpretation:
- yfinance/Kraken/IBKR provider fetches produce or attempted raw OHLCV market panels, not source-owned MainRegimeV2 label rows with provenance.
- TradingViewRemix remains blocked by MCP connectivity, and Auto-Quant is missing its managed dependency in this isolated run state.
- These checks therefore cannot populate `/tmp/ict-engine-source-label-equivalence-intake`, `/tmp/ict-engine-native-subhour-source-label-intake`, `/tmp/ict-engine-source-panel-recency-extension`, or `/tmp/ict-engine-direct-manipulation-row-intake`.

Artifacts:
- JSON: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205533-codex-provider-runtime-source-label-readback-v1/provider-runtime-source-label-readback/provider_runtime_source_label_readback_v1.json`
- Fetch profiles: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205533-codex-provider-runtime-source-label-readback-v1/provider-runtime-source-label-readback/provider_runtime_source_label_fetch_profiles_v1.csv`
- Assertions: `/Users/thrill3r/projects-ict-engine/ict-engine/docs/experiments/actionable-regime-confidence/runs/20260511T205533-codex-provider-runtime-source-label-readback-v1/checks/provider_runtime_source_label_readback_v1_assertions.out`
