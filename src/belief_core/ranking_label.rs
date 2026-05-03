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
pub const STRUCTURAL_PATH_RANKING_IPS_WEIGHT_CLIP: f64 = 5.0;
pub const STRUCTURAL_PATH_RANKING_EXECUTION_GATE_MIN_PATH_PROB: f64 = 0.5;

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

pub fn structural_path_ranking_reward_label(pending_reward_state: &str) -> Option<f64> {
    match pending_reward_state {
        "matured_success" => Some(1.0),
        "matured_failure" | "matured_invalidated" => Some(0.0),
        _ => None,
    }
}

pub fn structural_path_ranking_beta_mean(success_mass: f64, failure_mass: f64) -> f64 {
    let alpha = 1.0 + success_mass.max(0.0);
    let beta = 1.0 + failure_mass.max(0.0);
    (alpha / (alpha + beta)).clamp(0.0, 1.0)
}

pub fn structural_path_ranking_beta_lower_bound(success_mass: f64, failure_mass: f64) -> f64 {
    let mean = structural_path_ranking_beta_mean(success_mass, failure_mass);
    let n = 2.0 + success_mass.max(0.0) + failure_mass.max(0.0);
    let standard_error = (mean * (1.0 - mean) / (n + 1.0)).sqrt();
    (mean - 1.64 * standard_error).clamp(0.0, 1.0)
}

pub fn structural_path_ranking_ips_weight(propensity_estimate: Option<f64>) -> Option<f64> {
    let propensity = propensity_estimate?.clamp(0.0, 1.0);
    if propensity <= f64::EPSILON {
        None
    } else {
        Some((1.0 / propensity).min(STRUCTURAL_PATH_RANKING_IPS_WEIGHT_CLIP))
    }
}

pub fn structural_path_ranking_propensity_evaluation_weight(
    row: &StructuralPathRankingTargetRow,
) -> Option<f64> {
    let ips_weight = row
        .ips_weight
        .or_else(|| structural_path_ranking_ips_weight(row.propensity_estimate))?;
    let maturity_weight = if row.maturity_weight > f64::EPSILON {
        row.maturity_weight.clamp(0.0, 1.0)
    } else if row.maturity_mask
        || structural_path_ranking_reward_label(&row.pending_reward_state).is_some()
    {
        1.0
    } else {
        0.0
    };
    if maturity_weight <= f64::EPSILON {
        return None;
    }
    Some(ips_weight.clamp(0.0, STRUCTURAL_PATH_RANKING_IPS_WEIGHT_CLIP) * maturity_weight)
}

pub fn apply_structural_path_probability_bins(
    rows: &mut [StructuralPathRankingTargetRow],
    bins: &[StructuralPathProbabilityCalibrationBin],
) -> usize {
    let mut calibrated_rows = 0;
    for row in rows {
        let Some(raw_score) = row.raw_path_score else {
            continue;
        };
        let raw_score = raw_score.clamp(0.0, 1.0);
        let Some(bin) = bins.iter().find(|bin| {
            bin.regime_calibration_bucket == row.regime_calibration_bucket
                && raw_score >= bin.raw_path_score_min
                && raw_score <= bin.raw_path_score_max
        }) else {
            continue;
        };
        row.calibrated_path_prob = Some(bin.calibrated_path_prob);
        row.path_prob_lower_bound = Some(bin.path_prob_lower_bound);
        calibrated_rows += 1;
    }
    calibrated_rows
}

pub fn apply_structural_path_ranking_execution_gates(
    artifact: &mut StructuralPathRankingTargetArtifact,
) {
    for row in &mut artifact.rows {
        let Some(lower_bound) = row.path_prob_lower_bound else {
            continue;
        };
        let lower_bound = lower_bound.clamp(0.0, 1.0);
        let min_path_prob = STRUCTURAL_PATH_RANKING_EXECUTION_GATE_MIN_PATH_PROB;
        let status = if lower_bound >= min_path_prob {
            "pass"
        } else {
            "observe"
        };
        row.execution_gate_status = Some(status.to_string());
        row.execution_gate_min_path_prob = Some(min_path_prob);
        row.execution_gate_reason = Some(format!(
            "path_prob_lower_bound={lower_bound:.3} min_path_prob={min_path_prob:.3}"
        ));
    }
}

pub fn apply_structural_path_probability_calibration(
    artifact: &mut StructuralPathRankingTargetArtifact,
) -> StructuralPathProbabilityCalibrationReport {
    let mut by_bucket = BTreeMap::<String, Vec<(f64, f64)>>::new();
    for row in &artifact.rows {
        let Some(raw_score) = row.raw_path_score else {
            continue;
        };
        let Some(reward) = structural_path_ranking_reward_label(&row.pending_reward_state) else {
            continue;
        };
        by_bucket
            .entry(row.regime_calibration_bucket.clone())
            .or_default()
            .push((raw_score.clamp(0.0, 1.0), reward));
    }

    let observed_rows = by_bucket.values().map(Vec::len).sum::<usize>();
    let mut bins = Vec::new();
    let mut warnings = Vec::new();
    for (bucket, observations) in by_bucket {
        if observations.len() < 2 {
            warnings.push(format!(
                "calibration_bucket_insufficient_observations:{bucket}:{}",
                observations.len()
            ));
            continue;
        }
        let successes = observations
            .iter()
            .filter(|(_, reward)| *reward > 0.5)
            .count();
        let calibrated_path_prob = structural_path_ranking_beta_mean(
            successes as f64,
            (observations.len() - successes) as f64,
        );
        let path_prob_lower_bound = structural_path_ranking_beta_lower_bound(
            successes as f64,
            (observations.len() - successes) as f64,
        );
        let raw_path_score_min = observations
            .iter()
            .map(|(score, _)| *score)
            .fold(f64::INFINITY, f64::min);
        let raw_path_score_max = observations
            .iter()
            .map(|(score, _)| *score)
            .fold(f64::NEG_INFINITY, f64::max);
        bins.push(StructuralPathProbabilityCalibrationBin {
            regime_calibration_bucket: bucket,
            observations: observations.len(),
            successes,
            raw_path_score_min,
            raw_path_score_max,
            calibrated_path_prob,
            path_prob_lower_bound,
        });
    }

    let calibrated_rows = apply_structural_path_probability_bins(&mut artifact.rows, &bins);
    let status = if calibrated_rows > 0 {
        "calibrated"
    } else if observed_rows > 0 {
        "insufficient_calibration_data"
    } else {
        "no_calibration_observations"
    };
    if calibrated_rows == 0 {
        warnings.push("structural_path_probability_calibration_not_fitted".to_string());
    }
    apply_structural_path_ranking_execution_gates(artifact);
    StructuralPathProbabilityCalibrationReport {
        status: status.to_string(),
        observed_rows,
        calibrated_rows,
        bins,
        warnings,
        summary_line: format!(
            "structural_path_probability_calibration status={status} observed_rows={observed_rows} calibrated_rows={calibrated_rows}"
        ),
    }
}

pub fn evaluate_structural_path_probability_calibration_rows(
    rows: &[StructuralPathRankingTargetRow],
) -> StructuralPathProbabilityCalibrationEvaluationReport {
    let mut by_bucket = BTreeMap::<String, Vec<(f64, f64)>>::new();
    let mut squared_error_sum = 0.0;
    let mut propensity_weighted_squared_error_sum = 0.0;
    let mut propensity_weight_sum = 0.0;
    let mut propensity_weighted_rows = 0;
    for row in rows {
        if row.raw_path_score.is_none() {
            continue;
        }
        let Some(calibrated_prob) = row.calibrated_path_prob else {
            continue;
        };
        let Some(reward) = structural_path_ranking_reward_label(&row.pending_reward_state) else {
            continue;
        };
        let calibrated_prob = calibrated_prob.clamp(0.0, 1.0);
        let squared_error = (calibrated_prob - reward).powi(2);
        squared_error_sum += squared_error;
        if let Some(weight) = structural_path_ranking_propensity_evaluation_weight(row) {
            propensity_weighted_squared_error_sum += weight * squared_error;
            propensity_weight_sum += weight;
            propensity_weighted_rows += 1;
        }
        by_bucket
            .entry(row.regime_calibration_bucket.clone())
            .or_default()
            .push((calibrated_prob, reward));
    }

    let eligible_rows = by_bucket.values().map(Vec::len).sum::<usize>();
    let mut warnings = Vec::new();
    if eligible_rows < 2 {
        warnings.push(
            "structural_path_probability_calibration_evaluation_insufficient_rows".to_string(),
        );
        return StructuralPathProbabilityCalibrationEvaluationReport {
            status: "insufficient_calibration_evaluation_rows".to_string(),
            eligible_rows,
            warnings,
            summary_line: format!(
                "structural_path_probability_calibration_evaluation status=insufficient_calibration_evaluation_rows eligible_rows={eligible_rows}"
            ),
            ..StructuralPathProbabilityCalibrationEvaluationReport::default()
        };
    }

    let mut expected_calibration_error = 0.0;
    let mut max_calibration_error: f64 = 0.0;
    let mut bins = Vec::new();
    for (bucket, observations) in by_bucket {
        let observation_count = observations.len();
        let mean_calibrated_path_prob = observations
            .iter()
            .map(|(probability, _)| *probability)
            .sum::<f64>()
            / observation_count as f64;
        let empirical_success_rate =
            observations.iter().map(|(_, reward)| *reward).sum::<f64>() / observation_count as f64;
        let absolute_error = (mean_calibrated_path_prob - empirical_success_rate).abs();
        expected_calibration_error +=
            (observation_count as f64 / eligible_rows as f64) * absolute_error;
        max_calibration_error = max_calibration_error.max(absolute_error);
        bins.push(StructuralPathProbabilityCalibrationEvaluationBin {
            regime_calibration_bucket: bucket,
            observations: observation_count,
            mean_calibrated_path_prob,
            empirical_success_rate,
            absolute_error,
        });
    }

    let brier_score = squared_error_sum / eligible_rows as f64;
    let propensity_weighted_brier_score = if propensity_weight_sum > f64::EPSILON {
        Some(propensity_weighted_squared_error_sum / propensity_weight_sum)
    } else {
        warnings.push(
            "structural_path_probability_calibration_evaluation_propensity_missing".to_string(),
        );
        None
    };
    let propensity_weighted_brier_summary = propensity_weighted_brier_score
        .map(|score| format!(" propensity_weighted_brier_score={score:.6}"))
        .unwrap_or_default();
    StructuralPathProbabilityCalibrationEvaluationReport {
        status: "evaluated".to_string(),
        eligible_rows,
        brier_score: Some(brier_score),
        propensity_weighted_rows,
        propensity_weighted_brier_score,
        expected_calibration_error: Some(expected_calibration_error),
        max_calibration_error: Some(max_calibration_error),
        bins,
        warnings,
        summary_line: format!(
            "structural_path_probability_calibration_evaluation status=evaluated eligible_rows={eligible_rows} brier_score={brier_score:.6} expected_calibration_error={expected_calibration_error:.6} propensity_weighted_rows={propensity_weighted_rows}{propensity_weighted_brier_summary}"
        ),
    }
}
