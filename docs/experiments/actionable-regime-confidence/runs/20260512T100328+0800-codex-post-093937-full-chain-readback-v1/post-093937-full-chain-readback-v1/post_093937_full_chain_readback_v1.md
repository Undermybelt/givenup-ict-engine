# Post-093937 Full Chain Readback v1

Run id: `20260512T100328+0800-codex-post-093937-full-chain-readback-v1`

Mode: `non_promoting_aq_feedback`

## Scope

Fresh readback after the unregistered terminal roots `093820`, `093854`, and `093937`.
This run copies the existing recorded-MTF downstream state into this run root before
executing ict-engine status surfaces, so the shared source state is not mutated.

Source state:
- `docs/experiments/actionable-regime-confidence/runs/20260512T000748-codex-board-b-agent-selected-historical-factor-research-v1/state_agent_selected_historical_factor_research_downstream_v1`

State copy:
- `docs/experiments/actionable-regime-confidence/runs/20260512T100328+0800-codex-post-093937-full-chain-readback-v1/state_copy`

Symbol:
- `SRC_ROOT_CARRY_LONG_220646`

## Commands

All command exits are recorded under `command-output/*.exit`.

- `00_provider_status`: exit `0`
- `01_auto_quant_status`: exit `0`
- `02_pre_bayes_status`: exit `0`
- `03_pre_bayes_diff`: exit `0`
- `04_evidence_quality`: exit `0`
- `05_policy_training_status`: exit `0`
- `06_workflow_structural_bundle`: exit `0`
- `07_workflow_structural_feedback`: exit `0`
- `08_workflow_execution_candidate`: exit `0`
- `09_export_structural_path_target`: exit `0`
- `10_artifact_status_latest`: exit `0`
- `11_auto_quant_adoption_review`: exit `0`

## Provider Readback

Provider status summary: `entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:2/7 ready`.

Named-provider status:
- `yfinance`: ready in live-runtime and market-data lanes.
- `tradingview_mcp`: ready; MCP URL/API key available.
- `kraken_cli`: ready; `kraken_public` remains blocked by missing system Python provider dependencies.
- `ibkr` / `ibkr_bridge`: not ready because provider runtime dependencies are missing, but a local IBKR API is reachable on port `4002`.

## Auto-Quant Readback

`auto-quant-status` reports:
- `status=dependency_ready_data_missing`
- `dependency_healthy=true`
- `data_ready=false`
- recommended next command: `ict-engine auto-quant-prepare --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T100328+0800-codex-post-093937-full-chain-readback-v1/state_copy`

`auto-quant-adoption-review` reports:
- `review_status=prepare_required`
- `review_summary=Auto-Quant workspace is healthy but research data is not ready yet`
- `auto_quant_active_strategy_count=0`

## Pre-Bayes / BBN Readback

`pre-bayes-status` and `evidence-quality-breakdown` report:
- `latest_gate_status=pass_neutralized`
- `final_evidence_quality_score=0.5619249343265972`
- hard-pass gap `-0.18807506567340282`
- neutralized gap `0.16192493432659716`
- `uses_soft_evidence=true`
- `regime_bundle_bbn_application_status=applied`
- `read_only_regime_bbn_decision_state=single_label_95`
- `read_only_regime_bbn_label=primary::ExtremeStress`
- `read_only_regime_bbn_soft_evidence_weight=0.650`
- branch path retained in BBN label set: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`

This is BBN-consumable soft evidence, not a production promotion, because Pre-Bayes remains neutralized and the production source/control plus explicit selected-history gates are still unsatisfied.

## CatBoost / Path-Ranking Readback

`policy-training-status` reports entry-model training is not ready for BBN/CatBoost entry modules:
- `cisd_rb_long_v1`: `matched_rows=0`
- `breaker_rb_long_v1`: `matched_rows=0`

The structural path-ranking side is ready:
- runtime `enabled_candidate_set_ready`
- trainer artifact ready
- trainer artifact model family `catboost`
- trainer artifact trained rows `12329`
- calibration evaluated
- raw-scored mature rows `288/30`
- production validation rows `286/30`
- observation validation rows `48/30`

`export-structural-path-ranking-target` reports:
- rows `6`
- mature rows `4`
- history rows `295`
- history mature rows `288`
- rows with raw path score `4`
- rows with calibrated path probability `3`

## Execution Candidate / Execution Tree Readback

`workflow-status --phase structural-recommended-path-bundle` preserves:
- path `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- `path_ranker_runtime_source=history_path`
- `path_ranker_raw_score=0.65`

`workflow-status --phase execution-candidate` reports:
- path `structural-recommended-path-bundle:Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- `candidate_status=execution_observe_only`
- `execution_gate_status=execution_observe_only`
- `execution_readiness=0.4504361163104953`
- `pre_bayes_gate_status=pass_neutralized`
- `review_status=observe`
- `ready=false`

`artifact-status --latest-only` confirms the persisted execution-tree artifact remains `status=observe`, `promote_candidate=false`.

## Decision

Gate: `post_093937_full_chain_readback_v1=non_promoting_chain_exercised_observe_only_autoquant_prepare_required`.

The requested chain was exercised on a copied state through provider status, Auto-Quant status/adoption, Pre-Bayes, BBN soft evidence, CatBoost/path-ranking status/export, workflow structural bundle/feedback, and execution candidate surfaces.

The run does not satisfy Board A completion:
- accepted rows added: `0`
- new 95% root acceptance: `false`
- explicit selected-history approval: `false`
- R6/R5/R3 source/control unlock: `false`
- canonical merge: `false`
- selected-data Auto-Quant promotion: `false`
- downstream promotion: `false`
- trade usable: `false`
- `update_goal=false`

## Next

Do not repeat the same LTF/HTF no-data or Auto-Quant prepare-missing loop unless a new provider cache, source/control artifact, dependency repair, or explicit selected-history decision changes the evidence surface. Keep using the recorded-MTF branch only as non-promoting search feedback until Board A production unlock gates are real.
