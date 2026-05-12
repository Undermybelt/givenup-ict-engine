# Board B 220646 Downstream Readback v2

- Decision: `not_promoted:downstream_branch_path_or_bbn_mapping_gap`
- Source run: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1`
- Provider status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`
- Branch RC-SPA: `pass`, price roots `4/4`, Manipulation component `True`
- Branch paths preserved in source/downstream artifacts: `true`
- BBN roots applied: `Bull,Sideways,Crisis`; skipped unsupported: `Bear`
- CatBoost/path-ranker: model family `catboost_unavailable_fallback`, exact Board B structural target rows `0`
- Execution tree readback: execution blocked observed `false`
- Primary blocker: `bbn_soft_evidence_unsupported_roots=Bear;ict_engine_structural_path_ranker_target_has_no_exact_board_b_branch_path_rows`

## Provider Readback

- yfinance: `[{'provider_id': 'yfinance', 'domain': 'live_runtime', 'selectable_by_user': True, 'adopted_by_default': True, 'ready': True, 'access_mode': 'local_library', 'user_access': 'free_no_login', 'market_fit': ['tradfi'], 'fallback_priority': 1, 'status': 'ready', 'reason': 'native_yfinance_runtime_available', 'summary': 'Zero-config live runtime backed by yfinance-compatible fetches for observation and replay-adjacent workflows.'}, {'provider_id': 'yfinance', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': True, 'access_mode': 'public_or_env_ready', 'user_access': 'free_no_login', 'market_fit': ['tradfi'], 'fallback_priority': 1, 'status': 'ready', 'reason': 'public_yahoo_http_endpoints', 'summary': 'Free historical tradfi fallback for replay, factor research, and factor backtests.'}]`
- TradingView MCP: `[{'provider_id': 'tradingview_mcp', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': False, 'access_mode': 'operator_runtime_required', 'user_access': 'local_stdio_or_remote_api_key', 'market_fit': ['tradfi', 'crypto'], 'fallback_priority': 31, 'status': 'configured_runtime_unhealthy', 'reason': 'tradingview_mcp_connectivity_probe_failed', 'summary': 'Hot-pluggable TradingView MCP path: zero-config local stdio for OHLCV, optional remote key for enriched lanes.', 'install_prompts': ['Consumer agent request: TradingViewRemix MCP credentials were present but the live probe failed. Ask the user to re-enter ICT_ENGINE_TVREMIX_MCP_API_KEY and verify the MCP endpoint at https://tvremix.xyz/api/mcp/v1.', 'Consumer agent follow-up: retry a lightweight MCP health check such as tools/list before treating TradingViewRemix as usable.']}]`
- IBKR: `[{'provider_id': 'ibkr', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': False, 'access_mode': 'operator_runtime_required', 'user_access': 'login_and_local_runtime', 'market_fit': ['tradfi'], 'fallback_priority': 30, 'status': 'configured_runtime_unhealthy', 'reason': 'ibkr_runtime_dependencies_missing_with_gateway_reachable', 'summary': 'Setup-required IBKR market-data path for broker-linked futures and equities workflows.', 'install_prompts': ['Consumer agent follow-up: make sure the runtime that executes provider-status and provider fetches can import redis and ib_async. Low-pollution path: use uv run --with redis --with ib_async --with pandas for ad-hoc IBKR historical fetches.', 'Consumer agent follow-up: reuse the single reachable local IBKR API on port 4002 unless the user says otherwise.']}]`
- IBKR bridge: `[{'provider_id': 'ibkr_bridge', 'domain': 'local_runtime', 'selectable_by_user': False, 'adopted_by_default': False, 'ready': False, 'access_mode': 'local_consent_runtime', 'user_access': 'login_and_local_runtime', 'market_fit': ['tradfi'], 'fallback_priority': 40, 'status': 'configured_runtime_unhealthy', 'reason': 'ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable', 'summary': 'Local IBKR bridge reused by broker-linked workflows after the user enables the local API.', 'install_prompts': ['Make sure the runtime that executes provider-status and provider fetches can import redis and ib_async.', 'A local IBKR API is reachable on port 4002; reuse it unless the user says otherwise.']}]`
- Kraken CLI: `[{'provider_id': 'kraken_cli', 'domain': 'local_runtime', 'selectable_by_user': False, 'adopted_by_default': False, 'ready': True, 'access_mode': 'local_cli_runtime', 'user_access': 'login_and_local_runtime', 'market_fit': ['crypto'], 'fallback_priority': 40, 'status': 'ready', 'reason': 'kraken_cli_config_detected', 'summary': 'Credentialed local Kraken CLI/runtime path for wallet or execution-adjacent flows.'}]`
- Kraken public: `[{'provider_id': 'kraken_public', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': False, 'access_mode': 'public_script_adapter', 'user_access': 'public_no_login', 'market_fit': ['crypto', 'fx', 'tokenized_assets'], 'fallback_priority': 3, 'status': 'configured_runtime_unhealthy', 'reason': 'python3_provider_dependencies_missing', 'summary': 'Public no-login crypto, forex, and tokenized-asset data path; later wallet/runtime flows use kraken_cli separately.', 'install_prompts': ['System python3 is missing provider script modules: ccxt, ib_async, redis, sklearn, pyarrow, xgboost. Install with: python3 -m pip install --user --break-system-packages ccxt ib_async redis scikit-learn pyarrow xgboost']}]`

## Branch Paths

- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

## Next

Fix the downstream adapter boundary: Bear root BBN soft evidence is unsupported, and structural path-ranker/execution-tree targets still expose generic structural paths instead of exact Board B rooted branch paths; then rerun B5 for 220646.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T222350-codex-board-b-220646-downstream-readback-v2/downstream-readback/board_b_220646_downstream_readback_v2.json`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T222350-codex-board-b-220646-downstream-readback-v2/command-output`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T222350-codex-board-b-220646-downstream-readback-v2/checks/board_b_220646_downstream_readback_v2_assertions.out`
