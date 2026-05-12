finished_at=2026-05-12T07:51:29+08:00
board_a_sha_after=2f3b3ec0acc69df4fb5a3ae1a60f5abd45befc7db4d4c1a6977c8fee83196c1e
board_b_sha_after=04d3bbb170a0022f0b92479b01bf7361d04355f50ccafef998036b65b3e8cac9

exits
01_provider_status_agent.exit=0
02_auto_quant_status_compact.exit=0
03_workflow_status_agent.exit=0
04_pre_bayes_status_compact.exit=0
05_export_structural_path_ranking_target.exit=0

provider
{
  "summary_line": "entry_model:2/2 ready | live_runtime:1/3 ready | local_runtime:1/2 ready | market_data:1/7 ready",
  "ready_by_domain": {
    "entry_model": "2/2",
    "live_runtime": "1/3",
    "local_runtime": "1/2",
    "market_data": "1/7"
  },
  "providers": [
    {
      "provider_id": "breaker_rb_long_v1",
      "domain": "entry_model",
      "selectable_by_user": false,
      "adopted_by_default": false,
      "ready": true,
      "access_mode": "internal_model_registry",
      "user_access": "builtin_registry",
      "market_fit": [
        "entry_model"
      ],
      "status": "registered",
      "reason": "entry_model_registry_member",
      "summary": "Built-in entry-model registry member used by status and training surfaces."
    },
    {
      "provider_id": "cisd_rb_long_v1",
      "domain": "entry_model",
      "selectable_by_user": false,
      "adopted_by_default": false,
      "ready": true,
      "access_mode": "internal_model_registry",
      "user_access": "builtin_registry",
      "market_fit": [
        "entry_model"
      ],
      "status": "registered",
      "reason": "entry_model_registry_member",
      "summary": "Built-in entry-model registry member used by status and training surfaces."
    },
    {
      "provider_id": "crypto_public_runtime",
      "domain": "live_runtime",
      "selectable_by_user": true,
      "adopted_by_default": false,
      "ready": false,
      "access_mode": "public_runtime_bundle",
      "user_access": "operator_runtime_optional",
      "market_fit": [
        "crypto"
      ],
      "fallback_priority": 21,
      "status": "operator_runtime_required",
      "reason": "explicit_opt_in_required",
      "summary": "Optional crypto-public runtime bundle for CoinAnk/Hyperliquid-style futures observation when the user explicitly wants that lane.",
      "install_prompts": [
        "Consumer agent request: ask whether the user wants zero-config yfinance or the optional crypto_public_runtime lane."
      ]
    },
    {
      "provider_id": "external_http_runtime",
      "domain": "live_runtime",
      "selectable_by_user": true,
      "adopted_by_default": false,
      "ready": false,
      "access_mode": "external_http_runtime",
      "user_access": "operator_runtime_optional",
      "market_fit": [
        "tradfi",
        "crypto"
      ],
      "fallback_priority": 20,
      "status": "operator_runtime_required",
      "reason": "base_url_and_service_required",
      "summary": "Optional external HTTP runtime when the user already has a compatible market-data service.",
      "install_prompts": [
        "Consumer agent request: ask whether the user wants zero-config yfinance or a generic external HTTP runtime.",
        "Consumer agent follow-up: if the user chooses the external HTTP runtime, keep the external_http_runtime backend and pass --external-http-base-url <url> (default http://127.0.0.1:6901/api/v1)."
      ]
    },
    {

auto_quant
{
  "bootstrap_needed": false,
  "data_ready": false,
  "dependency_healthy": true,
  "healthy": false,
  "notes": [],
  "recommended_next_command": "ict-engine auto-quant-prepare --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/auto-quant",
  "status": "dependency_ready_data_missing",
  "summary_line": "auto_quant_status dependency_ready_data_missing healthy=false dependency_healthy=true data_ready=false bootstrap_needed=false update_available=false",
  "update_available": false
}

workflow
{
  "auto_quant_handoff": null,
  "available_opt_in_profiles": [],
  "blocking_reason": "user_selected_historical_data_missing",
  "blocking_status": "blocked",
  "closed_loop_branch_admission": {
    "actionable": false,
    "candidate_status": "execution_blocked",
    "evidence": [
      "pre_bayes_gate_status=observe_only",
      "execution_gate_status=execution_blocked",
      "review_status=observe"
    ],
    "execution_gate_status": "execution_blocked",
    "path_id": "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72",
    "path_label": "Manipulation(scoped) -> TelegramPumpEvent -> ProviderStopTakeShort -> ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72",
    "pre_bayes_gate_status": "observe_only",
    "ready": false,
    "reason": "exact_structural_branch_visible_but_not_ready_or_actionable",
    "review_status": "observe",
    "source_phase": "structural-recommended-path-bundle",
    "status": "fail_closed"
  },
  "dataset_resolution_line": null,
  "ensemble": {
    "confidence": 0.3993185754313692,
    "consensus_strength": 0.3993185754313692,
    "executor_scorecard_source": "persisted",
    "final_action": "Observe",
    "hard_block_active": false,
    "hard_block_reason": null,
    "recommended_command": "ask-user: Before using historical data for B2R_NQ_COST_CRISIS_REPAIR_032157 again, ask the user which dataset to use. recorded_paths=docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_htf.json, docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_mtf.json, docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_ltf.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol B2R_NQ_COST_CRISIS_REPAIR_032157 --data docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/analyze_nq_ltf.json --state-dir docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1",
    "top_executor": {
      "executor": "catboost_file",
      "latest_weight_hint": 0.55,
      "wins": 0
    }
  },
  "evidence_review": null,
  "experience_prior_surface": {
    "branch": {
      "composite_score": 0.3528704545302174,
      "current_posterior": 0.3528704545302174,
      "entity_id": "B2R_NQ_COST_CRISIS_REPAIR_032157:belief_regime_node:range:range_mean_reversion",
      "entity_kind": "branch",
      "experience_prior": 0.3528704545302174,
      "historical_followed_count": 0,
      "historical_total_records": 0,
      "source_panel_count": 0
    },
    "node": {
      "composite_score": 0.3220093181711522,
      "current_posterior": 0.3528704545302174,
      "entity_id": "B2R_NQ_COST_CRISIS_REPAIR_032157:belief_regime_node:range",
      "entity_kind": "node",
      "experience_prior": 0.25,
      "historical_followed_count": 0,
      "historical_total_records": 0,
      "source_panel_count": 0
    },
    "path": {
      "composite_score": 0.9,
      "current_posterior": 0.9,
      "entity_id": "Bear -> BearMarketDrawdown -> NQHighVixOversoldRebound -> NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72",
      "entity_kind": "path",
      "experience_prior": 0.9,
      "historical_followed_count": 0,
      "historical_total_records": 0,
      "source_panel_count": 0
    },
    "scenario": {
      "composite_score": 0.3528704545302174,
      "current_posterior": 0.3528704545302174,
      "entity_id": "scenario:B2R_NQ_COST_CRISIS_REPAIR_032157:belief_regime_node:range:range_mean_reversion",
      "entity_kind": "scenario",
      "experience_prior": 0.3528704545302174,
      "historical_followed_count": 0,
      "historical_total_records": 0,
      "source_panel_count": 0
    },
    "source_reliability_em": {
      "candidate_item_count": 1,
      "conflict_item_count": 0,
      "consensus_item_count": 0,
      "distinct_source_count": 1,
      "em_calibration_min_observations": 0,
      "em_calibration_observation_count": 0,
      "em_calibration_source_count": 0,
      "em_confusion_cell_count": 0,
      "em_distinct_label_count": 0,
      "em_holdout_evaluation_item_count": 0,
      "em_holdout_min_observations": 0,
      "em_holdout_min_training_items": 4,
      "em_holdout_observation_count": 0,
      "em_holdout_source_count": 0,
      "em_holdout_split_strategy": null,
      "em_holdout_training_item_count": 0,
      "em_iteration_count": 0,
      "em_latent_item_count": 0,
      "em_replay_evaluation_item_count": 0,
      "em_replay_observation_count": 0,
      "em_replay_source_count": 0,
      "labeled_item_count": 1,
      "max_sources_per_item": 1,
      "min_multi_source_items": 3,
      "multi_source_item_count": 0,
      "observed_label_count": 1,
      "persisted_confusion_cell_count": 0,
      "persisted_source_summary_count": 0,
      "ready": false,
      "status": "needs_multiple_sources"
    },
    "symbol": "B2R_NQ_COST_CRISIS_REPAIR_032157"
  },
  "first_run_router": null,
  "focus_phase": "analyze",
  "focus_reason": "market_policy=B2R hostile_liquidity_penalty=0.100 favorable_liquidity_bonus=0.050 hostile_liquidity_forces_high_uncertainty=true;multi_timeframe_direction_bias=bullish multi_timeframe_alignment_score=0.869 multi_timeframe_entry_alignment_score=0.994;long/short support gap 0.070 is too small, so alignment is treated as mixed;multi-timeframe direction bias 'bullish' conflicts with regime/alignment, so factor_alignment is neutralized;evidence quality is too low, so BBN input is downgraded to neutralized defaults;pre_bayes_quality_score=0.399 gating_status=observe_only;market_state_source=primary_regime=TrendExpansion secondary_regime=BullTrendAcceleration overall_confidence=0.629;market_state_source=volatility=ElevatedVol:0.664 liquidity=NormalLiquidity:0.363 structure=Trending:0.589 behavior=RiskOff:0.550;market_state_source=rationale=volatility=ElevatedVol conf=0.66;market_state_source=rationale=structure=Trending conf=0.59;market_state_source=rationale=behavior=RiskOff conf=0.55;market_state_source=rationale=primary=TrendExpansion secondary=BullTrendAcceleration overall=0.63;read_only_regime_bbn_soft_evidence_strength=moderate;read_only_regime_bbn_soft_evidence_weight=0.650;read_only_regime_bbn_decision_state=accepted;read_only_regime_bbn_trade_usable=true;read_only_regime_bbn_label=NQRootAdaptiveCostCrisisRepairV3;read_only_regime_bbn_label_set=Bull_->_TrendExpansion_->_NQSourceRootCarry_->_NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72,Bear_->_BearMarketDrawdown_->_NQHighVixOversoldRebound_->_NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72,Sideways_->_RangeConsolidation_->_NQCalmVixZReversion_->_NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72,Crisis_->_ExtremeStress_->_NQFlushRebound_->_NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72,Manipulation(scoped)_->_TelegramPumpEvent_->_ProviderStopTakeShort_->_ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72;read_only_regime_bbn_transition_hazard=0.000;read_only_regime_bbn_reasons=branch_rc_spa_all_price_roots_passed,scoped_manipulation_component_passed;regime_bundle_bbn_evidence_skipped=no_supported_label",
  "generated_at": "2026-05-11T23:51:17.047168Z",
  "hard_block_active": true,
  "hybrid_duration_model": "geometric",

pre_bayes
{
  "latest_bridge": {
    "long_entry_bias": [
      0.18348470606559952,
      0.48491861994126273,
      0.33159667399313775
    ],
    "long_entry_quality": {
      "high": 0.0,
      "low": 0.0,
      "medium": 1.0
    },
    "long_signal_probability": 0.5361933770026824,
    "multi_timeframe_alignment_score": 0.8691,
    "multi_timeframe_direction_bias": "bullish",
    "multi_timeframe_entry_alignment_score": 0.9938,
    "rationale": [
      "factor_alignment=mixed factor_uncertainty=low",
      "long_support=0.035 short_support=0.105 uncertainty=0.302",
      "multi_timeframe_direction_bias=bullish multi_timeframe_alignment_score=0.869 multi_timeframe_entry_alignment_score=0.994",
      "entry_quality_bias combines directional factor support with cascade probability bias"
    ],
    "selected_entry_quality": {
      "high": 0.0,
      "low": 0.0,
      "medium": 1.0
    },
    "short_entry_bias": [
      0.08068807056701656,
      0.32244007039769523,
      0.596871859035288
    ],
    "short_entry_quality": {
      "high": 0.0,
      "low": 0.0,
      "medium": 1.0
    },
    "short_signal_probability": 0.5531263706210107
  },
  "latest_bridge_diff": {
    "dominant_long_entry_quality": "medium",
    "dominant_long_entry_quality_probability": 1.0,
    "dominant_short_entry_quality": "medium",
    "dominant_short_entry_quality_probability": 1.0,
    "long_short_signal_probability_gap": 0.01693299361832823,
    "multi_timeframe_alignment_score": 0.8691,
    "multi_timeframe_direction_bias": "bullish",
    "multi_timeframe_entry_alignment_score": 0.9938,
    "rationale_summary": [
      "factor_alignment=mixed factor_uncertainty=low",
      "long_support=0.035 short_support=0.105 uncertainty=0.302",
      "multi_timeframe_direction_bias=bullish multi_timeframe_alignment_score=0.869 multi_timeframe_entry_alignment_score=0.994",
      "entry_quality_bias combines directional factor support with cascade probability bias"
    ],
    "selected_entry_quality": "medium",
    "selected_entry_quality_probability": 1.0
  },
  "latest_canonical_structural_active_regime": "range",
  "latest_canonical_structural_confidence": 0.3993185754313692,
  "latest_canonical_structural_probabilities": {
    "range": 0.3528704545302174,
    "stress": 0.1766356060961594,
    "transition": 0.23524696968681164,
    "trend": 0.23524696968681164
  },
  "latest_filtered_assignments": {
    "__policy_version": "318900600c5e8cf2",
    "factor_alignment": "mixed",
    "factor_uncertainty": "high",
    "liquidity_context": "neutral",
    "market_regime": "range",
    "market_state_primary_regime": "TrendExpansion",
    "market_state_secondary_regime": "BullTrendAcceleration",
    "multi_timeframe_resonance": "mixed",
    "read_only_regime_bbn_decision_state": "accepted",
    "read_only_regime_bbn_label": "NQRootAdaptiveCostCrisisRepairV3",
    "read_only_regime_bbn_label_set": "Bull_->_TrendExpansion_->_NQSourceRootCarry_->_NQRootAdaptiveCostCrisisRepairV3:bull_source_root_carry_h72,Bear_->_BearMarketDrawdown_->_NQHighVixOversoldRebound_->_NQRootAdaptiveCostCrisisRepairV3:bear_oversold_high_vix_rebound_h72,Sideways_->_RangeConsolidation_->_NQCalmVixZReversion_->_NQRootAdaptiveCostCrisisRepairV3:sideways_calm_vix_z_revert_h72,Crisis_->_ExtremeStress_->_NQFlushRebound_->_NQRootAdaptiveCostCrisisRepairV3:crisis_flush_rebound_h72,Manipulation(scoped)_->_TelegramPumpEvent_->_ProviderStopTakeShort_->_ManipulationStopTakeProfitGridV2:short_tp120_sl060_h72",
    "read_only_regime_bbn_reasons": "branch_rc_spa_all_price_roots_passed,scoped_manipulation_component_passed",
    "read_only_regime_bbn_soft_evidence_strength": "moderate",
    "read_only_regime_bbn_soft_evidence_weight": "0.650",

path_target
{
  "symbol": "B2R_NQ_COST_CRISIS_REPAIR_032157",
  "rows": 5,
  "candidate_set_id": "structural-candidates:B2R_NQ_COST_CRISIS_REPAIR_032157:fa87f88e4639b05f",
  "candidate_set_size": 5,
  "pending_reward_states": {
    "unobserved": 5
  },
  "mature_rows": 0,
  "rows_with_raw_path_score": 5,
  "rows_with_calibrated_path_prob": 0,
  "rows_with_path_prob_lower_bound": 0,
  "rows_with_propensity_estimate": 5,
  "rows_with_execution_gate_status": 0,
  "rows_with_training_weight": 0,
  "csv_path": "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target.csv",
  "jsonl_path": "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target.jsonl",
  "history_csv_path": "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target_history.csv",
  "history_jsonl_path": "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target_history.jsonl",
  "history_rows": 10,
  "history_mature_rows": 0,
  "history_rows_with_raw_path_score": 10,
  "history_rows_with_calibrated_path_prob": 0,
  "history_rows_with_path_prob_lower_bound": 0,
  "history_rows_with_propensity_estimate": 10,
  "history_rows_with_training_weight": 0,
  "summary_path": "docs/experiments/actionable-regime-confidence/runs/20260512T032157-codex-board-b-nq-cost-crisis-repair-v3/downstream-combined-v1/state_combined_v1/B2R_NQ_COST_CRISIS_REPAIR_032157/policy_training/structural_path_ranking_target_summary.json",
  "trainer_manifest": {
    "protocol_version": "structural-path-ranking-trainer-manifest-v1",
    "dataset_role": "external_path_ranker_training_dataset",
    "group_id_column": "candidate_set_id",
    "label_column": "calibrated_label",
    "weight_column": "training_weight",
    "maturity_column": "maturity_mask",
    "raw_score_column": "raw_path_score",
    "feature_columns": [
      "rank",
      "direction",
      "regime_calibration_bucket",
      "behavior_policy_probability",
      "execution_propensity",
      "target_policy_probability_confidence",
      "target_policy_probability_lower_bound",
      "target_policy_reward_prior",
      "target_policy_reward_lower_bound",
      "experience_prior",
      "current_posterior",
      "structural_baseline_score"
    ],
    "calibration_columns": [
      "calibrated_path_prob",
      "path_prob_lower_bound",
      "execution_gate_status"
    ],
    "guardrail_columns": [
      "candidate_set_size",
      "path_id",
      "scenario_id",
      "pending_reward_state",
      "maturity_weight",
      "propensity_estimate",
      "ips_weight"
    ],
    "notes": [
      "Trainer runs outside the Rust belief engine; this manifest only describes exported columns.",
      "Rows without calibrated_label or training_weight are censored/unusable for supervised ranker loss."
    ]
  },
  "summary_line": "structural_path_ranking_target rows=5 history_rows=10 candidate_set_size=5 mature_rows=0 history_mature_rows=0 propensity_rows=5 calibrated_rows=0 execution_gate_rows=0 training_weight_rows=0"
}
