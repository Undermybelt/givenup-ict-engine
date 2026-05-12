# Provider-Backed Agent-Material Auto-Quant Dispatch Fail-Closed v1

Run root: `docs/experiments/actionable-regime-confidence/runs/20260512T151057+0800-codex-provider-backed-agent-material-aq-dispatch-v1`

## Scope

This slice converts provider-backed inputs from `143900` and the high-density screen direction from `145809` into generic Auto-Quant agent-material packages, then dispatches the first package through the local Auto-Quant runtime. It is a real Auto-Quant dispatch and prior-init readback, but it is not a Board A acceptance packet.

## Artifacts

- Strategy source: `strategies/ProviderTrendPullbackResume.py`
- Material packages:
  - `materials/ibkr_spy_provider_trend_pullback_resume.json`
  - `materials/yahoo_es_provider_trend_pullback_resume.json`
- Imported strategy library: `provider_aq_dispatch_spy_strategy_library_v1.json`
- Auto-Quant batch/dispatch/rank state: `state/auto-quant/PROVIDER_AQ_151057/`
- Downstream readback state: `state_spy_downstream_v1/`
- Commands and exit codes: `command-output/`, `checks/`

## Command Results

| Step | Exit | Result |
|---|---:|---|
| `01_material_json_valid` | 0 | Both material JSON files parsed. |
| `02_strategy_py_compile` | 0 | Strategy source compiled under `/Users/thrill3r/Auto-Quant/.venv/bin/python`. |
| `03_agent_material_batch` | 0 | Batch created with `2` jobs and `max_parallel=1`. |
| `04_agent_material_dispatch_group0` | 0 | IBKR SPY package dispatched through Auto-Quant. |
| `05_agent_material_rank` | 0 | Completed SPY dispatch ranked. |
| `06_auto_quant_results_import` | 0 | SPY dispatch imported as one strategy-library handoff; `n_ok=1`. |
| `07_auto_quant_prior_init` | 0 | Prior init applied; `evidence_value_gate_passed=true`. |
| `08_pre_bayes_status_after_prior` | 0 | Readback succeeded but canonical regime/confidence remained absent. |
| `09_policy_training_status_after_prior` | 0 | Readback succeeded but `analyze_runs=0`, entry-model matched rows `0`, and path-ranker runtime disabled. |
| `10_workflow_status_after_prior` | 0 | Readback succeeded but no workflow phase snapshots were available; execution stayed observe/not ready. |

## Auto-Quant Dispatch Result

Dispatched job: `IBKR SPY 1h Provider Trend Pullback Resume`

- Status: `completed`
- Pair: `SPY/USD`
- Backtest window: `2023-01-01 00:00:00 -> 2025-12-31 00:00:00`
- Trades: `316`
- Total profit: `29.99%`
- Sharpe: `0.6637`
- Sortino: `1.6126`
- Calmar: `7.5834`
- Max drawdown: `-6.8992%`
- Win rate: `41.4557%`
- Profit factor: `1.3903`

The Yahoo ES material package was created but not dispatched in this slice because another provider-backed `ict-engine analyze` process for root `150515` was active at high CPU. Keeping `max_parallel=1` and stopping after group `0` preserves the local concurrency rule.

## Downstream Readback

- `auto-quant-results-import` imported the dispatch manifest with `n_total_strategies=1`, `n_ok=1`, and `n_error=0`.
- `auto-quant-prior-init` applied the SPY strategy with `n_win=131`, `n_loss=185`, `trade_count=316`, and `evidence_value_gate_passed=true`.
- `pre-bayes-status` had no latest canonical structural active regime, confidence, probabilities, filtered assignments, gate, policy, or soft evidence.
- `policy-training-status` had `analyze_runs=0`, entry-model `matched_rows=0`, structural path-ranker runtime `disabled`, and structural path-ranking target export missing.
- `workflow-status` reported `actionable_artifacts=0`, no latest promotable artifact, no consumed validation, no workflow phase snapshots, and an execution candidate with `ready=false`, `actionable=false`, `review_status=observe`.
- The generic Auto-Quant agent-material dispatch path did not export per-trade JSONL, so no `auto-quant-ingest-real-trades` step was run. The earlier `145809` screen trades were not relabeled as Auto-Quant realized trades.

## Gate

- `support_once:151057_provider_backed_agent_material_aq_dispatch_v1`.
- `evidence_class:provider_backed_auto_quant_agent_material_dispatch_fail_closed`.
- `pass:provider_backed_ibkr_spy_material_packaged`.
- `pass:provider_backed_yahoo_es_material_packaged`.
- `pass:auto_quant_agent_material_batch_exit0`.
- `pass:auto_quant_agent_material_dispatch_group0_exit0`.
- `pass:auto_quant_spy_dispatch_completed`.
- `pass:auto_quant_results_import_n_ok_1`.
- `pass:auto_quant_prior_init_evidence_value_gate_passed`.
- `partial:spy_trade_count_316`.
- `partial:spy_total_profit_pct_29_99`.
- `partial:spy_profit_factor_1_3903`.
- `fail_closed:spy_win_rate_41_4557_below_regime_confidence_gate`.
- `fail_closed:yahoo_es_material_not_dispatched_due_active_heavy_process`.
- `fail_closed:no_auto_quant_real_trades_jsonl_export`.
- `fail_closed:no_real_trade_ingest`.
- `fail_closed:pre_bayes_canonical_regime_absent`.
- `fail_closed:pre_bayes_confidence_absent`.
- `fail_closed:policy_training_analyze_runs_0`.
- `fail_closed:entry_models_matched_rows_0`.
- `fail_closed:path_ranker_runtime_disabled`.
- `fail_closed:structural_path_ranking_target_missing`.
- `fail_closed:no_catboost_training_or_runtime_admission`.
- `fail_closed:workflow_snapshots_absent`.
- `fail_closed:execution_ready_false`.
- `fail_closed:actionable_false`.
- `promotion_allowed=false`.
- `trade_usable=false`.
- `update_goal=false`.

## Next

Do not promote from `151057`. The next useful step is to let the active `150515` BTC provider-backed full chain finish, then either classify that result or dispatch the pending Yahoo ES material package only when local heavy-process pressure is low. Any acceptance attempt still needs provider-backed Auto-Quant output, real trade/feed-forward evidence, Pre-Bayes/filter, BBN, CatBoost/path-ranker calibration, and execution-tree readiness with calibrated per-regime confidence.
