//! Unified PDA event timeline + adjacency matrices.
//!
//! This module is **separate** from `crate::pda_sequence`:
//! - `pda_sequence` is the DTW / clustering pipeline keyed on
//!   `PdaTokenKind` (a 7-variant enum frozen at v1 to keep the
//!   clustering fixture stable).
//! - `pda_timeline` owns its own richer 13-variant `PdaEventKind`
//!   and is consumed by canonical-setup matchers and the
//!   factor_research evidence layer in P1b.
//!
//! Public surface:
//! - [`PdaEvent`], [`PdaEventKind`], [`ALL_EVENT_KINDS`]
//! - [`build_pda_timeline`] — assemble a sorted `Vec<PdaEvent>` from
//!   `(candles, atr)` using all 13 detectors with module defaults.
//! - [`compute_cooccurrence_matrix`], [`compute_precedence_matrix`],
//!   [`EventMatrix`], [`MatrixKind`].

pub mod builder;
pub mod event;
pub mod matrices;

pub use builder::{
    assert_timeline_bars_valid, build_pda_timeline, TIMELINE_DEFAULT_CISD_MIN_STRENGTH,
    TIMELINE_DEFAULT_LIQUIDITY_POOL_ATR_MULT, TIMELINE_DEFAULT_LIQUIDITY_POOL_MIN_TOUCHES,
    TIMELINE_DEFAULT_LIQUIDITY_SWEEP_RETURN_BARS, TIMELINE_DEFAULT_RB_BODY_WICK_RATIO,
    TIMELINE_DEFAULT_RB_MIN_RANGE_ATR, TIMELINE_DEFAULT_SWING_STRENGTH,
};
pub use event::{PdaEvent, PdaEventKind, ALL_EVENT_KINDS};
pub use matrices::{
    compute_cooccurrence_matrix, compute_precedence_matrix, EventMatrix, MatrixKind,
};
