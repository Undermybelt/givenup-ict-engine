use super::*;

pub(crate) struct FactorBacktestShellInput<'a> {
    pub symbol: &'a str,
    pub data: &'a str,
    pub multi_timeframe_inputs: MultiTimeframeInputPaths<'a>,
    pub paired_data: Option<&'a str>,
    pub auxiliary_evidence: Option<&'a str>,
    pub ensemble: bool,
    pub state_dir: &'a str,
    pub output_format: &'a str,
}

pub(crate) fn factor_backtest_shell(input: FactorBacktestShellInput<'_>) -> Result<()> {
    let FactorBacktestShellInput {
        symbol,
        data,
        multi_timeframe_inputs,
        paired_data,
        auxiliary_evidence,
        ensemble,
        state_dir,
        output_format,
    } = input;
    ensure_state_dir_ready(state_dir)?;
    let auxiliary_override = auxiliary_evidence
        .map(load_auxiliary_evidence_from_path)
        .transpose()?;
    ict_engine::application::backtest::factor_backtest_command(
        symbol,
        data,
        paired_data,
        ensemble,
        state_dir,
        output_format,
        |symbol, data, paired_data, state_dir| {
            run_factor_backtest(RunFactorBacktestInput {
                symbol,
                data,
                multi_timeframe_inputs,
                paired_data,
                auxiliary_override: auxiliary_override.as_ref(),
                state_dir,
            })
        },
    )
}

fn load_auxiliary_evidence_from_path(
    path: &str,
) -> Result<ict_engine::data::realtime::market_support::AuxiliaryMarketEvidence> {
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("reading auxiliary/options evidence from {}", path))?;
    if let Ok(auxiliary) = serde_json::from_str(&raw) {
        return Ok(auxiliary);
    }
    let value: serde_json::Value = serde_json::from_str(&raw)
        .with_context(|| format!("parsing auxiliary/options evidence JSON from {}", path))?;
    if let Some(auxiliary) = event_fundamentals_sidecar_bundle_to_auxiliary(&value)? {
        return Ok(auxiliary);
    }
    let nested = value
        .get("supporting")
        .and_then(|supporting| supporting.get("auxiliary"))
        .cloned()
        .or_else(|| value.get("auxiliary").cloned())
        .context(
            "expected AuxiliaryMarketEvidence JSON or an object at supporting.auxiliary / auxiliary",
        )?;
    serde_json::from_value(nested)
        .with_context(|| format!("deserializing AuxiliaryMarketEvidence from {}", path))
}

fn event_fundamentals_sidecar_bundle_to_auxiliary(
    value: &serde_json::Value,
) -> Result<Option<ict_engine::data::realtime::market_support::AuxiliaryMarketEvidence>> {
    if value.get("schema_version").and_then(|item| item.as_str())
        != Some("event-fundamentals-adoption/v1")
    {
        return Ok(None);
    }

    let profile_contract_ready = value
        .get("artifact_readiness")
        .and_then(|item| item.get("profile_contract_ready"))
        .and_then(|item| item.as_bool())
        .unwrap_or(false);
    let readiness_label = value
        .get("downstream_handoff")
        .and_then(|item| item.get("readiness"))
        .and_then(|item| item.as_str())
        .unwrap_or("unknown");
    let allowed_use_modes: Vec<String> = value
        .get("downstream_handoff")
        .and_then(|item| item.get("allowed_use_modes"))
        .and_then(|item| item.as_array())
        .map(|items| {
            items
                .iter()
                .filter_map(|item| item.as_str().map(str::to_string))
                .collect()
        })
        .unwrap_or_default();
    let allows_factor_research_opt_in = allowed_use_modes
        .iter()
        .any(|mode| mode == "factor_research_opt_in");

    if !profile_contract_ready || !allows_factor_research_opt_in {
        anyhow::bail!(
            "factor_research_auxiliary_sidecar_incomplete: expected profile_contract_ready=true and allowed_use_modes to include factor_research_opt_in readiness={} allowed_use_modes={:?}",
            readiness_label,
            allowed_use_modes
        );
    }

    let workflow_symbol = value
        .get("workflow_symbol")
        .and_then(|item| item.as_str())
        .or_else(|| value.get("market_key").and_then(|item| item.as_str()))
        .context("event-fundamentals sidecar bundle missing workflow_symbol / market_key")?;
    let market_key = value
        .get("market_key")
        .and_then(|item| item.as_str())
        .unwrap_or(workflow_symbol);
    let spot_kind = infer_sidecar_spot_kind(market_key, workflow_symbol);

    let mut notes = vec![
        "event_fundamentals_sidecar_bundle".to_string(),
        format!("sidecar_bundle_readiness={readiness_label}"),
        format!("sidecar_market_key={market_key}"),
    ];
    if let Some(warnings) = value.get("usage_warnings").and_then(|item| item.as_array()) {
        notes.extend(
            warnings
                .iter()
                .filter_map(|item| item.as_str().map(str::to_string)),
        );
    }

    Ok(Some(
        ict_engine::data::realtime::market_support::AuxiliaryMarketEvidence {
            spot_symbol: workflow_symbol.to_string(),
            options_symbol: workflow_symbol.to_string(),
            spot_kind,
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
            hedge_pressure_score: Some(0.0),
            long_bias: 0.0,
            short_bias: 0.0,
            uncertainty_penalty: 0.0,
            notes,
        },
    ))
}

fn infer_sidecar_spot_kind(
    market_key: &str,
    workflow_symbol: &str,
) -> ict_engine::data::realtime::market_support::SpotInstrumentKind {
    if workflow_symbol.trim().starts_with('^') {
        return ict_engine::data::realtime::market_support::SpotInstrumentKind::Index;
    }

    let normalized_market = market_key.trim().to_ascii_uppercase();
    if matches!(
        normalized_market.as_str(),
        "NQ" | "MNQ"
            | "ES"
            | "MES"
            | "YM"
            | "MYM"
            | "RTY"
            | "M2K"
            | "RUT"
            | "SPX"
            | "NDX"
            | "DJI"
            | "VIX"
    ) {
        ict_engine::data::realtime::market_support::SpotInstrumentKind::Index
    } else {
        ict_engine::data::realtime::market_support::SpotInstrumentKind::Equity
    }
}

pub(crate) fn factor_pipeline_debug_shell(
    input: ict_engine::application::factor_pipeline_debug::FactorPipelineDebugCommandInput<'_>,
) -> Result<()> {
    ict_engine::application::factor_pipeline_debug::factor_pipeline_debug_command(input)
}
