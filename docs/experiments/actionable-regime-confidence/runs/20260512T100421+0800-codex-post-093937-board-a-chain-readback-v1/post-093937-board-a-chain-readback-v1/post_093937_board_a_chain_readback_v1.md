# Post-093937 Board A Chain Readback v1

Run id: `20260512T100421+0800-codex-post-093937-board-a-chain-readback-v1`

Mode: `append_only_non_promoting_readback`

## Scope

Fresh isolated readback after the newer Board B roots `093435`, `093820`, `093854`, and `093937` appeared. The prior recorded-history state was copied into this run root before command execution so this run did not mutate another agent's run directory.

Source state:
- `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

Copied state:
- `docs/experiments/actionable-regime-confidence/runs/20260512T100421+0800-codex-post-093937-board-a-chain-readback-v1/state_readback_v1`

## Commands

Command outputs:
- `command-output/00_provider_status_agent.stdout.json`
- `command-output/01_auto_quant_status.stdout.json`
- `command-output/02_pre_bayes_status.stdout.json`
- `command-output/03_workflow_status_agent.stdout.json`
- `command-output/04_structural_recommended_path_bundle.stdout.json`
- `command-output/05_execution_candidate.stdout.json`
- `command-output/06_policy_training_status.stderr.txt`
- `command-output/06b_policy_training_status_output_format_agent.stdout.json`
- `command-output/07_export_structural_path_ranking_target.stdout.json`
- `checks/command_exit_summary.out`

Exit summary:
- Provider status: `0`.
- Auto-Quant status: `0`.
- Pre-Bayes status: `0`.
- Workflow full agent status: `0`.
- Structural recommended path bundle: `0`.
- Execution candidate: `0`.
- Policy training first invocation: `2` because `policy-training-status` does not accept the `--agent` alias.
- Policy training corrected invocation with `--output-format agent`: `0`.
- Structural path-ranking target export: `0`.

## Readback

Provider status:
- Summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`.
- Ready provider paths in the requested set: `yfinance` live/runtime ready, `yfinance` market-data ready, `tradingview_mcp` market-data ready, and `kraken_cli` local runtime ready.
- Not ready provider paths in the requested set: `ibkr` and `ibkr_bridge` are dependency-unhealthy despite gateway reachability; `kraken_public` is dependency-unhealthy.

Auto-Quant:
- Status: `dependency_ready_data_missing`.
- Dependency healthy: `true`.
- Data ready: `false`.
- Next command remains `ict-engine auto-quant-prepare --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T100421+0800-codex-post-093937-board-a-chain-readback-v1/state_readback_v1`.

Pre-Bayes / BBN:
- Latest gate status: `pass_neutralized`.
- Canonical structural active regime: `range`.
- Canonical structural confidence: `0.5619249343265972`.
- Read-only regime bundle BBN application status: `applied`.
- Read-only regime BBN decision state: `single_label_95`.
- Read-only regime BBN label set includes `primary::ExtremeStress` and `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- This is branch/sub-regime read-only evidence, not a new accepted `MainRegimeV2` root packet.

CatBoost / structural path-ranking:
- Entry-model BBN/CatBoost training remains not ready: both `cisd_rb_long_v1` and `breaker_rb_long_v1` have `matched_rows=0`.
- Structural path-ranking runtime is enabled and ready: `enabled_candidate_set_ready`, reuse mode `prefer_history`, source kind `candidate_set`.
- Structural target export produced `6` rows, `4` mature rows, `295` history rows, and `288` history mature rows.
- Structural path-ranking trainer artifact is ready with model family `catboost`, `12329` trained rows, `12329` history rows, and `275` calibration rows.

Execution candidate:
- Structural bundle path: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`.
- Path-ranker runtime source: `history_path`.
- Path-ranker raw score: `0.65`.
- Candidate status: `execution_observe_only`.
- Review status: `observe`.
- Execution readiness: `0.4504361163104953`.
- Ready: `false`.

## Decision

Gate: `post_093937_board_a_chain_readback_v1=path_ranker_catboost_ready_execution_observe_only_selected_history_and_source_control_blocked`.

This run proves the requested local surfaces were callable in an isolated state copy: provider status, Auto-Quant status, Pre-Bayes / BBN read-only evidence, structural path-ranking / CatBoost artifacts, and execution-candidate. It does not promote Board A.

Strict objective status remains false:
- Accepted rows added: `0`.
- New accepted `MainRegimeV2` root packet: `false`.
- Every regime at 95%-99% confidence: `false`.
- Cross-market / cross-period / cross-context validation complete: `false`.
- Explicit selected-history approval: `false`.
- R6/R5/R3 source-control unlock: `false`.
- Canonical merge: `false`.
- Selected-data Auto-Quant promotion: `false`.
- Downstream promotion: `false`.
- Trade claim: `false`.
- `update_goal=false`.

Next:
- Keep production gates fail-closed. The current Board A cursor next action remains the R6 owner-export/source-control unlock path. This recorded-history branch can only remain non-promoting feedback until explicit selected-history and source/control gates are satisfied.
