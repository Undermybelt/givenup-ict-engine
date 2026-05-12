# Auto-Quant Copied-State Workspace Rebase Fix v1

Scope: CLI/runtime plumbing repair for copied Board B states. This does not select historical data, does not run Auto-Quant backtests for promotion, does not produce mature rooted branch observations, does not rerun Pre-Bayes/BBN/CatBoost/execution-tree promotion checks, and does not call `update_goal`.

## Root Cause

The `043449` agent-selected MTF sidecar copied the `034002` combined state into `/tmp`, but the copied `auto_quant_dependency.json` still contained an absolute `managed_dir` pointing back to `034002/downstream-combined-v1/state_combined_v1/.deps/auto-quant`.

The previous repair path normalized copied configs only through `ensure_bootstrapped_config`. `auto_quant_status` read `load_config` directly, so readiness and factor-research handoff surfaces still emitted shared combined-state `run_tomac.py` paths.

## Fix

- `src/application/auto_quant/config.rs`: moved copied-state managed-dir normalization into shared config resolution.
- `src/application/auto_quant/status.rs`: switched status readback to the resolved config path so readiness and handoff surfaces see the copied state-local workspace.
- `src/application/auto_quant/mod.rs`: added a status-level regression test for copied states.

## Evidence

- `command-output/00_copied_state_config_tests.out`: `cargo test copied_state_config --lib -- --nocapture` passed `4/4`.
- `command-output/01_live_043449_status_after_fix.out`: patched `auto-quant-status` against the live `043449` copied state resolves `managed_dir`, `workspace.repo_root`, and `run_tomac.py` under `/tmp/20260512T043449+0800-codex-board-b-agent-selected-mtf-after-cli-fix-v1/state_mtf_after_cli_fix_v1/.deps/auto-quant`.
- `checks/02_factor_research_smoke_assertion.json`: factor-research smoke on a fresh tmp copy reports `managed_dir_tmp_local=true`, `repo_root_tmp_local=true`, `recommended_command_tmp_local=true`, and `shared_combined_state_in_command=false`.

## Gate

- `pass:copied_state_auto_quant_workspace_rebased_to_tmp_local`.
- `pass:factor_research_handoff_recommended_command_tmp_local`.
- `blocked:user_selected_historical_data_missing`.
- `not_started:no_selected_data_auto_quant_backtest`.
- `not_started:no_mature_rooted_observations_no_downstream_rerun`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Keep `034002` as the fail-closed cursor. This repair makes the next explicitly user-selected `HTF=1d`, `MTF=4h`, or `LTF=1h` run safer because copied states no longer route Auto-Quant execution back into the shared combined-state workspace. It is still plumbing evidence only.
