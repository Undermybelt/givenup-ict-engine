# Board B 220646 Post-Adapter Downstream Readback v1

- Decision: `not_promoted:post_adapter_downstream_rerun_failed`.
- Source: `docs/experiments/actionable-regime-confidence/runs/20260511T220646-codex-board-b-source-root-stop-carry-longhorizon-v1`.
- State dir: `/tmp/ict-engine-board-b-220646-post-adapter-downstream-v1-20260511T224522`.
- Branch RC-SPA: `pass`, stable score `85.7407`, price roots `4/4`, Manipulation component `pass`.
- Exact branch target rows before scores: `{'Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12': 1, 'Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12': 1, 'Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12': 1, 'Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12': 1}`.
- Score rows written/applied: `4` / `True`.
- Rows with raw path score after apply: `4`.
- Bear BBN applied: `False`; skipped unsupported: `False`.
- Policy validation: `Ranker validation: calibration=true quality_ready=true raw_scored_mature=7/30 production_validation=7/30 observation_validation=4/30 ready=false`.
- Runtime candidate-set summary: `Ranker runtime: structural_path_ranking_target rows=4 history_rows=16 mature_rows=4 history_mature_rows=13 raw_scored_mature=7/30 production_validation=7/30 observation_validation=4/30 calibration=evaluated trainer_artifact=ready trainer_status=present_validation_insufficient runtime_selection=enabled_candidate_set_ready runtime_mode=candidate_set_only runtime_source=candidate_set score_model_family=unknown score_source=unknown runtime_matches=3`.
- Runtime prefer-history summary: `Ranker runtime: structural_path_ranking_target rows=4 history_rows=16 mature_rows=4 history_mature_rows=13 raw_scored_mature=7/30 production_validation=7/30 observation_validation=4/30 calibration=evaluated trainer_artifact=ready trainer_status=present_validation_insufficient runtime_selection=enabled_candidate_set_ready runtime_mode=prefer_history runtime_source=candidate_set score_model_family=unknown score_source=unknown runtime_matches=3`.
- Workflow branch path observed: `True`; execution-candidate branch path observed: `False`.
- Execution candidate status: `None`; actionable: `None`.
- Provider status: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`.

## Branch Paths

- `Bull -> RootCarryExpansion -> StopManagedRiskCarry -> SourceRootStopCarryLongHorizonV1:bull_carry_h12_sl040_tp12`
- `Bear -> BearReliefCarry -> StopManagedRecoveryCarry -> SourceRootStopCarryLongHorizonV1:bear_carry_h20_sl048_tp12`
- `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

## Provider Readback

- yfinance: `[{'provider_id': 'yfinance', 'domain': 'live_runtime', 'selectable_by_user': True, 'adopted_by_default': True, 'ready': True, 'access_mode': 'local_library', 'user_access': 'free_no_login', 'market_fit': ['tradfi'], 'fallback_priority': 1, 'status': 'ready', 'reason': 'native_yfinance_runtime_available', 'summary': 'Zero-config live runtime backed by yfinance-compatible fetches for observation and replay-adjacent workflows.'}, {'provider_id': 'yfinance', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': True, 'access_mode': 'public_or_env_ready', 'user_access': 'free_no_login', 'market_fit': ['tradfi'], 'fallback_priority': 1, 'status': 'ready', 'reason': 'public_yahoo_http_endpoints', 'summary': 'Free historical tradfi fallback for replay, factor research, and factor backtests.'}]`
- TradingView MCP: `[{'provider_id': 'tradingview_mcp', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': True, 'access_mode': 'public_or_env_ready', 'user_access': 'local_stdio_or_remote_api_key', 'market_fit': ['tradfi', 'crypto'], 'fallback_priority': 31, 'status': 'ready', 'reason': 'mcp_url_and_api_key_available', 'summary': 'Hot-pluggable TradingView MCP path: zero-config local stdio for OHLCV, optional remote key for enriched lanes.'}]`
- IBKR: `[{'provider_id': 'ibkr', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': False, 'access_mode': 'operator_runtime_required', 'user_access': 'login_and_local_runtime', 'market_fit': ['tradfi'], 'fallback_priority': 30, 'status': 'configured_runtime_unhealthy', 'reason': 'ibkr_runtime_dependencies_missing_with_gateway_reachable', 'summary': 'Setup-required IBKR market-data path for broker-linked futures and equities workflows.', 'install_prompts': ['Consumer agent follow-up: make sure the runtime that executes provider-status and provider fetches can import redis and ib_async. Low-pollution path: use uv run --with redis --with ib_async --with pandas for ad-hoc IBKR historical fetches.', 'Consumer agent follow-up: reuse the single reachable local IBKR API on port 4002 unless the user says otherwise.']}]`
- IBKR bridge: `[{'provider_id': 'ibkr_bridge', 'domain': 'local_runtime', 'selectable_by_user': False, 'adopted_by_default': False, 'ready': False, 'access_mode': 'local_consent_runtime', 'user_access': 'login_and_local_runtime', 'market_fit': ['tradfi'], 'fallback_priority': 40, 'status': 'configured_runtime_unhealthy', 'reason': 'ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable', 'summary': 'Local IBKR bridge reused by broker-linked workflows after the user enables the local API.', 'install_prompts': ['Make sure the runtime that executes provider-status and provider fetches can import redis and ib_async.', 'A local IBKR API is reachable on port 4002; reuse it unless the user says otherwise.']}]`
- Kraken CLI: `[{'provider_id': 'kraken_cli', 'domain': 'local_runtime', 'selectable_by_user': False, 'adopted_by_default': False, 'ready': True, 'access_mode': 'local_cli_runtime', 'user_access': 'login_and_local_runtime', 'market_fit': ['crypto'], 'fallback_priority': 40, 'status': 'ready', 'reason': 'kraken_cli_config_detected', 'summary': 'Credentialed local Kraken CLI/runtime path for wallet or execution-adjacent flows.'}]`
- Kraken public: `[{'provider_id': 'kraken_public', 'domain': 'market_data', 'selectable_by_user': True, 'adopted_by_default': False, 'ready': False, 'access_mode': 'public_script_adapter', 'user_access': 'public_no_login', 'market_fit': ['crypto', 'fx', 'tokenized_assets'], 'fallback_priority': 3, 'status': 'configured_runtime_unhealthy', 'reason': 'python3_provider_dependencies_missing', 'summary': 'Public no-login crypto, forex, and tokenized-asset data path; later wallet/runtime flows use kraken_cli separately.', 'install_prompts': ['System python3 is missing provider script modules: ccxt, ib_async, redis, sklearn, pyarrow, xgboost. Install with: python3 -m pip install --user --break-system-packages ccxt ib_async redis scikit-learn pyarrow xgboost']}]`

## Next

Keep promotion blocked unless the validation and execution gate become ready on the same exact branch paths; do not promote from RC-SPA or raw CatBoost scores alone.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T224522-codex-board-b-220646-post-adapter-downstream-v1/downstream-readback/board_b_220646_post_adapter_downstream_v1.json`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T224522-codex-board-b-220646-post-adapter-downstream-v1/checks/board_b_220646_post_adapter_downstream_v1_assertions.out`
- Scores: `docs/experiments/actionable-regime-confidence/runs/20260511T224522-codex-board-b-220646-post-adapter-downstream-v1/downstream-readback/exact_branch_runtime_scores_post_adapter_v1.csv`
- Command outputs: `docs/experiments/actionable-regime-confidence/runs/20260511T224522-codex-board-b-220646-post-adapter-downstream-v1/command-output`
