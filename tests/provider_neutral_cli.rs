use ict_engine::application::data_sources::{
    build_market_data_harness_plan, MarketDataHarnessRequest, MarketDataHarnessSymbolSpec,
};
use ict_engine::market_catalog::load_market_catalog;
use std::collections::BTreeMap;
use std::path::PathBuf;
use std::process::Command;
use tempfile::TempDir;

#[test]
fn public_help_avoids_repo_market_examples() {
    let binary = env!("CARGO_BIN_EXE_ict-engine");

    let root_help = Command::new(binary).arg("--help").output().unwrap();
    let root_help = String::from_utf8(root_help.stdout).unwrap();
    assert!(!root_help.contains("NQ, ES, GC"));

    let harness_help = Command::new(binary)
        .args(["market-data-harness", "--help"])
        .output()
        .unwrap();
    let harness_help = String::from_utf8(harness_help.stdout).unwrap();
    assert!(!harness_help.contains("NQ, ES, AAPL, BTCUSDT"));
}

#[test]
fn harness_plan_rejects_repo_label_without_explicit_symbol_specs() {
    let err = build_market_data_harness_plan(MarketDataHarnessRequest {
        market_key: "ES".to_string(),
        primary_data_path: None,
        interval: Some("1d".to_string()),
        start: None,
        end: None,
        count: Some(30),
        related_roles: vec!["etf_reference".to_string()],
        provider_preferences: BTreeMap::new(),
        symbol_overrides: BTreeMap::new(),
        options_volatility_proxy_symbol: None,
    })
    .unwrap_err();

    assert!(err
        .to_string()
        .contains("market-data-harness request validation failed"));
}

#[test]
fn harness_plan_uses_only_explicit_request_data() {
    let plan = build_market_data_harness_plan(MarketDataHarnessRequest {
        market_key: "caller-label".to_string(),
        primary_data_path: None,
        interval: Some("1d".to_string()),
        start: None,
        end: None,
        count: Some(30),
        related_roles: vec!["etf_reference".to_string(), "options_underlying".to_string()],
        provider_preferences: BTreeMap::from([
            ("etf_reference".to_string(), "yfinance".to_string()),
            ("options_underlying".to_string(), "tradingview_mcp".to_string()),
        ]),
        symbol_overrides: BTreeMap::from([
            (
                "etf_reference".to_string(),
                MarketDataHarnessSymbolSpec {
                    display_symbol: Some("SPY".to_string()),
                    yfinance: Some("SPY".to_string()),
                    ..MarketDataHarnessSymbolSpec::default()
                },
            ),
            (
                "options_underlying".to_string(),
                MarketDataHarnessSymbolSpec {
                    display_symbol: Some("AMEX:SPY".to_string()),
                    tradingview_mcp: Some("AMEX:SPY".to_string()),
                    ..MarketDataHarnessSymbolSpec::default()
                },
            ),
        ]),
        options_volatility_proxy_symbol: Some("^VIX".to_string()),
    })
    .unwrap();

    assert_eq!(plan.tasks.len(), 2);
    assert!(plan
        .tasks
        .iter()
        .any(|task| task.role == "etf_reference" && task.request_symbol() == "SPY"));
    assert!(plan.tasks.iter().any(|task| {
        task.role == "options_underlying"
            && task.request_symbol() == "AMEX:SPY"
            && task.fallback_options_proxy_symbol.as_deref() == Some("^VIX")
    }));
}

#[test]
fn repo_market_pack_is_loadable_only_when_called_explicitly() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();

    let es = catalog.live_defaults("ES").unwrap();
    assert_eq!(es.futures_symbol, "ES=F");
    assert_eq!(es.spot_symbol, "SPY");
}

#[test]
fn bootstrap_output_keeps_actionable_local_paths_and_valid_commands() {
    let binary = env!("CARGO_BIN_EXE_ict-engine");
    let state = TempDir::new().unwrap();

    let output = Command::new(binary)
        .args([
            "workflow-status",
            "--symbol",
            "DEMO",
            "--state-dir",
            state.path().to_str().unwrap(),
            "--phase",
            "agent-bootstrap",
        ])
        .output()
        .unwrap();

    assert!(output.status.success());
    let stdout = String::from_utf8(output.stdout).unwrap();
    assert!(!stdout.contains("--market "));
    assert!(!stdout.contains("<local-path>"));
    assert!(stdout.contains(state.path().to_str().unwrap()));
}
