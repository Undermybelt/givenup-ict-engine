# Branch Path Field Bridge Downstream Addendum v1

Run id: `20260512T044611+0800-codex-board-b-branch-path-field-bridge-v1`

Gate result: `branch_path_field_bridge_downstream_addendum_v1=isolated_force_ingest_chain_ran_no_promotion`

## Purpose

This addendum records the downstream commands that completed after the initial bridge readback. It does not edit the Current Cursor, does not select historical data, does not promote a candidate, and does not call `update_goal`.

## Evidence

- Enriched-wire generation: `branch-path-field-bridge-v1/branch_path_field_bridge_v1.md`
- Dry-run ingest: `command-output/01_ingest_enriched_wire_dry_run.out`
- Non-force copied-state apply failure: `command-output/02_ingest_enriched_wire_apply_tmp_state.err`
- Force apply on copied `/tmp` state only: `command-output/03_ingest_enriched_wire_force_tmp_state.out`
- Analyze/BBN readback: `command-output/04_analyze_combined_bundle_tmp_state.out`
- Pre-Bayes/filter: `command-output/05_pre_bayes_status_tmp_state.out`
- CatBoost/path-ranker status: `command-output/07_policy_training_status_tmp_state.out`
- Workflow structural bundle: `command-output/08_workflow_structural_bundle_tmp_state.out`
- Execution candidate: `command-output/09_workflow_execution_candidate_tmp_state.out`
- Workflow full: `command-output/10_workflow_full_tmp_state.out`
- Provider readback: `command-output/11_provider_status_agent.out`

## Readback

- The enriched wire contains `15415/15415` full rooted branch-path rows with `0` missing strategy mappings.
- The dry-run ingest exited `0`: `trades_total=15415`, `trades_applied=15415`, `trades_invalid=0`, `content_hash=7dcaa5e44253c074`, `ledger_status=dry_run_preview`.
- A copied-state non-force apply exited `1` because the dry-run preview ledger already recorded the same content hash.
- A copied-state `--force` apply then exited `0` and applied `15415/15415` rows with `0` invalid rows. This was only in `/tmp/ict-engine-board-b-044611-branch-path-field-bridge-v1-state`.
- The copied-state analyze, Pre-Bayes, structural target export, policy/CatBoost status, workflow structural bundle, workflow execution-candidate, workflow full, and provider-status commands all exited `0`.
- Pre-Bayes still returns `latest_gate_status=observe_only`.
- Read-only BBN fields expose the five rooted branch paths in `read_only_regime_bbn_label_set` / `regime_bundle_branch_paths_json`, but `regime_bundle_bbn_application_status=skipped`.
- CatBoost/path-ranker runtime still has `runtime_matches=5`, but validation is not ready: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, and calibration is `not_fitted`.
- Workflow structural bundle selects the exact `Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72` path from candidate-set scores.
- Execution candidate preserves that exact path but remains `execution_blocked`, `ready=false`, with `pre_bayes_gate_status=observe_only` and execution readiness `0.3210541039505038`.
- Workflow full remains blocked by `user_selected_historical_data_missing`.
- Provider status exited `0`: yfinance is ready, Kraken CLI is ready, IBKR remains dependency-unhealthy with gateway reachable, and TradingView/other market-data providers remain not fully ready.

## Gate

- `diagnostic_only:branch_path_field_bridge_downstream_addendum`.
- `pass:enriched_wire_schema_accepted`.
- `pass:isolated_force_ingest_applied15415_invalid0`.
- `pass:downstream_commands_exit0`.
- `pass:bbn_read_only_exact_branch_path_visibility`.
- `pass:catboost_candidate_set_exact_branch_matches5`.
- `fail_closed:pre_bayes_observe_only`.
- `fail_closed:bbn_application_skipped`.
- `fail_closed:catboost_validation_0_of_30`.
- `fail_closed:execution_candidate_blocked`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Keep `034002` as the fail-closed cursor. The bridge proves the trade-wire schema can carry rooted branch paths and that the copied-state runtime can surface exact branch paths downstream, but it remains diagnostic. The next qualifying action still requires explicit user selection of exactly one `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data Auto-Quant evidence with nonzero mature rooted observations through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
