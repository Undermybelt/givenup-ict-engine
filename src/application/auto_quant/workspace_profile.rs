use anyhow::{bail, Context, Result};
use csv::Writer;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};

use crate::data::load_candles;

use super::handoff::{AutoQuantResearchHandoffPayload, AutoQuantWorkspaceConfig};

pub const AUTO_QUANT_WORKSPACE_PROFILE_FILE: &str = "auto_quant_workspace_profile.json";
pub const AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV: &str = "synthetic_ohlcv";
pub const AUTO_QUANT_PROFILE_MANAGED: &str = "managed";

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct AutoQuantWorkspaceProfileConfig {
    pub profile: String,
    pub symbol: String,
    pub source_data_path: String,
    pub pair: String,
    pub base_timeframe: String,
    pub additional_timeframes: Vec<String>,
    pub notes: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct ProfileSourceCsvSummary {
    timerange: String,
}

pub fn load_workspace_profile(state_dir: &str) -> Result<Option<AutoQuantWorkspaceProfileConfig>> {
    let path = workspace_profile_path(state_dir);
    if !path.exists() {
        return Ok(None);
    }
    let raw = fs::read_to_string(&path).with_context(|| format!("reading {}", path.display()))?;
    let profile =
        serde_json::from_str(&raw).with_context(|| format!("parsing {}", path.display()))?;
    Ok(Some(profile))
}

pub fn persist_workspace_profile_selection(
    state_dir: &str,
    profile_name: Option<&str>,
    symbol: &str,
    source_data_path: &str,
) -> Result<Option<AutoQuantWorkspaceProfileConfig>> {
    match profile_name
        .map(str::trim)
        .filter(|value| !value.is_empty())
    {
        None => load_workspace_profile(state_dir),
        Some(value)
            if value.eq_ignore_ascii_case(AUTO_QUANT_PROFILE_MANAGED)
                || value.eq_ignore_ascii_case("default") =>
        {
            clear_workspace_profile(state_dir)?;
            Ok(None)
        }
        Some(value) if value.eq_ignore_ascii_case(AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV) => {
            let inferred = infer_pair_and_timeframe_from_source_path(source_data_path, symbol)
                .unwrap_or_else(|| (synthetic_ohlcv_pair_alias(symbol), "1h".to_string()));
            let profile = AutoQuantWorkspaceProfileConfig {
                profile: AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV.to_string(),
                symbol: symbol.to_string(),
                source_data_path: source_data_path.to_string(),
                pair: inferred.0,
                base_timeframe: inferred.1.clone(),
                additional_timeframes: handoff_additional_timeframes(&inferred.1),
                notes: vec![
                    "profile_materializes_additive_external_runner".to_string(),
                    "profile_reuses_primary_cleaned_candle_json_as_prepare_external_source"
                        .to_string(),
                    "profile_is_opt_in_and_state_dir_scoped".to_string(),
                ],
            };
            save_workspace_profile(state_dir, &profile)?;
            Ok(Some(profile))
        }
        Some(value) => bail!("unknown auto-quant profile '{}'", value),
    }
}

pub fn apply_workspace_profile(
    state_dir: &str,
    workspace: &mut AutoQuantWorkspaceConfig,
) -> Result<Option<AutoQuantWorkspaceProfileConfig>> {
    let Some(profile) = load_workspace_profile(state_dir)? else {
        return Ok(None);
    };
    if profile.profile == AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV {
        apply_synthetic_profile_to_workspace(&profile, workspace);
    }
    Ok(Some(profile))
}

pub fn apply_handoff_workspace_profile(
    payload: &AutoQuantResearchHandoffPayload,
    workspace: &mut AutoQuantWorkspaceConfig,
) -> Option<AutoQuantWorkspaceProfileConfig> {
    let profile = handoff_workspace_profile(payload)?;
    apply_synthetic_profile_to_workspace(&profile, workspace);
    Some(profile)
}

pub fn materialize_handoff_workspace_profile(
    payload: &AutoQuantResearchHandoffPayload,
    workspace: &AutoQuantWorkspaceConfig,
) -> Result<Option<AutoQuantWorkspaceProfileConfig>> {
    let Some(profile) = handoff_workspace_profile(payload) else {
        return Ok(None);
    };
    materialize_synthetic_workspace_profile(&profile, workspace)?;
    Ok(Some(profile))
}

pub fn materialize_workspace_profile(
    state_dir: &str,
    workspace: &AutoQuantWorkspaceConfig,
) -> Result<Option<AutoQuantWorkspaceProfileConfig>> {
    let Some(profile) = load_workspace_profile(state_dir)? else {
        return Ok(None);
    };
    if profile.profile != AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV {
        return Ok(Some(profile));
    }
    materialize_synthetic_workspace_profile(&profile, workspace)?;
    Ok(Some(profile))
}

fn apply_synthetic_profile_to_workspace(
    profile: &AutoQuantWorkspaceProfileConfig,
    workspace: &mut AutoQuantWorkspaceConfig,
) {
    let repo_root = PathBuf::from(&workspace.repo_root);
    workspace.profile_name = Some(profile.profile.clone());
    workspace.prepare_script = repo_root
        .join("prepare_external.py")
        .to_string_lossy()
        .to_string();
    workspace.run_script = repo_root.join("run_tomac.py").to_string_lossy().to_string();
    workspace.config_json = repo_root
        .join("config.tomac.json")
        .to_string_lossy()
        .to_string();
    workspace.strategies_dir = repo_root
        .join("user_data/strategies_external")
        .to_string_lossy()
        .to_string();
    workspace.expected_data_files = expected_data_files(profile);
    workspace.strategy_seed_source_dir = (!synthetic_profile_requires_exact_seed(&profile.symbol))
        .then(|| {
            repo_root
                .join("user_data/strategies")
                .to_string_lossy()
                .to_string()
        });
}

fn materialize_synthetic_workspace_profile(
    profile: &AutoQuantWorkspaceProfileConfig,
    workspace: &AutoQuantWorkspaceConfig,
) -> Result<()> {
    let workspace_root = PathBuf::from(&workspace.repo_root);
    fs::create_dir_all(workspace_root.join("user_data/strategies_external"))?;
    fs::create_dir_all(workspace_root.join("user_data/data"))?;

    let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    fs::copy(
        repo_root.join("support/scripts/auto_quant_external/run_tomac.py"),
        workspace_root.join("run_tomac.py"),
    )?;
    fs::copy(
        repo_root.join("support/scripts/auto_quant_external/prepare_external.py"),
        workspace_root.join("prepare_external.py"),
    )?;
    fs::copy(
        repo_root.join("support/scripts/auto_quant_external/config.tomac.json"),
        workspace_root.join("config.tomac.json"),
    )?;
    let source_summary = write_profile_source_csv(
        &profile.source_data_path,
        &workspace_root.join("profile_source.csv"),
    )?;
    write_profile_config(
        &workspace_root.join("config.tomac.json"),
        profile,
        &source_summary.timerange,
    )?;
    seed_profile_strategies(
        workspace
            .strategy_seed_source_dir
            .as_deref()
            .map(Path::new)
            .unwrap_or_else(|| Path::new(&workspace.strategies_dir)),
        &workspace_root.join("user_data/strategies_external"),
        &repo_root
            .join("support/scripts/auto_quant_external/strategies/TomacNQ_KillzoneBreakout.py"),
        &profile.symbol,
    )?;
    Ok(())
}

fn handoff_workspace_profile(
    payload: &AutoQuantResearchHandoffPayload,
) -> Option<AutoQuantWorkspaceProfileConfig> {
    let data_path = payload.data_path.trim();
    if data_path.is_empty() || !Path::new(data_path).exists() {
        return None;
    }
    let (pair, base_timeframe) =
        infer_pair_and_timeframe_from_source_path(data_path, &payload.symbol)?;
    Some(AutoQuantWorkspaceProfileConfig {
        profile: AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV.to_string(),
        symbol: payload.symbol.clone(),
        source_data_path: data_path.to_string(),
        pair,
        additional_timeframes: handoff_additional_timeframes(&base_timeframe),
        base_timeframe,
        notes: vec![
            "profile_materializes_exact_auto_quant_handoff_data".to_string(),
            format!("handoff_artifact_id={}", payload.artifact_id),
        ],
    })
}

fn infer_pair_and_timeframe_from_source_path(
    data_path: &str,
    symbol: &str,
) -> Option<(String, String)> {
    let stem = Path::new(data_path).file_stem()?.to_str()?;
    let tokens = stem
        .split(|ch: char| !ch.is_ascii_alphanumeric())
        .filter(|token| !token.is_empty())
        .collect::<Vec<_>>();
    let (timeframe_index, timeframe) = tokens
        .iter()
        .enumerate()
        .rev()
        .find_map(|(index, token)| normalize_timeframe_token(token).map(|tf| (index, tf)))?;
    let base = tokens[..timeframe_index]
        .iter()
        .rev()
        .find_map(|token| normalize_symbol_token(token))
        .unwrap_or_else(|| synthetic_ohlcv_alias_base_from_symbol(symbol));
    Some((format!("{base}/USD"), timeframe))
}

fn handoff_additional_timeframes(base_timeframe: &str) -> Vec<String> {
    let timeframes: &[&str] = match base_timeframe {
        "1m" => &["5m", "15m", "30m", "1h", "4h", "1d"],
        "5m" => &["15m", "30m", "1h", "4h", "1d"],
        "15m" => &["30m", "1h", "4h", "1d"],
        "30m" => &["1h", "4h", "1d"],
        "1h" => &["4h", "1d"],
        "4h" => &["1d"],
        _ => &[],
    };
    timeframes
        .iter()
        .map(|timeframe| (*timeframe).to_string())
        .collect()
}

fn normalize_timeframe_token(token: &str) -> Option<String> {
    let lower = token.to_ascii_lowercase();
    matches!(
        lower.as_str(),
        "1m" | "3m" | "5m" | "15m" | "30m" | "1h" | "4h" | "1d"
    )
    .then_some(lower)
}

fn normalize_symbol_token(token: &str) -> Option<String> {
    let upper = token.to_ascii_uppercase();
    const SKIP: &[&str] = &["IBKR", "YF", "TVR", "KRAKEN", "BINANCE", "BYBIT"];
    if SKIP.contains(&upper.as_str()) || upper.chars().all(|ch| ch.is_ascii_digit()) {
        return None;
    }
    Some(upper)
}

fn workspace_profile_path(state_dir: &str) -> PathBuf {
    PathBuf::from(state_dir).join(AUTO_QUANT_WORKSPACE_PROFILE_FILE)
}

fn save_workspace_profile(
    state_dir: &str,
    profile: &AutoQuantWorkspaceProfileConfig,
) -> Result<()> {
    let path = workspace_profile_path(state_dir);
    fs::write(&path, serde_json::to_string_pretty(profile)?)
        .with_context(|| format!("writing {}", path.display()))
}

fn clear_workspace_profile(state_dir: &str) -> Result<()> {
    let path = workspace_profile_path(state_dir);
    if path.exists() {
        fs::remove_file(&path).with_context(|| format!("removing {}", path.display()))?;
    }
    Ok(())
}

fn expected_data_files(profile: &AutoQuantWorkspaceProfileConfig) -> Vec<String> {
    std::iter::once(profile.base_timeframe.clone())
        .chain(profile.additional_timeframes.clone())
        .map(|timeframe| format!("{}-{timeframe}.feather", profile.pair.replace('/', "_")))
        .collect()
}

fn synthetic_ohlcv_pair_alias(symbol: &str) -> String {
    let trimmed = symbol.trim();
    let base = trimmed
        .split_once("_EXT_")
        .map(|(head, _)| head)
        .unwrap_or(trimmed)
        .trim_end_matches("_EXT")
        .trim();
    let alias_base = synthetic_ohlcv_alias_base_from_symbol(base);
    format!("{alias_base}/USD")
}

fn synthetic_ohlcv_alias_base_from_symbol(symbol: &str) -> String {
    if !symbol.contains('_') {
        return symbol.to_string();
    }
    const STOPWORDS: &[&str] = &[
        "IBKR",
        "FUTURES",
        "YF",
        "TVR",
        "KRAKEN",
        "BINANCE",
        "BYBIT",
        "PAXOS",
        "PF",
        "EXT",
        "SYNTH",
        "CONFORMAL",
        "SMOKE",
        "LOCAL",
        "NONBTC",
        "MTF",
        "LTF",
        "HTF",
        "USD",
        "CURRENT",
        "PROFILE",
        "STATE",
        "WINDOW",
        "EARLY",
        "LATE",
        "CHAIN",
        "MKTSTRUCT",
        "B2R",
    ];
    const TIMEFRAME_TOKENS: &[&str] = &["1M", "5M", "15M", "30M", "1H", "4H", "1D"];

    let candidate = symbol
        .split('_')
        .map(str::trim)
        .filter(|token| !token.is_empty())
        .find(|token| {
            let upper = token.to_ascii_uppercase();
            !STOPWORDS.contains(&upper.as_str())
                && !TIMEFRAME_TOKENS.contains(&upper.as_str())
                && !upper.chars().all(|ch| ch.is_ascii_digit())
        });

    candidate
        .map(strip_runtime_timeframe_suffix)
        .unwrap_or_else(|| symbol.to_string())
}

fn strip_runtime_timeframe_suffix(token: &str) -> String {
    const SUFFIXES: &[&str] = &["15M", "30M", "1M", "5M", "1H", "4H", "1D"];
    let upper = token.to_ascii_uppercase();
    for suffix in SUFFIXES {
        if upper.ends_with(suffix) && token.len() > suffix.len() {
            return token[..token.len() - suffix.len()].to_string();
        }
    }
    token.to_string()
}

fn write_profile_config(
    path: &Path,
    profile: &AutoQuantWorkspaceProfileConfig,
    timerange: &str,
) -> Result<()> {
    let mut config: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(path)?).context("parsing config.tomac.json")?;
    config["timeframe"] = serde_json::Value::String(profile.base_timeframe.clone());
    config["exchange"]["pair_whitelist"] = serde_json::json!([profile.pair.clone()]);
    config["trading_mode"] = serde_json::Value::String("spot".to_string());
    config["timerange"] = serde_json::Value::String(timerange.to_string());
    config
        .as_object_mut()
        .map(|root| root.remove("margin_mode"));
    config["entry_pricing"]["use_order_book"] = serde_json::Value::Bool(false);
    config["exit_pricing"]["use_order_book"] = serde_json::Value::Bool(false);
    if let Some(exchange) = config["exchange"].as_object_mut() {
        exchange.remove("_ft_has_params");
    }
    fs::write(path, serde_json::to_string_pretty(&config)?)?;
    Ok(())
}

fn write_profile_source_csv(input_path: &str, csv_path: &Path) -> Result<ProfileSourceCsvSummary> {
    let candles = load_candles(input_path)?;
    let timerange = source_candle_timerange(&candles)?;
    let mut writer = Writer::from_path(csv_path)?;
    writer.write_record(["date", "open", "high", "low", "close", "volume"])?;
    for candle in candles {
        writer.write_record([
            candle.timestamp.to_rfc3339(),
            candle.open.to_string(),
            candle.high.to_string(),
            candle.low.to_string(),
            candle.close.to_string(),
            candle.volume.to_string(),
        ])?;
    }
    writer.flush()?;
    Ok(ProfileSourceCsvSummary { timerange })
}

fn source_candle_timerange(candles: &[crate::types::Candle]) -> Result<String> {
    let first = candles
        .first()
        .context("synthetic_ohlcv source candle set is empty")?;
    let last = candles
        .last()
        .context("synthetic_ohlcv source candle set is empty")?;
    Ok(format!(
        "{}-{}",
        first.timestamp.format("%Y%m%d"),
        last.timestamp.format("%Y%m%d")
    ))
}

fn seed_profile_strategies(
    source_dir: &Path,
    target_dir: &Path,
    fallback_strategy_path: &Path,
    profile_symbol: &str,
) -> Result<()> {
    fs::create_dir_all(target_dir)?;
    for entry in fs::read_dir(target_dir)? {
        let entry = entry?;
        let path = entry.path();
        let is_python = path
            .extension()
            .and_then(|ext| ext.to_str())
            .map(|ext| ext.eq_ignore_ascii_case("py"))
            .unwrap_or(false);
        if is_python {
            fs::remove_file(path)?;
        }
    }
    let mut copied = 0usize;
    if source_dir.exists() {
        for entry in fs::read_dir(source_dir)? {
            let entry = entry?;
            let path = entry.path();
            let is_python = path
                .extension()
                .and_then(|ext| ext.to_str())
                .map(|ext| ext.eq_ignore_ascii_case("py"))
                .unwrap_or(false);
            let is_active = entry
                .file_name()
                .to_str()
                .map(|name| !name.starts_with('_'))
                .unwrap_or(false);
            if is_python && is_active {
                let source = fs::read_to_string(&path)
                    .with_context(|| format!("reading strategy source {}", path.display()))?;
                if strategy_source_compatible_with_profile(&path, &source, profile_symbol) {
                    write_strategy_with_meta_source(
                        &source,
                        &target_dir.join(entry.file_name()),
                        profile_symbol,
                    )?;
                    copied += 1;
                }
            }
        }
    }
    if copied == 0 {
        let fallback_source = fs::read_to_string(fallback_strategy_path).with_context(|| {
            format!(
                "reading fallback strategy source {}",
                fallback_strategy_path.display()
            )
        })?;
        if !strategy_source_compatible_with_profile(
            fallback_strategy_path,
            &fallback_source,
            profile_symbol,
        ) {
            return Ok(());
        }
        let filename = fallback_strategy_path
            .file_name()
            .context("missing fallback strategy filename")?;
        write_strategy_with_meta_source(
            &fallback_source,
            &target_dir.join(filename),
            profile_symbol,
        )?;
    }
    Ok(())
}

fn write_strategy_with_meta_source(
    source: &str,
    target_path: &Path,
    profile_symbol: &str,
) -> Result<()> {
    let rendered = if source.contains("# AUTO_QUANT_META") {
        source.to_string()
    } else {
        let strategy = target_path
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or("SyntheticProfileStrategy");
        let base_factor = camel_to_snake(strategy);
        let hypothesis = sanitize_auto_quant_meta_value(
            &extract_doc_field(source, "Hypothesis")
                .unwrap_or_else(|| format!("{strategy} hypothesis under synthetic_ohlcv profile.")),
        );
        let paradigm = sanitize_auto_quant_meta_value(
            &extract_doc_field(source, "Paradigm").unwrap_or_else(|| "other".to_string()),
        );
        let parent = sanitize_auto_quant_meta_value(
            &extract_doc_field(source, "Parent").unwrap_or_else(|| "root".to_string()),
        );
        let status = sanitize_auto_quant_meta_value(
            &extract_doc_field(source, "Status").unwrap_or_else(|| "active".to_string()),
        );
        let created = sanitize_auto_quant_meta_value(
            &extract_doc_field(source, "Created").unwrap_or_default(),
        );
        let expected_regime =
            if source.contains("@informative(\"1d\")") || source.contains("@informative(\"4h\")") {
                "multi_timeframe_intraday_resonance"
            } else {
                "single_timeframe_intraday"
            };
        let asset_class = match profile_symbol {
            "NQ" | "ES" | "YM" => "futures_index",
            "GC" | "CL" => "futures_commodity",
            _ => "synthetic_ohlcv",
        };
        let meta_block = format!(
            "# AUTO_QUANT_META v1\nStrategy:        {strategy}\nMutation_id:     synthetic-ohlcv-{strategy}\nBase_factor:     {base_factor}\nHypothesis:      {hypothesis}\nParadigm:        {paradigm}\nExpected_regime: {expected_regime}\nFactors_used:    {base_factor}\nParent:          {parent}\nAsset_class:     {asset_class}\nStatus:          {status}\nCreated:         {created}\n# END_AUTO_QUANT_META"
        );
        inject_auto_quant_meta_into_docstring(source, &meta_block)
    };
    fs::write(target_path, rendered)
        .with_context(|| format!("writing exportable strategy {}", target_path.display()))
}

fn strategy_source_compatible_with_profile(
    source_path: &Path,
    source: &str,
    profile_symbol: &str,
) -> bool {
    if !synthetic_profile_requires_exact_seed(profile_symbol) {
        return true;
    }
    let exact = profile_symbol.to_ascii_uppercase();
    let base = synthetic_ohlcv_alias_base_from_symbol(profile_symbol).to_ascii_uppercase();
    let haystack = format!(
        "{}\n{}",
        source_path
            .file_stem()
            .and_then(|value| value.to_str())
            .unwrap_or_default(),
        source
    )
    .to_ascii_uppercase();
    haystack.contains(&exact) || (!base.is_empty() && haystack.contains(&base))
}

fn synthetic_profile_requires_exact_seed(symbol: &str) -> bool {
    symbol.contains('_')
}

fn extract_doc_field(source: &str, label: &str) -> Option<String> {
    source
        .lines()
        .find_map(|line| {
            let trimmed = line.trim();
            let (left, right) = trimmed.split_once(':')?;
            if left.trim() == label {
                Some(right.trim().to_string())
            } else {
                None
            }
        })
        .filter(|value| !value.is_empty())
}

fn camel_to_snake(raw: &str) -> String {
    let mut out = String::new();
    for (index, ch) in raw.chars().enumerate() {
        if ch.is_ascii_uppercase() && index > 0 {
            out.push('_');
        }
        out.push(ch.to_ascii_lowercase());
    }
    out
}

fn sanitize_auto_quant_meta_value(raw: &str) -> String {
    raw.replace("<=", " at_or_below ")
        .replace(">=", " at_or_above ")
        .replace('<', " below ")
        .replace('>', " above ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ")
}

fn inject_auto_quant_meta_into_docstring(source: &str, meta_block: &str) -> String {
    for delimiter in ["\"\"\"", "'''"] {
        if let Some(rest) = source.strip_prefix(delimiter) {
            if let Some(end) = rest.find(delimiter) {
                let doc = &rest[..end];
                let suffix = &rest[end..];
                let mut merged = String::new();
                merged.push_str(delimiter);
                merged.push_str(doc.trim_end());
                if !doc.trim_end().is_empty() {
                    merged.push_str("\n\n");
                }
                merged.push_str(meta_block);
                merged.push('\n');
                merged.push_str(suffix);
                return merged;
            }
        }
    }
    format!("\"\"\"\n{meta_block}\n\"\"\"\n\n{source}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn synthetic_ohlcv_pair_alias_preserves_plain_symbol_shape() {
        assert_eq!(synthetic_ohlcv_pair_alias("NQ"), "NQ/USD");
        assert_eq!(synthetic_ohlcv_pair_alias("BTCUSDT"), "BTCUSDT/USD");
    }

    #[test]
    fn synthetic_ohlcv_pair_alias_strips_external_runtime_suffixes() {
        assert_eq!(synthetic_ohlcv_pair_alias("BTCUSDT_EXT_1H"), "BTCUSDT/USD");
        assert_eq!(synthetic_ohlcv_pair_alias("ETHUSDT_EXT_4H"), "ETHUSDT/USD");
    }

    #[test]
    fn synthetic_ohlcv_pair_alias_collapses_provider_decorated_runtime_symbol_to_ticker() {
        assert_eq!(
            synthetic_ohlcv_pair_alias("IBKR_QQQ_SYNTH_CONFORMAL_SMOKE"),
            "QQQ/USD"
        );
    }

    #[test]
    fn synthetic_ohlcv_pair_alias_skips_asset_class_tokens_for_futures_symbols() {
        assert_eq!(
            synthetic_ohlcv_pair_alias("IBKR_FUTURES_MNQ1M_LIQUIDITY_SWEEP_SIM_TRADE_ADMISSION_V1"),
            "MNQ/USD"
        );
        assert_eq!(
            synthetic_ohlcv_pair_alias("IBKR_FUTURES_MGC1M_ADX_ATR_BREAKOUT_7D_GATE1_V1"),
            "MGC/USD"
        );
    }

    #[test]
    fn synthetic_ohlcv_pair_alias_collapses_local_nonbtc_runtime_symbol_to_ticker() {
        assert_eq!(
            synthetic_ohlcv_pair_alias("B2R_LOCAL_NONBTC_SPY_USD_MTF_124245"),
            "SPY/USD"
        );
    }

    #[test]
    fn source_candle_timerange_uses_first_and_last_utc_dates() {
        use crate::types::Candle;
        use chrono::{TimeZone, Utc};

        let candles = vec![
            Candle {
                timestamp: Utc.with_ymd_and_hms(2026, 5, 2, 23, 0, 0).unwrap(),
                open: 1.0,
                high: 2.0,
                low: 0.5,
                close: 1.5,
                volume: 10.0,
            },
            Candle {
                timestamp: Utc.with_ymd_and_hms(2026, 5, 15, 18, 0, 0).unwrap(),
                open: 1.5,
                high: 2.5,
                low: 1.0,
                close: 2.0,
                volume: 12.0,
            },
        ];

        assert_eq!(
            source_candle_timerange(&candles).unwrap(),
            "20260502-20260515"
        );
    }

    #[test]
    fn synthetic_profile_does_not_seed_nq_fallback_for_other_symbols() {
        let temp = tempfile::tempdir().unwrap();
        let source_dir = temp.path().join("source");
        let target_dir = temp.path().join("target");
        fs::create_dir_all(&source_dir).unwrap();
        fs::create_dir_all(&target_dir).unwrap();
        let nq_strategy = source_dir.join("TomacNQ_KillzoneBreakout.py");
        fs::write(
            &nq_strategy,
            r#""""NQ-only upstream template."""

from freqtrade.strategy import IStrategy

class TomacNQ_KillzoneBreakout(IStrategy):
    pass
"#,
        )
        .unwrap();

        seed_profile_strategies(
            &source_dir,
            &target_dir,
            &nq_strategy,
            "IBKR_M2K1M_RVOL_PDA_CONSISTENCY_FLOOR_AUTORESEARCH_REPAIR_V1",
        )
        .unwrap();

        let active_files = fs::read_dir(&target_dir)
            .unwrap()
            .filter_map(Result::ok)
            .filter(|entry| {
                entry
                    .path()
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .map(|ext| ext.eq_ignore_ascii_case("py"))
                    .unwrap_or(false)
            })
            .collect::<Vec<_>>();
        assert!(
            active_files.is_empty(),
            "M2K synthetic handoff must remain seed-required instead of copying generic NQ"
        );
    }

    #[test]
    fn synthetic_profile_selection_infers_exact_tomac_ladder_from_source_path() {
        let temp = tempfile::tempdir().unwrap();
        let state_dir = temp.path().join("state");
        fs::create_dir_all(&state_dir).unwrap();
        let source_data_path = temp
            .path()
            .join("data-root-diagnostic/tomac_tod_cap65_nq_1m_tail20k.csv");

        let profile = persist_workspace_profile_selection(
            state_dir.to_str().unwrap(),
            Some(AUTO_QUANT_PROFILE_SYNTHETIC_OHLCV),
            "TOMAC_TOD_BALANCED_PORTFOLIO_CAP65_DOWNSTREAM_V1",
            source_data_path.to_str().unwrap(),
        )
        .unwrap()
        .expect("synthetic profile");

        assert_eq!(profile.pair, "NQ/USD");
        assert_eq!(profile.base_timeframe, "1m");
        assert_eq!(
            profile.additional_timeframes,
            vec![
                "5m".to_string(),
                "15m".to_string(),
                "30m".to_string(),
                "1h".to_string(),
                "4h".to_string(),
                "1d".to_string(),
            ]
        );
        assert_eq!(profile.source_data_path, source_data_path.to_string_lossy());
    }
}
