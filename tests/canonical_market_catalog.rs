use ict_engine::market_catalog::load_market_catalog;
use ict_engine::application::data_sources::{
    build_inferable_live_defaults_map, build_market_data_harness_plan, resolve_options_volatility_proxy_symbol,
    MarketDataHarnessRequest,
};
use std::collections::BTreeMap;
use std::path::PathBuf;

#[test]
fn catalog_derives_live_defaults_and_relationships_from_repo_config() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();

    let es = catalog.live_defaults("ES").unwrap();
    assert_eq!(es.futures_symbol, "ES=F");
    assert_eq!(es.spot_symbol, "SPY");
    assert_eq!(es.options_symbol, "SPY");
    assert_eq!(es.spot_kind, "equity");

    let cl = catalog.live_defaults("CL").unwrap();
    assert_eq!(cl.futures_symbol, "CL=F");
    assert_eq!(cl.spot_symbol, "USO");

    let btc = catalog.relationships("BTC").unwrap();
    assert!(btc.related_crypto_symbols.contains(&"ETH".to_string()));
    assert_eq!(btc.options_volatility_proxy, None);
}

#[test]
fn harness_plan_preserves_provider_execution_specs_from_catalog() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();

    let plan = build_market_data_harness_plan(
        MarketDataHarnessRequest {
            market_key: "ES".to_string(),
            primary_data_path: None,
            interval: Some("1d".to_string()),
            start: None,
            end: None,
            count: Some(30),
            related_roles: vec!["etf_reference".to_string(), "volatility_reference".to_string()],
            provider_preferences: BTreeMap::from([
                ("etf_reference".to_string(), "tradingview_mcp".to_string()),
                ("volatility_reference".to_string(), "ibkr".to_string()),
            ]),
            symbol_overrides: BTreeMap::new(),
        },
        &catalog,
    )
    .unwrap();

    let spy = plan
        .tasks
        .iter()
        .find(|task| task.role == "etf_reference")
        .unwrap();
    assert_eq!(spy.request_symbol(), "AMEX:SPY");

    let vix = plan
        .tasks
        .iter()
        .find(|task| task.role == "volatility_reference")
        .unwrap();
    let contract = vix.ibkr_contract().unwrap();
    assert_eq!(contract.exchange, "CBOE");
    assert_eq!(contract.sec_type, "IND");
}

#[test]
fn workflow_bootstrap_defaults_match_catalog_defaults() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();
    let defaults = build_inferable_live_defaults_map(&catalog);

    assert_eq!(defaults["YM"]["spot_symbol"], "DIA");
    assert_eq!(defaults["CL"]["options_symbol"], "USO");
}

#[test]
fn catalog_relationships_define_es_companions_and_proxy() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();

    assert_eq!(
        resolve_options_volatility_proxy_symbol(&catalog, "ES").as_deref(),
        Some("^VIX")
    );
    let es = catalog.relationships("ES").unwrap();
    assert!(es.related_cfd_symbols.contains(&"US500".to_string()));
}

#[test]
fn catalog_covers_all_production_markets() {
    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let catalog = load_market_catalog(&repo_root).unwrap();

    for market in ["NQ", "ES", "YM", "GC", "CL"] {
        assert!(
            catalog.live_defaults(market).is_some(),
            "missing live defaults for {market}"
        );
    }

    for market in ["NQ", "ES", "YM", "GC", "CL", "BTC", "ETH", "SOL"] {
        assert!(
            catalog.relationships(market).is_some(),
            "missing relationships for {market}"
        );
    }
}
