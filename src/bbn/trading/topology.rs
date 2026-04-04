use anyhow::Result;

use crate::bbn::{
    dag::BayesianNetwork,
    node::{ConditionalProbabilityTable, Node, NodeType},
};

pub fn build_trading_network() -> Result<BayesianNetwork> {
    let mut network = BayesianNetwork::new();

    let nodes = vec![
        root_node(
            "market_regime",
            "Market Regime",
            vec!["bull", "bear", "range"],
            vec![0.35, 0.30, 0.35],
        ),
        root_node(
            "liquidity_context",
            "Liquidity Context",
            vec!["favorable", "neutral", "hostile"],
            vec![0.4, 0.35, 0.25],
        ),
        conditional_node(
            "entry_quality",
            "Entry Quality",
            vec!["high", "medium", "low"],
            vec!["market_regime", "liquidity_context"],
        ),
        conditional_node(
            "trade_outcome",
            "Trade Outcome",
            vec!["win", "breakeven", "loss"],
            vec!["entry_quality"],
        ),
    ];

    for node in nodes {
        network.add_node(node)?;
    }

    network.add_edge("market_regime".into(), "entry_quality".into())?;
    network.add_edge("liquidity_context".into(), "entry_quality".into())?;
    network.add_edge("entry_quality".into(), "trade_outcome".into())?;

    populate_entry_quality_cpt(&mut network)?;
    populate_trade_outcome_cpt(&mut network)?;

    Ok(network)
}

fn root_node(id: &str, label: &str, states: Vec<&str>, prior: Vec<f64>) -> Node {
    let mut cpt = ConditionalProbabilityTable::new();
    cpt.insert(Vec::new(), prior);

    Node {
        id: id.into(),
        name: label.into(),
        node_type: NodeType::Observed,
        states: states.into_iter().map(|s| s.to_string()).collect(),
        parents: Vec::new(),
        cpt,
    }
}

fn conditional_node(id: &str, label: &str, states: Vec<&str>, parents: Vec<&str>) -> Node {
    Node {
        id: id.into(),
        name: label.into(),
        node_type: NodeType::Hidden,
        states: states.into_iter().map(|s| s.to_string()).collect(),
        parents: parents.into_iter().map(|s| s.to_string()).collect(),
        cpt: ConditionalProbabilityTable::new(),
    }
}

fn populate_entry_quality_cpt(network: &mut BayesianNetwork) -> Result<()> {
    let node = network.nodes.get_mut("entry_quality").unwrap();
    node.cpt.insert(vec![0, 0], vec![0.65, 0.25, 0.10]);
    node.cpt.insert(vec![0, 1], vec![0.50, 0.35, 0.15]);
    node.cpt.insert(vec![0, 2], vec![0.35, 0.40, 0.25]);
    node.cpt.insert(vec![1, 0], vec![0.40, 0.40, 0.20]);
    node.cpt.insert(vec![1, 1], vec![0.30, 0.45, 0.25]);
    node.cpt.insert(vec![1, 2], vec![0.20, 0.40, 0.40]);
    node.cpt.insert(vec![2, 0], vec![0.25, 0.45, 0.30]);
    node.cpt.insert(vec![2, 1], vec![0.20, 0.45, 0.35]);
    node.cpt.insert(vec![2, 2], vec![0.10, 0.35, 0.55]);
    Ok(())
}

fn populate_trade_outcome_cpt(network: &mut BayesianNetwork) -> Result<()> {
    let node = network.nodes.get_mut("trade_outcome").unwrap();
    node.cpt.insert(vec![0], vec![0.58, 0.22, 0.20]);
    node.cpt.insert(vec![1], vec![0.36, 0.28, 0.36]);
    node.cpt.insert(vec![2], vec![0.18, 0.17, 0.65]);
    Ok(())
}
