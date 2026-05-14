# 103851 BTC Canary Downstream Fail-Closed v1

Run id: `20260512T104427+0800-codex-103851-btc-canary-downstream-failclosed-v1`

Mode: `append_only_downstream_readback_registration_non_promoting`

## Scope

This packet registers the completed downstream readback at `20260512T103851+0800-codex-103010-btc-ingest-downstream-readback-v1`. It consumes existing command outputs only. It does not rerun Auto-Quant, does not edit Current Cursor, does not approve selected history, does not approve source/control evidence, does not mutate canonical intake, does not promote Pre-Bayes/filter, BBN, CatBoost/path-ranking, or execution-tree output, does not make a trade claim, and does not call `update_goal`.

The source run reads back the `103010` BTC always-entry canary after its real-trade ingest. The source provider context is Binance `BTCUSDT` 1h from the provider-owned sidecar, but the strategy itself is still a canary/plumbing diagnostic rather than a Board-B-rooted non-canary recipe.

## Source Evidence

- Source readback root: `docs/experiments/actionable-regime-confidence/runs/20260512T103851+0800-codex-103010-btc-ingest-downstream-readback-v1`
- Source canary root: `docs/experiments/actionable-regime-confidence/runs/20260512T103010+0800-codex-board-b-provider-btc-always-entry-canary-v1`
- Symbol/state: `B2R_PROVIDER_BTC_CANARY_103010` under `103010/state_ingest`
- Command outputs:
  - `00_pre_bayes_status.out`
  - `01_policy_training_status.out`
  - `02_export_structural_path_ranking_target.out`
  - `03_workflow_structural_bundle.out`
  - `04_workflow_execution_candidate.out`
  - `05_workflow_full.out`
  - `06_policy_training_status_after_export.out`

## Readback

- All seven downstream readback commands exited `0`.
- Pre-Bayes status was empty: no latest bridge, policy, soft evidence, filtered assignments, canonical structural regime, or gate status.
- Initial policy training status had `matched_rows=0` for both entry models and no active path-ranker runtime.
- Structural path-ranking target export produced one row, `candidate_set_size=1`, but the row remained `unobserved` with `mature_rows=0`.
- After export, CatBoost/path-ranker validation remained below floor: `raw_scored_mature=0/30`, `production_validation=0/30`, `observation_validation=0/30`, calibration `not_fitted`, trainer artifact `missing`, runtime selection `disabled`, and runtime matches `0`.
- Workflow structural bundle selected only `bootstrap_readiness` with `direction=observe`, `current_posterior=0.0`, and trigger `No workflow snapshot exists yet`.
- Execution candidate stayed `actionable=false`, `ready=false`, `review_status=observe`, with reason `structural_recommended_path_visible_but_execution_or_pre_bayes_gate_not_ready`.
- Full workflow reported `closed_loop_branch_admission.status=fail_closed` and reason `exact_structural_branch_visible_but_not_ready_or_actionable`.

## Decision

This is a useful ordered-chain readback because it proves the canary ingest can be passed through the downstream status surfaces without crashing. It is not promotion evidence. The candidate has no mature rows, no Pre-Bayes/BBN state, no CatBoost trainer artifact, no enabled path-ranker runtime, no execution-tree readiness, and no non-canary rooted profitability recipe.

## Gate

- `count_once:103851_btc_canary_downstream_readback`.
- `pass:downstream_readback_commands_exit0`.
- `pass:structural_path_ranking_target_export_rows_1`.
- `fail_closed:source_is_btc_canary_plumbing_diagnostic_not_branch_rooted_recipe`.
- `fail_closed:pre_bayes_empty_no_policy_or_soft_evidence`.
- `fail_closed:entry_model_matched_rows_0`.
- `fail_closed:path_ranker_raw_scored_mature_0_of_30`.
- `fail_closed:path_ranker_trainer_artifact_missing`.
- `fail_closed:runtime_selection_disabled`.
- `fail_closed:workflow_bootstrap_readiness_observe_only`.
- `fail_closed:execution_candidate_actionable_false_ready_false`.
- `promotion_allowed=false`.
- `update_goal=false`.

## Next

Do not use the positive `103010` canary as a downstream promotion seed. The next useful Board B step remains a real non-canary provider-owned factor preserving the repaired precision and price-side constraints, with explicit `main_regime -> sub_regime -> sub_sub_regime_or_profit_factor -> profit_factor`, enough profitable rooted trades, and then a fresh ordered Auto-Quant -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution-tree promotion readback.
