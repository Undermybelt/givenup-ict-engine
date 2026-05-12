# 131621 ETH Same-Symbol Pre-Bayes/BBN Branch Regression v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T131621+0800-codex-125715-eth-same-symbol-prebayes-bbn-v1`

Source root: `docs/experiments/actionable-regime-confidence/runs/20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1`

## Scope

This is a support-only readback over the already-counted `125715` six-provider ETH AQ authority packet and the already-counted `131500` downstream ingest/rooted state.

It does not count a new profitability packet, does not update production BBN CPDs, CatBoost/path-ranker market labels, or execution-tree branch weights, does not promote a candidate, does not make a live-trade claim, and does not call `update_goal`.

Board B already records stronger six-provider Pre-Bayes/BBN evidence under `20260512T131333+0800-codex-131500-eth-prebayes-bbn-consumption-v1`; this `131621` run is retained only as a branch-regression negative sample.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Preserve same-root ETH AQ lineage | `source_root.txt` points to `20260512T131500+0800-codex-125715-eth-downstream-ingest-readback-v1` | pass |
| Run ict-engine analyze on the same symbol | `checks/02_analyze_same_symbol_eth_mtf_direct.exit=0`; initial `checks/01_analyze_same_symbol_eth_mtf.exit=127` preserved as a shell invocation failure | pass after direct rerun |
| Run Pre-Bayes/filter readback | `checks/03_pre_bayes_status.exit=0` | pass |
| Produce non-null Pre-Bayes policy/gate/soft evidence | `command-output/03_pre_bayes_status.out` shows policy `318900600c5e8cf2`, gate `pass_neutralized`, active canonical regime `trend`, confidence `0.5574970918447152`, and soft evidence across market regime, factor alignment, factor uncertainty, liquidity context, and multi-timeframe resonance | pass |
| Keep CatBoost/path-ranker runtime visible | `checks/04_policy_training_status.exit=0` and `command-output/04_policy_training_status.out` show `enabled_candidate_set_ready`, `score_model_family=catboost`, `runtime_matches=2`, `raw_scored_mature=163/30`, `production_validation=162/30`, `observation_validation=162/30` | pass for old runtime target |
| Preserve exact AQ branch through structural bundle | Required branch: `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1`; `command-output/05_workflow_structural_bundle.out` instead selected `path:scenario:B2R_ETH_SIX_PROVIDER_MOMENTUM_125715:belief_regime_node:trend:trend_follow_through:primary` | fail_closed |
| Match path-ranker scores to current structural bundle | `command-output/05_workflow_structural_bundle.out` reports `path_ranker_runtime.status=enabled_no_matching_scores`; `command-output/06_workflow_execution_candidate.out` has raw score, calibrated path probability, and lower bound all `null` | fail_closed |
| Reach execution admission | `command-output/06_workflow_execution_candidate.out` reports `candidate_status=execution_blocked`, `ready=false`, `actionable=false`, `review_status=observe`, `execution_readiness=0.43776422616823835` | fail_closed |
| Promotion/trade/update-goal allowed | Not allowed from this support-only negative sample | fail_closed |

## Readback

- The direct analyze command used `B2R_ETH_SIX_PROVIDER_MOMENTUM_125715` with Kraken ETH 1d/4h/1h same-symbol MTF inputs from `20260512T125753+0800-codex-provider-provenanced-eth-kraken-mtf-v1/data/`.
- Pre-Bayes/BBN is no longer null in this state: policy version `318900600c5e8cf2`, gate `pass_neutralized`, canonical active regime `trend`, canonical confidence `0.5574970918447152`, and canonical probabilities `trend=0.4460727525727625`, `range=0.3107854494854475`, `stress=0.16745597773596904`, `transition=0.075685820205821`.
- Filtered assignments were populated: `market_regime=trend`, `factor_alignment=mixed`, `factor_uncertainty=low`, `liquidity_context=neutral`, `multi_timeframe_resonance=aligned`, `market_state_primary_regime=TrendExpansion`, and `market_state_secondary_regime=BullTrendAcceleration`.
- BBN network state exists at `state_ingest/B2R_ETH_SIX_PROVIDER_MOMENTUM_125715/bbn_network.json` with nodes for market regime, liquidity context, factor alignment, factor uncertainty, multi-timeframe resonance, entry quality, and trade outcome.
- CatBoost/path-ranker runtime remains available from the prior rooted state, but the current structural bundle changed candidate set and selected path; runtime score matching was therefore lost for the active bundle.
- The prior exact branch from `131500` remained `Bull -> ProviderCryptoMomentum -> RsiMidlineExpansion -> ProviderCryptoMomentumStateV1` with raw CatBoost score `0.2934390186466203` after runtime closure; this `131621` structural bundle instead selected generic `trend_follow_through` with selected path probability `0.3673297349109715`.
- Execution stayed fail-closed: `execution_blocked`, `ready=false`, `actionable=false`, `review_status=observe`, no path-ranker raw score, no calibrated path probability, and no path probability lower bound.

## Gate

- `support_once:131621_eth_same_symbol_prebayes_bbn_branch_regression_v1`.
- `evidence_class:chain_contract_negative_sample`.
- `supporting_only:kraken_same_symbol_prebayes_bbn_non_null_but_branch_regressed`.
- `count_once:125715_six_provider_eth_aq_authority_packet`.
- `count_once:131500_125715_eth_downstream_ingest_readback_root`.
- `pass:analyze_direct_exit0`.
- `pass:pre_bayes_policy_present`.
- `pass:pre_bayes_gate_pass_neutralized`.
- `pass:soft_evidence_present`.
- `pass:bbn_network_present`.
- `pass:catboost_path_ranker_runtime_visible`.
- `fail_closed:initial_shell_invocation_exit127`.
- `fail_closed:exact_aq_branch_not_preserved`.
- `fail_closed:structural_bundle_shifted_to_generic_trend_follow_through`.
- `fail_closed:path_ranker_runtime_enabled_no_matching_scores`.
- `fail_closed:current_candidate_calibrated_path_prob_absent`.
- `fail_closed:current_candidate_path_prob_lower_bound_absent`.
- `fail_closed:execution_gate_status_execution_blocked`.
- `fail_closed:execution_ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not feed `131621` into regime-conditioned win-rate, BBN likelihood tables, CatBoost/path-ranker market labels, or execution-tree branch weights as positive profitability evidence. The valid continuation is the `131333`/`131803` line: preserve six-provider AQ provenance and exact branch attribution, then make the current structural candidate rows acquire calibrated path probability, lower-bound evidence, and non-observe execution admission without relaxing thresholds.
