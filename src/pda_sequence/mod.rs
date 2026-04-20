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
pub mod kmedoids;
pub mod token;

pub use cluster::{cluster_pda_sequences, PdaDtwClusterPacket, PDA_DTW_CLUSTER_METHOD};
pub use dtw::{dtw_alignment, dtw_distance, dtw_distance_matrix, DtwAlignment};
pub use kmedoids::{pam_cluster, PamOutcome};
pub use token::{pda_token_cost, PdaToken, PdaTokenKind};
