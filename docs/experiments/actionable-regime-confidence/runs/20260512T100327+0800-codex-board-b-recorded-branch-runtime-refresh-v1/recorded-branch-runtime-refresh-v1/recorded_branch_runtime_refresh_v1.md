# Board B Recorded Branch Runtime Refresh v1

Run id: `20260512T100327+0800-codex-board-b-recorded-branch-runtime-refresh-v1`

Mode: `incubation_only` / non-promoting readback.

Scope:
- Fresh provider and downstream readback for the existing recorded-history branch.
- No `HTF`, `MTF`, `LTF`, or `spot` history path is selected here.
- No Board B cursor row is edited.
- No production promotion is allowed.
- `update_goal=false`.

## Evidence

Provider/status and fetch artifacts:
- `command-output/01_provider_status_agent.stdout`
- `command-output/02_provider_status_yfinance.stdout`
- `command-output/03_provider_status_tradingview_mcp.stdout`
- `command-output/04_provider_status_ibkr.stdout`
- `command-output/05_provider_status_kraken_cli.stdout`
- `provider-fetch/yfinance_qqq_1h.csv`
- `command-output/07_tradingview_harness_qqq_1d.stdout`
- `provider-fetch/kraken_public_xbtusd_1h.csv`
- `provider-fetch/ibkr_aapl_1h.csv`

Downstream artifacts:
- `command-output/10_auto_quant_status_recorded_state.stdout`
- `command-output/11_pre_bayes_status_recorded_state.stdout`
- `command-output/12_policy_training_status_recorded_state.stdout`
- `command-output/13_export_structural_path_ranking_target_recorded_state.stdout`
- `command-output/14_workflow_structural_bundle_recorded_state.stdout`
- `command-output/15_workflow_execution_candidate_recorded_state.stdout`
- `command-output/16_workflow_full_recorded_state.stdout`

Pair-alias incubation check:
- `pair-alias-work/config.tomac.nq_alias.json`
- `pair-alias-work/run_pair_alias.py`
- `command-output/19_run_tomac_pair_alias_nq_usd_abs2.stdout`
- `command-output/19_run_tomac_pair_alias_nq_usd_abs2.stderr`

## Readback

Provider panel:
- `yfinance` QQQ 1h fetch exited `0` and wrote `197` rows after one HTTP 429 retry.
- TradingViewRemix stdio harness fetch exited `0` and returned `21` QQQ daily bars. Catalog `provider-status --provider tradingview_mcp` still reports the default MCP probe unhealthy, so this is local-stdio reachability, not generic catalog readiness.
- Kraken public kline fetch exited `0` and wrote `721` XBTUSD 1h rows; `kraken_cli` provider status exited `0` and stayed ready.
- IBKR historical fetch exited `0` through the reachable local gateway on port `4002` and wrote `160` AAPL 1h rows. This improves over earlier dependency-download failures, but the catalog status still reports the configured provider unhealthy because the default provider-status runtime path lacks IBKR dependencies/consent.

Downstream chain:
- Auto-Quant status exited `0`: `dependency_ready_data_missing`, `dependency_healthy=true`, `data_ready=false`.
- Pre-Bayes/filter exited `0`: `latest_gate_status=pass_neutralized`.
- BBN evidence is applied in the filtered assignments for the exact path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- CatBoost/path-ranker is runtime-ready: trainer artifact model family `catboost`, runtime status `enabled_candidate_set_ready`, production validation `286/30`, observation validation `48/30`.
- Structural bundle preserves the same exact rooted branch path and carries `path_ranker_raw_score=0.65`.
- Execution-candidate preserves the same exact path but remains `execution_observe_only`, `review_status=observe`, `ready=false`, with `execution_readiness=0.4504361163104953` and `pre_bayes_gate_status=pass_neutralized`.
- The structural recommended next step still requires explicit user selection of historical data before another factor-research pass.

Pair-alias check:
- The first two wrapper attempts failed before measurement because the script path/source path was relative to the Auto-Quant workspace owner.
- The corrected wrapper `19_run_tomac_pair_alias_nq_usd_abs2` exited `0`.
- The sanitized `NQ/USD` alias removes the previous underscore pairlist failure and reaches measurement.
- Result remains non-promoting: `TomacNQ_KillzoneBreakout` produced `0` trades, `0.0000%` profit, `0.0000` Sharpe, and no mature rooted observations.

## Decision

Gate: `incubation_only:recorded_branch_runtime_refresh_provider_fetches_succeeded_execution_observe_only`.

This run materially improves provider evidence because all four requested provider paths produced current fetch/readback evidence, including IBKR. It does not satisfy production promotion because selected-history approval is still missing, Auto-Quant data readiness remains false in the recorded state, Pre-Bayes is neutralized, and execution-candidate remains observe-only.

Promotion allowed: `false`.

`update_goal=false`.

## Next

Ask the user to select exactly one recorded path for `SRC_ROOT_CARRY_LONG_220646`: `HTF`, `MTF`, `LTF`, or `spot`. After that selection, run the deferred factor-research path and then the branch-preserving Pre-Bayes -> BBN -> CatBoost/path-ranker -> execution-tree chain again.
