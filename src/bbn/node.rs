use std::collections::HashMap;

use anyhow::{anyhow, bail, Result};
use serde::{Deserialize, Serialize};

use super::evidence::{Evidence, EvidenceType};

pub type NodeId = String;
pub type ParentConfig = Vec<usize>;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum NodeType {
    Observed,
    Hidden,
    Decision,
    Utility,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ConditionalProbabilityTable {
    #[serde(with = "cpt_entries_serde")]
    pub entries: HashMap<ParentConfig, Vec<f64>>,
}

impl ConditionalProbabilityTable {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn insert(&mut self, parent_config: ParentConfig, probabilities: Vec<f64>) {
        self.entries.insert(parent_config, probabilities);
    }

    pub fn get(&self, parent_config: &ParentConfig) -> Option<&Vec<f64>> {
        self.entries.get(parent_config)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Node {
    pub id: NodeId,
    pub name: String,
    pub node_type: NodeType,
    pub states: Vec<String>,
    pub parents: Vec<NodeId>,
    pub cpt: ConditionalProbabilityTable,
}

impl Node {
    pub fn validate(&self) -> Result<()> {
        if self.id.trim().is_empty() {
            bail!("node id cannot be empty");
        }
        if self.states.is_empty() {
            bail!("node '{}' must define at least one state", self.id);
        }

        for (config, probs) in &self.cpt.entries {
            if probs.len() != self.states.len() {
                bail!(
                    "node '{}' CPT entry {:?} has {} probs but {} states",
                    self.id,
                    config,
                    probs.len(),
                    self.states.len()
                );
            }
            validate_probabilities(probs)?;
        }

        Ok(())
    }

    pub fn state_index(&self, state: &str) -> Option<usize> {
        self.states.iter().position(|s| s == state)
    }

    pub fn state_name(&self, index: usize) -> Option<&str> {
        self.states.get(index).map(|s| s.as_str())
    }

    pub fn probabilities_for_evidence(&self, evidence: &Evidence) -> Result<Vec<f64>> {
        let config = Self::parent_config_from_evidence(&self.parents, evidence)?;
        self.cpt.get(&config).cloned().ok_or_else(|| {
            anyhow!(
                "missing CPT entry for node '{}' and config {:?}",
                self.id,
                config
            )
        })
    }

    pub fn parent_config_from_evidence(
        parents: &[NodeId],
        evidence: &Evidence,
    ) -> Result<ParentConfig> {
        parents
            .iter()
            .map(|parent| match evidence.get(parent) {
                Some(EvidenceType::Hard(index)) => Ok(*index),
                Some(EvidenceType::Soft(distribution)) => distribution
                    .iter()
                    .enumerate()
                    .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                    .map(|(idx, _)| idx)
                    .ok_or_else(|| anyhow!("soft evidence for '{}' is empty", parent)),
                None => Err(anyhow!("missing evidence for parent '{}'", parent)),
            })
            .collect()
    }
}

fn validate_probabilities(probs: &[f64]) -> Result<()> {
    if probs.iter().any(|p| *p < 0.0 || !p.is_finite()) {
        bail!("probabilities must be finite and non-negative");
    }
    let sum: f64 = probs.iter().sum();
    if (sum - 1.0).abs() > 1e-6 {
        bail!("probabilities must sum to 1.0, got {}", sum);
    }
    Ok(())
}

mod cpt_entries_serde {
    use std::collections::HashMap;

    use serde::{Deserialize, Deserializer, Serialize, Serializer};

    use super::ParentConfig;

    pub fn serialize<S>(
        entries: &HashMap<ParentConfig, Vec<f64>>,
        serializer: S,
    ) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let entries: Vec<(&ParentConfig, &Vec<f64>)> = entries.iter().collect();
        entries.serialize(serializer)
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<HashMap<ParentConfig, Vec<f64>>, D::Error>
    where
        D: Deserializer<'de>,
    {
        let entries = Vec::<(ParentConfig, Vec<f64>)>::deserialize(deserializer)?;
        Ok(entries.into_iter().collect())
    }
}
