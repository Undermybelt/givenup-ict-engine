pub mod debug_report;
pub mod jump_model_sidecar;
pub mod logic_family;
pub mod pipeline_builder;
pub mod pipeline_shared;
pub mod pipeline_types;
pub mod policy_lineage_surface;
pub mod shadow_policy_surface;
pub mod shared;

pub use pipeline_builder::{
    adapt_factor_pipeline_debug_report, build_canonical_belief_report,
    build_canonical_belief_snapshot, build_expansion_factor_pipeline_report,
    build_expansion_factor_pipeline_report_with_registry, build_factor_pipeline_debug_report,
    infer_market_from_symbol, pre_bayes_evidence_policy, FactorPipelineDebugReport,
};
pub use pipeline_shared::{
    apply_factor_outcome_overlay, build_pre_bayes_entry_quality_bridge, combine_bias_vectors,
    effective_trade_outcome_win_probability, multi_timeframe_entry_quality_bias, probability_map,
    raw_liquidity_context_trace, raw_market_regime_trace, raw_multi_timeframe_resonance_trace,
};
pub use jump_model_sidecar::{
    build_jump_model_regime_sidecar, build_regime_disagreement_summary,
    jump_model_workflow_summary,
};
pub use pipeline_types::ExpansionFactorPipelineReport;
pub use policy_lineage_surface::{build_belief_policy_lineage_surface, BeliefPolicyLineageSurface};
pub use shadow_policy_surface::{build_belief_shadow_policy_surface, BeliefShadowPolicySurface};
