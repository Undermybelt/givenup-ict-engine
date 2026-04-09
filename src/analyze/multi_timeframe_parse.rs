#[derive(Debug, Clone, Default)]
pub struct ParsedMultiTimeframeEvidence {
    pub direction_bias: String,
    pub alignment_score: Option<f64>,
    pub entry_alignment_score: Option<f64>,
}

pub fn multi_timeframe_direction_conflicts_with(label: &str, direction_bias: &str) -> bool {
    matches!(
        (label, direction_bias),
        ("bull", "bearish") | ("bear", "bullish") | ("bullish", "bearish") | ("bearish", "bullish")
    )
}

pub fn classify_multi_timeframe_resonance(
    policy: &crate::state::PreBayesEvidencePolicy,
    direction_conflict: bool,
    evidence: &ParsedMultiTimeframeEvidence,
) -> String {
    let alignment = evidence.alignment_score.unwrap_or(0.5);
    let entry_alignment = evidence.entry_alignment_score.unwrap_or(0.5);
    if direction_conflict
        || alignment < policy.min_multi_timeframe_alignment_score * 0.8
        || entry_alignment < policy.min_multi_timeframe_entry_alignment_score * 0.8
    {
        "dislocated".to_string()
    } else if evidence.direction_bias == "neutral"
        || alignment < policy.min_multi_timeframe_alignment_score
        || entry_alignment < policy.min_multi_timeframe_entry_alignment_score
    {
        "mixed".to_string()
    } else {
        "aligned".to_string()
    }
}

pub fn parse_multi_timeframe_evidence(
    multi_timeframe_summary: &[String],
) -> ParsedMultiTimeframeEvidence {
    let direction_bias = multi_timeframe_summary
        .iter()
        .find_map(|item| item.strip_prefix("higher_timeframe_direction_bias="))
        .unwrap_or("neutral")
        .to_string();
    let alignment_score = multi_timeframe_summary
        .iter()
        .find_map(|item| item.strip_prefix("higher_timeframe_alignment_score="))
        .and_then(|value| value.parse::<f64>().ok());
    let entry_alignment_score = multi_timeframe_summary
        .iter()
        .find_map(|item| item.strip_prefix("lower_timeframe_entry_alignment_score="))
        .and_then(|value| value.parse::<f64>().ok());
    ParsedMultiTimeframeEvidence {
        direction_bias,
        alignment_score,
        entry_alignment_score,
    }
}
