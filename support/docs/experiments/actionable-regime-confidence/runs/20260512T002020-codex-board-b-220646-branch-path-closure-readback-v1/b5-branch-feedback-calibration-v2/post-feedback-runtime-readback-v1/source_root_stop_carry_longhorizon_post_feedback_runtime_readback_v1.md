# SourceRootStopCarryLongHorizon Post-Feedback Runtime Readback v1

Run id: `20260512T004313+0800-codex-board-b-220646-post-feedback-runtime-readback-v1`

Source cursor: `20260512T002020+0800-codex-board-b-220646-branch-path-closure-readback-v1`

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T002020-codex-board-b-220646-branch-path-closure-readback-v1`

State: `fail_closed:post_feedback_runtime_readback_no_promotion`

## Scope

This is an append-only readback of the fresh post-feedback runtime logs under:

`b5-branch-feedback-calibration-v2/post-feedback-runtime-readback-v1`

It does not rescore RC-SPA, change the recipe, change runtime code, or supersede the active `002020` blocked cursor. The check is only whether the already-measured `220646` branch paths still survive the ordered local chain after feedback calibration:

`Auto-Quant/source feedback -> Pre-Bayes/filter -> BBN -> CatBoost/path-ranker -> execution tree/workflow`.

## Command Readback

All `*.exit` files in `post-feedback-runtime-readback-v1` returned `0`:

- `01_provider_status_agent`
- `02_auto_quant_status_json`
- `03_analyze_live_post_feedback`
- `04_pre_bayes_status_json`
- `05_policy_training_status_json`
- `06_export_structural_path_ranking_target`
- `07_workflow_structural_bundle_agent`
- `08_workflow_execution_candidate_agent`
- `09_workflow_full_json`
- `10_policy_training_status_final_json`
- `11_workflow_full_final_json`

## Source Status

The source candidate remains the prior strict RC-SPA pass, not a new score:

- Recipe: `SourceRootStopCarryLongHorizonV1`
- Source score: `85.7407`
- Price roots passed: `4/4`
- Scoped Manipulation component: inherited upstream pass
- Feedback calibration set: `80` exact branch feedback records, `20` per Bull/Bear/Sideways/Crisis root

## Provider / Auto-Quant Status

Provider readback exited `0`.

- Ready: `yfinance`, `kraken_cli`
- Recorded but unhealthy: `ibkr` with gateway reachable but runtime dependencies missing
- Unhealthy: `tradingview_mcp`, `kraken_public`, `binance_public`, `bybit_public`
- Auto-Quant status in this isolated state: `missing_dependency` / not bootstrapped

This is not a total provider block, but it is also not evidence of a freshly bootstrapped Auto-Quant workspace for this isolated state.

## Ordered Chain Readback

Pre-Bayes/filter:

- Gate status: `pass_neutralized`
- Quality score from workflow: `0.558445370096112`
- Soft evidence used: `true`
- Branch path count in filtered assignments: `4`
- Low directional separation remains a risk flag

BBN:

- Read-only regime BBN decision: `accepted`
- Read-only label: `SourceRootStopCarryLongHorizonV1`
- Read-only trade usable: `true`
- Soft evidence strength: `moderate`, weight `0.650`
- Application status: `skipped`
- Workflow reason includes `regime_bundle_bbn_evidence_skipped=no_supported_label`
- Result: BBN evidence is visible as a read-only acceptance, but this is not a full applied posterior closure.

CatBoost/path-ranker:

- Runtime enabled and ready: `true`
- Active matches: `4`
- Raw scored mature rows: `818/30`
- Production validation: `818/30`
- Observation validation: `80/30`
- Final policy status after export says `score_model_family=unknown`, while the runtime trace still shows the execution tree consuming a `catboost` / `history_path` ranker. Treat the final readback as validation-ready but do not promote from model-family labeling alone.

Structural bundle:

- Selected path: `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`
- Bundle path-ranker score: raw `0.857407`, calibrated `0.500000`, lower bound `0.190069`, gate `observe`
- Execution-tree trace ranker lineage used `history_path` with raw `0.989590`, calibrated `0.580402`, lower bound `0.551734`, gate `pass`

Execution tree/workflow:

- Latest analyze execution readiness: `0.44860389082179186`
- Latest analyze execution gate: `execution_blocked`
- Execution tree trace status: `observe`
- Execution tree branch: `transition_guardrail`
- Execution bias: `guarded`
- Decision hint: `execution_guarded_due_to_high_transition_hazard`
- Workflow blocking truth: `user_selected_historical_data_missing`

The execution-candidate artifact itself reports `actionable=true` and `candidate_status=ready`, but that is not promotion evidence because the workflow still blocks historical-data reuse, the execution-tree artifact remains `observe`, and the applied BBN posterior is skipped.

## Gate Result

Post-feedback runtime chain is callable and branch-aware, but production promotion remains blocked:

- `pass:post_feedback_commands_exit_zero`
- `pass:branch_paths_visible_to_pre_bayes_and_ranker`
- `pass:catboost_path_ranker_validation_ready`
- `fail_closed:pre_bayes_pass_neutralized_low_separation`
- `fail_closed:bbn_application_skipped_no_supported_label`
- `fail_closed:execution_tree_observe_transition_guardrail`
- `fail_closed:workflow_user_selected_historical_data_missing`

Promotion allowed: `false`.

## Next

Keep the current blocked `002020` cursor. The next safe action is still to repair or resolve the exact Pre-Bayes/BBN branch-path consumption gap and select an explicit historical dataset for `SRC_ROOT_CARRY_LONG_220646` before rerunning factor-research and execution-candidate. Do not promote from RC-SPA, read-only BBN acceptance, or CatBoost/path-ranker readiness alone.

