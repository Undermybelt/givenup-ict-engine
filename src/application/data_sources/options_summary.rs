use anyhow::Result;

use crate::data::realtime::IntegratedLiveDataSource;
use crate::data::realtime::openalice::OptionsChainSummary;
use crate::market_catalog::MarketCatalog;

pub fn resolve_options_volatility_proxy_symbol(
    catalog: &MarketCatalog,
    market_key: &str,
) -> Option<String> {
    catalog
        .relationships(market_key)
        .and_then(|item| item.options_volatility_proxy.clone())
}

pub fn fetch_options_summary_with_fallback(
    provider: &dyn IntegratedLiveDataSource,
    catalog: &MarketCatalog,
    market_key: &str,
    options_symbol: &str,
) -> Result<OptionsChainSummary> {
    match provider.fetch_options_chain_summary(options_symbol) {
        Ok(summary) => Ok(summary),
        Err(primary_error) => {
            if let Some(proxy_symbol) = resolve_options_volatility_proxy_symbol(catalog, market_key) {
                provider.fetch_options_volatility_proxy_summary(&proxy_symbol, options_symbol)
            } else {
                Err(primary_error)
            }
        }
    }
}
