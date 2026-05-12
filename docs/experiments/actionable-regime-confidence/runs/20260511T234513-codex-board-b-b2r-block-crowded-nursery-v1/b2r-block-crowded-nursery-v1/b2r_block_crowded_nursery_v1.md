# B2R Block-Crowded Nursery Packet v1

Run id: `20260511T234513+0800-codex-board-b-b2r-block-crowded-nursery-v1`
Source exact readback: `20260511T231800+0800-codex-board-b-220646-exact-branch-closed-loop-readback-v4`
Source feedback packet: `20260511T233358+0800-codex-board-b-220646-block-crowded-feedback-packet-v1`

## Nursery Row

- Status: `incubation_only`
- Branch: `Crisis -> CrisisReliefCarry -> StopManagedPanicRecovery -> SourceRootStopCarryLongHorizonV1:crisis_carry_h8_sl048_tp12`
- Action leaf: `suppress_or_wait_when_block_crowded`
- Why keep exploring: The exact Crisis branch passed RC-SPA and preserved identity through Pre-Bayes, BBN soft evidence, CatBoost/path-ranker, and execution-candidate, but execution-tree blocked it under RangeConsolidation/WideRange with crowded readiness. Treat this as negative execution-admissibility feedback, not a profitability rejection.
- Promotion blocker: `promotion_not_allowed: execution_tree_block_crowded; source readiness 0.4433 < 0.45; current execution_readiness=0.4471 -> gate_status=blocked; incubation_only until repeated and admitted by execution tree`

## Real Chain Readback

- Auto-Quant recipe imported: exit `0`; total trades `12329`.
- Pre-Bayes/filter: `{'exit': 0, 'gating_status': 'pass_neutralized', 'policy': '318900600c5e8cf2'}`
- BBN soft evidence: `{'status': 'skipped', 'soft_market_regime_distribution': {'bear': 0.0, 'bull': 0.0, 'range': 1.0}}`
- CatBoost/path-ranker: `{'ranker_validation_ready': True, 'path_ranker_score_visible_to_execution_tree': True, 'path_ranker_score_used_by_execution_tree': True, 'policy_training_exit': 0, 'policy_training_status_shape': ['analyze_runs', 'entry_models', 'factor_hotplug_summary', 'structural_path_ranking_runtime', 'structural_path_ranking_runtime_summary', 'structural_path_ranking_target', 'structural_path_ranking_validation', 'structural_path_ranking_validation_summary', 'summary_line', 'symbol', 'update_runs']}`
- Execution tree: `{'analyze_live_exit': 0, 'workflow_bundle_exit': 0, 'workflow_execution_candidate_exit': 0, 'branch': 'block_crowded', 'gate_status': 'blocked', 'execution_bias': 'skip', 'decision_hint': 'execution_blocked_regardless_of_prediction', 'consumer_reason': 'market_state=RangeConsolidation/WideRange | execution=blocked/block_crowded/skip | ranker=history_path/unknown/ready', 'readiness_line': 'execution_readiness=0.4471 -> gate_status=blocked', 'branch_path_preserved': True, 'workflow_bundle_keys': ['candidate_set_id', 'candidate_set_size', 'composite_score', 'confirmation_summary', 'current_posterior', 'direction', 'experience_prior', 'historical_invalidation_rate', 'historical_total_records', 'invalidation_summary', 'path_id', 'path_label'], 'workflow_candidate_keys': ['actionable', 'artifact_id', 'candidate_status', 'decision_hint', 'generated_at', 'multi_timeframe_summary', 'path', 'posterior_delta', 'pre_bayes_bridge_selected_entry_quality', 'pre_bayes_gate_status', 'review_reason', 'review_rule_version']}`

## Provider Panel

- `ibkr_bridge`: ready=False status=configured_runtime_unhealthy reason=ibkr_bridge_runtime_dependencies_missing_with_gateway_reachable
- `kraken_cli`: ready=True status=ready reason=kraken_cli_config_detected
- `kraken_public`: ready=False status=configured_runtime_unhealthy reason=python3_provider_dependencies_missing
- `tradingview_mcp`: ready=False status=configured_runtime_unhealthy reason=tradingview_mcp_connectivity_probe_failed
- `yfinance`: ready=True status=ready reason=public_yahoo_http_endpoints

## Decision

This is nursery feedback only. The candidate remains fail-closed for production because the execution tree blocked the exact Crisis branch under current crowded/wide-range context.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/b2r_block_crowded_nursery_v1.json`
- CSV: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/b2r-block-crowded-nursery-v1/b2r_block_crowded_nursery_v1.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260511T234513-codex-board-b-b2r-block-crowded-nursery-v1/checks/b2r_block_crowded_nursery_v1_assertions.out`
