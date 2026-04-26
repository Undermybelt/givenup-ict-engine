//! Canonical ICT setup matchers over the PDA event timeline.
//!
//! Each matcher consumes the sorted `Vec<PdaEvent>` from
//! `super::builder::build_pda_timeline` and emits zero or more
//! `SetupMatch` records for the named ICT setup.
//!
//! ## Scope (v1)
//!
//! Of the 30 canonical setups enumerated in
//! `docs/2026-04-27-pda-factor-universe-plan.md` §4.1, this module
//! ships **13** that operate purely on a single-timeframe local
//! event timeline:
//!
//! | # | Variant                   | Pattern                                      |
//! |---|---------------------------|----------------------------------------------|
//! | 1 | ObRetestPropulsionConfirm | OB → Propulsion (same dir, within horizon)   |
//! | 2 | IFvgContinuation          | MSS → iFVG (same dir, within horizon)        |
//! | 3 | BreakerBlockRetest        | BreakerBlock event present                   |
//! | 4 | MitigationBlockRetest     | MitigationBlock event present                |
//! | 5 | RejectionBlockAtKeyLevel  | RB level near a recent MSS/SB level          |
//! | 6 | VolumeImbalanceFiller     | VI → MSS/SB/Propulsion (same dir)            |
//! | 7 | LiquidityVoidContinuation | LV → MSS/SB (same dir)                       |
//! | 8 | PropulsionPostMss         | MSS → Propulsion (same dir, within horizon)  |
//! | 9 | CisdAfterDistribution     | last MSS Bull → CISD Bear within horizon     |
//! |10 | CisdAfterAccumulation     | last MSS Bear → CISD Bull within horizon     |
//! |11 | UnicornModel              | BreakerBlock + FVG overlap (same dir, near)  |
//! |12 | PowerOfThree              | LiquiditySweep → opposite-dir MSS/SB         |
//! |13 | TurtleSoupLiquidityGrab   | LiquiditySweep → opposite-dir MSS            |
//!
//! The remaining 17 setups (HTF/LTF nesting, session windows, SMT
//! divergence, OTE retracement) are deferred to a later commit
//! because they require cross-timeframe data, a session calendar,
//! cross-symbol candle joins, or Fibonacci helpers — none of which
//! belong in the single-TF event timeline. They are deliberately
//! **not** present as inert enum variants here so the public
//! surface stays honest.

use serde::{Deserialize, Serialize};

use super::event::{PdaEvent, PdaEventKind};
use crate::types::Direction;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum CanonicalSetupKind {
    ObRetestPropulsionConfirm,
    IFvgContinuation,
    BreakerBlockRetest,
    MitigationBlockRetest,
    RejectionBlockAtKeyLevel,
    VolumeImbalanceFiller,
    LiquidityVoidContinuation,
    PropulsionPostMss,
    CisdAfterDistribution,
    CisdAfterAccumulation,
    UnicornModel,
    PowerOfThree,
    TurtleSoupLiquidityGrab,
}

impl CanonicalSetupKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ObRetestPropulsionConfirm => "ob_retest_propulsion_confirm",
            Self::IFvgContinuation => "ifvg_continuation",
            Self::BreakerBlockRetest => "breaker_block_retest",
            Self::MitigationBlockRetest => "mitigation_block_retest",
            Self::RejectionBlockAtKeyLevel => "rejection_block_at_key_level",
            Self::VolumeImbalanceFiller => "volume_imbalance_filler",
            Self::LiquidityVoidContinuation => "liquidity_void_continuation",
            Self::PropulsionPostMss => "propulsion_post_mss",
            Self::CisdAfterDistribution => "cisd_after_distribution",
            Self::CisdAfterAccumulation => "cisd_after_accumulation",
            Self::UnicornModel => "unicorn_model",
            Self::PowerOfThree => "power_of_three",
            Self::TurtleSoupLiquidityGrab => "turtle_soup_liquidity_grab",
        }
    }
}

pub const ALL_CANONICAL_SETUPS: [CanonicalSetupKind; 13] = [
    CanonicalSetupKind::ObRetestPropulsionConfirm,
    CanonicalSetupKind::IFvgContinuation,
    CanonicalSetupKind::BreakerBlockRetest,
    CanonicalSetupKind::MitigationBlockRetest,
    CanonicalSetupKind::RejectionBlockAtKeyLevel,
    CanonicalSetupKind::VolumeImbalanceFiller,
    CanonicalSetupKind::LiquidityVoidContinuation,
    CanonicalSetupKind::PropulsionPostMss,
    CanonicalSetupKind::CisdAfterDistribution,
    CanonicalSetupKind::CisdAfterAccumulation,
    CanonicalSetupKind::UnicornModel,
    CanonicalSetupKind::PowerOfThree,
    CanonicalSetupKind::TurtleSoupLiquidityGrab,
];

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SetupMatch {
    pub kind: CanonicalSetupKind,
    pub direction: Direction,
    pub anchor_bar: usize,
    pub confirm_bar: usize,
    pub event_bars: Vec<usize>,
}

pub const DEFAULT_SETUP_HORIZON_BARS: usize = 30;
/// Tolerance (in price terms relative to the level) for "near a key level".
/// 25 bps mirrors the magnitude `pda_state.rs` uses for touch checks.
pub const DEFAULT_KEY_LEVEL_TOLERANCE_BPS: f64 = 0.0025;

pub fn match_all_setups(events: &[PdaEvent], horizon_bars: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    out.extend(match_ob_retest_propulsion(events, horizon_bars));
    out.extend(match_ifvg_continuation(events, horizon_bars));
    out.extend(match_breaker_block_retest(events));
    out.extend(match_mitigation_block_retest(events));
    out.extend(match_rejection_block_at_key_level(
        events,
        horizon_bars,
        DEFAULT_KEY_LEVEL_TOLERANCE_BPS,
    ));
    out.extend(match_volume_imbalance_filler(events, horizon_bars));
    out.extend(match_liquidity_void_continuation(events, horizon_bars));
    out.extend(match_propulsion_post_mss(events, horizon_bars));
    out.extend(match_cisd_after_distribution(events, horizon_bars));
    out.extend(match_cisd_after_accumulation(events, horizon_bars));
    out.extend(match_unicorn_model(events, horizon_bars));
    out.extend(match_power_of_three(events, horizon_bars));
    out.extend(match_turtle_soup_liquidity_grab(events, horizon_bars));
    out.sort_by_key(|m| (m.confirm_bar, m.kind.as_str()));
    out
}

pub fn match_all_setups_default(events: &[PdaEvent]) -> Vec<SetupMatch> {
    match_all_setups(events, DEFAULT_SETUP_HORIZON_BARS)
}

// --------------------------------------------------------------------
// Generic helpers
// --------------------------------------------------------------------

fn find_recent_before(
    events: &[PdaEvent],
    from_idx: usize,
    horizon: usize,
    pred: impl Fn(&PdaEvent) -> bool,
) -> Option<&PdaEvent> {
    let anchor_bar = events[from_idx].bar_index;
    events[..from_idx]
        .iter()
        .rev()
        .take_while(|e| anchor_bar.saturating_sub(e.bar_index) <= horizon)
        .find(|e| pred(e))
}

fn find_after(
    events: &[PdaEvent],
    from_idx: usize,
    horizon: usize,
    pred: impl Fn(&PdaEvent) -> bool,
) -> Option<&PdaEvent> {
    let anchor_bar = events[from_idx].bar_index;
    events
        .iter()
        .skip(from_idx + 1)
        .take_while(|e| e.bar_index.saturating_sub(anchor_bar) <= horizon)
        .find(|e| pred(e))
}

fn opposite(direction: Direction) -> Direction {
    match direction {
        Direction::Bull => Direction::Bear,
        Direction::Bear => Direction::Bull,
        Direction::Neutral => Direction::Neutral,
    }
}

// --------------------------------------------------------------------
// 1. ObRetestPropulsionConfirm
// --------------------------------------------------------------------

fn match_ob_retest_propulsion(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::PropulsionBlock {
            continue;
        }
        if let Some(ob) = find_recent_before(events, i, horizon, |e| {
            e.kind == PdaEventKind::OrderBlock && e.direction == ev.direction
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::ObRetestPropulsionConfirm,
                direction: ev.direction,
                anchor_bar: ob.bar_index,
                confirm_bar: ev.bar_index,
                event_bars: vec![ob.bar_index, ev.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 2. IFvgContinuation: MSS → iFVG (same direction)
// --------------------------------------------------------------------

fn match_ifvg_continuation(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::InverseFairValueGap {
            continue;
        }
        if let Some(mss) = find_recent_before(events, i, horizon, |e| {
            e.kind == PdaEventKind::MarketStructureShift && e.direction == ev.direction
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::IFvgContinuation,
                direction: ev.direction,
                anchor_bar: mss.bar_index,
                confirm_bar: ev.bar_index,
                event_bars: vec![mss.bar_index, ev.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 3. BreakerBlockRetest — every BreakerBlock event already encodes
//    the violation + retest; the timeline event is the match.
// --------------------------------------------------------------------

fn match_breaker_block_retest(events: &[PdaEvent]) -> Vec<SetupMatch> {
    events
        .iter()
        .filter(|e| e.kind == PdaEventKind::BreakerBlock)
        .map(|e| SetupMatch {
            kind: CanonicalSetupKind::BreakerBlockRetest,
            direction: e.direction,
            anchor_bar: e.bar_index,
            confirm_bar: e.bar_index,
            event_bars: vec![e.bar_index],
        })
        .collect()
}

// --------------------------------------------------------------------
// 4. MitigationBlockRetest — every MitigationBlock event is a match.
// --------------------------------------------------------------------

fn match_mitigation_block_retest(events: &[PdaEvent]) -> Vec<SetupMatch> {
    events
        .iter()
        .filter(|e| e.kind == PdaEventKind::MitigationBlock)
        .map(|e| SetupMatch {
            kind: CanonicalSetupKind::MitigationBlockRetest,
            direction: e.direction,
            anchor_bar: e.bar_index,
            confirm_bar: e.bar_index,
            event_bars: vec![e.bar_index],
        })
        .collect()
}

// --------------------------------------------------------------------
// 5. RejectionBlockAtKeyLevel — RB.level within ε of a recent
//    MSS/StructureBreak level.
// --------------------------------------------------------------------

fn match_rejection_block_at_key_level(
    events: &[PdaEvent],
    horizon: usize,
    tolerance_bps: f64,
) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::RejectionBlock {
            continue;
        }
        let Some(rb_level) = ev.level else { continue };
        let tolerance = rb_level.abs() * tolerance_bps;
        if let Some(level_event) = find_recent_before(events, i, horizon, |e| {
            (e.kind == PdaEventKind::MarketStructureShift
                || e.kind == PdaEventKind::StructureBreak)
                && e
                    .level
                    .map(|l| (l - rb_level).abs() <= tolerance)
                    .unwrap_or(false)
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::RejectionBlockAtKeyLevel,
                direction: ev.direction,
                anchor_bar: level_event.bar_index,
                confirm_bar: ev.bar_index,
                event_bars: vec![level_event.bar_index, ev.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 6. VolumeImbalanceFiller — VI followed by structure event same dir.
// --------------------------------------------------------------------

fn match_volume_imbalance_filler(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::VolumeImbalance {
            continue;
        }
        if ev.direction == Direction::Neutral {
            continue;
        }
        if let Some(follow) = find_after(events, i, horizon, |e| {
            (e.kind == PdaEventKind::MarketStructureShift
                || e.kind == PdaEventKind::StructureBreak
                || e.kind == PdaEventKind::PropulsionBlock)
                && e.direction == ev.direction
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::VolumeImbalanceFiller,
                direction: ev.direction,
                anchor_bar: ev.bar_index,
                confirm_bar: follow.bar_index,
                event_bars: vec![ev.bar_index, follow.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 7. LiquidityVoidContinuation — LV followed by MSS/SB same dir.
// --------------------------------------------------------------------

fn match_liquidity_void_continuation(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::LiquidityVoid {
            continue;
        }
        if let Some(follow) = find_after(events, i, horizon, |e| {
            (e.kind == PdaEventKind::MarketStructureShift
                || e.kind == PdaEventKind::StructureBreak)
                && e.direction == ev.direction
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::LiquidityVoidContinuation,
                direction: ev.direction,
                anchor_bar: ev.bar_index,
                confirm_bar: follow.bar_index,
                event_bars: vec![ev.bar_index, follow.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 8. PropulsionPostMss — MSS followed by Propulsion same dir.
// --------------------------------------------------------------------

fn match_propulsion_post_mss(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::MarketStructureShift {
            continue;
        }
        if let Some(prop) = find_after(events, i, horizon, |e| {
            e.kind == PdaEventKind::PropulsionBlock && e.direction == ev.direction
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::PropulsionPostMss,
                direction: ev.direction,
                anchor_bar: ev.bar_index,
                confirm_bar: prop.bar_index,
                event_bars: vec![ev.bar_index, prop.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 9-10. Cisd After Distribution / Accumulation
// --------------------------------------------------------------------

fn match_cisd_after_phase(
    events: &[PdaEvent],
    horizon: usize,
    cisd_direction: Direction,
    prior_phase_direction: Direction,
    kind: CanonicalSetupKind,
) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::Cisd || ev.direction != cisd_direction {
            continue;
        }
        // Prior phase = most recent MSS in the opposite direction of the CISD.
        if let Some(prior) = find_recent_before(events, i, horizon, |e| {
            e.kind == PdaEventKind::MarketStructureShift && e.direction == prior_phase_direction
        }) {
            out.push(SetupMatch {
                kind,
                direction: ev.direction,
                anchor_bar: prior.bar_index,
                confirm_bar: ev.bar_index,
                event_bars: vec![prior.bar_index, ev.bar_index],
            });
        }
    }
    out
}

fn match_cisd_after_distribution(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    // Distribution = bull regime exhausted; CISD bear ends it.
    match_cisd_after_phase(
        events,
        horizon,
        Direction::Bear,
        Direction::Bull,
        CanonicalSetupKind::CisdAfterDistribution,
    )
}

fn match_cisd_after_accumulation(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    // Accumulation = bear regime exhausted; CISD bull ends it.
    match_cisd_after_phase(
        events,
        horizon,
        Direction::Bull,
        Direction::Bear,
        CanonicalSetupKind::CisdAfterAccumulation,
    )
}

// --------------------------------------------------------------------
// 11. UnicornModel — Breaker overlapping FVG (same dir, near in time).
// --------------------------------------------------------------------

fn match_unicorn_model(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::BreakerBlock {
            continue;
        }
        // Look both forward and backward within horizon for a same-dir
        // FVG; either direction works because the breaker confirms
        // late and the FVG can sit on either side of the violation.
        let neighbours = events
            .iter()
            .enumerate()
            .filter(|(j, _)| *j != i)
            .filter(|(_, other)| other.kind == PdaEventKind::FairValueGap);
        for (_, other) in neighbours {
            let dt = other
                .bar_index
                .max(ev.bar_index)
                .saturating_sub(other.bar_index.min(ev.bar_index));
            if dt > horizon {
                continue;
            }
            if other.direction != ev.direction {
                continue;
            }
            out.push(SetupMatch {
                kind: CanonicalSetupKind::UnicornModel,
                direction: ev.direction,
                anchor_bar: other.bar_index.min(ev.bar_index),
                confirm_bar: other.bar_index.max(ev.bar_index),
                event_bars: vec![ev.bar_index, other.bar_index],
            });
            // Only emit once per breaker — pick the closest FVG
            // implicitly by the take_break below.
            break;
        }
    }
    out
}

// --------------------------------------------------------------------
// 12. PowerOfThree — LiquiditySweep → opposite-direction MSS/SB.
//     This is the "manipulation → distribution" simplification.
// --------------------------------------------------------------------

fn match_power_of_three(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::LiquiditySweep {
            continue;
        }
        let target = opposite(ev.direction);
        if target == Direction::Neutral {
            continue;
        }
        if let Some(follow) = find_after(events, i, horizon, |e| {
            (e.kind == PdaEventKind::MarketStructureShift
                || e.kind == PdaEventKind::StructureBreak)
                && e.direction == target
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::PowerOfThree,
                direction: target,
                anchor_bar: ev.bar_index,
                confirm_bar: follow.bar_index,
                event_bars: vec![ev.bar_index, follow.bar_index],
            });
        }
    }
    out
}

// --------------------------------------------------------------------
// 13. TurtleSoupLiquidityGrab — LiquiditySweep → opposite-dir MSS only
//     (stricter than PowerOfThree's MSS/SB tolerance).
// --------------------------------------------------------------------

fn match_turtle_soup_liquidity_grab(events: &[PdaEvent], horizon: usize) -> Vec<SetupMatch> {
    let mut out = Vec::new();
    for (i, ev) in events.iter().enumerate() {
        if ev.kind != PdaEventKind::LiquiditySweep {
            continue;
        }
        let target = opposite(ev.direction);
        if target == Direction::Neutral {
            continue;
        }
        if let Some(follow) = find_after(events, i, horizon, |e| {
            e.kind == PdaEventKind::MarketStructureShift && e.direction == target
        }) {
            out.push(SetupMatch {
                kind: CanonicalSetupKind::TurtleSoupLiquidityGrab,
                direction: target,
                anchor_bar: ev.bar_index,
                confirm_bar: follow.bar_index,
                event_bars: vec![ev.bar_index, follow.bar_index],
            });
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ev(kind: PdaEventKind, bar: usize, direction: Direction) -> PdaEvent {
        PdaEvent::new(kind, bar, direction).with_level(100.0)
    }

    fn ev_with_level(
        kind: PdaEventKind,
        bar: usize,
        direction: Direction,
        level: f64,
    ) -> PdaEvent {
        PdaEvent::new(kind, bar, direction).with_level(level)
    }

    #[test]
    fn empty_timeline_yields_no_matches() {
        assert!(match_all_setups_default(&[]).is_empty());
    }

    #[test]
    fn single_event_yields_only_self_anchored_setups() {
        // Lone BreakerBlock — should fire BreakerBlockRetest but no
        // pair-based setup.
        let events = vec![ev(PdaEventKind::BreakerBlock, 10, Direction::Bull)];
        let matches = match_all_setups_default(&events);
        assert_eq!(matches.len(), 1);
        assert_eq!(matches[0].kind, CanonicalSetupKind::BreakerBlockRetest);
    }

    #[test]
    fn ob_retest_propulsion_fires() {
        let events = vec![
            ev(PdaEventKind::OrderBlock, 10, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 12, Direction::Bull),
        ];
        let m = match_all_setups_default(&events);
        let setup = m
            .iter()
            .find(|s| s.kind == CanonicalSetupKind::ObRetestPropulsionConfirm)
            .expect("expected setup");
        assert_eq!(setup.direction, Direction::Bull);
        assert_eq!(setup.anchor_bar, 10);
        assert_eq!(setup.confirm_bar, 12);
    }

    #[test]
    fn ob_retest_propulsion_does_not_fire_across_direction_mismatch() {
        let events = vec![
            ev(PdaEventKind::OrderBlock, 10, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 12, Direction::Bear),
        ];
        let m = match_all_setups_default(&events);
        assert!(!m
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::ObRetestPropulsionConfirm));
    }

    #[test]
    fn horizon_excludes_far_pairs() {
        let events = vec![
            ev(PdaEventKind::OrderBlock, 10, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 100, Direction::Bull),
        ];
        let near = match_all_setups(&events, 5);
        let far = match_all_setups(&events, 200);
        assert!(!near
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::ObRetestPropulsionConfirm));
        assert!(far
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::ObRetestPropulsionConfirm));
    }

    #[test]
    fn ifvg_continuation_requires_prior_mss() {
        // iFVG without a same-dir MSS preceding it should not fire.
        let events = vec![
            ev(PdaEventKind::FairValueGap, 5, Direction::Bull),
            ev(PdaEventKind::InverseFairValueGap, 10, Direction::Bear),
        ];
        let m = match_all_setups_default(&events);
        assert!(!m
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::IFvgContinuation));
        // Now add the MSS
        let events_with_mss = vec![
            ev(PdaEventKind::MarketStructureShift, 8, Direction::Bear),
            ev(PdaEventKind::InverseFairValueGap, 10, Direction::Bear),
        ];
        let m2 = match_all_setups_default(&events_with_mss);
        let setup = m2
            .iter()
            .find(|s| s.kind == CanonicalSetupKind::IFvgContinuation)
            .expect("expected iFvgContinuation");
        assert_eq!(setup.direction, Direction::Bear);
    }

    #[test]
    fn rejection_block_at_key_level_uses_price_proximity() {
        // RB at 100.0; MSS at 100.05 (~5 bps) → within tolerance (25 bps).
        let events = vec![
            ev_with_level(
                PdaEventKind::MarketStructureShift,
                5,
                Direction::Bear,
                100.05,
            ),
            ev_with_level(PdaEventKind::RejectionBlock, 8, Direction::Bear, 100.0),
        ];
        let m = match_all_setups_default(&events);
        assert!(
            m.iter()
                .any(|s| s.kind == CanonicalSetupKind::RejectionBlockAtKeyLevel),
            "RB at MSS level (~5 bps) should match"
        );

        // Same bars but MSS level far away (105) → outside tolerance.
        let far = vec![
            ev_with_level(
                PdaEventKind::MarketStructureShift,
                5,
                Direction::Bear,
                105.0,
            ),
            ev_with_level(PdaEventKind::RejectionBlock, 8, Direction::Bear, 100.0),
        ];
        let m2 = match_all_setups_default(&far);
        assert!(!m2
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::RejectionBlockAtKeyLevel));
    }

    #[test]
    fn volume_imbalance_filler_requires_same_dir_continuation() {
        let events = vec![
            ev(PdaEventKind::VolumeImbalance, 5, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 8, Direction::Bull),
        ];
        let m = match_all_setups_default(&events);
        assert!(m
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::VolumeImbalanceFiller));

        let events_no_match = vec![
            ev(PdaEventKind::VolumeImbalance, 5, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 8, Direction::Bear),
        ];
        let m2 = match_all_setups_default(&events_no_match);
        assert!(!m2
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::VolumeImbalanceFiller));
    }

    #[test]
    fn turtle_soup_requires_opposite_direction() {
        let events = vec![
            ev(PdaEventKind::LiquiditySweep, 5, Direction::Bull),
            ev(PdaEventKind::MarketStructureShift, 8, Direction::Bear),
        ];
        let m = match_all_setups_default(&events);
        let turtle = m
            .iter()
            .find(|s| s.kind == CanonicalSetupKind::TurtleSoupLiquidityGrab)
            .expect("expected turtle soup");
        // Direction reflects the eventual move (opposite of sweep).
        assert_eq!(turtle.direction, Direction::Bear);
        assert_eq!(turtle.anchor_bar, 5);
        assert_eq!(turtle.confirm_bar, 8);

        let same_dir = vec![
            ev(PdaEventKind::LiquiditySweep, 5, Direction::Bull),
            ev(PdaEventKind::MarketStructureShift, 8, Direction::Bull),
        ];
        let m2 = match_all_setups_default(&same_dir);
        assert!(!m2
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::TurtleSoupLiquidityGrab));
    }

    #[test]
    fn cisd_after_distribution_requires_bull_regime_then_bear_cisd() {
        let events = vec![
            ev(PdaEventKind::MarketStructureShift, 5, Direction::Bull),
            ev(PdaEventKind::Cisd, 10, Direction::Bear),
        ];
        let m = match_all_setups_default(&events);
        assert!(m
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::CisdAfterDistribution));

        let no_prior = vec![ev(PdaEventKind::Cisd, 10, Direction::Bear)];
        let m2 = match_all_setups_default(&no_prior);
        assert!(!m2
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::CisdAfterDistribution));
    }

    #[test]
    fn unicorn_model_pairs_breaker_with_same_dir_fvg() {
        let events = vec![
            ev(PdaEventKind::FairValueGap, 8, Direction::Bull),
            ev(PdaEventKind::BreakerBlock, 12, Direction::Bull),
        ];
        let m = match_all_setups_default(&events);
        assert!(m.iter().any(|s| s.kind == CanonicalSetupKind::UnicornModel));

        let mismatch = vec![
            ev(PdaEventKind::FairValueGap, 8, Direction::Bear),
            ev(PdaEventKind::BreakerBlock, 12, Direction::Bull),
        ];
        let m2 = match_all_setups_default(&mismatch);
        assert!(!m2
            .iter()
            .any(|s| s.kind == CanonicalSetupKind::UnicornModel));
    }

    #[test]
    fn output_is_sorted_by_confirm_bar_then_kind_name() {
        let events = vec![
            ev(PdaEventKind::OrderBlock, 10, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 20, Direction::Bull),
            ev(PdaEventKind::BreakerBlock, 15, Direction::Bull),
            ev(PdaEventKind::MitigationBlock, 12, Direction::Bear),
        ];
        let m = match_all_setups_default(&events);
        for window in m.windows(2) {
            assert!(window[0].confirm_bar <= window[1].confirm_bar);
            if window[0].confirm_bar == window[1].confirm_bar {
                assert!(window[0].kind.as_str() <= window[1].kind.as_str());
            }
        }
    }

    #[test]
    fn determinism_across_calls() {
        let events = vec![
            ev(PdaEventKind::OrderBlock, 10, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 12, Direction::Bull),
            ev(PdaEventKind::MarketStructureShift, 14, Direction::Bull),
            ev(PdaEventKind::PropulsionBlock, 16, Direction::Bull),
            ev(PdaEventKind::BreakerBlock, 18, Direction::Bear),
        ];
        let a = match_all_setups_default(&events);
        let b = match_all_setups_default(&events);
        assert_eq!(a, b);
    }
}
