# Board B 220646 Real CatBoost Explicit Closure - Corrected Register V2

Generated: 2026-05-12T01:30:02+0800

## Decision

Not promoted.

The exact Sideways branch path is preserved through Pre-Bayes and CatBoost/path-ranker, and the corrected export/register/enable command shapes are closed. Promotion remains blocked because the execution-candidate surface is still an `analyze-live` Bull artifact, not an exact structural-branch promotion packet, and workflow/execution-tree remain fail-closed on `different_data_fingerprint`, `observe`, and no consumed validation.

## Ordered Chain

| Layer | Evidence | Result |
|---|---|---|
| Provider visibility | `command-output/00_provider_status.out` | yfinance and `kraken_cli` ready; IBKR gateway visible but deps missing; TradingViewRemix MCP unhealthy. |
| Auto-Quant handoff | `command-output/02_factor_research_explicit_historical.out`, `command-output/23_auto_quant_status_env_root.out` | `dependency_ready_data_ready`, data ready, dependency healthy at Auto-Quant commit `34ba6b6ee6aa69813a50a72158d4c089d97afb96`. |
| Auto-Quant recorded branch | `../20260512T004738-codex-board-b-220646-explicit-historical-rerun-v1/explicit-historical-rerun-v1/logs/13_auto_quant_run_recorded_branch_offline_2021_2025_selected.out` | Closed exit `0`; real NQ/USD 2021-2025 backtests emitted nonzero trades for three strategies. Supplemental only until consumed by the exact branch stack. |
| Pre-Bayes | `command-output/04_pre_bayes_status_after_feedback.out`, `command-output/22_workflow_full_after_repair.out` | `pass_neutralized`; `parent_regime_root=Sideways`; exact branch path preserved. |
| BBN | `state_real_catboost_explicit_closure_v1/SRC_ROOT_CARRY_LONG_220646/workflow_snapshot.json` | Read-only BBN accepted `SourceRootStopCarryLongHorizonV1` and marked trade usable, but applied bundle BBN still recorded `regime_bundle_bbn_application_status=skipped` / `no_supported_label`; not promotion evidence. |
| CatBoost/path-ranker | `command-output/19_policy_training_status_after_repair.out`, `catboost/scores/current_scores.csv`, `catboost/scores/history_scores.csv` | Real CatBoost artifact ready; current scores `4` rows; history scores `883` rows; runtime ready; production validation `869/30`; observation validation `82/30`; runtime matches `4`. |
| Structural bundle | `command-output/20_workflow_structural_bundle_after_repair.out` | Selected exact branch `Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`; path-ranker gate still `observe`. |
| Execution candidate / workflow | `command-output/21_workflow_execution_candidate_after_repair.out`, `command-output/22_workflow_full_after_repair.out`, `state_real_catboost_explicit_closure_v1/SRC_ROOT_CARRY_LONG_220646/execution_tree_trace.json` | Execution candidate is `analyze-live` / Bull / `promote_latest`; workflow current focus is `update` with `different_data_fingerprint`; execution tree trace is `observe` / `transition_guardrail` / `guarded`. |

## Auto-Quant Recorded-Branch Results

The lingering `004738` recorded-branch run finished after the first `010454` readback and is supplemental evidence for the same explicit-historical workspace.

| Strategy | Trades | Total profit | Sharpe | Win rate | Profit factor | Max drawdown |
|---|---:|---:|---:|---:|---:|---:|
| `RegimeRootPulseBranch` | 4705 | 59.59% | 1.1480 | 35.7705% | 1.0872 | -25.1489% |
| `RegimeTrendCarry` | 556 | 70.45% | 0.4874 | 34.7122% | 1.2951 | -18.5655% |
| `RegimeVolBreakout` | 515 | 37.35% | 0.2928 | 36.5049% | 1.1837 | -17.9457% |

These are real backtests, but they are not a promotion packet because they have not been consumed as an exact structural-branch execution candidate with closed-loop confidence.

## Command Closure

- Initial ordered chain `00-15`: closed; `05`, `10`, and `11` failed due command compatibility, not a profitability rejection.
- Corrected register chain `16-23`: closed with exits `0`.
- `16_export_structural_path_ranking_target_cli_repair`: fixed unsupported `--output-dir` usage.
- `17_register_catboost_path_ranker_artifact_json_repair`: registered JSON trainer metadata instead of binary `.cbm`.
- `18_enable_structural_path_ranking_runtime_prefer_history_repair`: used supported `prefer_history`.
- `19-22`: policy-training, structural bundle, execution-candidate, and full workflow readbacks closed with exits `0`.
- `23_auto_quant_status_env_root`: confirmed `dependency_ready_data_ready`.

## Remaining Blocker

The full ordered chain is callable and branch-preserving through CatBoost/path-ranker, but closed-loop promotion is still absent. The next narrow task is to make execution-candidate/workflow emit and evaluate an exact structural-branch promotion packet for:

`Sideways -> RangeCarry -> StopManagedRangeCarry -> SourceRootStopCarryLongHorizonV1:sideways_carry_h8_sl040_tp12`

Do not rerun RC-SPA or promote from `analyze-live` readiness alone.
