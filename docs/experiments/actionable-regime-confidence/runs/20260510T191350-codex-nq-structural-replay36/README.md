# NQ Structural Replay36 CatBoost Closure

This run continues Board A after `SessionLiquidityCoreViable` reached accepted_95. It does not claim a tradable strategy.

Key result: policy training now reports CatBoost structural path-ranker validation ready: Ranker validation: calibration=true quality_ready=true raw_scored_mature=1397/30 production_validation=1395/30 observation_validation=40/30 ready=true

CatBoost model: `catboost/path_ranker_model/catboost_model.cbm` trained on 1397 mature rows using ['structural_baseline_score'].

Latest evidence packet: `evidence_packet_structural_replay36_catboost_closure.json`.

Mid-run files named `replay36_*` and `evidence_packet_structural_replay36_validation.json` are earlier snapshots before CatBoost scores were fully applied; the catboost closure packet supersedes them.

Post-audit additions:
- BBN apply artifact: `ict-engine/16_auto_quant_prior_init_nq_apply.json` (`dry_run=false`).
- Post-BBN readbacks: `ict-engine/17_pre_bayes_status_after_bbn_apply_nq.json`, `ict-engine/18_policy_training_status_after_bbn_apply_nq_agent.json`, `ict-engine/19_workflow_status_after_bbn_apply_nq_agent.json`, `ict-engine/20_execution_tree_trace_after_bbn_apply_nq.json`.
- Completion audit: `completion_audit_prompt_to_artifact.json`.
- Final readbacks: `ict-engine/21_provider_status_final_readback_agent.json`, `ict-engine/22_workflow_phase_structural_recommended_path_bundle_final_agent.json`, `ict-engine/23_workflow_phase_structural_validation_final_agent.json`.
