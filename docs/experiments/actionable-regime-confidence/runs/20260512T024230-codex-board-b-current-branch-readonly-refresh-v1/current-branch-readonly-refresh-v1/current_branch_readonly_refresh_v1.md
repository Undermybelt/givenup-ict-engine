# Board B Current Branch Readonly Refresh v1

Run id: `20260512T024230-codex-board-b-current-branch-readonly-refresh-v1`

Board hash observed before artifact writeback:
- Board B: `2405983308e4b140c0e5431fc73cf2bb33ab98ad`
- Board A: `979c8d222095ddd1fa6c6bab4664d052f4a1cd66`

## Scope

This is a fresh local read-only command slice for the active Board B branch.
It copies the prior `023559` fail-closed state into this run root, then runs
provider, Auto-Quant, Pre-Bayes, BBN evidence readback, CatBoost/path-ranker,
workflow, and execution-tree checks against the copy. It does not mutate source
roots, canonical intake, runtime code, thresholds, or the active Current Cursor.

Copied state:
`docs/experiments/actionable-regime-confidence/runs/20260512T024230-codex-board-b-current-branch-readonly-refresh-v1/current-branch-readonly-refresh-v1/state_current_branch_readonly_refresh_v1`

## Exact Branch

`Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

## Command Readback

- Provider status exited `0`: yfinance ready, Kraken CLI ready, IBKR gateway reachable but dependency-unhealthy, TradingView MCP/Remix probe unhealthy.
- Prepared Auto-Quant crypto workspace exited `0`: status `dependency_ready_data_ready`, `healthy=true`, `dependency_healthy=true`, `data_ready=true`.
- Copied branch-state Auto-Quant status exited `0` but remains `missing_dependency`; do not count it as a fresh branch Auto-Quant readiness upgrade.
- Pre-Bayes status exited `0`: `latest_gate_status=pass_neutralized`.
- BBN evidence is visible as read-only branch evidence: decision state `accepted`, label `SourceRootStopCarryLongHorizonV1`, soft-evidence weight `0.650`, branch path count `4`, but runtime application status remains `skipped`.
- CatBoost/path-ranker status exited `0`: structural path ranking is runtime eligible, `raw_scored_mature=869/30`, `production_validation=869/30`, `observation_validation=82/30`, score source `external_model`; entry-model BBN/CatBoost training rows remain `0`.
- Workflow execution-candidate exited `0`: candidate status `execution_blocked`, `ready=false`, `actionable=false`, `execution_readiness=0.4420748337394927`, Pre-Bayes `pass_neutralized`.
- Workflow full exited `0`: `closed_loop_branch_admission.status=fail_closed`, exact Sideways path preserved, blocking truth `user_selected_historical_data_missing`.
- Execution-tree trace readback preserves the exact Sideways branch but keeps it fail-closed: `execution_tree_branch=transition_guardrail`, `execution_tree_bias=guarded`, `review_status=observe`.
- Artifact ledger tail remains non-promoting: latest execution candidate has `promote_candidate=false`, `actionable=false`, and the ensemble vote asks for explicit user-selected historical data before another same-branch replay.

## Decision

Gate result:
`current_branch_readonly_refresh_v1=exact_branch_visible_catboost_ready_pre_bayes_neutralized_execution_fail_closed_no_promotion`

Promotion is rejected for this slice. The branch path is present through the
downstream surfaces, but the current runtime context still does not admit the
Sideways/RangeCarry branch. Do not rerun trace parity or CatBoost readiness for
`220646`; the next non-duplicative action is either explicit user-selected /
provider-sourced Sideways-compatible historical data for one final same-branch
check, or move to `B2R-repeat-next` with a materially different rooted family
and provider panel.

## Artifacts

- Provider output: `command-output/00_provider_status_agent.out`
- Prepared Auto-Quant status: `command-output/01_auto_quant_status_prepared_crypto.out`
- Branch-state Auto-Quant status: `command-output/02_auto_quant_status_branch_state.out`
- Pre-Bayes status: `command-output/03_pre_bayes_status_refresh.out`
- CatBoost/path-ranker status: `command-output/04_policy_training_status.out`
- Workflow execution candidate: `command-output/05_workflow_execution_candidate_refresh.out`
- Workflow full: `command-output/06_workflow_full_refresh.out`
- BBN network shape: `command-output/07_bbn_network_shape.out`
- Summary JSON: `current_branch_readonly_refresh_v1.json`
- Assertions: `current_branch_readonly_refresh_v1_assertions.out`

## Promotion Status

- Accepted rows added: `0`
- New confidence gate: `false`
- Canonical merge allowed: `false`
- Downstream promotion allowed: `false`
- Runtime code changed: `false`
- Shared intake mutated: `false`
- Thresholds relaxed: `false`
- Raw data committed: `false`
- Trade usable: `false`
- `update_goal=false`
