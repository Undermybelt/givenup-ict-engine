# Root Branch Chain Refresh v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T050430+0800-codex-board-b-root-branch-chain-refresh-v1`

This is an append-only Board B readback. It copied the existing 034002/034711 state into this run directory, then reran provider status, Auto-Quant status, Pre-Bayes, policy/CatBoost status, structural target export, workflow structural bundle, workflow execution-candidate, and workflow full status. It does not edit the Current Cursor, does not start new Auto-Quant/Freqtrade training, does not consume the in-flight 043932 miner, does not select HTF/MTF/LTF for the user, and does not call update_goal.

## Command Status

All command exits zero: `True`.
- `00_provider_status_agent.exit` = `0`
- `01_provider_status_compact.exit` = `0`
- `02_auto_quant_status.exit` = `0`
- `03_pre_bayes_status.exit` = `0`
- `04_policy_training_status.exit` = `0`
- `05_export_structural_path_target.exit` = `0`
- `06_workflow_structural_bundle.exit` = `0`
- `07_workflow_execution_candidate.exit` = `0`
- `08_workflow_full.exit` = `0`

## Provider / Auto-Quant Readback

Provider summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.
- `yfinance:live_runtime` ready=`True` status=`ready` reason=`native_yfinance_runtime_available`
- `ibkr_bridge:local_runtime` ready=`False` status=`configured_runtime_unhealthy` reason=`ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable`
- `kraken_cli:local_runtime` ready=`True` status=`ready` reason=`kraken_cli_config_detected`
- `ibkr:market_data` ready=`False` status=`configured_runtime_unhealthy` reason=`ibkr_runtime_dependencies_missing_with_gateway_reachable`
- `kraken_public:market_data` ready=`False` status=`configured_runtime_unhealthy` reason=`python3_provider_dependencies_missing`
- `tradingview_mcp:market_data` ready=`False` status=`configured_runtime_unhealthy` reason=`tradingview_mcp_connectivity_probe_failed`
- `yfinance:market_data` ready=`True` status=`ready` reason=`public_yahoo_http_endpoints`
- Auto-Quant status in the isolated state copy: `missing_dependency`, healthy=`False`, notes=`['auto_quant_not_bootstrapped']`.

## Root Branch Preservation

- BBN/read-only bundle exposes `5` rooted branch paths.
- `Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72`
- `Bear -> BearMarketDrawdown -> NQHighVixOversoldRebound -> NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72`
- `Sideways -> RangeConsolidation -> NQCalmVixZReversion -> NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72`
- `Crisis -> ExtremeStress -> NQFlushRebound -> NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72`
- `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72`
- Structural workflow candidate set size is `5`, runtime source `candidate_set`, runtime matches `5`.
- Execution trace contains `1` of these exact branch strings: `['Bull -> TrendExpansion -> NQSourceRootCarry -> NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72']`.

## Gate Result

Gate result: `root_branch_chain_refresh_v1=full_runtime_refresh_exit0_no_promotion`.
- Pre-Bayes gate: `observe_only`.
- BBN read-only decision: `accepted`; BBN application status: `skipped`; trade usable field: `true`.
- Policy/CatBoost training readiness: `False`; summary: `entry-model training modules mixed: ready=[] pending=[cisd_rb_long_v1,breaker_rb_long_v1] | structural_path_ranking_target rows=5 history_rows=13 mature_rows=0 history_mature_rows=0 raw_scored_mature=0/30 production_validation=0/30 observation_validation=0/30 calibration=not_fitted trainer_artifact=ready trainer_status=present_validation_insufficient runtime_selection=enabled_candidate_set_ready runtime_mode=prefer_history runtime_source=candidate_set score_model_family=catboost score_source=external_model runtime_matches=5`.
- Structural validation summary: `Ranker validation: calibration=false quality_ready=false raw_scored_mature=0/30 production_validation=0/30 observation_validation=0/30 ready=false`.
- Structural runtime summary: `Ranker runtime: structural_path_ranking_target rows=5 history_rows=13 mature_rows=0 history_mature_rows=0 raw_scored_mature=0/30 production_validation=0/30 observation_validation=0/30 calibration=not_fitted trainer_artifact=ready trainer_status=present_validation_insufficient runtime_selection=enabled_candidate_set_ready runtime_mode=prefer_history runtime_source=candidate_set score_model_family=catboost score_source=external_model runtime_matches=5`.
- Workflow execution-candidate status: `execution_blocked`, ready=`False`, reason=`structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- Workflow latest execution candidate remains `no_trade`.

Promotion remains fail-closed: no user-selected HTF/MTF/LTF historical-data selection, isolated Auto-Quant dependency status is missing_dependency, Pre-Bayes is observe_only, BBN application is skipped, policy training matched rows remain zero, CatBoost/path-ranker is candidate-set-only with 0/30 validation, and execution candidate is not ready/actionable.

## Next

Keep `034002` as the fail-closed cursor. Do not promote from this refresh. The next qualifying move remains explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, then selected-data factor-research/Auto-Quant must emit nonzero mature rooted branch observations and preserve the same branch path through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
