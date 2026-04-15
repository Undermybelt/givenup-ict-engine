use super::*;

#[test]
fn catboost_policy_engine_loads_sample_artifact() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src/application/orchestration/catboost_policy.sample.json");
    let engine = CatBoostCompatiblePolicyEngine::load_from_file(&path).unwrap();
    assert_eq!(engine.artifact_version(), "catboost-policy-v1-sample");
    assert_eq!(engine.model_artifact.model_family, "catboost");
    assert_eq!(
        engine.model_artifact.feature_schema_version,
        "policy_features_v1"
    );
}

#[test]
fn catboost_policy_engine_infer_uses_loaded_artifact_version() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src/application/orchestration/catboost_policy.sample.json");
    let engine = CatBoostCompatiblePolicyEngine::load_from_file(&path).unwrap();
    let decision = engine.infer(&PolicyFeatureVector {
        factor_alignment: "mixed".to_string(),
        factor_uncertainty: "low".to_string(),
        gating_status: "trend".to_string(),
        selected_entry_quality: "medium".to_string(),
        recommended_command: "update".to_string(),
        evidence_quality_score: 0.82,
        selected_direction: "Bull".to_string(),
        risk_reward: 2.4,
        kelly_fraction: 0.12,
    });
    assert_eq!(decision.policy_version, "catboost-policy-v1-sample");
    assert_eq!(decision.qualification, "qualified");
    assert_eq!(decision.action, "Bull");
    assert_eq!(decision.leaf_id, "qualified-bull");
    assert!(decision.recommended_command.contains("ict-engine update"));
}

#[test]
fn catboost_policy_engine_falls_back_when_feature_conditions_do_not_match() {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src/application/orchestration/catboost_policy.sample.json");
    let engine = CatBoostCompatiblePolicyEngine::load_from_file(&path).unwrap();
    let decision = engine.infer(&PolicyFeatureVector {
        factor_alignment: "bearish".to_string(),
        factor_uncertainty: "low".to_string(),
        gating_status: "transition".to_string(),
        selected_entry_quality: "low".to_string(),
        recommended_command: "update".to_string(),
        evidence_quality_score: 0.82,
        selected_direction: "Bull".to_string(),
        risk_reward: 2.4,
        kelly_fraction: 0.12,
    });
    assert_ne!(decision.leaf_id, "qualified-bull");
}

#[test]
fn catboost_policy_engine_load_default_or_placeholder_prefers_file() {
    let engine = CatBoostCompatiblePolicyEngine::load_default_or_placeholder();
    assert_eq!(engine.artifact_version(), "catboost-policy-v1-sample");
}
