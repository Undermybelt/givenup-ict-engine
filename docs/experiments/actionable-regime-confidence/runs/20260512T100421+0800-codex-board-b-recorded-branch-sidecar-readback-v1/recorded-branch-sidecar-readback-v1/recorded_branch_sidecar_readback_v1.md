# Recorded Branch Sidecar Readback v1

Run id: `20260512T100421+0800-codex-board-b-recorded-branch-sidecar-readback-v1`

Mode: `incubation_only`

## Scope

This readback continues from the `092330` precision-fixed recorded-MTF nursery signal and adds a count-once pointer for the unrecorded `093435` TOMAC smoke sidecar. It does not edit Current Cursor, does not select `HTF`, `MTF`, or `LTF`, does not approve source/control evidence, does not promote a candidate, and does not call `update_goal`.

Source state copied before refresh:

`docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

Run-local state copy:

`docs/experiments/actionable-regime-confidence/runs/20260512T100421+0800-codex-board-b-recorded-branch-sidecar-readback-v1/state_recorded_branch_sidecar_v1`

## Commands

All command outputs are under:

`docs/experiments/actionable-regime-confidence/runs/20260512T100421+0800-codex-board-b-recorded-branch-sidecar-readback-v1/command-output/`

Commands exited `0`:

- `provider-status --agent`
- `auto-quant-status --state-dir ... --output-format json`
- `pre-bayes-status --refresh --output-format json`
- `policy-training-status --output-format agent`
- `export-structural-path-ranking-target`
- `workflow-status --phase structural-recommended-path-bundle --refresh --agent`
- `workflow-status --phase execution-candidate --refresh --agent`
- `workflow-status --refresh --agent`

## Provider Readback

Fresh provider status:

- `yfinance` live runtime ready.
- `yfinance` market data ready.
- `kraken_cli` ready.
- `tradingview_mcp` not ready in this fresh run: `tradingview_mcp_connectivity_probe_failed`.
- `ibkr` and `ibkr_bridge` not ready because runtime dependencies are missing, although the local gateway is reachable.
- `kraken_public` not ready because Python provider dependencies are missing.
- Summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready`.

## Auto-Quant Readback

`auto-quant-status` returned `dependency_ready_data_missing`:

- dependency healthy: `true`
- bootstrap needed: `false`
- data ready: `false`
- pinned/current commit: `34ba6b6ee6aa69813a50a72158d4c089d97afb96`

This copied state is useful for downstream readback, not as a fresh data-ready Auto-Quant training workspace.

## Pre-Bayes / BBN Readback

Pre-Bayes status remains `pass_neutralized`.

BBN branch evidence is applied read-only against the exact branch:

`Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

Readback fields:

- `read_only_regime_bbn_label=primary::ExtremeStress`
- `regime_bundle_bbn_evidence_application=applied`
- `regime_bundle_branch_path_count=1`
- `market_regime=range`

This is not promotion evidence because closed-loop admission remains fail-closed.

## CatBoost / Path-Ranker Readback

The structural path-ranker runtime is ready, but this is still observation/incubation evidence:

- runtime status: `enabled_candidate_set_ready`
- target rows: `6`
- history rows: `295`
- history mature rows: `288`
- raw scored mature rows: `288/30`
- production validation: `286/30`
- observation validation: `48/30`
- trainer artifact status: `runtime_eligible`
- runtime active match count: `1`

The built-in entry-model training modules remain not ready for BBN/CatBoost entry-model promotion:

- `cisd_rb_long_v1`: ready `false`, matched rows `0`
- `breaker_rb_long_v1`: ready `false`, matched rows `0`

## Execution Tree Readback

Structural bundle and execution-candidate both preserve the exact branch path:

`Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

Execution-candidate readback:

- `pre_bayes_gate_status=pass_neutralized`
- `path_ranker_raw_score=0.65`
- `path_ranker_runtime_source=history_path`
- `execution_readiness=0.4504361163104953`
- `candidate_status=execution_observe_only`
- `review_status=observe`
- `ready=false`

Full workflow readback:

- `blocking_status=blocked`
- `blocking_reason=user_selected_historical_data_missing`
- `closed_loop_branch_admission.status=fail_closed`
- `closed_loop_branch_admission.reason=exact_structural_branch_visible_but_not_ready_or_actionable`
- `ensemble.final_action=Observe`

## Sidecar 093435 Readback

Existing sidecar:

`docs/experiments/actionable-regime-confidence/runs/20260512T093435+0800-codex-board-b-aq-first-tomac-smoke-downstream-v1`

The direct TOMAC smoke run exited `0` and produced a real negative Auto-Quant/Freqtrade readback for `TomacNQ_KillzoneBreakout` on `NQ/USD`:

- trades: `5`
- total profit: `-1.3100%`
- win rate: `60.0000%`
- profit factor: `0.6185`
- Sharpe: `-0.0192`
- max drawdown: `-2.7549%`

This is count-once negative `incubation_only` evidence. It is not source/control evidence, not selected-history approval, not a selected-data Auto-Quant promotion run, and not downstream promotion evidence.

## Decision

Gate:

- `incubation_only:recorded_branch_sidecar_readback_v1`
- `fail_closed:execution_candidate_ready_false`
- `fail_closed:closed_loop_branch_admission_fail_closed`
- `fail_closed:user_selected_historical_data_missing`
- `fail_closed:auto_quant_data_ready_false_for_copied_state`
- `fail_closed:tradingview_mcp_connectivity_probe_failed_current_run`
- `fail_closed:ibkr_dependencies_missing_with_gateway_reachable`
- `fail_closed:source_control_evidence_acquired_false`

Promotion: `false`.

`update_goal=false`.

## Next

Do not repeat closed LTF/TOMAC shapes unless a concrete data, pair alias, DNS, or dependency fix changes the measurement surface. The only useful continuation is either explicit user-selected historical data for the recorded branch, or a non-promoting recorded-history slice that adds mature observations or materially improves execution readiness while preserving the same rooted branch path.
