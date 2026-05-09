use ict_engine::application::regime::consumer_bundle_adapter::{
    BundleStatus, ExecutionTreeHint, RegimeConsumerBundleAdapter,
};
use serde_json::json;
use std::fs;

#[test]
fn disabled_adapter_is_noop_default() {
    let adapter = RegimeConsumerBundleAdapter::load_optional(None, false).unwrap();

    assert_eq!(adapter.status, BundleStatus::Disabled);
    assert!(!adapter.is_loaded());
    assert_eq!(adapter.execution_tree_hint(), ExecutionTreeHint::UnknownAbstain);
    assert!(adapter.bbn_evidence_hint().is_none());
}

#[test]
fn valid_bundle_loads_known_fields() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("regime_consumer_bundle.json");
    fs::write(
        &path,
        json!({
            "schema_version": "regime-consumer-bundle/v1",
            "latest_decision": {
                "decision_state": "single_label_99",
                "trade_usable": true,
                "final_label": "primary::TrendExpansion",
                "label_set": ["primary::TrendExpansion"],
                "abstain_reasons": []
            },
            "consumer_hints": {
                "execution_tree_hint": "accept_regime",
                "bbn_evidence_hint": {"regime_trade_usable": true},
                "path_ranker_context": {"regime_label": "primary::TrendExpansion"},
                "user_vrp_nq_context": {"qqq_hv_level": 0.22}
            }
        })
        .to_string(),
    )
    .unwrap();

    let adapter = RegimeConsumerBundleAdapter::load_optional(Some(&path), false).unwrap();

    assert_eq!(adapter.status, BundleStatus::Loaded);
    assert!(adapter.is_loaded());
    assert_eq!(adapter.execution_tree_hint(), ExecutionTreeHint::AcceptRegime);
    assert_eq!(adapter.latest_decision.as_ref().unwrap().decision_state, "single_label_99");
    assert!(adapter.latest_decision.as_ref().unwrap().trade_usable);
    assert!(adapter.bbn_evidence_hint().is_some());
}

#[test]
fn missing_bundle_non_strict_is_neutral_noop() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("missing.json");

    let adapter = RegimeConsumerBundleAdapter::load_optional(Some(&path), false).unwrap();

    assert_eq!(adapter.status, BundleStatus::Missing);
    assert!(!adapter.is_loaded());
    assert_eq!(adapter.execution_tree_hint(), ExecutionTreeHint::UnknownAbstain);
    assert!(adapter.error.as_ref().unwrap().contains("missing"));
}

#[test]
fn missing_bundle_strict_errors_before_state_mutation() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("missing.json");

    let err = RegimeConsumerBundleAdapter::load_optional(Some(&path), true).unwrap_err();

    assert!(err.to_string().contains("missing"));
}

#[test]
fn invalid_schema_non_strict_is_neutral_noop() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("invalid.json");
    fs::write(&path, json!({"schema_version": "wrong/v1"}).to_string()).unwrap();

    let adapter = RegimeConsumerBundleAdapter::load_optional(Some(&path), false).unwrap();

    assert_eq!(adapter.status, BundleStatus::Invalid);
    assert!(!adapter.is_loaded());
    assert_eq!(adapter.execution_tree_hint(), ExecutionTreeHint::UnknownAbstain);
}

#[test]
fn invalid_schema_strict_errors() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("invalid.json");
    fs::write(&path, json!({"schema_version": "wrong/v1"}).to_string()).unwrap();

    let err = RegimeConsumerBundleAdapter::load_optional(Some(&path), true).unwrap_err();

    assert!(err.to_string().contains("schema"));
}
