use std::collections::BTreeMap;
use std::path::Path;

use serde::{Deserialize, Serialize};

use super::{
    CatBoostCompatiblePolicyEngine, EnsembleDecision, EnsembleVoteArtifact, PolicyEngine,
    PolicyFeatureVector, PosteriorAuditArtifact,
};
use crate::domain::belief::BeliefReportPacket;
use crate::factor_lab::research::ResearchReport;
use crate::state::{
    load_ensemble_executor_scorecards, load_ensemble_vote_history, DatasetComparability,
    EnsembleExecutorScorecard, RunProvenance,
};

const DEFAULT_CATBOOST_WEIGHT: f64 = 0.55;
const DEFAULT_XGBOOST_WEIGHT: f64 = 0.45;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AnalyzeEnsembleVoteInput {
    pub symbol: String,
    pub state_dir: Option<String>,
    pub recommended_next_command: String,
    pub provenance: RunProvenance,
    pub dataset_comparability: DatasetComparability,
    pub belief: BeliefReportPacket,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EnsembleExecutorDecision {
    pub executor: String,
    pub action: String,
    pub confidence: f64,
    pub recommended_command: Option<String>,
    pub split_explanations: Vec<String>,
}

pub trait VotingAggregator {
    fn aggregate(
        &self,
        input: &AnalyzeEnsembleVoteInput,
        posterior: &PosteriorAuditArtifact,
        executors: &[EnsembleExecutorDecision],
        weights: &[f64],
    ) -> EnsembleDecision;
}

#[derive(Debug, Clone, Copy, Default)]
pub struct WeightedVotingAggregator;

fn normalization_status(probabilities: &BTreeMap<String, f64>) -> String {
    if probabilities.is_empty() {
        return "missing_probabilities".to_string();
    }
    let sum: f64 = probabilities.values().sum();
    if (sum - 1.0).abs() <= 0.05 {
        "normalized".to_string()
    } else {
        format!("sum_out_of_band:{sum:.6}")
    }
}

fn dominant_probability(probabilities: &BTreeMap<String, f64>) -> f64 {
    probabilities.values().copied().fold(0.0_f64, f64::max)
}

fn decide_action(active_regime: &str, regime_confidence: f64) -> String {
    match active_regime {
        "trend" if regime_confidence >= 0.55 => "execute_follow_through".to_string(),
        "stress" if regime_confidence >= 0.45 => "de_risk_and_reduce_size".to_string(),
        "transition" => "wait_for_confirmation".to_string(),
        "range" => "favor_mean_reversion_only".to_string(),
        _ => "observe".to_string(),
    }
}

fn fallback_command(symbol: &str, action: &str) -> String {
    match action {
        "execute_follow_through" => format!(
            "ict-engine update --symbol {symbol} --outcome <win|loss|breakeven> --entry-signal medium"
        ),
        "de_risk_and_reduce_size" => {
            format!("ict-engine workflow-status --symbol {symbol} --phase human-next")
        }
        "wait_for_confirmation" => format!(
            "ict-engine analyze --symbol {symbol} --data-htf <htf.json> --data-mtf <mtf.json> --data-ltf <ltf.json>"
        ),
        "favor_mean_reversion_only" => format!(
            "ict-engine factor-research --symbol {symbol} --data <historical.json> --objective generic"
        ),
        _ => format!("ict-engine workflow-status --symbol {symbol} --phase human-next"),
    }
}

fn summarize_executor(decision: &EnsembleExecutorDecision) -> String {
    format!(
        "executor={} action={} confidence={:.3}",
        decision.executor, decision.action, decision.confidence
    )
}

impl VotingAggregator for WeightedVotingAggregator {
    fn aggregate(
        &self,
        input: &AnalyzeEnsembleVoteInput,
        posterior: &PosteriorAuditArtifact,
        executors: &[EnsembleExecutorDecision],
        weights: &[f64],
    ) -> EnsembleDecision {
        let weighted = executors
            .iter()
            .zip(weights.iter().copied())
            .map(|(decision, weight)| {
                (
                    decision,
                    weight,
                    decision.confidence * weight,
                    format!("{} weight={:.2}", summarize_executor(decision), weight),
                )
            })
            .collect::<Vec<_>>();
        let final_action = if weighted
            .windows(2)
            .all(|pair| pair[0].0.action == pair[1].0.action)
        {
            weighted
                .first()
                .map(|item| item.0.action.clone())
                .unwrap_or_else(|| "observe".to_string())
        } else {
            weighted
                .iter()
                .max_by(|a, b| a.2.partial_cmp(&b.2).unwrap_or(std::cmp::Ordering::Equal))
                .map(|item| item.0.action.clone())
                .unwrap_or_else(|| "observe".to_string())
        };
        let consensus_strength = if weighted
            .windows(2)
            .all(|pair| pair[0].0.action == pair[1].0.action)
        {
            weighted.iter().map(|item| item.2).sum::<f64>().clamp(0.0, 1.0)
        } else if weighted.len() >= 2 {
            let mut scores = weighted.iter().map(|item| item.2).collect::<Vec<_>>();
            scores.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
            (scores[0] - scores[1]).abs().clamp(0.0, 1.0)
        } else {
            0.0
        };
        let recommended_command = weighted
            .iter()
            .find_map(|item| item.0.recommended_command.clone())
            .filter(|value| !value.trim().is_empty())
            .unwrap_or_else(|| {
                if input.recommended_next_command.trim().is_empty() {
                    fallback_command(&input.symbol, &final_action)
                } else {
                    input.recommended_next_command.clone()
                }
            });
        let disagreement_flags = if weighted
            .windows(2)
            .all(|pair| pair[0].0.action == pair[1].0.action)
        {
            Vec::new()
        } else {
            weighted
                .windows(2)
                .map(|pair| {
                    format!(
                        "executor_disagreement:{}_vs_{}",
                        pair[0].0.action, pair[1].0.action
                    )
                })
                .collect()
        };
        EnsembleDecision {
            final_action: final_action.clone(),
            recommended_command: recommended_command.clone(),
            human_next_triage: format!(
                "ensemble_action={} consensus={:.3} regime={} command={}",
                final_action, consensus_strength, posterior.active_regime, recommended_command
            ),
            confidence: weighted.iter().map(|item| item.2).sum::<f64>().clamp(0.0, 1.0),
            consensus_strength,
            disagreement_flags,
            executor_summaries: weighted.iter().map(|item| item.3.clone()).collect(),
            split_explanations: executors
                .iter()
                .flat_map(|item| item.split_explanations.clone())
                .collect(),
        }
    }
}

fn policy_features_from_input(input: &AnalyzeEnsembleVoteInput) -> PolicyFeatureVector {
    let gate = input
        .belief
        .regime_posterior
        .active_regime
        .clone()
        .unwrap_or_else(|| "observe_only".to_string());
    let direction = if input.recommended_next_command.contains(" update ")
        || input.recommended_next_command.contains("--outcome")
    {
        "Bull".to_string()
    } else {
        "Observe".to_string()
    };
    PolicyFeatureVector {
        factor_alignment: input
            .belief
            .regime_posterior
            .market_behavior_profile
            .clone()
            .unwrap_or_else(|| "mixed".to_string()),
        factor_uncertainty: if input.belief.regime_posterior.confidence.unwrap_or(0.5) >= 0.6 {
            "low".to_string()
        } else {
            "high".to_string()
        },
        gating_status: gate,
        selected_entry_quality: "medium".to_string(),
        recommended_command: input.recommended_next_command.clone(),
        evidence_quality_score: input.belief.regime_posterior.confidence.unwrap_or(0.5),
        selected_direction: direction,
        risk_reward: 2.0,
        kelly_fraction: 0.1,
    }
}

fn load_named_policy_or_placeholder(filename: &str) -> CatBoostCompatiblePolicyEngine {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src/application/orchestration")
        .join(filename);
    CatBoostCompatiblePolicyEngine::load_from_file(&path)
        .unwrap_or_else(|_| CatBoostCompatiblePolicyEngine::placeholder())
}

fn policy_decision_to_executor(
    name: &str,
    decision: super::PolicyDecisionArtifact,
) -> EnsembleExecutorDecision {
    let confidence = match decision.confidence_band.as_str() {
        "high" => 0.85,
        "medium" => 0.60,
        _ => 0.35,
    };
    EnsembleExecutorDecision {
        executor: name.to_string(),
        action: decision.action,
        confidence,
        recommended_command: Some(decision.recommended_command),
        split_explanations: decision.split_trace,
    }
}

fn load_canonical_executor_scorecards(
    state_dir: &str,
    symbol: &str,
) -> Vec<EnsembleExecutorScorecard> {
    let persisted = load_ensemble_executor_scorecards(state_dir, symbol).unwrap_or_default();
    if !persisted.is_empty() {
        return persisted;
    }
    load_ensemble_vote_history(state_dir, symbol)
        .unwrap_or_default()
        .into_iter()
        .rev()
        .find_map(|record| {
            if record.executor_scorecards.is_empty() {
                None
            } else {
                Some(record.executor_scorecards)
            }
        })
        .unwrap_or_default()
}

fn historical_executor_weights(input: &AnalyzeEnsembleVoteInput) -> (f64, f64) {
    let Some(state_dir) = input.state_dir.as_deref() else {
        return (DEFAULT_CATBOOST_WEIGHT, DEFAULT_XGBOOST_WEIGHT);
    };
    let scorecards = load_canonical_executor_scorecards(state_dir, &input.symbol);
    if !scorecards.is_empty() {
        return historical_executor_weights_from_scorecards(&scorecards);
    }
    let path = Path::new(state_dir)
        .join(&input.symbol)
        .join("artifact_ledger.json");
    let Ok(raw) = std::fs::read_to_string(path) else {
        return (DEFAULT_CATBOOST_WEIGHT, DEFAULT_XGBOOST_WEIGHT);
    };
    let Ok(entries) = serde_json::from_str::<Vec<crate::state::ArtifactLedgerEntry>>(&raw) else {
        return (DEFAULT_CATBOOST_WEIGHT, DEFAULT_XGBOOST_WEIGHT);
    };
    historical_executor_weights_from_entries(&entries)
}

fn historical_executor_weights_from_scorecards(
    scorecards: &[EnsembleExecutorScorecard],
) -> (f64, f64) {
    let mut catboost_score = 0.0;
    let mut xgboost_score = 0.0;
    for scorecard in scorecards {
        let total = scorecard.wins + scorecard.losses + scorecard.breakevens;
        let activity_bias = if total == 0 {
            0.1
        } else {
            ((scorecard.wins as f64 + scorecard.validated_positive as f64)
                - (scorecard.losses as f64 + scorecard.validated_negative as f64 * 0.8))
                .max(0.0)
                / total as f64
        };
        let quality_bias = (scorecard.cumulative_quality_score.max(0) as f64 / 1000.0).max(0.0);
        let score =
            (activity_bias + quality_bias + scorecard.latest_weight_hint.unwrap_or(0.0)).max(0.05);
        if scorecard.executor.contains("catboost") {
            catboost_score += score;
        }
        if scorecard.executor.contains("xgboost") {
            xgboost_score += score;
        }
    }
    if (catboost_score + xgboost_score) <= f64::EPSILON {
        return (DEFAULT_CATBOOST_WEIGHT, DEFAULT_XGBOOST_WEIGHT);
    }
    let total = catboost_score + xgboost_score;
    (catboost_score / total, xgboost_score / total)
}

fn historical_executor_weights_from_entries(
    entries: &[crate::state::ArtifactLedgerEntry],
) -> (f64, f64) {
    let mut catboost_score = 0.0;
    let mut xgboost_score = 0.0;
    let mut seen = 0.0;
    for entry in entries
        .iter()
        .filter(|entry| entry.artifact_kind == "ensemble_vote")
    {
        seen += 1.0;
        let reason = entry.review_reason.to_ascii_lowercase();
        let quality = (entry.quality_score.max(0) as f64 / 100.0).clamp(0.0, 1.0);
        let outcome_bias = match (
            entry.consumption_regrade_status.as_deref(),
            entry.consumed_outcome.as_deref(),
        ) {
            (Some("validated_positive"), _) | (_, Some("win")) => 0.25,
            (Some("validated_negative"), _) | (_, Some("loss")) => -0.20,
            _ => 0.0,
        };
        let cat_present = reason.contains("catboost") || reason.contains("weight=0.55");
        let xgb_present = reason.contains("xgboost") || reason.contains("weight=0.45");
        if cat_present {
            catboost_score += (quality + outcome_bias).max(0.1);
        }
        if xgb_present {
            xgboost_score += (quality + outcome_bias).max(0.1);
        }
    }
    if seen == 0.0 || (catboost_score + xgboost_score) <= f64::EPSILON {
        return (DEFAULT_CATBOOST_WEIGHT, DEFAULT_XGBOOST_WEIGHT);
    }
    let total = catboost_score + xgboost_score;
    (catboost_score / total, xgboost_score / total)
}

pub fn build_posterior_audit_artifact(
    provenance: &RunProvenance,
    comparability: &DatasetComparability,
    belief: &BeliefReportPacket,
) -> PosteriorAuditArtifact {
    PosteriorAuditArtifact {
        posterior_version: "ensemble-audit-v1".to_string(),
        fingerprint: provenance.data_fingerprint.clone(),
        comparable: comparability.comparable,
        comparison_class: comparability.comparison_class.clone(),
        normalization_status: normalization_status(&belief.regime_posterior.probabilities),
        active_regime: belief
            .regime_posterior
            .active_regime
            .clone()
            .unwrap_or_else(|| "regime_unavailable".to_string()),
        confidence: belief.regime_posterior.confidence,
        probabilities: belief.regime_posterior.probabilities.clone(),
        evidence: belief.regime_posterior.evidence.clone(),
    }
}

pub fn build_stub_ensemble_vote_from_input(
    input: &AnalyzeEnsembleVoteInput,
) -> EnsembleVoteArtifact {
    let posterior = build_posterior_audit_artifact(
        &input.provenance,
        &input.dataset_comparability,
        &input.belief,
    );
    let dominant = dominant_probability(&posterior.probabilities);
    let active_regime = posterior.active_regime.clone();
    let features = policy_features_from_input(input);

    let catboost_engine = CatBoostCompatiblePolicyEngine::load_default_or_placeholder();
    let xgboost_engine = load_named_policy_or_placeholder("xgboost_policy.sample.json");

    let mut catboost_like =
        policy_decision_to_executor("catboost_file", catboost_engine.infer(&features));
    let mut xgboost_like =
        policy_decision_to_executor("xgboost_file", xgboost_engine.infer(&features));

    if catboost_like.action.eq_ignore_ascii_case("observe") && dominant >= 0.55 {
        catboost_like.action = decide_action(&active_regime, dominant);
        catboost_like.confidence = catboost_like
            .confidence
            .max((dominant + posterior.confidence.unwrap_or(dominant)) / 2.0);
        catboost_like
            .split_explanations
            .push(format!("posterior_override={active_regime}:{dominant:.3}"));
    }
    if xgboost_like.action.eq_ignore_ascii_case("observe") && dominant >= 0.60 {
        xgboost_like.action = decide_action(&active_regime, dominant);
        xgboost_like.confidence = xgboost_like.confidence.max(dominant);
        xgboost_like
            .split_explanations
            .push(format!("posterior_override={active_regime}:{dominant:.3}"));
    }

    let (catboost_weight, xgboost_weight) = historical_executor_weights(input);
    let aggregator = WeightedVotingAggregator;
    let decision = aggregator.aggregate(
        input,
        &posterior,
        &[catboost_like.clone(), xgboost_like.clone()],
        &[catboost_weight, xgboost_weight],
    );

    EnsembleVoteArtifact {
        ensemble_version: "ensemble-audit-v2-weighted".to_string(),
        posterior,
        final_action: decision.final_action,
        recommended_command: decision.recommended_command,
        human_next_triage: decision.human_next_triage,
        confidence: decision.confidence,
        consensus_strength: decision.consensus_strength,
        disagreement_flags: decision.disagreement_flags,
        executor_summaries: decision.executor_summaries,
        split_explanations: decision.split_explanations,
    }
}

pub fn build_stub_ensemble_vote_from_research(report: &ResearchReport) -> EnsembleVoteArtifact {
    let mut probabilities = BTreeMap::new();
    let active_phase = if report.workflow_state.phase.is_empty() {
        "research".to_string()
    } else {
        report.workflow_state.phase.clone()
    };
    let top_score = report
        .factor_score_deltas
        .iter()
        .map(|item| item.new_score)
        .fold(0.0_f64, f64::max)
        .clamp(0.0, 1.0);
    let lead = if top_score > 0.0 { top_score } else { 0.5 };
    probabilities.insert(active_phase.clone(), lead);
    probabilities.insert("fallback".to_string(), (1.0 - lead).clamp(0.0, 1.0));
    build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
        symbol: report.symbol_or_default(),
        state_dir: None,
        recommended_next_command: report.recommended_next_command.clone(),
        provenance: report.provenance.clone(),
        dataset_comparability: report.dataset_comparability.clone(),
        belief: BeliefReportPacket {
            regime_posterior: crate::domain::regime::RegimePosterior {
                active_regime: Some(active_phase),
                market_family: None,
                market_behavior_profile: None,
                jump_model: Some(crate::domain::regime::JumpModelRegimeSummary {
                    active_state: "jump_transition".to_string(),
                    confidence: 0.5,
                    transition_risk: 0.5,
                    state_probabilities: BTreeMap::from([
                        ("trend_persistent".to_string(), 0.25),
                        ("balance_mean_revert".to_string(), 0.25),
                        ("jump_transition".to_string(), 0.5),
                    ]),
                    evidence: report.multi_timeframe_summary.clone(),
                }),
                probabilities,
                confidence: Some(0.5),
                credible_intervals: BTreeMap::new(),
                evidence: report.multi_timeframe_summary.clone(),
            },
            regime_companion: crate::domain::belief::RegimeCompanionPacket {
                jump_model: Some(crate::domain::regime::JumpModelRegimeSummary {
                    active_state: "jump_transition".to_string(),
                    confidence: 0.5,
                    transition_risk: 0.5,
                    state_probabilities: BTreeMap::from([
                        ("trend_persistent".to_string(), 0.25),
                        ("balance_mean_revert".to_string(), 0.25),
                        ("jump_transition".to_string(), 0.5),
                    ]),
                    evidence: report.multi_timeframe_summary.clone(),
                }),
                disagreement: Some(crate::application::belief::build_regime_disagreement_summary(
                    Some("transition"),
                    Some(&crate::domain::regime::JumpModelRegimeSummary {
                        active_state: "jump_transition".to_string(),
                        confidence: 0.5,
                        transition_risk: 0.5,
                        state_probabilities: BTreeMap::from([
                            ("trend_persistent".to_string(), 0.25),
                            ("balance_mean_revert".to_string(), 0.25),
                            ("jump_transition".to_string(), 0.5),
                        ]),
                        evidence: report.multi_timeframe_summary.clone(),
                    }),
                )),
            },
            ..BeliefReportPacket::default()
        },
    })
}

trait ResearchReportSymbolExt {
    fn symbol_or_default(&self) -> String;
}

impl ResearchReportSymbolExt for ResearchReport {
    fn symbol_or_default(&self) -> String {
        self.workflow_snapshot.symbol.clone()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn posterior_audit_marks_normalized_probabilities() {
        let mut belief = BeliefReportPacket::default();
        belief.regime_posterior.active_regime = Some("trend".to_string());
        belief
            .regime_posterior
            .probabilities
            .insert("trend".to_string(), 0.7);
        belief
            .regime_posterior
            .probabilities
            .insert("range".to_string(), 0.3);
        let artifact = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
            symbol: "NQ".to_string(),
            state_dir: None,
            recommended_next_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                .to_string(),
            provenance: RunProvenance {
                data_fingerprint: "fp1".to_string(),
                ..RunProvenance::default()
            },
            dataset_comparability: DatasetComparability {
                comparable: true,
                comparison_class: "same_data_different_config".to_string(),
                ..DatasetComparability::default()
            },
            belief,
        });
        assert_eq!(artifact.posterior.normalization_status, "normalized");
        assert!(!artifact.final_action.is_empty());
        assert_eq!(artifact.ensemble_version, "ensemble-audit-v2-weighted");
        assert_eq!(artifact.executor_summaries.len(), 2);
    }

    #[test]
    fn weighted_voting_keeps_two_executor_summaries() {
        let mut belief = BeliefReportPacket::default();
        belief.regime_posterior.active_regime = Some("trend".to_string());
        belief
            .regime_posterior
            .probabilities
            .insert("trend".to_string(), 0.8);
        belief
            .regime_posterior
            .probabilities
            .insert("range".to_string(), 0.2);
        belief.regime_posterior.confidence = Some(0.8);
        belief.regime_companion.jump_model = Some(crate::domain::regime::JumpModelRegimeSummary {
            active_state: "jump_transition".to_string(),
            confidence: 0.8,
            transition_risk: 0.8,
            state_probabilities: BTreeMap::new(),
            evidence: vec![],
        });
        belief.regime_companion.disagreement = Some(
            crate::application::belief::build_regime_disagreement_summary(
                belief.regime_posterior.active_regime.as_deref(),
                belief.regime_companion.jump_model.as_ref(),
            ),
        );
        let artifact = build_stub_ensemble_vote_from_input(&AnalyzeEnsembleVoteInput {
            symbol: "NQ".to_string(),
            state_dir: None,
            recommended_next_command:
                "ict-engine update --symbol NQ --outcome <win|loss|breakeven> --entry-signal medium"
                    .to_string(),
            provenance: RunProvenance {
                data_fingerprint: "fp2".to_string(),
                ..RunProvenance::default()
            },
            dataset_comparability: DatasetComparability::default(),
            belief,
        });
        assert_eq!(artifact.executor_summaries.len(), 2);
    }

    #[test]
    fn historical_weights_fallback_to_defaults_without_entries() {
        let (cat, xgb) = historical_executor_weights_from_entries(&[]);
        assert!((cat - DEFAULT_CATBOOST_WEIGHT).abs() < 1e-9);
        assert!((xgb - DEFAULT_XGBOOST_WEIGHT).abs() < 1e-9);
    }

    #[test]
    fn canonical_scorecard_loader_falls_back_to_vote_history() {
        let temp = tempfile::tempdir().unwrap();
        let record = crate::state::EnsembleVoteRecord {
            artifact_id: "ensemble-vote:test".to_string(),
            generated_at: chrono::Utc::now(),
            symbol: "NQ".to_string(),
            source_phase: "analyze".to_string(),
            source_run_id: Some("run-1".to_string()),
            provenance: RunProvenance::default(),
            dataset_comparability: DatasetComparability::default(),
            ensemble_version: "ensemble-audit-v2-weighted".to_string(),
            final_action: "observe".to_string(),
            recommended_command: "ict-engine workflow-status --symbol NQ --phase human-next"
                .to_string(),
            human_next_triage: "ensemble_action=observe".to_string(),
            confidence: 0.5,
            consensus_strength: 0.5,
            disagreement_flags: Vec::new(),
            executor_summaries: vec![
                "executor=catboost_stub action=observe confidence=0.500".to_string()
            ],
            split_explanations: vec!["active_regime=research".to_string()],
            executor_scorecards: vec![EnsembleExecutorScorecard {
                executor: "catboost_stub".to_string(),
                latest_weight_hint: Some(0.55),
                ..EnsembleExecutorScorecard::default()
            }],
            executor_scorecards_source: Some("fallback".to_string()),
            posterior_fingerprint: "fp-test".to_string(),
            posterior_normalization_status: "normalized".to_string(),
            posterior_active_regime: "research".to_string(),
            posterior_confidence: Some(0.5),
            posterior_probabilities: BTreeMap::new(),
            posterior_evidence: vec!["mtf=test".to_string()],
        };
        crate::state::append_ensemble_vote_history(temp.path(), "NQ", record).unwrap();

        let scorecards = load_canonical_executor_scorecards(temp.path().to_str().unwrap(), "NQ");
        assert_eq!(scorecards[0].executor, "catboost_stub");
    }

    #[test]
    fn historical_weights_bias_toward_stronger_executor_presence() {
        let entries = vec![
            crate::state::ArtifactLedgerEntry {
                artifact_kind: "ensemble_vote".to_string(),
                review_reason: "catboost weight=0.55 xgboost weight=0.45".to_string(),
                quality_score: 90,
                ..crate::state::ArtifactLedgerEntry::default()
            },
            crate::state::ArtifactLedgerEntry {
                artifact_kind: "ensemble_vote".to_string(),
                review_reason: "catboost weight=0.55".to_string(),
                quality_score: 80,
                ..crate::state::ArtifactLedgerEntry::default()
            },
        ];
        let (cat, xgb) = historical_executor_weights_from_entries(&entries);
        assert!(cat > xgb);
        assert!((cat + xgb - 1.0).abs() < 1e-9);
    }

    #[test]
    fn historical_weights_reward_positive_and_penalize_negative_outcomes() {
        let entries = vec![
            crate::state::ArtifactLedgerEntry {
                artifact_kind: "ensemble_vote".to_string(),
                review_reason: "catboost".to_string(),
                quality_score: 60,
                consumed_outcome: Some("win".to_string()),
                consumption_regrade_status: Some("validated_positive".to_string()),
                ..crate::state::ArtifactLedgerEntry::default()
            },
            crate::state::ArtifactLedgerEntry {
                artifact_kind: "ensemble_vote".to_string(),
                review_reason: "xgboost".to_string(),
                quality_score: 60,
                consumed_outcome: Some("loss".to_string()),
                consumption_regrade_status: Some("validated_negative".to_string()),
                ..crate::state::ArtifactLedgerEntry::default()
            },
        ];
        let (cat, xgb) = historical_executor_weights_from_entries(&entries);
        assert!(cat > xgb);
    }
}
