use anyhow::{Context, Result};
use serde::{de::DeserializeOwned, Serialize};
use std::path::Path;

/// Load state from JSON file
pub fn load_state<T: DeserializeOwned, P: AsRef<Path>>(
    dir: P,
    symbol: &str,
    filename: &str,
) -> Result<T> {
    let path = dir.as_ref().join(symbol).join(filename);
    let content = std::fs::read_to_string(&path)
        .with_context(|| format!("Failed to read state file: {:?}", path))?;
    let data: T = serde_json::from_str(&content)
        .with_context(|| format!("Failed to parse state file: {:?}", path))?;
    Ok(data)
}

/// Save state to JSON file
pub fn save_state<T: Serialize, P: AsRef<Path>>(
    dir: P,
    symbol: &str,
    filename: &str,
    data: &T,
) -> Result<()> {
    let dir_path = dir.as_ref().join(symbol);
    std::fs::create_dir_all(&dir_path)
        .with_context(|| format!("Failed to create directory: {:?}", dir_path))?;

    let path = dir_path.join(filename);
    let json = serde_json::to_string_pretty(data).context("Failed to serialize state")?;
    std::fs::write(&path, json)
        .with_context(|| format!("Failed to write state file: {:?}", path))?;

    Ok(())
}

/// Check if state file exists
pub fn state_exists<P: AsRef<Path>>(dir: P, symbol: &str, filename: &str) -> bool {
    dir.as_ref().join(symbol).join(filename).exists()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::bbn::trading::topology::build_trading_network;

    #[test]
    fn test_save_and_load_bayesian_network_state() {
        let temp = tempfile::tempdir().unwrap();
        let network = build_trading_network().unwrap();

        save_state(temp.path(), "NQ", "bbn_network.json", &network).unwrap();
        let restored =
            load_state::<crate::bbn::BayesianNetwork, _>(temp.path(), "NQ", "bbn_network.json")
                .unwrap();

        assert_eq!(network.nodes.len(), restored.nodes.len());
        assert_eq!(network.edges.len(), restored.edges.len());
        assert_eq!(network.topological_order, restored.topological_order);
    }
}
