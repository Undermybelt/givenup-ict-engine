use super::*;

pub(crate) struct FactorResearchShellInput<'a> {
    pub(crate) symbol: &'a str,
    pub(crate) data: &'a str,
    pub(crate) objective: &'a str,
    pub(crate) data_1m: Option<&'a str>,
    pub(crate) data_5m: Option<&'a str>,
    pub(crate) data_15m: Option<&'a str>,
    pub(crate) data_1h: Option<&'a str>,
    pub(crate) data_4h: Option<&'a str>,
    pub(crate) data_1d: Option<&'a str>,
    pub(crate) paired_data: Option<&'a str>,
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

pub(crate) fn factor_research_shell(input: FactorResearchShellInput<'_>) -> Result<()> {
    let FactorResearchShellInput {
        symbol,
        data,
        objective,
        data_1m,
        data_5m,
        data_15m,
        data_1h,
        data_4h,
        data_1d,
        paired_data,
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

    ensure_state_dir_ready(state_dir)?;
    let output_format = match resolve_output_format(output_format, compact, agent, human)? {
        OutputFormat::Json => "json",
        OutputFormat::Compact => "compact",
        OutputFormat::Agent => "agent",
        OutputFormat::Human => "human",
    };
    if backend == "auto-quant" {
        auto_quant_factor_research_command(AutoQuantFactorResearchCommandInput {
            symbol,
            data,
            objective,
            paired_data,
            mutation_spec_path: mutation_spec,
            strategy_material_root,
            state_dir,
            output_format,
        })
    } else {
        ict_engine::application::backtest::factor_research_command(
            ict_engine::application::backtest::FactorResearchCommandInput {
                symbol,
                data,
                objective,
                mutation_spec_path: mutation_spec,
                control_matrix_pb12,
                emit_mutation_evaluation,
                ensemble,
                state_dir,
                output_format,
            },
            load_factor_mutation_spec,
            |objective_mode,
             mutation_spec,
             control_matrix_plan,
             _control_matrix_run,
             runtime_overrides,
             run_state_dir| {
                run_factor_research(RunFactorResearchInput {
                    symbol,
                    data,
                    objective: objective_mode,
                    data_1m,
                    data_5m,
                    data_15m,
                    data_1h,
                    data_4h,
                    data_1d,
                    paired_data,
                    paired_candles_override: runtime_overrides.paired_candles,
                    auxiliary_override: runtime_overrides.auxiliary,
                    runtime_notes: runtime_overrides.runtime_notes,
                    mutation_spec: mutation_spec.as_ref(),
                    control_matrix_plan,
                    state_dir: run_state_dir,
                })
            },
        )
    }
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
    pub(crate) data_1h: Option<&'a str>,
    pub(crate) data_4h: Option<&'a str>,
    pub(crate) data_1d: Option<&'a str>,
    pub(crate) paired_data: Option<&'a str>,
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
        data_1h,
        data_4h,
        data_1d,
        paired_data,
        strategy_material_root,
        session_id,
        resume_latest,
        max_cluster_fail_streak,
        state_dir,
        backend,
    } = input;

    ensure_state_dir_ready(state_dir)?;
    if backend == "auto-quant" {
        auto_quant_factor_autoresearch_command(AutoQuantFactorAutoresearchCommandInput {
            symbol,
            data,
            objective,
            paired_data,
            mutation_spec_path: mutation_spec,
            strategy_material_root,
            iterations,
            session_id,
            state_dir,
        })
    } else {
        ict_engine::application::factor_lifecycle::factor_autoresearch_command(
            ict_engine::application::factor_lifecycle::FactorAutoresearchCommandInput {
                symbol,
                data,
                objective,
                mutation_spec_path: mutation_spec,
                iterations,
                data_1m,
                data_5m,
                data_15m,
                data_1h,
                data_4h,
                data_1d,
                paired_data,
                session_id,
                resume_latest,
                max_cluster_fail_streak,
                state_dir,
            },
            load_factor_mutation_spec,
            |objective_mode, mutation_spec| {
                run_factor_research(RunFactorResearchInput {
                    symbol,
                    data,
                    objective: objective_mode,
                    data_1m,
                    data_5m,
                    data_15m,
                    data_1h,
                    data_4h,
                    data_1d,
                    paired_data,
                    paired_candles_override: None,
                    auxiliary_override: None,
                    runtime_notes: Vec::new(),
                    mutation_spec: Some(mutation_spec),
                    control_matrix_plan: None,
                    state_dir,
                })
            },
        )
    }
}
