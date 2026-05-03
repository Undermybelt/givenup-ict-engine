use anyhow::Result;
use csv::StringRecord;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::Duration;

const STRUCTURAL_PATH_RANKING_RUNTIME_DIR: &str = "policy_training";

pub const STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_FILE: &str =
    "structural_path_ranking_runtime_selection.json";
pub const STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_PROTOCOL_VERSION: &str =
    "structural-path-ranking-runtime-selection-v1";
pub const STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY: &str =
    "candidate_set_only";
pub const STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY: &str = "prefer_history";

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankingRuntimeSelection {
    pub protocol_version: String,
    pub enabled: bool,
    pub reuse_mode: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub selected_at: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankerRuntimeSurface {
    pub enabled: bool,
    pub status: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reuse_mode: Option<String>,
    #[serde(default)]
    pub artifact_match_count: usize,
    #[serde(default)]
    pub candidate_set_match_count: usize,
    #[serde(default)]
    pub history_match_count: usize,
    #[serde(default)]
    pub applied_path_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankerRuntimeRow {
    pub candidate_set_id: String,
    pub path_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub raw_path_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub calibrated_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_prob_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_gate_status: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankingTrainerManifest {
    pub protocol_version: String,
    pub dataset_role: String,
    pub group_id_column: String,
    pub label_column: String,
    pub weight_column: String,
    pub maturity_column: String,
    pub raw_score_column: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub feature_columns: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub calibration_columns: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub guardrail_columns: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankingTargetExportSummary {
    pub symbol: String,
    pub rows: usize,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    pub pending_reward_states: BTreeMap<String, usize>,
    #[serde(default)]
    pub mature_rows: usize,
    pub rows_with_raw_path_score: usize,
    pub rows_with_calibrated_path_prob: usize,
    pub rows_with_path_prob_lower_bound: usize,
    pub rows_with_propensity_estimate: usize,
    #[serde(default)]
    pub rows_with_execution_gate_status: usize,
    #[serde(default)]
    pub rows_with_training_weight: usize,
    pub csv_path: String,
    pub jsonl_path: String,
    #[serde(default)]
    pub history_csv_path: String,
    #[serde(default)]
    pub history_jsonl_path: String,
    #[serde(default)]
    pub history_rows: usize,
    #[serde(default)]
    pub history_mature_rows: usize,
    #[serde(default)]
    pub history_rows_with_raw_path_score: usize,
    #[serde(default)]
    pub history_rows_with_calibrated_path_prob: usize,
    #[serde(default)]
    pub history_rows_with_path_prob_lower_bound: usize,
    #[serde(default)]
    pub history_rows_with_propensity_estimate: usize,
    #[serde(default)]
    pub history_rows_with_training_weight: usize,
    pub summary_path: String,
    #[serde(default)]
    pub trainer_manifest: StructuralPathRankingTrainerManifest,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathProbabilityCalibrationReport {
    pub status: String,
    pub observed_rows: usize,
    pub calibrated_rows: usize,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub bins: Vec<StructuralPathProbabilityCalibrationBin>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub warnings: Vec<String>,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathProbabilityCalibrationBin {
    pub regime_calibration_bucket: String,
    pub observations: usize,
    pub successes: usize,
    pub raw_path_score_min: f64,
    pub raw_path_score_max: f64,
    pub calibrated_path_prob: f64,
    pub path_prob_lower_bound: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathProbabilityCalibrationEvaluationReport {
    pub status: String,
    pub eligible_rows: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub brier_score: Option<f64>,
    #[serde(default)]
    pub propensity_weighted_rows: usize,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub propensity_weighted_brier_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub expected_calibration_error: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_calibration_error: Option<f64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub bins: Vec<StructuralPathProbabilityCalibrationEvaluationBin>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub warnings: Vec<String>,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathProbabilityCalibrationEvaluationBin {
    pub regime_calibration_bucket: String,
    pub observations: usize,
    pub mean_calibrated_path_prob: f64,
    pub empirical_success_rate: f64,
    pub absolute_error: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathRankingTargetArtifact {
    pub protocol_version: String,
    pub symbol: String,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    pub generated_at: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub rows: Vec<StructuralPathRankingTargetRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StructuralPathRankingTargetRow {
    pub rank: usize,
    pub candidate_set_id: String,
    pub candidate_set_size: usize,
    pub path_id: String,
    pub scenario_id: String,
    pub path_label: String,
    pub direction: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub raw_path_score: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub calibrated_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_prob_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_gate_status: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_gate_min_path_prob: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_gate_reason: Option<String>,
    pub pending_reward_state: String,
    #[serde(default)]
    pub maturity_mask: bool,
    #[serde(default)]
    pub maturity_weight: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub calibrated_label: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub propensity_estimate: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ips_weight: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub training_weight: Option<f64>,
    pub regime_calibration_bucket: String,
    pub behavior_policy_probability: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub execution_propensity: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_confidence: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_probability_lower_bound: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_reward_prior: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_policy_reward_lower_bound: Option<f64>,
    pub experience_prior: f64,
    pub current_posterior: f64,
    pub structural_baseline_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankingExternalScoreInput {
    pub candidate_set_id: String,
    pub path_id: String,
    pub raw_path_score: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
struct StructuralPathRankerRuntimeArtifactRef {
    #[serde(default)]
    protocol_version: String,
    #[serde(default)]
    dataset_role: String,
    #[serde(default)]
    artifact_uri: String,
    #[serde(default)]
    score_column: String,
}

pub fn structural_path_ranking_runtime_selection_path(state_dir: &str, symbol: &str) -> String {
    Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_RUNTIME_DIR)
        .join(STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_FILE)
        .to_string_lossy()
        .to_string()
}

pub fn load_structural_path_ranking_runtime_selection(
    state_dir: &str,
    symbol: &str,
) -> Option<StructuralPathRankingRuntimeSelection> {
    let path = structural_path_ranking_runtime_selection_path(state_dir, symbol);
    let raw = fs::read_to_string(path).ok()?;
    let selection = serde_json::from_str::<StructuralPathRankingRuntimeSelection>(&raw).ok()?;
    if selection.protocol_version.trim() != STRUCTURAL_PATH_RANKING_RUNTIME_SELECTION_PROTOCOL_VERSION
    {
        return None;
    }
    if !matches!(
        selection.reuse_mode.as_str(),
        STRUCTURAL_PATH_RANKING_RUNTIME_MODE_CANDIDATE_SET_ONLY
            | STRUCTURAL_PATH_RANKING_RUNTIME_MODE_PREFER_HISTORY
    ) {
        return None;
    }
    Some(selection)
}

fn structural_path_ranker_artifact_json_path(state_dir: &str, symbol: &str) -> PathBuf {
    Path::new(state_dir)
        .join(symbol)
        .join(STRUCTURAL_PATH_RANKING_RUNTIME_DIR)
        .join("structural_path_ranking_trainer_artifact.json")
}

pub fn load_structural_path_ranker_runtime_artifact_ref(
    state_dir: &str,
    symbol: &str,
) -> Option<(String, String)> {
    let path = structural_path_ranker_artifact_json_path(state_dir, symbol);
    let raw = fs::read_to_string(path).ok()?;
    let artifact = serde_json::from_str::<StructuralPathRankerRuntimeArtifactRef>(&raw).ok()?;
    if artifact.artifact_uri.trim().is_empty() || artifact.score_column.trim().is_empty() {
        return None;
    }
    Some((artifact.artifact_uri, artifact.score_column))
}

fn structural_path_ranker_artifact_uri_path(
    state_dir: &str,
    symbol: &str,
    artifact_uri: &str,
) -> Option<PathBuf> {
    let artifact_uri = artifact_uri.trim();
    if artifact_uri.is_empty() {
        return None;
    }
    if let Some(path) = artifact_uri.strip_prefix("file://") {
        return Some(PathBuf::from(path));
    }
    if artifact_uri.contains("://") {
        return None;
    }
    let path = Path::new(artifact_uri);
    if path.is_absolute() {
        Some(path.to_path_buf())
    } else {
        Some(
            Path::new(state_dir)
                .join(symbol)
                .join(STRUCTURAL_PATH_RANKING_RUNTIME_DIR)
                .join(path),
        )
    }
}

fn structural_path_ranker_runtime_source_kind(artifact_uri: &str) -> &'static str {
    let artifact_uri = artifact_uri.trim();
    if artifact_uri.starts_with("http://") || artifact_uri.starts_with("https://") {
        "remote"
    } else {
        "local"
    }
}

fn structural_path_ranker_runtime_source_extension(source_hint: &str) -> String {
    let trimmed = source_hint.trim();
    let path_like = trimmed
        .split('?')
        .next()
        .unwrap_or(trimmed)
        .split('#')
        .next()
        .unwrap_or(trimmed);
    Path::new(path_like)
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or_default()
        .to_ascii_lowercase()
}

fn structural_path_ranker_runtime_row_from_value(
    value: &Value,
    score_column: &str,
) -> Option<StructuralPathRankerRuntimeRow> {
    let candidate_set_id = value.get("candidate_set_id")?.as_str()?.trim().to_string();
    let path_id = value.get("path_id")?.as_str()?.trim().to_string();
    let raw_path_score = value.get(score_column).and_then(Value::as_f64);
    let calibrated_path_prob = value.get("calibrated_path_prob").and_then(Value::as_f64);
    let path_prob_lower_bound = value.get("path_prob_lower_bound").and_then(Value::as_f64);
    let execution_gate_status = value
        .get("execution_gate_status")
        .and_then(Value::as_str)
        .map(ToString::to_string);
    Some(StructuralPathRankerRuntimeRow {
        candidate_set_id,
        path_id,
        raw_path_score,
        calibrated_path_prob,
        path_prob_lower_bound,
        execution_gate_status,
    })
}

fn structural_path_ranker_runtime_row_from_csv_record(
    headers: &StringRecord,
    record: &StringRecord,
    score_column: &str,
) -> Option<StructuralPathRankerRuntimeRow> {
    let value_for = |name: &str| -> Option<&str> {
        let index = headers.iter().position(|header| header == name)?;
        record.get(index)
    };
    let candidate_set_id = value_for("candidate_set_id")?.trim().to_string();
    let path_id = value_for("path_id")?.trim().to_string();
    let parse_f64 = |name: &str| -> Option<f64> { value_for(name)?.trim().parse::<f64>().ok() };
    let execution_gate_status = value_for("execution_gate_status")
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(ToString::to_string);
    Some(StructuralPathRankerRuntimeRow {
        candidate_set_id,
        path_id,
        raw_path_score: parse_f64(score_column),
        calibrated_path_prob: parse_f64("calibrated_path_prob"),
        path_prob_lower_bound: parse_f64("path_prob_lower_bound"),
        execution_gate_status,
    })
}

fn parse_structural_path_ranker_runtime_rows_from_raw(
    source_hint: &str,
    raw: &str,
    score_column: &str,
) -> Result<Vec<StructuralPathRankerRuntimeRow>> {
    match structural_path_ranker_runtime_source_extension(source_hint).as_str() {
        "jsonl" => Ok(raw
            .lines()
            .filter(|line| !line.trim().is_empty())
            .filter_map(|line| serde_json::from_str::<Value>(line).ok())
            .filter_map(|value| structural_path_ranker_runtime_row_from_value(&value, score_column))
            .collect()),
        "json" => {
            let value = serde_json::from_str::<Value>(raw)?;
            let rows = match value {
                Value::Array(items) => items
                    .iter()
                    .filter_map(|item| structural_path_ranker_runtime_row_from_value(item, score_column))
                    .collect(),
                Value::Object(_) => structural_path_ranker_runtime_row_from_value(&value, score_column)
                    .into_iter()
                    .collect(),
                _ => Vec::new(),
            };
            Ok(rows)
        }
        _ => {
            let mut reader = csv::Reader::from_reader(raw.as_bytes());
            let headers = reader.headers()?.clone();
            Ok(reader
                .records()
                .filter_map(|record| record.ok())
                .filter_map(|record| {
                    structural_path_ranker_runtime_row_from_csv_record(
                        &headers,
                        &record,
                        score_column,
                    )
                })
                .collect())
        }
    }
}

pub fn load_structural_path_ranker_runtime_artifact_rows(
    state_dir: &str,
    symbol: &str,
    artifact_uri: &str,
    score_column: &str,
) -> Result<Vec<StructuralPathRankerRuntimeRow>> {
    if structural_path_ranker_runtime_source_kind(artifact_uri) == "remote" {
        let client = Client::builder().timeout(Duration::from_secs(3)).build()?;
        let raw = client
            .get(artifact_uri)
            .send()?
            .error_for_status()?
            .text()?;
        return parse_structural_path_ranker_runtime_rows_from_raw(artifact_uri, &raw, score_column);
    }
    let artifact_path = structural_path_ranker_artifact_uri_path(state_dir, symbol, artifact_uri)
        .ok_or_else(|| anyhow::anyhow!("artifact uri is not a supported local path"))?;
    if !artifact_path.exists() {
        return Ok(Vec::new());
    }
    let raw = fs::read_to_string(&artifact_path)?;
    parse_structural_path_ranker_runtime_rows_from_raw(
        artifact_path.to_string_lossy().as_ref(),
        &raw,
        score_column,
    )
}
