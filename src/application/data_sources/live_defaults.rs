use std::collections::BTreeMap;

use crate::data::realtime::LiveDataBackend;
use crate::market_catalog::MarketCatalog;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AnalyzeLiveSymbolDefaults {
    pub futures_symbol: String,
    pub spot_symbol: String,
    pub options_symbol: String,
    pub spot_kind: String,
}

pub fn resolve_live_backend_base_url(
    backend: &str,
    openalice_base_url: &str,
    nofx_base_url: &str,
) -> String {
    match backend.trim().to_ascii_lowercase().as_str() {
        "openbb" => "native://openbb".to_string(),
        "openalice" => openalice_base_url.to_string(),
        "nofx" => nofx_base_url.to_string(),
        _ => "native://openbb".to_string(),
    }
}

pub fn analyze_live_inferred_symbols(
    catalog: &MarketCatalog,
    symbol: &str,
) -> Option<AnalyzeLiveSymbolDefaults> {
    let defaults = catalog.live_defaults(symbol)?;
    Some(AnalyzeLiveSymbolDefaults {
        futures_symbol: defaults.futures_symbol,
        spot_symbol: defaults.spot_symbol,
        options_symbol: defaults.options_symbol,
        spot_kind: defaults.spot_kind,
    })
}

pub fn build_inferable_live_defaults_map(
    catalog: &MarketCatalog,
) -> BTreeMap<String, BTreeMap<String, String>> {
    catalog
        .market_keys_with_live_defaults()
        .into_iter()
        .filter_map(|market_key| {
            analyze_live_inferred_symbols(catalog, &market_key).map(|defaults| {
                (
                    market_key,
                    BTreeMap::from([
                        ("futures_symbol".to_string(), defaults.futures_symbol),
                        ("spot_symbol".to_string(), defaults.spot_symbol),
                        ("options_symbol".to_string(), defaults.options_symbol),
                        ("spot_kind".to_string(), defaults.spot_kind),
                    ]),
                )
            })
        })
        .collect()
}

pub fn parse_live_backend(backend: &str) -> anyhow::Result<LiveDataBackend> {
    LiveDataBackend::parse(backend)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::market_catalog::load_market_catalog;
    use std::path::PathBuf;

    #[test]
    fn resolve_live_backend_base_url_uses_expected_sources() {
        assert_eq!(
            resolve_live_backend_base_url("openbb", "http://oa", "http://nofx"),
            "native://openbb"
        );
        assert_eq!(
            resolve_live_backend_base_url("openalice", "http://oa", "http://nofx"),
            "http://oa"
        );
        assert_eq!(
            resolve_live_backend_base_url("nofx", "http://oa", "http://nofx"),
            "http://nofx"
        );
        assert_eq!(
            resolve_live_backend_base_url("unknown", "http://oa", "http://nofx"),
            "native://openbb"
        );
    }

    #[test]
    fn analyze_live_symbol_can_infer_gc_and_cl_defaults() {
        let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let catalog = load_market_catalog(&repo_root).unwrap();
        let gc = analyze_live_inferred_symbols(&catalog, "GC").unwrap();
        let cl = analyze_live_inferred_symbols(&catalog, "CL").unwrap();
        assert_eq!(gc.futures_symbol, "GC=F");
        assert_eq!(gc.spot_symbol, "GLD");
        assert_eq!(cl.futures_symbol, "CL=F");
        assert_eq!(cl.spot_symbol, "USO");
    }

    #[test]
    fn build_inferable_live_defaults_map_matches_catalog_markets() {
        let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
        let catalog = load_market_catalog(&repo_root).unwrap();
        let defaults = build_inferable_live_defaults_map(&catalog);
        assert_eq!(defaults["YM"]["spot_symbol"], "DIA");
        assert_eq!(defaults["CL"]["options_symbol"], "USO");
    }

    #[test]
    fn parse_live_backend_accepts_supported_values() {
        assert_eq!(parse_live_backend("openbb").unwrap().as_str(), "openbb");
        assert_eq!(
            parse_live_backend("openalice").unwrap().as_str(),
            "openalice"
        );
        assert_eq!(parse_live_backend("nofx").unwrap().as_str(), "nofx");
    }
}
