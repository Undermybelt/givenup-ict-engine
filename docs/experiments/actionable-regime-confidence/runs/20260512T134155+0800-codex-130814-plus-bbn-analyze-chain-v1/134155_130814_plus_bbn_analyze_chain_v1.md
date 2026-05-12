# 134155 130814 Plus BBN Analyze Chain v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T134155+0800-codex-130814-plus-bbn-analyze-chain-v1`

Source roots:
- CatBoost/path-ranker state: `docs/experiments/actionable-regime-confidence/runs/20260512T130814+0800-codex-131500-eth-catboost-pathranker-closure-v1`
- Six-provider composite data: `docs/experiments/actionable-regime-confidence/runs/20260512T131333+0800-codex-131500-eth-prebayes-bbn-consumption-v1/data/`

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Preserve the rooted ETH six-provider branch | Symbol `B2R_ETH_SIX_PROVIDER_MOMENTUM_125715`; branch path inherited from `125715 -> 131500 -> 130814` | pass |
| Reuse CatBoost/path-ranker closure rather than rerunning provider/AQ authority | `source_root_130814.txt`, copied `state_ingest` into `state_catboost_plus_bbn_v1` | pass |
| Run analyze with BBN soft evidence | `checks/01_analyze_catboost_state_apply_bbn.exit=0` | pass |
| Run Pre-Bayes/filter readback | `checks/02_pre_bayes_status.exit=0` | pass, gate still observe-only |
| Run CatBoost/path-ranker status | `checks/03_policy_training_status.exit=0`, `checks/09_policy_training_status_after_export.exit=0` | pass, but runtime candidate matching regressed |
| Run execution-tree/workflow readbacks | `checks/04_workflow_structural_feedback.exit=0` through `12_workflow_full_after_export.exit=0` | pass, execution remains blocked |
| Export structural path-ranking target after analyze | `checks/08_export_structural_path_ranking_target.exit=0` | pass |
| Reach calibrated 95% actionable confidence | canonical confidence `0.367008438103555`; selected path probability `0.33333333333333337`; no current calibrated path probability or lower bound | fail_closed |

## Readback

- All twelve commands exited `0`.
- Pre-Bayes/BBN state was present but non-admitting: policy version `318900600c5e8cf2`, active canonical structural regime `range`, gate `observe_only`, and canonical confidence `0.367008438103555`.
- Soft evidence remained diffuse: `range=0.34954935902525164`, `stress=0.18438482894107935`, `transition=0.2330329060168345`, and `trend=0.2330329060168345`.
- Entry-model training stayed not ready: both `cisd_rb_long_v1` and `breaker_rb_long_v1` had `matched_rows=0`.
- Structural path-ranking validation stayed numerically mature at the history layer: `raw_scored_mature=163/30`, `production_validation=162/30`, and `observation_validation=162/30`.
- The refreshed current candidate set regressed from runtime matching to no matching scores: `runtime_selection_status=enabled_no_matching_scores`, `runtime_active_match_count=0`, `score_model_family=unknown`, and `score_source=unknown`.
- Current target rows after export: `rows=4`, `candidate_set_size=3`, `mature_rows=1`, `history_rows=329`, `history_mature_rows=325`, `rows_with_calibrated_path_prob=0`, `rows_with_execution_gate_status=0`, and current lower-bound rows `0`.
- Execution stayed blocked: `actionable=false`, `ready=false`, `review_status=observe`, `candidate_status=execution_blocked`, `execution_gate_status=execution_blocked`, `execution_readiness=0.3046756738194877`, selected path `range_mean_reversion`, and selected path probability `0.33333333333333337`.

## Gate

- `count_once:134155_130814_plus_bbn_analyze_chain_v1`.
- `support_once:125715_131500_130814_131333_rooted_eth_branch`.
- `pass:all_commands_exit0`.
- `pass:pre_bayes_bbn_soft_evidence_present`.
- `pass:catboost_history_validation_mature`.
- `fail_closed:pre_bayes_gate_observe_only`.
- `fail_closed:canonical_confidence_0.367008438103555_below_0.95`.
- `fail_closed:selected_path_probability_0.33333333333333337_below_0.95`.
- `fail_closed:current_candidate_calibrated_path_prob_absent`.
- `fail_closed:current_candidate_path_prob_lower_bound_absent`.
- `fail_closed:runtime_selection_enabled_no_matching_scores`.
- `fail_closed:entry_model_matched_rows_0`.
- `fail_closed:execution_gate_status_execution_blocked`.
- `fail_closed:execution_ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not repeat provider/AQ authority, downstream ingest, or CatBoost numeric-floor closure for this ETH root. The immediate blocker is candidate-set continuity after BBN/analyze: current candidate rows need matching CatBoost runtime scores plus calibrated path probability/lower-bound and a non-observe Pre-Bayes/execution gate before any Board A acceptance can be claimed.
