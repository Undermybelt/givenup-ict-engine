# Current Goal Strict Gap Audit v59

- Gate result: `current_goal_strict_gap_audit_v59=scoped_consumer_95_passes_strict_full_goal_still_blocked`.
- Checklist status: `blocked`.
- Scoped consumer 95 lanes: `5/5` accepted.
- R6 live rows: positives `73`, matched controls `73`; verifier status `schema_ready_unscored`.
- R6 pooled direct Wilson95 LCB: `0.950006246616`; pooled gate `true`.
- R6 split/species gates: chronological `false`, symbol `false`, venue `false`, species `false`.
- All-correct Wilson95 row requirement per bucket: `73`.
- Local Auto-Quant: status `dependency_ready_seed_required`, healthy `True`, data_ready `True`, active strategy files `0`.
- Strict full objective achieved: `false`; `update_goal=false`.
- Runtime code changed: `false`; thresholds relaxed: `false`; raw data committed: `false`; shared intake mutated: `false`; trade usable: `false`.

## Prompt To Artifact Checklist

| Requirement | Status | Evidence | Notes |
|---|---|---|---|
| Authoritative board file used and multi-agent safety preserved | `pass` | `docs/plans/2026-05-10-actionable-regime-confidence-todo.md` | This audit reads the board and writes only under its own run root; board writeback is append-only if performed. |
| Each active regime has a 95% scoped consumer factor | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T153637-codex-regime-factor-consumer-map-v1/regime-factor-map/regime_factor_consumer_map_v1.csv` | accepted_95_count=5/5 for Bull/Bear/Sideways/Crisis/scoped Manipulation. |
| Strict objective: every regime validated across other markets and other periods/timeframes | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1/r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_calibration_v1.json plus board Current Cursor` | Board still marks strict objective blocked; R6 chronological/symbol/venue/species gates remain false. |
| Direct Manipulation is direct-source evidence, not OHLCV proxy promotion | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1/r6-live-intake-rehydrate-calibration/positive_spoofing_layering_rows_v1.csv` | Current R6 rows are timestamped CFTC event/order-lifecycle spoofing/layering rows with matched controls. |
| R6 direct Manipulation pooled Wilson95 >= 0.95 | `pass` | `docs/experiments/actionable-regime-confidence/runs/20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1/r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_calibration_v1.json` | pooled_min_wilson95_lcb=0.950006246616 |
| R6 direct Manipulation chronological, symbol, venue, and species gates close | `fail` | `docs/experiments/actionable-regime-confidence/runs/20260511T235815-codex-r6-live-intake-rehydrate-calibration-v1/r6-live-intake-rehydrate-calibration/r6_live_intake_rehydrate_split_metrics_v1.csv` | chronological_split_gate=false, heldout_symbol_gate=false, heldout_venue_gate=false, direct_species_closed=false. |
| IBKR, TradingViewRemix, yfinance, Kraken provider paths checked | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output` | ready={'ibkr': False, 'tradingview_mcp': False, 'yfinance': True, 'kraken_public': False, 'kraken_cli': True}; provider paths checked but only ready providers can promote evidence. |
| Auto-Quant personally checked against local runtime | `partial` | `/Users/thrill3r/Auto-Quant` | healthy=True data_ready=True next=dependency_ready_seed_required |
| ict-engine chain exercised through filter/BBN/CatBoost/execution tree surfaces | `partial` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output` | analyze/pre-bayes/policy-training/workflow/path-ranking commands were run. policy_training_exit=0 workflow_execution_exit=0. |

## R6 Split Summary

| Split Family | Buckets | Failing | Pos Deficit | Neg Deficit | Worst LCB | Passes |
|---|---:|---:|---:|---:|---:|---:|
| `pooled_all_source_rows` | `1` | `0` | `0` | `0` | `0.950006246616` | `true` |
| `chronological_group_split` | `3` | `3` | `146` | `146` | `0.815676339628` | `false` |
| `heldout_symbol_exact` | `36` | `36` | `2555` | `2555` | `0.0` | `false` |
| `heldout_venue_exact` | `11` | `11` | `730` | `730` | `0.0` | `false` |

## Providers

| Provider | Ready | Status | Reason |
|---|---:|---|---|
| `ibkr` | `false` | `configured_runtime_unhealthy` | `ibkr_runtime_dependencies_missing_with_gateway_reachable` |
| `tradingview_mcp` | `false` | `configured_runtime_unhealthy` | `tradingview_mcp_connectivity_probe_failed` |
| `yfinance` | `true` | `ready` | `native_yfinance_runtime_available;public_yahoo_http_endpoints` |
| `kraken_public` | `false` | `configured_runtime_unhealthy` | `python3_provider_dependencies_missing` |
| `kraken_cli` | `true` | `ready` | `kraken_cli_config_detected` |

## Commands

| Command | Exit | Output | Error |
|---|---:|---|---|
| `direct_manipulation_verifier` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_direct_manipulation_verifier.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_direct_manipulation_verifier.err` |
| `provider_status_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_agent.err` |
| `provider_status_ibkr_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_ibkr_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_ibkr_agent.err` |
| `provider_status_tradingview_mcp_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_tradingview_mcp_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_tradingview_mcp_agent.err` |
| `provider_status_yfinance_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_yfinance_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_yfinance_agent.err` |
| `provider_status_kraken_public_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_kraken_public_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_kraken_public_agent.err` |
| `provider_status_kraken_cli_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_kraken_cli_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_provider_status_kraken_cli_agent.err` |
| `auto_quant_status_local` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_auto_quant_status_local.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_auto_quant_status_local.err` |
| `analyze_demo_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_demo_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_demo_agent.err` |
| `pre_bayes_status_demo` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_pre_bayes_status_demo.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_pre_bayes_status_demo.err` |
| `policy_training_status_demo` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_policy_training_status_demo.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_policy_training_status_demo.err` |
| `workflow_status_demo_agent` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_workflow_status_demo_agent.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_workflow_status_demo_agent.err` |
| `workflow_status_execution_candidate_demo` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_workflow_status_execution_candidate_demo.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_workflow_status_execution_candidate_demo.err` |
| `export_structural_path_ranking_target_demo` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_export_structural_path_ranking_target_demo.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_export_structural_path_ranking_target_demo.err` |
| `analyze_live_nq_yfinance_compact` | `0` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_live_nq_yfinance_compact.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_live_nq_yfinance_compact.err` |
| `analyze_live_btc_kraken_public_compact` | `1` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_live_btc_kraken_public_compact.out` | `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/command-output/current_goal_strict_gap_audit_v59_analyze_live_btc_kraken_public_compact.err` |

## Next

Do not chase more pooled R6 rows. Either redesign the validation axis away from impossible exact-symbol/exact-venue all-bucket closure, or acquire bulk direct rows and matched controls that raise each chosen validation bucket to at least 73 all-correct rows; then rerun the direct verifier and downstream chain.

## Artifacts

- JSON: `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/current-goal-strict-gap-audit/current_goal_strict_gap_audit_v59.json`
- Report: `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/current-goal-strict-gap-audit/current_goal_strict_gap_audit_v59.md`
- Checklist CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/current-goal-strict-gap-audit/prompt_to_artifact_checklist_v59.csv`
- R6 split deficit CSV: `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/current-goal-strict-gap-audit/r6_split_deficits_v59.csv`
- Assertions: `docs/experiments/actionable-regime-confidence/runs/20260512T000724-codex-current-goal-strict-gap-audit-v59/checks/current_goal_strict_gap_audit_v59_assertions.out`
