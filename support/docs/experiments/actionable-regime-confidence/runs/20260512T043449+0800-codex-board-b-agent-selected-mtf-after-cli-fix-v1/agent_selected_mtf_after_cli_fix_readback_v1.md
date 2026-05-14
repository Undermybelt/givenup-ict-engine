# Agent-Selected MTF After CLI Fix Readback v1

Scope: non-promotional diagnostic for the repaired Auto-Quant CLI prepare/state-resolution path after `042905`.

This does not select historical data, does not edit the Board B cursor, does not promote any candidate, and does not call `update_goal`.

## Inputs

- Board cursor before run: `034002`, `board_state=rejected`, `hard_gate_result=fail:downstream_closed_loop_not_promotable`.
- Candidate data: `analyze_nq_mtf.json`, actual cadence `4h`, `260` candles from `2025-10-31T16:00:00Z` to `2025-12-31T20:00:00Z`.
- Source state copied to tmp state: `/tmp/20260512T043449+0800-codex-board-b-agent-selected-mtf-after-cli-fix-v1/state_mtf_after_cli_fix_v1`.
- Runtime binary: `/tmp/ict-engine-codex-auto-quant-prepare-target/debug/ict-engine`.

## Command Readback

- `02_copy_state.exit=0`.
- `03_auto_quant_status_before.exit=0`.
- `04_factor_research_mtf_agent_selected.exit=0`.
- `05_auto_quant_status_after.exit=0`.

`factor-research` emitted an Auto-Quant handoff for the MTF data path and reported:

- `data_ready=true`.
- `dependency_ready_data_ready`.
- `auto_quant_active_strategy_count=1`.
- `recommended_next_step.action_type=run_command`.
- `recommended_next_step.user_input_required=false`.

## Isolation Finding

The copied tmp state still carries absolute Auto-Quant workspace paths pointing back to the shared combined-state workspace:

```text
docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/.deps/auto-quant
```

The emitted recommended command also points at the shared combined-state `run_tomac.py`, not a tmp-local copied workspace. Therefore this diagnostic must stop before running Auto-Quant. Running the recommended command would risk mutating shared combined-state Auto-Quant files and would still not satisfy the explicit `user_selected_historical_data` gate.

## Gate

- `diagnostic_only:agent_selected_mtf_after_cli_fix`.
- `pass:factor_research_handoff_dependency_ready_data_ready`.
- `fail_closed:copied_state_auto_quant_workspace_absolute_path_leak`.
- `blocked:user_selected_historical_data_missing`.
- `not_started:auto_quant_run_tomac_not_run_to_avoid_shared_state_mutation`.
- `not_started:no_mature_rooted_observations_no_downstream_rerun`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not promote from this diagnostic. The next qualifying move remains explicit user selection of exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h`.

After explicit selection, run selected-data factor-research/Auto-Quant only with a state-local Auto-Quant workspace or a deliberate output override that prevents shared combined-state mutation. Continue downstream only if the run emits nonzero mature rooted branch observations preserving `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor` through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
