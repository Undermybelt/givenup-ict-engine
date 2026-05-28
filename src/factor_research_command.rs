use super::*;

pub(crate) struct FactorResearchShellInput<'a> {
    pub(crate) symbol: &'a str,
    pub(crate) data: &'a str,
    pub(crate) objective: &'a str,
    pub(crate) data_1m: Option<&'a str>,
    pub(crate) data_5m: Option<&'a str>,
    pub(crate) data_15m: Option<&'a str>,
    pub(crate) data_30m: Option<&'a str>,
    pub(crate) data_1h: Option<&'a str>,
    pub(crate) data_4h: Option<&'a str>,
    pub(crate) data_1d: Option<&'a str>,
    pub(crate) paired_data: Option<&'a str>,
    pub(crate) provider_profile: Option<&'a str>,
    pub(crate) auto_quant_profile: Option<&'a str>,
    pub(crate) auxiliary_evidence: Option<&'a str>,
    pub(crate) mutation_spec: Option<&'a str>,
    pub(crate) control_matrix_pb12: bool,
    pub(crate) strategy_material_root: Option<&'a str>,
    pub(crate) emit_mutation_evaluation: bool,
    pub(crate) ensemble: bool,
    pub(crate) state_dir: &'a str,
    pub(crate) output_format: &'a str,
    pub(crate) compact: bool,
    pub(crate) agent: bool,
    pub(crate) human: bool,
    pub(crate) backend: &'a str,
}

fn ensure_public_auto_quant_backend(backend: &str, surface: &str) -> Result<()> {
    let normalized = backend.trim().to_ascii_lowercase();
    if normalized.is_empty() || normalized == "auto-quant" {
        return Ok(());
    }
    anyhow::bail!(
        "{} public factor iteration is locked to Auto-Quant; rerun without --backend or pass --backend auto-quant",
        surface
    );
}

pub(crate) fn factor_research_shell(input: FactorResearchShellInput<'_>) -> Result<()> {
    let FactorResearchShellInput {
        symbol,
        data,
        objective,
        data_1m,
        data_5m,
        data_15m,
        data_30m,
        data_1h,
        data_4h,
        data_1d,
        paired_data,
        provider_profile,
        auto_quant_profile,
        auxiliary_evidence,
        mutation_spec,
        control_matrix_pb12,
        strategy_material_root,
        emit_mutation_evaluation,
        ensemble,
        state_dir,
        output_format,
        compact,
        agent,
        human,
        backend,
    } = input;

    ensure_public_auto_quant_backend(backend, "factor-research")?;
    ensure_state_dir_ready(state_dir)?;
    let cli_auxiliary_override = load_auxiliary_evidence_override(auxiliary_evidence)?;
    let cli_runtime_notes =
        build_auxiliary_runtime_notes(auxiliary_evidence, cli_auxiliary_override.as_ref());
    let output_format = crate::output_format::output_format_label(resolve_output_format(
        output_format,
        compact,
        agent,
        human,
    )?);
    let _ = (
        data_1m,
        data_5m,
        data_15m,
        data_30m,
        data_1h,
        data_4h,
        data_1d,
        cli_auxiliary_override,
        cli_runtime_notes,
        control_matrix_pb12,
        emit_mutation_evaluation,
        ensemble,
        backend,
    );
    auto_quant_factor_research_command(AutoQuantFactorResearchCommandInput {
        symbol,
        data,
        objective,
        provider_profile_selector: provider_profile,
        paired_data,
        auto_quant_profile,
        auxiliary_evidence_path: auxiliary_evidence,
        mutation_spec_path: mutation_spec,
        strategy_material_root,
        state_dir,
        output_format,
    })
}

pub(crate) struct FactorAutoresearchShellInput<'a> {
    pub(crate) symbol: &'a str,
    pub(crate) data: &'a str,
    pub(crate) objective: &'a str,
    pub(crate) mutation_spec: Option<&'a str>,
    pub(crate) iterations: usize,
    pub(crate) data_1m: Option<&'a str>,
    pub(crate) data_5m: Option<&'a str>,
    pub(crate) data_15m: Option<&'a str>,
    pub(crate) data_30m: Option<&'a str>,
    pub(crate) data_1h: Option<&'a str>,
    pub(crate) data_4h: Option<&'a str>,
    pub(crate) data_1d: Option<&'a str>,
    pub(crate) paired_data: Option<&'a str>,
    pub(crate) provider_profile: Option<&'a str>,
    pub(crate) auto_quant_profile: Option<&'a str>,
    pub(crate) auxiliary_evidence: Option<&'a str>,
    pub(crate) strategy_material_root: Option<&'a str>,
    pub(crate) session_id: Option<&'a str>,
    pub(crate) resume_latest: bool,
    pub(crate) max_cluster_fail_streak: usize,
    pub(crate) state_dir: &'a str,
    pub(crate) backend: &'a str,
}

pub(crate) fn factor_autoresearch_shell(input: FactorAutoresearchShellInput<'_>) -> Result<()> {
    let FactorAutoresearchShellInput {
        symbol,
        data,
        objective,
        mutation_spec,
        iterations,
        data_1m,
        data_5m,
        data_15m,
        data_30m,
        data_1h,
        data_4h,
        data_1d,
        paired_data,
        provider_profile,
        auto_quant_profile,
        auxiliary_evidence,
        strategy_material_root,
        session_id,
        resume_latest,
        max_cluster_fail_streak,
        state_dir,
        backend,
    } = input;

    ensure_public_auto_quant_backend(backend, "factor-autoresearch")?;
    ensure_state_dir_ready(state_dir)?;
    let cli_auxiliary_override = load_auxiliary_evidence_override(auxiliary_evidence)?;
    let cli_runtime_notes =
        build_auxiliary_runtime_notes(auxiliary_evidence, cli_auxiliary_override.as_ref());
    let _ = (
        data_1m,
        data_5m,
        data_15m,
        data_30m,
        data_1h,
        data_4h,
        data_1d,
        cli_auxiliary_override,
        cli_runtime_notes,
        resume_latest,
        max_cluster_fail_streak,
        backend,
    );
    auto_quant_factor_autoresearch_command(AutoQuantFactorAutoresearchCommandInput {
        symbol,
        data,
        objective,
        provider_profile_selector: provider_profile,
        paired_data,
        auto_quant_profile,
        auxiliary_evidence_path: auxiliary_evidence,
        mutation_spec_path: mutation_spec,
        strategy_material_root,
        iterations,
        session_id,
        state_dir,
    })
}

fn load_auxiliary_evidence_override(path: Option<&str>) -> Result<Option<AuxiliaryMarketEvidence>> {
    path.map(load_auxiliary_evidence_from_path).transpose()
}

fn load_auxiliary_evidence_from_path(path: &str) -> Result<AuxiliaryMarketEvidence> {
    if !std::path::Path::new(path).exists() {
        anyhow::bail!(
            "factor_research_auxiliary_evidence_missing: flag=--auxiliary-evidence path={} expected=AuxiliaryMarketEvidence JSON, analyze-report JSON containing supporting.auxiliary, or event-fundamentals sidecar bundle recovery=export auxiliary market/options evidence or rerun without --auxiliary-evidence until that artifact exists",
            path
        );
    }
    let raw = std::fs::read_to_string(path)
        .with_context(|| format!("reading auxiliary/options evidence from {}", path))?;
    if let Ok(auxiliary) = serde_json::from_str::<AuxiliaryMarketEvidence>(&raw) {
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
    serde_json::from_value::<AuxiliaryMarketEvidence>(nested)
        .with_context(|| format!("deserializing AuxiliaryMarketEvidence from {}", path))
}

fn event_fundamentals_sidecar_bundle_to_auxiliary(
    value: &serde_json::Value,
) -> Result<Option<AuxiliaryMarketEvidence>> {
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

    Ok(Some(AuxiliaryMarketEvidence {
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
    }))
}

fn infer_sidecar_spot_kind(market_key: &str, workflow_symbol: &str) -> SpotInstrumentKind {
    if workflow_symbol.trim().starts_with('^') {
        return SpotInstrumentKind::Index;
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
        SpotInstrumentKind::Index
    } else {
        SpotInstrumentKind::Equity
    }
}

fn build_auxiliary_runtime_notes(
    path: Option<&str>,
    auxiliary: Option<&AuxiliaryMarketEvidence>,
) -> Vec<String> {
    let mut notes = Vec::new();
    if let Some(path) = path {
        notes.push(format!("auxiliary_evidence_path={path}"));
    }
    if let Some(auxiliary) = auxiliary {
        notes.push(format!("auxiliary_spot_symbol={}", auxiliary.spot_symbol));
        notes.push(format!(
            "auxiliary_options_symbol={}",
            auxiliary.options_symbol
        ));
    }
    notes
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn public_factor_iteration_backend_accepts_auto_quant() {
        assert!(ensure_public_auto_quant_backend("auto-quant", "factor-research").is_ok());
        assert!(ensure_public_auto_quant_backend("", "factor-research").is_ok());
    }

    #[test]
    fn public_factor_iteration_backend_rejects_native() {
        let error = ensure_public_auto_quant_backend("native", "factor-research")
            .expect_err("native backend should be rejected on public CLI");
        assert!(error
            .to_string()
            .contains("public factor iteration is locked to Auto-Quant"));
    }

    #[test]
    fn loads_auxiliary_evidence_from_direct_json() {
        let temp = tempfile::NamedTempFile::new().unwrap();
        let payload = serde_json::json!({
            "spot_symbol": "QQQ",
            "options_symbol": "QQQ",
            "spot_kind": "Equity",
            "spot_last_close": 500.0,
            "futures_last_close": 19999.0,
            "spot_return": 0.01,
            "futures_return": 0.02,
            "raw_basis_bps": 1.5,
            "normalized_basis_bps": 0.5,
            "rolling_price_ratio_mean": 1.02,
            "put_call_oi_ratio": 0.8,
            "put_call_volume_ratio": 0.9,
            "near_atm_implied_volatility": 0.2,
            "near_atm_delta": 0.55,
            "near_atm_gamma": 0.12,
            "near_atm_vega": 0.18,
            "call_gamma_oi": 100.0,
            "put_gamma_oi": 80.0,
            "gamma_skew": 0.25,
            "hedge_pressure_direction": "long",
            "hedge_pressure_score": 0.4,
            "long_bias": 0.15,
            "short_bias": 0.05,
            "uncertainty_penalty": 0.1,
            "notes": ["direct_auxiliary"]
        });
        std::fs::write(temp.path(), serde_json::to_string(&payload).unwrap()).unwrap();

        let auxiliary = load_auxiliary_evidence_from_path(temp.path().to_str().unwrap()).unwrap();
        assert_eq!(auxiliary.spot_symbol, "QQQ");
        assert_eq!(auxiliary.options_symbol, "QQQ");
        assert_eq!(auxiliary.hedge_pressure_direction.as_deref(), Some("long"));
    }

    #[test]
    fn missing_auxiliary_evidence_error_names_flag_schema_and_recovery() {
        let temp = tempfile::tempdir().unwrap();
        let missing_path = temp.path().join("missing-auxiliary-evidence.json");

        let err = load_auxiliary_evidence_from_path(missing_path.to_str().unwrap()).unwrap_err();
        let message = format!("{err:#}");

        assert!(
            message.contains("factor_research_auxiliary_evidence_missing"),
            "{message}"
        );
        assert!(message.contains("flag=--auxiliary-evidence"), "{message}");
        assert!(message.contains("AuxiliaryMarketEvidence"), "{message}");
        assert!(message.contains("supporting.auxiliary"), "{message}");
        assert!(message.contains("recovery="), "{message}");
    }

    #[test]
    fn loads_auxiliary_evidence_from_analyze_report_wrapper() {
        let temp = tempfile::NamedTempFile::new().unwrap();
        let payload = serde_json::json!({
            "supporting": {
                "auxiliary": {
                    "spot_symbol": "SPY",
                    "options_symbol": "SPY",
                    "spot_kind": "Equity",
                    "spot_last_close": 500.0,
                    "futures_last_close": 5200.0,
                    "spot_return": 0.01,
                    "futures_return": 0.02,
                    "raw_basis_bps": 2.0,
                    "normalized_basis_bps": 0.6,
                    "rolling_price_ratio_mean": 1.01,
                    "put_call_oi_ratio": 1.1,
                    "put_call_volume_ratio": 1.2,
                    "near_atm_implied_volatility": 0.21,
                    "near_atm_delta": 0.45,
                    "near_atm_gamma": 0.10,
                    "near_atm_vega": 0.17,
                    "call_gamma_oi": 120.0,
                    "put_gamma_oi": 130.0,
                    "gamma_skew": -0.15,
                    "hedge_pressure_direction": "short",
                    "hedge_pressure_score": -0.35,
                    "long_bias": 0.02,
                    "short_bias": 0.14,
                    "uncertainty_penalty": 0.12,
                    "notes": ["wrapped_auxiliary"]
                }
            }
        });
        std::fs::write(temp.path(), serde_json::to_string(&payload).unwrap()).unwrap();

        let auxiliary = load_auxiliary_evidence_from_path(temp.path().to_str().unwrap()).unwrap();
        assert_eq!(auxiliary.spot_symbol, "SPY");
        assert_eq!(auxiliary.options_symbol, "SPY");
        assert_eq!(auxiliary.hedge_pressure_direction.as_deref(), Some("short"));
    }

    #[test]
    fn loads_auxiliary_evidence_from_event_fundamentals_sidecar_bundle_when_ready() {
        let temp = tempfile::NamedTempFile::new().unwrap();
        let payload = serde_json::json!({
            "schema_version": "event-fundamentals-adoption/v1",
            "market_key": "NQ",
            "workflow_symbol": "NQ_EVENT_CONTEXT",
            "artifact_readiness": {
                "profile_contract_ready": true,
                "covered_contract_count": 4,
                "covered_contract_ids": [
                    "dividend_event_series",
                    "earnings_event_series",
                    "lagged_fundamentals_sidecar",
                    "macro_event_series"
                ],
                "missing_contract_ids": []
            },
            "usage_warnings": [
                "Lag fundamentals by effective date before backtest or live reuse.",
                "Keep macro events aligned to scheduled release timestamps and explicit importance tiers."
            ],
            "downstream_handoff": {
                "readiness": "profile_contract_ready",
                "missing_artifact_kinds": [],
                "allowed_use_modes": [
                    "research_context",
                    "factor_research_opt_in",
                    "auto_quant_handoff_context"
                ]
            }
        });
        std::fs::write(temp.path(), serde_json::to_string(&payload).unwrap()).unwrap();

        let auxiliary = load_auxiliary_evidence_from_path(temp.path().to_str().unwrap()).unwrap();
        assert_eq!(auxiliary.spot_symbol, "NQ_EVENT_CONTEXT");
        assert_eq!(auxiliary.options_symbol, "NQ_EVENT_CONTEXT");
        assert_eq!(auxiliary.spot_kind, SpotInstrumentKind::Index);
        assert_eq!(auxiliary.long_bias, 0.0);
        assert_eq!(auxiliary.short_bias, 0.0);
        assert_eq!(auxiliary.uncertainty_penalty, 0.0);
        assert!(auxiliary
            .notes
            .iter()
            .any(|note| note == "event_fundamentals_sidecar_bundle"));
        assert!(auxiliary
            .notes
            .iter()
            .any(|note| note == "sidecar_bundle_readiness=profile_contract_ready"));
        assert!(auxiliary
            .notes
            .iter()
            .any(|note| note.contains("Lag fundamentals by effective date")));
    }

    #[test]
    fn rejects_event_fundamentals_sidecar_bundle_when_not_ready_for_factor_research() {
        let temp = tempfile::NamedTempFile::new().unwrap();
        let payload = serde_json::json!({
            "schema_version": "event-fundamentals-adoption/v1",
            "market_key": "NQ",
            "workflow_symbol": "NQ_EVENT_CONTEXT",
            "artifact_readiness": {
                "profile_contract_ready": false,
                "covered_contract_count": 2,
                "covered_contract_ids": [
                    "earnings_event_series",
                    "lagged_fundamentals_sidecar"
                ],
                "missing_contract_ids": [
                    "dividend_event_series",
                    "macro_event_series"
                ]
            },
            "usage_warnings": [
                "Lag fundamentals by effective date before backtest or live reuse."
            ],
            "downstream_handoff": {
                "readiness": "partial_sidecar_pack",
                "missing_artifact_kinds": ["dividends", "macro"],
                "allowed_use_modes": [
                    "research_context",
                    "auto_quant_handoff_context"
                ]
            }
        });
        std::fs::write(temp.path(), serde_json::to_string(&payload).unwrap()).unwrap();

        let err = load_auxiliary_evidence_from_path(temp.path().to_str().unwrap()).unwrap_err();
        let message = format!("{err:#}");

        assert!(
            message.contains("factor_research_auxiliary_sidecar_incomplete"),
            "{message}"
        );
        assert!(message.contains("profile_contract_ready"), "{message}");
        assert!(message.contains("factor_research_opt_in"), "{message}");
    }
}
