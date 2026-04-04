use std::collections::HashMap;

use anyhow::{bail, Result};
use serde::{Deserialize, Serialize};

use super::node::NodeId;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum EvidenceType {
    Hard(usize),
    Soft(Vec<f64>),
}

pub type Evidence = HashMap<NodeId, EvidenceType>;
pub type IndicatorValues = HashMap<String, f64>;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ICTStructureSummary {
    pub bias: Option<String>,
    pub dealing_range: Option<String>,
    pub session: Option<String>,
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EvidenceSource {
    pub indicator_values: IndicatorValues,
    pub structure_summary: ICTStructureSummary,
}

#[derive(Debug, Clone, Default)]
pub struct EvidenceManager {
    evidence: Evidence,
}

impl EvidenceManager {
    pub fn new() -> Self {
        Self {
            evidence: Evidence::new(),
        }
    }

    pub fn with_evidence(evidence: Evidence) -> Result<Self> {
        validate_evidence(&evidence)?;
        Ok(Self { evidence })
    }

    pub fn insert_hard(&mut self, node_id: impl Into<NodeId>, state_index: usize) {
        self.evidence
            .insert(node_id.into(), EvidenceType::Hard(state_index));
    }

    pub fn insert_soft(&mut self, node_id: impl Into<NodeId>, distribution: Vec<f64>) {
        self.evidence
            .insert(node_id.into(), EvidenceType::Soft(distribution));
    }

    pub fn get(&self, node_id: &str) -> Option<&EvidenceType> {
        self.evidence.get(node_id)
    }

    pub fn as_map(&self) -> &Evidence {
        &self.evidence
    }

    pub fn into_map(self) -> Evidence {
        self.evidence
    }
}

pub fn validate_evidence(evidence: &Evidence) -> Result<()> {
    for (node_id, value) in evidence {
        match value {
            EvidenceType::Hard(_) => {}
            EvidenceType::Soft(probs) => {
                if probs.is_empty() {
                    bail!("soft evidence for '{}' cannot be empty", node_id);
                }
                if probs.iter().any(|p| *p < 0.0 || !p.is_finite()) {
                    bail!(
                        "soft evidence for '{}' contains invalid probability",
                        node_id
                    );
                }
                let sum: f64 = probs.iter().sum();
                if (sum - 1.0).abs() > 1e-6 {
                    bail!(
                        "soft evidence for '{}' must sum to 1.0, got {}",
                        node_id,
                        sum
                    );
                }
            }
        }
    }
    Ok(())
}

pub trait EvidenceExt {
    fn insert_hard(&mut self, node_id: impl Into<NodeId>, state_index: usize);
    fn insert_soft(&mut self, node_id: impl Into<NodeId>, distribution: Vec<f64>);
}

impl EvidenceExt for Evidence {
    fn insert_hard(&mut self, node_id: impl Into<NodeId>, state_index: usize) {
        self.insert(node_id.into(), EvidenceType::Hard(state_index));
    }

    fn insert_soft(&mut self, node_id: impl Into<NodeId>, distribution: Vec<f64>) {
        self.insert(node_id.into(), EvidenceType::Soft(distribution));
    }
}
