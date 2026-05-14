# 165222 162400 Repaired AQ Downstream Readback v1

This is a diagnostic terminal readback for Board A claim `165222_162400_repaired_aq_downstream_readback_v1`.

This session did not rerun provider fetches, Auto-Quant, or downstream commands. During collision checks, late downstream artifacts appeared under the older `state_downstream_v1` path, so this readback inspects those outputs instead of creating a duplicate `state_downstream_repair_v2_v1` state.

## Evidence

- Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T162400+0800-codex-board-a-six-provider-btc-local-tvr-aq-v1/`
- Repaired provider/AQ source: `six-provider-btc-local-tvr-aq-same-root-repair-v2/same_root_repair_v2.json`
- Late downstream command outputs: `command-output/20_build_downstream_inputs.*` through `command-output/27_export_structural_path_ranking_target.*`
- Late downstream state: `state_downstream_v1/`

## Readback

- All late downstream commands `20` through `27` exited `0`.
- `auto-quant-results-import` imported `12/12` ok strategies.
- `auto-quant-prior-init` applied `12` strategies and `224` total trades in the isolated run-root state; final trade-outcome probabilities were approximately `[0.4445, 0.0000, 0.5555]`.
- Pre-Bayes was only `pass_neutralized`; canonical structural active regime was `range` with confidence `0.5233`, not `>=95%`.
- Analyze stayed `Observe only`; market state was `RangeConsolidation/WideRange` with overall confidence about `0.398`.
- Execution tree stayed `observe / transition_guardrail / guarded`; branch probability was `0.0`, posterior uncertainty was `1.0`, and ranker status was not ready.
- Policy training was not ready: entry-model matched rows were `0`; CatBoost/path-ranker validation had `raw_scored_mature=0`.
- Structural path-ranking export produced `3` rows, `0` mature rows, `0` raw path scores, `0` calibrated path probabilities, `0` execution-gate rows, and `0` training-weight rows.

## Gate

- `active_claim_closed:165222_162400_repaired_aq_downstream_readback_v1`
- `diagnostic_only:true`
- `pass:late_downstream_commands_exit0_8_of_8`
- `pass:auto_quant_import_ok_12_of_12`
- `pass:bbn_prior_init_applied_12_strategies_224_trades_isolated_state`
- `partial:pre_bayes_pass_neutralized_confidence_0_523`
- `fail_closed:canonical_structural_confidence_below_95`
- `fail_closed:market_state_confidence_0_398`
- `fail_closed:execution_tree_observe_transition_guardrail`
- `fail_closed:path_ranker_mature_rows_0_of_3`
- `fail_closed:policy_training_matched_rows_0`
- `fail_closed:no_cross_market_timeframe_validation`
- `accepted_95_contexts_added_0`
- `promotion_allowed=false`
- `trade_usable=false`
- `update_goal=false`
