use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::Path;

use anyhow::Context;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StructureEventKind {
    Cisd,
    Mss,
    MarketStructureShift,
    FairValueGap,
    InversionFairValueGap,
    OrderBlock,
    LiquiditySweep,
    RejectionBlock,
    BalancedPriceRange,
    Other,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StructureDirection {
    Bull,
    Bear,
    Mixed,
    Neutral,
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StructureDirectionEvent {
    pub timeframe: String,
    pub kind: StructureEventKind,
    pub direction: StructureDirection,
    #[serde(default)]
    pub state: Option<String>,
    #[serde(default)]
    pub strength: Option<f64>,
    #[serde(default)]
    pub source: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct StructureDirectionEventBundle {
    pub symbol: String,
    #[serde(default)]
    pub source_profile: Option<String>,
    #[serde(default = "default_require_multi_timeframe")]
    pub require_multi_timeframe: bool,
    #[serde(default)]
    pub events: Vec<StructureDirectionEvent>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct StructureDirectionConfirmation {
    pub confirmed: bool,
    pub direction: StructureDirection,
    pub source: String,
    pub confirming_timeframes: Vec<String>,
    pub confirming_event_count: usize,
    pub context_event_count: usize,
    pub rationale: Vec<String>,
}

fn default_require_multi_timeframe() -> bool {
    true
}

impl StructureEventKind {
    fn is_direction_confirmation(&self) -> bool {
        matches!(self, Self::Cisd | Self::Mss | Self::MarketStructureShift)
    }

    fn as_compact_str(&self) -> &'static str {
        match self {
            Self::Cisd => "cisd",
            Self::Mss => "mss",
            Self::MarketStructureShift => "market_structure_shift",
            Self::FairValueGap => "fvg",
            Self::InversionFairValueGap => "ifvg",
            Self::OrderBlock => "order_block",
            Self::LiquiditySweep => "liquidity_sweep",
            Self::RejectionBlock => "rejection_block",
            Self::BalancedPriceRange => "bpr",
            Self::Other => "other",
        }
    }
}

impl StructureDirection {
    fn is_trade_direction(&self) -> bool {
        matches!(self, Self::Bull | Self::Bear)
    }

    fn as_compact_str(&self) -> &'static str {
        match self {
            Self::Bull => "bull",
            Self::Bear => "bear",
            Self::Mixed => "mixed",
            Self::Neutral => "neutral",
            Self::Unknown => "unknown",
        }
    }
}

pub fn load_structure_direction_event_bundle(
    path: impl AsRef<Path>,
) -> anyhow::Result<StructureDirectionEventBundle> {
    let path = path.as_ref();
    let raw = fs::read_to_string(path)
        .with_context(|| format!("failed to read structure events from {}", path.display()))?;
    serde_json::from_str(&raw).with_context(|| {
        format!(
            "failed to parse structure events JSON from {}",
            path.display()
        )
    })
}

pub fn evaluate_structure_direction_confirmation(
    bundle: &StructureDirectionEventBundle,
) -> StructureDirectionConfirmation {
    let mut directional: BTreeMap<&'static str, Vec<&StructureDirectionEvent>> = BTreeMap::new();
    let mut context_event_count = 0usize;
    for event in &bundle.events {
        if event.kind.is_direction_confirmation() && event.direction.is_trade_direction() {
            directional
                .entry(event.direction.as_compact_str())
                .or_default()
                .push(event);
        } else {
            context_event_count += 1;
        }
    }

    let mut ranked: Vec<(&'static str, Vec<&StructureDirectionEvent>)> =
        directional.into_iter().collect();
    ranked.sort_by(|left, right| {
        right
            .1
            .len()
            .cmp(&left.1.len())
            .then_with(|| left.0.cmp(right.0))
    });

    let Some((direction, events)) = ranked.first() else {
        return StructureDirectionConfirmation {
            confirmed: false,
            direction: StructureDirection::Unknown,
            source: "structure_events_hotplug".to_string(),
            confirming_timeframes: Vec::new(),
            confirming_event_count: 0,
            context_event_count,
            rationale: vec!["missing_cisd_mss_direction_confirmation".to_string()],
        };
    };

    let tied = ranked
        .get(1)
        .is_some_and(|(_, other_events)| other_events.len() == events.len());
    let timeframes: BTreeSet<String> = events
        .iter()
        .map(|event| event.timeframe.trim().to_ascii_lowercase())
        .filter(|value| !value.is_empty())
        .collect();
    let has_mtf = timeframes.len() >= 2;
    let confirmed = !tied && (!bundle.require_multi_timeframe || has_mtf);
    let mut rationale = Vec::new();
    if tied {
        rationale.push("mixed_cisd_mss_direction_votes".to_string());
    }
    if bundle.require_multi_timeframe && !has_mtf {
        rationale.push("missing_multi_timeframe_resonance".to_string());
    }
    if confirmed {
        rationale.push(format!("confirmed_by_cisd_mss_{direction}"));
    }

    StructureDirectionConfirmation {
        confirmed,
        direction: match *direction {
            "bull" => StructureDirection::Bull,
            "bear" => StructureDirection::Bear,
            _ => StructureDirection::Unknown,
        },
        source: "structure_events_hotplug".to_string(),
        confirming_timeframes: timeframes.into_iter().collect(),
        confirming_event_count: events.len(),
        context_event_count,
        rationale,
    }
}

pub fn structure_direction_summary_lines(
    confirmation: &StructureDirectionConfirmation,
) -> Vec<String> {
    vec![
        "structure_direction_source=structure_events_hotplug".to_string(),
        format!("structure_direction_confirmed={}", confirmation.confirmed),
        format!(
            "structure_direction={}",
            confirmation.direction.as_compact_str()
        ),
        "structure_direction_confirmation_source=cisd_mss".to_string(),
        format!(
            "structure_direction_confirming_timeframes={}",
            confirmation.confirming_timeframes.join(",")
        ),
        format!(
            "structure_direction_confirming_event_count={}",
            confirmation.confirming_event_count
        ),
        format!(
            "structure_context_event_count={}",
            confirmation.context_event_count
        ),
        format!(
            "structure_direction_rationale={}",
            confirmation.rationale.join("|")
        ),
    ]
}

pub fn structure_event_bundle_summary_line(bundle: &StructureDirectionEventBundle) -> String {
    let kinds = bundle
        .events
        .iter()
        .map(|event| event.kind.as_compact_str())
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>()
        .join(",");
    format!(
        "structure_events_hotplug=symbol:{} events:{} kinds:{} require_mtf:{}",
        bundle.symbol,
        bundle.events.len(),
        kinds,
        bundle.require_multi_timeframe
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    fn event(
        timeframe: &str,
        kind: StructureEventKind,
        direction: StructureDirection,
    ) -> StructureDirectionEvent {
        StructureDirectionEvent {
            timeframe: timeframe.to_string(),
            kind,
            direction,
            state: None,
            strength: None,
            source: None,
        }
    }

    #[test]
    fn no_events_fail_closed_without_personal_data_dependency() {
        let bundle = StructureDirectionEventBundle {
            symbol: "DEMO".to_string(),
            source_profile: None,
            require_multi_timeframe: true,
            events: Vec::new(),
        };
        let confirmation = evaluate_structure_direction_confirmation(&bundle);
        assert!(!confirmation.confirmed);
        assert_eq!(confirmation.direction, StructureDirection::Unknown);
        assert_eq!(
            confirmation.rationale,
            vec!["missing_cisd_mss_direction_confirmation".to_string()]
        );
    }

    #[test]
    fn cisd_and_mss_same_direction_across_timeframes_confirms_direction() {
        let bundle = StructureDirectionEventBundle {
            symbol: "NQ".to_string(),
            source_profile: Some("local_ict_scripts".to_string()),
            require_multi_timeframe: true,
            events: vec![
                event("5m", StructureEventKind::Cisd, StructureDirection::Bull),
                event("15m", StructureEventKind::Mss, StructureDirection::Bull),
                event(
                    "15m",
                    StructureEventKind::FairValueGap,
                    StructureDirection::Bull,
                ),
                event(
                    "15m",
                    StructureEventKind::OrderBlock,
                    StructureDirection::Bull,
                ),
            ],
        };
        let confirmation = evaluate_structure_direction_confirmation(&bundle);
        assert!(confirmation.confirmed);
        assert_eq!(confirmation.direction, StructureDirection::Bull);
        assert_eq!(confirmation.confirming_event_count, 2);
        assert_eq!(confirmation.context_event_count, 2);
        assert_eq!(
            structure_direction_summary_lines(&confirmation)[1],
            "structure_direction_confirmed=true"
        );
    }

    #[test]
    fn ob_fvg_liquidity_only_remains_context_not_confirmation() {
        let bundle = StructureDirectionEventBundle {
            symbol: "NQ".to_string(),
            source_profile: Some("local_ict_scripts".to_string()),
            require_multi_timeframe: true,
            events: vec![
                event(
                    "5m",
                    StructureEventKind::LiquiditySweep,
                    StructureDirection::Bull,
                ),
                event(
                    "5m",
                    StructureEventKind::OrderBlock,
                    StructureDirection::Bull,
                ),
                event(
                    "15m",
                    StructureEventKind::FairValueGap,
                    StructureDirection::Bull,
                ),
            ],
        };
        let confirmation = evaluate_structure_direction_confirmation(&bundle);
        assert!(!confirmation.confirmed);
        assert_eq!(confirmation.confirming_event_count, 0);
        assert_eq!(confirmation.context_event_count, 3);
    }

    #[test]
    fn single_timeframe_cisd_waits_when_mtf_required() {
        let bundle = StructureDirectionEventBundle {
            symbol: "NQ".to_string(),
            source_profile: Some("local_ict_scripts".to_string()),
            require_multi_timeframe: true,
            events: vec![event(
                "5m",
                StructureEventKind::Cisd,
                StructureDirection::Bull,
            )],
        };
        let confirmation = evaluate_structure_direction_confirmation(&bundle);
        assert!(!confirmation.confirmed);
        assert_eq!(
            confirmation.rationale,
            vec!["missing_multi_timeframe_resonance".to_string()]
        );
    }
}
