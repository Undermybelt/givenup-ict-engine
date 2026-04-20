//! NLP-inspired PDA sequence clustering (Phase 1 skeleton of
//! `docs/plans/nlp-inspired-pda-sequence-clustering-plan.md`).
//!
//! This module is intentionally standalone:
//! - no main.rs wiring
//! - no PreBayes / BBN hookup
//! - no trading decisions derived from cluster labels
//!
//! The schema (`PdaDtwClusterPacket`) is fixed first so downstream surfaces
//! (RegimeSegmentationPacket, reflection_bundle, factor-research output)
//! can start consuming it as soon as the PDA detection layer learns to emit
//! `PdaToken` sequences.

pub mod cluster;
pub mod dtw;
pub mod emitter;
pub mod kmedoids;
pub mod token;

pub use cluster::{cluster_pda_sequences, PdaDtwClusterPacket, PDA_DTW_CLUSTER_METHOD};
pub use dtw::{dtw_alignment, dtw_distance, dtw_distance_matrix, DtwAlignment};
pub use emitter::{
    emit_pda_sequence_from_candles, EMITTER_ATR_PERIOD, EMITTER_CISD_MIN_STRENGTH,
    EMITTER_LIQUIDITY_POOL_ATR_MULT, EMITTER_LIQUIDITY_POOL_MIN_TOUCHES,
    EMITTER_LIQUIDITY_SWEEP_RETURN_BARS, EMITTER_NEAR_SWEEP_WINDOW_BARS,
    EMITTER_OVERLAP_WINDOW_BARS, EMITTER_RB_BODY_WICK_RATIO, EMITTER_RB_MIN_RANGE_ATR,
    EMITTER_SWING_STRENGTH,
};
pub use kmedoids::{pam_cluster, PamOutcome};
pub use token::{pda_token_cost, PdaToken, PdaTokenKind};
