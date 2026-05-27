use super::*;
use clap::Parser;

#[test]
fn test_cli_backtest_accepts_human_output_alias() {
    let cli = parse_cli_from([
        "ict-engine",
        "backtest",
        "--symbol",
        "NQ",
        "--data",
        "candles.json",
        "--human",
    ])
    .unwrap();
    match cli.command {
        Commands::Backtest(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_backtest_uses_extracted_args() {
    let cli = parse_cli_from([
        "ict-engine",
        "backtest",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--paired-data",
        "paired.json",
        "--state-dir",
        "/tmp/ict-engine-backtest-state",
        "--output-format",
        "agent",
        "--warmup-bars",
        "72",
        "--hold-bars",
        "14",
        "--spread-bps",
        "1.25",
        "--slippage-bps",
        "2.5",
        "--fee-bps",
        "0.75",
        "--ambiguous-bar-policy",
        "favor_take_profit",
        "--online-learn",
    ])
    .unwrap();

    match cli.command {
        Commands::Backtest(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "primary.json");
            assert_eq!(args.paired_data.as_deref(), Some("paired.json"));
            assert_eq!(args.state_dir, "/tmp/ict-engine-backtest-state");
            assert_eq!(args.output_format, "agent");
            assert_eq!(args.warmup_bars, 72);
            assert_eq!(args.hold_bars, 14);
            assert_eq!(args.spread_bps, 1.25);
            assert_eq!(args.slippage_bps, 2.5);
            assert_eq!(args.fee_bps, 0.75);
            assert_eq!(args.ambiguous_bar_policy, "favor_take_profit");
            assert!(args.online_learn);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_runtime_command_input_types_live_with_owner_modules() {
    fn assert_update_input_owner(_: Option<crate::update_command::UpdateCommandInput<'_>>) {}
    fn assert_backtest_input_owner(
        _: Option<crate::probabilistic_backtest_runtime::RunProbabilisticBacktestInput<'_>>,
    ) {
    }

    assert_update_input_owner(None);
    assert_backtest_input_owner(None);
}

#[test]
fn test_cli_factor_research_accepts_output_format() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-research",
        "--symbol",
        "NQ",
        "--data",
        "candles.json",
        "--output-format",
        "compact",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorResearch(args) => assert_eq!(args.output_format, "compact"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_research_accepts_provider_profile() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-research",
        "--symbol",
        "NQ",
        "--data",
        "candles.json",
        "--profile",
        "thrill3r-nq-closed-loop-v1",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorResearch(args) => {
            assert_eq!(args.profile.as_deref(), Some("thrill3r-nq-closed-loop-v1"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_research_loop_commands_use_extracted_args() {
    let research_cli = parse_cli_from([
        "ict-engine",
        "factor-research",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--objective",
        "expansion-test",
        "--data-1m",
        "1m.json",
        "--data-5m",
        "5m.json",
        "--data-15m",
        "15m.json",
        "--data-30m",
        "30m.json",
        "--data-1h",
        "1h.json",
        "--data-4h",
        "4h.json",
        "--data-1d",
        "1d.json",
        "--paired-data",
        "paired.json",
        "--profile",
        "public-demo-profile",
        "--auto-quant-profile",
        "synthetic_ohlcv",
        "--auxiliary-evidence",
        "aux.json",
        "--mutation-spec",
        "mutation.json",
        "--control-matrix-pb12",
        "--strategy-material-root",
        "/tmp/materials",
        "--emit-mutation-evaluation",
        "--ensemble",
        "--state-dir",
        "/tmp/ict-engine-factor-research",
        "--output-format",
        "agent",
        "--backend",
        "auto-quant",
    ])
    .unwrap();
    match research_cli.command {
        Commands::FactorResearch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "primary.json");
            assert_eq!(args.objective, "expansion-test");
            assert_eq!(args.data_1m.as_deref(), Some("1m.json"));
            assert_eq!(args.data_5m.as_deref(), Some("5m.json"));
            assert_eq!(args.data_15m.as_deref(), Some("15m.json"));
            assert_eq!(args.data_30m.as_deref(), Some("30m.json"));
            assert_eq!(args.data_1h.as_deref(), Some("1h.json"));
            assert_eq!(args.data_4h.as_deref(), Some("4h.json"));
            assert_eq!(args.data_1d.as_deref(), Some("1d.json"));
            assert_eq!(args.paired_data.as_deref(), Some("paired.json"));
            assert_eq!(args.profile.as_deref(), Some("public-demo-profile"));
            assert_eq!(args.auto_quant_profile.as_deref(), Some("synthetic_ohlcv"));
            assert_eq!(args.auxiliary_evidence.as_deref(), Some("aux.json"));
            assert_eq!(args.mutation_spec.as_deref(), Some("mutation.json"));
            assert!(args.control_matrix_pb12);
            assert_eq!(
                args.strategy_material_root.as_deref(),
                Some("/tmp/materials")
            );
            assert!(args.emit_mutation_evaluation);
            assert!(args.ensemble);
            assert_eq!(args.state_dir, "/tmp/ict-engine-factor-research");
            assert_eq!(args.output_format, "agent");
            assert_eq!(args.backend, "auto-quant");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let autoresearch_cli = parse_cli_from([
        "ict-engine",
        "factor-autoresearch",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--objective",
        "expansion-test",
        "--mutation-spec",
        "mutation.json",
        "--iterations",
        "4",
        "--data-1m",
        "1m.json",
        "--data-5m",
        "5m.json",
        "--data-15m",
        "15m.json",
        "--data-30m",
        "30m.json",
        "--data-1h",
        "1h.json",
        "--data-4h",
        "4h.json",
        "--data-1d",
        "1d.json",
        "--paired-data",
        "paired.json",
        "--profile",
        "public-demo-profile",
        "--auto-quant-profile",
        "synthetic_ohlcv",
        "--auxiliary-evidence",
        "aux.json",
        "--strategy-material-root",
        "/tmp/materials",
        "--session-id",
        "session-1",
        "--resume-latest",
        "--max-cluster-fail-streak",
        "5",
        "--ensemble",
        "--state-dir",
        "/tmp/ict-engine-factor-autoresearch",
        "--backend",
        "auto-quant",
    ])
    .unwrap();
    match autoresearch_cli.command {
        Commands::FactorAutoresearch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "primary.json");
            assert_eq!(args.objective, "expansion-test");
            assert_eq!(args.mutation_spec.as_deref(), Some("mutation.json"));
            assert_eq!(args.iterations, 4);
            assert_eq!(args.data_1m.as_deref(), Some("1m.json"));
            assert_eq!(args.data_5m.as_deref(), Some("5m.json"));
            assert_eq!(args.data_15m.as_deref(), Some("15m.json"));
            assert_eq!(args.data_30m.as_deref(), Some("30m.json"));
            assert_eq!(args.data_1h.as_deref(), Some("1h.json"));
            assert_eq!(args.data_4h.as_deref(), Some("4h.json"));
            assert_eq!(args.data_1d.as_deref(), Some("1d.json"));
            assert_eq!(args.paired_data.as_deref(), Some("paired.json"));
            assert_eq!(args.profile.as_deref(), Some("public-demo-profile"));
            assert_eq!(args.auto_quant_profile.as_deref(), Some("synthetic_ohlcv"));
            assert_eq!(args.auxiliary_evidence.as_deref(), Some("aux.json"));
            assert_eq!(
                args.strategy_material_root.as_deref(),
                Some("/tmp/materials")
            );
            assert_eq!(args.session_id.as_deref(), Some("session-1"));
            assert!(args.resume_latest);
            assert_eq!(args.max_cluster_fail_streak, 5);
            assert!(args.ensemble);
            assert_eq!(args.state_dir, "/tmp/ict-engine-factor-autoresearch");
            assert_eq!(args.backend, "auto-quant");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let backtest_cli = parse_cli_from([
        "ict-engine",
        "factor-backtest",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--data-1m",
        "1m.json",
        "--data-5m",
        "5m.json",
        "--data-15m",
        "15m.json",
        "--data-30m",
        "30m.json",
        "--data-1h",
        "1h.json",
        "--data-4h",
        "4h.json",
        "--data-1d",
        "1d.json",
        "--paired-data",
        "paired.json",
        "--auxiliary-evidence",
        "aux.json",
        "--ensemble",
        "--state-dir",
        "/tmp/ict-engine-factor-backtest",
        "--output-format",
        "human",
    ])
    .unwrap();
    match backtest_cli.command {
        Commands::FactorBacktest(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "primary.json");
            assert_eq!(args.data_1m.as_deref(), Some("1m.json"));
            assert_eq!(args.data_5m.as_deref(), Some("5m.json"));
            assert_eq!(args.data_15m.as_deref(), Some("15m.json"));
            assert_eq!(args.data_30m.as_deref(), Some("30m.json"));
            assert_eq!(args.data_1h.as_deref(), Some("1h.json"));
            assert_eq!(args.data_4h.as_deref(), Some("4h.json"));
            assert_eq!(args.data_1d.as_deref(), Some("1d.json"));
            assert_eq!(args.paired_data.as_deref(), Some("paired.json"));
            assert_eq!(args.auxiliary_evidence.as_deref(), Some("aux.json"));
            assert!(args.ensemble);
            assert_eq!(args.state_dir, "/tmp/ict-engine-factor-backtest");
            assert_eq!(args.output_format, "human");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_market_data_and_debug_commands_use_extracted_args() {
    let harness_cli = parse_cli_from([
        "ict-engine",
        "market-data-harness",
        "--action",
        "fetch",
        "--market",
        "NQ",
        "--primary-data",
        "primary.json",
        "--interval",
        "15m",
        "--role",
        "primary",
        "--role",
        "options.summary",
        "--provider",
        "primary=yfinance",
        "--symbol-spec",
        "primary=NQ",
        "--request-stdin",
        "--options-volatility-proxy-symbol",
        "VIX",
        "--request-json",
        "request.json",
        "--agent",
    ])
    .unwrap();
    match harness_cli.command {
        Commands::MarketDataHarness(args) => {
            assert_eq!(args.action, "fetch");
            assert_eq!(args.market.as_deref(), Some("NQ"));
            assert_eq!(args.primary_data.as_deref(), Some("primary.json"));
            assert_eq!(args.interval.as_deref(), Some("15m"));
            assert_eq!(args.role, vec!["primary", "options.summary"]);
            assert_eq!(args.provider, vec!["primary=yfinance"]);
            assert_eq!(args.symbol_spec, vec!["primary=NQ"]);
            assert!(args.request_stdin);
            assert_eq!(args.options_volatility_proxy_symbol.as_deref(), Some("VIX"));
            assert_eq!(args.request_json.as_deref(), Some("request.json"));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let harness_human_cli = parse_cli_from([
        "ict-engine",
        "market-data-harness",
        "--action",
        "plan",
        "--market",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match harness_human_cli.command {
        Commands::MarketDataHarness(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let debug_cli = parse_cli_from([
        "ict-engine",
        "factor-pipeline-debug",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--factor",
        "trend_momentum",
        "--objective",
        "expansion",
        "--data-1m",
        "1m.json",
        "--data-5m",
        "5m.json",
        "--data-15m",
        "15m.json",
        "--data-30m",
        "30m.json",
        "--data-1h",
        "1h.json",
        "--data-4h",
        "4h.json",
        "--data-1d",
        "1d.json",
        "--agent",
    ])
    .unwrap();
    match debug_cli.command {
        Commands::FactorPipelineDebug(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "primary.json");
            assert_eq!(args.factor, "trend_momentum");
            assert_eq!(args.objective, "expansion");
            assert_eq!(args.data_1m.as_deref(), Some("1m.json"));
            assert_eq!(args.data_5m.as_deref(), Some("5m.json"));
            assert_eq!(args.data_15m.as_deref(), Some("15m.json"));
            assert_eq!(args.data_30m.as_deref(), Some("30m.json"));
            assert_eq!(args.data_1h.as_deref(), Some("1h.json"));
            assert_eq!(args.data_4h.as_deref(), Some("4h.json"));
            assert_eq!(args.data_1d.as_deref(), Some("1d.json"));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let debug_human_cli = parse_cli_from([
        "ict-engine",
        "factor-pipeline-debug",
        "--symbol",
        "NQ",
        "--data",
        "primary.json",
        "--factor",
        "trend_momentum",
        "--output-format",
        "human",
    ])
    .unwrap();
    match debug_human_cli.command {
        Commands::FactorPipelineDebug(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_market_data_sop_commands_use_extracted_args() {
    let clean_cli = parse_cli_from([
        "ict-engine",
        "clean-futures",
        "--root",
        "/tmp/raw",
        "--output-dir",
        "/tmp/out",
        "--interval",
        "5m",
        "--multi-timeframe",
    ])
    .unwrap();
    match clean_cli.command {
        Commands::CleanFutures(args) => {
            assert_eq!(args.root.as_deref(), Some("/tmp/raw"));
            assert_eq!(args.output_dir, "/tmp/out");
            assert_eq!(args.interval, "5m");
            assert!(args.multi_timeframe);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let futures_cli = parse_cli_from([
        "ict-engine",
        "futures-sop",
        "--root",
        "/tmp/raw",
        "--output-dir",
        "/tmp/sop",
        "--interval",
        "30m",
    ])
    .unwrap();
    match futures_cli.command {
        Commands::FuturesSop(args) => {
            assert_eq!(args.root.as_deref(), Some("/tmp/raw"));
            assert_eq!(args.output_dir, "/tmp/sop");
            assert_eq!(args.interval, "30m");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let expansion_cli = parse_cli_from([
        "ict-engine",
        "expansion-sop",
        "--root",
        "/tmp/raw",
        "--output-dir",
        "/tmp/expansion",
        "--interval",
        "1h",
        "--lookback",
        "34",
        "--atr-multiplier",
        "2.25",
        "--objective",
        "expansion-test",
        "--mutation-spec",
        "mutation.json",
        "--emit-mutation-evaluation",
    ])
    .unwrap();
    match expansion_cli.command {
        Commands::ExpansionSop(args) => {
            assert_eq!(args.root.as_deref(), Some("/tmp/raw"));
            assert_eq!(args.output_dir, "/tmp/expansion");
            assert_eq!(args.interval, "1h");
            assert_eq!(args.lookback, 34);
            assert_eq!(args.atr_multiplier, 2.25);
            assert_eq!(args.objective, "expansion-test");
            assert_eq!(args.mutation_spec.as_deref(), Some("mutation.json"));
            assert!(args.emit_mutation_evaluation);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_candidate_packs_accepts_output_format() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-candidate-packs",
        "--output-format",
        "json",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorCandidatePacks(args) => {
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_candidate_admission_targets_requires_symbol() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-candidate-admission-targets",
        "--symbol",
        "FACTOR_CANDIDATES",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--output-format",
        "json",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorCandidateAdmissionTargets(args) => {
            assert_eq!(args.symbol, "FACTOR_CANDIDATES");
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_asset_commands_accept_output_aliases() {
    let packs_cli = parse_cli_from(["ict-engine", "factor-candidate-packs", "--human"]).unwrap();
    match packs_cli.command {
        Commands::FactorCandidatePacks(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let admission_cli = parse_cli_from([
        "ict-engine",
        "factor-candidate-admission-targets",
        "--symbol",
        "FACTOR_CANDIDATES",
        "--agent",
    ])
    .unwrap();
    match admission_cli.command {
        Commands::FactorCandidateAdmissionTargets(args) => assert!(args.agent),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let assets_cli = parse_cli_from(["ict-engine", "regime-confidence-assets", "--human"]).unwrap();
    match assets_cli.command {
        Commands::RegimeConfidenceAssets(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let intake_cli = parse_cli_from([
        "ict-engine",
        "factor-asset-closure-intake",
        "--symbol",
        "NQ",
        "--agent",
    ])
    .unwrap();
    match intake_cli.command {
        Commands::FactorAssetClosureIntake(args) => assert!(args.agent),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_asset_commands_use_extracted_args() {
    let packs_cli = parse_cli_from([
        "ict-engine",
        "factor-candidate-packs",
        "--candidate-pack-root",
        "support/examples/factor_candidate_packs/test",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-factor-packs",
        "--output-format",
        "json",
    ])
    .unwrap();
    match packs_cli.command {
        Commands::FactorCandidatePacks(args) => {
            assert_eq!(
                args.candidate_pack_root,
                "support/examples/factor_candidate_packs/test"
            );
            assert_eq!(args.symbol.as_deref(), Some("NQ"));
            assert_eq!(
                args.state_dir.as_deref(),
                Some("/tmp/ict-engine-factor-packs")
            );
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let admission_cli = parse_cli_from([
        "ict-engine",
        "factor-candidate-admission-targets",
        "--candidate-pack-root",
        "support/examples/factor_candidate_packs/test",
        "--symbol",
        "FACTOR_CANDIDATES",
        "--state-dir",
        "/tmp/ict-engine-factor-admission",
        "--output-format",
        "json",
    ])
    .unwrap();
    match admission_cli.command {
        Commands::FactorCandidateAdmissionTargets(args) => {
            assert_eq!(
                args.candidate_pack_root,
                "support/examples/factor_candidate_packs/test"
            );
            assert_eq!(args.symbol, "FACTOR_CANDIDATES");
            assert_eq!(args.state_dir, "/tmp/ict-engine-factor-admission");
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let assets_cli = parse_cli_from([
        "ict-engine",
        "regime-confidence-assets",
        "--asset-ledger",
        "config/test_assets.csv",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-regime-assets",
        "--output-format",
        "json",
    ])
    .unwrap();
    match assets_cli.command {
        Commands::RegimeConfidenceAssets(args) => {
            assert_eq!(args.asset_ledger, "config/test_assets.csv");
            assert_eq!(args.symbol.as_deref(), Some("NQ"));
            assert_eq!(
                args.state_dir.as_deref(),
                Some("/tmp/ict-engine-regime-assets")
            );
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let intake_cli = parse_cli_from([
        "ict-engine",
        "factor-asset-closure-intake",
        "--candidate-pack-root",
        "support/examples/factor_candidate_packs/test",
        "--asset-ledger",
        "config/test_assets.csv",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-factor-intake",
        "--output-format",
        "json",
    ])
    .unwrap();
    match intake_cli.command {
        Commands::FactorAssetClosureIntake(args) => {
            assert_eq!(
                args.candidate_pack_root,
                "support/examples/factor_candidate_packs/test"
            );
            assert_eq!(args.asset_ledger, "config/test_assets.csv");
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-factor-intake");
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_structural_path_ranker_commands_accept_output_aliases() {
    let export_cli = parse_cli_from([
        "ict-engine",
        "export-structural-path-ranking-target",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--human",
    ])
    .unwrap();
    match export_cli.command {
        Commands::ExportStructuralPathRankingTarget(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let apply_cli = parse_cli_from([
        "ict-engine",
        "apply-structural-path-ranking-external-scores",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--scores-file",
        "scores.csv",
        "--output-format",
        "compact",
    ])
    .unwrap();
    match apply_cli.command {
        Commands::ApplyStructuralPathRankingExternalScores(args) => {
            assert_eq!(args.output_format, "compact");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_structural_path_ranker_commands_use_extracted_args() {
    let register_cli = parse_cli_from([
        "ict-engine",
        "register-structural-path-ranking-trainer-artifact",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--artifact-uri",
        "trainer.json",
        "--model-family",
        "catboost",
        "--score-column",
        "score",
        "--trained-rows",
        "12",
        "--calibration-rows",
        "3",
    ])
    .unwrap();
    match register_cli.command {
        Commands::RegisterStructuralPathRankingTrainerArtifact(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.artifact_uri, "trainer.json");
            assert_eq!(args.model_family, "catboost");
            assert_eq!(args.score_column, "score");
            assert_eq!(args.trained_rows, Some(12));
            assert_eq!(args.calibration_rows, Some(3));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let clear_cli = parse_cli_from([
        "ict-engine",
        "clear-structural-path-ranking-trainer-artifact",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-clear",
    ])
    .unwrap();
    match clear_cli.command {
        Commands::ClearStructuralPathRankingTrainerArtifact(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-clear");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let enable_cli = parse_cli_from([
        "ict-engine",
        "enable-structural-path-ranking-runtime",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-enable",
        "--reuse-mode",
        "prefer_history",
    ])
    .unwrap();
    match enable_cli.command {
        Commands::EnableStructuralPathRankingRuntime(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.reuse_mode, "prefer_history");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let disable_cli = parse_cli_from([
        "ict-engine",
        "disable-structural-path-ranking-runtime",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-disable",
    ])
    .unwrap();
    match disable_cli.command {
        Commands::DisableStructuralPathRankingRuntime(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-disable");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let export_cli = parse_cli_from([
        "ict-engine",
        "export-structural-path-ranking-target",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-export",
        "--agent",
    ])
    .unwrap();
    match export_cli.command {
        Commands::ExportStructuralPathRankingTarget(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-export");
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let apply_cli = parse_cli_from([
        "ict-engine",
        "apply-structural-path-ranking-external-scores",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-apply",
        "--scores-file",
        "scores.csv",
        "--human",
    ])
    .unwrap();
    match apply_cli.command {
        Commands::ApplyStructuralPathRankingExternalScores(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-apply");
            assert_eq!(args.scores_file, "scores.csv");
            assert!(args.human);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_policy_training_status_accepts_agent_alias() {
    let cli = parse_cli_from([
        "ict-engine",
        "policy-training-status",
        "--symbol",
        "DEMO",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--agent",
    ])
    .unwrap();

    match cli.command {
        Commands::PolicyTrainingStatus(args) => assert!(args.agent),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_research_status_commands_use_extracted_args() {
    let mutation_cli = parse_cli_from([
        "ict-engine",
        "factor-mutation-status",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-mutation",
        "--source-command",
        "factor-research",
        "--latest-only",
        "--accepted-only",
        "--bucket-by-source",
        "--limit",
        "7",
        "--agent",
    ])
    .unwrap();
    match mutation_cli.command {
        Commands::FactorMutationStatus(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-mutation");
            assert_eq!(args.source_command.as_deref(), Some("factor-research"));
            assert!(args.latest_only);
            assert!(args.accepted_only);
            assert!(args.bucket_by_source);
            assert_eq!(args.limit, Some(7));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let mutation_human_cli = parse_cli_from([
        "ict-engine",
        "factor-mutation-status",
        "--symbol",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match mutation_human_cli.command {
        Commands::FactorMutationStatus(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let autoresearch_status_cli = parse_cli_from([
        "ict-engine",
        "factor-autoresearch-status",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-autoresearch",
        "--session-id",
        "session-1",
        "--latest-only",
        "--limit",
        "3",
        "--agent",
    ])
    .unwrap();
    match autoresearch_status_cli.command {
        Commands::FactorAutoresearchStatus(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-autoresearch");
            assert_eq!(args.session_id.as_deref(), Some("session-1"));
            assert!(args.latest_only);
            assert_eq!(args.limit, Some(3));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let autoresearch_status_human_cli = parse_cli_from([
        "ict-engine",
        "factor-autoresearch-status",
        "--symbol",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match autoresearch_status_human_cli.command {
        Commands::FactorAutoresearchStatus(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let verdict_cli = parse_cli_from([
        "ict-engine",
        "research-verdict",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-verdict",
        "--agent",
    ])
    .unwrap();
    match verdict_cli.command {
        Commands::ResearchVerdict(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-verdict");
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let verdict_human_cli = parse_cli_from([
        "ict-engine",
        "research-verdict",
        "--symbol",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match verdict_human_cli.command {
        Commands::ResearchVerdict(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let evidence_cli = parse_cli_from([
        "ict-engine",
        "evidence-quality-breakdown",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-evidence",
        "--agent",
    ])
    .unwrap();
    match evidence_cli.command {
        Commands::EvidenceQualityBreakdown(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-evidence");
            assert!(args.refresh);
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let evidence_human_cli = parse_cli_from([
        "ict-engine",
        "evidence-quality-breakdown",
        "--symbol",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match evidence_human_cli.command {
        Commands::EvidenceQualityBreakdown(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_auto_quant_setup_commands_use_extracted_args() {
    let status_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-status",
        "--state-dir",
        "/tmp/ict-engine-aq-status",
        "--agent",
    ])
    .unwrap();
    match status_cli.command {
        Commands::AutoQuantStatus(args) => {
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-status");
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let cost_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-futures-cost",
        "--symbol",
        "NQ",
        "--price",
        "17000.5",
        "--profile",
        "cost-profile.json",
        "--human",
    ])
    .unwrap();
    match cost_cli.command {
        Commands::AutoQuantFuturesCost(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.price, 17000.5);
            assert_eq!(args.profile.as_deref(), Some("cost-profile.json"));
            assert!(args.human);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let bootstrap_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-bootstrap",
        "--state-dir",
        "/tmp/ict-engine-aq-bootstrap",
        "--repo-url",
        "https://example.invalid/auto-quant.git",
        "--tracked-branch",
        "main",
    ])
    .unwrap();
    match bootstrap_cli.command {
        Commands::AutoQuantBootstrap(args) => {
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-bootstrap");
            assert_eq!(
                args.repo_url.as_deref(),
                Some("https://example.invalid/auto-quant.git")
            );
            assert_eq!(args.tracked_branch.as_deref(), Some("main"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let update_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-update",
        "--state-dir",
        "/tmp/ict-engine-aq-update",
        "--repo-url",
        "https://example.invalid/auto-quant.git",
        "--tracked-branch",
        "develop",
        "--target-ref",
        "abc123",
    ])
    .unwrap();
    match update_cli.command {
        Commands::AutoQuantUpdate(args) => {
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-update");
            assert_eq!(
                args.repo_url.as_deref(),
                Some("https://example.invalid/auto-quant.git")
            );
            assert_eq!(args.tracked_branch.as_deref(), Some("develop"));
            assert_eq!(args.target_ref.as_deref(), Some("abc123"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let prepare_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-prepare",
        "--state-dir",
        "/tmp/ict-engine-aq-prepare",
    ])
    .unwrap();
    match prepare_cli.command {
        Commands::AutoQuantPrepare(args) => {
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-prepare");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let review_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-adoption-review",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-review",
        "--artifact-id",
        "artifact-1",
        "--sidecar-handoff",
        "/tmp/event-fundamentals.json",
        "--agent",
    ])
    .unwrap();
    match review_cli.command {
        Commands::AutoQuantAdoptionReview(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-review");
            assert_eq!(args.artifact_id.as_deref(), Some("artifact-1"));
            assert_eq!(
                args.sidecar_handoff.as_deref(),
                Some("/tmp/event-fundamentals.json")
            );
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let review_human_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-adoption-review",
        "--symbol",
        "NQ",
        "--output-format",
        "human",
    ])
    .unwrap();
    match review_human_cli.command {
        Commands::AutoQuantAdoptionReview(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let decision_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-adoption-decision",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-decision",
        "--artifact-id",
        "artifact-1",
        "--decision",
        "adopt",
        "--rationale",
        "verified",
        "--requested-by",
        "test",
    ])
    .unwrap();
    match decision_cli.command {
        Commands::AutoQuantAdoptionDecision(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-decision");
            assert_eq!(args.artifact_id.as_deref(), Some("artifact-1"));
            assert_eq!(args.decision, "adopt");
            assert_eq!(args.rationale, "verified");
            assert_eq!(args.requested_by, "test");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_auto_quant_agent_material_commands_use_extracted_args() {
    let seed_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-seed-evidence",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-seed",
        "--strategy-material-root",
        "/tmp/material-root",
        "--limit",
        "3",
    ])
    .unwrap();
    match seed_cli.command {
        Commands::AutoQuantSeedEvidence(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-seed");
            assert_eq!(args.strategy_material_root, "/tmp/material-root");
            assert_eq!(args.limit, 3);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let batch_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-agent-material-batch",
        "--symbol",
        "NQ",
        "--material",
        "/tmp/material-a.json",
        "--material",
        "/tmp/material-b.json",
        "--max-parallel",
        "2",
        "--state-dir",
        "/tmp/ict-engine-aq-material",
        "--repo-url",
        "https://example.invalid/auto-quant.git",
        "--tracked-branch",
        "main",
    ])
    .unwrap();
    match batch_cli.command {
        Commands::AutoQuantAgentMaterialBatch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(
                args.materials,
                vec![
                    "/tmp/material-a.json".to_string(),
                    "/tmp/material-b.json".to_string()
                ]
            );
            assert_eq!(args.max_parallel, 2);
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-material");
            assert_eq!(
                args.repo_url.as_deref(),
                Some("https://example.invalid/auto-quant.git")
            );
            assert_eq!(args.tracked_branch.as_deref(), Some("main"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let dispatch_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-agent-material-dispatch",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-material",
        "--group-indices",
        "0,2",
    ])
    .unwrap();
    match dispatch_cli.command {
        Commands::AutoQuantAgentMaterialDispatch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-material");
            assert_eq!(args.group_indices.as_deref(), Some("0,2"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let rank_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-agent-material-rank",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-material",
    ])
    .unwrap();
    match rank_cli.command {
        Commands::AutoQuantAgentMaterialRank(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-material");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_auto_quant_result_application_commands_use_extracted_args() {
    let import_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-results-import",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-results",
        "--library",
        "/tmp/strategy_library.json",
        "--log",
        "/tmp/run_ibkr.log",
    ])
    .unwrap();
    match import_cli.command {
        Commands::AutoQuantResultsImport(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-results");
            assert_eq!(args.library, "/tmp/strategy_library.json");
            assert_eq!(args.log.as_deref(), Some("/tmp/run_ibkr.log"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let prior_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-prior-init",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-prior",
        "--library",
        "/tmp/strategy_library.json",
        "--strategies",
        "alpha,beta",
        "--temper",
        "0.25",
        "--prior-strength",
        "6.5",
        "--parent-config",
        "1,2,3",
        "--dry-run",
        "--force",
    ])
    .unwrap();
    match prior_cli.command {
        Commands::AutoQuantPriorInit(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-prior");
            assert_eq!(args.library.as_deref(), Some("/tmp/strategy_library.json"));
            assert_eq!(
                args.strategies.as_ref().unwrap(),
                &vec!["alpha".to_string(), "beta".to_string()]
            );
            assert_eq!(args.temper, Some(0.25));
            assert_eq!(args.prior_strength, Some(6.5));
            assert_eq!(args.parent_config.as_ref().unwrap(), &vec![1, 2, 3]);
            assert!(args.dry_run);
            assert!(args.force);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let live_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-consume-live-signals",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-live",
        "--redis-url",
        "redis://127.0.0.1:6380",
        "--max-iter",
        "2",
        "--block-ms",
        "250",
        "--start-from",
        "0",
    ])
    .unwrap();
    match live_cli.command {
        Commands::AutoQuantConsumeLiveSignals(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-live");
            assert_eq!(args.redis_url, "redis://127.0.0.1:6380");
            assert_eq!(args.max_iter, Some(2));
            assert_eq!(args.block_ms, 250);
            assert_eq!(args.start_from, "0");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let trades_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-ingest-real-trades",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-trades",
        "--trades",
        "/tmp/all_real_trades.jsonl",
        "--source",
        "auto_quant_real_trades:test",
        "--dry-run",
        "--force",
    ])
    .unwrap();
    match trades_cli.command {
        Commands::AutoQuantIngestRealTrades(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-trades");
            assert_eq!(args.trades, "/tmp/all_real_trades.jsonl");
            assert_eq!(args.source, "auto_quant_real_trades:test");
            assert!(args.dry_run);
            assert!(args.force);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_auto_quant_pda_unit_commands_use_extracted_args() {
    let batch_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-pda-unit-batch",
        "--symbol",
        "NQ",
        "--objective",
        "expansion_manipulation",
        "--factors",
        "order_block,fair_value_gap",
        "--combination-size",
        "2",
        "--directions",
        "long",
        "--timeframes",
        "15m,1h",
        "--timeframe-data",
        "15m=/tmp/nq-15m.json",
        "--timeframe-data",
        "1h=/tmp/nq-1h.json",
        "--evidence-surfaces",
        "indicators,volatility",
        "--indicator-list",
        "rsi14,atr14",
        "--evidence-note",
        "needs clean HTF context",
        "--evidence-note",
        "keep observe-only",
        "--max-parallel",
        "2",
        "--state-dir",
        "/tmp/ict-engine-aq-pda",
        "--repo-url",
        "https://example.invalid/auto-quant.git",
        "--tracked-branch",
        "main",
    ])
    .unwrap();
    match batch_cli.command {
        Commands::AutoQuantPdaUnitBatch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.objective, "expansion_manipulation");
            assert_eq!(args.factors, "order_block,fair_value_gap");
            assert_eq!(args.combination_size, 2);
            assert_eq!(args.directions, "long");
            assert_eq!(args.timeframes, "15m,1h");
            assert_eq!(
                args.timeframe_data,
                vec![
                    "15m=/tmp/nq-15m.json".to_string(),
                    "1h=/tmp/nq-1h.json".to_string()
                ]
            );
            assert_eq!(args.evidence_surfaces, "indicators,volatility");
            assert_eq!(args.indicator_list, "rsi14,atr14");
            assert_eq!(
                args.evidence_notes,
                vec![
                    "needs clean HTF context".to_string(),
                    "keep observe-only".to_string()
                ]
            );
            assert_eq!(args.max_parallel, 2);
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-pda");
            assert_eq!(
                args.repo_url.as_deref(),
                Some("https://example.invalid/auto-quant.git")
            );
            assert_eq!(args.tracked_branch.as_deref(), Some("main"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let dispatch_cli = parse_cli_from([
        "ict-engine",
        "auto-quant-pda-unit-dispatch",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-aq-pda",
        "--batch-artifact-id",
        "batch-1",
        "--group-indices",
        "0,2",
    ])
    .unwrap();
    match dispatch_cli.command {
        Commands::AutoQuantPdaUnitDispatch(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-pda");
            assert_eq!(args.batch_artifact_id.as_deref(), Some("batch-1"));
            assert_eq!(args.group_indices.as_deref(), Some("0,2"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_auto_quant_promote_canonical_setup_uses_extracted_args() {
    let cli = parse_cli_from([
        "ict-engine",
        "auto-quant-promote-canonical-setup",
        "--symbol",
        "NQ",
        "--setup-name",
        "nq_liquidity_sweep_mss_v1",
        "--sequence-label",
        "liquidity_sweep -> market_structure_shift",
        "--direction",
        "bull",
        "--sweep-id",
        "sweep-1",
        "--horizon-bars",
        "42",
        "--state-dir",
        "/tmp/ict-engine-aq-promote",
    ])
    .unwrap();
    match cli.command {
        Commands::AutoQuantPromoteCanonicalSetup(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.setup_name, "nq_liquidity_sweep_mss_v1");
            assert_eq!(
                args.sequence_label,
                "liquidity_sweep -> market_structure_shift"
            );
            assert_eq!(args.direction.as_deref(), Some("bull"));
            assert_eq!(args.sweep_id.as_deref(), Some("sweep-1"));
            assert_eq!(args.horizon_bars, 42);
            assert_eq!(args.state_dir, "/tmp/ict-engine-aq-promote");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_regime_confidence_assets_accepts_output_format() {
    let cli = parse_cli_from([
        "ict-engine",
        "regime-confidence-assets",
        "--output-format",
        "json",
    ])
    .unwrap();
    match cli.command {
        Commands::RegimeConfidenceAssets(args) => {
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_asset_closure_intake_requires_symbol() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-asset-closure-intake",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--output-format",
        "json",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorAssetClosureIntake(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.output_format, "json");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_factor_autoresearch_accepts_provider_profile() {
    let cli = parse_cli_from([
        "ict-engine",
        "factor-autoresearch",
        "--symbol",
        "NQ",
        "--data",
        "candles.json",
        "--profile",
        "thrill3r-nq-closed-loop-v1",
    ])
    .unwrap();
    match cli.command {
        Commands::FactorAutoresearch(args) => {
            assert_eq!(args.profile.as_deref(), Some("thrill3r-nq-closed-loop-v1"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_env_command_parses() {
    let cli = parse_cli_from(["ict-engine", "env", "--agent"]).unwrap();
    match cli.command {
        Commands::Env(args) => assert!(args.agent),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let human_cli = parse_cli_from(["ict-engine", "env", "--output-format", "human"]).unwrap();
    match human_cli.command {
        Commands::Env(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_env_report_helpers_live_in_owner_module() {
    let report = crate::env_command::build_env_report();
    assert_eq!(
        report["state_dir_env_var"],
        crate::state_dir::STATE_DIR_ENV_VAR
    );
    assert_eq!(
        report["default_state_dir"],
        crate::state_dir::DEFAULT_STATE_DIR
    );
    assert!(report["variables"]
        .as_array()
        .unwrap()
        .iter()
        .any(|item| item["name"] == crate::state_dir::STATE_DIR_ENV_VAR));
}

#[test]
fn test_auto_quant_output_dir_helpers_live_in_owner_module() {
    assert_eq!(
        crate::auto_quant_command::DEFAULT_AUTO_QUANT_SUBDIR,
        "auto-quant"
    );
    assert_eq!(
        crate::auto_quant_command::resolve_auto_quant_output_dir("/tmp/ict-engine-aq-owner"),
        "/tmp/ict-engine-aq-owner/auto-quant"
    );
}

#[test]
fn test_auto_quant_futures_cost_shell_lives_in_owner_module() {
    fn assert_futures_cost_owner(_: fn(&str, f64, Option<&str>, &str) -> anyhow::Result<()>) {}

    assert_futures_cost_owner(crate::auto_quant_command::auto_quant_futures_cost_shell);
}

#[test]
fn test_update_agent_prompt_builder_lives_in_update_command_module() {
    let update_source = include_str!("update_command.rs");
    assert!(update_source.contains("pub(crate) fn build_update_agent_prompts("));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn build_update_agent_prompts("),
        "build_update_agent_prompts should not be defined in src/main.rs"
    );
    assert!(
        !main_source.contains("struct BuildUpdateAgentPromptsInput"),
        "BuildUpdateAgentPromptsInput should not be defined in src/main.rs"
    );
}

#[test]
fn test_analyze_agent_prompt_builder_lives_in_analyze_shared_module() {
    let analyze_shared_source = include_str!("analyze_shared.rs");
    assert!(analyze_shared_source.contains("pub(crate) fn build_analyze_agent_prompts("));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn build_analyze_agent_prompts("),
        "build_analyze_agent_prompts should not be defined in src/main.rs"
    );
    assert!(
        !main_source.contains("struct BuildAnalyzeAgentPromptsInput"),
        "BuildAnalyzeAgentPromptsInput should not be defined in src/main.rs"
    );
}

#[test]
fn test_analyze_signal_rankings_lives_in_analyze_shared_module() {
    let analyze_shared_source = include_str!("analyze_shared.rs");
    assert!(analyze_shared_source.contains("pub(crate) fn analyze_signal_rankings("));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn analyze_signal_rankings("),
        "analyze_signal_rankings should not be defined in src/main.rs"
    );
}

#[test]
fn test_executor_summary_formatter_lives_in_output_foundation_module() {
    let lines = ict_engine::application::output_foundation::format_executor_summary_lines(&[
        "executor=catboost_file action=observe confidence=0.55".to_string(),
    ]);

    assert_eq!(lines.len(), 1);
    assert!(lines[0].contains("executor=catboost_file"));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn format_executor_summary_lines("),
        "format_executor_summary_lines should not be defined in src/main.rs"
    );
}

#[test]
fn test_resolved_vote_scorecards_lives_in_orchestration_and_preserves_vote_source() {
    let vote = ict_engine::state::EnsembleVoteRecord {
        executor_scorecards: vec![ict_engine::state::EnsembleExecutorScorecard {
            executor: "catboost_stub".to_string(),
            ..ict_engine::state::EnsembleExecutorScorecard::default()
        }],
        executor_scorecards_source: Some("vote_snapshot".to_string()),
        ..ict_engine::state::EnsembleVoteRecord::default()
    };

    let (fallback_scorecards, fallback_source) =
        ict_engine::application::orchestration::resolved_vote_scorecards(&[], &vote);
    assert_eq!(fallback_scorecards[0].executor, "catboost_stub");
    assert_eq!(fallback_source, "vote_snapshot");

    let persisted = vec![ict_engine::state::EnsembleExecutorScorecard {
        executor: "catboost_file".to_string(),
        ..ict_engine::state::EnsembleExecutorScorecard::default()
    }];
    let (persisted_scorecards, persisted_source) =
        ict_engine::application::orchestration::resolved_vote_scorecards(&persisted, &vote);
    assert_eq!(persisted_scorecards[0].executor, "catboost_file");
    assert_eq!(persisted_source, "persisted");

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn resolved_vote_scorecards"),
        "resolved_vote_scorecards should not be defined in src/main.rs"
    );
}

#[test]
fn test_multi_timeframe_phase_hint_lives_in_multi_timeframe_owner() {
    let summary = vec![
        "multi_timeframe_source=explicit_with_auto_fill".to_string(),
        "higher_timeframe_direction_bias=bullish".to_string(),
        "higher_timeframe_alignment_score=0.625".to_string(),
        "lower_timeframe_entry_alignment_score=0.500".to_string(),
    ];

    let hint =
        ict_engine::application::multi_timeframe_inputs::multi_timeframe_phase_hint(&summary);

    assert_eq!(
        hint,
        "mtf_source=explicit_with_auto_fill mtf_direction=bullish mtf_alignment=0.625 mtf_entry_alignment=0.500"
    );

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn multi_timeframe_phase_hint("),
        "multi_timeframe_phase_hint should not be defined in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_branch_helpers_live_in_orchestration_owner() {
    let expression = serde_json::json!({
        "branch_path_contract": {
            "regime_profit_branch_path": "TrendExpansion -> VolatilityCompression -> iv_hv_compression_regime -> family_f_vrp_real_ivhv_qqq_observation_v1"
        }
    });

    let fields = ict_engine::application::orchestration::resolve_factor_candidate_branch_fields(
        &expression,
        "fallback_main",
        "fallback_sub".to_string(),
        "fallback_leaf".to_string(),
        "fallback_profit".to_string(),
    );

    assert_eq!(fields.main_regime, "TrendExpansion");
    assert_eq!(fields.sub_regime, "VolatilityCompression");
    assert_eq!(
        fields.sub_sub_regime_or_profit_factor,
        "iv_hv_compression_regime"
    );
    assert_eq!(
        fields.profit_factor,
        "family_f_vrp_real_ivhv_qqq_observation_v1"
    );
    assert_eq!(
        fields.regime_profit_branch_path,
        "TrendExpansion -> VolatilityCompression -> iv_hv_compression_regime -> family_f_vrp_real_ivhv_qqq_observation_v1"
    );
    assert_eq!(
        ict_engine::application::orchestration::candidate_pack_root_slug(
            "support/examples/factor_candidate_packs/Curated Auto Quant!"
        ),
        "curated-auto-quant"
    );

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn resolve_factor_candidate_branch_fields("),
        "resolve_factor_candidate_branch_fields should not be defined in src/main.rs"
    );
    assert!(
        !main_source.contains("fn candidate_pack_root_slug("),
        "candidate_pack_root_slug should not be defined in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_admission_target_builder_lives_in_orchestration_owner() {
    let artifact =
        ict_engine::application::orchestration::build_factor_candidate_admission_target_artifact(
            "support/examples/factor_candidate_packs/curated-auto-quant-v1",
            "FACTOR_CANDIDATES",
        )
        .unwrap();

    assert_eq!(artifact.rows.len(), 41);
    assert_eq!(
        artifact.candidate_set_id,
        "factor-candidate-admission:FACTOR_CANDIDATES:curated-auto-quant-v1"
    );
    assert!(artifact.rows.iter().any(|row| {
        row.regime_profit_branch_path
            .as_deref()
            .is_some_and(|value| {
                value
                    == "Transition -> LiquiditySweep -> sweep_reclaim_small_cycle -> liquidity_sweep_reclaim_15m_wide_v1"
            })
    }));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn build_factor_candidate_admission_target_artifact("),
        "build_factor_candidate_admission_target_artifact should not be defined in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_pack_inventory_builder_lives_in_orchestration_owner() {
    let payload = ict_engine::application::orchestration::build_factor_candidate_pack_inventory(
        "support/examples/factor_candidate_packs/curated-auto-quant-v1",
    )
    .unwrap();

    assert_eq!(payload["summary"]["candidate_pack_count"].as_u64(), Some(8));
    let candidates = payload["candidates"].as_array().unwrap();
    assert!(candidates.iter().any(|candidate| {
        candidate["candidate_id"].as_str() == Some("family_f_vrp_compression_15m_v1")
            && candidate["aggregate_trade_count"].as_u64() == Some(334)
            && candidate["transfer_status"].as_str() == Some("cross_market_candidate")
    }));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn build_factor_candidate_pack_inventory("),
        "build_factor_candidate_pack_inventory should not be defined in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_trainer_artifact_payloads_live_in_orchestration_owner() {
    let artifact =
        ict_engine::application::orchestration::build_factor_candidate_admission_target_artifact(
            "support/examples/factor_candidate_packs/curated-auto-quant-v1",
            "FACTOR_CANDIDATES",
        )
        .unwrap();
    let summary =
        ict_engine::application::orchestration::structural_path_ranking_target_export_summary(
            ict_engine::application::orchestration::StructuralPathRankingTargetExportSummaryInput {
                state_dir: "/tmp/ict-engine-cli-surface-test",
                symbol: "FACTOR_CANDIDATES",
                artifact: &artifact,
                csv_name: "policy_training/structural_path_ranking_target.csv",
                jsonl_name: "policy_training/structural_path_ranking_target.jsonl",
                history_csv_name: "policy_training/structural_path_ranking_target_history.csv",
                history_jsonl_name: "policy_training/structural_path_ranking_target_history.jsonl",
                history_rows: &artifact.rows,
                summary_name: "policy_training/structural_path_ranking_target_summary.json",
            },
        );

    let model =
        ict_engine::application::orchestration::build_factor_candidate_ranker_direct_model_artifact(
        );
    assert_eq!(
        model["model_family"].as_str(),
        Some("weighted_feature_sum_v1")
    );
    assert_eq!(
        model["notes"][0].as_str(),
        Some("generated_by=factor-candidate-admission-targets")
    );

    let trainer = ict_engine::application::orchestration::build_factor_candidate_trainer_artifact(
        &summary,
        "2026-05-22T00:00:00Z",
    );
    assert_eq!(
        trainer["protocol_version"].as_str(),
        Some("structural-path-ranking-trainer-artifact-v1")
    );
    assert_eq!(
        trainer["dataset_role"].as_str(),
        Some(summary.trainer_manifest.dataset_role.as_str())
    );
    assert_eq!(
        trainer["trained_rows"].as_u64(),
        Some(summary.rows_with_training_weight as u64)
    );
    assert_eq!(trainer["created_at"].as_str(), Some("2026-05-22T00:00:00Z"));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("\"protocol_version\": \"structural-path-ranker-direct-model-v1\""),
        "factor-candidate direct model JSON should not be constructed in src/main.rs"
    );
    assert!(
        !main_source
            .contains("\"protocol_version\": \"structural-path-ranking-trainer-artifact-v1\""),
        "factor-candidate trainer artifact JSON should not be constructed in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_trainer_artifact_writer_lives_in_orchestration_owner() {
    let temp = tempfile::tempdir().unwrap();
    let artifact =
        ict_engine::application::orchestration::build_factor_candidate_admission_target_artifact(
            "support/examples/factor_candidate_packs/curated-auto-quant-v1",
            "FACTOR_CANDIDATES",
        )
        .unwrap();
    let summary =
        ict_engine::application::orchestration::structural_path_ranking_target_export_summary(
            ict_engine::application::orchestration::StructuralPathRankingTargetExportSummaryInput {
                state_dir: temp.path().to_str().unwrap(),
                symbol: "FACTOR_CANDIDATES",
                artifact: &artifact,
                csv_name: "policy_training/structural_path_ranking_target.csv",
                jsonl_name: "policy_training/structural_path_ranking_target.jsonl",
                history_csv_name: "policy_training/structural_path_ranking_target_history.csv",
                history_jsonl_name: "policy_training/structural_path_ranking_target_history.jsonl",
                history_rows: &artifact.rows,
                summary_name: "policy_training/structural_path_ranking_target_summary.json",
            },
        );

    ict_engine::application::orchestration::write_factor_candidate_trainer_artifacts(
        temp.path().to_str().unwrap(),
        "FACTOR_CANDIDATES",
        &summary,
    )
    .unwrap();

    let model_path = temp
        .path()
        .join("FACTOR_CANDIDATES/policy_training/factor_candidate_ranker_direct_model.json");
    let trainer_path = temp
        .path()
        .join("FACTOR_CANDIDATES/policy_training/structural_path_ranking_trainer_artifact.json");
    assert!(model_path.exists());
    assert!(trainer_path.exists());
    let ledger = ict_engine::state::load_artifact_ledger(temp.path(), "FACTOR_CANDIDATES").unwrap();
    assert!(ledger.iter().any(|entry| entry.artifact_kind
        == "structural_path_ranking_trainer_artifact"
        && entry.status == "ready_observation_only"));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn write_factor_candidate_trainer_artifacts("),
        "write_factor_candidate_trainer_artifacts should not be defined in src/main.rs"
    );
}

#[test]
fn test_factor_candidate_pack_inventory_persistence_lives_in_orchestration_owner() {
    let temp = tempfile::tempdir().unwrap();
    let payload = ict_engine::application::orchestration::build_factor_candidate_pack_inventory(
        "support/examples/factor_candidate_packs/curated-auto-quant-v1",
    )
    .unwrap();

    let path = ict_engine::application::orchestration::persist_factor_candidate_pack_inventory(
        temp.path().to_str().unwrap(),
        "FACTOR_CANDIDATES",
        &payload,
    )
    .unwrap();

    assert!(std::path::Path::new(&path).exists());
    let ledger = ict_engine::state::load_artifact_ledger(temp.path(), "FACTOR_CANDIDATES").unwrap();
    assert!(ledger.iter().any(
        |entry| entry.artifact_kind == "factor_candidate_pack_inventory"
            && entry.status == "ready"
            && entry.top_factor_action.as_deref() == Some("inspect")
    ));

    let main_source = include_str!("main.rs");
    assert!(
        !main_source.contains("fn persist_factor_candidate_pack_inventory("),
        "persist_factor_candidate_pack_inventory should not be defined in src/main.rs"
    );
}

#[test]
fn test_emit_analyze_output_adapter_lives_in_analyze_command_module() {
    fn assert_emit_adapter_owner(
        _: fn(
            &ict_engine::analyze_report_shell::AnalyzeReport,
            crate::output_format::OutputFormat,
            bool,
        ) -> anyhow::Result<()>,
    ) {
    }

    assert_emit_adapter_owner(crate::analyze_command::emit_analyze_output);
}

#[test]
fn test_cli_core_runtime_commands_use_extracted_args() {
    let validate_cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
        "--window-size",
        "64",
        "--step-size",
        "4",
        "--verbose",
        "--compact",
        "--no-enhanced",
        "--config",
        "market-state.json",
        "--profile",
        "high_confidence",
    ])
    .unwrap();
    match validate_cli.command {
        Commands::ValidateMarketState(args) => {
            assert_eq!(args.data, "candles.json");
            assert_eq!(args.window_size, 64);
            assert_eq!(args.step_size, 4);
            assert!(args.verbose);
            assert!(args.compact);
            assert!(args.no_enhanced);
            assert_eq!(args.config.as_deref(), Some("market-state.json"));
            assert_eq!(args.profile.as_deref(), Some("high_confidence"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let train_cli = parse_cli_from([
        "ict-engine",
        "train",
        "--symbol",
        "NQ",
        "--data",
        "train-candles.json",
        "--epochs",
        "7",
        "--state-dir",
        "/tmp/ict-engine-train-state",
    ])
    .unwrap();
    match train_cli.command {
        Commands::Train(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data, "train-candles.json");
            assert_eq!(args.epochs, 7);
            assert_eq!(args.state_dir, "/tmp/ict-engine-train-state");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let update_cli = parse_cli_from([
        "ict-engine",
        "update",
        "--symbol",
        "NQ",
        "--outcome",
        "win",
        "--entry-signal",
        "strong_sell",
        "--state-dir",
        "/tmp/ict-engine-update-state",
        "--pnl",
        "125.5",
        "--regime",
        "trend",
        "--direction",
        "short",
        "--feedback-file",
        "feedback.json",
        "--ensemble",
    ])
    .unwrap();
    match update_cli.command {
        Commands::Update(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.outcome, "win");
            assert_eq!(args.entry_signal, "strong_sell");
            assert_eq!(args.state_dir, "/tmp/ict-engine-update-state");
            assert_eq!(args.pnl, Some(125.5));
            assert_eq!(args.regime.as_deref(), Some("trend"));
            assert_eq!(args.direction.as_deref(), Some("short"));
            assert_eq!(args.feedback_file.as_deref(), Some("feedback.json"));
            assert!(args.ensemble);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_validate_market_state_accepts_zero_config_defaults() {
    let cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
    ])
    .unwrap();

    match cli.command {
        Commands::ValidateMarketState(args) => {
            assert_eq!(args.data, "candles.json");
            assert_eq!(args.window_size, 100);
            assert_eq!(args.step_size, 1);
            assert!(!args.verbose);
            assert!(!args.compact);
            assert!(!args.no_enhanced);
            assert!(args.config.is_none());
            assert!(args.profile.is_none());
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_validate_market_state_accepts_compact_flag() {
    let cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
        "--compact",
    ])
    .unwrap();

    match cli.command {
        Commands::ValidateMarketState(args) => assert!(args.compact),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_validate_market_state_accepts_output_aliases() {
    let human_cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
        "--human",
    ])
    .unwrap();
    match human_cli.command {
        Commands::ValidateMarketState(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let format_cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
        "--output-format",
        "compact",
    ])
    .unwrap();
    match format_cli.command {
        Commands::ValidateMarketState(args) => assert_eq!(args.output_format, "compact"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_validate_market_state_accepts_high_confidence_profile() {
    let cli = parse_cli_from([
        "ict-engine",
        "validate-market-state",
        "--data",
        "candles.json",
        "--profile",
        "high_confidence",
    ])
    .unwrap();

    match cli.command {
        Commands::ValidateMarketState(args) => {
            assert_eq!(args.profile.as_deref(), Some("high_confidence"));
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_recommended_next_command_meta_classifies_ask_user_gate() {
    let meta = recommended_next_command_meta(
        "ask-user: Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json | blocked until user_selected_historical_data | then ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state"
    );
    assert!(meta.requires_user_input);
    assert!(meta.blocked);
    assert_eq!(
        meta.prompt.as_deref(),
        Some(
            "Before using historical data for NQ again, ask the user which dataset to use. recorded_paths=/tmp/a.json, /tmp/b.json"
        )
    );
    assert_eq!(
        meta.executable_command.as_deref(),
        Some("ict-engine factor-research --symbol NQ --data /tmp/a.json --state-dir state")
    );
    assert_eq!(meta.recorded_data_paths.len(), 2);
}

#[test]
fn test_recommended_next_command_meta_classifies_ict_engine_command() {
    let meta = recommended_next_command_meta(
        "ict-engine workflow-status --symbol NQ --state-dir state --phase artifact-consumed-gate",
    );
    assert!(!meta.requires_user_input);
    assert!(!meta.blocked);
    assert_eq!(
        meta.executable_command.as_deref(),
        Some("ict-engine workflow-status --symbol NQ --state-dir state --phase artifact-consumed-gate")
    );
}

#[test]
fn test_output_format_resolve_rejects_human_and_explicit_json_mix() {
    let error = resolve_output_format("json", false, false, true).unwrap_err();
    assert!(error
        .to_string()
        .contains("do not combine --output-format with --compact/--agent/--human"));
}

#[test]
fn test_output_format_resolve_rejects_compact_and_explicit_json_mix() {
    let error = resolve_output_format("json", true, false, false).unwrap_err();
    assert!(error
        .to_string()
        .contains("do not combine --output-format with --compact/--agent/--human"));
}

#[test]
fn test_output_format_resolve_allows_alias_with_default_empty_value() {
    let resolved = resolve_output_format("", false, false, true).unwrap();
    assert_eq!(resolved, OutputFormat::Human);
}

#[test]
fn test_output_format_resolve_empty_defaults_to_json() {
    let resolved = resolve_output_format("", false, false, false).unwrap();
    assert_eq!(resolved, OutputFormat::Json);
}

#[test]
fn test_output_format_types_live_in_owner_module() {
    let resolved = crate::output_format::resolve_output_format("", false, true, false).unwrap();
    assert_eq!(resolved, crate::output_format::OutputFormat::Agent);
}

#[test]
fn test_output_format_agent_preserving_label_lives_in_owner_module() {
    assert_eq!(
        crate::output_format::output_format_label(crate::output_format::OutputFormat::Agent),
        "agent"
    );
    assert_eq!(
        crate::output_format::output_format_label(crate::output_format::OutputFormat::Human),
        "human"
    );
}

#[test]
fn test_state_dir_helpers_live_in_owner_module() {
    assert_eq!(crate::state_dir::DEFAULT_STATE_DIR, "state");
    assert_eq!(crate::state_dir::STATE_DIR_ENV_VAR, "ICT_ENGINE_STATE_DIR");
    let temp = tempfile::tempdir().unwrap();
    let state_dir = temp.path().join("state-dir-owner-check");
    crate::state_dir::ensure_state_dir_ready(state_dir.to_str().unwrap()).unwrap();
    assert!(state_dir.exists());
}

#[test]
fn test_cli_analyze_accepts_json_alias_mix_at_parse_level() {
    let cli = parse_cli_from([
        "ict-engine",
        "analyze",
        "--symbol",
        "DEMO",
        "--demo",
        "--human",
        "--output-format",
        "json",
    ]);
    assert!(
        cli.is_ok(),
        "cli parse should succeed; runtime guard handles conflict"
    );
}

#[test]
fn test_cli_analyze_default_output_format_is_empty_sentinel() {
    let cli = parse_cli_from(["ict-engine", "analyze", "--symbol", "DEMO", "--demo"]).unwrap();
    match cli.command {
        Commands::Analyze(args) => assert_eq!(args.output_format, ""),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_analyze_commands_use_extracted_args() {
    let analyze_cli = parse_cli_from([
        "ict-engine",
        "analyze",
        "--symbol",
        "NQ",
        "--data-htf",
        "htf.json",
        "--data-mtf",
        "mtf.json",
        "--data-ltf",
        "ltf.json",
        "--data-root",
        "/tmp/ict-engine-data",
        "--demo",
        "--state-dir",
        "/tmp/ict-engine-analyze-state",
        "--output-format",
        "agent",
        "--inline-ledger",
        "--no-execution-focus",
        "--regime-consumer-bundle",
        "bundle.json",
        "--regime-consumer-bundle-strict",
        "--apply-regime-bundle-bbn-soft-evidence",
        "--structure-events",
        "structure-events.json",
    ])
    .unwrap();

    match analyze_cli.command {
        Commands::Analyze(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.data_htf.as_deref(), Some("htf.json"));
            assert_eq!(args.data_mtf.as_deref(), Some("mtf.json"));
            assert_eq!(args.data_ltf.as_deref(), Some("ltf.json"));
            assert_eq!(args.data_root.as_deref(), Some("/tmp/ict-engine-data"));
            assert!(args.demo);
            assert_eq!(args.state_dir, "/tmp/ict-engine-analyze-state");
            assert_eq!(args.output_format, "agent");
            assert!(args.inline_ledger);
            assert!(args.no_execution_focus);
            assert_eq!(args.regime_consumer_bundle.as_deref(), Some("bundle.json"));
            assert!(args.regime_consumer_bundle_strict);
            assert!(args.apply_regime_bundle_bbn_soft_evidence);
            assert_eq!(
                args.structure_events.as_deref(),
                Some("structure-events.json")
            );
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let live_cli = parse_cli_from([
        "ict-engine",
        "analyze-live",
        "--symbol",
        "NQ",
        "--futures-symbol",
        "NQ=F",
        "--spot-symbol",
        "QQQ",
        "--options-symbol",
        "QQQ",
        "--options-volatility-proxy-symbol",
        "VIX",
        "--spot-kind",
        "etf",
        "--futures-backend",
        "yfinance",
        "--aux-backend",
        "yfinance",
        "--external-http-base-url",
        "http://127.0.0.1:6901/api/v1",
        "--crypto-public-base-url",
        "http://127.0.0.1:8080",
        "--state-dir",
        "/tmp/ict-engine-analyze-live-state",
        "--output-format",
        "human",
        "--regime-consumer-bundle",
        "bundle.json",
        "--regime-consumer-bundle-strict",
        "--apply-regime-bundle-bbn-soft-evidence",
    ])
    .unwrap();

    match live_cli.command {
        Commands::AnalyzeLive(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.futures_symbol.as_deref(), Some("NQ=F"));
            assert_eq!(args.spot_symbol.as_deref(), Some("QQQ"));
            assert_eq!(args.options_symbol.as_deref(), Some("QQQ"));
            assert_eq!(args.options_volatility_proxy_symbol.as_deref(), Some("VIX"));
            assert_eq!(args.spot_kind.as_deref(), Some("etf"));
            assert_eq!(args.futures_backend, "yfinance");
            assert_eq!(args.aux_backend, "yfinance");
            assert_eq!(args.external_http_base_url, "http://127.0.0.1:6901/api/v1");
            assert_eq!(args.crypto_public_base_url, "http://127.0.0.1:8080");
            assert_eq!(args.state_dir, "/tmp/ict-engine-analyze-live-state");
            assert_eq!(args.output_format, "human");
            assert_eq!(args.regime_consumer_bundle.as_deref(), Some("bundle.json"));
            assert!(args.regime_consumer_bundle_strict);
            assert!(args.apply_regime_bundle_bbn_soft_evidence);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_workflow_status_accepts_stable_flag() {
    let cli = parse_cli_from([
        "ict-engine",
        "workflow-status",
        "--symbol",
        "NQ",
        "--stable",
    ])
    .unwrap();

    match cli.command {
        Commands::WorkflowStatus(args) => {
            assert!(args.stable);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_workflow_status_uses_extracted_args() {
    let cli = parse_cli_from([
        "ict-engine",
        "workflow-status",
        "--symbol",
        "NQ",
        "--state-dir",
        "/tmp/ict-engine-workflow",
        "--profile",
        "demo-profile",
        "--phase",
        "artifact-consumed-gate",
        "--actionable-only",
        "--conflicts-only",
        "--latest-promotable",
        "--hard-block-only",
        "--hard-block-reason",
        "provider",
        "--limit",
        "5",
        "--agent",
        "--stable",
        "--no-execution-focus",
    ])
    .unwrap();

    match cli.command {
        Commands::WorkflowStatus(args) => {
            assert_eq!(args.symbol, "NQ");
            assert_eq!(args.state_dir, "/tmp/ict-engine-workflow");
            assert_eq!(args.profile.as_deref(), Some("demo-profile"));
            assert_eq!(args.phase.as_deref(), Some("artifact-consumed-gate"));
            assert!(args.actionable_only);
            assert!(args.conflicts_only);
            assert!(args.latest_promotable);
            assert!(args.hard_block_only);
            assert_eq!(args.hard_block_reason.as_deref(), Some("provider"));
            assert_eq!(args.limit, Some(5));
            assert!(args.agent);
            assert!(args.stable);
            assert!(args.no_execution_focus);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_pre_bayes_status_accepts_agent_alias() {
    let cli = parse_cli_from([
        "ict-engine",
        "pre-bayes-status",
        "--symbol",
        "DEMO",
        "--agent",
    ])
    .unwrap();

    match cli.command {
        Commands::PreBayesStatus(args) => {
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_provider_status_accepts_output_aliases() {
    let human = parse_cli_from(["ict-engine", "provider-status", "--human"]).unwrap();
    match human.command {
        Commands::ProviderStatus(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let jsonl = parse_cli_from([
        "ict-engine",
        "provider-status",
        "--domain",
        "market_data",
        "--output-format",
        "jsonl",
    ])
    .unwrap();
    match jsonl.command {
        Commands::ProviderStatus(args) => {
            assert_eq!(args.domain.as_deref(), Some("market_data"));
            assert_eq!(args.output_format, "jsonl");
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_provider_status_output_format_rejects_alias_mix() {
    let error = crate::status_command::resolve_provider_status_output_format(
        "json", true, false, false, false,
    )
    .unwrap_err();
    assert!(error
        .to_string()
        .contains("do not combine --output-format with --compact/--agent/--human/--jsonl"));
}

#[test]
fn test_cli_status_commands_use_extracted_args() {
    let pre_bayes = parse_cli_from([
        "ict-engine",
        "pre-bayes-status",
        "--symbol",
        "DEMO",
        "--state-dir",
        "/tmp/ict-engine-test",
        "--human",
    ])
    .unwrap();
    match pre_bayes.command {
        Commands::PreBayesStatus(args) => {
            assert_eq!(args.symbol, "DEMO");
            assert_eq!(args.state_dir, "/tmp/ict-engine-test");
            assert!(args.human);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let provider = parse_cli_from([
        "ict-engine",
        "provider-status",
        "--domain",
        "live_runtime",
        "--provider",
        "yfinance",
        "--profile",
        "demo-profile",
        "--agent",
    ])
    .unwrap();
    match provider.command {
        Commands::ProviderStatus(args) => {
            assert_eq!(args.domain.as_deref(), Some("live_runtime"));
            assert_eq!(args.provider.as_deref(), Some("yfinance"));
            assert_eq!(args.profile.as_deref(), Some("demo-profile"));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_more_status_commands_use_extracted_args() {
    let policy_training = parse_cli_from([
        "ict-engine",
        "policy-training-status",
        "--symbol",
        "DEMO",
        "--state-dir",
        "/tmp/ict-engine-policy",
        "--entry-model",
        "demo-entry",
        "--agent",
    ])
    .unwrap();
    match policy_training.command {
        Commands::PolicyTrainingStatus(args) => {
            assert_eq!(args.symbol, "DEMO");
            assert_eq!(args.state_dir, "/tmp/ict-engine-policy");
            assert_eq!(args.entry_model.as_deref(), Some("demo-entry"));
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let pre_bayes_diff = parse_cli_from([
        "ict-engine",
        "pre-bayes-diff",
        "--symbol",
        "DEMO",
        "--state-dir",
        "/tmp/ict-engine-diff",
        "--agent",
    ])
    .unwrap();
    match pre_bayes_diff.command {
        Commands::PreBayesDiff(args) => {
            assert_eq!(args.symbol, "DEMO");
            assert_eq!(args.state_dir, "/tmp/ict-engine-diff");
            assert!(args.refresh);
            assert!(args.agent);
        }
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let pre_bayes_diff_human = parse_cli_from([
        "ict-engine",
        "pre-bayes-diff",
        "--symbol",
        "DEMO",
        "--output-format",
        "human",
    ])
    .unwrap();
    match pre_bayes_diff_human.command {
        Commands::PreBayesDiff(args) => assert_eq!(args.output_format, "human"),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

#[test]
fn test_cli_artifact_commands_accept_output_aliases() {
    let status = parse_cli_from([
        "ict-engine",
        "artifact-status",
        "--symbol",
        "DEMO",
        "--agent",
    ])
    .unwrap();
    match status.command {
        Commands::ArtifactStatus(args) => assert!(args.agent),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let lineage = parse_cli_from([
        "ict-engine",
        "artifact-lineage",
        "--symbol",
        "DEMO",
        "--human",
    ])
    .unwrap();
    match lineage.command {
        Commands::ArtifactLineage(args) => assert!(args.human),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }

    let diff = parse_cli_from([
        "ict-engine",
        "artifact-diff",
        "--symbol",
        "DEMO",
        "--left-artifact-id",
        "left",
        "--right-artifact-id",
        "right",
        "--compact",
    ])
    .unwrap();
    match diff.command {
        Commands::ArtifactDiff(args) => assert!(args.compact),
        other => panic!("unexpected command: {:?}", std::mem::discriminant(&other)),
    }
}

fn parse_cli_from<const N: usize>(args: [&str; N]) -> Result<Cli, clap::Error> {
    let owned = args.into_iter().map(str::to_string).collect::<Vec<_>>();
    std::thread::Builder::new()
        .stack_size(16 * 1024 * 1024)
        .spawn(move || Cli::try_parse_from(owned))
        .expect("spawn parse thread")
        .join()
        .expect("join parse thread")
}
