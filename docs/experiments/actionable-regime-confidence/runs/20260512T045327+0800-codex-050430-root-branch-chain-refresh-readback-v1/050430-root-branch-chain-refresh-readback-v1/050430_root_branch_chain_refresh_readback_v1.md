# 050430 Root Branch Chain Refresh Readback v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T050430+0800-codex-board-b-root-branch-chain-refresh-v1`

Source state: `docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-chain/closure_reuse_cleanwire_bundle_catboost_20260512T034711+0800/state_reuse_cleanwire_bundle_catboost_v1`

Readback timestamp: `20260512T045327+0800`

## Command Evidence

All recorded `050430` chain-refresh commands exited `0`:

- `00_provider_status_agent.exit=0`
- `01_provider_status_compact.exit=0`
- `02_auto_quant_status.exit=0`
- `03_pre_bayes_status.exit=0`
- `04_policy_training_status.exit=0`
- `05_export_structural_path_target.exit=0`
- `06_workflow_structural_bundle.exit=0`
- `07_workflow_execution_candidate.exit=0`
- `08_workflow_full.exit=0`

## Layer Readback

- Provider status was enumerated rather than collapsed into a data blocker: `yfinance` ready, `kraken_cli` ready, `ibkr` / `ibkr_bridge` configured but dependency-unhealthy with gateway reachable, `tradingview_mcp` connectivity probe failed, and `kraken_public` remained unhealthy under system Python dependency gaps.
- Auto-Quant status for the copied `050430` state was `missing_dependency`, `bootstrap_needed=true`, `data_ready=false`; this run did not perform a fresh selected-data Auto-Quant backtest.
- Pre-Bayes/filter carried the five-root label set in read-only assignments, but the actual gate was `observe_only`, `pass_to_bbn=false`, and quality stayed below pass at `0.39931857543136917`.
- BBN read-only regime decision was `accepted` and `trade_usable=true`, but `regime_bundle_bbn_application_status=skipped`, so this is not applied BBN promotion evidence.
- CatBoost/path-ranker runtime was enabled and matched the five candidate paths, but validation remained unfit: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, `mature_rows=0`, and `calibration=not_fitted`.
- Workflow structural bundle selected the scoped Manipulation path as rank 1, direction `Observe`, and returned `ask_user_choose_historical_data` with `blocked_reason=user_selected_historical_data_missing`.
- Execution candidate was `actionable=false`, `ready=false`, `candidate_status=execution_blocked`, `pre_bayes_gate_status=observe_only`, and `execution_readiness=0.3210541039505038`.
- Execution tree closed-loop admission remained fail-closed: it preserved a Bull path in `closed_loop_branch_admission`, but reported `status=fail_closed`, `execution_tree_branch=transition_guardrail`, `execution_tree_gate_status=observe`, `path_ranker_score_visible_to_execution_tree=false`, and `path_ranker_score_used_by_execution_tree=false`.
- Workflow full still emitted `ask-user` review reasons requiring the user to choose one recorded historical data path before running `factor-research` again.

## Gate

- `diagnostic_only:root_branch_chain_refresh_readback`.
- `pass:chain_commands_exit_zero`.
- `pass:rooted_candidate_paths_visible_to_policy_training_and_workflow_bundle`.
- `fail_closed:auto_quant_copied_state_missing_dependency_no_fresh_backtest`.
- `fail_closed:pre_bayes_observe_only`.
- `fail_closed:bbn_application_skipped`.
- `fail_closed:catboost_validation_zero_of_30`.
- `fail_closed:execution_candidate_execution_blocked`.
- `fail_closed:execution_tree_not_using_path_ranker_score`.
- `blocked:user_selected_historical_data_missing`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Keep `034002/downstream-combined-v1` fail-closed. Do not promote from `050430`; it is useful chain-refresh evidence only. The next qualifying action still requires explicit user selection of exactly one of `HTF=1d`, `MTF=4h`, or `LTF=1h`, followed by selected-data factor-research / Auto-Quant and downstream continuation only if nonzero mature rooted observations preserve the full branch path through Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree.
