//! Load / fallback persistence for the trading-domain Bayesian network.
//!
//! Centralises the snapshot-or-rebuild logic so the binary CLI
//! (`main.rs`) and library command entry points
//! (`application::auto_quant::command_entry`) share a single
//! implementation rather than maintaining duplicate copies.

use anyhow::Result;

use crate::bbn::BayesianNetwork;
use crate::state::{load_state, state_exists, BBN_STATE_FILE};

use super::topology::{build_trading_network, upgrade_trading_network};

/// Load the trading network from `<state_dir>/<symbol>/bbn_network.json`
/// if a persisted snapshot exists, otherwise initialise a fresh
/// network from the canonical topology builder. A malformed snapshot
/// is logged to `stderr` and falls back to a fresh build, matching
/// the long-standing CLI behaviour.
pub fn load_or_init_trading_network(symbol: &str, state_dir: &str) -> Result<BayesianNetwork> {
    if !state_exists(state_dir, symbol, BBN_STATE_FILE) {
        return build_trading_network();
    }
    match load_state::<BayesianNetwork, _>(state_dir, symbol, BBN_STATE_FILE) {
        Ok(mut network) => {
            upgrade_trading_network(&mut network)?;
            Ok(network)
        }
        Err(err) => {
            eprintln!(
                "warning: failed to load BBN state for '{}' from '{}': {}",
                symbol, state_dir, err
            );
            build_trading_network()
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::state::{save_state, BBN_STATE_FILE};

    #[test]
    fn returns_fresh_network_when_no_snapshot_exists() {
        let temp = tempfile::tempdir().unwrap();
        let net = load_or_init_trading_network("NQ", temp.path().to_str().unwrap()).unwrap();
        assert!(
            !net.nodes.is_empty(),
            "fresh trading network must have nodes"
        );
    }

    #[test]
    fn round_trips_persisted_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let original = build_trading_network().unwrap();
        save_state(temp.path(), "NQ", BBN_STATE_FILE, &original).unwrap();
        let loaded = load_or_init_trading_network("NQ", temp.path().to_str().unwrap()).unwrap();
        // Same topology, same node count.
        assert_eq!(loaded.nodes.len(), original.nodes.len());
    }

    #[test]
    fn falls_back_to_fresh_build_on_malformed_snapshot() {
        let temp = tempfile::tempdir().unwrap();
        let symbol = "NQ";
        std::fs::create_dir_all(temp.path().join(symbol)).unwrap();
        std::fs::write(
            temp.path().join(symbol).join(BBN_STATE_FILE),
            "{not valid json",
        )
        .unwrap();
        // Must not bubble up the parse error.
        let net = load_or_init_trading_network(symbol, temp.path().to_str().unwrap()).unwrap();
        assert!(!net.nodes.is_empty());
    }
}
