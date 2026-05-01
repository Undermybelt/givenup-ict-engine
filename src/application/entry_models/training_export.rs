use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use crate::application::orchestration::{
    StructuralPathRankingTargetExportSummary, STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE,
};
use crate::state::{
    load_state_or_default, save_text_state, AnalyzeRunRecord, UpdateRunRecord, ANALYZE_RUNS_FILE,
    UPDATE_RUNS_FILE,
};
use crate::types::RegimeProbs;

use super::{
    bin_breaker_rb_for_bbn, bin_cisd_rb_for_bbn, build_breaker_rb_catboost_feature_row,
    build_cisd_rb_catboost_feature_row, decode_entry_model_packet, entry_model_providers,
    BreakerRbBbnEvidence, BreakerRbEntryModelPacket, CisdRbBbnEvidence, CisdRbEntryModelPacket,
    ConsumerDefaultMode, EntryModelProvider, EntryModelTrainingRows, BREAKER_RB_SETUP_MODEL_ID,
    CISD_RB_SETUP_MODEL_ID,
};

pub const POLICY_TRAINING_DIR: &str = "policy_training";
pub const CISD_RB_BBN_TRAINING_FILE: &str = "cisd_rb_bbn_training.csv";
pub const CISD_RB_CATBOOST_TRAINING_FILE: &str = "cisd_rb_catboost_training.csv";
pub const CISD_RB_TRAINING_SUMMARY_FILE: &str = "cisd_rb_training_export_summary.json";
pub const BREAKER_RB_BBN_TRAINING_FILE: &str = "breaker_rb_bbn_training.csv";
pub const BREAKER_RB_CATBOOST_TRAINING_FILE: &str = "breaker_rb_catboost_training.csv";
pub const BREAKER_RB_TRAINING_SUMMARY_FILE: &str = "breaker_rb_training_export_summary.json";

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
struct CisdRbCollectedTrainingRows {
    analyze_runs: usize,
    update_runs: usize,
    bbn_rows: Vec<CisdRbBbnTrainingRow>,
    catboost_rows: Vec<CisdRbCatBoostTrainingRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
struct BreakerCollectedTrainingRows {
    analyze_runs: usize,
    update_runs: usize,
    bbn_rows: Vec<BreakerRbBbnTrainingRow>,
    catboost_rows: Vec<BreakerRbCatBoostTrainingRow>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CisdRbBbnTrainingRow {
    pub analyze_run_id: String,
    pub update_run_id: String,
    pub symbol: String,
    pub timeframe: String,
    pub setup_model_id: String,
    pub trend_alignment: String,
    pub liquidity_interaction_quality: String,
    pub trigger_confirmation_quality: String,
    pub session_quality: String,
    pub entry_quality: String,
    pub evidence_quality_score: f64,
    pub gating_status: String,
    pub realized_outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CisdRbCatBoostTrainingRow {
    pub analyze_run_id: String,
    pub update_run_id: String,
    pub symbol: String,
    pub timeframe: String,
    pub setup_model_id: String,
    pub setup_progress_state: String,
    pub hmm_accumulation_prob: f64,
    pub hmm_manipulation_expansion_prob: f64,
    pub hmm_distribution_prob: f64,
    pub bbn_trend_alignment: String,
    pub bbn_liquidity_interaction_quality: String,
    pub bbn_trigger_confirmation_quality: String,
    pub bbn_session_quality: String,
    pub bbn_entry_quality: String,
    pub cisd_run_length_observed: f64,
    pub cisd_impulse_atr: f64,
    pub cisd_body_ratio_mean: f64,
    pub rb_wick_body_ratio: f64,
    pub rb_close_location_ratio: f64,
    pub bars_between_cisd_and_rb: f64,
    pub seq_window_hit: bool,
    pub ema19_distance_bps: f64,
    pub atr14_bps: f64,
    pub realized_vol_zscore: f64,
    pub evidence_quality_score: f64,
    pub session_label: String,
    pub realized_outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct CisdRbTrainingExportSummary {
    pub symbol: String,
    pub analyze_runs: usize,
    pub update_runs: usize,
    pub matched_rows: usize,
    pub bbn_training_path: String,
    pub catboost_training_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct BreakerRbTrainingExportSummary {
    pub symbol: String,
    pub analyze_runs: usize,
    pub update_runs: usize,
    pub matched_rows: usize,
    pub bbn_training_path: String,
    pub catboost_training_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct NumericRangeSummary {
    pub min: f64,
    pub max: f64,
    pub span: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct BbnTrainingStatusSurface {
    pub ready: bool,
    pub rows: usize,
    pub outcome_counts: BTreeMap<String, usize>,
    pub entry_quality_counts: BTreeMap<String, usize>,
    pub trigger_confirmation_quality_counts: BTreeMap<String, usize>,
    pub session_quality_counts: BTreeMap<String, usize>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct CatBoostTrainingStatusSurface {
    pub ready: bool,
    pub rows: usize,
    pub outcome_counts: BTreeMap<String, usize>,
    pub numeric_ranges: BTreeMap<String, NumericRangeSummary>,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct CisdRbTrainingStatusSurface {
    pub symbol: String,
    pub analyze_runs: usize,
    pub update_runs: usize,
    pub matched_rows: usize,
    pub setup_model_ids: BTreeMap<String, usize>,
    pub bbn: BbnTrainingStatusSurface,
    pub catboost: CatBoostTrainingStatusSurface,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct BreakerRbTrainingStatusSurface {
    pub symbol: String,
    pub analyze_runs: usize,
    pub update_runs: usize,
    pub matched_rows: usize,
    pub setup_model_ids: BTreeMap<String, usize>,
    pub bbn: BbnTrainingStatusSurface,
    pub catboost: CatBoostTrainingStatusSurface,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BreakerRbBbnTrainingRow {
    pub analyze_run_id: String,
    pub update_run_id: String,
    pub symbol: String,
    pub timeframe: String,
    pub setup_model_id: String,
    pub trend_alignment: String,
    pub breaker_retest_quality: String,
    pub session_quality: String,
    pub entry_quality: String,
    pub evidence_quality_score: f64,
    pub gating_status: String,
    pub realized_outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BreakerRbCatBoostTrainingRow {
    pub analyze_run_id: String,
    pub update_run_id: String,
    pub symbol: String,
    pub timeframe: String,
    pub setup_model_id: String,
    pub setup_progress_state: String,
    pub hmm_accumulation_prob: f64,
    pub hmm_manipulation_expansion_prob: f64,
    pub hmm_distribution_prob: f64,
    pub bbn_trend_alignment: String,
    pub bbn_breaker_retest_quality: String,
    pub bbn_session_quality: String,
    pub bbn_entry_quality: String,
    pub bars_between_violation_and_retest: f64,
    pub breaker_width_bps: f64,
    pub retest_reclaim_bps: f64,
    pub rb_wick_body_ratio: f64,
    pub rb_close_location_ratio: f64,
    pub ema19_distance_bps: f64,
    pub atr14_bps: f64,
    pub realized_vol_zscore: f64,
    pub evidence_quality_score: f64,
    pub session_label: String,
    pub realized_outcome: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct PolicyTrainingProviderStatusSurface {
    #[serde(rename = "entry_model_id")]
    pub provider_id: String,
    pub consumer_adopted_by_default: bool,
    pub consumer_effect: String,
    pub ready: bool,
    pub matched_rows: usize,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct PolicyTrainingStatusSurface {
    pub symbol: String,
    pub analyze_runs: usize,
    pub update_runs: usize,
    #[serde(rename = "entry_models")]
    pub providers: Vec<PolicyTrainingProviderStatusSurface>,
    pub structural_path_ranking_target: StructuralPathRankingTargetTrainingStatusSurface,
    pub summary_line: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, PartialEq)]
pub struct StructuralPathRankingTargetTrainingStatusSurface {
    pub export_ready: bool,
    pub calibration_ready: bool,
    pub rows: usize,
    pub candidate_set_id: Option<String>,
    pub candidate_set_size: usize,
    pub rows_with_propensity_estimate: usize,
    pub rows_with_calibrated_path_prob: usize,
    pub summary_path: String,
    pub csv_path: Option<String>,
    pub jsonl_path: Option<String>,
    pub warnings: Vec<String>,
    pub summary_line: String,
}

#[derive(Debug, Clone, Copy, Default)]
pub struct CisdRbEntryModelProvider;

#[derive(Debug, Clone, Copy, Default)]
pub struct BreakerRbEntryModelProvider;

impl EntryModelProvider for CisdRbEntryModelProvider {
    fn provider_id(&self) -> &'static str {
        CISD_RB_SETUP_MODEL_ID
    }

    fn consumer_default_mode(&self) -> ConsumerDefaultMode {
        ConsumerDefaultMode::InternalTrainingOnly
    }

    fn build_analyze_packet(
        &self,
        symbol: &str,
        timeframe: &str,
        candles: &[crate::types::Candle],
        filter: &crate::state::PreBayesEvidenceFilter,
    ) -> Option<Value> {
        super::build_cisd_rb_entry_model_packet(symbol, timeframe, candles, filter)
            .and_then(|packet| serde_json::to_value(packet).ok())
    }

    fn training_rows(&self, state_dir: &str, symbol: &str) -> Result<EntryModelTrainingRows> {
        build_cisd_rb_training_rows(state_dir, symbol)
    }

    fn status_surface(
        &self,
        state_dir: &str,
        symbol: &str,
    ) -> Result<PolicyTrainingProviderStatusSurface> {
        let cisd_rb = cisd_rb_training_status(state_dir, symbol)?;
        Ok(PolicyTrainingProviderStatusSurface {
            provider_id: self.provider_id().to_string(),
            consumer_adopted_by_default: self.consumer_default_mode().adopted_by_default(),
            consumer_effect: self.consumer_default_mode().effect_label().to_string(),
            ready: cisd_rb.bbn.ready && cisd_rb.catboost.ready,
            matched_rows: cisd_rb.matched_rows,
            summary_line: cisd_rb.summary_line,
        })
    }
}

impl EntryModelProvider for BreakerRbEntryModelProvider {
    fn provider_id(&self) -> &'static str {
        BREAKER_RB_SETUP_MODEL_ID
    }

    fn consumer_default_mode(&self) -> ConsumerDefaultMode {
        ConsumerDefaultMode::InternalTrainingOnly
    }

    fn build_analyze_packet(
        &self,
        symbol: &str,
        timeframe: &str,
        candles: &[crate::types::Candle],
        filter: &crate::state::PreBayesEvidenceFilter,
    ) -> Option<Value> {
        super::build_breaker_rb_entry_model_packet(symbol, timeframe, candles, filter)
            .and_then(|packet| serde_json::to_value(packet).ok())
    }

    fn training_rows(&self, state_dir: &str, symbol: &str) -> Result<EntryModelTrainingRows> {
        build_breaker_rb_training_rows(state_dir, symbol)
    }

    fn status_surface(
        &self,
        state_dir: &str,
        symbol: &str,
    ) -> Result<PolicyTrainingProviderStatusSurface> {
        let breaker_rb = breaker_rb_training_status(state_dir, symbol)?;
        Ok(PolicyTrainingProviderStatusSurface {
            provider_id: self.provider_id().to_string(),
            consumer_adopted_by_default: self.consumer_default_mode().adopted_by_default(),
            consumer_effect: self.consumer_default_mode().effect_label().to_string(),
            ready: breaker_rb.bbn.ready && breaker_rb.catboost.ready,
            matched_rows: breaker_rb.matched_rows,
            summary_line: breaker_rb.summary_line,
        })
    }
}

pub fn export_cisd_rb_training_tables(
    state_dir: &str,
    symbol: &str,
) -> Result<CisdRbTrainingExportSummary> {
    let rows = build_cisd_rb_training_rows(state_dir, symbol)?;
    persist_training_rows(state_dir, symbol, &rows)?;
    let summary: CisdRbTrainingExportSummary = serde_json::from_str(&rows.summary_json)?;
    Ok(summary)
}

pub fn export_breaker_rb_training_tables(
    state_dir: &str,
    symbol: &str,
) -> Result<BreakerRbTrainingExportSummary> {
    let rows = build_breaker_rb_training_rows(state_dir, symbol)?;
    persist_training_rows(state_dir, symbol, &rows)?;
    let summary: BreakerRbTrainingExportSummary = serde_json::from_str(&rows.summary_json)?;
    Ok(summary)
}

fn build_breaker_rb_training_rows(state_dir: &str, symbol: &str) -> Result<EntryModelTrainingRows> {
    let rows = collect_breaker_training_rows(state_dir, symbol)?;
    let bbn_csv = render_breaker_bbn_training_csv(&rows.bbn_rows);
    let catboost_csv = render_breaker_catboost_training_csv(&rows.catboost_rows);
    let summary = BreakerRbTrainingExportSummary {
        symbol: symbol.to_string(),
        analyze_runs: rows.analyze_runs,
        update_runs: rows.update_runs,
        matched_rows: rows.bbn_rows.len(),
        bbn_training_path: Path::new(state_dir)
            .join(symbol)
            .join(POLICY_TRAINING_DIR)
            .join(BREAKER_RB_BBN_TRAINING_FILE)
            .to_string_lossy()
            .to_string(),
        catboost_training_path: Path::new(state_dir)
            .join(symbol)
            .join(POLICY_TRAINING_DIR)
            .join(BREAKER_RB_CATBOOST_TRAINING_FILE)
            .to_string_lossy()
            .to_string(),
    };
    Ok(EntryModelTrainingRows {
        provider_id: BREAKER_RB_SETUP_MODEL_ID.to_string(),
        matched_rows: rows.bbn_rows.len(),
        bbn_training_filename: BREAKER_RB_BBN_TRAINING_FILE.to_string(),
        bbn_csv,
        catboost_training_filename: BREAKER_RB_CATBOOST_TRAINING_FILE.to_string(),
        catboost_csv,
        summary_filename: BREAKER_RB_TRAINING_SUMMARY_FILE.to_string(),
        summary_json: serde_json::to_string_pretty(&summary)?,
    })
}

pub fn export_policy_training_tables(state_dir: &str, symbol: &str) -> Result<()> {
    for provider in entry_model_providers() {
        let rows = provider.training_rows(state_dir, symbol)?;
        persist_training_rows(state_dir, symbol, &rows)?;
    }
    Ok(())
}

fn build_cisd_rb_training_rows(state_dir: &str, symbol: &str) -> Result<EntryModelTrainingRows> {
    let rows = collect_training_rows(state_dir, symbol)?;
    let bbn_csv = render_bbn_training_csv(&rows.bbn_rows);
    let catboost_csv = render_catboost_training_csv(&rows.catboost_rows);
    let summary = CisdRbTrainingExportSummary {
        symbol: symbol.to_string(),
        analyze_runs: rows.analyze_runs,
        update_runs: rows.update_runs,
        matched_rows: rows.bbn_rows.len(),
        bbn_training_path: Path::new(state_dir)
            .join(symbol)
            .join(POLICY_TRAINING_DIR)
            .join(CISD_RB_BBN_TRAINING_FILE)
            .to_string_lossy()
            .to_string(),
        catboost_training_path: Path::new(state_dir)
            .join(symbol)
            .join(POLICY_TRAINING_DIR)
            .join(CISD_RB_CATBOOST_TRAINING_FILE)
            .to_string_lossy()
            .to_string(),
    };
    Ok(EntryModelTrainingRows {
        provider_id: CISD_RB_SETUP_MODEL_ID.to_string(),
        matched_rows: rows.bbn_rows.len(),
        bbn_training_filename: CISD_RB_BBN_TRAINING_FILE.to_string(),
        bbn_csv,
        catboost_training_filename: CISD_RB_CATBOOST_TRAINING_FILE.to_string(),
        catboost_csv,
        summary_filename: CISD_RB_TRAINING_SUMMARY_FILE.to_string(),
        summary_json: serde_json::to_string_pretty(&summary)?,
    })
}

pub fn cisd_rb_training_status(
    state_dir: &str,
    symbol: &str,
) -> Result<CisdRbTrainingStatusSurface> {
    let rows = collect_training_rows(state_dir, symbol)?;
    let setup_model_ids =
        rows.catboost_rows
            .iter()
            .fold(BTreeMap::<String, usize>::new(), |mut acc, row| {
                *acc.entry(row.setup_model_id.clone()).or_insert(0) += 1;
                acc
            });
    let bbn = build_bbn_status(&rows.bbn_rows);
    let catboost = build_catboost_status(&rows.catboost_rows);
    let summary_line = if bbn.ready && catboost.ready {
        format!(
            "policy training looks healthy for BBN and CatBoost: matched_rows={} outcomes={}",
            rows.bbn_rows.len(),
            format_counts(&catboost.outcome_counts)
        )
    } else if !bbn.ready && !catboost.ready {
        format!(
            "policy training is not ready for either BBN or CatBoost: matched_rows={} bbn_warnings={} catboost_warnings={}",
            rows.bbn_rows.len(),
            bbn.warnings.join("; "),
            catboost.warnings.join("; ")
        )
    } else if !bbn.ready {
        format!(
            "policy training is CatBoost-usable but BBN-weak: matched_rows={} bbn_warnings={}",
            rows.bbn_rows.len(),
            bbn.warnings.join("; ")
        )
    } else {
        format!(
            "policy training is BBN-usable but CatBoost-weak: matched_rows={} catboost_warnings={}",
            rows.catboost_rows.len(),
            catboost.warnings.join("; ")
        )
    };
    Ok(CisdRbTrainingStatusSurface {
        symbol: symbol.to_string(),
        analyze_runs: rows.analyze_runs,
        update_runs: rows.update_runs,
        matched_rows: rows.bbn_rows.len(),
        setup_model_ids,
        bbn,
        catboost,
        summary_line,
    })
}

pub fn breaker_rb_training_status(
    state_dir: &str,
    symbol: &str,
) -> Result<BreakerRbTrainingStatusSurface> {
    let rows = collect_breaker_training_rows(state_dir, symbol)?;
    let setup_model_ids =
        rows.catboost_rows
            .iter()
            .fold(BTreeMap::<String, usize>::new(), |mut acc, row| {
                *acc.entry(row.setup_model_id.clone()).or_insert(0) += 1;
                acc
            });
    let outcome_counts = count_strings(
        rows.bbn_rows
            .iter()
            .map(|row| row.realized_outcome.as_str()),
    );
    let bbn = build_generic_bbn_status(
        rows.bbn_rows.len(),
        outcome_counts.clone(),
        count_strings(rows.bbn_rows.iter().map(|row| row.entry_quality.as_str())),
        count_strings(
            rows.bbn_rows
                .iter()
                .map(|row| row.breaker_retest_quality.as_str()),
        ),
        count_strings(rows.bbn_rows.iter().map(|row| row.session_quality.as_str())),
    );
    let catboost = build_generic_catboost_status(
        rows.catboost_rows.len(),
        outcome_counts,
        BTreeMap::from([
            (
                "bars_between_violation_and_retest".to_string(),
                range_of(
                    rows.catboost_rows
                        .iter()
                        .map(|row| row.bars_between_violation_and_retest),
                ),
            ),
            (
                "breaker_width_bps".to_string(),
                range_of(rows.catboost_rows.iter().map(|row| row.breaker_width_bps)),
            ),
            (
                "retest_reclaim_bps".to_string(),
                range_of(rows.catboost_rows.iter().map(|row| row.retest_reclaim_bps)),
            ),
            (
                "rb_wick_body_ratio".to_string(),
                range_of(rows.catboost_rows.iter().map(|row| row.rb_wick_body_ratio)),
            ),
            (
                "realized_vol_zscore".to_string(),
                range_of(rows.catboost_rows.iter().map(|row| row.realized_vol_zscore)),
            ),
        ]),
    );
    let summary_line =
        build_provider_summary_line("Breaker RB", rows.bbn_rows.len(), &bbn, &catboost);
    Ok(BreakerRbTrainingStatusSurface {
        symbol: symbol.to_string(),
        analyze_runs: rows.analyze_runs,
        update_runs: rows.update_runs,
        matched_rows: rows.bbn_rows.len(),
        setup_model_ids,
        bbn,
        catboost,
        summary_line,
    })
}

pub fn cisd_rb_training_status_command(state_dir: &str, symbol: &str) -> Result<()> {
    let surface = cisd_rb_training_status(state_dir, symbol)?;
    println!("{}", serde_json::to_string_pretty(&surface)?);
    Ok(())
}

pub fn policy_training_status(
    state_dir: &str,
    symbol: &str,
    provider_filter: Option<&str>,
) -> Result<PolicyTrainingStatusSurface> {
    if let Some(filter) = provider_filter {
        if entry_model_providers()
            .into_iter()
            .all(|provider| provider.provider_id() != filter)
        {
            bail!(
                "unsupported policy training provider '{}'; available: {}",
                filter,
                entry_model_providers()
                    .into_iter()
                    .map(|provider| provider.provider_id())
                    .collect::<Vec<_>>()
                    .join(", ")
            );
        }
    }
    let cisd_rb = cisd_rb_training_status(state_dir, symbol)?;
    let structural_path_ranking_target =
        structural_path_ranking_target_training_status(state_dir, symbol)?;
    let providers = entry_model_providers()
        .into_iter()
        .filter(|provider| {
            provider_filter
                .map(|filter| filter == provider.provider_id())
                .unwrap_or(true)
        })
        .map(|provider| provider.status_surface(state_dir, symbol))
        .collect::<Result<Vec<_>>>()?;
    let summary_line = if providers.iter().all(|provider| provider.ready) {
        format!(
            "all entry-model training modules ready: {}",
            providers
                .iter()
                .map(|provider| format!("{}={}", provider.provider_id, provider.matched_rows))
                .collect::<Vec<_>>()
                .join(",")
        )
    } else {
        let ready = providers
            .iter()
            .filter(|provider| provider.ready)
            .map(|provider| provider.provider_id.clone())
            .collect::<Vec<_>>();
        let pending = providers
            .iter()
            .filter(|provider| !provider.ready)
            .map(|provider| provider.provider_id.clone())
            .collect::<Vec<_>>();
        format!(
            "entry-model training modules mixed: ready=[{}] pending=[{}]",
            ready.join(","),
            pending.join(",")
        )
    };
    Ok(PolicyTrainingStatusSurface {
        symbol: symbol.to_string(),
        analyze_runs: cisd_rb.analyze_runs,
        update_runs: cisd_rb.update_runs,
        providers,
        structural_path_ranking_target,
        summary_line,
    })
}

pub fn structural_path_ranking_target_training_status(
    state_dir: &str,
    symbol: &str,
) -> Result<StructuralPathRankingTargetTrainingStatusSurface> {
    let summary_path = Path::new(state_dir)
        .join(symbol)
        .join(POLICY_TRAINING_DIR)
        .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE);
    if !summary_path.exists() {
        return Ok(StructuralPathRankingTargetTrainingStatusSurface {
            summary_path: summary_path.to_string_lossy().to_string(),
            warnings: vec!["structural_path_ranking_target_export_missing".to_string()],
            summary_line: "structural path ranking target export missing".to_string(),
            ..StructuralPathRankingTargetTrainingStatusSurface::default()
        });
    }
    let raw = fs::read_to_string(&summary_path)?;
    let summary: StructuralPathRankingTargetExportSummary = serde_json::from_str(&raw)?;
    let calibration_ready = summary.rows_with_calibrated_path_prob > 0
        && summary.rows_with_path_prob_lower_bound > 0;
    let mut warnings = Vec::new();
    if summary.rows == 0 {
        warnings.push("structural_path_ranking_target_rows_empty".to_string());
    }
    if summary.rows_with_propensity_estimate == 0 {
        warnings.push("structural_path_ranking_target_propensity_missing".to_string());
    }
    if !calibration_ready {
        warnings.push("structural_path_ranking_target_calibration_not_fitted".to_string());
    }
    Ok(StructuralPathRankingTargetTrainingStatusSurface {
        export_ready: summary.rows > 0,
        calibration_ready,
        rows: summary.rows,
        candidate_set_id: Some(summary.candidate_set_id),
        candidate_set_size: summary.candidate_set_size,
        rows_with_propensity_estimate: summary.rows_with_propensity_estimate,
        rows_with_calibrated_path_prob: summary.rows_with_calibrated_path_prob,
        summary_path: summary.summary_path,
        csv_path: Some(summary.csv_path),
        jsonl_path: Some(summary.jsonl_path),
        warnings,
        summary_line: summary.summary_line,
    })
}

pub fn policy_training_status_command(
    state_dir: &str,
    symbol: &str,
    provider_filter: Option<&str>,
) -> Result<()> {
    let surface = policy_training_status(state_dir, symbol, provider_filter)?;
    println!("{}", serde_json::to_string_pretty(&surface)?);
    Ok(())
}

fn collect_training_rows(state_dir: &str, symbol: &str) -> Result<CisdRbCollectedTrainingRows> {
    let analyze_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let update_runs: Vec<UpdateRunRecord> =
        load_state_or_default(state_dir, symbol, UPDATE_RUNS_FILE)?;
    let legacy_packets_by_run_id = load_legacy_cisd_rb_packets(state_dir, symbol)?;
    let analyze_by_id = analyze_runs
        .iter()
        .map(|run| (run.run_id.clone(), run))
        .collect::<BTreeMap<_, _>>();

    let mut bbn_rows = Vec::new();
    let mut catboost_rows = Vec::new();

    for update in &update_runs {
        let Some(analyze_run_id) = update.consumed_analyze_run_id.as_deref() else {
            continue;
        };
        let Some(analyze) = analyze_by_id.get(analyze_run_id) else {
            continue;
        };
        let packet = decode_entry_model_packet::<CisdRbEntryModelPacket>(
            &analyze.entry_model_packets,
            CISD_RB_SETUP_MODEL_ID,
        )
        .or_else(|| legacy_packets_by_run_id.get(analyze_run_id).cloned());
        let Some(packet) = packet else {
            continue;
        };
        let bins = bin_cisd_rb_for_bbn(&packet);
        let hmm = analyze.regime_probs.unwrap_or(RegimeProbs {
            accumulation: 0.0,
            manipulation_expansion: 0.0,
            distribution: 0.0,
        });
        bbn_rows.push(build_bbn_training_row(analyze, update, &packet, &bins));
        catboost_rows.push(build_catboost_training_row(
            analyze, update, &packet, &bins, &hmm,
        ));
    }

    Ok(CisdRbCollectedTrainingRows {
        analyze_runs: analyze_runs.len(),
        update_runs: update_runs.len(),
        bbn_rows,
        catboost_rows,
    })
}

fn collect_breaker_training_rows(
    state_dir: &str,
    symbol: &str,
) -> Result<BreakerCollectedTrainingRows> {
    let analyze_runs: Vec<AnalyzeRunRecord> =
        load_state_or_default(state_dir, symbol, ANALYZE_RUNS_FILE)?;
    let update_runs: Vec<UpdateRunRecord> =
        load_state_or_default(state_dir, symbol, UPDATE_RUNS_FILE)?;
    let analyze_by_id = analyze_runs
        .iter()
        .map(|run| (run.run_id.clone(), run))
        .collect::<BTreeMap<_, _>>();

    let mut bbn_rows = Vec::new();
    let mut catboost_rows = Vec::new();

    for update in &update_runs {
        let Some(analyze_run_id) = update.consumed_analyze_run_id.as_deref() else {
            continue;
        };
        let Some(analyze) = analyze_by_id.get(analyze_run_id) else {
            continue;
        };
        let Some(packet) = decode_entry_model_packet::<BreakerRbEntryModelPacket>(
            &analyze.entry_model_packets,
            BREAKER_RB_SETUP_MODEL_ID,
        ) else {
            continue;
        };
        let bins = bin_breaker_rb_for_bbn(&packet);
        let hmm = analyze.regime_probs.unwrap_or(RegimeProbs {
            accumulation: 0.0,
            manipulation_expansion: 0.0,
            distribution: 0.0,
        });
        bbn_rows.push(build_breaker_bbn_training_row(
            analyze, update, &packet, &bins,
        ));
        catboost_rows.push(build_breaker_catboost_training_row(
            analyze, update, &packet, &bins, &hmm,
        ));
    }

    Ok(BreakerCollectedTrainingRows {
        analyze_runs: analyze_runs.len(),
        update_runs: update_runs.len(),
        bbn_rows,
        catboost_rows,
    })
}

fn persist_training_rows(
    state_dir: &str,
    symbol: &str,
    rows: &EntryModelTrainingRows,
) -> Result<()> {
    let symbol_dir = Path::new(state_dir).join(symbol).join(POLICY_TRAINING_DIR);
    fs::create_dir_all(&symbol_dir)?;
    save_text_state(
        state_dir,
        symbol,
        &format!("{POLICY_TRAINING_DIR}/{}", rows.bbn_training_filename),
        &rows.bbn_csv,
    )?;
    save_text_state(
        state_dir,
        symbol,
        &format!("{POLICY_TRAINING_DIR}/{}", rows.catboost_training_filename),
        &rows.catboost_csv,
    )?;
    save_text_state(
        state_dir,
        symbol,
        &format!("{POLICY_TRAINING_DIR}/{}", rows.summary_filename),
        &rows.summary_json,
    )?;
    Ok(())
}

fn load_legacy_cisd_rb_packets(
    state_dir: &str,
    symbol: &str,
) -> Result<BTreeMap<String, CisdRbEntryModelPacket>> {
    let path = Path::new(state_dir).join(symbol).join(ANALYZE_RUNS_FILE);
    if !path.exists() {
        return Ok(BTreeMap::new());
    }
    let raw = fs::read_to_string(&path)?;
    let value: Value = serde_json::from_str(&raw)?;
    let Some(items) = value.as_array() else {
        return Ok(BTreeMap::new());
    };
    let mut out = BTreeMap::new();
    for item in items {
        let Some(run_id) = item.get("run_id").and_then(Value::as_str) else {
            continue;
        };
        let Some(packet_value) = item.get("cisd_rb_entry_model_packet") else {
            continue;
        };
        let Some(packet) =
            serde_json::from_value::<CisdRbEntryModelPacket>(packet_value.clone()).ok()
        else {
            continue;
        };
        out.insert(run_id.to_string(), packet);
    }
    Ok(out)
}

fn build_bbn_status(rows: &[CisdRbBbnTrainingRow]) -> BbnTrainingStatusSurface {
    let outcome_counts = count_strings(rows.iter().map(|row| row.realized_outcome.as_str()));
    let entry_quality_counts = count_strings(rows.iter().map(|row| row.entry_quality.as_str()));
    let trigger_confirmation_quality_counts = count_strings(
        rows.iter()
            .map(|row| row.trigger_confirmation_quality.as_str()),
    );
    let session_quality_counts = count_strings(rows.iter().map(|row| row.session_quality.as_str()));
    build_generic_bbn_status(
        rows.len(),
        outcome_counts,
        entry_quality_counts,
        trigger_confirmation_quality_counts,
        session_quality_counts,
    )
}

fn build_generic_bbn_status(
    rows_len: usize,
    outcome_counts: BTreeMap<String, usize>,
    entry_quality_counts: BTreeMap<String, usize>,
    trigger_confirmation_quality_counts: BTreeMap<String, usize>,
    session_quality_counts: BTreeMap<String, usize>,
) -> BbnTrainingStatusSurface {
    let mut warnings = Vec::new();
    if rows_len < 30 {
        warnings.push(format!("matched_rows_below_minimum: {}", rows_len));
    }
    if outcome_counts.len() < 2 {
        warnings.push("outcome_labels_do_not_cover_win_loss".to_string());
    }
    if entry_quality_counts.len() < 2 {
        warnings.push("entry_quality_bins_have_low_diversity".to_string());
    }
    if trigger_confirmation_quality_counts.len() < 2 {
        warnings.push("trigger_confirmation_bins_have_low_diversity".to_string());
    }
    let ready = warnings.is_empty();
    BbnTrainingStatusSurface {
        ready,
        rows: rows_len,
        outcome_counts,
        entry_quality_counts,
        trigger_confirmation_quality_counts,
        session_quality_counts,
        warnings,
    }
}

fn build_catboost_status(rows: &[CisdRbCatBoostTrainingRow]) -> CatBoostTrainingStatusSurface {
    let outcome_counts = count_strings(rows.iter().map(|row| row.realized_outcome.as_str()));
    let numeric_ranges = BTreeMap::from([
        (
            "cisd_impulse_atr".to_string(),
            range_of(rows.iter().map(|row| row.cisd_impulse_atr)),
        ),
        (
            "rb_wick_body_ratio".to_string(),
            range_of(rows.iter().map(|row| row.rb_wick_body_ratio)),
        ),
        (
            "bars_between_cisd_and_rb".to_string(),
            range_of(rows.iter().map(|row| row.bars_between_cisd_and_rb)),
        ),
        (
            "ema19_distance_bps".to_string(),
            range_of(rows.iter().map(|row| row.ema19_distance_bps)),
        ),
        (
            "realized_vol_zscore".to_string(),
            range_of(rows.iter().map(|row| row.realized_vol_zscore)),
        ),
    ]);
    build_generic_catboost_status(rows.len(), outcome_counts, numeric_ranges)
}

fn build_generic_catboost_status(
    rows_len: usize,
    outcome_counts: BTreeMap<String, usize>,
    numeric_ranges: BTreeMap<String, NumericRangeSummary>,
) -> CatBoostTrainingStatusSurface {
    let varying_features = numeric_ranges
        .values()
        .filter(|range| range.span > 0.0)
        .count();
    let mut warnings = Vec::new();
    if rows_len < 50 {
        warnings.push(format!(
            "matched_rows_below_recommended_minimum: {}",
            rows_len
        ));
    }
    if outcome_counts.len() < 2 {
        warnings.push("outcome_labels_do_not_cover_win_loss".to_string());
    }
    if varying_features < 4 {
        warnings.push(format!(
            "numeric_feature_variation_too_low: {varying_features}/5 varying"
        ));
    }
    let ready = warnings.is_empty();
    CatBoostTrainingStatusSurface {
        ready,
        rows: rows_len,
        outcome_counts,
        numeric_ranges,
        warnings,
    }
}

fn build_provider_summary_line(
    label: &str,
    matched_rows: usize,
    bbn: &BbnTrainingStatusSurface,
    catboost: &CatBoostTrainingStatusSurface,
) -> String {
    if bbn.ready && catboost.ready {
        format!(
            "{label} policy training looks healthy for BBN and CatBoost: matched_rows={} outcomes={}",
            matched_rows,
            format_counts(&catboost.outcome_counts)
        )
    } else if !bbn.ready && !catboost.ready {
        format!(
            "{label} policy training is not ready for either BBN or CatBoost: matched_rows={} bbn_warnings={} catboost_warnings={}",
            matched_rows,
            bbn.warnings.join("; "),
            catboost.warnings.join("; ")
        )
    } else if !bbn.ready {
        format!(
            "{label} policy training is CatBoost-usable but BBN-weak: matched_rows={} bbn_warnings={}",
            matched_rows,
            bbn.warnings.join("; ")
        )
    } else {
        format!(
            "{label} policy training is BBN-usable but CatBoost-weak: matched_rows={} catboost_warnings={}",
            matched_rows,
            catboost.warnings.join("; ")
        )
    }
}

fn count_strings<'a>(values: impl Iterator<Item = &'a str>) -> BTreeMap<String, usize> {
    let mut counts = BTreeMap::new();
    for value in values {
        *counts.entry(value.to_string()).or_insert(0) += 1;
    }
    counts
}

fn range_of(values: impl Iterator<Item = f64>) -> NumericRangeSummary {
    let vals = values.collect::<Vec<_>>();
    if vals.is_empty() {
        return NumericRangeSummary::default();
    }
    let min = vals.iter().copied().fold(f64::INFINITY, f64::min);
    let max = vals.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    NumericRangeSummary {
        min,
        max,
        span: max - min,
    }
}

fn format_counts(counts: &BTreeMap<String, usize>) -> String {
    counts
        .iter()
        .map(|(label, count)| format!("{label}={count}"))
        .collect::<Vec<_>>()
        .join(",")
}

fn build_bbn_training_row(
    analyze: &AnalyzeRunRecord,
    update: &UpdateRunRecord,
    packet: &CisdRbEntryModelPacket,
    bins: &CisdRbBbnEvidence,
) -> CisdRbBbnTrainingRow {
    CisdRbBbnTrainingRow {
        analyze_run_id: analyze.run_id.clone(),
        update_run_id: update.run_id.clone(),
        symbol: analyze.symbol.clone(),
        timeframe: packet.timeframe.clone(),
        setup_model_id: packet.setup_model_id.clone(),
        trend_alignment: bins.trend_alignment.clone(),
        liquidity_interaction_quality: bins.liquidity_interaction_quality.clone(),
        trigger_confirmation_quality: bins.trigger_confirmation_quality.clone(),
        session_quality: bins.session_quality.clone(),
        entry_quality: bins.entry_quality.clone(),
        evidence_quality_score: packet.evidence_quality_score,
        gating_status: analyze.pre_bayes_evidence_filter.gating_status.clone(),
        realized_outcome: update.realized_outcome.clone(),
    }
}

fn build_breaker_bbn_training_row(
    analyze: &AnalyzeRunRecord,
    update: &UpdateRunRecord,
    packet: &BreakerRbEntryModelPacket,
    bins: &BreakerRbBbnEvidence,
) -> BreakerRbBbnTrainingRow {
    BreakerRbBbnTrainingRow {
        analyze_run_id: analyze.run_id.clone(),
        update_run_id: update.run_id.clone(),
        symbol: analyze.symbol.clone(),
        timeframe: packet.timeframe.clone(),
        setup_model_id: packet.setup_model_id.clone(),
        trend_alignment: bins.trend_alignment.clone(),
        breaker_retest_quality: bins.breaker_retest_quality.clone(),
        session_quality: bins.session_quality.clone(),
        entry_quality: bins.entry_quality.clone(),
        evidence_quality_score: packet.evidence_quality_score,
        gating_status: analyze.pre_bayes_evidence_filter.gating_status.clone(),
        realized_outcome: update.realized_outcome.clone(),
    }
}

fn build_catboost_training_row(
    analyze: &AnalyzeRunRecord,
    update: &UpdateRunRecord,
    packet: &CisdRbEntryModelPacket,
    bins: &CisdRbBbnEvidence,
    hmm: &RegimeProbs,
) -> CisdRbCatBoostTrainingRow {
    let row = build_cisd_rb_catboost_feature_row(packet, hmm, bins);
    CisdRbCatBoostTrainingRow {
        analyze_run_id: analyze.run_id.clone(),
        update_run_id: update.run_id.clone(),
        symbol: analyze.symbol.clone(),
        timeframe: packet.timeframe.clone(),
        setup_model_id: row.setup_model_id,
        setup_progress_state: row.setup_progress_state,
        hmm_accumulation_prob: row.hmm_accumulation_prob,
        hmm_manipulation_expansion_prob: row.hmm_manipulation_expansion_prob,
        hmm_distribution_prob: row.hmm_distribution_prob,
        bbn_trend_alignment: row.bbn_trend_alignment,
        bbn_liquidity_interaction_quality: row.bbn_liquidity_interaction_quality,
        bbn_trigger_confirmation_quality: row.bbn_trigger_confirmation_quality,
        bbn_session_quality: row.bbn_session_quality,
        bbn_entry_quality: row.bbn_entry_quality,
        cisd_run_length_observed: row.cisd_run_length_observed,
        cisd_impulse_atr: row.cisd_impulse_atr,
        cisd_body_ratio_mean: row.cisd_body_ratio_mean,
        rb_wick_body_ratio: row.rb_wick_body_ratio,
        rb_close_location_ratio: row.rb_close_location_ratio,
        bars_between_cisd_and_rb: row.bars_between_cisd_and_rb,
        seq_window_hit: row.seq_window_hit,
        ema19_distance_bps: row.ema19_distance_bps,
        atr14_bps: row.atr14_bps,
        realized_vol_zscore: row.realized_vol_zscore,
        evidence_quality_score: row.evidence_quality_score,
        session_label: row.session_label,
        realized_outcome: update.realized_outcome.clone(),
    }
}

fn build_breaker_catboost_training_row(
    analyze: &AnalyzeRunRecord,
    update: &UpdateRunRecord,
    packet: &BreakerRbEntryModelPacket,
    bins: &BreakerRbBbnEvidence,
    hmm: &RegimeProbs,
) -> BreakerRbCatBoostTrainingRow {
    let row = build_breaker_rb_catboost_feature_row(packet, hmm, bins);
    BreakerRbCatBoostTrainingRow {
        analyze_run_id: analyze.run_id.clone(),
        update_run_id: update.run_id.clone(),
        symbol: analyze.symbol.clone(),
        timeframe: packet.timeframe.clone(),
        setup_model_id: row.setup_model_id,
        setup_progress_state: row.setup_progress_state,
        hmm_accumulation_prob: row.hmm_accumulation_prob,
        hmm_manipulation_expansion_prob: row.hmm_manipulation_expansion_prob,
        hmm_distribution_prob: row.hmm_distribution_prob,
        bbn_trend_alignment: row.bbn_trend_alignment,
        bbn_breaker_retest_quality: row.bbn_breaker_retest_quality,
        bbn_session_quality: row.bbn_session_quality,
        bbn_entry_quality: row.bbn_entry_quality,
        bars_between_violation_and_retest: row.bars_between_violation_and_retest,
        breaker_width_bps: row.breaker_width_bps,
        retest_reclaim_bps: row.retest_reclaim_bps,
        rb_wick_body_ratio: row.rb_wick_body_ratio,
        rb_close_location_ratio: row.rb_close_location_ratio,
        ema19_distance_bps: row.ema19_distance_bps,
        atr14_bps: row.atr14_bps,
        realized_vol_zscore: row.realized_vol_zscore,
        evidence_quality_score: row.evidence_quality_score,
        session_label: row.session_label,
        realized_outcome: update.realized_outcome.clone(),
    }
}

fn render_bbn_training_csv(rows: &[CisdRbBbnTrainingRow]) -> String {
    let mut out = String::from(
        "analyze_run_id,update_run_id,symbol,timeframe,setup_model_id,trend_alignment,liquidity_interaction_quality,trigger_confirmation_quality,session_quality,entry_quality,evidence_quality_score,gating_status,realized_outcome\n",
    );
    for row in rows {
        out.push_str(&format!(
            "{},{},{},{},{},{},{},{},{},{},{:.6},{},{}\n",
            row.analyze_run_id,
            row.update_run_id,
            row.symbol,
            row.timeframe,
            row.setup_model_id,
            row.trend_alignment,
            row.liquidity_interaction_quality,
            row.trigger_confirmation_quality,
            row.session_quality,
            row.entry_quality,
            row.evidence_quality_score,
            row.gating_status,
            row.realized_outcome
        ));
    }
    out
}

fn render_catboost_training_csv(rows: &[CisdRbCatBoostTrainingRow]) -> String {
    let mut out = String::from(
        "analyze_run_id,update_run_id,symbol,timeframe,setup_model_id,setup_progress_state,hmm_accumulation_prob,hmm_manipulation_expansion_prob,hmm_distribution_prob,bbn_trend_alignment,bbn_liquidity_interaction_quality,bbn_trigger_confirmation_quality,bbn_session_quality,bbn_entry_quality,cisd_run_length_observed,cisd_impulse_atr,cisd_body_ratio_mean,rb_wick_body_ratio,rb_close_location_ratio,bars_between_cisd_and_rb,seq_window_hit,ema19_distance_bps,atr14_bps,realized_vol_zscore,evidence_quality_score,session_label,realized_outcome\n",
    );
    for row in rows {
        out.push_str(&format!(
            "{},{},{},{},{},{},{:.6},{:.6},{:.6},{},{},{},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{},{:.6},{:.6},{:.6},{:.6},{},{}\n",
            row.analyze_run_id,
            row.update_run_id,
            row.symbol,
            row.timeframe,
            row.setup_model_id,
            row.setup_progress_state,
            row.hmm_accumulation_prob,
            row.hmm_manipulation_expansion_prob,
            row.hmm_distribution_prob,
            row.bbn_trend_alignment,
            row.bbn_liquidity_interaction_quality,
            row.bbn_trigger_confirmation_quality,
            row.bbn_session_quality,
            row.bbn_entry_quality,
            row.cisd_run_length_observed,
            row.cisd_impulse_atr,
            row.cisd_body_ratio_mean,
            row.rb_wick_body_ratio,
            row.rb_close_location_ratio,
            row.bars_between_cisd_and_rb,
            row.seq_window_hit,
            row.ema19_distance_bps,
            row.atr14_bps,
            row.realized_vol_zscore,
            row.evidence_quality_score,
            row.session_label,
            row.realized_outcome
        ));
    }
    out
}

fn render_breaker_bbn_training_csv(rows: &[BreakerRbBbnTrainingRow]) -> String {
    let mut out = String::from(
        "analyze_run_id,update_run_id,symbol,timeframe,setup_model_id,trend_alignment,breaker_retest_quality,session_quality,entry_quality,evidence_quality_score,gating_status,realized_outcome\n",
    );
    for row in rows {
        out.push_str(&format!(
            "{},{},{},{},{},{},{},{},{},{:.6},{},{}\n",
            row.analyze_run_id,
            row.update_run_id,
            row.symbol,
            row.timeframe,
            row.setup_model_id,
            row.trend_alignment,
            row.breaker_retest_quality,
            row.session_quality,
            row.entry_quality,
            row.evidence_quality_score,
            row.gating_status,
            row.realized_outcome
        ));
    }
    out
}

fn render_breaker_catboost_training_csv(rows: &[BreakerRbCatBoostTrainingRow]) -> String {
    let mut out = String::from(
        "analyze_run_id,update_run_id,symbol,timeframe,setup_model_id,setup_progress_state,hmm_accumulation_prob,hmm_manipulation_expansion_prob,hmm_distribution_prob,bbn_trend_alignment,bbn_breaker_retest_quality,bbn_session_quality,bbn_entry_quality,bars_between_violation_and_retest,breaker_width_bps,retest_reclaim_bps,rb_wick_body_ratio,rb_close_location_ratio,ema19_distance_bps,atr14_bps,realized_vol_zscore,evidence_quality_score,session_label,realized_outcome\n",
    );
    for row in rows {
        out.push_str(&format!(
            "{},{},{},{},{},{},{:.6},{:.6},{:.6},{},{},{},{},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{:.6},{},{}\n",
            row.analyze_run_id,
            row.update_run_id,
            row.symbol,
            row.timeframe,
            row.setup_model_id,
            row.setup_progress_state,
            row.hmm_accumulation_prob,
            row.hmm_manipulation_expansion_prob,
            row.hmm_distribution_prob,
            row.bbn_trend_alignment,
            row.bbn_breaker_retest_quality,
            row.bbn_session_quality,
            row.bbn_entry_quality,
            row.bars_between_violation_and_retest,
            row.breaker_width_bps,
            row.retest_reclaim_bps,
            row.rb_wick_body_ratio,
            row.rb_close_location_ratio,
            row.ema19_distance_bps,
            row.atr14_bps,
            row.realized_vol_zscore,
            row.evidence_quality_score,
            row.session_label,
            row.realized_outcome
        ));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::application::entry_models::{
        insert_entry_model_packet, EntryModelPacketStore, CISD_RB_SETUP_MODEL_ID,
    };
    use crate::state::{save_state, AnalyzeRunRecord, UpdateRunRecord};

    fn sample_packet() -> CisdRbEntryModelPacket {
        CisdRbEntryModelPacket {
            setup_model_id: CISD_RB_SETUP_MODEL_ID.to_string(),
            symbol: "NQ".to_string(),
            timeframe: "5m".to_string(),
            direction: "long".to_string(),
            cisd_bars_required: 3,
            cisd_run_length_observed: 3,
            cisd_impulse_atr: 1.2,
            cisd_body_ratio_mean: 0.7,
            rb_wick_body_ratio: 1.3,
            rb_close_location_ratio: 0.7,
            rb_bullish: true,
            bars_between_cisd_and_rb: 4,
            seq_window_limit: 18,
            seq_window_hit: true,
            ema19_distance_bps: 12.0,
            atr14_bps: 25.0,
            realized_vol_zscore: 0.4,
            session_label: "ny_open".to_string(),
            liquidity_swept: true,
            mss_up: true,
            filtered_market_regime_label: "bull".to_string(),
            filtered_liquidity_context_label: "favorable".to_string(),
            filtered_resonance_label: "aligned".to_string(),
            evidence_quality_score: 0.72,
        }
    }

    #[test]
    fn exports_training_tables_from_matched_histories() {
        let temp = tempfile::tempdir().unwrap();
        let mut entry_model_packets = EntryModelPacketStore::default();
        insert_entry_model_packet(
            &mut entry_model_packets,
            CISD_RB_SETUP_MODEL_ID,
            &sample_packet(),
        )
        .unwrap();
        let analyze = AnalyzeRunRecord {
            run_id: "analyze:1".to_string(),
            symbol: "NQ".to_string(),
            regime_probs: Some(RegimeProbs {
                accumulation: 0.1,
                manipulation_expansion: 0.8,
                distribution: 0.1,
            }),
            entry_model_packets,
            pre_bayes_evidence_filter: crate::state::PreBayesEvidenceFilter {
                gating_status: "pass_hard".to_string(),
                ..Default::default()
            },
            ..AnalyzeRunRecord::default()
        };
        let update = UpdateRunRecord {
            run_id: "update:1".to_string(),
            symbol: "NQ".to_string(),
            consumed_analyze_run_id: Some("analyze:1".to_string()),
            realized_outcome: "win".to_string(),
            ..UpdateRunRecord::default()
        };
        save_state(temp.path(), "NQ", ANALYZE_RUNS_FILE, &[analyze]).unwrap();
        save_state(temp.path(), "NQ", UPDATE_RUNS_FILE, &[update]).unwrap();

        let summary = export_cisd_rb_training_tables(temp.path().to_str().unwrap(), "NQ").unwrap();
        assert_eq!(summary.matched_rows, 1);
        assert!(Path::new(&summary.bbn_training_path).exists());
        assert!(Path::new(&summary.catboost_training_path).exists());
    }

    #[test]
    fn builds_status_surface_from_matched_histories() {
        let temp = tempfile::tempdir().unwrap();
        let mut entry_model_packets = EntryModelPacketStore::default();
        insert_entry_model_packet(
            &mut entry_model_packets,
            CISD_RB_SETUP_MODEL_ID,
            &sample_packet(),
        )
        .unwrap();
        let analyze = AnalyzeRunRecord {
            run_id: "analyze:1".to_string(),
            symbol: "NQ".to_string(),
            regime_probs: Some(RegimeProbs {
                accumulation: 0.1,
                manipulation_expansion: 0.8,
                distribution: 0.1,
            }),
            entry_model_packets,
            pre_bayes_evidence_filter: crate::state::PreBayesEvidenceFilter {
                gating_status: "pass_hard".to_string(),
                ..Default::default()
            },
            ..AnalyzeRunRecord::default()
        };
        let update_win = UpdateRunRecord {
            run_id: "update:1".to_string(),
            symbol: "NQ".to_string(),
            consumed_analyze_run_id: Some("analyze:1".to_string()),
            realized_outcome: "win".to_string(),
            ..UpdateRunRecord::default()
        };
        let update_loss = UpdateRunRecord {
            run_id: "update:2".to_string(),
            symbol: "NQ".to_string(),
            consumed_analyze_run_id: Some("analyze:1".to_string()),
            realized_outcome: "loss".to_string(),
            ..UpdateRunRecord::default()
        };
        save_state(temp.path(), "NQ", ANALYZE_RUNS_FILE, &[analyze]).unwrap();
        save_state(
            temp.path(),
            "NQ",
            UPDATE_RUNS_FILE,
            &[update_win, update_loss],
        )
        .unwrap();

        let status = cisd_rb_training_status(temp.path().to_str().unwrap(), "NQ").unwrap();
        assert_eq!(status.matched_rows, 2);
        assert_eq!(status.setup_model_ids.get(CISD_RB_SETUP_MODEL_ID), Some(&2));
        assert!(status.summary_line.contains("matched_rows=2"));
        assert!(!status.bbn.ready);
        assert!(!status.catboost.ready);
    }

    #[test]
    fn policy_training_status_lists_registered_providers() {
        let temp = tempfile::tempdir().unwrap();
        let status = policy_training_status(temp.path().to_str().unwrap(), "NQ", None).unwrap();
        let provider_ids = status
            .providers
            .iter()
            .map(|provider| provider.provider_id.as_str())
            .collect::<Vec<_>>();
        assert!(provider_ids.contains(&CISD_RB_SETUP_MODEL_ID));
        assert!(provider_ids.contains(&BREAKER_RB_SETUP_MODEL_ID));
        assert!(!status.structural_path_ranking_target.export_ready);
        assert!(status
            .structural_path_ranking_target
            .warnings
            .contains(&"structural_path_ranking_target_export_missing".to_string()));
    }

    #[test]
    fn structural_path_ranking_target_training_status_reads_summary() {
        let temp = tempfile::tempdir().unwrap();
        let summary_dir = temp.path().join("NQ").join(POLICY_TRAINING_DIR);
        std::fs::create_dir_all(&summary_dir).unwrap();
        let summary = StructuralPathRankingTargetExportSummary {
            symbol: "NQ".to_string(),
            rows: 3,
            candidate_set_id: "structural-candidates:NQ:test".to_string(),
            candidate_set_size: 3,
            rows_with_propensity_estimate: 2,
            rows_with_calibrated_path_prob: 0,
            rows_with_path_prob_lower_bound: 0,
            csv_path: summary_dir
                .join("structural_path_ranking_target.csv")
                .to_string_lossy()
                .to_string(),
            jsonl_path: summary_dir
                .join("structural_path_ranking_target.jsonl")
                .to_string_lossy()
                .to_string(),
            summary_path: summary_dir
                .join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE)
                .to_string_lossy()
                .to_string(),
            summary_line: "structural_path_ranking_target rows=3".to_string(),
            ..StructuralPathRankingTargetExportSummary::default()
        };
        std::fs::write(
            summary_dir.join(STRUCTURAL_PATH_RANKING_TARGET_SUMMARY_FILE),
            serde_json::to_string_pretty(&summary).unwrap(),
        )
        .unwrap();

        let status =
            structural_path_ranking_target_training_status(temp.path().to_str().unwrap(), "NQ")
                .unwrap();

        assert!(status.export_ready);
        assert!(!status.calibration_ready);
        assert_eq!(status.rows, 3);
        assert_eq!(
            status.candidate_set_id.as_deref(),
            Some("structural-candidates:NQ:test")
        );
        assert_eq!(status.rows_with_propensity_estimate, 2);
        assert!(status
            .warnings
            .contains(&"structural_path_ranking_target_calibration_not_fitted".to_string()));
    }
}
