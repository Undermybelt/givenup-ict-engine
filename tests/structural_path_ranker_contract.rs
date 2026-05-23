use ict_engine::application::entry_models::training_export::structural_path_ranking_target_training_status;
use ict_engine::application::entry_models::{
    apply_structural_path_ranking_external_scores_command_with_format,
    enable_structural_path_ranking_runtime_command,
    register_structural_path_ranking_trainer_artifact_command, POLICY_TRAINING_DIR,
};
use ict_engine::application::orchestration::{
    STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
    STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE,
};
use ict_engine::belief_core::ranking_label::{
    structural_path_ranking_trainer_manifest, StructuralPathRankingTargetExportSummary,
    StructuralPathRankingTargetRow, STRUCTURAL_PATH_RANKER_EXPLICIT_FAMILY_CORELS,
};

const SYMBOL: &str = "NQ";
const CANDIDATE_SET_ID: &str = "structural-candidates:NQ:contract";
const PATH_ID: &str = "path:scenario:NQ:contract:trend-follow-through:primary";

fn contract_row(path_id: &str) -> StructuralPathRankingTargetRow {
    StructuralPathRankingTargetRow {
        rank: 1,
        candidate_set_id: CANDIDATE_SET_ID.to_string(),
        candidate_set_size: 1,
        path_id: path_id.to_string(),
        scenario_id: format!("scenario:{path_id}"),
        path_label: path_id.to_string(),
        direction: "long".to_string(),
        pending_reward_state: "matured_success".to_string(),
        maturity_mask: true,
        maturity_weight: 1.0,
        calibrated_label: Some(1.0),
        propensity_estimate: Some(0.5),
        ips_weight: Some(2.0),
        training_weight: Some(2.0),
        regime_calibration_bucket: "trend".to_string(),
        behavior_policy_probability: 0.5,
        experience_prior: 0.5,
        current_posterior: 0.5,
        structural_baseline_score: 0.5,
        ..StructuralPathRankingTargetRow::default()
    }
}

fn write_contract_target(temp: &tempfile::TempDir) {
    let policy_dir = temp.path().join(SYMBOL).join(POLICY_TRAINING_DIR);
    std::fs::create_dir_all(&policy_dir).unwrap();
    let current_jsonl = policy_dir.join("structural_path_ranking_target.jsonl");
    let history_jsonl = policy_dir.join("structural_path_ranking_target_history.jsonl");
    let current_csv = policy_dir.join("structural_path_ranking_target.csv");
    let history_csv = policy_dir.join("structural_path_ranking_target_history.csv");
    let summary_path = policy_dir.join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    let row = contract_row(PATH_ID);
    let jsonl = format!("{}\n", serde_json::to_string(&row).unwrap());
    std::fs::write(&current_jsonl, &jsonl).unwrap();
    std::fs::write(&history_jsonl, &jsonl).unwrap();
    std::fs::write(&current_csv, "candidate_set_id,path_id,raw_path_score\n").unwrap();
    std::fs::write(&history_csv, "candidate_set_id,path_id,raw_path_score\n").unwrap();
    let summary = StructuralPathRankingTargetExportSummary {
        symbol: SYMBOL.to_string(),
        rows: 1,
        candidate_set_id: CANDIDATE_SET_ID.to_string(),
        candidate_set_size: 1,
        mature_rows: 1,
        rows_with_training_weight: 1,
        rows_with_propensity_estimate: 1,
        csv_path: current_csv.to_string_lossy().to_string(),
        jsonl_path: current_jsonl.to_string_lossy().to_string(),
        history_csv_path: history_csv.to_string_lossy().to_string(),
        history_jsonl_path: history_jsonl.to_string_lossy().to_string(),
        history_rows: 1,
        history_mature_rows: 1,
        history_rows_with_training_weight: 1,
        history_rows_with_propensity_estimate: 1,
        trainer_manifest: structural_path_ranking_trainer_manifest(),
        summary_path: summary_path.to_string_lossy().to_string(),
        summary_line: "structural_path_ranking_target rows=1 history_rows=1".to_string(),
        ..StructuralPathRankingTargetExportSummary::default()
    };
    std::fs::write(
        summary_path,
        serde_json::to_string_pretty(&summary).unwrap(),
    )
    .unwrap();
}

#[test]
fn structural_path_ranker_apply_updates_fixture_scores() {
    let temp = tempfile::tempdir().unwrap();
    write_contract_target(&temp);
    let scores = temp.path().join("scores.csv");
    std::fs::copy(
        "tests/fixtures/policy_training/structural_path_ranking_scores.csv",
        &scores,
    )
    .unwrap();

    apply_structural_path_ranking_external_scores_command_with_format(
        temp.path().to_str().unwrap(),
        SYMBOL,
        scores.to_str().unwrap(),
        "human",
    )
    .unwrap();

    let updated_jsonl = temp
        .path()
        .join(SYMBOL)
        .join(POLICY_TRAINING_DIR)
        .join("structural_path_ranking_target.jsonl");
    let updated_rows = std::fs::read_to_string(updated_jsonl)
        .unwrap()
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(serde_json::from_str::<StructuralPathRankingTargetRow>)
        .collect::<Result<Vec<_>, _>>()
        .unwrap();
    assert_eq!(updated_rows.len(), 1);
    assert_eq!(updated_rows[0].path_id, PATH_ID);
    assert_eq!(updated_rows[0].raw_path_score, Some(0.87));
}

#[test]
fn structural_path_ranker_fixture_chain_registers_and_enables_runtime_source() {
    let temp = tempfile::tempdir().unwrap();
    write_contract_target(&temp);
    let scores = temp.path().join("scores.csv");
    std::fs::copy(
        "tests/fixtures/policy_training/structural_path_ranking_scores.csv",
        &scores,
    )
    .unwrap();

    apply_structural_path_ranking_external_scores_command_with_format(
        temp.path().to_str().unwrap(),
        SYMBOL,
        scores.to_str().unwrap(),
        "compact",
    )
    .unwrap();
    register_structural_path_ranking_trainer_artifact_command(
        temp.path().to_str().unwrap(),
        SYMBOL,
        scores.to_str().unwrap(),
        "catboost",
        Some("raw_path_score"),
        Some(1),
        Some(1),
    )
    .unwrap();
    enable_structural_path_ranking_runtime_command(
        temp.path().to_str().unwrap(),
        SYMBOL,
        STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY,
    )
    .unwrap();

    let status =
        structural_path_ranking_target_training_status(temp.path().to_str().unwrap(), SYMBOL)
            .unwrap();
    assert_eq!(
        status.runtime_selection_status,
        "enabled_registered_artifact_ready"
    );
    assert_eq!(
        status.runtime_source_kind.as_deref(),
        Some("registered_artifact")
    );
    assert_eq!(status.runtime_artifact_match_count, 1);
    assert_eq!(status.runtime_active_match_count, 1);
    assert_eq!(
        status.trainer_artifact_model_family.as_deref(),
        Some("catboost")
    );
    assert_eq!(
        status.score_source_kind.as_deref(),
        Some("external_artifact")
    );
    assert!(status
        .summary_line
        .contains("runtime_source=registered_artifact"));
}

#[test]
fn structural_path_ranker_apply_missing_scores_file_has_recovery_context() {
    let temp = tempfile::tempdir().unwrap();
    write_contract_target(&temp);
    let missing = temp.path().join("missing_scores.csv");

    let err = apply_structural_path_ranking_external_scores_command_with_format(
        temp.path().to_str().unwrap(),
        SYMBOL,
        missing.to_str().unwrap(),
        "human",
    )
    .unwrap_err()
    .to_string();

    assert!(err.contains("scores file"), "err={err}");
    assert!(err.contains(missing.to_str().unwrap()), "err={err}");
    assert!(
        err.contains("candidate_set_id,path_id,raw_path_score"),
        "err={err}"
    );
    assert!(
        err.contains("export-structural-path-ranking-target"),
        "err={err}"
    );
}

#[test]
fn structural_path_ranker_apply_malformed_scores_file_has_schema_context() {
    let temp = tempfile::tempdir().unwrap();
    write_contract_target(&temp);
    let malformed = temp.path().join("malformed_scores.csv");
    std::fs::write(
        &malformed,
        "candidate_set_id,raw_path_score\ncontract,0.87\n",
    )
    .unwrap();

    let err = apply_structural_path_ranking_external_scores_command_with_format(
        temp.path().to_str().unwrap(),
        SYMBOL,
        malformed.to_str().unwrap(),
        "human",
    )
    .unwrap_err()
    .to_string();

    assert!(err.contains("scores file"), "err={err}");
    assert!(err.contains(malformed.to_str().unwrap()), "err={err}");
    assert!(err.contains("path_id"), "err={err}");
    assert!(
        err.contains("candidate_set_id,path_id,raw_path_score"),
        "err={err}"
    );
}

#[test]
fn structural_path_ranker_register_missing_target_export_has_recovery_context() {
    let temp = tempfile::tempdir().unwrap();

    let err = register_structural_path_ranking_trainer_artifact_command(
        temp.path().to_str().unwrap(),
        SYMBOL,
        "s3://rankers/nq-path-ranker-v1.bin",
        "catboost",
        Some("raw_path_score"),
        Some(1),
        Some(1),
    )
    .unwrap_err()
    .to_string();

    assert!(err.contains("target export"), "err={err}");
    assert!(
        err.contains(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE),
        "err={err}"
    );
    assert!(
        err.contains("export-structural-path-ranking-target"),
        "err={err}"
    );
}

#[test]
fn structural_path_ranker_register_malformed_summary_has_schema_context() {
    let temp = tempfile::tempdir().unwrap();
    let policy_dir = temp.path().join(SYMBOL).join(POLICY_TRAINING_DIR);
    std::fs::create_dir_all(&policy_dir).unwrap();
    let summary_path = policy_dir.join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    std::fs::write(&summary_path, "{not-json").unwrap();

    let err = register_structural_path_ranking_trainer_artifact_command(
        temp.path().to_str().unwrap(),
        SYMBOL,
        "s3://rankers/nq-path-ranker-v1.bin",
        "catboost",
        Some("raw_path_score"),
        Some(1),
        Some(1),
    )
    .unwrap_err()
    .to_string();

    assert!(err.contains("target export summary"), "err={err}");
    assert!(err.contains(summary_path.to_str().unwrap()), "err={err}");
    assert!(err.contains("structural_path_ranking_target"), "err={err}");
    assert!(
        err.contains("export-structural-path-ranking-target"),
        "err={err}"
    );
}

#[test]
fn structural_path_ranker_register_malformed_explicit_artifact_has_recovery_context() {
    let temp = tempfile::tempdir().unwrap();
    write_contract_target(&temp);
    let malformed_artifact = temp.path().join("corels-artifact.json");
    std::fs::write(&malformed_artifact, "{not-json").unwrap();

    let err = register_structural_path_ranking_trainer_artifact_command(
        temp.path().to_str().unwrap(),
        SYMBOL,
        malformed_artifact.to_str().unwrap(),
        STRUCTURAL_PATH_RANKER_EXPLICIT_FAMILY_CORELS,
        Some("raw_path_score"),
        Some(1),
        Some(1),
    )
    .unwrap_err()
    .to_string();

    assert!(err.contains("trainer artifact"), "err={err}");
    assert!(
        err.contains(malformed_artifact.to_str().unwrap()),
        "err={err}"
    );
    assert!(err.contains("rule_list or tree_json"), "err={err}");
    assert!(
        err.contains("register-structural-path-ranking-trainer-artifact"),
        "err={err}"
    );
}
