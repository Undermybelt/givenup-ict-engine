use anyhow::Result;
use chrono::Timelike;
use chrono_tz::America::New_York;
use serde::Serialize;

use super::series::{aligned_close_series, close_to_returns};
use crate::data::realtime::market_support::AuxiliaryMarketEvidence;
use crate::ict::{
    detect_market_structure_shifts_default, detect_order_blocks, detect_propulsion_blocks_default,
    find_nearest_fvg, has_recent_cisd,
};
use crate::indicators::atr::compute_atr;
use crate::smt::{Cointegration, Correlation, Divergence};
use crate::types::{Candle, Direction};

#[derive(Debug, Clone, Serialize)]
pub struct SmtRelationshipResolverOutput {
    pub symbol: String,
    pub primary_related_symbols: Vec<String>,
    pub futures_peers: Vec<String>,
    pub cfd_proxies: Vec<String>,
    pub etf_proxies: Vec<String>,
    pub sector_or_industry_peers: Vec<String>,
    pub currency_macro_drivers: Vec<String>,
    pub session_leaders: Vec<String>,
    pub relationship_type: String,
    pub confidence: f64,
    pub evidence_source: String,
}

#[derive(Debug, Clone)]
struct CorrelationAssetMap {
    related_futures_symbols: Vec<String>,
    related_etf_symbols: Vec<String>,
    related_options_symbols: Vec<String>,
    related_cfd_symbols: Vec<String>,
    related_crypto_symbols: Vec<String>,
}

pub fn resolve_smt_relationships(
    symbol: &str,
    available_symbols: Option<&[String]>,
) -> SmtRelationshipResolverOutput {
    let upper = symbol.to_ascii_uppercase();
    let mut output = match upper.as_str() {
        "NQ" | "MNQ" => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: vec!["ES", "YM", "RTY"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            futures_peers: vec!["ES", "YM", "RTY", "DXY", "VIX"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            cfd_proxies: vec!["NAS100", "US500", "US30"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            etf_proxies: vec!["QQQ", "SPY", "DIA", "IWM"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: vec!["DXY", "VIX"].into_iter().map(str::to_string).collect(),
            session_leaders: vec!["NQ", "ES"].into_iter().map(str::to_string).collect(),
            relationship_type: "index_peer".to_string(),
            confidence: 0.90,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        "ES" | "MES" => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: vec!["NQ", "YM", "RTY"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            futures_peers: vec!["NQ", "YM", "RTY", "DXY", "VIX"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            cfd_proxies: vec!["US500", "NAS100", "US30"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            etf_proxies: vec!["SPY", "QQQ", "DIA", "IWM"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: vec!["DXY", "VIX"].into_iter().map(str::to_string).collect(),
            session_leaders: vec!["ES", "NQ"].into_iter().map(str::to_string).collect(),
            relationship_type: "index_peer".to_string(),
            confidence: 0.90,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        "EURUSD" => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: vec!["GBPUSD", "DXY", "EURGBP"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            futures_peers: vec!["6E", "DX"].into_iter().map(str::to_string).collect(),
            cfd_proxies: vec!["GBPUSD", "EURGBP"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            etf_proxies: vec!["FXE", "UUP"].into_iter().map(str::to_string).collect(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: vec!["DXY", "US10Y"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            session_leaders: vec!["EURUSD", "DXY"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            relationship_type: "currency_driver".to_string(),
            confidence: 0.80,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        "XAUUSD" | "GC" | "MGC" => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: vec!["XAGUSD", "DXY", "US10Y", "real_yield", "GDX"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            futures_peers: vec!["GC", "SI"].into_iter().map(str::to_string).collect(),
            cfd_proxies: vec!["XAUUSD", "XAGUSD"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            etf_proxies: vec!["GLD", "SLV", "GDX"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: vec!["DXY", "US10Y", "real_yield"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            session_leaders: vec!["GC", "DXY"].into_iter().map(str::to_string).collect(),
            relationship_type: "commodity_pair".to_string(),
            confidence: 0.78,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        "BTC" | "BTCUSD" | "BTCUSDT" => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: vec!["ETH", "SOL", "TOTAL", "QQQ", "DXY"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            futures_peers: vec!["BTC", "ETH"].into_iter().map(str::to_string).collect(),
            cfd_proxies: vec!["BTCUSD", "ETHUSD"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            etf_proxies: vec!["IBIT", "ETHA", "QQQ"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: vec!["DXY", "QQQ"].into_iter().map(str::to_string).collect(),
            session_leaders: vec!["BTC", "ETH"].into_iter().map(str::to_string).collect(),
            relationship_type: "crypto_beta".to_string(),
            confidence: 0.78,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        _ if looks_like_equity_symbol(&upper) => SmtRelationshipResolverOutput {
            symbol: upper.clone(),
            primary_related_symbols: vec!["SPY", "QQQ"].into_iter().map(str::to_string).collect(),
            futures_peers: vec!["ES", "NQ", "VIX", "DXY"]
                .into_iter()
                .map(str::to_string)
                .collect(),
            cfd_proxies: Vec::new(),
            etf_proxies: equity_market_proxy_etfs(&upper)
                .into_iter()
                .map(str::to_string)
                .collect(),
            sector_or_industry_peers: vec![equity_market_proxy_etfs(&upper)
                .last()
                .copied()
                .unwrap_or("SPY")
                .to_string()],
            currency_macro_drivers: vec!["DXY", "VIX"].into_iter().map(str::to_string).collect(),
            session_leaders: vec![upper.clone(), "SPY".to_string()],
            relationship_type: "sector_peer".to_string(),
            confidence: 0.65,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
        _ => SmtRelationshipResolverOutput {
            symbol: upper,
            primary_related_symbols: Vec::new(),
            futures_peers: Vec::new(),
            cfd_proxies: Vec::new(),
            etf_proxies: Vec::new(),
            sector_or_industry_peers: Vec::new(),
            currency_macro_drivers: Vec::new(),
            session_leaders: Vec::new(),
            relationship_type: "unknown".to_string(),
            confidence: 0.0,
            evidence_source: "builtin_symbol_relationship_seed".to_string(),
        },
    };

    if let Some(available) = available_symbols {
        filter_available_symbols(&mut output.primary_related_symbols, available);
        filter_available_symbols(&mut output.futures_peers, available);
        filter_available_symbols(&mut output.cfd_proxies, available);
        filter_available_symbols(&mut output.etf_proxies, available);
        filter_available_symbols(&mut output.sector_or_industry_peers, available);
        filter_available_symbols(&mut output.currency_macro_drivers, available);
        filter_available_symbols(&mut output.session_leaders, available);
    }

    dedup_sorted(&mut output.primary_related_symbols);
    dedup_sorted(&mut output.futures_peers);
    dedup_sorted(&mut output.cfd_proxies);
    dedup_sorted(&mut output.etf_proxies);
    dedup_sorted(&mut output.sector_or_industry_peers);
    dedup_sorted(&mut output.currency_macro_drivers);
    dedup_sorted(&mut output.session_leaders);
    output
}

fn dedup_sorted(symbols: &mut Vec<String>) {
    symbols.sort();
    symbols.dedup();
}

fn correlation_asset_map(
    futures_symbol: &str,
    spot_symbol: &str,
    options_symbol: &str,
) -> CorrelationAssetMap {
    correlation_asset_map_with_available(futures_symbol, spot_symbol, options_symbol, None)
}

fn correlation_asset_map_with_available(
    futures_symbol: &str,
    spot_symbol: &str,
    options_symbol: &str,
    available_symbols: Option<&[String]>,
) -> CorrelationAssetMap {
    let upper = futures_symbol.to_ascii_uppercase();
    let mut related_futures_symbols = Vec::new();
    let mut related_etf_symbols = vec![spot_symbol.to_string()];
    let mut related_cfd_symbols = Vec::new();
    let mut related_crypto_symbols = Vec::new();

    match upper.as_str() {
        "NQ" | "MNQ" => {
            related_futures_symbols.extend(["ES", "YM", "RTY", "DXY", "VIX"].map(str::to_string));
            related_etf_symbols.extend(["QQQ", "SPY", "DIA", "IWM"].map(str::to_string));
            related_cfd_symbols.extend(["NAS100", "US500", "US30"].map(str::to_string));
        }
        "ES" | "MES" => {
            related_futures_symbols.extend(["NQ", "YM", "RTY", "DXY", "VIX"].map(str::to_string));
            related_etf_symbols.extend(["SPY", "QQQ", "DIA", "IWM"].map(str::to_string));
            related_cfd_symbols.extend(["US500", "NAS100", "US30"].map(str::to_string));
        }
        "YM" | "MYM" => {
            related_futures_symbols.extend(["ES", "NQ", "RTY"].map(str::to_string));
            related_etf_symbols.extend(["DIA", "SPY", "QQQ", "IWM"].map(str::to_string));
            related_cfd_symbols.extend(["US30", "US500", "NAS100"].map(str::to_string));
        }
        "RTY" | "M2K" => {
            related_futures_symbols.extend(["ES", "NQ", "YM"].map(str::to_string));
            related_etf_symbols.extend(["IWM", "SPY", "QQQ", "DIA"].map(str::to_string));
            related_cfd_symbols.extend(["US2000", "US500", "NAS100"].map(str::to_string));
        }
        "XAUUSD" | "GC" | "MGC" => {
            related_futures_symbols
                .extend(["XAGUSD", "SI", "DXY", "US10Y", "REAL_YIELD"].map(str::to_string));
            related_etf_symbols.extend(["GLD", "SLV", "GDX"].map(str::to_string));
        }
        "BTC" | "BTCUSD" | "BTCUSDT" => {
            related_crypto_symbols.extend(["ETH", "SOL", "TOTAL"].map(str::to_string));
            related_futures_symbols.extend(["DXY"].map(str::to_string));
            related_etf_symbols.extend(["IBIT", "ETHE", "QQQ"].map(str::to_string));
        }
        "EURUSD" => {
            related_futures_symbols.extend(["DXY"].map(str::to_string));
            related_etf_symbols.extend(["FXE", "UUP"].map(str::to_string));
            related_cfd_symbols.extend(["GBPUSD", "EURGBP"].map(str::to_string));
        }
        "GBPUSD" => {
            related_futures_symbols.extend(["DXY"].map(str::to_string));
            related_etf_symbols.extend(["FXB", "UUP"].map(str::to_string));
            related_cfd_symbols.extend(["EURUSD", "EURGBP"].map(str::to_string));
        }
        _ => {
            if looks_like_equity_symbol(&upper) {
                related_etf_symbols.extend(
                    equity_market_proxy_etfs(&upper)
                        .into_iter()
                        .map(str::to_string),
                );
                related_futures_symbols.extend(["ES", "NQ", "VIX", "DXY"].map(str::to_string));
            }
        }
    }

    if let Some(available) = available_symbols {
        filter_available_symbols(&mut related_futures_symbols, available);
        filter_available_symbols(&mut related_etf_symbols, available);
        filter_available_symbols(&mut related_cfd_symbols, available);
        filter_available_symbols(&mut related_crypto_symbols, available);
    }

    related_futures_symbols.sort();
    related_futures_symbols.dedup();
    related_etf_symbols.sort();
    related_etf_symbols.dedup();
    related_cfd_symbols.sort();
    related_cfd_symbols.dedup();
    related_crypto_symbols.sort();
    related_crypto_symbols.dedup();

    CorrelationAssetMap {
        related_futures_symbols,
        related_etf_symbols,
        related_options_symbols: vec![options_symbol.to_string()],
        related_cfd_symbols,
        related_crypto_symbols,
    }
}

fn looks_like_equity_symbol(symbol: &str) -> bool {
    !symbol.is_empty()
        && symbol.len() <= 5
        && symbol
            .chars()
            .all(|character| character.is_ascii_uppercase() || character == '.')
}

fn equity_market_proxy_etfs(symbol: &str) -> Vec<&'static str> {
    let sector_etf = match symbol {
        "AAPL" | "MSFT" | "NVDA" | "AMD" | "AVGO" | "META" | "GOOGL" | "GOOG" => "XLK",
        "JPM" | "BAC" | "GS" | "MS" | "WFC" => "XLF",
        "XOM" | "CVX" | "COP" | "SLB" => "XLE",
        "TSLA" | "AMZN" | "HD" | "MCD" | "NKE" => "XLY",
        "LLY" | "UNH" | "JNJ" | "MRK" | "PFE" => "XLV",
        _ => "SPY",
    };
    vec!["SPY", "QQQ", "IWM", sector_etf]
}

fn filter_available_symbols(symbols: &mut Vec<String>, available_symbols: &[String]) {
    let available: std::collections::BTreeSet<String> = available_symbols
        .iter()
        .map(|symbol| symbol.to_ascii_uppercase())
        .collect();
    symbols.retain(|symbol| available.contains(&symbol.to_ascii_uppercase()));
}

#[derive(Debug, Serialize)]
pub struct SmtCorrelationSection {
    pub probability_role: String,
    pub paired_market_available: bool,
    pub futures_symbol: Option<String>,
    pub spot_symbol: Option<String>,
    pub timeframe: Option<String>,
    pub session: Option<String>,
    pub primary_related_symbols: Vec<String>,
    pub futures_peers: Vec<String>,
    pub cfd_proxies: Vec<String>,
    pub etf_proxies: Vec<String>,
    pub sector_or_industry_peers: Vec<String>,
    pub currency_macro_drivers: Vec<String>,
    pub session_leaders: Vec<String>,
    pub related_futures_symbols: Vec<String>,
    pub related_etf_symbols: Vec<String>,
    pub related_options_symbols: Vec<String>,
    pub related_cfd_symbols: Vec<String>,
    pub related_crypto_symbols: Vec<String>,
    pub rolling_correlation_20: Option<f64>,
    pub rolling_correlation_50: Option<f64>,
    pub divergence_detected: Option<bool>,
    pub cointegration_stat: Option<f64>,
    pub cointegrated: Option<bool>,
    pub raw_basis_bps: Option<f64>,
    pub normalized_basis_bps: Option<f64>,
    pub rolling_price_ratio_mean: Option<f64>,
    pub smt_signal: Option<String>,
    pub base_swing_type: Option<String>,
    pub base_level: Option<f64>,
    pub comparison_swing_type: Option<String>,
    pub comparison_level: Option<f64>,
    pub raw_comparison_swing_type: Option<String>,
    pub raw_comparison_level: Option<f64>,
    pub swept_side: Option<String>,
    pub normalized_for_inverse_correlation: bool,
    pub near_pd_array: Option<bool>,
    pub pd_array_type: Option<String>,
    pub mss_or_cisd_confirmed: Option<bool>,
    pub displacement_confirmed: Option<bool>,
    pub resolver_relationship_type: String,
    pub resolver_confidence: f64,
    pub resolver_evidence_source: String,
    pub relationship_type: String,
    pub relationship_confidence: f64,
    pub trade_use: String,
    pub fail_closed_reason: Option<String>,
    pub notes: Vec<String>,
    pub narrative: String,
}

#[derive(Debug, Clone)]
struct IctSmtSnapshot {
    smt_signal: Option<String>,
    base_swing_type: Option<String>,
    base_level: Option<f64>,
    comparison_swing_type: Option<String>,
    comparison_level: Option<f64>,
    raw_comparison_swing_type: Option<String>,
    raw_comparison_level: Option<f64>,
    swept_side: Option<String>,
    fail_closed_reason: Option<String>,
}

#[derive(Debug, Clone)]
struct SmtContextHints {
    timeframe: Option<String>,
    session: Option<String>,
    near_pd_array: Option<bool>,
    pd_array_type: Option<String>,
    mss_or_cisd_confirmed: Option<bool>,
    displacement_confirmed: Option<bool>,
}

pub fn empty_smt_correlation_section() -> SmtCorrelationSection {
    SmtCorrelationSection {
        probability_role: "cross_market_confirmation_for_probability_model".to_string(),
        paired_market_available: false,
        futures_symbol: None,
        spot_symbol: None,
        timeframe: None,
        session: None,
        primary_related_symbols: Vec::new(),
        futures_peers: Vec::new(),
        cfd_proxies: Vec::new(),
        etf_proxies: Vec::new(),
        sector_or_industry_peers: Vec::new(),
        currency_macro_drivers: Vec::new(),
        session_leaders: Vec::new(),
        related_futures_symbols: Vec::new(),
        related_etf_symbols: Vec::new(),
        related_options_symbols: Vec::new(),
        related_cfd_symbols: Vec::new(),
        related_crypto_symbols: Vec::new(),
        rolling_correlation_20: None,
        rolling_correlation_50: None,
        divergence_detected: None,
        cointegration_stat: None,
        cointegrated: None,
        raw_basis_bps: None,
        normalized_basis_bps: None,
        rolling_price_ratio_mean: None,
        smt_signal: None,
        base_swing_type: None,
        base_level: None,
        comparison_swing_type: None,
        comparison_level: None,
        raw_comparison_swing_type: None,
        raw_comparison_level: None,
        swept_side: None,
        normalized_for_inverse_correlation: false,
        near_pd_array: None,
        pd_array_type: None,
        mss_or_cisd_confirmed: None,
        displacement_confirmed: None,
        resolver_relationship_type: "unknown".to_string(),
        resolver_confidence: 0.0,
        resolver_evidence_source: "unavailable".to_string(),
        relationship_type: "unavailable".to_string(),
        relationship_confidence: 0.0,
        trade_use: "confirmation_only".to_string(),
        fail_closed_reason: Some("paired_market_not_provided".to_string()),
        notes: vec!["paired_market_not_provided".to_string()],
        narrative: "smt_analysis_unavailable_without_paired_market".to_string(),
    }
}

pub fn build_smt_correlation_section(
    futures_symbol: &str,
    spot_symbol: &str,
    futures_candles: &[Candle],
    spot_candles: &[Candle],
    auxiliary: &AuxiliaryMarketEvidence,
) -> Result<SmtCorrelationSection> {
    let asset_map = correlation_asset_map(futures_symbol, spot_symbol, &auxiliary.options_symbol);
    let (futures_series, spot_series) = aligned_close_series(futures_candles, spot_candles);
    let futures_returns = close_to_returns(&futures_series);
    let spot_returns = close_to_returns(&spot_series);
    let rolling_correlation_20 = Correlation::rolling(&futures_returns, &spot_returns, 20)
        .last()
        .copied();
    let rolling_correlation_50 = Correlation::rolling(&futures_returns, &spot_returns, 50)
        .last()
        .copied();
    let (relationship_type, relationship_confidence, normalized_for_inverse_correlation) =
        classify_relationship(rolling_correlation_20, rolling_correlation_50);
    let divergence_detected = Divergence::detect(&futures_series, &spot_series, 20)
        .last()
        .copied();
    let ict_smt = if relationship_type == "uncertain" {
        empty_ict_smt("relationship_uncertain")
    } else {
        detect_ict_smt(
            futures_candles,
            spot_candles,
            20,
            normalized_for_inverse_correlation,
        )
    };
    let context_hints = derive_smt_context_hints(futures_candles);
    let resolver = resolve_smt_relationships(futures_symbol, None);
    let (cointegration_stat, cointegrated) =
        Cointegration::engle_granger(&futures_series, &spot_series);
    let narrative = if let Some(signal) = &ict_smt.smt_signal {
        format!("ict_{signal}_is_confirmation_only_wait_for_pda_and_mss_or_cisd")
    } else if let Some(reason) = &ict_smt.fail_closed_reason {
        format!("ict_smt_fail_closed_{reason}")
    } else if cointegrated && rolling_correlation_20.unwrap_or(0.0) > 0.6 {
        "paired_markets_are_aligned_and_statistically_supportive".to_string()
    } else if divergence_detected.unwrap_or(false) {
        "paired_markets_show_divergence_so_smt_confidence_is_reduced".to_string()
    } else {
        "paired_markets_offer_mixed_confirmation".to_string()
    };

    Ok(SmtCorrelationSection {
        probability_role: "cross_market_confirmation_for_probability_model".to_string(),
        paired_market_available: true,
        futures_symbol: Some(futures_symbol.to_string()),
        spot_symbol: Some(spot_symbol.to_string()),
        timeframe: context_hints.timeframe,
        session: context_hints.session,
        primary_related_symbols: resolver.primary_related_symbols,
        futures_peers: resolver.futures_peers,
        cfd_proxies: resolver.cfd_proxies,
        etf_proxies: resolver.etf_proxies,
        sector_or_industry_peers: resolver.sector_or_industry_peers,
        currency_macro_drivers: resolver.currency_macro_drivers,
        session_leaders: resolver.session_leaders,
        related_futures_symbols: asset_map.related_futures_symbols,
        related_etf_symbols: asset_map.related_etf_symbols,
        related_options_symbols: asset_map.related_options_symbols,
        related_cfd_symbols: asset_map.related_cfd_symbols,
        related_crypto_symbols: asset_map.related_crypto_symbols,
        rolling_correlation_20,
        rolling_correlation_50,
        divergence_detected,
        cointegration_stat: Some(cointegration_stat),
        cointegrated: Some(cointegrated),
        raw_basis_bps: auxiliary.raw_basis_bps,
        normalized_basis_bps: auxiliary.normalized_basis_bps,
        rolling_price_ratio_mean: auxiliary.rolling_price_ratio_mean,
        smt_signal: ict_smt.smt_signal,
        base_swing_type: ict_smt.base_swing_type,
        base_level: ict_smt.base_level,
        comparison_swing_type: ict_smt.comparison_swing_type,
        comparison_level: ict_smt.comparison_level,
        raw_comparison_swing_type: ict_smt.raw_comparison_swing_type,
        raw_comparison_level: ict_smt.raw_comparison_level,
        swept_side: ict_smt.swept_side,
        normalized_for_inverse_correlation,
        near_pd_array: context_hints.near_pd_array,
        pd_array_type: context_hints.pd_array_type,
        mss_or_cisd_confirmed: context_hints.mss_or_cisd_confirmed,
        displacement_confirmed: context_hints.displacement_confirmed,
        resolver_relationship_type: resolver.relationship_type,
        resolver_confidence: resolver.confidence,
        resolver_evidence_source: resolver.evidence_source,
        relationship_type,
        relationship_confidence,
        trade_use: "confirmation_only".to_string(),
        fail_closed_reason: ict_smt.fail_closed_reason,
        notes: auxiliary.notes.clone(),
        narrative,
    })
}

fn classify_relationship(corr20: Option<f64>, corr50: Option<f64>) -> (String, f64, bool) {
    let corr = corr20.or(corr50).unwrap_or(0.0);
    let confidence = corr.abs().min(1.0);
    if corr >= 0.3 {
        ("positive".to_string(), confidence, false)
    } else if corr <= -0.3 {
        ("negative".to_string(), confidence, true)
    } else {
        ("uncertain".to_string(), confidence, false)
    }
}

fn derive_smt_context_hints(candles: &[Candle]) -> SmtContextHints {
    let timeframe = infer_timeframe_label(candles);
    let session = candles.last().map(classify_session_label);
    let current_close = candles.last().map(|candle| candle.close);
    let atr = compute_atr(candles, 14);
    let latest_atr = atr.last().copied().filter(|value| *value > f64::EPSILON);
    let recent_mss = detect_market_structure_shifts_default(candles)
        .last()
        .map(|event| event.bar_index >= candles.len().saturating_sub(5))
        .unwrap_or(false);
    let order_blocks = detect_order_blocks(candles);
    let recent_cisd = has_recent_cisd(candles, &order_blocks, 5, 1);
    let displacement_confirmed = latest_atr.map(|atr_value| {
        detect_propulsion_blocks_default(candles, &atr)
            .last()
            .map(|block| {
                block.bar_index >= candles.len().saturating_sub(5)
                    && block.range_atr >= 1.5
                    && atr_value > f64::EPSILON
            })
            .unwrap_or(false)
    });
    let nearest_fvg = current_close.and_then(|price| {
        find_nearest_fvg(candles, price, Direction::Bull)
            .or_else(|| find_nearest_fvg(candles, price, Direction::Bear))
    });
    let near_fvg = match (nearest_fvg.as_ref(), current_close, latest_atr) {
        (Some(fvg), Some(price), Some(atr_value)) => {
            let midpoint = (fvg.top + fvg.bottom) / 2.0;
            (midpoint - price).abs() <= atr_value
        }
        _ => false,
    };
    let near_order_block = match (order_blocks.last(), current_close, latest_atr) {
        (Some(ob), Some(price), Some(atr_value)) => {
            let midpoint = (ob.high + ob.low) / 2.0;
            (midpoint - price).abs() <= atr_value
        }
        _ => false,
    };
    let (near_pd_array, pd_array_type) = if near_fvg {
        (Some(true), Some("FVG".to_string()))
    } else if near_order_block {
        (Some(true), Some("OB".to_string()))
    } else {
        (Some(false), Some("none".to_string()))
    };

    SmtContextHints {
        timeframe,
        session,
        near_pd_array,
        pd_array_type,
        mss_or_cisd_confirmed: Some(recent_mss || recent_cisd),
        displacement_confirmed,
    }
}

fn infer_timeframe_label(candles: &[Candle]) -> Option<String> {
    if candles.len() < 2 {
        return None;
    }
    let last = candles[candles.len() - 1].timestamp;
    let prev = candles[candles.len() - 2].timestamp;
    let minutes = last.signed_duration_since(prev).num_minutes().abs();
    match minutes {
        1 => Some("1m".to_string()),
        5 => Some("5m".to_string()),
        15 => Some("15m".to_string()),
        30 => Some("30m".to_string()),
        60 => Some("1h".to_string()),
        240 => Some("4h".to_string()),
        1440 => Some("1d".to_string()),
        0 => None,
        other => Some(format!("{other}m")),
    }
}

fn classify_session_label(candle: &Candle) -> String {
    let ny = candle.timestamp.with_timezone(&New_York);
    match ny.hour() {
        3..=7 => "london".to_string(),
        9 if ny.minute() >= 30 => "ny_open".to_string(),
        10 => "ny_open".to_string(),
        11..=13 => "ny_mid".to_string(),
        20..=23 | 0..=2 => "asia".to_string(),
        _ => "dead_zone".to_string(),
    }
}

fn detect_ict_smt(
    base_candles: &[Candle],
    comparison_candles: &[Candle],
    lookback: usize,
    normalize_comparison_for_inverse: bool,
) -> IctSmtSnapshot {
    let len = base_candles.len().min(comparison_candles.len());
    if len < 3 {
        return IctSmtSnapshot {
            smt_signal: None,
            base_swing_type: None,
            base_level: None,
            comparison_swing_type: None,
            comparison_level: None,
            raw_comparison_swing_type: None,
            raw_comparison_level: None,
            swept_side: None,
            fail_closed_reason: Some("insufficient_paired_candles".to_string()),
        };
    }

    let start = len.saturating_sub(lookback + 1);
    let base_window = &base_candles[start..len - 1];
    let comparison_window = &comparison_candles[start..len - 1];
    let Some(base_last) = base_candles.get(len - 1) else {
        return empty_ict_smt("insufficient_paired_candles");
    };
    let Some(comparison_last) = comparison_candles.get(len - 1) else {
        return empty_ict_smt("insufficient_paired_candles");
    };
    if base_window.is_empty() || comparison_window.is_empty() {
        return empty_ict_smt("insufficient_paired_candles");
    }

    let base_prev_high = base_window
        .iter()
        .map(|candle| candle.high)
        .fold(f64::NEG_INFINITY, f64::max);
    let base_prev_low = base_window
        .iter()
        .map(|candle| candle.low)
        .fold(f64::INFINITY, f64::min);
    let comparison_prev_high = comparison_window
        .iter()
        .map(|candle| normalized_high(candle, normalize_comparison_for_inverse))
        .fold(f64::NEG_INFINITY, f64::max);
    let comparison_prev_low = comparison_window
        .iter()
        .map(|candle| normalized_low(candle, normalize_comparison_for_inverse))
        .fold(f64::INFINITY, f64::min);

    let base_hh = base_last.high > base_prev_high;
    let base_ll = base_last.low < base_prev_low;
    let comparison_hh =
        normalized_high(comparison_last, normalize_comparison_for_inverse) > comparison_prev_high;
    let comparison_ll =
        normalized_low(comparison_last, normalize_comparison_for_inverse) < comparison_prev_low;

    if base_hh && !comparison_hh {
        IctSmtSnapshot {
            smt_signal: Some("bearish_smt".to_string()),
            base_swing_type: Some("HH_sweep".to_string()),
            base_level: Some(base_last.high),
            comparison_swing_type: Some("failed_HH".to_string()),
            comparison_level: Some(comparison_failure_high_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            raw_comparison_swing_type: Some(
                raw_swing_label("failed_HH", normalize_comparison_for_inverse).to_string(),
            ),
            raw_comparison_level: Some(comparison_failure_high_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            swept_side: Some("buy_side_liquidity".to_string()),
            fail_closed_reason: None,
        }
    } else if comparison_hh && !base_hh {
        IctSmtSnapshot {
            smt_signal: Some("bearish_smt".to_string()),
            base_swing_type: Some("failed_HH".to_string()),
            base_level: Some(base_last.high),
            comparison_swing_type: Some("HH_sweep".to_string()),
            comparison_level: Some(comparison_sweep_high_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            raw_comparison_swing_type: Some(
                raw_swing_label("HH_sweep", normalize_comparison_for_inverse).to_string(),
            ),
            raw_comparison_level: Some(comparison_sweep_high_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            swept_side: Some("buy_side_liquidity".to_string()),
            fail_closed_reason: None,
        }
    } else if base_ll && !comparison_ll {
        IctSmtSnapshot {
            smt_signal: Some("bullish_smt".to_string()),
            base_swing_type: Some("LL_sweep".to_string()),
            base_level: Some(base_last.low),
            comparison_swing_type: Some("failed_LL".to_string()),
            comparison_level: Some(comparison_failure_low_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            raw_comparison_swing_type: Some(
                raw_swing_label("failed_LL", normalize_comparison_for_inverse).to_string(),
            ),
            raw_comparison_level: Some(comparison_failure_low_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            swept_side: Some("sell_side_liquidity".to_string()),
            fail_closed_reason: None,
        }
    } else if comparison_ll && !base_ll {
        IctSmtSnapshot {
            smt_signal: Some("bullish_smt".to_string()),
            base_swing_type: Some("failed_LL".to_string()),
            base_level: Some(base_last.low),
            comparison_swing_type: Some("LL_sweep".to_string()),
            comparison_level: Some(comparison_sweep_low_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            raw_comparison_swing_type: Some(
                raw_swing_label("LL_sweep", normalize_comparison_for_inverse).to_string(),
            ),
            raw_comparison_level: Some(comparison_sweep_low_level(
                comparison_last,
                normalize_comparison_for_inverse,
            )),
            swept_side: Some("sell_side_liquidity".to_string()),
            fail_closed_reason: None,
        }
    } else {
        IctSmtSnapshot {
            smt_signal: None,
            base_swing_type: None,
            base_level: None,
            comparison_swing_type: None,
            comparison_level: None,
            raw_comparison_swing_type: None,
            raw_comparison_level: None,
            swept_side: None,
            fail_closed_reason: Some("no_swing_confirmation_failure".to_string()),
        }
    }
}

fn empty_ict_smt(reason: &str) -> IctSmtSnapshot {
    IctSmtSnapshot {
        smt_signal: None,
        base_swing_type: None,
        base_level: None,
        comparison_swing_type: None,
        comparison_level: None,
        raw_comparison_swing_type: None,
        raw_comparison_level: None,
        swept_side: None,
        fail_closed_reason: Some(reason.to_string()),
    }
}

fn normalized_high(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        -candle.low
    } else {
        candle.high
    }
}

fn normalized_low(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        -candle.high
    } else {
        candle.low
    }
}

fn raw_swing_label(normalized_label: &str, inverse: bool) -> &'static str {
    match (normalized_label, inverse) {
        ("HH_sweep", true) => "LL_sweep",
        ("failed_HH", true) => "failed_LL",
        ("LL_sweep", true) => "HH_sweep",
        ("failed_LL", true) => "failed_HH",
        ("HH_sweep", false) => "HH_sweep",
        ("failed_HH", false) => "failed_HH",
        ("LL_sweep", false) => "LL_sweep",
        ("failed_LL", false) => "failed_LL",
        _ => "unknown",
    }
}

fn comparison_sweep_high_level(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        candle.low
    } else {
        candle.high
    }
}

fn comparison_failure_high_level(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        candle.low
    } else {
        candle.high
    }
}

fn comparison_sweep_low_level(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        candle.high
    } else {
        candle.low
    }
}

fn comparison_failure_low_level(candle: &Candle, inverse: bool) -> f64 {
    if inverse {
        candle.high
    } else {
        candle.low
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data::realtime::market_support::SpotInstrumentKind;
    use chrono::{Duration, TimeZone, Utc};

    fn candle(index: i64, high: f64, low: f64, close: f64) -> Candle {
        Candle {
            timestamp: Utc.with_ymd_and_hms(2026, 5, 12, 13, 30, 0).unwrap()
                + Duration::minutes(index),
            open: close,
            high,
            low,
            close,
            volume: 1000.0,
        }
    }

    fn auxiliary() -> AuxiliaryMarketEvidence {
        AuxiliaryMarketEvidence {
            spot_symbol: "ES".to_string(),
            options_symbol: "SPY".to_string(),
            spot_kind: SpotInstrumentKind::Index,
            spot_last_close: None,
            futures_last_close: None,
            spot_return: None,
            futures_return: None,
            raw_basis_bps: None,
            normalized_basis_bps: None,
            rolling_price_ratio_mean: None,
            put_call_oi_ratio: None,
            put_call_volume_ratio: None,
            near_atm_implied_volatility: None,
            near_atm_delta: None,
            near_atm_gamma: None,
            near_atm_vega: None,
            call_gamma_oi: None,
            put_gamma_oi: None,
            gamma_skew: None,
            hedge_pressure_direction: None,
            hedge_pressure_score: None,
            long_bias: 0.0,
            short_bias: 0.0,
            uncertainty_penalty: 0.0,
            notes: Vec::new(),
        }
    }

    #[test]
    fn ict_smt_bearish_requires_higher_high_sweep_without_pair_confirmation() {
        let mut base = Vec::new();
        let mut pair = Vec::new();
        for index in 0..24 {
            base.push(candle(index, 100.0 + index as f64 * 0.1, 95.0, 99.0));
            pair.push(candle(index, 200.0 + index as f64 * 0.1, 195.0, 199.0));
        }
        base.push(candle(24, 106.75, 96.0, 105.5));
        pair.push(candle(24, 201.20, 196.0, 200.4));

        let section = build_smt_correlation_section("NQ", "ES", &base, &pair, &auxiliary())
            .expect("smt section");

        assert_eq!(section.smt_signal.as_deref(), Some("bearish_smt"));
        assert_eq!(section.base_swing_type.as_deref(), Some("HH_sweep"));
        assert_eq!(section.base_level, Some(106.75));
        assert_eq!(section.comparison_swing_type.as_deref(), Some("failed_HH"));
        assert_eq!(section.comparison_level, Some(201.2));
        assert_eq!(
            section.raw_comparison_swing_type.as_deref(),
            Some("failed_HH")
        );
        assert_eq!(section.raw_comparison_level, Some(201.2));
        assert_eq!(section.swept_side.as_deref(), Some("buy_side_liquidity"));
        assert_eq!(section.timeframe.as_deref(), Some("1m"));
        assert_eq!(section.session.as_deref(), Some("ny_open"));
        assert!(section.near_pd_array.is_some());
        assert!(section.pd_array_type.is_some());
        assert!(section.mss_or_cisd_confirmed.is_some());
        assert!(section.displacement_confirmed.is_some());
        assert!(section.primary_related_symbols.contains(&"ES".to_string()));
        assert!(section.futures_peers.contains(&"YM".to_string()));
        assert!(section.etf_proxies.contains(&"QQQ".to_string()));
        assert!(section.currency_macro_drivers.contains(&"DXY".to_string()));
        assert!(section.session_leaders.contains(&"ES".to_string()));
        assert_eq!(section.resolver_relationship_type, "index_peer");
        assert!(section.resolver_confidence >= 0.80);
        assert_eq!(
            section.resolver_evidence_source,
            "builtin_symbol_relationship_seed"
        );
        assert_eq!(section.trade_use, "confirmation_only");
    }

    #[test]
    fn ict_smt_bullish_requires_lower_low_sweep_without_pair_confirmation() {
        let mut base = Vec::new();
        let mut pair = Vec::new();
        for index in 0..24 {
            base.push(candle(index, 105.0, 100.0 - index as f64 * 0.1, 101.0));
            pair.push(candle(index, 205.0, 200.0 - index as f64 * 0.1, 201.0));
        }
        base.push(candle(24, 103.0, 96.25, 97.0));
        pair.push(candle(24, 203.0, 197.85, 199.0));

        let section = build_smt_correlation_section("NQ", "ES", &base, &pair, &auxiliary())
            .expect("smt section");

        assert_eq!(section.smt_signal.as_deref(), Some("bullish_smt"));
        assert_eq!(section.base_swing_type.as_deref(), Some("LL_sweep"));
        assert_eq!(section.base_level, Some(96.25));
        assert_eq!(section.comparison_swing_type.as_deref(), Some("failed_LL"));
        assert_eq!(section.comparison_level, Some(197.85));
        assert_eq!(
            section.raw_comparison_swing_type.as_deref(),
            Some("failed_LL")
        );
        assert_eq!(section.raw_comparison_level, Some(197.85));
        assert_eq!(section.swept_side.as_deref(), Some("sell_side_liquidity"));
        assert_eq!(section.trade_use, "confirmation_only");
    }

    #[test]
    fn ict_smt_inverse_relationship_normalizes_comparison_structure() {
        let mut base = Vec::new();
        let mut inverse_pair = Vec::new();
        for index in 0..24 {
            base.push(candle(index, 100.0 + index as f64 * 0.1, 95.0, 99.0));
            inverse_pair.push(candle(index, 205.0, 200.0 - index as f64 * 0.1, 201.0));
        }
        base.push(candle(24, 106.75, 96.0, 105.5));
        inverse_pair.push(candle(24, 203.0, 197.85, 199.0));

        let snapshot = detect_ict_smt(&base, &inverse_pair, 20, true);

        assert_eq!(snapshot.smt_signal.as_deref(), Some("bearish_smt"));
        assert_eq!(snapshot.base_swing_type.as_deref(), Some("HH_sweep"));
        assert_eq!(snapshot.base_level, Some(106.75));
        assert_eq!(snapshot.comparison_swing_type.as_deref(), Some("failed_HH"));
        assert_eq!(snapshot.comparison_level, Some(197.85));
        assert_eq!(
            snapshot.raw_comparison_swing_type.as_deref(),
            Some("failed_LL")
        );
        assert_eq!(snapshot.raw_comparison_level, Some(197.85));
        assert_eq!(snapshot.swept_side.as_deref(), Some("buy_side_liquidity"));
    }

    #[test]
    fn smt_relationship_resolver_keeps_crypto_macro_driver() {
        let map = correlation_asset_map("BTC", "BTC", "IBIT");

        assert!(map.related_crypto_symbols.contains(&"ETH".to_string()));
        assert!(map.related_crypto_symbols.contains(&"SOL".to_string()));
        assert!(map.related_futures_symbols.contains(&"DXY".to_string()));
        assert!(map.related_etf_symbols.contains(&"QQQ".to_string()));
    }

    #[test]
    fn smt_relationship_resolver_filters_by_provider_universe() {
        let available = vec![
            "ETH".to_string(),
            "DXY".to_string(),
            "QQQ".to_string(),
            "SPY".to_string(),
        ];
        let map = correlation_asset_map_with_available("BTC", "BTC", "IBIT", Some(&available));

        assert_eq!(map.related_crypto_symbols, vec!["ETH".to_string()]);
        assert_eq!(map.related_futures_symbols, vec!["DXY".to_string()]);
        assert_eq!(map.related_etf_symbols, vec!["QQQ".to_string()]);
    }

    #[test]
    fn smt_relationship_resolver_adds_equity_index_sector_and_options_proxies() {
        let available = vec![
            "SPY".to_string(),
            "QQQ".to_string(),
            "XLK".to_string(),
            "DXY".to_string(),
            "VIX".to_string(),
        ];
        let map = correlation_asset_map_with_available("AAPL", "AAPL", "AAPL", Some(&available));

        assert_eq!(map.related_etf_symbols, vec!["QQQ", "SPY", "XLK"]);
        assert_eq!(map.related_futures_symbols, vec!["DXY", "VIX"]);
        assert_eq!(map.related_options_symbols, vec!["AAPL".to_string()]);
    }

    #[test]
    fn smt_relationship_resolver_emits_first_class_schema_for_index_fx_metals_crypto() {
        let nq = resolve_smt_relationships("NQ", None);
        assert_eq!(nq.symbol, "NQ");
        assert!(nq.primary_related_symbols.contains(&"ES".to_string()));
        assert!(nq.futures_peers.contains(&"YM".to_string()));
        assert!(nq.cfd_proxies.contains(&"NAS100".to_string()));
        assert!(nq.etf_proxies.contains(&"QQQ".to_string()));
        assert!(nq.currency_macro_drivers.contains(&"DXY".to_string()));
        assert!(nq.session_leaders.contains(&"ES".to_string()));
        assert_eq!(nq.relationship_type, "index_peer");
        assert!(nq.confidence >= 0.80);
        assert_eq!(nq.evidence_source, "builtin_symbol_relationship_seed");

        let eur = resolve_smt_relationships("EURUSD", None);
        assert!(eur.primary_related_symbols.contains(&"GBPUSD".to_string()));
        assert!(eur.currency_macro_drivers.contains(&"DXY".to_string()));
        assert_eq!(eur.relationship_type, "currency_driver");

        let xau = resolve_smt_relationships("XAUUSD", None);
        assert!(xau.primary_related_symbols.contains(&"XAGUSD".to_string()));
        assert!(xau
            .currency_macro_drivers
            .contains(&"real_yield".to_string()));
        assert!(xau.etf_proxies.contains(&"GDX".to_string()));
        assert_eq!(xau.relationship_type, "commodity_pair");

        let btc = resolve_smt_relationships("BTC", None);
        assert!(btc.primary_related_symbols.contains(&"ETH".to_string()));
        assert!(btc.currency_macro_drivers.contains(&"DXY".to_string()));
        assert!(btc.etf_proxies.contains(&"QQQ".to_string()));
        assert_eq!(btc.relationship_type, "crypto_beta");
    }

    #[test]
    fn smt_relationship_resolver_filters_by_available_universe_without_inventing_symbols() {
        let available = vec!["ES".to_string(), "QQQ".to_string(), "DXY".to_string()];
        let resolved = resolve_smt_relationships("NQ", Some(&available));

        assert_eq!(resolved.primary_related_symbols, vec!["ES".to_string()]);
        assert_eq!(
            resolved.futures_peers,
            vec!["DXY".to_string(), "ES".to_string()]
        );
        assert_eq!(resolved.etf_proxies, vec!["QQQ".to_string()]);
        assert!(resolved.cfd_proxies.is_empty());
        assert!(resolved.session_leaders.contains(&"ES".to_string()));
    }
}
